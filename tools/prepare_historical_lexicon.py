"""Export or verify the complete owner-supplied historical source-record artifact.

Rust owns indexing and query semantics. This tool only orchestrates export and
checks hashes and exact original CSV-cell coverage; it grants no content license.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/sources/tamil-lexicon"
PIN = ROOT / "data/sources/tamil-lexicon.sha256.json"
OUTPUT = ROOT / "playground/public/historical-lexicon"


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_export(output: Path, *, source: Path = SOURCE, pin: Path = PIN) -> dict:
    """Check every original cell and locator, not just totals or sampled rows."""
    expected_files = json.loads(pin.read_text(encoding="utf-8"))
    for item in expected_files:
        path = source / item["file"]
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Frozen source changed: {item['file']}")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1
            or manifest.get("data_status") != "owner_supplied_unverified"
            or manifest.get("rights_status") != "unresolved"):
        raise ValueError("Incorrect historical data status or schema")
    if set(manifest["buckets"]) != {f"{i:02x}" for i in range(256)}:
        raise ValueError("Export must contain exactly 256 buckets")
    # Hash each complete exported row so the comparison remains memory bounded.
    observed: dict[str, dict[int, str]] = {}
    keys: set[str] = set()
    total = 0
    for bucket, meta in manifest["buckets"].items():
        if meta["file"] != f"{bucket}.json":
            raise ValueError("Unsafe or unexpected bucket filename")
        path = output / meta["file"]
        if path.stat().st_size != meta["bytes"] or sha256(path) != meta["sha256"]:
            raise ValueError(f"Export bucket changed: {bucket}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["schema_version"] != 1 or data["bucket"] != bucket:
            raise ValueError("Bucket header mismatch")
        if len(data["records"]) != meta["records"]:
            raise ValueError("Bucket record count mismatch")
        for record in data["records"]:
            filename, row = record["source_file"], record["source_row"]
            if not isinstance(row, int) or isinstance(row, bool) or row < 1:
                raise ValueError("Invalid row locator")
            by_row = observed.setdefault(filename, {})
            if row in by_row:
                raise ValueError("Duplicate source row in export")
            encoded = json.dumps(record["fields"], ensure_ascii=True, sort_keys=True)
            by_row[row] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            key = record["lookup_key"]
            if hashlib.sha256(key.encode("utf-8")).hexdigest()[:2] != bucket:
                raise ValueError("Record assigned to wrong bucket")
            keys.add(key)
            total += 1
    counts = {}
    for item in expected_files:
        if not item["file"].endswith(".csv"):
            continue
        filename = item["file"]
        by_row = observed.pop(filename, {})
        count = 0
        with (source / filename).open(encoding="utf-8-sig", newline="") as handle:
            for count, fields in enumerate(csv.DictReader(handle), 1):
                encoded = json.dumps(fields, ensure_ascii=True, sort_keys=True)
                if by_row.pop(count, None) != hashlib.sha256(encoded.encode("utf-8")).hexdigest():
                    raise ValueError(f"Original cells differ: {filename}:{count}")
        if by_row:
            raise ValueError(f"Unexpected rows in {filename}")
        counts[filename] = count
    if observed or sum(counts.values()) != total or manifest["total_records"] != total:
        raise ValueError("Full record accounting mismatch")
    if len(keys) != manifest["distinct_keys"]:
        raise ValueError("Distinct key count mismatch")
    manifest_counts = {item["file"]: item["rows"] for item in manifest["files"]}
    if counts != manifest_counts:
        raise ValueError("Per-file counts differ from manifest")
    return {"verified": True, "total_records": total, "distinct_keys": len(keys),
            "all_original_cells_identical": True, "per_file": counts,
            "data_status": manifest["data_status"], "rights_status": manifest["rights_status"]}


def prepare(output: Path = OUTPUT, *, check: bool = False) -> dict:
    if not (output / "manifest.json").is_file():
        if check:
            raise ValueError("Historical export is missing; run tools/prepare_historical_lexicon.py")
        if output.exists():
            raise ValueError("Incomplete output exists; preserve it and select a new --output directory")
        env = dict(os.environ)
        env["PATH"] = str(Path.home() / ".cargo/bin") + os.pathsep + env.get("PATH", "")
        cargo = shutil.which("cargo", path=env["PATH"])
        if cargo is None:
            raise ValueError("Cargo is required to build the historical source exporter")
        subprocess.run([cargo, "run", "--locked", "-p", "tamil-toolkit", "--bin",
                        "source-records", "--", str(SOURCE), str(PIN), str(output)],
                       cwd=ROOT, env=env, check=True)
    return verify_export(output)


def archive_export(output: Path, archive: Path) -> None:
    """Package the separate data artifact without changing engine SPDX metadata."""
    verify_export(output)
    if archive.exists():
        raise ValueError("Archive already exists; preserve it and choose a new path")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    files = ["manifest.json", "NOTICE.md", *[meta["file"] for meta in manifest["buckets"].values()]]
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as handle:
        for name in sorted(files):
            info = zipfile.ZipInfo(f"historical-lexicon/{name}", date_time=(2026, 11, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            handle.writestr(info, (output / name).read_bytes())
    with zipfile.ZipFile(archive) as handle:
        if handle.testzip() is not None:
            raise ValueError("Historical archive integrity check failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--archive", type=Path, help="Write a separate deterministic owner-directed data ZIP")
    args = parser.parse_args()
    output = args.output.resolve()
    result = prepare(output, check=args.check)
    if args.archive:
        archive_export(output, args.archive.resolve())
        result["archive_sha256"] = sha256(args.archive.resolve())
        result["archive_bytes"] = args.archive.stat().st_size
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
