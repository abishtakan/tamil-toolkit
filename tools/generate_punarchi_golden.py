"""Programmatic compiler and validator for tests/golden/punarchi_nannool.jsonl.

Enforces Constitution Principles II, III, and IV:
- Zero hand-counted UTF-8 byte or Tamil written-unit offsets (`split_byte`, `split_unit`).
- Escaped ASCII JSONL (`ensure_ascii=True`), UTF-8 without BOM, LF line endings.
- Globally unique `punarchi_*` IDs across all `tests/golden/*.jsonl` suites.
- Explicit primary witness provenance (`viruttiyurai_pno=`, `kandigai=`, `extended_usage`,
  or `contracts/punarchi.md` for contract-error rows) and zero copied commentary prose.
- Exact `unicode_exceptions` matching `tools.harness.unicode_issues`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.harness import GOLDEN, unicode_issues, validate_rows  # noqa: E402

OUTPUT = GOLDEN / "punarchi_nannool.jsonl"
ALLOWED_OPS = frozenset({"punarchi_join", "punarchi_split_candidates", "punarchi_rules"})
PROVENANCE_MARKERS = (
    "viruttiyurai_pno=",
    "kandigai=",
    "pmuni0147",
    "extended_usage",
    "contracts/punarchi.md",
)
ID_RE = re.compile(r"^punarchi_[a-z0-9_]+$")

# Atomic tailored written units matching crates/tamil-core/src/lib.rs (`ATOMIC_LETTERS`).
ATOMIC_PREFIXES = (
    "\u0B95\u0BCD\u0BB7",  # க்ஷ
    "\u0BB8\u0BCD\u0BB0\u0BC0",  # ஸ்ரீ
    "\u0BB6\u0BCD\u0BB0\u0BC0",  # ஶ்ரீ
)

TAMIL_COMBINING_MARKS = frozenset(
    {
        0x0B82,
        0x0BBE,
        0x0BBF,
        0x0BC0,
        0x0BC1,
        0x0BC2,
        0x0BC6,
        0x0BC7,
        0x0BC8,
        0x0BCA,
        0x0BCB,
        0x0BCC,
        0x0BCD,
        0x0BD7,
    }
)


def tamil_written_units(text: str) -> list[str]:
    """Split an NFC string into Tamil written units matching `tamil_core::Letters`."""
    units: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        matched_atomic = None
        for atomic in ATOMIC_PREFIXES:
            if text.startswith(atomic, i):
                matched_atomic = atomic
                break
        if matched_atomic is not None:
            j = i + len(matched_atomic)
            while j < n and (
                ord(text[j]) in TAMIL_COMBINING_MARKS
                or unicodedata.category(text[j]) in {"Mn", "Mc"}
            ):
                j += 1
            units.append(text[i:j])
            i = j
            continue

        j = i + 1
        while j < n and (
            ord(text[j]) in TAMIL_COMBINING_MARKS
            or unicodedata.category(text[j]) in {"Mn", "Mc"}
        ):
            j += 1
        units.append(text[i:j])
        i = j
    return units


def written_unit_boundaries(surface: str) -> dict[int, int]:
    """Map written-unit index -> UTF-8 byte offset for an NFC surface string."""
    units = tamil_written_units(surface)
    offsets: dict[int, int] = {0: 0}
    byte_pos = 0
    for idx, unit in enumerate(units, 1):
        byte_pos += len(unit.encode("utf-8"))
        offsets[idx] = byte_pos
    return offsets


def split_coords_for_prefix_units(surface: str, split_unit: int) -> tuple[int, int]:
    """Return exact `(split_byte, split_unit)` for a given written-unit boundary."""
    nfc = unicodedata.normalize("NFC", surface)
    offsets = written_unit_boundaries(nfc)
    if split_unit not in offsets or split_unit == 0 or split_unit == len(offsets) - 1:
        raise ValueError(
            f"invalid internal split_unit={split_unit} for {surface!r} (valid 1..{len(offsets) - 2})"
        )
    return offsets[split_unit], split_unit


def split_coords_for_byte_prefix(surface: str, prefix_text: str) -> tuple[int, int]:
    """Return exact `(split_byte, split_unit)` where `surface` begins with `prefix_text`."""
    nfc = unicodedata.normalize("NFC", surface)
    prefix_nfc = unicodedata.normalize("NFC", prefix_text)
    if not nfc.startswith(prefix_nfc) or not prefix_nfc or prefix_nfc == nfc:
        raise ValueError(f"prefix {prefix_text!r} is not a strict non-empty prefix of {surface!r}")
    target_byte = len(prefix_nfc.encode("utf-8"))
    offsets = written_unit_boundaries(nfc)
    for unit_idx, byte_off in offsets.items():
        if byte_off == target_byte:
            return byte_off, unit_idx
    raise ValueError(
        f"prefix {prefix_text!r} (byte {target_byte}) does not align to a Tamil written-unit boundary in {surface!r}"
    )


def build_vector(
    *,
    vector_id: str,
    op: str,
    input_data: Any,
    expected: Any = None,
    expected_error: str | None = None,
    dialect: str = "COMMON",
    region: str | None = None,
    tags: list[str],
    source: str,
    unicode_exceptions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Construct a schema-valid punarchi golden vector."""
    if not ID_RE.match(vector_id):
        raise ValueError(f"invalid punarchi vector id: {vector_id!r}")
    if op not in ALLOWED_OPS:
        raise ValueError(f"invalid punarchi op: {op!r}")
    if (expected is None) == (expected_error is None):
        raise ValueError(f"{vector_id}: specify exactly one of expected or expected_error")
    row: dict[str, Any] = {
        "id": vector_id,
        "op": op,
        "input": input_data,
        "dialect": dialect,
        "tags": tags,
        "source": source,
    }
    if region is not None:
        row["region"] = region
    if expected_error is not None:
        row["expected_error"] = expected_error
    else:
        row["expected"] = expected
    if unicode_exceptions:
        row["unicode_exceptions"] = unicode_exceptions
    return row


def encode_jsonl_row(row: dict[str, Any]) -> str:
    """Serialize a golden row as pure ASCII escaped JSONL."""
    return json.dumps(row, ensure_ascii=True, separators=(",", ":"))


def load_case_builders() -> list[dict[str, Any]]:
    """Collect golden vector definitions from `tools/punarchi_golden_cases.py` if present."""
    cases_file = ROOT / "tools" / "punarchi_golden_cases.py"
    if not cases_file.is_file():
        return []
    import importlib.util

    spec = importlib.util.spec_from_file_location("punarchi_golden_cases", cases_file)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.build_all_vectors())


def render() -> str:
    rows = load_case_builders()
    if not rows:
        return ""
    return "\n".join(encode_jsonl_row(r) for r in rows) + "\n"


def validate_punarchi_file(path: Path = OUTPUT) -> list[str]:
    """Validate punarchi_nannool.jsonl for formatting, schema, uniqueness, provenance, and offsets."""
    failures: list[str] = []
    if not path.is_file():
        return [f"{path}: file does not exist"]

    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append(f"{path}: UTF-8 BOM is not permitted")
    if b"\r\n" in raw:
        failures.append(f"{path}: CRLF line endings are not permitted (use LF)")

    text = raw.decode("utf-8")
    if not text:
        # Empty planned placeholder file is allowed until Phase 2 T013 populates vectors.
        return failures

    if not text.endswith("\n"):
        failures.append(f"{path}: file must end with a single LF newline")

    # Collect IDs from all OTHER golden suites to ensure global uniqueness.
    other_ids: set[str] = set()
    for other in sorted(GOLDEN.glob("*.jsonl")):
        if other.resolve() == path.resolve():
            continue
        for line in other.read_text(encoding="utf-8").splitlines():
            if line.strip():
                other_ids.add(json.loads(line)["id"])

    # Schema & unicode_exceptions validation via shared harness.
    try:
        rows = validate_rows(path, seen=set(other_ids))
    except ValueError as exc:
        failures.append(str(exc))
        return failures

    for line_no, (raw_line, row) in enumerate(zip(text.splitlines(), rows), 1):
        # Escaped ASCII-only JSONL check.
        if any(ord(ch) > 0x7F for ch in raw_line):
            failures.append(f"{path}:{line_no}: non-ASCII character must be \\uXXXX-escaped in JSONL")

        vid = row["id"]
        if not ID_RE.match(vid):
            failures.append(f"{path}:{line_no}: id {vid!r} must start with 'punarchi_'")

        op = row["op"]
        if op not in ALLOWED_OPS:
            failures.append(f"{path}:{line_no}: unexpected op {op!r}")

        src = row["source"]
        if not any(marker in src for marker in PROVENANCE_MARKERS):
            failures.append(
                f"{path}:{line_no}: source {src!r} missing required witness provenance marker {PROVENANCE_MARKERS}"
            )
        if len(src) > 220:
            failures.append(
                f"{path}:{line_no}: source exceeds 220 chars ({len(src)}); do not copy commentary prose"
            )

        # Verify unicode_exceptions exactness (double-check beyond harness).
        issues = unicode_issues(row)
        declared = {(e["path"], e["kind"]) for e in row.get("unicode_exceptions", [])}
        if issues != declared:
            failures.append(f"{path}:{line_no}: unicode_exceptions mismatch {issues!r} != {declared!r}")

        # Verify split_byte / split_unit coordinates programmatically on split vectors.
        if op == "punarchi_split_candidates" and "expected" in row:
            surface = row["input"]["surface"]
            nfc_surface = unicodedata.normalize("NFC", surface)
            offsets = written_unit_boundaries(nfc_surface)
            max_unit = len(offsets) - 1
            for cand_idx, cand in enumerate(row["expected"]):
                sb = cand.get("split_byte")
                su = cand.get("split_unit")
                if not isinstance(sb, int) or not isinstance(su, int):
                    failures.append(
                        f"{path}:{line_no}: expected[{cand_idx}] missing integer split_byte/split_unit"
                    )
                    continue
                if su not in offsets or su == 0 or su == max_unit:
                    failures.append(
                        f"{path}:{line_no}: expected[{cand_idx}] split_unit={su} is not a valid internal boundary (1..{max_unit - 1})"
                    )
                elif offsets[su] != sb:
                    failures.append(
                        f"{path}:{line_no}: expected[{cand_idx}] split_byte={sb} does not match written-unit {su} byte offset {offsets[su]}"
                    )

    # If a case builder exists, verify generated output matches file on disk.
    cases_file = ROOT / "tools" / "punarchi_golden_cases.py"
    if cases_file.is_file():
        expected_text = render()
        if text != expected_text:
            failures.append(
                f"{path}: golden file is out of sync with tools/punarchi_golden_cases.py; run `uv run --locked python tools/generate_punarchi_golden.py --write`"
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile and validate punarchi_nannool.jsonl")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Validate existing JSONL and sync status")
    group.add_argument("--write", action="store_true", help="Write compiled JSONL from case specs")
    args = parser.parse_args()

    if args.write:
        rendered = render()
        OUTPUT.write_bytes(rendered.encode("utf-8"))
        failures = validate_punarchi_file(OUTPUT)
        if failures:
            for f in failures:
                print(f, file=sys.stderr)
            return 1
        row_count = len(rendered.splitlines())
        print(f"Wrote and verified {row_count} punarchi golden vectors to {OUTPUT.relative_to(ROOT)}")
        return 0

    failures = validate_punarchi_file(OUTPUT)
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        return 1
    row_count = len(OUTPUT.read_text(encoding="utf-8").splitlines()) if OUTPUT.is_file() else 0
    print(f"punarchi golden check passed ({row_count} vectors).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
