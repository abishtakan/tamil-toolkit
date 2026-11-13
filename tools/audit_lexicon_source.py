"""Read-only inventory of the supplied lexicon; no linguistic inference or repair."""

import argparse
import collections
import csv
import hashlib
import json
import platform
import re
import sys
import unicodedata
from pathlib import Path


def examples(rows, limit=4):
    return rows[:limit]


def audit(root):
    tables = {}
    report = {
        "python": platform.python_version(),
        "unicode_version": unicodedata.unidata_version,
        "files": {},
    }
    categorical = {
        "part_of_speech", "register", "language_variety", "status", "confidence",
        "verb_class", "sol_vagai", "padham_type", "lexical_stratum", "domain",
        "relation_code", "directionality", "region_dialect", "literary_source",
        "period_era", "domain_category", "source_code", "name_type", "origin_language",
        "domain_field", "specialization_tier", "corpus_frequency_tier", "sandhi_behavior",
        "syllable_structure", "etymology_type",
    }
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        stats = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        report["files"][path.name] = stats
        if path.suffix != ".csv":
            stats["header_hex"] = raw[:32].hex()
            continue
        raw.decode("utf-8-sig", errors="strict")
        stats["utf8_valid"] = True
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            header = next(reader)
            values = list(reader)
        bad_width = [i + 2 for i, row in enumerate(values) if len(row) != len(header)]
        stats.update(columns=header, rows=len(values), malformed_width_records=bad_width)
        if bad_width:
            raise ValueError(f"{path}: malformed records {bad_width[:4]}")
        rows = [dict(zip(header, row)) for row in values]
        tables[path.stem] = rows
        stats["empty_cells"] = {col: sum(not row[col] for row in rows) for col in header}
        counts = collections.Counter(row[header[0]] for row in rows)
        stats["duplicate_primary_ids"] = sum(n - 1 for n in counts.values())
        stats["duplicate_full_records"] = len(values) - len({tuple(row) for row in values})
        stats["categories"] = {
            col: dict(collections.Counter(row[col] for row in rows).most_common(40))
            for col in header if col in categorical
        }
        issues = collections.Counter()
        issue_examples = collections.defaultdict(list)
        for number, row in enumerate(rows, 2):
            for col, value in row.items():
                if not value:
                    continue
                kinds = []
                if unicodedata.normalize("NFC", value) != value:
                    kinds.append("non_nfc_cells")
                if value != value.strip():
                    kinds.append("outer_whitespace_cells")
                if "\ufffd" in value:
                    kinds.append("replacement_character_cells")
                controls = sorted({f"U+{ord(c):04X}" for c in value
                                   if unicodedata.category(c) in {"Cf", "Cc"}})
                if controls:
                    kinds.append("control_or_format_cells")
                    for code in controls:
                        issues["control_" + code] += 1
                for kind in kinds:
                    issues[kind] += 1
                    if len(issue_examples[kind]) < 4:
                        issue_examples[kind].append({"record": number, "field": col,
                                                     "value": value[:180]})
        stats["unicode_issues"] = dict(issues)
        stats["issue_examples"] = dict(issue_examples)
        word_col = next((col for col in ["headword_ta", "term_ta", "phrase_ta", "name_ta",
                                        "tamil_name", "transliterated_ta"] if col in header), None)
        if word_col:
            words = [row[word_col] for row in rows]
            frequency = collections.Counter(words)
            normalized = {unicodedata.normalize("NFC", word) for word in words}
            stats["headwords"] = {
                "field": word_col, "unique": len(frequency), "unique_nfc": len(normalized),
                "duplicate_extra_rows": len(words) - len(frequency),
                "duplicate_examples": examples([(w, n) for w, n in frequency.items() if n > 1]),
                "with_whitespace": sum(any(c.isspace() for c in w) for w in words),
                "without_tamil_scalars": sum(not any("\u0b80" <= c <= "\u0bff" for c in w) for w in words),
                "initial_scalars": dict(collections.Counter(w[:1] for w in words).most_common(40)),
            }
    lemmas = tables["primary_lemmas"]
    master = tables["unified_master_30col"]
    meanings = tables["primary_meanings"]
    relationships = tables["primary_relationships"]
    by_id = {r["word_id"]: r for r in lemmas}
    master_by_id = {r["word_id"]: r for r in master}
    by_headword = collections.defaultdict(list)
    for row in lemmas:
        by_headword[row["headword_ta"]].append(row["word_id"])
    report["integrity"] = integrity = {}
    integrity["duplicate_lexeme_ids"] = len(lemmas) - len({r["lexeme_id"] for r in lemmas})
    integrity["master_missing_lemma_ids"] = len(set(by_id) - set(master_by_id))
    integrity["master_extra_ids"] = len(set(master_by_id) - set(by_id))
    shared = sorted(set(lemmas[0]) & set(master[0]) - {"confidence"})
    integrity["master_lemma_field_mismatches"] = {
        col: sum(r[col] != master_by_id[r["word_id"]][col] for r in lemmas
                 if r["word_id"] in master_by_id) for col in shared
    }
    sense_counts = collections.Counter(r["word_id"] for r in meanings)
    integrity["meanings_missing_parent"] = sum(r["word_id"] not in by_id for r in meanings)
    integrity["meaning_headword_mismatches"] = sum(
        r["word_id"] in by_id and r["headword_ta"] != by_id[r["word_id"]]["headword_ta"]
        for r in meanings)
    integrity["lemmas_without_senses"] = sum(r["word_id"] not in sense_counts for r in lemmas)
    pairs = collections.Counter((r["word_id"], r["sense_number"]) for r in meanings)
    integrity["duplicate_sense_numbers"] = sum(n - 1 for n in pairs.values())
    integrity["master_sense_count_mismatches"] = sum(
        int(r["sense_count"]) != sense_counts[r["word_id"]] for r in master)
    integrity["master_non_nfc_normalized_headwords"] = sum(
        r["headword_normalized"] != unicodedata.normalize("NFC", r["headword_ta"])
        for r in master)
    for side in ("source", "target"):
        integrity[f"relationships_missing_{side}"] = sum(
            r[f"{side}_word_id"] not in by_id for r in relationships)
        integrity[f"relationships_{side}_headword_mismatches"] = sum(
            r[f"{side}_word_id"] in by_id
            and by_id[r[f"{side}_word_id"]]["headword_ta"] != r[f"{side}_headword_ta"]
            for r in relationships)
    integrity["relationships_self_links"] = sum(
        r["source_word_id"] == r["target_word_id"] for r in relationships)
    relkeys = collections.Counter((r["source_word_id"], r["target_word_id"], r["relation_code"])
                                  for r in relationships)
    integrity["duplicate_relationship_triples"] = sum(n - 1 for n in relkeys.values())
    integrity["relationships_targets_with_multiple_lexemes"] = sum(
        len(by_headword[r["target_headword_ta"]]) > 1 for r in relationships)
    report["content"] = {
        "english_meanings_containing_tamil": sum(any("\u0b80" <= c <= "\u0bff" for c in r["meaning_en"])
                                                  for r in meanings),
        "identical_meaning_and_definition_en": sum(bool(r["meaning_en"]) and r["meaning_en"] == r["definition_en"]
                                                   for r in meanings),
        "lemma_root_equals_headword": sum(r["root_word"] == r["headword_ta"] for r in lemmas),
        "master_example_equals_headword": sum(bool(r["example_sentence_ta"]) and
                                               r["example_sentence_ta"] == r["headword_ta"] for r in master),
        "secondary_overlap_primary": {},
    }
    for name, rows in tables.items():
        if not name.startswith("secondary_"):
            continue
        col = report["files"][name + ".csv"]["headwords"]["field"]
        report["content"]["secondary_overlap_primary"][name] = sum(r[col] in by_headword for r in rows)
    manifest = json.loads((root.parent / "tamil-lexicon.sha256.json").read_text(encoding="utf-8-sig"))
    report["source_checksums_match"] = all(report["files"][item["file"]]["sha256"] == item["sha256"]
                                           for item in manifest)
    report["total_bytes"] = sum(f["bytes"] for f in report["files"].values())
    report["content"]["duplicate_headword_pos_extra_rows"] = len(lemmas) - len(
        {(r["headword_ta"], r["part_of_speech"]) for r in lemmas})
    report["content"]["sense_blobs_with_multiple_numbered_segments"] = sum(
        bool(re.search(r"\b1\.\s", r["definition_en"]))
        and bool(re.search(r"\b2\.\s", r["definition_en"])) for r in meanings)
    return report


def runtime_audit(root):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bindings/python/python"))
    import tamil_toolkit as toolkit

    counts = collections.Counter()
    samples = collections.defaultdict(list)
    duration_cache = {}
    with (root / "unified_master_30col.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        letters = toolkit.get_letters(row["headword_ta"])
        for letter in letters:
            if letter not in duration_cache:
                duration_cache[letter] = toolkit.baseline_maathirai(letter)
        for name, supplied, current in (
            ("grapheme_count", int(row["grapheme_count"]), len(letters)),
            ("matra_count", float(row["matra_count"]), sum(duration_cache[x] for x in letters)),
        ):
            if supplied != current:
                counts[name] += 1
                if len(samples[name]) < 8:
                    samples[name].append({"word_id": row["word_id"], "headword": row["headword_ta"],
                                          "supplied": supplied, "current_rust": current})
    return {"rows": len(rows), "disagreement_counts": dict(counts), "examples": dict(samples),
            "scope": "Current local native Rust binding; not independent linguistic adjudication."}


def index_audit(root, keys_path):
    with (root / "primary_lemmas.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {r["word_id"]: r for r in rows}
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row["headword_ta"]].append(row["word_id"])
    with keys_path.open(encoding="utf-8", newline="") as handle:
        keys = dict(csv.reader(handle, delimiter="\t"))
    return {
        "fst_keys": len(keys), "missing_headword_keys": len(set(groups) - set(keys)),
        "extra_headword_keys": len(set(keys) - set(groups)),
        "values_match_same_headword_word_id": sum(
            value in by_id and by_id[value]["headword_ta"] == key for key, value in keys.items()),
        "word_ids_not_directly_addressed": len(set(by_id) - set(keys.values())),
        "multiple_entry_headwords": sum(len(ids) > 1 for ids in groups.values()),
        "examples": [{"headword": key, "word_ids": ids, "fst_value": keys.get(key)}
                     for key, ids in groups.items() if len(ids) > 1][:8],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/sources/tamil-lexicon"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-check", action="store_true", help="Compare against installed native Rust bindings")
    parser.add_argument("--fst-keys", type=Path, help="TSV exported by fst 0.4.7 Map stream")
    args = parser.parse_args()
    result = audit(args.source)
    if args.runtime_check:
        result["runtime_comparison"] = runtime_audit(args.source)
    if args.fst_keys:
        result["index_comparison"] = index_audit(args.source, args.fst_keys)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {len(result['files'])} files; original checksums match: {result['source_checksums_match']}")
