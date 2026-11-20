"""Deterministic coverage selection and fail-closed L2 acceptance."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import tomllib

import tools.lexicon as lexicon
from tools.lexicon import (LexiconError, MANIFEST, NAMESPACE, ROOT, SOURCE, _checked_files,
    allocate_id, atomic_json, digest, json_text, native_inspect, safe_output, source_rows)
from tools.lexicon_tables import is_intentional_control

AUDIT = ROOT / "docs/audits/lexicon-2026-11-13.metrics.json"
_DEFAULT_MANIFEST = MANIFEST
SECONDARIES = ["secondary_" + s + ".csv" for s in ["archaic_literary_terms", "dialect_colloquialisms", "phrases_mwes", "proper_names_toponyms", "scientific_taxa", "specialized_technical_terms", "transliterations_loanwords"]]


def _issues(row, native=True):
    issues = set()
    for text in row.values():
        if not text:
            continue
        if text != text.strip():
            issues.add("outer_whitespace_cells")
        if chr(0xFFFD) in text:
            issues.add("replacement_character_cells")
        for cp in {ord(c) for c in text}:
            if is_intentional_control(cp):
                issues.add(f"control_U+{cp:04X}")
        if native and not native_inspect(text)["is_nfc"]:
            issues.add("non_nfc_cells")
    return issues


@lru_cache(maxsize=2)
def _scan(source_name, signature):
    source = Path(source_name)
    is_actual = source.resolve() == SOURCE.resolve()
    audit_locs = defaultdict(lambda: defaultdict(set))
    audit_files = {}
    audit_runtime_disagreements = set()
    audit_runtime_rows = None
    if is_actual:
        # Actual source mode uses the frozen audit's bounded per-class locators
        # (truncated issue_examples) for FR-019 class coverage without full raw-cell
        # linguistic adjudication; this never certifies raw unparsed Unicode.
        audit = json.loads(AUDIT.read_text(encoding="utf-8-sig"))
        if audit.get("source_checksums_match") is not True:
            raise LexiconError("frozen audit report does not confirm source checksums")
        audit_files = audit.get("files", {})
        if set(audit_files) != {name for name, _ in signature}:
            raise LexiconError("frozen audit report file set differs from pinned source")
        for name, checksum in signature:
            item = audit_files[name]
            path = source / name
            if item.get("sha256") != checksum or item.get("bytes") != path.stat().st_size:
                raise LexiconError(f"frozen audit report disagrees with pinned source: {name}")
            covered = set()
            for issue, examples in item.get("issue_examples", {}).items():
                for example in examples:
                    if issue == "control_or_format_cells":
                        codes = {
                            f"control_U+{ord(ch):04X}"
                            for ch in example.get("value", "")
                            if is_intentional_control(ord(ch))
                        }
                        if not codes:
                            raise LexiconError(
                                f"frozen audit example lacks control scalar in {name}:{example.get('record')}"
                            )
                    else:
                        codes = {issue}
                    audit_locs[name][example["record"]].update(codes)
                    covered.update(codes)
            expected_classes = {
                k for k, v in item.get("unicode_issues", {}).items()
                if v > 0 and k != "control_or_format_cells"
            }
            missing = expected_classes - covered
            if missing:
                raise LexiconError(
                    f"frozen audit issue_examples missing observed classes in {name}: {sorted(missing)}"
                )
        runtime_comp = audit.get("runtime_comparison", {})
        audit_runtime_rows = runtime_comp.get("rows")
        audit_runtime_disagreements = {
            f"count:{k}" for k, v in runtime_comp.get("disagreement_counts", {}).items() if v > 0
        }
    rows, by_file, homographs, all_issues, file_meta = {}, defaultdict(list), defaultdict(list), set(), {}
    for name, checksum in signature:
        path = source / name
        snapshot = allocate_id("snap", NAMESPACE, checksum)
        if path.suffix != ".csv":
            file_meta[name] = {
                "snapshot_id": snapshot,
                "relative_path": name,
                "byte_length": path.stat().st_size,
                "sha256": checksum,
                "media_type": "application/octet-stream",
                "logical_row_count": None,
            }
            continue
        row_count = 0
        unseen_audit_ordinals = set(audit_locs[name]) if is_actual else set()
        for ordinal, start, end, row_hash, row in source_rows(path):
            row_count += 1
            unseen_audit_ordinals.discard(ordinal)
            rec = {"record_id": allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{row_hash}"), "snapshot_id": snapshot,
                "file": name, "ordinal": ordinal, "raw_row_sha256": row_hash, "purposes": [], "evidence_only": False}
            issues = set(audit_locs[name][ordinal]) if is_actual else _issues(row)
            info = {"record": rec, "issues": issues, "word_id": row.get("word_id"), "legacy": next(iter(row.values())),
                "physical_line_start": start, "physical_line_end": end}
            if name == "primary_lemmas.csv":
                report = native_inspect(row["headword_ta"])
                invalid = any(x["classification"] == "other" and any(0x0B80 <= ord(c) <= 0x0BDF for c in x["text"]) for x in report["letters"])
                if invalid:
                    issues.add("invalid_orthography")
                info.update(headword=row["headword_ta"], verb=row.get("part_of_speech") == "VERB")
                homographs[row["headword_ta"]].append(rec["record_id"])
            elif name == "primary_meanings.csv":
                text = row.get("definition_en", "") or row.get("meaning_en", "")
                numbered = bool(re.search(r"\b1\.\s", text) and re.search(r"\b2\.\s", text))
                mixed = any(0x0B80 <= ord(c) <= 0x0BFF for c in text) and any(c.isascii() and c.isalpha() for c in text)
                info["mixed"] = numbered or mixed
            elif name == "primary_relationships.csv":
                info.update(source_id=row["source_word_id"], target_id=row["target_word_id"])
            elif name == "unified_master_30col.csv":
                text = row["headword_ta"]
                report = native_inspect(text)
                # Thin aggregation of native letter duration results matches the
                # existing audit methodology; no duration rules live in Python.
                from tamil_toolkit import baseline_maathirai
                current = sum(baseline_maathirai(x["text"]) for x in report["letters"])
                mismatch = False
                for field, expected in [("grapheme_count", report["ezhuthu_count"]), ("matra_count", current)]:
                    try:
                        different = float(row[field]) != expected
                    except (ValueError, KeyError):
                        different = True
                    if different:
                        issues.add("count:" + field)
                        mismatch = True
                if mismatch:
                    if "\u0b95\u0bcd\u0bb7" in text:
                        issues.add("count_reason:ksha_tailoring")
                    if "\u0bb6\u0bcd\u0bb0\u0bc0" in text:
                        issues.add("count_reason:shri_ligature")
                    if any(x["classification"] == "other" and any(0x0B80 <= ord(c) <= 0x0BDF for c in x["text"]) for x in report["letters"]):
                        issues.add("count_reason:invalid_orthography")
            elif name in SECONDARIES:
                # FR-019 coverage sampling tags only; never implies regional attestation or scope approval.
                info["technical_mwe"] = name == "secondary_specialized_technical_terms.csv" and " " in row.get("term_ta", "")
                region = row.get("region_dialect", "")
                info["regional_jaffna"] = region == "Jaffna"
                info["regional_tn"] = region in {"Kongu", "Madras", "Madras Baashai", "Madurai", "Nellai"}
            all_issues.update(issues)
            rows[rec["record_id"]] = info
            by_file[name].append(rec["record_id"])
        if is_actual:
            if audit_files[name].get("rows") != row_count:
                raise LexiconError(f"frozen audit row count differs from pinned source: {name}")
            if unseen_audit_ordinals:
                raise LexiconError(f"frozen audit issue_examples reference missing ordinals in {name}: {sorted(unseen_audit_ordinals)}")
        file_meta[name] = {
            "snapshot_id": snapshot,
            "relative_path": name,
            "byte_length": path.stat().st_size,
            "sha256": checksum,
            "media_type": "text/csv",
            "logical_row_count": row_count + 1,
        }
    if is_actual:
        if audit_runtime_rows is not None and "unified_master_30col.csv" in file_meta:
            if audit_runtime_rows != file_meta["unified_master_30col.csv"]["logical_row_count"] - 1:
                raise LexiconError("frozen audit runtime_comparison row count differs from pinned source")
        missing_runtime = audit_runtime_disagreements - all_issues
        if missing_runtime:
            raise LexiconError(f"frozen audit runtime disagreement classes missing from scan: {sorted(missing_runtime)}")
    return rows, by_file, homographs, all_issues, file_meta


def _catalog(source):
    source = Path(source).resolve()
    manifest_path = None
    if source == SOURCE.resolve():
        manifest_path = MANIFEST if MANIFEST != _DEFAULT_MANIFEST else lexicon.MANIFEST
    source, paths = _checked_files(source, manifest_path=manifest_path)
    signature = tuple((p.name, digest(p)) for p in paths if p.is_file())
    return signature, _scan(str(source), signature)


def _coverage(chosen, rows, homographs):
    primary = [r for r in chosen if rows[r]["record"]["file"] == "primary_lemmas.csv"]
    secondary = {name: sum(rows[r]["record"]["file"] == name for r in chosen) for name in SECONDARIES}
    complete = [ids for ids in homographs.values() if len(ids) > 1 and set(ids) <= chosen]
    cov = {"homograph_spellings": len(complete), "homograph_entries": sum(map(len, complete)),
        "verbs": sum(rows[r].get("verb", False) for r in primary),
        "mixed_sense_records": sum(rows[r].get("mixed", False) for r in chosen),
        "technical_mwes": sum(rows[r].get("technical_mwe", False) for r in chosen),
        "regional_tn": sum(rows[r].get("regional_tn", False) for r in chosen),
        "regional_jaffna": sum(rows[r].get("regional_jaffna", False) for r in chosen),
        "audit_issue_classes": sorted(set().union(*(rows[r]["issues"] for r in chosen)))}
    cov["regional_total"] = cov["regional_tn"] + cov["regional_jaffna"]
    return {"selected_primary_entries": len(primary), "selected_secondary_by_file": secondary, "coverage": cov}


def select_pilot(source=SOURCE):
    signature, (rows, by_file, homographs, issues, _) = _catalog(source)
    chosen, purposes = set(), defaultdict(set)
    def add(rid, purpose):
        chosen.add(rid)
        purposes[rid].add(purpose)
    primary = sorted(by_file["primary_lemmas.csv"])
    for group in sorted((sorted(ids) for ids in homographs.values() if len(ids) > 1), key=lambda ids: ids[0])[:10]:
        for rid in group:
            add(rid, "homograph_group")
    for rid in [r for r in primary if rows[r].get("verb")][:10]:
        add(rid, "verb")
    for rid in sorted(by_file["primary_meanings.csv"]):
        if rows[rid].get("mixed") and sum("mixed_sense" in p for p in purposes.values()) < 10:
            add(rid, "mixed_sense")
    for issue in sorted(issues):
        candidates = sorted(r for r in rows if issue in rows[r]["issues"])
        if candidates:
            add(candidates[0], "audit:" + issue)
    for name in SECONDARIES:
        for rid in sorted(by_file[name])[:20]:
            add(rid, "secondary_minimum")
    for key in ["technical_mwe", "regional_tn", "regional_jaffna"]:
        for rid in sorted(r for r in rows if rows[r].get(key))[:10 if key == "technical_mwe" else 5]:
            add(rid, key)
    needed_words = {rows[r]["word_id"] for r in chosen if rows[r]["record"]["file"] in {"primary_meanings.csv", "unified_master_30col.csv"}}
    for rid in primary:
        if rows[rid]["word_id"] in needed_words:
            add(rid, "linked_primary")
    for rid in primary:
        if sum(rows[r]["record"]["file"] == "primary_lemmas.csv" for r in chosen) >= 100:
            break
        add(rid, "primary_minimum")
    for group in homographs.values():
        if len(group) > 1 and set(group) & chosen:
            for rid in group:
                add(rid, "homograph_group")
    word_ids = {rows[r]["word_id"] for r in chosen if rows[r]["record"]["file"] == "primary_lemmas.csv"}
    for name in ["primary_meanings.csv", "unified_master_30col.csv", "primary_relationships.csv"]:
        for rid in by_file[name]:
            info = rows[rid]
            if info.get("word_id") in word_ids or name == "primary_relationships.csv" and {info["source_id"], info["target_id"]} & word_ids:
                add(rid, "linked_evidence")
    records = []
    for rid in sorted(chosen):
        rec = deepcopy(rows[rid]["record"])
        rec["purposes"] = sorted(purposes[rid])
        if rec["file"] == "primary_relationships.csv":
            rec["evidence_only"] = not {rows[rid]["source_id"], rows[rid]["target_id"]} <= word_ids
        records.append(rec)
    return {"schema_version": 1, "selection_version": "1", "files": [{"file": name, "sha256": sha} for name, sha in signature],
        "summary": _coverage(chosen, rows, homographs), "records": records}


def write_selection(path, selection, source_root=None):
    path = safe_output(path, source_root)
    lines = []
    def emit(table, value):
        scalars = {k:v for k,v in value.items() if not isinstance(v, dict) and not (isinstance(v, list) and v and isinstance(v[0], dict))}
        if table:
            lines.append("[" + table + "]")
        for key, item in scalars.items():
            lines.append(f"{json_text(key)} = {json_text(item)}")
        for key, item in value.items():
            if isinstance(item, dict):
                emit((table + "." if table else "") + json_text(key), item)
        for key, item in value.items():
            if isinstance(item, list) and item and isinstance(item[0], dict):
                for row in item:
                    lines.append("[[" + (table + "." if table else "") + json_text(key) + "]]")
                    for col, cell in row.items():
                        lines.append(f"{json_text(col)} = {json_text(cell)}")
    emit("", selection)
    content = "\n".join(lines) + "\n"
    if path.exists() and path.read_text(encoding="ascii") != content:
        raise LexiconError("existing pilot selection conflicts")
    if tomllib.loads(content) != selection:
        raise LexiconError("selection cannot round-trip through TOML")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="ascii", newline="\n")


def _report_output(workspace, output, inputs=()):
    if output is not None:
        output = safe_output(output)
        ws = Path(workspace).resolve()
        if output == ws or output.is_relative_to(ws) or ws.is_relative_to(output):
            raise LexiconError("report output overlaps workspace")
        if any(output == Path(p).resolve() for p in inputs if p is not None):
            raise LexiconError("report output overlaps an input file")
    return output


def pilot(workspace, selection, output=None, source=None):
    from tools.lexicon_tables import read_rows
    workspace = Path(workspace)
    output = _report_output(workspace, output, () if isinstance(selection, dict) else [selection])
    if not isinstance(selection, dict):
        selection = tomllib.loads(Path(selection).read_text(encoding="ascii"))
    if source is None:
        files = selection.get("files", [])
        if (
            len(files) == 12
            and all(
                isinstance(r.get("file"), str)
                and Path(r["file"]).name == r["file"]
                and (SOURCE / r["file"]).is_file()
                and digest(SOURCE / r["file"]) == r.get("sha256")
                for r in files
            )
        ):
            source = SOURCE
        else:
            source = _SOURCE_HINTS.get(json_text(files), SOURCE)
    findings = []
    def issue(code, reason, subject=""):
        findings.append({"code": code, "severity": "error", "subject_id": subject, "reason": reason})
    signature, (rows, by_file, homographs, all_issues, file_meta) = _catalog(source)
    if [{"file": n, "sha256": h} for n,h in signature] != selection["files"]:
        issue("SOURCE_HASH_MISMATCH", "Frozen file digests differ from selection")
    snapshots_path = workspace / "snapshots.csv"
    if not snapshots_path.is_file():
        issue("MISSING_SNAPSHOT", "Workspace snapshots.csv is missing")
    else:
        snaps_by_path = {}
        seen_snap_ids = set()
        for row in read_rows(snapshots_path):
            rel = row["relative_path"]
            sid = row["snapshot_id"]
            if rel in snaps_by_path or sid in seen_snap_ids:
                issue("DUPLICATE_SNAPSHOT", "Duplicate snapshot path or id in snapshots.csv", rel)
            else:
                snaps_by_path[rel] = row
            seen_snap_ids.add(sid)
        for name, expected_snap in file_meta.items():
            snap = snaps_by_path.get(name)
            if snap is None:
                issue("MISSING_SNAPSHOT", "Source file missing from snapshots.csv", name)
            elif any(snap[k] != expected_snap[k] for k in ("snapshot_id", "byte_length", "sha256", "media_type", "logical_row_count")):
                issue("SNAPSHOT_MISMATCH", "Snapshot row metadata differs from source file", name)
        for name in sorted(set(snaps_by_path) - set(file_meta)):
            issue("UNEXPECTED_SNAPSHOT", "Snapshot entry does not correspond to a source file", name)
    chosen = {r["record_id"] for r in selection["records"]}
    if len(chosen) != len(selection["records"]) or chosen - rows.keys():
        issue("INVALID_SELECTION_RECORD", "Duplicate or unknown selected record")
    chosen &= rows.keys()
    summary = _coverage(chosen, rows, homographs)
    cov = summary["coverage"]
    if summary["selected_primary_entries"] < 100:
        issue("PILOT_MIN_PRIMARY", "At least 100 primary entries required")
    if any(v < 20 for v in summary["selected_secondary_by_file"].values()):
        issue("PILOT_MIN_SECONDARY", "At least 20 records per secondary dataset required")
    for key, minimum in [("homograph_spellings",10),("verbs",10),("mixed_sense_records",10),("technical_mwes",10)]:
        if cov[key] < minimum:
            issue("PILOT_MIN_" + key.upper(), "Coverage minimum not met")
    if cov["regional_total"] < 10 or not cov["regional_tn"] or not cov["regional_jaffna"]:
        issue("PILOT_MIN_REGIONAL", "Regional sample must span TN and Jaffna")
    for ids in homographs.values():
        if len(ids) > 1 and set(ids) & chosen and not set(ids) <= chosen:
            issue("PILOT_INCOMPLETE_HOMOGRAPH_GROUP", "All homograph entries must be retained")
    for missing_class in sorted(all_issues - set(cov["audit_issue_classes"])):
        issue("PILOT_MISSING_AUDIT_CLASS", f"Observed audit class missing: {missing_class}", missing_class)
    words = {rows[r]["word_id"] for r in chosen if rows[r]["record"]["file"] == "primary_lemmas.csv"}
    for name, code in [("primary_meanings.csv", "PILOT_MISSING_PRIMARY_MEANINGS"),("primary_relationships.csv", "PILOT_MISSING_PRIMARY_RELATIONSHIPS")]:
        for rid in by_file[name]:
            info = rows[rid]
            needed = info.get("word_id") in words if name == "primary_meanings.csv" else bool({info["source_id"],info["target_id"]} & words)
            if needed and rid not in chosen:
                issue(code, "Linked source evidence missing", rid)
    ledger, ledger_counts = {}, Counter()
    for row in read_rows(workspace / "source_records.csv"):
        if row["record_id"] in chosen:
            ledger[row["record_id"]] = row
            ledger_counts[row["record_id"]] += 1
    dispositions = defaultdict(list)
    for row in read_rows(workspace / "dispositions.csv"):
        if row["record_id"] in chosen:
            dispositions[row["record_id"]].append(row)
    targets = Counter(r["record_id"] for r in read_rows(workspace / "record_targets.csv"))
    for rid in sorted(chosen):
        if ledger_counts[rid] > 1:
            issue("DUPLICATE_SOURCE_RECORD", "Selected record occurs more than once", rid)
        if rid not in ledger or any(ledger[rid][key] != rows[rid]["record"][key] for key in ["snapshot_id","ordinal","raw_row_sha256"]):
            issue("MISSING_SOURCE_RECORD", "Selected locator missing or changed", rid)
        elif any(ledger[rid][key] != rows[rid][key] for key in ["physical_line_start", "physical_line_end"]):
            issue("INVALID_SOURCE_SPAN", "Physical source span differs from frozen evidence", rid)
        ds = dispositions[rid]
        if not ds:
            issue("MISSING_DISPOSITION", "Selected record has no disposition", rid)
        elif len(ds) != 1:
            issue("DUPLICATE_DISPOSITION", "Selected record has multiple dispositions", rid)
        elif ds[0]["structural_state"] != "validated":
            issue("PENDING_DISPOSITION", "Disposition is not structurally validated", rid)
        elif ds[0]["disposition"] in {"quarantined", "excluded"} and targets[rid]:
            issue("QUARANTINED_TARGET_PRESENT", "Unapproved disposition has approved targets", rid)
        elif ds[0]["disposition"] in {"mapped", "merged", "split"} and targets[rid] < (2 if ds[0]["disposition"] == "split" else 1):
            issue("MISSING_TARGET", "Disposition target cardinality failed", rid)
    for row in read_rows(workspace / "findings.csv"):
        if row["record_id"] in chosen and row["severity"] == "error" and row["status"] == "open" and any(k in row["issue_code"].upper() for k in ["ACCOUNT", "REFERENCE", "DANGLING", "DISPOSITION"]):
            issue("UNRESOLVED_BLOCKING_FINDING", "Open structural accounting finding", row["record_id"])
    stage_report = json.loads((workspace / "stage-report.json").read_text(encoding="utf-8"))
    fdisps = {r["snapshot_id"] for r in stage_report.get("file_dispositions", []) if r["disposition"] == "quarantined"}
    for name, checksum in signature:
        if not name.endswith(".csv") and allocate_id("snap", NAMESPACE, checksum) not in fdisps:
            issue("MISSING_FILE_DISPOSITION", "Derived artifact lacks quarantine disposition")
    report = {"schema_version":1,"command":"pilot","mode":"structural","selection_version":selection["selection_version"],
        "input_sha256":hashlib.sha256(json_text(selection).encode("ascii")).hexdigest(),"summary":summary,
        "selected_records":len(chosen),"eligible_assertions":release_guard(workspace)["eligible_assertions"],"l2_structural_accepted":not findings,
        "l3_pack_eligible":False,"runtime_verified":None,"findings":sorted(findings,key=json_text)}
    if output:
        atomic_json(output, report, source)
    return report


_SOURCE_HINTS = {}
_select = select_pilot
def select_pilot(source=SOURCE):
    result = _select(source)
    _SOURCE_HINTS[json_text(result["files"])] = Path(source)
    return result


def release_guard(workspace, pack="core", output=None):
    from tools.lexicon_packs import validate_release
    return validate_release(workspace, pack=pack, output=output)
