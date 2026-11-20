"""Reconcile historical Wiktionary-labelled spellings with pinned official pages.

Historical text is never used as the definition of a recovered candidate.
This tool creates evidence/reconciliation artifacts, not acceptance decisions.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import urllib.parse

from tools.audit_lexicon_readiness import ROOT, collect, digest, rows
from tools.lexicon_wiktionary_bulk import _api_get_json, parse_wiktionary_page


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return
    path.write_bytes(encoded)


def verify_page(page: dict):
    if any(type(page.get(key)) is not int or page[key] <= 0 for key in ("pageid", "revid")):
        raise ValueError("Invalid pinned page identity")
    actual = hashlib.sha256(page["wikitext"].encode("utf-8")).hexdigest()
    if actual != page["wikitext_sha256"]:
        raise ValueError("Page wikitext digest mismatch")
    for key in ("permalink_url", "history_url"):
        url = urllib.parse.urlsplit(page[key])
        query = urllib.parse.parse_qs(url.query)
        if url.scheme != "https" or url.netloc != "en.wiktionary.org" or url.path != "/w/index.php":
            raise ValueError("Unsafe source attribution URL")
        if key == "permalink_url" and query.get("oldid") != [str(page["revid"])]:
            raise ValueError("Source attribution revision mismatch")
        if key == "history_url" and query.get("action") != ["history"]:
            raise ValueError("Source attribution history mismatch")


def reconcile_records(candidates, pages, *, parser=parse_wiktionary_page, check_native=False):
    records = []
    entries = []
    seen = set()
    for candidate in sorted(candidates, key=lambda row: row["headword"]):
        title = candidate["headword"]
        if title in seen:
            raise ValueError("Duplicate gap candidate")
        seen.add(title)
        row = {**candidate, "historical_claims_approved": False}
        page = pages.get(title)
        if page is None:
            row.update(status="missing_from_snapshot", blocker_counts={})
        else:
            if page["title"] != title:
                raise ValueError("Source page title mismatch; alias resolution requires separate evidence")
            verify_page(page)
            parsed = parser(page, check_native=check_native)
            row.update(
                status="recoverable_candidate" if parsed["entries"] else "source_present_parser_blocked",
                source={k: page[k] for k in ("pageid", "revid", "wikitext_sha256", "permalink_url", "history_url")},
                blocker_counts=dict(sorted(Counter(e["reason_code"] for e in parsed["exclusions"]).items())),
                extracted_entry_ids=[e["entry_id"] for e in parsed["entries"]],
                extracted_senses=sum(len(e["senses"]) for e in parsed["entries"]),
            )
            entries.extend(parsed["entries"])
        records.append(row)
    return {
        "records": records,
        "status_counts": dict(sorted(Counter(row["status"] for row in records).items())),
        "candidate_entries": entries,
        "candidate_senses": sum(len(e["senses"]) for e in entries),
    }


def historical_candidates(package: Path, readiness_path: Path):
    baseline = json.loads(readiness_path.read_text(encoding="utf-8"))
    now = collect(package)
    for key in ("frozen_source_files", "packs", "recovered_package"):
        if now[key] != baseline[key]:
            raise ValueError(f"Readiness baseline input mismatch: {key}; preserve the initial queue before changing inputs")
    usable = set()
    for relative in ("lexicon/dictionary", "lexicon/packs/names_taxa", "lexicon/packs/regional"):
        path = ROOT / relative
        assertions = {r["assertion_id"]: r for r in rows(path / "assertions.csv")}
        usable.update(json.loads(assertions[r["text_assertion_id"]]["value_json"]) for r in rows(path / "forms.csv") if r["representation"] == "written")
    grouped = defaultdict(lambda: {"word_ids": set(), "meaning_ids": set(), "historical_pos_labels": set()})
    database = package / "databases/utlkd_primary.sqlite"
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        for title, wid, mid, pos in connection.execute(
            "SELECT w.headword_ta,w.word_id,m.meaning_id,w.part_of_speech "
            "FROM word_meanings m JOIN tamil_words w USING(word_id) WHERE m.notes IN (?,?)",
            ("Sense verified from Wiktionary dictionary entry.", "Additional sense verified and deduplicated from Wiktionary."),
        ):
            if title not in usable:
                grouped[title]["word_ids"].add(wid)
                grouped[title]["meaning_ids"].add(mid)
                grouped[title]["historical_pos_labels"].add(pos)
    expected = baseline["recovered_package"]["combined_meaning_label_groups"]["Wiktionary_label"]["exact_absent_usable"]
    if len(grouped) != expected:
        raise ValueError("Historical candidate count differs from readiness report")
    return [{"headword": title, **{key: sorted(value) for key, value in group.items()}} for title, group in sorted(grouped.items())]


def load_snapshot(snapshot_dir: Path):
    manifest = json.loads((snapshot_dir / "snapshots_manifest.json").read_text(encoding="utf-8"))
    path = snapshot_dir / "pages.jsonl.gz"
    if digest(path)["sha256"] != manifest["pages_jsonl_gz_sha256"]:
        raise ValueError("Pinned snapshot digest mismatch")
    pages = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            page = json.loads(line)
            if page["title"] in pages:
                raise ValueError("Duplicate title in pinned snapshot")
            pages[page["title"]] = page
    return pages, manifest


def verify_capture(directory: Path):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    verify_raw_files(directory, manifest["raw_files"])
    if digest(directory / "pages.json") != manifest["pages_file"]:
        raise ValueError("Cached source pages digest mismatch")
    if "pages_jsonl_gz_sha256" in manifest:
        path = directory / "pages.jsonl.gz"
        if digest(path)["sha256"] != manifest["pages_jsonl_gz_sha256"]:
            raise ValueError("Cached compressed source pages digest mismatch")
        if hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest() != manifest["pages_uncompressed_sha256"]:
            raise ValueError("Cached uncompressed source pages digest mismatch")
    return manifest


def verify_raw_files(directory: Path, expected: dict):
    for filename, fingerprint in expected.items():
        if re.fullmatch(r"batch-[0-9]{3,}\.json", filename) is None:
            raise ValueError("Invalid cached source batch filename")
        if not (directory / filename).is_file() or digest(directory / filename) != fingerprint:
            raise ValueError("Cached source batch digest mismatch")
    if {p.name for p in directory.glob("batch-*.json")} != set(expected):
        raise ValueError("Unregistered cached source batches; no hash evidence")


def fetch_missing(titles: list[str], directory: Path):
    """Capture exact-title API results without following or silently merging redirects."""
    directory.mkdir(parents=True, exist_ok=True)
    previous_manifest = directory / "manifest.json"
    checkpoint_path = directory / "capture-checkpoint.json"
    checkpoint_files = {}
    if previous_manifest.exists():
        previous = verify_capture(directory)
        if sorted(previous["title_outcomes"]) != sorted(titles):
            raise ValueError("Source capture belongs to a different title queue")
    elif checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint["requested_titles"] != titles:
            raise ValueError("Partial source capture belongs to a different title queue")
        verify_raw_files(directory, checkpoint["raw_files"])
        checkpoint_files = dict(checkpoint["raw_files"])
    elif any(directory.glob("batch-*.json")):
        raise ValueError("Cached source batches have no manifest or checkpoint hash evidence")
    records = {}
    outcomes = {}
    raw_files = checkpoint_files
    capture_dates = set()
    for start in range(0, len(titles), 25):
        batch = titles[start:start + 25]
        path = directory / f"batch-{start // 25:03d}.json"
        if path.exists():
            saved = json.loads(path.read_text(encoding="utf-8"))
            if saved["requested_titles"] != batch:
                raise ValueError("Existing source batch belongs to a different title queue")
        else:
            payload = _api_get_json({
                "action": "query", "prop": "revisions", "titles": "|".join(batch),
                "rvprop": "ids|timestamp|sha1|user|content", "rvslots": "main",
                "format": "json", "formatversion": "2",
            }, retries=1)
            if "error" in payload or "query" not in payload:
                raise ValueError("Official API query failed; no missing-page outcome inferred")
            saved = {"requested_titles": batch, "fetched_at_utc": datetime.now(timezone.utc).isoformat(), "api_response": payload}
            write_json(path, saved)
        raw_files[path.name] = digest(path)
        # A partial fetch is reusable only with a fingerprinted checkpoint.
        if not previous_manifest.exists():
            write_json(checkpoint_path, {"requested_titles": titles, "raw_files": raw_files})
        capture_dates.add(saved["fetched_at_utc"][:10])
        payload = saved["api_response"]
        by_title = {p["title"]: p for p in payload["query"]["pages"]}
        aliases = {a["from"]: a["to"] for a in payload["query"].get("normalized", [])}
        for title in batch:
            if title in aliases and aliases[title] != title:
                outcomes[title] = {"status": "api_title_normalization_requires_review", "api_title": aliases[title]}
                continue
            page = by_title.get(title)
            if page is None:
                raise ValueError("API omitted an exact requested title")
            if page.get("missing") or page.get("invalid"):
                outcomes[title] = {"status": "api_page_missing" if page.get("missing") else "api_title_invalid"}
                continue
            revisions = page.get("revisions") or []
            if not revisions or not isinstance(revisions[0].get("slots", {}).get("main", {}).get("content"), str):
                outcomes[title] = {"status": "api_revision_unavailable"}
                continue
            rev = revisions[0]
            text = rev["slots"]["main"]["content"]
            qtitle = urllib.parse.quote(title.replace(" ", "_"), safe="")
            record = {
                "title": title, "pageid": page["pageid"], "revid": rev["revid"],
                "parentid": rev.get("parentid"), "revision_timestamp": rev["timestamp"],
                "user": rev.get("user", ""), "sha1": rev.get("sha1", ""), "categories": [],
                "wikitext": text, "wikitext_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "permalink_url": f"https://en.wiktionary.org/w/index.php?title={qtitle}&oldid={rev['revid']}",
                "history_url": f"https://en.wiktionary.org/w/index.php?title={qtitle}&action=history",
            }
            verify_page(record)
            records[title] = record
            outcomes[title] = {"status": "api_revision_pinned", "revid": rev["revid"]}
    write_json(directory / "pages.json", [records[key] for key in sorted(records)])
    encoded = "".join(json.dumps(records[key], ensure_ascii=True, sort_keys=True) + "\n" for key in sorted(records)).encode("utf-8")
    (directory / "pages.jsonl.gz").write_bytes(gzip.compress(encoded, mtime=0))
    manifest = {"schema_version": 1, "api_endpoint": "https://en.wiktionary.org/w/api.php", "raw_files": raw_files,
                "pages_file": digest(directory / "pages.json"), "requested_title_count": len(titles),
                "pages_jsonl_gz_sha256": digest(directory / "pages.jsonl.gz")["sha256"],
                "pages_uncompressed_sha256": hashlib.sha256(encoded).hexdigest(),
                "snapshot_date": max(capture_dates, default=""), "capture_dates": sorted(capture_dates),
                "total_fetched_pages": len(records),
                "title_outcomes": outcomes, "license_evidence": "https://en.wiktionary.org/wiki/Wiktionary:Copyrights",
                "reuse_note": "Fresh revision evidence only; historical claims remain unapproved; no automatic acceptance."}
    write_json(directory / "manifest.json", manifest)
    return records, manifest


def validate_supplemental_directory(directory: Path, snapshot_dir: Path) -> Path:
    supplement = directory.resolve()
    allowed = (ROOT / "data/sources").resolve()
    protected = (snapshot_dir.resolve(), (allowed / "enwiktionary-tamil").resolve(), (allowed / "tamil-lexicon").resolve())
    if not supplement.is_relative_to(allowed) or supplement == allowed or any(supplement.is_relative_to(path) for path in protected):
        raise ValueError("Supplement must be a separate directory beneath data/sources")
    return supplement


def stage_candidates(reconciliation: dict, supplemental_dir: Path, output: Path):
    """Validate a separate candidate pack; never replace the current usable packs."""
    from tools.lexicon_cldf import export_cldf
    from tools.lexicon_packs import promote, validate_canonical_dir
    from tools.lexicon_tables import read_rows
    from tools.lexicon_wiktionary_bulk import _build_bulk_pack_workspace

    if not reconciliation["candidate_entries"]:
        raise ValueError("No source-backed candidates to stage")
    manifest = json.loads((supplemental_dir / "manifest.json").read_text(encoding="utf-8"))
    verify_capture(supplemental_dir)
    if manifest != reconciliation["supplemental_manifest"]:
        raise ValueError("Supplemental source manifest mismatch")
    source_pages = {page["title"]: page for page in json.loads((supplemental_dir / "pages.json").read_text(encoding="utf-8"))}
    for entry in reconciliation["candidate_entries"]:
        if entry.get("pack_id") != "core" or entry.get("headword_nfc_normalized"):
            raise ValueError("This staging profile supports only exact, non-normalized core candidates")
        page = source_pages.get(entry["headword"])
        if page is None:
            raise ValueError("Candidate is outside this supplemental source capture")
        verify_page(page)
        if entry not in parse_wiktionary_page(page, check_native=True)["entries"]:
            raise ValueError("Candidate differs from verified supplemental source extraction")
    workspace = output / "candidate-workspace"
    canonical = output / "candidate-canonical"
    cldf = output / "candidate-cldf"
    if any(path.exists() for path in (workspace, canonical, cldf)):
        raise ValueError("Candidate output already exists; use a fresh reconciliation output directory")
    summary = _build_bulk_pack_workspace(
        "core", [(e["headword"], e) for e in reconciliation["candidate_entries"]],
        manifest=manifest, workspace_dir=workspace,
        legalcode_src=ROOT / "data/sources/enwiktionary-tamil/notices/cc_by_sa_4_0_legalcode.txt",
        snapshot_date=manifest["snapshot_date"],
    )
    from tools.lexicon_tables import write_rows
    source_rows = list(read_rows(workspace / "sources.csv", "sources"))
    for source in source_rows:
        source["url_json"] = "https://en.wiktionary.org/w/api.php"
        locator = json.loads(source["locator_json"])
        locator.update(acquisition="exact_title_revision_query", capture_manifest_sha256=digest(supplemental_dir / "manifest.json")["sha256"])
        source["locator_json"] = json.dumps(locator, ensure_ascii=True, sort_keys=True)
    write_rows(workspace / "sources.csv", "sources", source_rows)
    promoted = promote(workspace, pack="core", output=canonical)
    findings = validate_canonical_dir(canonical)
    if findings:
        raise ValueError(f"Candidate canonical validation failed: {findings}")
    exported = export_cldf(canonical, "core", cldf, check=True)
    if not exported["cldf_valid"] or not exported["roundtrip_ok"]:
        raise ValueError("Candidate CLDF validation or roundtrip failed")
    decisions = list(read_rows(canonical / "decisions.csv", "decisions"))
    if any(r["outcome"] != "accepted_auto_source" or r["actor_type"] != "automated" for r in decisions):
        raise ValueError("Unexpected human or non-source candidate acceptance")
    proof = {
        "schema_version": 1, "scope": "isolated candidate pack; current runtime packs unchanged",
        "workspace_summary": summary,
        "promoted_entries": promoted["entry_count"], "promoted_senses": promoted["sense_count"],
        "dataset_version": promoted["dataset_version"], "manifest_sha256": promoted["manifest_sha256"],
        "canonical_findings": findings, "cldf_valid": exported["cldf_valid"], "roundtrip_ok": exported["roundtrip_ok"],
        "acceptance_decisions": len(decisions), "decision_dates": sorted({r["decision_date"] for r in decisions}),
        "historical_claims_approved": False, "runtime_integrated": False,
    }
    write_json(output / "candidate-proof.json", proof)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--readiness", type=Path, default=ROOT / "docs/audits/lexicon-source-readiness-2026-11-16.json")
    parser.add_argument("--snapshot-dir", type=Path, default=ROOT / "data/sources/enwiktionary-tamil")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "target/lexicon/wiktionary-gaps")
    parser.add_argument("--supplemental-dir", type=Path)
    parser.add_argument("--fetch-missing", action="store_true")
    parser.add_argument("--check-native", action="store_true")
    parser.add_argument("--stage-candidates", action="store_true", help="Validate an isolated candidate pack; never modify usable packs")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not output.is_relative_to((ROOT / "target/lexicon").resolve()):
        parser.error("Reconciliation output must stay under target/lexicon")
    if args.fetch_missing and not args.supplemental_dir:
        parser.error("--fetch-missing requires an explicit new --supplemental-dir")
    if args.stage_candidates and not args.fetch_missing:
        parser.error("--stage-candidates requires --fetch-missing (verified cached captures are reused)")
    candidates = historical_candidates(args.package, args.readiness)
    pages, manifest = load_snapshot(args.snapshot_dir)
    initial = reconcile_records(candidates, pages, check_native=args.check_native)
    write_json(output / "initial-candidates.json", candidates)
    write_json(output / "pinned-reconciliation.json", initial)
    supplemental_manifest = None
    if args.fetch_missing:
        try:
            supplement = validate_supplemental_directory(args.supplemental_dir, args.snapshot_dir)
        except ValueError as exc:
            parser.error(str(exc))
        missing = sorted(r["headword"] for r in initial["records"] if r["status"] == "missing_from_snapshot")
        extra, supplemental_manifest = fetch_missing(missing, supplement)
        pages.update(extra)
    result = reconcile_records(candidates, pages, check_native=args.check_native)
    if supplemental_manifest:
        for row in result["records"]:
            outcome = supplemental_manifest["title_outcomes"].get(row["headword"])
            if outcome:
                row["fresh_source_capture"] = outcome
    result.update(schema_version=1, baseline_status_counts=initial["status_counts"],
                  readiness_sha256=digest(args.readiness)["sha256"], snapshot_sha256=manifest["pages_jsonl_gz_sha256"],
                  parser_sha256=digest(ROOT / "tools/lexicon_wiktionary_bulk.py")["sha256"],
                  supplemental_manifest=supplemental_manifest)
    write_json(output / "reconciliation.json", result)
    if args.stage_candidates:
        stage_candidates(result, supplement, output)
    print(json.dumps({"status_counts": result["status_counts"], "candidate_entries": len(result["candidate_entries"]), "candidate_senses": result["candidate_senses"]}))


if __name__ == "__main__":
    main()
