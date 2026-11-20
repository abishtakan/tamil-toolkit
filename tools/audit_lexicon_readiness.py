"""Read-only inventory of historical lexicon candidates; never approves claims."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
HEADWORD_COLUMNS = {
    "primary_lemmas.csv": "headword_ta",
    "primary_meanings.csv": "headword_ta",
    "secondary_archaic_literary_terms.csv": "term_ta",
    "secondary_dialect_colloquialisms.csv": "term_ta",
    "secondary_phrases_mwes.csv": "phrase_ta",
    "secondary_proper_names_toponyms.csv": "name_ta",
    "secondary_scientific_taxa.csv": "tamil_name",
    "secondary_specialized_technical_terms.csv": "term_ta",
    "secondary_transliterations_loanwords.csv": "transliterated_ta",
    "unified_master_30col.csv": "headword_ta",
}


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def digest(path: Path) -> dict:
    with path.open("rb") as handle:
        return {"bytes": path.stat().st_size, "sha256": hashlib.file_digest(handle, "sha256").hexdigest()}


def summarize(records: list[dict], column: str, usable: set[str]) -> dict:
    words = {r[column] for r in records if r[column]}
    return {
        "rows": len(records), "distinct_nonempty_spellings": len(words),
        "empty_headword_rows": sum(not r[column] for r in records),
        "exact_overlap_usable": len(words & usable),
        "exact_absent_usable": len(words - usable),
        "whitespace_boundary_rows": sum(r[column] != r[column].strip() for r in records),
    }


def collect(package: Path | None = None) -> dict:
    source = ROOT / "data/sources/tamil-lexicon"
    manifest = json.loads((source.parent / "tamil-lexicon.sha256.json").read_text(encoding="utf-8"))
    verified = {}
    for item in manifest:
        actual = digest(source / item["file"])
        if actual != {k: item[k] for k in ("bytes", "sha256")}:
            raise ValueError(f"Frozen source mismatch: {item['file']}")
        verified[item["file"]] = actual
    usable: set[str] = set()
    packs = {}
    for pack, relative in (("core", "lexicon/dictionary"), ("names_taxa", "lexicon/packs/names_taxa"), ("regional", "lexicon/packs/regional")):
        path = ROOT / relative
        assertions = {r["assertion_id"]: r for r in rows(path / "assertions.csv")}
        written = {json.loads(assertions[r["text_assertion_id"]]["value_json"]) for r in rows(path / "forms.csv") if r["representation"] == "written"}
        usable.update(written)
        packs[pack] = {"manifest": digest(path / "packs.toml"), "distinct_written_spellings": len(written)}
    files = {}
    all_words: set[str] = set()
    primary_words: set[str] = set()
    total = 0
    for path in sorted(source.glob("*.csv")):
        records = list(rows(path))
        total += len(records)
        info = {"rows": len(records)}
        column = HEADWORD_COLUMNS.get(path.name)
        if column:
            info.update(summarize(records, column, usable))
            info["nonempty_field_rows"] = {
                field: sum(bool(r[field]) for r in records)
                for field in ("meaning_ta", "meaning_en", "definition_ta", "definition_en", "english_term", "english_gloss")
                if field in records[0]
            }
            words = {r[column] for r in records if r[column]}
            all_words.update(words)
            if path.name == "primary_lemmas.csv":
                primary_words = words
            if "source_code" in records[0]:
                info["source_groups"] = {key: summarize([r for r in records if r["source_code"] == key], column, usable) for key in sorted({r["source_code"] for r in records})}
            for label in ("region_dialect", "literary_source", "origin_language"):
                if label in records[0]:
                    info[label + "_counts"] = dict(sorted(Counter(r[label] for r in records).items()))
        if path.name == "primary_meanings.csv":
            suffix = " (" + "".join(map(chr, (0x0B95, 0x0BB2, 0x0BC8, 0x0B9A, 0x0BCD, 0x0B9A, 0x0BCA, 0x0BB2, 0x0BCD))) + ")"
            info["self_label_placeholder_rows"] = sum(r["definition_ta"] == r["headword_ta"] + suffix for r in records)
        files[path.name] = info
    workspace = ROOT / "data/curation/tamil-lexicon"
    outcomes = Counter(r["outcome"] for r in rows(workspace / "decisions.csv"))
    source_states = Counter((r["evidence_verification_state"], r["reuse_state"]) for r in rows(workspace / "sources.csv"))
    result = {
        "schema_version": 1,
        "comparison": "Exact decoded scalar-string equality; no normalization, trimming, POS or sense equivalence inferred. Absent spellings are candidates, not approved additions.",
        "frozen_source_files": verified, "csv_rows": total, "packs": packs,
        "usable_distinct_written_spellings": len(usable), "files": files,
        "historical_union": {"distinct_nonempty_spellings": len(all_words), "exact_overlap_usable": len(all_words & usable), "exact_absent_usable": len(all_words - usable)},
        "secondary_absent_primary": len(all_words - primary_words),
        "historical_workspace": {
            "decision_outcomes": dict(sorted(outcomes.items())),
            "acceptance_decision_rows": sum(c for outcome, c in outcomes.items() if outcome in ("accepted_human", "accepted_auto_source")),
            "source_states": [{"evidence_verification_state": evidence, "reuse_state": reuse, "rows": count} for (evidence, reuse), count in sorted(source_states.items())],
            "decisions_fingerprint": digest(workspace / "decisions.csv"),
            "sources_fingerprint": digest(workspace / "sources.csv"),
        },
    }
    if package is not None:
        database = package / "databases/utlkd_primary.sqlite"
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            groups = []
            combined: dict[str, list[dict]] = {}
            for note, count in connection.execute("SELECT notes, count(*) FROM word_meanings GROUP BY notes ORDER BY count(*) DESC"):
                group = list(connection.execute("SELECT w.headword_ta FROM word_meanings m JOIN tamil_words w USING(word_id) WHERE m.notes IS ?", (note,)))
                words = {r[0] for r in group}
                groups.append({"note_label": note, "meaning_rows": count, "distinct_spellings": len(words), "exact_overlap_usable": len(words & usable), "exact_absent_usable": len(words - usable)})
                label = "other_unresolved"
                if note and "Wiktionary" in note:
                    label = "Wiktionary_label"
                elif note and ("Madras Tamil Lexicon" in note or "dsal_madras" in note):
                    label = "DSAL_Madras_label"
                elif note == "Oxford Tamil Dictionary":
                    label = "Oxford_label"
                elif note is None:
                    label = "no_note"
                combined.setdefault(label, []).extend({"headword": word[0]} for word in group)
            result["recovered_package"] = {
                "primary_database": digest(database),
                "warning": "Notes and source links are unverified historical labels, not proven attribution or permissions. Groups can overlap by headword.",
                "meaning_note_groups": groups,
                "combined_meaning_label_groups": {label: summarize(records, "headword", usable) for label, records in sorted(combined.items())},
                "word_source_links": [dict(zip(("source_code", "linked_words"), r)) for r in connection.execute("SELECT s.source_code,count(*) FROM word_source_links l JOIN sources s USING(source_id) GROUP BY s.source_code ORDER BY s.source_code")],
                "lemma_note_counts": [{"note_label": n, "rows": c} for n, c in connection.execute("SELECT notes,count(*) FROM tamil_words GROUP BY notes ORDER BY count(*) DESC")],
            }
        # Verify the supplied package is the origin of the same frozen exports.
        for filename, expected in verified.items():
            if digest(package / "tamil-lexicon" / filename) != expected:
                raise ValueError(f"Recovered package export mismatch: {filename}")
        result["recovered_package"]["all_12_exports_match"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, help="Optional recovered UTLKD package; opened read-only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    for protected in (ROOT / "data", ROOT / "lexicon", ROOT / "crates"):
        if output.is_relative_to(protected.resolve()):
            parser.error("Report output must be outside source, curation, canonical and crate data directories")
    result = collect(args.package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"csv_rows": result["csv_rows"], "historical_union": result["historical_union"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
