"""Tests for deterministic offline lexicon cleaning, deduplication, and organization."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
import unicodedata

import pytest

from tools.lexicon_organize import (
    DEFAULT_HISTORICAL_DIR,
    DEFAULT_HISTORICAL_PIN,
    DEFAULT_OUT_DIR,
    EXPECTED_HISTORICAL_TOTAL_ROWS,
    _clean_domain_value,
    clean_technical_parens,
    normalize_dialect_region,
    normalize_domain,
    normalize_pos,
    normalize_register,
    organize_lexicon,
    repair_tamil_mojibake,
    verify_historical_sources,
    verify_tawiktionary_sources,
)
from tools.lexicon_quality_gate import run_quality_gate

HISTORICAL_HEADERS = {
    "primary_lemmas.csv": [
        "word_id", "lexeme_id", "headword_ta", "transliteration", "pronunciation_ipa",
        "part_of_speech", "sol_vagai", "grammatical_subclass", "animacy_gender",
        "padham_type", "lexical_stratum", "root_word", "verb_class", "register",
        "language_variety", "status", "confidence",
    ],
    "primary_meanings.csv": [
        "meaning_id", "word_id", "headword_ta", "sense_number", "meaning_ta",
        "meaning_en", "definition_ta", "definition_en", "domain", "register", "status",
    ],
    "primary_relationships.csv": [
        "relationship_id", "source_word_id", "source_headword_ta", "target_word_id",
        "target_headword_ta", "relation_code", "directionality", "confidence", "status",
    ],
    "secondary_archaic_literary_terms.csv": [
        "archaic_id", "term_ta", "transliteration", "meaning_ta", "meaning_en",
        "literary_source", "period_era",
    ],
    "secondary_dialect_colloquialisms.csv": [
        "colloquial_id", "term_ta", "transliteration", "pronunciation_ipa",
        "standard_equivalent", "region_dialect", "meaning_ta", "notes",
    ],
    "secondary_phrases_mwes.csv": [
        "phrase_id", "phrase_ta", "transliteration", "component_count",
        "domain_category", "english_gloss", "source_code",
    ],
    "secondary_proper_names_toponyms.csv": [
        "proper_id", "name_ta", "english_name", "name_type", "transliteration", "notes",
    ],
    "secondary_scientific_taxa.csv": [
        "taxa_id", "scientific_name", "tamil_name", "transliteration",
        "taxonomic_rank", "kingdom_phylum", "notes",
    ],
    "secondary_specialized_technical_terms.csv": [
        "term_id", "term_ta", "transliteration", "english_term", "domain_field",
        "definition_ta", "definition_en", "specialization_tier", "source_code",
    ],
    "secondary_transliterations_loanwords.csv": [
        "loanword_id", "transliterated_ta", "transliteration", "source_word_en",
        "origin_language", "pure_tamil_equivalent", "domain",
    ],
    "unified_master_30col.csv": [
        "word_id", "lexeme_id", "headword_ta", "headword_normalized", "transliteration",
        "pronunciation_ipa", "part_of_speech", "grammatical_subclass", "animacy_gender",
        "matra_count", "grapheme_count", "syllable_structure", "phonetic_weight",
        "sandhi_behavior", "root_word", "etymology_type", "dedr_id", "meaning_ta",
        "meaning_en", "definition_ta", "definition_en", "domain", "register",
        "synonyms", "antonyms", "corpus_frequency_tier", "example_sentence_ta",
        "status", "confidence", "sense_count",
    ],
}


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in header})


def _make_synthetic_historical_fixture(base: Path, overrides: dict[str, list[dict[str, str]]] | None = None) -> tuple[Path, Path, int]:
    hist = base / "tamil-lexicon"
    hist.mkdir(parents=True, exist_ok=True)
    data = {k: [] for k in HISTORICAL_HEADERS}
    if overrides:
        data.update(overrides)

    for fname, cols in HISTORICAL_HEADERS.items():
        _write_csv(hist / fname, cols, data[fname])

    (hist / "primary_lexicon.fst").write_bytes(b"FST0")

    pin_entries = []
    for p in sorted(hist.iterdir()):
        raw = p.read_bytes()
        pin_entries.append({
            "file": p.name,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    pin_path = base / "tamil-lexicon.sha256.json"
    pin_path.write_text(json.dumps(pin_entries, indent=2), encoding="utf-8")
    total_rows = sum(len(data[k]) for k in HISTORICAL_HEADERS)
    return hist, pin_path, total_rows


def _make_synthetic_open_fixture(base: Path) -> tuple[dict[str, Path], Path, Path]:
    open_root = base / "open_src"
    packs = {}
    for pid, hw, pos, region in (
        ("core", "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "NOUN", ""),
        ("names_taxa", "\u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8", "PROPN", ""),
        ("regional", "\u0baa\u0bc6\u0b9f\u0bcd\u0b9f\u0bc8", "NOUN", "JAFFNA"),
    ):
        pdir = open_root / pid
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "packs.toml").write_text(f'description = "Test {pid}"\n', encoding="utf-8")
        _write_csv(
            pdir / "sources.csv",
            ["source_id", "label_json", "publication_json", "url_json"],
            [{
                "source_id": f"src_{pid}",
                "label_json": json.dumps(f"lbl_{pid}"),
                "publication_json": json.dumps("enwikt"),
                "url_json": json.dumps(f"https://en.wiktionary.org/wiki/{pid}"),
            }],
        )
        _write_csv(
            pdir / "entries.csv",
            ["entry_id", "language_id", "variety_id", "canonical_form_id", "pos_assertion_id", "structural_kind", "revision"],
            [{
                "entry_id": f"ent_{pid}_1",
                "language_id": "tam",
                "variety_id": "",
                "canonical_form_id": f"frm_{pid}_1",
                "pos_assertion_id": f"ast_pos_{pid}",
                "structural_kind": "wiktionary_bulk",
                "revision": "rev1",
            }],
        )
        _write_csv(
            pdir / "forms.csv",
            ["form_id", "entry_id", "representation", "role", "text_assertion_id", "convention_assertion_id"],
            [{
                "form_id": f"frm_{pid}_1",
                "entry_id": f"ent_{pid}_1",
                "representation": "written",
                "role": "canonical",
                "text_assertion_id": f"ast_hw_{pid}",
                "convention_assertion_id": "",
            }],
        )
        _write_csv(
            pdir / "senses.csv",
            ["sense_id", "entry_id", "display_order", "parent_sense_id"],
            [{"sense_id": f"sen_{pid}_1", "entry_id": f"ent_{pid}_1", "display_order": "1", "parent_sense_id": ""}],
        )
        _write_csv(
            pdir / "texts.csv",
            ["text_id", "owner_kind", "owner_id", "component", "language_id", "text_assertion_id", "paired_translation_id", "cited_source_locator_json"],
            [{
                "text_id": f"txt_{pid}_1",
                "owner_kind": "sense",
                "owner_id": f"sen_{pid}_1",
                "component": "definition",
                "language_id": "eng",
                "text_assertion_id": f"ast_def_{pid}",
                "paired_translation_id": "",
                "cited_source_locator_json": json.dumps("{}"),
            }],
        )
        scope_rows = []
        if pid == "core":
            scope_rows.extend([
                {
                    "subject_kind": "sense",
                    "subject_id": f"sen_{pid}_1",
                    "dimension": "domain",
                    "state": "attested",
                    "label_code": "anatomy, astrology",
                    "supporting_assertion_id": "",
                    "decision_id": "",
                },
                {
                    "subject_kind": "sense",
                    "subject_id": f"sen_{pid}_1",
                    "dimension": "register",
                    "state": "attested",
                    "label_code": "Childish, Colloquial, slang",
                    "supporting_assertion_id": "",
                    "decision_id": "",
                },
            ])
        if region:
            scope_rows.append({
                "subject_kind": "sense",
                "subject_id": f"sen_{pid}_1",
                "dimension": "region",
                "state": "attested",
                "label_code": region,
                "supporting_assertion_id": "",
                "decision_id": "",
            })
        _write_csv(
            pdir / "scopes.csv",
            ["subject_kind", "subject_id", "dimension", "state", "label_code", "supporting_assertion_id", "decision_id"],
            scope_rows,
        )
        _write_csv(
            pdir / "relations.csv",
            ["relation_id", "source_kind", "source_id", "target_kind", "target_id", "relation_code_assertion_id", "directionality", "inverse_relation_id"],
            [],
        )
        _write_csv(
            pdir / "assertions.csv",
            ["assertion_id", "subject_kind", "subject_id", "property_code", "value_state", "value_json"],
            [
                {
                    "assertion_id": f"ast_hw_{pid}",
                    "subject_kind": "form",
                    "subject_id": f"frm_{pid}_1",
                    "property_code": "headword",
                    "value_state": "known",
                    "value_json": json.dumps(hw, ensure_ascii=False),
                },
                {
                    "assertion_id": f"ast_pos_{pid}",
                    "subject_kind": "entry",
                    "subject_id": f"ent_{pid}_1",
                    "property_code": "part_of_speech",
                    "value_state": "known",
                    "value_json": json.dumps(pos),
                },
                {
                    "assertion_id": f"ast_def_{pid}",
                    "subject_kind": "text",
                    "subject_id": f"txt_{pid}_1",
                    "property_code": "definition",
                    "value_state": "known",
                    "value_json": json.dumps(f"gloss for {pid}"),
                },
            ],
        )
        loc_payload = json.dumps({"pageid": 100, "revid": 200, "permalink": f"https://en.wiktionary.org/?oldid=200"})
        _write_csv(
            pdir / "evidence.csv",
            ["assertion_id", "source_id", "source_record_id", "locator_json", "evidence_role", "extraction_version", "extraction_sha256"],
            [{
                "assertion_id": f"ast_hw_{pid}",
                "source_id": f"src_{pid}",
                "source_record_id": "",
                "locator_json": json.dumps(loc_payload),
                "evidence_role": "supports",
                "extraction_version": "v1",
                "extraction_sha256": "0" * 64,
            }],
        )
        packs[pid] = pdir

    ta_dir = base / "tawikt"
    ta_dir.mkdir(parents=True, exist_ok=True)
    dump_bytes = b"dummy-bz2"
    (ta_dir / "dump.xml.bz2").write_bytes(dump_bytes)
    tawikt_manifest = ta_dir / "snapshots_manifest.json"
    tawikt_manifest.write_text(
        json.dumps({
            "source_id": "ta-wikt-test",
            "dump_filename": "dump.xml.bz2",
            "dump_bytes": len(dump_bytes),
            "dump_sha256": hashlib.sha256(dump_bytes).hexdigest(),
            "kept_entries": 4,
        }),
        encoding="utf-8",
    )
    tawikt_gz = ta_dir / "entries.jsonl.gz"
    nfd_hw = unicodedata.normalize("NFD", "\u0b94\u0bb5\u0bc8")
    zwj = chr(0x200D)
    zwj_hw = f"\u0b95{zwj}\u0ba9\u0bcd"
    with gzip.GzipFile(filename="entries.jsonl", mode="wb", fileobj=tawikt_gz.open("wb"), mtime=0) as gz:
        gz.write((json.dumps({
            "headword": nfd_hw,
            "pos": "NOUN",
            "tam_defs": ["\u0ba4\u0bae\u0bbf\u0bb4\u0bcd \u0baa\u0bca\u0bb0\u0bc1\u0bb3\u0bcd 1", "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd \u0baa\u0bca\u0bb0\u0bc1\u0bb3\u0bcd 2"],
            "eng_trans": ["poetess"],
            "source_id": "ta-wikt-test",
            "pageid": 11,
            "revid": 111,
            "permalink": "https://ta.wiktionary.org/?oldid=111",
        }, ensure_ascii=False) + "\n").encode("utf-8"))
        gz.write((json.dumps({
            "headword": zwj_hw,
            "pos": "VERB",
            "tam_defs": ["\u0bb5\u0bbf\u0ba9\u0bc8 (note", "attaining 5&nbsp;ft.<!--cmt-->", "act"],
            "eng_trans": ["act"],
            "source_id": "ta-wikt-test",
            "pageid": 12,
            "revid": 112,
            "permalink": "https://ta.wiktionary.org/?oldid=112",
        }, ensure_ascii=False) + "\n").encode("utf-8"))
        gz.write((json.dumps({
            "headword": "\u0bae\u0bb2\u00a6\u0bae\u0b9a\u0bae\u0bcd",
            "pos": "NOUN",
            "tam_defs": ["\u0baa\u0bca\u0bb0\u0bc1\u0bb3\u0bcd"],
            "eng_trans": [],
            "source_id": "ta-wikt-test",
            "pageid": 13,
            "revid": 113,
            "permalink": "https://ta.wiktionary.org/?oldid=113",
        }, ensure_ascii=False) + "\n").encode("utf-8"))
        gz.write((json.dumps({
            "headword": "\u0b85\u0b9a\u0bcd\u0b9a\u0ba8\u0bcd\u0ba4\u0bcc\u00a4\u0ba4\u0bcd\u0ba4\u0bb2\u0bcd",
            "pos": "NOUN",
            "tam_defs": ["\u0baa\u0bca\u0bb0\u0bc1\u0bb3\u0bcd"],
            "eng_trans": [],
            "source_id": "ta-wikt-test",
            "pageid": 14,
            "revid": 114,
            "permalink": "https://ta.wiktionary.org/?oldid=114",
        }, ensure_ascii=False) + "\n").encode("utf-8"))

    return packs, tawikt_manifest, tawikt_gz


def test_unit_cleaners_mojibake_parens_domain_and_pos() -> None:
    assert repair_tamil_mojibake("\u0b87\u0ba9\u0bcd\u0ba4\u0bc7\u0bb1\u0bb2\u0bcd \u0baa\u0ba3\u0bbf\u0baf\u0bbe\u0bb3\u0bbe\xa2") == (
        "\u0b87\u0ba9\u0bcd\u0ba4\u0bc7\u0bb1\u0bb2\u0bcd \u0baa\u0ba3\u0bbf\u0baf\u0bbe\u0bb3\u0bb0\u0bcd",
        "repaired",
    )
    assert repair_tamil_mojibake("\u0ba4\u0b9f\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0bb1\u0bcd\u0bb1\u0bb2\u0bcd \u0ba4\u0bc1\xa3\u0ba3\u0bcd\u0b9f\u0bb2\u0bcd") == (
        "\u0ba4\u0b9f\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0bb1\u0bcd\u0bb1\u0bb2\u0bcd \u0ba4\u0bc2\u0ba3\u0bcd\u0b9f\u0bb2\u0bcd",
        "repaired",
    )
    assert repair_tamil_mojibake("\u0b9a\u0bc1\u0ba3\u0bcd\u0ba3\u0b95\u0bcd\xa2\u0b95\u0b9f\u0bcd\u0b9f\u0bbf") == (
        "\u0b9a\u0bc1\u0ba3\u0bcd\u0ba3\u0b95\u0bcd\u0b95\u0b9f\u0bcd\u0b9f\u0bbf",
        "repaired",
    )
    assert repair_tamil_mojibake("\u0ba8\u0bc6\u0b9e\u0bcd\u0b9a\u0bc1\u0b9a\xa2\u0b9a\u0bc1\u0bb5\u0bb0\u0bcd") == (
        "\u0ba8\u0bc6\u0b9e\u0bcd\u0b9a\u0bc1\u0b9a\u0bcd\u0b9a\u0bc1\u0bb5\u0bb0\u0bcd",
        "repaired",
    )
    assert repair_tamil_mojibake("\u0bae\u0bc1\u0b9f\u0bbf\u0bb5\u0bc1\u0bb1\u0bbe \u0b8e\u0ba3\u0bcd (\xa3....)") == (
        "\u0bae\u0bc1\u0b9f\u0bbf\u0bb5\u0bc1\u0bb1\u0bbe \u0b8e\u0ba3\u0bcd (\xa3....)",
        "flagged_unrepaired",
    )

    assert clean_technical_parens("\u0b85\u0b95\u0bcd\u0b95\u0bbf (\u0b95\u0bbe\u0baf\u0bcd\u0b9a\u0bcd\u0b9a\u0bb2\u0bcd") == (
        "\u0b85\u0b95\u0bcd\u0b95\u0bbf",
        "\u0b95\u0bbe\u0baf\u0bcd\u0b9a\u0bcd\u0b9a\u0bb2\u0bcd",
        True,
    )
    assert clean_technical_parens("\u0b85\u0bb2\u0bcd\u0bb2\u0bbf \u0b87\u0ba4\u0bb4\u0bcd)") == (
        "\u0b85\u0bb2\u0bcd\u0bb2\u0bbf \u0b87\u0ba4\u0bb4\u0bcd",
        None,
        True,
    )
    assert clean_technical_parens("(\u0b85\u0bb4\u0bc8\u0baf\u0bbe\u0ba4\u0bc1 \u0ba8\u0bc1\u0bb4\u0bc8\u0baa\u0bb5\u0bb0\u0bcd)") == (
        "\u0b85\u0bb4\u0bc8\u0baf\u0bbe\u0ba4\u0bc1 \u0ba8\u0bc1\u0bb4\u0bc8\u0baa\u0bb5\u0bb0\u0bcd",
        None,
        False,
    )
    assert clean_technical_parens("\u0b85\u0b99\u0bcd\u0b95\u0bc8 (\u0b89\u0bb3\u0bcd\u0bb3\u0b99\u0bcd\u0b95\u0bc8)") == (
        "\u0b85\u0b99\u0bcd\u0b95\u0bc8",
        "\u0b89\u0bb3\u0bcd\u0bb3\u0b99\u0bcd\u0b95\u0bc8",
        False,
    )

    assert normalize_domain("Vetenary  Science") == ("Veterinary Science", True, True)
    assert normalize_pos("Proper noun") == "PROPN"
    assert normalize_pos("verb") == "VERB"
    assert normalize_dialect_region("Madras Baashai") == "CHENNAI"
    assert normalize_dialect_region("Gen-Z / Cinema") == "GEN_Z"

    # D1: Tamil-in-domain corruption, leading slash/dot, sentence-like
    dom, salvaged, meta = _clean_domain_value("/ \u0b95\u0bc6\u0b9f\u0b9a\u0bbe\u0bb0\u0bae\u0bcd/ \u0b95\u0bc6\u0b9f\u0bc1\u0ba4\u0bbf")
    assert dom is None
    assert salvaged == "\u0b95\u0bc6\u0b9f\u0b9a\u0bbe\u0bb0\u0bae\u0bcd/ \u0b95\u0bc6\u0b9f\u0bc1\u0ba4\u0bbf"
    assert meta["corrupted"] is True

    dom_sariyai, sal_sariyai, meta_sariyai = _clean_domain_value("// \u0b9a\u0bbe\u0bb0\u0bbf\u0baf\u0bc8")
    assert dom_sariyai is None
    assert sal_sariyai == "\u0b9a\u0bbe\u0bb0\u0bbf\u0baf\u0bc8"
    assert meta_sariyai["corrupted"] is True

    dom_dots, sal_dots, meta_dots = _clean_domain_value("...\u0bae\u0bc1\u0bb1\u0bc8\u0baf\u0bbe\u0b95\u0b95\u0bcd \u0b95\u0bc1\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1")
    assert dom_dots is None
    assert sal_dots is None
    assert meta_dots["corrupted"] is True

    dom_long, _, meta_long = _clean_domain_value("This is a very long sentence-like domain description exceeding forty-eight characters")
    assert dom_long is None
    assert meta_long["corrupted"] is True

    # D2: Atomic splitting, Title Case, acronym preservation, register snake_case
    assert normalize_domain("anatomy; astrology,  Anatomy , artificial_intelligence")[0] == (
        "Anatomy, Artificial Intelligence, Astrology"
    )
    assert normalize_domain("information_technology, ai, dna, ict")[0] == (
        "AI, DNA, ICT, Information Technology"
    )
    assert normalize_domain('"agriculture"')[0] == "Agriculture"
    assert normalize_domain("Measurement (Length)")[0] == "Measurement (Length)"
    assert normalize_register("Childish, Colloquial ; Slang, colloquial") == "childish, colloquial, slang"
    assert normalize_register("Gen-Z / Cinema, Formal") == "formal, gen_z_cinema"

    # D3: WordNet lexname mapping and generic drops
    assert _clean_domain_value("noun.animal")[0] == "Zoology"
    assert _clean_domain_value("noun.food")[0] == "Food & Cooking"
    assert _clean_domain_value("noun.communication")[0] == "Language & Communication"
    assert _clean_domain_value("noun.Tops")[0] is None
    assert _clean_domain_value("noun.act")[0] is None
    assert _clean_domain_value("verb.motion")[0] is None
    assert _clean_domain_value("adj.all")[0] is None
    assert _clean_domain_value("adv.all")[0] is None


def test_fail_closed_tamper_detection(tmp_path: Path) -> None:
    hist, pin_path, _total = _make_synthetic_historical_fixture(tmp_path)
    verify_historical_sources(hist, pin_path)

    # Corrupt one frozen CSV byte -> must fail closed
    target_csv = hist / "primary_lemmas.csv"
    orig_bytes = target_csv.read_bytes()
    target_csv.write_bytes(orig_bytes + b" ")
    with pytest.raises(ValueError, match="size mismatch"):
        verify_historical_sources(hist, pin_path)

    # Restore exact byte count with altered content -> must fail SHA-256 check
    target_csv.write_bytes(b"X" + orig_bytes[1:])
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_historical_sources(hist, pin_path)

    # ta.wiktionary dump tamper check
    packs, tawikt_manifest, tawikt_gz = _make_synthetic_open_fixture(tmp_path / "open_case")
    verify_tawiktionary_sources(tawikt_manifest, tawikt_gz)
    (tawikt_manifest.parent / "dump.xml.bz2").write_bytes(b"tampered!")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_tawiktionary_sources(tawikt_manifest, tawikt_gz)
    assert packs


def test_synthetic_end_to_end_cleaning_dedup_joiners_and_accounting(tmp_path: Path) -> None:
    overrides = {
        "primary_lemmas.csv": [
            {
                "word_id": "1",
                "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
                "part_of_speech": "NOUN",
                "register": "standard",
                "transliteration": "nanri",
                "pronunciation_ipa": "/n\u0250nr\u026a/",
                "root_word": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
                "animacy_gender": "\u0b85\u0b83\u0bb1\u0bbf\u0ba3\u0bc8",
            },
            {"word_id": "2", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "part_of_speech": "INTJ", "register": "standard", "transliteration": "nanri"},
            {
                "word_id": "3",
                "headword_ta": "\u0b85\u0b83\u0b95\u0bb2\u0bcd",
                "part_of_speech": "VERB",
                "verb_class": "3",
                "grammatical_subclass": "\u0bb5\u0bbf\u0ba9\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd (\u0ba4\u0ba9\u0bcd\u0bb5\u0bbf\u0ba9\u0bc8 \u2014 \u0bb5\u0b95\u0bc1\u0baa\u0bcd\u0baa\u0bc1 3)",
                "register": "standard",
            },
        ],
        "unified_master_30col.csv": [
            {
                "word_id": "1",
                "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
                "headword_normalized": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
                "domain": "General",
                "example_sentence_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf \u0b8e\u0ba9\u0bcd\u0bb1\u0bc1 \u0b9a\u0bca\u0bb2\u0bcd",
                "etymology_type": "\u0b87\u0baf\u0bb1\u0bcd\u0b9a\u0bca\u0bb2\u0bcd",
                "dedr_id": "3610",
                "sandhi_behavior": "\u0b89\u0baf\u0bbf\u0bb0\u0bc0\u0bb1\u0bc1",
                "corpus_frequency_tier": "Tier 1",
            },
            {"word_id": "2", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "headword_normalized": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "domain": "General"},
            {"word_id": "3", "headword_ta": "\u0b85\u0b83\u0b95\u0bb2\u0bcd", "headword_normalized": "\u0b85\u0b83\u0b95\u0bb2\u0bcd", "domain": "General"},
        ],
        "primary_meanings.csv": [
            {"meaning_id": "10", "word_id": "1", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "sense_number": "1", "meaning_ta": "", "meaning_en": "\ufeffgratitude, \u0b89\u0baa\u0b95\u0bbe\u0bb0\u0bae\u0bcd", "definition_ta": "", "definition_en": "\ufeffgratitude, \u0b89\u0baa\u0b95\u0bbe\u0bb0\u0bae\u0bcd"},
            {"meaning_id": "11", "word_id": "1", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "sense_number": "2", "meaning_ta": "\u0b87\u0baf\u0bb2\u0bcd", "meaning_en": "wrong lemma 1", "definition_ta": "\u0b87\u0baf\u0bb2\u0bcd", "definition_en": "wrong lemma 1"},
            {"meaning_id": "12", "word_id": "1", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "sense_number": "3", "meaning_ta": "\u0b87\u0baf\u0bb2\u0bcd", "meaning_en": "wrong lemma 2", "definition_ta": "\u0b87\u0baf\u0bb2\u0bcd", "definition_en": "wrong lemma 2"},
            {"meaning_id": "13", "word_id": "1", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "sense_number": "4", "meaning_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf\u0baf\u0bc7", "meaning_en": "vocative singular of \u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "definition_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf\u0baf\u0bc7", "definition_en": "vocative singular of \u0ba8\u0ba9\u0bcd\u0bb1\u0bbf"},
            {"meaning_id": "14", "word_id": "2", "headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "sense_number": "1", "meaning_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf (\u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd)", "meaning_en": "", "definition_ta": "", "definition_en": ""},
            {"meaning_id": "15", "word_id": "3", "headword_ta": "\u0b85\u0b83\u0b95\u0bb2\u0bcd", "sense_number": "1", "meaning_ta": "(\u0baa\u0bc6\u0bb0\u0bc1\u0bae\u0bcd\u0baa\u0bbe\u0bb2\u0bc1\u0bae\u0bcd \u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd\u0bb2\u0bbe\u0b95) \u0b9a\u0bc1\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bc1\u0ba4\u0bb2\u0bcd", "meaning_en": "(transitive) becoming small", "definition_ta": "\u0b85\u0b83\u0b95\u0bb2\u0bcd (\u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd)", "definition_en": "becoming small", "domain": "noun.act"},
            {"meaning_id": "16", "word_id": "3", "headword_ta": "\u0b85\u0b83\u0b95\u0bb2\u0bcd", "sense_number": "2", "meaning_ta": "", "meaning_en": "becoming small", "definition_ta": "", "definition_en": "becoming small"},
            {"meaning_id": "17", "word_id": "3", "headword_ta": "\u0b85\u0b83\u0b95\u0bb2\u0bcd", "sense_number": "3", "meaning_ta": "", "meaning_en": "contraction", "definition_ta": "", "definition_en": "contraction", "domain": "// \u0b9a\u0bc1\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bae\u0bcd"},
        ],
        "secondary_specialized_technical_terms.csv": [
            {"term_id": "1", "term_ta": "\u0b85\u0b95\u0baa\u0bcd \u0baa\u0bca\u0ba4\u0bbf\u0baf\u0bc1\u0bb1\u0bc8 (\u0b95\u0bc1\u0bb3\u0bbf\u0b95\u0bc8)", "english_term": "Internal Capsule\u2019s", "domain_field": "Vetenary  Science", "source_code": "TVA_KALAICHOL"},
            {"term_id": "2", "term_ta": "\u0b85\u0b95\u0baa\u0bcd\u0baa\u0bca\u0ba4\u0bbf\u0baf\u0bc1\u0bb1\u0bc8", "english_term": "internal capsule\u2019s ", "domain_field": "General Medicine", "source_code": "sorkuvai_technical"},
            {"term_id": "3", "term_ta": "\u0b85\u0b95\u0bcd\u0b95\u0bbf (\u0b95\u0bbe\u0baf\u0bcd\u0b9a\u0bcd\u0b9a\u0bb2\u0bcd", "english_term": "erysipelas", "domain_field": "General Medicine", "source_code": "TVA_KALAICHOL"},
            {"term_id": "4", "term_ta": "\u0baa\u0ba3\u0bbf\u0baf\u0bbe\u0bb3\u0bbe\xa2", "english_term": "worker", "domain_field": "Administration", "source_code": "TVA_KALAICHOL"},
            {"term_id": "5", "term_ta": "\u00e2 \u0baa\u0bc6\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bb0\u0b9f\u0bbf)", "english_term": "pointers", "domain_field": "Astronomy", "source_code": "TVA_KALAICHOL"},
            {"term_id": "6", "term_ta": "\u0ba4\u0bbf\u0b9a\u0bc8\u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0bbf(\u00e1", "english_term": "compass", "domain_field": "Astronomy", "source_code": "TVA_KALAICHOL"},
            {"term_id": "102083", "term_ta": "\u0bae\u0bc1\u0b9f\u0bbf\u0bb5\u0bc1\u0bb1\u0bbe \u0b8e\u0ba3\u0bcd (\u00a3....)", "english_term": "transcendental number", "domain_field": "Philosophy", "source_code": "TVA_KALAICHOL"},
            {"term_id": "108490", "term_ta": "\u0bb0\u0bc0\u0b95\u0bb2\u0bcd \u0bb5\u0bbf\u0ba3\u0bcd\u0bae\u0bc0\u0ba9\u0bcd (\u00e2-\u0bae\u0bbe\u0ba9\u0bcd \u0ba4\u0bb2\u0bc8\u0b95\u0bcd \u0b95\u0bca\u0bae\u0bcd\u0baa\u0bc1\u0bae\u0bc0\u0ba9\u0bcd)", "english_term": "rigel (\u00e2 orionis)", "domain_field": "Astronomy", "source_code": "TVA_KALAICHOL"},
        ],
        "secondary_phrases_mwes.csv": [
            {"phrase_id": "1", "phrase_ta": "\u0b85\u0b9f\u0bc1\u0b95\u0bcd\u0b95\u0bc1\u0baa\u0bcd \u0baa\u0bc2", "domain_category": "\u0ba8\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd; \u0ba8\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bc8", "english_gloss": "jasmine &amp; flower"},
            {"phrase_id": "2", "phrase_ta": "\u0b95\u0bc7\u0bb8\u0bc1", "domain_category": "noun.animal", "english_gloss": ""},
            {"phrase_id": "3", "phrase_ta": "\u0bb5\u0bc6\u0bb1\u0bc1\u0bae\u0bcd \u0ba4\u0bca\u0b9f\u0bb0\u0bcd", "domain_category": "verb.motion", "english_gloss": ""},
        ],
        "secondary_dialect_colloquialisms.csv": [
            {"colloquial_id": "1", "term_ta": "\u0b95\u0bc7\u0bb8\u0bc1", "pronunciation_ipa": "/ke\u02d0s\u026f/", "standard_equivalent": "\u0bb5\u0bb4\u0b95\u0bcd\u0b95\u0bc1", "region_dialect": "Madras Baashai", "meaning_ta": "\u0bb5\u0bb4\u0b95\u0bcd\u0b95\u0bc1"},
            {"colloquial_id": "2", "term_ta": "\u0baa\u0bc7\u0b9a\u0bc1", "pronunciation_ipa": "/pe\u02d0s\u026f/", "standard_equivalent": "\u0baa\u0bc7\u0b9a\u0bc1", "region_dialect": "General Spoken", "meaning_ta": "\u0b89\u0bb0\u0bc8\u0baf\u0bbe\u0b9f\u0bc1"},
            {"colloquial_id": "3", "term_ta": "\u0bae\u0b9a\u0bcd\u0b9a\u0bbe\u0ba9\u0bcd", "pronunciation_ipa": "/m\u0250t\u0283\u02d0a\u02d0n/", "standard_equivalent": "\u0ba8\u0ba3\u0bcd\u0baa\u0ba9\u0bcd", "region_dialect": "Gen-Z / Cinema", "meaning_ta": "\u0ba8\u0ba3\u0bcd\u0baa\u0ba9\u0bcd"},
        ],
        "primary_relationships.csv": [
            {"relationship_id": "1", "source_word_id": "1", "source_headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "target_word_id": "4", "target_headword_ta": "\u0b89\u0ba4\u0bb5\u0bbf", "relation_code": "synonym", "directionality": "bidirectional"},
            {"relationship_id": "2", "source_word_id": "1", "source_headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "target_word_id": "4", "target_headword_ta": "\u0b89\u0ba4\u0bb5\u0bbf", "relation_code": "SYNONYM", "directionality": "directed"},
            {"relationship_id": "3", "source_word_id": "1", "source_headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "target_word_id": "1", "target_headword_ta": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "relation_code": "SYNONYM", "directionality": "directed"},
        ],
    }
    hist, pin_path, total_rows = _make_synthetic_historical_fixture(tmp_path / "hist_src", overrides)
    packs, tawikt_manifest, tawikt_gz = _make_synthetic_open_fixture(tmp_path / "open_src")
    out_dir = tmp_path / "out"

    audit = organize_lexicon(
        out_dir,
        track="all",
        historical_dir=hist,
        historical_pin=pin_path,
        open_packs=packs,
        tawikt_manifest_path=tawikt_manifest,
        tawikt_entries_path=tawikt_gz,
        expected_historical_rows=total_rows,
    )

    assert audit["open"]["tawiktionary_quarantined_mojibake_count"] == 2
    assert audit["open"]["tawiktionary_emitted_entries"] == 2
    assert audit["open"]["tawiktionary_routed_ascii_defs"] == 2
    assert audit["local"]["accounting_exact"] is True
    assert audit["local"]["total_accounted_rows"] == total_rows
    assert audit["local"]["local_core"]["excluded_placeholder_meanings"] == 2
    assert audit["local"]["local_core"]["dropped_empty_senses"] == 1
    assert audit["local"]["local_core"]["filtered_cross_lemma_senses"] == 2
    assert audit["local"]["local_core"]["filtered_inflected_senses"] == 1
    assert audit["local"]["local_core"]["deduped_within_entry_senses"] == 1
    assert audit["local"]["local_core"]["bilingual_glosses_split"] == 2
    assert audit["local"]["local_core"]["kalaichol_prefix_stripped"] == 1
    assert audit["local"]["local_core"]["homograph_headwords_count"] == 1
    assert audit["local"]["local_core"]["bom_stripped_count"] == 2
    assert audit["local"]["local_core"]["corrupted_domains_cleared"] == 1
    assert audit["local"]["local_core"]["salvaged_tamil_domains_to_gloss"] == 1
    assert audit["local"]["local_core"]["wordnet_domains_dropped"] == 1
    assert audit["local"]["local_terminology"]["deduped_sorkuvai_merged"] == 1
    assert audit["local"]["local_terminology"]["mojibake_repaired_count"] == 4
    assert audit["local"]["local_terminology"]["mojibake_flagged_unrepaired_count"] == 0
    assert audit["local"]["local_terminology"]["domain_typos_fixed"] == 1
    assert audit["local"]["local_terminology"]["unbalanced_parens_fixed"] == 3
    assert audit["local"]["local_terminology"]["dropped_junk_glosses_count"] == 2
    assert audit["local"]["local_phrases"]["tamil_domains_reclassified"] == 1
    assert audit["local"]["local_phrases"]["wordnet_domains_mapped"] == 1
    assert audit["local"]["local_phrases"]["wordnet_domains_dropped"] == 1
    assert audit["local"]["local_phrases"]["backfilled_glosses"] == 1
    assert audit["local"]["local_phrases"]["quarantined_empty_senses"] == 1
    assert audit["local"]["local_relations"]["valid_relations"] == 2
    assert audit["local"]["local_relations"]["deduplicated_relations"] == 1
    assert audit["local"]["local_relations"]["expanded_symmetric_edges"] == 1
    assert audit["local"]["local_relations"]["invalid_or_self_rows"] == 1

    # Check C1 + ZWJ + NFD in ta_wiktionary
    tawikt_entries = [
        json.loads(line)
        for line in (out_dir / "open/ta_wiktionary/entries.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(tawikt_entries) == 2
    by_eid = {e["entry_id"]: e for e in tawikt_entries}
    assert chr(0x200D) in by_eid["tawikt:12:112:2"]["headword"]
    assert unicodedata.is_normalized("NFC", by_eid["tawikt:11:111:1"]["headword"])
    assert any(f["role"] == "raw_source" for f in by_eid["tawikt:11:111:1"]["forms"])
    assert len(by_eid["tawikt:11:111:1"]["senses"]) == 3
    zwj_senses = by_eid["tawikt:12:112:2"]["senses"]
    assert [s["definition_ta"] for s in zwj_senses if s["definition_ta"]] == ["\u0bb5\u0bbf\u0ba9\u0bc8 (note)"]
    assert [s["gloss_en"] for s in zwj_senses if s["gloss_en"]] == ["act", "attaining 5 ft."]

    # Check C2 + H4 in local_core
    core_entries = [
        json.loads(line)
        for line in (out_dir / "local/local_core/entries.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    c_by_id = {e["entry_id"]: e for e in core_entries}
    assert c_by_id["loc_core:1"]["dedr_id"] == "3610"
    assert c_by_id["loc_core:1"]["root_word"] == "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf"
    assert c_by_id["loc_core:1"]["sandhi_behavior"] == "\u0b89\u0baf\u0bbf\u0bb0\u0bc0\u0bb1\u0bc1"
    assert c_by_id["loc_core:1"]["frequency_tier"] == "Tier 1"
    assert {"role": "ipa", "text": "/n\u0250nr\u026a/"} in c_by_id["loc_core:1"]["forms"]
    assert len(c_by_id["loc_core:1"]["senses"]) == 1
    assert c_by_id["loc_core:1"]["senses"][0]["gloss_en"] == "gratitude"
    assert c_by_id["loc_core:1"]["senses"][0]["gloss_ta"] == "\u0b89\u0baa\u0b95\u0bbe\u0bb0\u0bae\u0bcd"
    assert c_by_id["loc_core:3"]["verb_class"] == "3"
    assert c_by_id["loc_core:3"]["transitivity"] == "intransitive"
    assert len(c_by_id["loc_core:3"]["senses"]) == 2
    assert c_by_id["loc_core:3"]["senses"][0]["gloss_ta"] == "\u0b9a\u0bc1\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bc1\u0ba4\u0bb2\u0bcd"
    assert c_by_id["loc_core:3"]["senses"][0]["domain"] is None
    assert c_by_id["loc_core:3"]["senses"][1]["domain"] is None
    assert c_by_id["loc_core:3"]["senses"][1]["gloss_ta"] == "\u0b9a\u0bc1\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bae\u0bcd"

    # Check open/core D2 domain & register normalization
    open_core_entries = [
        json.loads(line)
        for line in (out_dir / "open/core/entries.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert open_core_entries[0]["domain"] == "Anatomy, Astrology"
    assert open_core_entries[0]["register"] == "childish, colloquial, slang"

    # Check local_terminology M1 + D4 fixes
    term_entries = [
        json.loads(line)
        for line in (out_dir / "local/local_terminology/entries.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    t_by_id = {e["entry_id"]: e for e in term_entries}
    assert t_by_id["loc_term:1"]["headword"] == "\u0b85\u0b95\u0baa\u0bcd \u0baa\u0bca\u0ba4\u0bbf\u0baf\u0bc1\u0bb1\u0bc8"
    assert t_by_id["loc_term:1"]["domain"] == "Veterinary Science"
    assert t_by_id["loc_term:1"]["senses"][0]["gloss_ta"] == "\u0b95\u0bc1\u0bb3\u0bbf\u0b95\u0bc8"
    assert t_by_id["loc_term:1"]["senses"][0]["gloss_en"] == "Internal Capsule's"
    assert t_by_id["loc_term:1"]["senses"][0]["definition_ta"] is None
    assert t_by_id["loc_term:1"]["senses"][0]["definition_en"] is None
    assert {"role": "variant", "text": "\u0b85\u0b95\u0baa\u0bcd\u0baa\u0bca\u0ba4\u0bbf\u0baf\u0bc1\u0bb1\u0bc8"} in t_by_id["loc_term:1"]["forms"]
    assert t_by_id["loc_term:4"]["headword"] == "\u0baa\u0ba3\u0bbf\u0baf\u0bbe\u0bb3\u0bb0\u0bcd"
    assert {"role": "raw_source", "text": "\u0baa\u0ba3\u0bbf\u0baf\u0bbe\u0bb3\u0bbe\xa2"} in t_by_id["loc_term:4"]["forms"]
    assert t_by_id["loc_term:5"]["headword"] == "\u0baa\u0bc6\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bb0\u0b9f\u0bbf"
    assert t_by_id["loc_term:6"]["senses"][0]["gloss_ta"] is None
    assert t_by_id["loc_term:102083"]["headword"] == "\u0bae\u0bc1\u0b9f\u0bbf\u0bb5\u0bc1\u0bb1\u0bbe \u0b8e\u0ba3\u0bcd"
    assert t_by_id["loc_term:102083"]["senses"][0]["gloss_ta"] is None
    assert t_by_id["loc_term:108490"]["senses"][0]["gloss_ta"] == "\u03b2-\u0bae\u0bbe\u0ba9\u0bcd \u0ba4\u0bb2\u0bc8\u0b95\u0bcd \u0b95\u0bca\u0bae\u0bcd\u0baa\u0bc1\u0bae\u0bc0\u0ba9\u0bcd"
    assert t_by_id["loc_term:108490"]["senses"][0]["gloss_en"] == "rigel (\u03b2 orionis)"

    # Check H3 + D3 in local_phrases
    phr_entries = [
        json.loads(line)
        for line in (out_dir / "local/local_phrases/entries.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(phr_entries) == 2
    p_by_id = {e["entry_id"]: e for e in phr_entries}
    assert p_by_id["loc_phr:1"]["domain"] is None
    assert p_by_id["loc_phr:1"]["senses"][0]["gloss_en"] == "jasmine & flower"
    assert p_by_id["loc_phr:1"]["senses"][0]["gloss_ta"] == "\u0ba8\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd; \u0ba8\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bc8"
    assert {"role": "variant", "text": "\u0ba8\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd"} in p_by_id["loc_phr:1"]["forms"]
    assert p_by_id["loc_phr:2"]["domain"] == "Zoology"
    assert p_by_id["loc_phr:2"]["senses"][0]["gloss_ta"] == "\u0bb5\u0bb4\u0b95\u0bcd\u0b95\u0bc1"

    # Check H4 + H5 in local_dialect
    dial_entries = [
        json.loads(line)
        for line in (out_dir / "local/local_dialect/entries.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    d_by_id = {e["entry_id"]: e for e in dial_entries}
    assert d_by_id["loc_dial:1"]["region"] == "CHENNAI"
    assert d_by_id["loc_dial:1"]["domain"] is None
    assert d_by_id["loc_dial:1"]["register"] == "colloquial"
    assert d_by_id["loc_dial:1"]["standard_equivalent"] == "\u0bb5\u0bb4\u0b95\u0bcd\u0b95\u0bc1"
    assert {"role": "ipa", "text": "/ke\u02d0s\u026f/"} in d_by_id["loc_dial:1"]["forms"]
    assert d_by_id["loc_dial:2"]["region"] is None
    assert d_by_id["loc_dial:2"]["register"] == "spoken"
    assert d_by_id["loc_dial:3"]["region"] is None
    assert d_by_id["loc_dial:3"]["register"] == "slang"

    # Check M2 symmetric relations
    rel_rows = [
        json.loads(line)
        for line in (out_dir / "local/local_relations/relations.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {(r["source_headword"], r["target_headword"], r["relation_code"]) for r in rel_rows} == {
        ("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "\u0b89\u0ba4\u0bb5\u0bbf", "SYNONYM"),
        ("\u0b89\u0ba4\u0bb5\u0bbf", "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "SYNONYM"),
    }

    # Check cross-track overlap (நன்றி is in both open core and local_core)
    assert audit["cross_track_overlap"]["overlap_distinct_headwords"] == 1

    # Quality gate must pass on synthetic organized output
    gate_report = run_quality_gate(out_dir, expected_historical_rows=total_rows)
    assert gate_report["status"] == "pass"
    assert gate_report["failure_count"] == 0

    # Accounting mismatch must fail closed
    with pytest.raises(ValueError, match="accounting mismatch"):
        organize_lexicon(
            tmp_path / "bad_out",
            track="local",
            historical_dir=hist,
            historical_pin=pin_path,
            expected_historical_rows=total_rows + 1,
        )


def test_real_corpus_organized_outputs_and_determinism(tmp_path: Path) -> None:
    """Verify full real corpus outputs under target/lexicon/organized and byte-identical reproducibility."""
    if not DEFAULT_HISTORICAL_DIR.is_dir() or not DEFAULT_HISTORICAL_PIN.is_file():
        pytest.skip("Frozen historical corpus not present")
    if not (DEFAULT_OUT_DIR / "cleaning_audit.json").is_file():
        organize_lexicon(DEFAULT_OUT_DIR, track="all")

    audit = json.loads((DEFAULT_OUT_DIR / "cleaning_audit.json").read_text(encoding="utf-8"))
    assert audit["local"]["expected_historical_csv_rows"] == EXPECTED_HISTORICAL_TOTAL_ROWS
    assert audit["local"]["total_accounted_rows"] == EXPECTED_HISTORICAL_TOTAL_ROWS
    assert audit["local"]["accounting_exact"] is True
    assert sum(audit["local"]["per_file_accounted_rows"].values()) == EXPECTED_HISTORICAL_TOTAL_ROWS
    assert audit["local"]["local_core"]["excluded_placeholder_meanings"] == 12021
    assert audit["local"]["local_core"]["filtered_cross_lemma_senses"] == 1969
    assert audit["local"]["local_core"]["filtered_inflected_senses"] == 761
    assert audit["local"]["local_core"]["deduped_within_entry_senses"] == 37
    assert audit["local"]["local_core"]["bilingual_glosses_split"] == 18759
    assert audit["local"]["local_core"]["pure_ta_moved_from_en"] == 54
    assert audit["local"]["local_core"]["kalaichol_prefix_stripped"] == 6
    assert audit["local"]["local_core"]["corrupted_domains_cleared"] == 1886
    assert audit["local"]["local_core"]["corrupted_entry_domains_cleared"] == 1886
    assert audit["local"]["local_core"]["salvaged_tamil_domains_to_gloss"] == 1878
    assert audit["local"]["local_core"]["wordnet_domains_mapped"] == 242
    assert audit["local"]["local_core"]["wordnet_domains_dropped"] == 178
    assert audit["local"]["local_core"]["homograph_headwords_count"] == 389
    assert audit["local"]["local_terminology"]["mojibake_repaired_count"] == 16
    assert audit["local"]["local_terminology"]["mojibake_flagged_unrepaired_count"] == 0
    assert audit["local"]["local_terminology"]["mojibake_quarantined_count"] == 0
    assert audit["local"]["local_terminology"]["unbalanced_parens_fixed"] == 271
    assert audit["local"]["local_terminology"]["dropped_junk_glosses_count"] == 2
    assert audit["local"]["local_terminology"]["domain_typos_fixed"] == 4091
    assert audit["local"]["local_terminology"]["deduped_sorkuvai_merged"] >= 2205
    assert audit["local"]["local_phrases"]["tamil_domains_reclassified"] == 46
    assert audit["local"]["local_phrases"]["wordnet_domains_mapped"] == 325
    assert audit["local"]["local_phrases"]["wordnet_domains_dropped"] == 188
    assert audit["local"]["local_phrases"]["backfilled_glosses"] == 10
    assert audit["local"]["local_phrases"]["quarantined_empty_senses"] == 398
    assert audit["local"]["local_relations"]["valid_relations"] == 30858
    assert audit["local"]["local_relations"]["deduplicated_relations"] == 61
    assert audit["local"]["local_relations"]["expanded_symmetric_edges"] == 11070
    assert audit["open"]["tawiktionary_quarantined_mojibake_count"] == 7
    assert audit["open"]["tawiktionary_quarantined_mojibake_defs_count"] == 10
    assert audit["open"]["tawiktionary_routed_ascii_defs"] == 10208
    assert audit["open"]["packs"]["ta_wiktionary"]["entry_count"] == 85882

    real_gate = run_quality_gate(DEFAULT_OUT_DIR)
    assert real_gate["status"] == "pass"
    assert real_gate["failure_count"] == 0

    # Verify all 12 pack directories, schemas, sorting, UTF-8 no BOM, LF endings
    expected_open = {"core", "names_taxa", "regional", "ta_wiktionary"}
    expected_local = {
        "local_core", "local_terminology", "local_phrases", "local_dialect",
        "local_literary", "local_names_taxa", "local_loans", "local_relations",
    }
    assert {p.name for p in (DEFAULT_OUT_DIR / "open").iterdir() if p.is_dir()} == expected_open
    assert {p.name for p in (DEFAULT_OUT_DIR / "local").iterdir() if p.is_dir()} == expected_local

    required_entry_keys = {
        "entry_id", "headword", "pos", "forms", "senses", "domain", "region",
        "register", "origin_language", "pure_tamil_equivalent", "standard_equivalent",
        "scientific_name", "literary_source", "source_id", "source_locator",
        "rights_status", "permalink",
    }
    optional_morph_keys = {
        "verb_class", "transitivity", "root_word", "etymology_type",
        "dedr_id", "sandhi_behavior", "animacy_gender", "frequency_tier",
    }
    required_manifest_keys = {
        "schema_version", "pack_id", "pack_tier", "rights_status", "license",
        "dataset_version", "description", "source_ids", "attribution_notice",
        "entry_count", "sense_count", "relation_count", "distinct_headwords",
    }

    for pack_dir in sorted(
        [*(DEFAULT_OUT_DIR / "open").iterdir(), *(DEFAULT_OUT_DIR / "local").iterdir()]
    ):
        manifest_path = pack_dir / "manifest.json"
        entries_path = pack_dir / "entries.jsonl"
        relations_path = pack_dir / "relations.jsonl"
        for fpath in (manifest_path, entries_path, relations_path):
            raw = fpath.read_bytes()
            assert not raw.startswith(b"\xef\xbb\xbf"), f"BOM in {fpath}"
            assert b"\r" not in raw, f"CR in {fpath}"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert set(manifest.keys()) == required_manifest_keys
        assert manifest["schema_version"] == 2
        assert manifest["dataset_version"] == "0.2.0"

        prev_key: tuple[str, str] | None = None
        seen_ids: set[str] = set()
        line_count = 0
        with entries_path.open(encoding="utf-8") as fh:
            for line in fh:
                line_count += 1
                obj = json.loads(line)
                if line_count <= 50:
                    assert required_entry_keys <= set(obj.keys()) <= (required_entry_keys | optional_morph_keys)
                assert obj["headword"]
                assert unicodedata.is_normalized("NFC", obj["headword"])
                eid = obj["entry_id"]
                assert eid not in seen_ids
                seen_ids.add(eid)
                key = (obj["headword"], eid)
                if prev_key is not None:
                    assert key >= prev_key
                prev_key = key
        assert line_count == manifest["entry_count"]

        prev_rel: tuple[str, str, str, str] | None = None
        rel_count = 0
        with relations_path.open(encoding="utf-8") as fh:
            for line in fh:
                rel_count += 1
                rel = json.loads(line)
                rkey = (rel["source_headword"], rel["relation_code"], rel["target_headword"], rel["source_locator"])
                if prev_rel is not None:
                    assert rkey >= prev_rel
                prev_rel = rkey
        assert rel_count == manifest["relation_count"]

    # Second run to tmp_path must be byte-identical across all generated files
    second_out = tmp_path / "organized_run2"
    organize_lexicon(second_out, track="all")
    first_files = sorted(p.relative_to(DEFAULT_OUT_DIR) for p in DEFAULT_OUT_DIR.rglob("*") if p.is_file())
    second_files = sorted(p.relative_to(second_out) for p in second_out.rglob("*") if p.is_file())
    assert first_files == second_files
    for rel_path in first_files:
        assert (DEFAULT_OUT_DIR / rel_path).read_bytes() == (second_out / rel_path).read_bytes(), (
            f"Non-deterministic output in {rel_path}"
        )


def test_lexicon_quality_gate_rejects_defects(tmp_path: Path) -> None:
    """Verify lexicon_quality_gate catches Tamil domains, WordNet tags, HTML, mojibake, case dups, and bad manifests."""
    pack_dir = tmp_path / "open" / "bad_pack"
    pack_dir.mkdir(parents=True)
    bad_entries = [
        {
            "entry_id": "e1",
            "headword": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf&nbsp;",
            "pos": "NOUN",
            "forms": [],
            "senses": [
                {
                    "gloss_ta": "ok",
                    "gloss_en": "bad\u00a2",
                    "definition_ta": None,
                    "definition_en": "<!--comment-->",
                    "examples": [],
                    "domain": "noun.animal, \u0ba4\u0bae\u0bbf\u0bb4\u0bcd",
                    "region": None,
                    "register": "Colloquial, \u0ba4\u0bae\u0bbf\u0bb4\u0bcd",
                }
            ],
            "domain": "agriculture",
            "region": None,
            "register": None,
        },
        {
            "entry_id": "e2",
            "headword": "\u0b85\u0bb1\u0bae\u0bcd",
            "pos": "NOUN",
            "forms": [],
            "senses": [],
            "domain": "Agriculture",
            "region": None,
            "register": None,
        },
    ]
    (pack_dir / "entries.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in bad_entries) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "cleaning_audit.json").write_text(
        json.dumps({
            "local": {
                "accounting_exact": True,
                "expected_historical_csv_rows": 100,
                "total_accounted_rows": 99,
                "per_file_accounted_rows": {"a.csv": 99},
            }
        }),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps({
            "schema_version": 2,
            "pack_count": 1,
            "packs": [
                {
                    "file": "open/bad_pack.tlpack",
                    "summary": {
                        "pack_id": "bad_pack",
                        "domains": ["anatomy, astrology"],
                        "registers": ["childish, slang"],
                        "regions": ["SL, TN"],
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    report = run_quality_gate(
        tmp_path,
        manifest_path=manifest_path,
        expected_historical_rows=100,
    )
    assert report["status"] == "fail"
    details = " | ".join(f["detail"] for f in report["failures"])
    assert "HTML entity/comment in headword" in details
    assert "Mojibake character in gloss_en" in details
    assert "HTML entity/comment in definition_en" in details
    assert "Raw WordNet lexname in domain" in details
    assert "Tamil script in domain token" in details
    assert "Tamil script in register token" in details
    assert "Non-lowercase register token" in details
    assert "Case-duplicate domain tokens" in details
    assert "Historical row accounting mismatch" in details
    assert "Non-atomic comma/semicolon-joined token in domains" in details
    assert "Non-atomic comma/semicolon-joined token in registers" in details
    assert "Non-atomic comma/semicolon-joined token in regions" in details

    from tools.lexicon_quality_gate import main as quality_gate_main

    assert quality_gate_main([
        "--organized-dir",
        str(tmp_path),
        "--manifest",
        str(manifest_path),
        "--expected-historical-rows",
        "100",
    ]) == 1
