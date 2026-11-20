"""Full-cell verification must catch a re-signed source-record alteration."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.prepare_historical_lexicon import verify_export


def _write(path: Path, value: object) -> dict:
    raw = json.dumps(value, ensure_ascii=True).encode("utf-8")
    path.write_bytes(raw)
    return {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def test_export_verifies_every_original_cell_even_after_resigning_bucket(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    raw = b"headword_ta,meaning_en\nword,first\nword,second\n"
    csv_path = source / "primary_meanings.csv"
    csv_path.write_bytes(raw)
    pin = tmp_path / "pin.json"
    pin.write_text(json.dumps([{"file": csv_path.name, "bytes": len(raw),
                               "sha256": hashlib.sha256(raw).hexdigest()}]), encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    key = "word"
    wanted = hashlib.sha256(key.encode()).hexdigest()[:2]
    metas = {}
    rows = [{"source_file": csv_path.name, "source_row": i, "lookup_key": key,
             "fields": {"headword_ta": key, "meaning_en": value}}
            for i, value in enumerate(("first", "second"), 1)]
    for i in range(256):
        bucket = f"{i:02x}"
        records = rows if bucket == wanted else []
        metas[bucket] = _write(output / f"{bucket}.json", {
            "schema_version": 1, "bucket": bucket, "records": records}) | {"records": len(records)}
    manifest = {"schema_version": 1, "data_status": "owner_supplied_unverified",
                "rights_status": "unresolved", "total_records": 2, "distinct_keys": 1,
                "files": [{"file": csv_path.name, "rows": 2}], "buckets": metas}
    _write(output / "manifest.json", manifest)
    assert verify_export(output, source=source, pin=pin)["all_original_cells_identical"]
    rows[1]["fields"]["meaning_en"] = "changed"
    metas[wanted] = _write(output / f"{wanted}.json", {
        "schema_version": 1, "bucket": wanted, "records": rows}) | {"records": 2}
    _write(output / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Original cells differ"):
        verify_export(output, source=source, pin=pin)
