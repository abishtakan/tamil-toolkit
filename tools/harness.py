"""Shared fixture validation. No Tamil linguistic algorithms belong here."""

import json
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"
JOINERS = frozenset(map(chr, (0x200C, 0x200D)))


def strings(value, path=""):
    """Yield (member JSON Pointer, text, is_key) for strings and object keys."""
    if isinstance(value, str):
        yield path, value, False
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, f"{path}/{index}")
    elif isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            member = f"{path}/{escaped}"
            yield member, str(key), True
            yield from strings(item, member)


def unicode_issues(value):
    """Check decoded strings, including escapes hidden in JSON source."""
    issues = set()
    for path, text, is_key in strings(value):
        # Key issues are deliberately outside the schema's value-only exceptions.
        prefix = "key_" if is_key else ""
        if any(0xD800 <= ord(char) <= 0xDFFF for char in text):
            issues.add((path, prefix + "surrogate"))
        if not unicodedata.is_normalized("NFC", text):
            issues.add((path, prefix + "non_nfc"))
        if JOINERS.intersection(text):
            issues.add((path, prefix + "joiner"))
    return issues


def validate_rows(path: Path, seen=None):
    seen = set() if seen is None else seen
    validator = Draft202012Validator(json.loads((GOLDEN / "schema.json").read_text(encoding="utf-8")))
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path}:{line_number}: blank JSONL row")
        row = json.loads(line)
        errors = sorted(validator.iter_errors(row), key=lambda error: str(error.path))
        if errors:
            raise ValueError(f"{path}:{line_number}: {errors[0].message}")
        if row["id"] in seen:
            raise ValueError(f"{path}:{line_number}: duplicate id {row['id']}")
        seen.add(row["id"])
        exceptions = row.get("unicode_exceptions", [])
        allowed = {(entry["path"], entry["kind"]) for entry in exceptions}
        if len(allowed) != len(exceptions):
            raise ValueError(f"{path}:{line_number}: duplicate Unicode exception")
        actual = unicode_issues(row)
        if actual != allowed:
            raise ValueError(f"{path}:{line_number}: unexpected Unicode issues {sorted(actual - allowed)!a}; unused exceptions {sorted(allowed - actual)!a}")
        if row.get("locale") and row["dialect"] != row["locale"]:
            raise ValueError(f"{path}:{line_number}: locale/dialect mismatch")
        if row.get("region") in {"JAFFNA", "BATTICALOA", "VANNI", "UP_COUNTRY"} and row["dialect"] != "SL":
            raise ValueError(f"{path}:{line_number}: SL region requires dialect SL")
        if row.get("region") in {"TN", "KONGU", "CHENNAI"} and row["dialect"] != "TN":
            raise ValueError(f"{path}:{line_number}: TN region requires dialect TN")
        rows.append(row)
    return rows


def load_vectors(root=GOLDEN):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or not isinstance(manifest.get("suites"), list):
        raise ValueError("invalid golden manifest")
    seen, files, active = set(), set(), []
    for suite in manifest["suites"]:
        name = suite["file"]
        if Path(name).name != name or not name.endswith(".jsonl") or name in files:
            raise ValueError(f"invalid or duplicate suite: {name}")
        files.add(name)
        rows = validate_rows(root / name, seen)
        if suite["status"] == "active":
            operations = suite.get("operations", [])
            if not rows or not operations or any(row["op"] not in operations for row in rows):
                raise ValueError(f"empty suite or undeclared operation in {name}")
            active.extend(rows)
        elif suite["status"] != "planned" or not suite.get("reason"):
            raise ValueError(f"unknown status or missing reason: {name}")
    if files != {path.name for path in root.glob("*.jsonl")}:
        raise ValueError("every JSONL suite must be registered in manifest.json")
    if not active or {row["dialect"] for row in active} != {"COMMON", "TN", "SL"}:
        raise ValueError("active fixtures must include COMMON, TN, and SL")
    return active


def validate_golden_schema(file_path: str):
    path = Path(file_path)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(GOLDEN.resolve()) or path.suffix != ".jsonl":
        raise ValueError("file_path must identify a JSONL file under tests/golden")
    # Global validation catches IDs duplicated across different suites too.
    active = load_vectors()
    rows = validate_rows(path)
    return {"valid": True, "file": path.relative_to(ROOT).as_posix(), "rows": len(rows), "active_vectors": len(active)}
