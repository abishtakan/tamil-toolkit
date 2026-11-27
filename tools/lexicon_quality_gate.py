"""Standalone hygiene and integrity gate for organized lexicon JSONL packs and manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORGANIZED_DIR = ROOT / "target/lexicon/organized"
EXPECTED_HISTORICAL_TOTAL_ROWS = 307243

_RE_TAMIL_SCRIPT = re.compile(r"[\u0b80-\u0bff]")
_RE_WORDNET_LEXNAME = re.compile(r"^(?:noun|verb|adj|adv)\.[A-Za-z_]+$", re.IGNORECASE)
_RE_HTML_ARTIFACT = re.compile(r"&(?:nbsp|amp|lt|gt|quot);?|<!--", re.IGNORECASE)
_RE_MOJIBAKE = re.compile(r"[\u00a2\u00a3\u00a4\u00a6]")
_RE_UPPER = re.compile(r"[A-Z]")


def _split_tokens(raw: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;]", raw) if part.strip()]


def _check_jsonl_packs(organized_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    entries_files = sorted(organized_dir.rglob("entries.jsonl"))
    if not entries_files:
        failures.append({
            "pack": "<all>",
            "entry_id": "<none>",
            "field": "entries.jsonl",
            "detail": f"No entries.jsonl files found under {organized_dir}",
        })
        return failures, {"packs_checked": 0, "entries_checked": 0}

    total_entries = 0
    per_pack_stats: dict[str, dict[str, int]] = {}

    for entries_path in entries_files:
        pack_id = entries_path.parent.name
        pack_entries = 0
        # lowercased token -> {exact_casing: first_entry_id}
        domain_casings: dict[str, dict[str, str]] = {}
        register_tokens: set[str] = set()

        with entries_path.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                raw_line = line.strip()
                if not raw_line:
                    continue
                pack_entries += 1
                total_entries += 1
                entry = json.loads(raw_line)
                eid = str(entry.get("entry_id") or f"line:{line_num}")

                def _record(field: str, detail: str) -> None:
                    failures.append({
                        "pack": pack_id,
                        "entry_id": eid,
                        "field": field,
                        "detail": detail,
                    })

                hw = entry.get("headword") or ""
                if _RE_HTML_ARTIFACT.search(hw):
                    _record("headword", f"HTML entity/comment in headword: {hw!r}")
                if _RE_MOJIBAKE.search(hw):
                    _record("headword", f"Mojibake character in headword: {hw!r}")

                def _check_domain(field: str, val: str | None) -> None:
                    if not val:
                        return
                    if _RE_HTML_ARTIFACT.search(val):
                        _record(field, f"HTML entity/comment in domain: {val!r}")
                    for tok in _split_tokens(val):
                        if _RE_TAMIL_SCRIPT.search(tok):
                            _record(field, f"Tamil script in domain token: {tok!r}")
                        if _RE_WORDNET_LEXNAME.match(tok):
                            _record(field, f"Raw WordNet lexname in domain: {tok!r}")
                        domain_casings.setdefault(tok.lower(), {}).setdefault(tok, eid)

                def _check_register(field: str, val: str | None) -> None:
                    if not val:
                        return
                    for tok in _split_tokens(val):
                        if _RE_TAMIL_SCRIPT.search(tok):
                            _record(field, f"Tamil script in register token: {tok!r}")
                        if _RE_UPPER.search(tok):
                            _record(field, f"Non-lowercase register token: {tok!r}")
                        register_tokens.add(tok)

                _check_domain("domain", entry.get("domain"))
                _check_register("register", entry.get("register"))

                for s_idx, sense in enumerate(entry.get("senses") or []):
                    for text_field in ("gloss_ta", "gloss_en", "definition_ta", "definition_en"):
                        tval = sense.get(text_field)
                        if not tval:
                            continue
                        fpath = f"senses[{s_idx}].{text_field}"
                        if _RE_HTML_ARTIFACT.search(tval):
                            _record(fpath, f"HTML entity/comment in {text_field}: {tval[:120]!r}")
                        if _RE_MOJIBAKE.search(tval):
                            _record(fpath, f"Mojibake character in {text_field}: {tval[:120]!r}")
                    _check_domain(f"senses[{s_idx}].domain", sense.get("domain"))
                    _check_register(f"senses[{s_idx}].register", sense.get("register"))

        for low, casings in sorted(domain_casings.items()):
            if len(casings) > 1:
                sample_eid = next(iter(casings.values()))
                failures.append({
                    "pack": pack_id,
                    "entry_id": sample_eid,
                    "field": "domain",
                    "detail": f"Case-duplicate domain tokens for {low!r}: {sorted(casings)}",
                })

        per_pack_stats[pack_id] = {
            "entries": pack_entries,
            "distinct_domains": len(domain_casings),
            "distinct_registers": len(register_tokens),
        }

    return failures, {
        "packs_checked": len(entries_files),
        "entries_checked": total_entries,
        "packs": per_pack_stats,
    }


def _check_cleaning_audit(
    organized_dir: Path,
    *,
    expected_historical_rows: int = EXPECTED_HISTORICAL_TOTAL_ROWS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    audit_path = organized_dir / "cleaning_audit.json"
    if not audit_path.is_file():
        failures.append({
            "pack": "<audit>",
            "entry_id": "cleaning_audit.json",
            "field": "file",
            "detail": f"Missing cleaning_audit.json at {audit_path}",
        })
        return failures, {"historical_accounted_rows": None}

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    local_audit = audit.get("local")
    if not isinstance(local_audit, dict):
        if not (organized_dir / "local").exists():
            return failures, {"historical_accounted_rows": 0}
        failures.append({
            "pack": "<audit>",
            "entry_id": "cleaning_audit.json",
            "field": "local",
            "detail": "Missing 'local' track accounting in cleaning_audit.json",
        })
        return failures, {"historical_accounted_rows": None}

    total_rows = local_audit.get("total_accounted_rows")
    expected_in_audit = local_audit.get("expected_historical_csv_rows")
    per_file = local_audit.get("per_file_accounted_rows") or {}
    per_file_sum = sum(int(v) for v in per_file.values()) if isinstance(per_file, dict) else -1
    exact_flag = local_audit.get("accounting_exact") is True

    if (
        not exact_flag
        or total_rows != expected_historical_rows
        or expected_in_audit != expected_historical_rows
        or per_file_sum != expected_historical_rows
    ):
        failures.append({
            "pack": "<audit>",
            "entry_id": "cleaning_audit.json",
            "field": "local.total_accounted_rows",
            "detail": (
                f"Historical row accounting mismatch: expected={expected_historical_rows}, "
                f"total_accounted_rows={total_rows}, expected_historical_csv_rows={expected_in_audit}, "
                f"per_file_sum={per_file_sum}, accounting_exact={exact_flag}"
            ),
        })

    return failures, {"historical_accounted_rows": total_rows}


def _check_manifest(manifest_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    packs = data.get("packs") or []
    for item in packs:
        summary = item.get("summary") if isinstance(item, dict) and "summary" in item else item
        if not isinstance(summary, dict):
            continue
        pack_id = str(summary.get("pack_id") or item.get("file") or "<unknown>")
        for field in ("domains", "registers", "regions"):
            for tok in summary.get(field) or []:
                if "," in tok or ";" in tok:
                    failures.append({
                        "pack": pack_id,
                        "entry_id": "MANIFEST.json",
                        "field": field,
                        "detail": f"Non-atomic comma/semicolon-joined token in {field}: {tok!r}",
                    })
                if field in ("domains", "registers") and _RE_TAMIL_SCRIPT.search(tok):
                    failures.append({
                        "pack": pack_id,
                        "entry_id": "MANIFEST.json",
                        "field": field,
                        "detail": f"Tamil script in {field}: {tok!r}",
                    })
                if field == "domains" and _RE_WORDNET_LEXNAME.match(tok.strip()):
                    failures.append({
                        "pack": pack_id,
                        "entry_id": "MANIFEST.json",
                        "field": field,
                        "detail": f"Raw WordNet lexname in domains: {tok!r}",
                    })
        dom_casings: dict[str, set[str]] = {}
        for tok in summary.get("domains") or []:
            dom_casings.setdefault(tok.lower(), set()).add(tok)
        for low, casings in sorted(dom_casings.items()):
            if len(casings) > 1:
                failures.append({
                    "pack": pack_id,
                    "entry_id": "MANIFEST.json",
                    "field": "domains",
                    "detail": f"Case-duplicate domain tokens in MANIFEST.json for {low!r}: {sorted(casings)}",
                })

    return failures, {"manifest_packs_checked": len(packs)}


def run_quality_gate(
    organized_dir: Path = DEFAULT_ORGANIZED_DIR,
    *,
    manifest_path: Path | None = None,
    expected_historical_rows: int = EXPECTED_HISTORICAL_TOTAL_ROWS,
) -> dict[str, Any]:
    """Run all organized lexicon hygiene and accounting checks and return a report."""
    failures: list[dict[str, Any]] = []

    pack_failures, pack_summary = _check_jsonl_packs(organized_dir)
    failures.extend(pack_failures)

    audit_failures, audit_summary = _check_cleaning_audit(
        organized_dir,
        expected_historical_rows=expected_historical_rows,
    )
    failures.extend(audit_failures)

    manifest_checked = False
    manifest_summary: dict[str, Any] = {}
    if manifest_path is not None and manifest_path.is_file():
        manifest_checked = True
        m_failures, manifest_summary = _check_manifest(manifest_path)
        failures.extend(m_failures)

    return {
        "status": "pass" if not failures else "fail",
        "organized_dir": str(organized_dir),
        "manifest_checked": manifest_checked,
        "manifest_path": str(manifest_path) if manifest_path is not None else None,
        "failure_count": len(failures),
        "failures": failures,
        **pack_summary,
        **audit_summary,
        **manifest_summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--organized-dir",
        type=Path,
        default=DEFAULT_ORGANIZED_DIR,
        help="Organized lexicon directory (default: target/lexicon/organized)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional compiled MANIFEST.json path to validate if present",
    )
    parser.add_argument(
        "--expected-historical-rows",
        type=int,
        default=EXPECTED_HISTORICAL_TOTAL_ROWS,
        help=f"Expected historical CSV total row count (default: {EXPECTED_HISTORICAL_TOTAL_ROWS})",
    )
    args = parser.parse_args(argv)

    report = run_quality_gate(
        args.organized_dir,
        manifest_path=args.manifest,
        expected_historical_rows=args.expected_historical_rows,
    )
    if report["status"] == "pass":
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0

    preview = dict(report)
    if len(report["failures"]) > 50:
        preview["failures_truncated"] = f"showing 50 of {len(report['failures'])}"
        preview["failures"] = report["failures"][:50]
    print(json.dumps(preview, ensure_ascii=True, indent=2), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
