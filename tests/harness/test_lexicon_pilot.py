"""Structural pilot selection, accounting, and L2 acceptance tests (Feature 021 T033)."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tomllib
from copy import deepcopy
from pathlib import Path

import pytest

from tools.lexicon import (
    NAMESPACE,
    SOURCE,
    LexiconError,
    allocate_id,
    digest,
    inventory,
    json_text,
    source_rows,
    write_table,
)

ROOT = Path(__file__).resolve().parents[2]


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _encode_schema_row(table_name: str, row: dict) -> dict[str, str]:
    """Encode a decoded row dict to CSV cell strings matching schemas/lexicon/*.schema.json."""
    out: dict[str, str] = {}
    for key, val in row.items():
        if key.endswith("_json") or key in {"scalar_positions", "scalar_sequence"}:
            out[key] = json_text(val)
        elif val is None:
            out[key] = ""
        else:
            out[key] = str(val)
    return out


def _write_workspace_table(workspace: Path, table_name: str, columns: list[str], rows: list[dict]) -> None:
    try:
        from tools.lexicon_tables import write_rows

        write_rows(workspace / f"{table_name}.csv", table_name, rows)
        return
    except ImportError:
        pass
    encoded = [_encode_schema_row(table_name, row) for row in rows]
    write_table(workspace / f"{table_name}.csv", columns, encoded)


def _tamil_word(idx: int) -> str:
    consonants = [
        "\u0b95",
        "\u0b9a",
        "\u0b9f",
        "\u0ba4",
        "\u0baa",
        "\u0bb1",
        "\u0bae",
        "\u0ba8",
        "\u0bb5",
        "\u0bb2",
    ]
    a = consonants[idx % len(consonants)]
    b = consonants[(idx // len(consonants)) % len(consonants)]
    c = consonants[(idx // (len(consonants) ** 2)) % len(consonants)]
    return f"\u0b85{a}{b}{c}\u0bae\u0bcd"


def _rust_counts(headword: str) -> tuple[int, float]:
    wrapper = str(ROOT / "bindings/python/python")
    if wrapper not in sys.path:
        sys.path.insert(0, wrapper)
    import tamil_toolkit as toolkit

    letters = toolkit.get_letters(headword)
    return len(letters), sum(toolkit.baseline_maathirai(letter) for letter in letters)


def make_synthetic_source(root: Path) -> Path:
    """Create a synthetic 12-file intake bundle with no approved data."""
    src = root / "synthetic_source"
    src.mkdir(parents=True, exist_ok=True)

    lemma_cols = [
        "word_id", "lexeme_id", "headword_ta", "transliteration", "pronunciation_ipa",
        "part_of_speech", "sol_vagai", "grammatical_subclass", "animacy_gender",
        "padham_type", "lexical_stratum", "root_word", "verb_class", "register",
        "language_variety", "status", "confidence",
    ]
    meaning_cols = [
        "meaning_id", "word_id", "headword_ta", "sense_number", "meaning_ta",
        "meaning_en", "definition_ta", "definition_en", "domain", "register", "status",
    ]
    rel_cols = [
        "relationship_id", "source_word_id", "source_headword_ta",
        "target_word_id", "target_headword_ta", "relation_code",
        "directionality", "confidence", "status",
    ]
    master_cols = [
        "word_id", "lexeme_id", "headword_ta", "headword_normalized", "transliteration",
        "pronunciation_ipa", "part_of_speech", "grammatical_subclass", "animacy_gender",
        "matra_count", "grapheme_count", "syllable_structure", "phonetic_weight",
        "sandhi_behavior", "root_word", "etymology_type", "dedr_id", "meaning_ta",
        "meaning_en", "definition_ta", "definition_en", "domain", "register",
        "synonyms", "antonyms", "corpus_frequency_tier", "example_sentence_ta",
        "status", "confidence", "sense_count",
    ]

    lemmas, meanings, master = [], [], []
    meaning_id = 1
    headword_by_id: dict[str, str] = {}

    # 130 primary entries: pilot requires >=100, leaving rows 121..130 as unselected candidates
    # so external-endpoint relationships can be exercised cleanly.
    for idx in range(1, 131):
        wid = str(idx)
        pos = "NOUN"
        vclass = ""
        hw = _tamil_word(idx + 500)
        if 1 <= idx <= 20:
            # 10 homograph spellings, 2 entries each (odd=NOUN, even=VERB)
            pair = (idx + 1) // 2
            hw = _tamil_word(pair)
            if idx % 2 == 0:
                pos = "VERB"
                vclass = str(((pair - 1) % 7) + 1)
        elif 21 <= idx <= 32:
            pos = "VERB"
            vclass = str(((idx - 21) % 7) + 1)
        elif idx == 33:
            # Invalid vowel-sign sequence (NFC yet classification == "other")
            hw = "\u0b85\u0bae\u0bc1\u0ba4\u0bc1" + "\u0bbe\u0bb0\u0bcd"
        elif idx == 34:
            # KSHA tailoring count disagreement
            hw = "\u0b85\u0b95\u0bcd\u0bb7\u0bae\u0bcd"
        elif idx == 35:
            # SHRI ligature count disagreement
            hw = "\u0bb6\u0bcd\u0bb0\u0bc0"

        headword_by_id[wid] = hw
        lemmas.append({
            "word_id": wid,
            "lexeme_id": f"LEM_SYN_{idx:06d}",
            "headword_ta": hw,
            "transliteration": f"syn_{idx}",
            "pronunciation_ipa": "/syn/",
            "part_of_speech": pos,
            "sol_vagai": "\u0baa\u0bc6\u0baf\u0bb0\u0bcd\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd" if pos == "NOUN" else "\u0bb5\u0bbf\u0ba9\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd",
            "grammatical_subclass": "synthetic",
            "animacy_gender": "synthetic",
            "padham_type": "\u0baa\u0b95\u0bbe\u0baa\u0bcd\u0baa\u0ba4\u0bae\u0bcd",
            "lexical_stratum": "\u0b87\u0baf\u0bb1\u0bcd\u0b9a\u0bca\u0bb2\u0bcd",
            "root_word": hw,
            "verb_class": vclass,
            "register": "standard",
            "language_variety": "TA-GEN",
            "status": "verified",
            "confidence": "1.0",
        })

        m_ta = ""
        m_en = f"Synthetic gloss {idx}"
        d_en = f"Synthetic gloss {idx}"
        domain = "General"
        if idx == 36:
            m_en = chr(0xFEFF) + "bom synthetic gloss"
            d_en = m_en
        elif idx == 37:
            m_en = "  outer space gloss"
            d_en = m_en
        elif idx == 38:
            domain = "\u0b95\u0bc6" + "\u0bbe\u0bb3\u0bcd"
        elif idx == 39:
            m_en = "Bra" + "\u0307" + "h synthetic"
            d_en = m_en
        elif idx == 40:
            m_en = "replacement " + chr(0xFFFD) + " synthetic"
            d_en = m_en
        elif 41 <= idx <= 46:
            m_en = f"1. First sense {idx}; 2. Second sense {idx}."
            d_en = m_en
        elif 47 <= idx <= 52:
            m_en = f"English gloss with \u0ba4\u0bae\u0bbf\u0bb4\u0bcd {idx}"
            d_en = m_en

        entry_meanings = [{
            "meaning_id": str(meaning_id),
            "word_id": wid,
            "headword_ta": hw,
            "sense_number": "1",
            "meaning_ta": m_ta,
            "meaning_en": m_en,
            "definition_ta": "",
            "definition_en": d_en,
            "domain": domain,
            "register": "standard",
            "status": "verified",
        }]
        meaning_id += 1
        if idx in {1, 2, 41}:
            entry_meanings.append({
                "meaning_id": str(meaning_id),
                "word_id": wid,
                "headword_ta": hw,
                "sense_number": "2",
                "meaning_ta": "",
                "meaning_en": f"Secondary sense {idx}",
                "definition_ta": "",
                "definition_en": f"Secondary sense {idx}",
                "domain": "General",
                "register": "standard",
                "status": "verified",
            })
            meaning_id += 1
        meanings.extend(entry_meanings)

        rust_g, rust_m = _rust_counts(hw)
        if idx == 33:
            g_count, m_count = rust_g + 1, rust_m + 1.0
        elif idx in {34, 35}:
            g_count, m_count = rust_g + 1, rust_m + 0.5
        else:
            g_count, m_count = rust_g, rust_m

        master.append({
            "word_id": wid,
            "lexeme_id": f"LEM_SYN_{idx:06d}",
            "headword_ta": hw,
            "headword_normalized": hw,
            "transliteration": f"syn_{idx}",
            "pronunciation_ipa": "/syn/",
            "part_of_speech": pos,
            "grammatical_subclass": "synthetic",
            "animacy_gender": "synthetic",
            "matra_count": f"{m_count:.1f}",
            "grapheme_count": str(g_count),
            "syllable_structure": "\u0ba8\u0bc7\u0bb0\u0bcd",
            "phonetic_weight": "1.0",
            "sandhi_behavior": "synthetic",
            "root_word": hw,
            "etymology_type": "\u0b87\u0baf\u0bb1\u0bcd\u0b9a\u0bca\u0bb2\u0bcd",
            "dedr_id": "",
            "meaning_ta": m_ta,
            "meaning_en": m_en,
            "definition_ta": "",
            "definition_en": d_en,
            "domain": domain,
            "register": "standard",
            "synonyms": "",
            "antonyms": "",
            "corpus_frequency_tier": "Lexical Entry",
            "example_sentence_ta": "",
            "status": "verified",
            "confidence": "1.00",
            "sense_count": str(len(entry_meanings)),
        })

    rels = [
        {
            "relationship_id": "1",
            "source_word_id": "1",
            "source_headword_ta": headword_by_id["1"],
            "target_word_id": "2",
            "target_headword_ta": headword_by_id["2"],
            "relation_code": "SYNONYM",
            "directionality": "directed",
            "confidence": "1.0",
            "status": "verified",
        },
        {
            "relationship_id": "2",
            "source_word_id": "21",
            "source_headword_ta": headword_by_id["21"],
            "target_word_id": "22",
            "target_headword_ta": headword_by_id["22"],
            "relation_code": "RELATED",
            "directionality": "directed",
            "confidence": "1.0",
            "status": "verified",
        },
        {
            "relationship_id": "3",
            "source_word_id": "1",
            "source_headword_ta": headword_by_id["1"],
            "target_word_id": "130",
            "target_headword_ta": headword_by_id["130"],
            "relation_code": "ANTONYM",
            "directionality": "directed",
            "confidence": "1.0",
            "status": "verified",
        },
    ]

    _write_csv(src / "primary_lemmas.csv", lemma_cols, lemmas)
    # Select an ordinary endpoint after the stable-ID fill boundary, rather
    # than assuming numeric source row 130 has the greatest record ID.
    checksum = digest(src / "primary_lemmas.csv")
    outside = max((allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{sha}"), row["word_id"])
                  for ordinal, _, _, sha, row in source_rows(src / "primary_lemmas.csv") if int(row["word_id"]) > 100)[1]
    rels[-1]["target_word_id"] = outside
    rels[-1]["target_headword_ta"] = headword_by_id[outside]
    _write_csv(src / "primary_meanings.csv", meaning_cols, meanings)
    _write_csv(src / "primary_relationships.csv", rel_cols, rels)
    _write_csv(src / "unified_master_30col.csv", master_cols, master)

    # 7 secondary datasets (24 rows each)
    _write_csv(
        src / "secondary_archaic_literary_terms.csv",
        ["archaic_id", "term_ta", "transliteration", "meaning_ta", "meaning_en", "literary_source", "period_era"],
        [
            {
                "archaic_id": str(i),
                "term_ta": _tamil_word(2000 + i),
                "transliteration": f"arc_{i}",
                "meaning_ta": f"\u0b9a\u0bca\u0bb2\u0bcd {i}",
                "meaning_en": f"archaic {i}",
                "literary_source": "Thirukkural",
                "period_era": "Classical Sangam",
            }
            for i in range(1, 25)
        ],
    )

    regions = (
        ["Kongu"] * 4
        + ["Madras Baashai"] * 3
        + ["Madurai"] * 2
        + ["Nellai"] * 2
        + ["Jaffna"] * 7
        + ["General Spoken"] * 3
        + ["Gen-Z / Cinema"] * 3
    )
    _write_csv(
        src / "secondary_dialect_colloquialisms.csv",
        ["colloquial_id", "term_ta", "transliteration", "pronunciation_ipa", "standard_equivalent", "region_dialect", "meaning_ta", "notes"],
        [
            {
                "colloquial_id": str(i),
                "term_ta": _tamil_word(2100 + i),
                "transliteration": f"dia_{i}",
                "pronunciation_ipa": "/dia/",
                "standard_equivalent": _tamil_word(1),
                "region_dialect": regions[i - 1],
                "meaning_ta": "\u0baa\u0bca\u0bb0\u0bc1\u0bb3\u0bcd",
                "notes": f"synthetic dialect note {i}",
            }
            for i in range(1, 25)
        ],
    )

    phrase_sources = ["SRC-OXFORD-APPLE", "Tamilcube Bilingual Dictionary", "technical_compound_deconstruction"]
    _write_csv(
        src / "secondary_phrases_mwes.csv",
        ["phrase_id", "phrase_ta", "transliteration", "component_count", "domain_category", "english_gloss", "source_code"],
        [
            {
                "phrase_id": str(i),
                "phrase_ta": f"{_tamil_word(2200 + i)} {_tamil_word(2300 + i)}",
                "transliteration": f"phr_{i}",
                "component_count": "2",
                "domain_category": "General",
                "english_gloss": f"phrase gloss {i}",
                "source_code": phrase_sources[i % len(phrase_sources)],
            }
            for i in range(1, 25)
        ],
    )

    name_types = ["person_or_toponym", "country", "person", "city_toponym"]
    _write_csv(
        src / "secondary_proper_names_toponyms.csv",
        ["proper_id", "name_ta", "english_name", "name_type", "transliteration", "notes"],
        [
            {
                "proper_id": str(i),
                "name_ta": _tamil_word(2400 + i),
                "english_name": f"Place{i}",
                "name_type": name_types[i % len(name_types)],
                "transliteration": f"name_{i}",
                "notes": f"proper note {i}",
            }
            for i in range(1, 25)
        ],
    )

    _write_csv(
        src / "secondary_scientific_taxa.csv",
        ["taxa_id", "scientific_name", "tamil_name", "transliteration", "taxonomic_rank", "kingdom_phylum", "notes"],
        [
            {
                "taxa_id": str(i),
                "scientific_name": f"Taxon spec{i}",
                "tamil_name": _tamil_word(2500 + (1 if i in {1, 2} else i)),
                "transliteration": f"tax_{i}",
                "taxonomic_rank": "species",
                "kingdom_phylum": "Plantae",
                "notes": f"taxa note {i}",
            }
            for i in range(1, 25)
        ],
    )

    _write_csv(
        src / "secondary_specialized_technical_terms.csv",
        ["term_id", "term_ta", "transliteration", "english_term", "domain_field", "definition_ta", "definition_en", "specialization_tier", "source_code"],
        [
            {
                "term_id": str(i),
                "term_ta": f"{_tamil_word(2600 + i)} {_tamil_word(2700 + i)}" if i <= 14 else _tamil_word(2600 + i),
                "transliteration": f"tech_{i}",
                "english_term": f"tech term {i}",
                "domain_field": "Information Technology" if i % 2 == 0 else "Physics",
                "definition_ta": "",
                "definition_en": "",
                "specialization_tier": "specialized_kalaisol",
                "source_code": "TVA_KALAICHOL" if i <= 14 else "sorkuvai_technical",
            }
            for i in range(1, 25)
        ],
    )

    origins = ["English", "Sanskrit", "Arabic", "Foreign"]
    _write_csv(
        src / "secondary_transliterations_loanwords.csv",
        ["loanword_id", "transliterated_ta", "transliteration", "source_word_en", "origin_language", "pure_tamil_equivalent", "domain"],
        [
            {
                "loanword_id": str(i),
                "transliterated_ta": _tamil_word(2800 + i),
                "transliteration": f"loan_{i}",
                "source_word_en": f"loan_{i}",
                "origin_language": origins[i % len(origins)],
                "pure_tamil_equivalent": _tamil_word(1),
                "domain": "General",
            }
            for i in range(1, 25)
        ],
    )

    (src / "primary_lexicon.fst").write_bytes(b"SYNTH_FST_000001")
    return src


def stage_synthetic_workspace(source: Path, workspace: Path) -> Path:
    """Create a schema-valid all-quarantine editorial workspace from a synthetic source."""
    workspace.mkdir(parents=True, exist_ok=True)
    snapshots, sources, identities, source_records = [], [], [], []
    dispositions, assertions, evidence, findings = [], [], [], []
    seen_identities: set[tuple[str, str]] = set()
    primary_ids: set[str] = set()
    file_dispositions = []
    empty_finding_hash = hashlib.sha256(b"[]").hexdigest()

    paths = sorted(source.iterdir())
    paths.sort(key=lambda p: (p.name == "unified_master_30col.csv", p.name))

    for path in paths:
        checksum = digest(path)
        snap_id = allocate_id("snap", NAMESPACE, checksum)
        is_csv = path.suffix == ".csv"
        csv_rows = list(source_rows(path)) if is_csv else []
        snapshots.append({
            "snapshot_id": snap_id,
            "dataset_id": "synthetic-intake",
            "relative_path": path.name,
            "byte_length": path.stat().st_size,
            "sha256": checksum,
            "media_type": "text/csv" if is_csv else "application/octet-stream",
            "logical_row_count": len(csv_rows) + 1 if is_csv else None,
        })
        if not is_csv:
            file_dispositions.append({
                "snapshot_id": snap_id,
                "disposition": "quarantined",
                "reason_code": "UNREPRODUCIBLE_DERIVED_ARTIFACT",
            })
            continue

        src_id = allocate_id("src", NAMESPACE, json_text(["unrecovered:" + path.stem, snap_id]))
        sources.append({
            "source_id": src_id,
            "label_json": "unrecovered:" + path.stem,
            "publication_json": None,
            "url_json": None,
            "edition_json": None,
            "locator_json": None,
            "snapshot_id": snap_id,
            "retrieval_date_state": "unknown",
            "retrieval_date_json": None,
            "extraction_method": "synthetic_fixture",
            "extraction_version": "1",
            "evidence_verification_state": "unknown",
            "reuse_basis_json": None,
            "reuse_state": "unknown",
            "attribution_text_json": None,
            "attribution_reference_json": None,
        })

        for ordinal, start, end, row_hash, row in csv_rows:
            legacy = next(iter(row.values()))
            rec_id = allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{row_hash}")
            source_records.append({
                "record_id": rec_id,
                "snapshot_id": snap_id,
                "ordinal": ordinal,
                "physical_line_start": start,
                "physical_line_end": end,
                "legacy_key_json": legacy,
                "raw_row_sha256": row_hash,
            })

            if path.name in {"primary_lemmas.csv", "unified_master_30col.csv"}:
                kind, key = "ent", "primary:word:" + legacy
                if path.name == "primary_lemmas.csv":
                    primary_ids.add(legacy)
                else:
                    assert legacy in primary_ids
            else:
                kind = "sen" if path.name == "primary_meanings.csv" else "rel" if path.name == "primary_relationships.csv" else "ent"
                key = path.stem + ":legacy:" + legacy

            ent_id = allocate_id(kind, NAMESPACE, key)
            if (kind, key) not in seen_identities:
                seen_identities.add((kind, key))
                identities.append({
                    "entity_id": ent_id,
                    "kind": {"ent": "entry", "sen": "sense", "rel": "relation"}[kind],
                    "allocation_key": key,
                    "lifecycle": "active",
                    "identity_decision_id": None,
                })

            ast_id = allocate_id("ast", NAMESPACE, rec_id + ":unparsed")
            claim = {
                "assertion_id": ast_id,
                "subject_kind": {"ent": "entry", "sen": "sense", "rel": "relation"}[kind],
                "subject_id": ent_id,
                "property_code": "imported_master_fields" if path.name.startswith("unified_master") else "unparsed_source_record",
                "value_state": "known",
                "value_json": json_text(row),
                "origin": "verbatim_source",
                "source_fidelity_state": "unknown",
                "ambiguity_state": "unknown",
                "algorithm_reference": None,
                "convention_reference": None,
                "imported_status_json": row.get("status"),
                "imported_confidence_json": row.get("confidence"),
            }
            claim_rev = hashlib.sha256(json_text(claim).encode("ascii")).hexdigest()
            claim["claim_revision_sha256"] = claim_rev
            assertions.append(claim)

            evidence.append({
                "assertion_id": ast_id,
                "source_id": src_id,
                "source_record_id": rec_id,
                "locator_json": json_text({"snapshot_id": snap_id, "ordinal": ordinal}),
                "evidence_role": "transcribes",
                "extraction_version": "lexicon-host-v1",
                "extraction_sha256": row_hash,
            })

            dispositions.append({
                "record_id": rec_id,
                "disposition": "quarantined",
                "structural_state": "validated",
                "reason_code": "SOURCE_AND_REUSE_UNVERIFIED",
                "note_json": "Unparsed imported claims retained; no approved mapping.",
                "finding_set_sha256": empty_finding_hash,
                "method": "lexicon-host",
                "method_version": "1",
            })

    _write_workspace_table(
        workspace, "snapshots",
        ["snapshot_id", "dataset_id", "relative_path", "byte_length", "sha256", "media_type", "logical_row_count"],
        snapshots,
    )
    _write_workspace_table(
        workspace, "sources",
        [
            "source_id", "label_json", "publication_json", "url_json", "edition_json",
            "locator_json", "snapshot_id", "retrieval_date_state", "retrieval_date_json",
            "extraction_method", "extraction_version", "evidence_verification_state",
            "reuse_basis_json", "reuse_state", "attribution_text_json", "attribution_reference_json",
        ],
        sources,
    )
    _write_workspace_table(
        workspace, "identities",
        ["entity_id", "kind", "allocation_key", "lifecycle", "identity_decision_id"],
        identities,
    )
    _write_workspace_table(
        workspace, "source_records",
        ["record_id", "snapshot_id", "ordinal", "physical_line_start", "physical_line_end", "legacy_key_json", "raw_row_sha256"],
        source_records,
    )
    _write_workspace_table(
        workspace, "dispositions",
        ["record_id", "disposition", "structural_state", "reason_code", "note_json", "finding_set_sha256", "method", "method_version"],
        dispositions,
    )
    _write_workspace_table(
        workspace, "record_targets",
        ["record_id", "entity_id", "target_role"],
        [],
    )
    _write_workspace_table(
        workspace, "assertions",
        [
            "assertion_id", "subject_kind", "subject_id", "property_code", "value_state",
            "value_json", "origin", "source_fidelity_state", "ambiguity_state",
            "algorithm_reference", "convention_reference", "imported_status_json",
            "imported_confidence_json", "claim_revision_sha256",
        ],
        assertions,
    )
    _write_workspace_table(
        workspace, "evidence",
        ["assertion_id", "source_id", "source_record_id", "locator_json", "evidence_role", "extraction_version", "extraction_sha256"],
        evidence,
    )
    _write_workspace_table(
        workspace, "decisions",
        [
            "decision_id", "assertion_id", "assertion_revision_sha256", "evidence_bundle_sha256",
            "outcome", "actor_type", "actor_id", "method_version", "decision_date",
            "note_json", "predecessor_decision_id",
        ],
        [],
    )
    _write_workspace_table(
        workspace, "findings",
        ["finding_id", "record_id", "assertion_id", "issue_code", "severity", "scalar_positions", "status", "resolution_reason_json"],
        findings,
    )
    (workspace / "stage-report.json").write_text(
        json.dumps({"schema_version": 1, "file_dispositions": file_dispositions}, indent=2) + "\n",
        encoding="utf-8",
    )
    return workspace


def test_select_pilot_synthetic_meets_all_fr019_minima_and_matches_inventory(tmp_path):
    from tools.lexicon_pilot import select_pilot

    src = make_synthetic_source(tmp_path)
    inv_dir = tmp_path / "inventory"
    inventory(src, inv_dir)
    with (inv_dir / "source_records.csv").open(encoding="utf-8", newline="") as handle:
        inv_records = {r["record_id"]: r for r in csv.DictReader(handle)}

    sel1 = select_pilot(src)
    sel2 = select_pilot(src)
    assert sel1 == sel2

    selected_ids = {rec["record_id"] for rec in sel1["records"]}
    assert selected_ids <= set(inv_records)
    for rec in sel1["records"]:
        inv = inv_records[rec["record_id"]]
        assert rec["snapshot_id"] == inv["snapshot_id"]
        assert rec["ordinal"] == int(inv["logical_ordinal"])
        assert rec["raw_row_sha256"] == inv["row_sha256"]

    cov = sel1["summary"]["coverage"]
    assert sel1["summary"]["selected_primary_entries"] >= 100
    assert cov["homograph_spellings"] >= 10
    assert cov["homograph_entries"] >= 20
    assert cov["verbs"] >= 10
    assert cov["mixed_sense_records"] >= 10
    assert cov["technical_mwes"] >= 10
    assert cov["regional_total"] >= 10
    assert cov["regional_tn"] >= 1
    assert cov["regional_jaffna"] >= 1
    assert all(count >= 20 for count in sel1["summary"]["selected_secondary_by_file"].values())
    assert len(sel1["summary"]["selected_secondary_by_file"]) == 7

    # All synthetic Unicode & count audit classes must be represented
    classes = set(cov["audit_issue_classes"])
    assert {
        "control_U+FEFF",
        "non_nfc_cells",
        "outer_whitespace_cells",
        "replacement_character_cells",
        "invalid_orthography",
        "count:grapheme_count",
        "count:matra_count",
        "count_reason:ksha_tailoring",
        "count_reason:shri_ligature",
        "count_reason:invalid_orthography",
    } <= classes

    # Relationships: external endpoint to entry 130 must be marked evidence_only=True
    rel_recs = [r for r in sel1["records"] if r["file"] == "primary_relationships.csv"]
    assert any(r["evidence_only"] is True for r in rel_recs)
    assert any(r["evidence_only"] is False for r in rel_recs)


def test_write_selection_is_deterministic_ascii_toml_and_rejects_existing_different(tmp_path):
    from tools.lexicon_pilot import select_pilot, write_selection

    src = make_synthetic_source(tmp_path)
    sel = select_pilot(src)
    toml_path = tmp_path / "pilot-selection.toml"

    write_selection(toml_path, sel)
    raw = toml_path.read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    text = raw.decode("ascii")
    assert tomllib.loads(text) == sel

    # Identical rewrite succeeds idempotently
    write_selection(toml_path, sel)
    assert toml_path.read_bytes() == raw

    # Modified selection is rejected without overwriting existing TOML
    modified = deepcopy(sel)
    modified["records"] = modified["records"][:-1]
    with pytest.raises(LexiconError):
        write_selection(toml_path, modified)
    assert toml_path.read_bytes() == raw

    # Writing inside frozen source is rejected
    with pytest.raises(LexiconError):
        write_selection(src / "pilot-selection.toml", sel, source_root=src)


def test_pilot_all_quarantine_zero_eligible_passes_l2_deterministically(tmp_path):
    from tools.lexicon_pilot import pilot, select_pilot, write_selection

    src = make_synthetic_source(tmp_path)
    ws = stage_synthetic_workspace(src, tmp_path / "workspace")
    sel = select_pilot(src)
    sel_path = tmp_path / "pilot-selection.toml"
    write_selection(sel_path, sel)
    out_path = tmp_path / "reports" / "pilot-report.json"

    report1 = pilot(ws, sel_path, output=out_path, source=src)
    report2 = pilot(ws, sel)

    assert report1["l2_structural_accepted"] is True
    assert report1["l3_pack_eligible"] is False
    assert report1["runtime_verified"] is None
    assert report1["eligible_assertions"] == 0
    assert report1 == report2
    assert json.loads(out_path.read_text(encoding="ascii")) == report1
    assert out_path.read_text(encoding="ascii").isascii()
    assert not any(f["severity"] == "error" for f in report1["findings"])


def test_pilot_rejects_missing_pending_duplicate_or_target_violating_dispositions(tmp_path):
    from tools.lexicon_pilot import pilot, select_pilot

    src = make_synthetic_source(tmp_path)
    sel = select_pilot(src)
    target_rec = sel["records"][0]["record_id"]

    # 1. Missing disposition
    ws1 = stage_synthetic_workspace(src, tmp_path / "ws_missing")
    with (ws1 / "dispositions.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _write_csv(ws1 / "dispositions.csv", list(rows[0].keys()), [r for r in rows if r["record_id"] != target_rec])
    r1 = pilot(ws1, sel, source=src)
    assert r1["l2_structural_accepted"] is False
    assert "MISSING_DISPOSITION" in {f["code"] for f in r1["findings"]}

    # 2. Pending structural_state
    ws2 = stage_synthetic_workspace(src, tmp_path / "ws_pending")
    rows2 = [dict(r, structural_state="pending") if r["record_id"] == target_rec else r for r in rows]
    _write_csv(ws2 / "dispositions.csv", list(rows[0].keys()), rows2)
    r2 = pilot(ws2, sel, source=src)
    assert r2["l2_structural_accepted"] is False
    assert "PENDING_DISPOSITION" in {f["code"] for f in r2["findings"]}

    # 3. Duplicate disposition
    ws3 = stage_synthetic_workspace(src, tmp_path / "ws_dup")
    dup_row = next(r for r in rows if r["record_id"] == target_rec)
    _write_csv(ws3 / "dispositions.csv", list(rows[0].keys()), rows + [dup_row])
    r3 = pilot(ws3, sel, source=src)
    assert r3["l2_structural_accepted"] is False
    assert "DUPLICATE_DISPOSITION" in {f["code"] for f in r3["findings"]}

    # 4. Quarantined record with target mapping
    ws4 = stage_synthetic_workspace(src, tmp_path / "ws_qtarget")
    with (ws4 / "identities.csv").open(encoding="utf-8", newline="") as handle:
        first_ent = next(csv.DictReader(handle))["entity_id"]
    _write_csv(
        ws4 / "record_targets.csv",
        ["record_id", "entity_id", "target_role"],
        [{"record_id": target_rec, "entity_id": first_ent, "target_role": "primary"}],
    )
    r4 = pilot(ws4, sel, source=src)
    assert r4["l2_structural_accepted"] is False
    assert "QUARANTINED_TARGET_PRESENT" in {f["code"] for f in r4["findings"]}

    # 5. Missing FST file disposition
    ws5 = stage_synthetic_workspace(src, tmp_path / "ws_nofst")
    (ws5 / "stage-report.json").write_text('{"schema_version":1,"file_dispositions":[]}\n', encoding="utf-8")
    r5 = pilot(ws5, sel, source=src)
    assert r5["l2_structural_accepted"] is False
    assert "MISSING_FILE_DISPOSITION" in {f["code"] for f in r5["findings"]}


def test_pilot_rejects_unmet_fr019_coverage_and_incomplete_linked_records(tmp_path):
    from tools.lexicon_pilot import pilot, select_pilot

    src = make_synthetic_source(tmp_path)
    ws = stage_synthetic_workspace(src, tmp_path / "ws")
    sel = select_pilot(src)

    # Drop one secondary_archaic row below 20
    bad_sec = deepcopy(sel)
    archaic = [r for r in bad_sec["records"] if r["file"] == "secondary_archaic_literary_terms.csv"]
    drop_id = archaic[-1]["record_id"]
    bad_sec["records"] = [r for r in bad_sec["records"] if r["record_id"] != drop_id]
    r_sec = pilot(ws, bad_sec, source=src)
    assert r_sec["l2_structural_accepted"] is False
    assert "PILOT_MIN_SECONDARY" in {f["code"] for f in r_sec["findings"]}

    # Drop one member of a homograph pair
    bad_hom = deepcopy(sel)
    hom_pair = [r for r in bad_hom["records"] if r["file"] == "primary_lemmas.csv" and "homograph_group" in r["purposes"]]
    bad_hom["records"] = [r for r in bad_hom["records"] if r["record_id"] != hom_pair[0]["record_id"]]
    r_hom = pilot(ws, bad_hom, source=src)
    assert r_hom["l2_structural_accepted"] is False
    assert "PILOT_INCOMPLETE_HOMOGRAPH_GROUP" in {f["code"] for f in r_hom["findings"]}

    # Drop Jaffna regional entries (even if General Spoken remains, TN+Jaffna must span Jaffna)
    bad_reg = deepcopy(sel)
    with (src / "secondary_dialect_colloquialisms.csv").open(encoding="utf-8-sig", newline="") as handle:
        jaffna_ords = {idx for idx, r in enumerate(csv.DictReader(handle), 2) if r["region_dialect"] == "Jaffna"}
    bad_reg["records"] = [
        r for r in bad_reg["records"]
        if not (r["file"] == "secondary_dialect_colloquialisms.csv" and r["ordinal"] in jaffna_ords)
    ]
    r_reg = pilot(ws, bad_reg, source=src)
    assert r_reg["l2_structural_accepted"] is False
    assert "PILOT_MIN_REGIONAL" in {f["code"] for f in r_reg["findings"]}

    # Drop one primary meaning belonging to a selected entry
    bad_mean = deepcopy(sel)
    mean_rec = next(r for r in bad_mean["records"] if r["file"] == "primary_meanings.csv")
    bad_mean["records"] = [r for r in bad_mean["records"] if r["record_id"] != mean_rec["record_id"]]
    r_mean = pilot(ws, bad_mean, source=src)
    assert r_mean["l2_structural_accepted"] is False
    assert "PILOT_MISSING_PRIMARY_MEANINGS" in {f["code"] for f in r_mean["findings"]}

    # Drop a primary relationship touching a selected entry
    bad_rel = deepcopy(sel)
    rel_rec = next(r for r in bad_rel["records"] if r["file"] == "primary_relationships.csv")
    bad_rel["records"] = [r for r in bad_rel["records"] if r["record_id"] != rel_rec["record_id"]]
    r_rel = pilot(ws, bad_rel, source=src)
    assert r_rel["l2_structural_accepted"] is False
    assert "PILOT_MISSING_PRIMARY_RELATIONSHIPS" in {f["code"] for f in r_rel["findings"]}


def test_pilot_rejects_blocking_accounting_findings_and_source_tampering(tmp_path):
    from tools.lexicon_pilot import pilot, select_pilot

    src = make_synthetic_source(tmp_path)
    ws = stage_synthetic_workspace(src, tmp_path / "ws")
    sel = select_pilot(src)

    # Open blocking accounting error finding blocks L2 even when records are quarantined
    target_rec = sel["records"][0]["record_id"]
    _write_workspace_table(
        ws,
        "findings",
        ["finding_id", "record_id", "assertion_id", "issue_code", "severity", "scalar_positions", "status", "resolution_reason_json"],
        [{
            "finding_id": "fnd_1",
            "record_id": target_rec,
            "assertion_id": None,
            "issue_code": "ACCOUNTING_ERROR",
            "severity": "error",
            "scalar_positions": [],
            "status": "open",
            "resolution_reason_json": None,
        }],
    )
    r_err = pilot(ws, sel, source=src)
    assert r_err["l2_structural_accepted"] is False
    assert "UNRESOLVED_BLOCKING_FINDING" in {f["code"] for f in r_err["findings"]}

    # Source file hash mismatch fails pilot
    ws_clean = stage_synthetic_workspace(src, tmp_path / "ws_clean")
    (src / "primary_lexicon.fst").write_bytes(b"TAMPERED_FST_001")
    r_hash = pilot(ws_clean, sel, source=src)
    assert r_hash["l2_structural_accepted"] is False
    assert "SOURCE_HASH_MISMATCH" in {f["code"] for f in r_hash["findings"]}

    # Report output overlapping workspace or frozen source raises LexiconError
    with pytest.raises(LexiconError):
        pilot(ws_clean, sel, output=ws_clean / "report.json", source=src)


def test_pilot_accepts_nonprefix_secondary_selection_and_madras_baashai_without_approval(tmp_path):
    from tools.lexicon_pilot import pilot, select_pilot

    src = make_synthetic_source(tmp_path)
    # Expand archaic and dialect secondaries to 50 rows each so manual selections
    # can sit cleanly outside the 20+10 prefix retained by the old _scan implementation.
    _write_csv(
        src / "secondary_archaic_literary_terms.csv",
        ["archaic_id", "term_ta", "transliteration", "meaning_ta", "meaning_en", "literary_source", "period_era"],
        [
            {
                "archaic_id": str(i),
                "term_ta": _tamil_word(2000 + i),
                "transliteration": f"arc_{i}",
                "meaning_ta": f"\u0b9a\u0bca\u0bb2\u0bcd {i}",
                "meaning_en": f"archaic {i}",
                "literary_source": "Thirukkural",
                "period_era": "Classical Sangam",
            }
            for i in range(1, 51)
        ],
    )
    regions = ["General Spoken"] * 30 + ["Madras Baashai"] * 10 + ["Jaffna"] * 10
    _write_csv(
        src / "secondary_dialect_colloquialisms.csv",
        ["colloquial_id", "term_ta", "transliteration", "pronunciation_ipa", "standard_equivalent", "region_dialect", "meaning_ta", "notes"],
        [
            {
                "colloquial_id": str(i),
                "term_ta": _tamil_word(2100 + i),
                "transliteration": f"dia_{i}",
                "pronunciation_ipa": "/dia/",
                "standard_equivalent": _tamil_word(1),
                "region_dialect": regions[i - 1],
                "meaning_ta": "\u0baa\u0bca\u0bb0\u0bc1\u0bb3\u0bcd",
                "notes": f"synthetic dialect note {i}",
            }
            for i in range(1, 51)
        ],
    )

    ws = stage_synthetic_workspace(src, tmp_path / "ws_nonprefix")
    auto_sel = select_pilot(src)

    # Pick non-prefix archaic records completely disjoint from auto_sel's archaic slice.
    auto_archaic = {r["record_id"] for r in auto_sel["records"] if r["file"] == "secondary_archaic_literary_terms.csv"}
    archaic_snap = allocate_id("snap", NAMESPACE, digest(src / "secondary_archaic_literary_terms.csv"))
    all_archaic_recs = [
        {
            "record_id": allocate_id("rec", NAMESPACE, f"{digest(src / 'secondary_archaic_literary_terms.csv')}:{ordinal}:{row_hash}"),
            "snapshot_id": archaic_snap,
            "file": "secondary_archaic_literary_terms.csv",
            "ordinal": ordinal,
            "raw_row_sha256": row_hash,
            "purposes": ["manual_nonprefix"],
            "evidence_only": False,
        }
        for ordinal, _, _, row_hash, _ in source_rows(src / "secondary_archaic_literary_terms.csv")
    ]
    nonprefix_archaic = [r for r in all_archaic_recs if r["record_id"] not in auto_archaic][:20]
    assert len(nonprefix_archaic) == 20

    # Pick dialect records consisting ONLY of Madras Baashai (10) + Jaffna (10),
    # sorted descending so non-prefix IDs are exercised too.
    dia_sha = digest(src / "secondary_dialect_colloquialisms.csv")
    dia_snap = allocate_id("snap", NAMESPACE, dia_sha)
    madras_recs, jaffna_recs, general_recs = [], [], []
    for ordinal, _, _, row_hash, row in source_rows(src / "secondary_dialect_colloquialisms.csv"):
        rec = {
            "record_id": allocate_id("rec", NAMESPACE, f"{dia_sha}:{ordinal}:{row_hash}"),
            "snapshot_id": dia_snap,
            "file": "secondary_dialect_colloquialisms.csv",
            "ordinal": ordinal,
            "raw_row_sha256": row_hash,
            "purposes": ["manual_regional"],
            "evidence_only": False,
        }
        if row["region_dialect"] == "Madras Baashai":
            madras_recs.append(rec)
        elif row["region_dialect"] == "Jaffna":
            jaffna_recs.append(rec)
        else:
            general_recs.append(rec)

    manual_sel = deepcopy(auto_sel)
    manual_sel["records"] = [
        r for r in manual_sel["records"]
        if r["file"] not in {"secondary_archaic_literary_terms.csv", "secondary_dialect_colloquialisms.csv"}
    ] + nonprefix_archaic + madras_recs + jaffna_recs

    report = pilot(ws, manual_sel, source=src)
    assert report["l2_structural_accepted"] is True
    assert report["l3_pack_eligible"] is False
    assert report["eligible_assertions"] == 0
    assert report["summary"]["coverage"]["regional_tn"] == 10
    assert report["summary"]["coverage"]["regional_jaffna"] == 10
    assert report["summary"]["coverage"]["regional_total"] == 20

    # Replacing Madras Baashai with General Spoken drops regional_tn to 0 and fails PILOT_MIN_REGIONAL.
    no_tn_sel = deepcopy(manual_sel)
    no_tn_sel["records"] = [
        r for r in no_tn_sel["records"]
        if r["file"] != "secondary_dialect_colloquialisms.csv"
    ] + general_recs[:10] + jaffna_recs
    no_tn_report = pilot(ws, no_tn_sel, source=src)
    assert no_tn_report["l2_structural_accepted"] is False
    assert "PILOT_MIN_REGIONAL" in {f["code"] for f in no_tn_report["findings"]}


def test_pilot_verifies_snapshots_and_frozen_manifest_and_audit_report(tmp_path, monkeypatch):
    import tools.lexicon_pilot as lexicon_pilot
    from tools.lexicon_pilot import pilot, select_pilot
    from tools.lexicon_tables import read_rows, write_rows

    # 1. Snapshot consistency checks (rows/path/bytes/hash) on synthetic source.
    src_snap = make_synthetic_source(tmp_path / "snap_case")
    ws_snap = stage_synthetic_workspace(src_snap, tmp_path / "ws_snap")
    sel_snap = select_pilot(src_snap)

    original_snaps = list(read_rows(ws_snap / "snapshots.csv"))
    bad_count_snaps = [
        dict(r, logical_row_count=r["logical_row_count"] + 1) if r["relative_path"] == "primary_lemmas.csv" else r
        for r in original_snaps
    ]
    write_rows(ws_snap / "snapshots.csv", "snapshots", bad_count_snaps)
    r_count = pilot(ws_snap, sel_snap, source=src_snap)
    assert r_count["l2_structural_accepted"] is False
    assert "SNAPSHOT_MISMATCH" in {f["code"] for f in r_count["findings"]}

    missing_snaps = [r for r in original_snaps if r["relative_path"] != "primary_lexicon.fst"]
    write_rows(ws_snap / "snapshots.csv", "snapshots", missing_snaps)
    r_missing = pilot(ws_snap, sel_snap, source=src_snap)
    assert r_missing["l2_structural_accepted"] is False
    assert "MISSING_SNAPSHOT" in {f["code"] for f in r_missing["findings"]}

    extra_snaps = original_snaps + [dict(
        original_snaps[0],
        snapshot_id=allocate_id("snap", NAMESPACE, "extra-snapshot"),
        relative_path="extra_unexpected.csv",
    )]
    write_rows(ws_snap / "snapshots.csv", "snapshots", extra_snaps)
    r_extra = pilot(ws_snap, sel_snap, source=src_snap)
    assert r_extra["l2_structural_accepted"] is False
    assert "UNEXPECTED_SNAPSHOT" in {f["code"] for f in r_extra["findings"]}

    # 2. Actual-mode _checked_files manifest + frozen audit consistency on fast synthetic fixture.
    src_actual = make_synthetic_source(tmp_path / "actual_case")
    ws_actual = stage_synthetic_workspace(src_actual, tmp_path / "ws_actual")

    manifest_entries = []
    audit_files = {}
    for path in sorted(src_actual.iterdir()):
        sha = digest(path)
        size = path.stat().st_size
        manifest_entries.append({"file": path.name, "bytes": size, "sha256": sha})
        entry = {"bytes": size, "sha256": sha}
        if path.suffix == ".csv":
            csv_list = list(source_rows(path))
            entry["rows"] = len(csv_list)
            entry["unicode_issues"] = {}
            entry["issue_examples"] = {}
            if path.name == "primary_meanings.csv":
                # Simulate truncated per-class audit examples (1 locator per class even when >1 exist).
                ex_map = {}
                for ordinal, _, _, _, row in csv_list:
                    text = row.get("meaning_en", "")
                    dom = row.get("domain", "")
                    if chr(0xFEFF) in text and "control_or_format_cells" not in ex_map:
                        ex_map["control_or_format_cells"] = [{"record": ordinal, "field": "meaning_en", "value": text}]
                    elif text != text.strip() and "outer_whitespace_cells" not in ex_map:
                        ex_map["outer_whitespace_cells"] = [{"record": ordinal, "field": "meaning_en", "value": text}]
                    elif chr(0xFFFD) in text and "replacement_character_cells" not in ex_map:
                        ex_map["replacement_character_cells"] = [{"record": ordinal, "field": "meaning_en", "value": text}]
                    elif dom == "".join(map(chr, [0x0B95, 0x0BC6, 0x0BBE, 0x0BB3, 0x0BCD])) and "non_nfc_cells" not in ex_map:
                        ex_map["non_nfc_cells"] = [{"record": ordinal, "field": "domain", "value": dom}]
                    if "Bra\u0307h" in text and "non_nfc_cells" not in ex_map:
                        ex_map["non_nfc_cells"] = [{"record": ordinal, "field": "meaning_en", "value": text}]
                entry["unicode_issues"] = {
                    "control_U+FEFF": 2,
                    "control_or_format_cells": 2,
                    "outer_whitespace_cells": 5,
                    "replacement_character_cells": 2,
                    "non_nfc_cells": 4,
                }
                entry["issue_examples"] = ex_map
        audit_files[path.name] = entry

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_entries, indent=2), encoding="utf-8")
    audit_path = tmp_path / "metrics.json"
    audit_data = {
        "source_checksums_match": True,
        "files": audit_files,
        "runtime_comparison": {
            "rows": audit_files["unified_master_30col.csv"]["rows"],
            "disagreement_counts": {"grapheme_count": 3, "matra_count": 3},
        },
    }
    audit_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")

    monkeypatch.setattr(lexicon_pilot, "SOURCE", src_actual)
    monkeypatch.setattr(lexicon_pilot, "MANIFEST", manifest_path)
    monkeypatch.setattr(lexicon_pilot, "AUDIT", audit_path)
    lexicon_pilot._scan.cache_clear()
    try:
        sel_actual = select_pilot(src_actual)
        rep_actual = pilot(ws_actual, sel_actual)
        assert rep_actual["l2_structural_accepted"] is True
        assert rep_actual["l3_pack_eligible"] is False
        assert rep_actual["eligible_assertions"] == 0

        # Dropping a covered audit class fails clearly with PILOT_MISSING_AUDIT_CLASS naming it.
        bad_sel = deepcopy(sel_actual)
        bad_sel["records"] = [
            r for r in bad_sel["records"]
            if "audit:replacement_character_cells" not in r["purposes"]
        ]
        rep_missing_cls = pilot(ws_actual, bad_sel)
        assert rep_missing_cls["l2_structural_accepted"] is False
        missing_findings = [f for f in rep_missing_cls["findings"] if f["code"] == "PILOT_MISSING_AUDIT_CLASS"]
        assert missing_findings
        assert any("replacement_character_cells" in (f["subject_id"] + f["reason"]) for f in missing_findings)

        # Frozen audit missing issue_examples for an observed unicode_issues class raises LexiconError.
        bad_audit = deepcopy(audit_data)
        del bad_audit["files"]["primary_meanings.csv"]["issue_examples"]["replacement_character_cells"]
        audit_path.write_text(json.dumps(bad_audit, indent=2), encoding="utf-8")
        lexicon_pilot._scan.cache_clear()
        with pytest.raises(LexiconError, match="missing observed classes"):
            pilot(ws_actual, sel_actual)

        # Restore audit, then tamper actual source file AND lie in selection["files"] -> _checked_files rejects.
        audit_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
        lexicon_pilot._scan.cache_clear()
        (src_actual / "primary_lexicon.fst").write_bytes(b"TAMPERED_ACTUAL_FST")
        lying_sel = deepcopy(sel_actual)
        for item in lying_sel["files"]:
            if item["file"] == "primary_lexicon.fst":
                item["sha256"] = digest(src_actual / "primary_lexicon.fst")
        with pytest.raises(LexiconError, match="source hash mismatch"):
            pilot(ws_actual, lying_sel)
    finally:
        lexicon_pilot._scan.cache_clear()


def test_actual_source_pilot_selection_and_l2_contrast(tmp_path):
    """Single end-to-end check against frozen data/sources/tamil-lexicon."""
    from tools.lexicon_pilot import pilot, release_guard, select_pilot, write_selection

    sel = select_pilot(SOURCE)
    sel_path = tmp_path / "pilot-selection.toml"
    write_selection(sel_path, sel)

    # Pure ASCII TOML with zero raw Tamil
    toml_bytes = sel_path.read_bytes()
    assert toml_bytes.decode("ascii").isascii()
    assert tomllib.loads(toml_bytes.decode("ascii")) == sel

    cov = sel["summary"]["coverage"]
    assert sel["summary"]["selected_primary_entries"] >= 100
    assert all(v >= 20 for v in sel["summary"]["selected_secondary_by_file"].values())
    assert len(sel["summary"]["selected_secondary_by_file"]) == 7
    assert cov["homograph_spellings"] >= 10
    assert cov["verbs"] >= 10
    assert cov["mixed_sense_records"] >= 10
    assert cov["technical_mwes"] >= 10
    assert cov["regional_total"] >= 10 and cov["regional_tn"] >= 1 and cov["regional_jaffna"] >= 1
    assert {
        "control_U+FEFF",
        "non_nfc_cells",
        "outer_whitespace_cells",
        "invalid_orthography",
        "count:grapheme_count",
        "count:matra_count",
        "count_reason:ksha_tailoring",
        "count_reason:shri_ligature",
        "count_reason:invalid_orthography",
    } <= set(cov["audit_issue_classes"])

    # Stage only the selected pilot slice + real 12 snapshot hashes into an isolated temp workspace
    # to exercise real-source pilot() L2 acceptance and release_guard() contrast quickly.
    selected_by_file: dict[str, set[int]] = {}
    for rec in sel["records"]:
        selected_by_file.setdefault(rec["file"], set()).add(rec["ordinal"])

    ws = tmp_path / "real_pilot_ws"
    ws.mkdir()
    snapshots, sources, identities, source_records = [], [], [], []
    dispositions, assertions, evidence = [], [], []
    seen_ids: set[tuple[str, str]] = set()
    file_dispositions = []
    empty_hash = hashlib.sha256(b"[]").hexdigest()

    for path in sorted(SOURCE.iterdir()):
        checksum = digest(path)
        snap_id = allocate_id("snap", NAMESPACE, checksum)
        is_csv = path.suffix == ".csv"
        wanted = selected_by_file.get(path.name, set())
        row_total = 0
        if not is_csv:
            snapshots.append({
                "snapshot_id": snap_id,
                "dataset_id": "tamil-lexicon-intake",
                "relative_path": path.name,
                "byte_length": path.stat().st_size,
                "sha256": checksum,
                "media_type": "application/octet-stream",
                "logical_row_count": None,
            })
            file_dispositions.append({
                "snapshot_id": snap_id,
                "disposition": "quarantined",
                "reason_code": "UNREPRODUCIBLE_DERIVED_ARTIFACT",
            })
            continue

        src_id = allocate_id("src", NAMESPACE, json_text(["unrecovered:" + path.stem, snap_id]))
        sources.append({
            "source_id": src_id,
            "label_json": "unrecovered:" + path.stem,
            "publication_json": None,
            "url_json": None,
            "edition_json": None,
            "locator_json": None,
            "snapshot_id": snap_id,
            "retrieval_date_state": "unknown",
            "retrieval_date_json": None,
            "extraction_method": "owner_reported_python",
            "extraction_version": "unknown",
            "evidence_verification_state": "unknown",
            "reuse_basis_json": None,
            "reuse_state": "unknown",
            "attribution_text_json": None,
            "attribution_reference_json": None,
        })
        for ordinal, start, end, row_hash, row in source_rows(path):
            row_total += 1
            if ordinal not in wanted:
                continue
            legacy = next(iter(row.values()))
            rec_id = allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{row_hash}")
            source_records.append({
                "record_id": rec_id,
                "snapshot_id": snap_id,
                "ordinal": ordinal,
                "physical_line_start": start,
                "physical_line_end": end,
                "legacy_key_json": legacy,
                "raw_row_sha256": row_hash,
            })
            if path.name in {"primary_lemmas.csv", "unified_master_30col.csv"}:
                kind, key = "ent", "primary:word:" + legacy
            else:
                kind = "sen" if path.name == "primary_meanings.csv" else "rel" if path.name == "primary_relationships.csv" else "ent"
                key = path.stem + ":legacy:" + legacy
            ent_id = allocate_id(kind, NAMESPACE, key)
            if (kind, key) not in seen_ids:
                seen_ids.add((kind, key))
                identities.append({
                    "entity_id": ent_id,
                    "kind": {"ent": "entry", "sen": "sense", "rel": "relation"}[kind],
                    "allocation_key": key,
                    "lifecycle": "active",
                    "identity_decision_id": None,
                })
            ast_id = allocate_id("ast", NAMESPACE, rec_id + ":unparsed")
            claim = {
                "assertion_id": ast_id,
                "subject_kind": {"ent": "entry", "sen": "sense", "rel": "relation"}[kind],
                "subject_id": ent_id,
                "property_code": "imported_master_fields" if path.name.startswith("unified_master") else "unparsed_source_record",
                "value_state": "known",
                "value_json": json_text(row),
                "origin": "verbatim_source",
                "source_fidelity_state": "unknown",
                "ambiguity_state": "unknown",
                "algorithm_reference": None,
                "convention_reference": None,
                "imported_status_json": row.get("status"),
                "imported_confidence_json": row.get("confidence"),
            }
            claim["claim_revision_sha256"] = hashlib.sha256(json_text(claim).encode("ascii")).hexdigest()
            assertions.append(claim)
            evidence.append({
                "assertion_id": ast_id,
                "source_id": src_id,
                "source_record_id": rec_id,
                "locator_json": json_text({"snapshot_id": snap_id, "ordinal": ordinal}),
                "evidence_role": "transcribes",
                "extraction_version": "lexicon-host-v1",
                "extraction_sha256": row_hash,
            })
            dispositions.append({
                "record_id": rec_id,
                "disposition": "quarantined",
                "structural_state": "validated",
                "reason_code": "SOURCE_AND_REUSE_UNVERIFIED",
                "note_json": "Unparsed imported claims retained; no approved mapping.",
                "finding_set_sha256": empty_hash,
                "method": "lexicon-host",
                "method_version": "1",
            })
        snapshots.append({
            "snapshot_id": snap_id,
            "dataset_id": "tamil-lexicon-intake",
            "relative_path": path.name,
            "byte_length": path.stat().st_size,
            "sha256": checksum,
            "media_type": "text/csv",
            "logical_row_count": row_total + 1,
        })

    _write_workspace_table(ws, "snapshots", ["snapshot_id", "dataset_id", "relative_path", "byte_length", "sha256", "media_type", "logical_row_count"], snapshots)
    _write_workspace_table(ws, "sources", ["source_id", "label_json", "publication_json", "url_json", "edition_json", "locator_json", "snapshot_id", "retrieval_date_state", "retrieval_date_json", "extraction_method", "extraction_version", "evidence_verification_state", "reuse_basis_json", "reuse_state", "attribution_text_json", "attribution_reference_json"], sources)
    _write_workspace_table(ws, "identities", ["entity_id", "kind", "allocation_key", "lifecycle", "identity_decision_id"], identities)
    _write_workspace_table(ws, "source_records", ["record_id", "snapshot_id", "ordinal", "physical_line_start", "physical_line_end", "legacy_key_json", "raw_row_sha256"], source_records)
    _write_workspace_table(ws, "dispositions", ["record_id", "disposition", "structural_state", "reason_code", "note_json", "finding_set_sha256", "method", "method_version"], dispositions)
    _write_workspace_table(ws, "record_targets", ["record_id", "entity_id", "target_role"], [])
    _write_workspace_table(ws, "assertions", ["assertion_id", "subject_kind", "subject_id", "property_code", "value_state", "value_json", "origin", "source_fidelity_state", "ambiguity_state", "algorithm_reference", "convention_reference", "imported_status_json", "imported_confidence_json", "claim_revision_sha256"], assertions)
    _write_workspace_table(ws, "evidence", ["assertion_id", "source_id", "source_record_id", "locator_json", "evidence_role", "extraction_version", "extraction_sha256"], evidence)
    _write_workspace_table(ws, "decisions", ["decision_id", "assertion_id", "assertion_revision_sha256", "evidence_bundle_sha256", "outcome", "actor_type", "actor_id", "method_version", "decision_date", "note_json", "predecessor_decision_id"], [])
    _write_workspace_table(ws, "findings", ["finding_id", "record_id", "assertion_id", "issue_code", "severity", "scalar_positions", "status", "resolution_reason_json"], [])
    (ws / "stage-report.json").write_text(json.dumps({"schema_version": 1, "file_dispositions": file_dispositions}, indent=2) + "\n", encoding="utf-8")

    l2_report = pilot(ws, sel_path, output=tmp_path / "real-l2-report.json", source=SOURCE)
    assert l2_report["l2_structural_accepted"] is True
    assert l2_report["l3_pack_eligible"] is False
    assert l2_report["runtime_verified"] is None
    assert l2_report["eligible_assertions"] == 0

    l3_guard = release_guard(ws, pack="core")
    assert l3_guard["l3_pack_eligible"] is False
    assert l3_guard["eligible_assertions"] == 0
    assert l3_guard["runtime_verified"] is None
    assert "NONEMPTY_ELIGIBLE_PACK_REQUIRED" in {f["code"] for f in l3_guard["findings"]}
