"""Inventory, tamper, quoted-multiline, and record-accounting tests (Feature 021 T010)."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest

from tools.lexicon import LexiconError, decode_text, inventory

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/reference/lexicon/structural"
SAMPLE_SOURCE = FIXTURES / "sample_source"
SAMPLE_MANIFEST = FIXTURES / "sample_manifest.json"


def _copy_sample(tmp_path: Path) -> tuple[Path, Path]:
    src = tmp_path / "source"
    shutil.copytree(SAMPLE_SOURCE, src)
    manifest = tmp_path / "manifest.json"
    shutil.copy2(SAMPLE_MANIFEST, manifest)
    return src, manifest


def test_inventory_handles_bom_multiline_spans_and_fst_disposition(tmp_path):
    out_dir = tmp_path / "inv_out"
    report = inventory(SAMPLE_SOURCE, out_dir, manifest_path=SAMPLE_MANIFEST)

    assert report["schema_version"] == 1
    assert Path(report["source_root"]).resolve() == SAMPLE_SOURCE.resolve()
    assert report["csv_records"] == 2

    files_by_name = {item["file"]: item for item in report["files"]}
    assert set(files_by_name) == {"entries_sample.csv", "derived_sample.fst"}
    assert files_by_name["entries_sample.csv"]["rows"] == 2
    assert files_by_name["derived_sample.fst"]["rows"] == 0
    assert files_by_name["derived_sample.fst"]["snapshot_id"].startswith("snap_")

    manifest_disk = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_disk == report

    with (out_dir / "source_records.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, strict=True))

    assert len(rows) == 2
    assert set(rows[0].keys()) == {
        "record_id",
        "snapshot_id",
        "logical_ordinal",
        "line_start",
        "line_end",
        "legacy_key_json",
        "row_sha256",
    }
    by_key = {decode_text(r["legacy_key_json"]): r for r in rows}
    assert by_key["L001"]["logical_ordinal"] == "2"
    assert int(by_key["L001"]["line_start"]) == 2
    assert int(by_key["L001"]["line_end"]) == 3
    assert by_key["L002"]["logical_ordinal"] == "3"
    assert int(by_key["L002"]["line_start"]) == 4
    assert int(by_key["L002"]["line_end"]) == 4


def test_inventory_is_idempotent_and_rejects_conflicting_output(tmp_path):
    out_dir = tmp_path / "inv_out"
    first = inventory(SAMPLE_SOURCE, out_dir, manifest_path=SAMPLE_MANIFEST)
    second = inventory(SAMPLE_SOURCE, out_dir, manifest_path=SAMPLE_MANIFEST)
    assert first == second

    (out_dir / "manifest.json").write_text('{"tampered": true}\n', encoding="utf-8")
    with pytest.raises(LexiconError):
        inventory(SAMPLE_SOURCE, out_dir, manifest_path=SAMPLE_MANIFEST)


def test_inventory_rejects_tampered_csv_or_fst_before_writing_output(tmp_path):
    src, manifest = _copy_sample(tmp_path)
    out_dir = tmp_path / "inv_out"

    fst = src / "derived_sample.fst"
    fst.write_bytes(fst.read_bytes() + b"X")
    with pytest.raises(LexiconError, match="hash mismatch"):
        inventory(src, out_dir, manifest_path=manifest)
    assert not out_dir.exists()

    # Restore FST and tamper CSV byte.
    shutil.copy2(SAMPLE_SOURCE / "derived_sample.fst", fst)
    csv_file = src / "entries_sample.csv"
    csv_file.write_bytes(csv_file.read_bytes().replace(b"L002", b"L009"))
    with pytest.raises(LexiconError, match="hash mismatch"):
        inventory(src, out_dir, manifest_path=manifest)
    assert not out_dir.exists()


def test_inventory_rejects_extra_or_missing_source_file(tmp_path):
    src, manifest = _copy_sample(tmp_path)
    (src / "unexpected.csv").write_text("id\n1\n", encoding="utf-8")
    with pytest.raises(LexiconError, match="file set mismatch"):
        inventory(src, tmp_path / "inv_out", manifest_path=manifest)


def test_inventory_rejects_width_mismatch_and_duplicate_headers(tmp_path):
    bad_width = tmp_path / "bad_width"
    bad_width.mkdir()
    (bad_width / "rows.csv").write_text("id,word\n1,a,extra\n", encoding="utf-8")
    with pytest.raises(LexiconError, match="width mismatch"):
        inventory(bad_width, tmp_path / "out_width")

    dup_header = tmp_path / "dup_header"
    dup_header.mkdir()
    (dup_header / "rows.csv").write_text("id,id\n1,2\n", encoding="utf-8")
    with pytest.raises(LexiconError, match="duplicate CSV header"):
        inventory(dup_header, tmp_path / "out_dup")
