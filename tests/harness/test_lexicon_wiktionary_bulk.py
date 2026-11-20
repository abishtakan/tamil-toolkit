"""Focused unit and dry-run tests for Track 2B bulk Wiktionary parser, cleaner, and pack router."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import unicodedata

import pytest

from tools.lexicon import allocate_id
from tools.lexicon_packs import validate_canonical_dir
from tools.lexicon_tables import read_rows
from tools.lexicon_wiktionary_bulk import (
    BULK_SNAPSHOT_DATE,
    _build_bulk_pack_workspace,
    _build_pack_attribution_notice,
    _pack_namespace,
    assign_pack,
    check_unicode_scalar_integrity,
    clean_sense_line,
    parse_wiktionary_page,
    promote_bulk_packs,
    run_bulk_dryrun,
)


def _make_page(
    *,
    pageid: int = 1001,
    revid: int = 9001,
    title: str = "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
    wikitext: str,
    categories: list[str] | None = None,
) -> dict:
    return {
        "pageid": pageid,
        "revid": revid,
        "title": title,
        "revision_timestamp": "2026-11-15T00:00:00Z",
        "user": "TestEditor",
        "sha1": "0" * 40,
        "wikitext_sha256": hashlib.sha256(wikitext.encode("utf-8")).hexdigest(),
        "permalink_url": f"https://en.wiktionary.org/w/index.php?oldid={revid}",
        "history_url": "https://en.wiktionary.org/w/index.php?action=history",
        "categories": categories or ["Category:Tamil lemmas"],
        "wikitext": wikitext,
    }


def test_pos_homograph_separation_and_non_tamil_isolation() -> None:
    """Multi-POS Tamil page emits distinct (headword, POS) entries and ignores non-Tamil sections."""
    wt = "\n".join([
        "==Malayalam==",
        "===Noun===",
        "# should not leak from Malayalam",
        "",
        "==Tamil==",
        "===Pronunciation===",
        "* {{ta-IPA}}",
        "",
        "===Interjection===",
        "{{ta-interj}}",
        "# [[thank you]]",
        "",
        "===Noun===",
        "{{ta-noun}}",
        "# [[gratitude]], [[thanks]]",
        "#: {{ux|ta|example line}}",
        "",
        "===Verb===",
        "{{ta-verb}}",
        "# to [[thank]]",
        "{{ta-conj|...}}",
        "",
        "==Sanskrit==",
        "===Noun===",
        "# should not leak from Sanskrit",
    ])
    parsed = parse_wiktionary_page(_make_page(wikitext=wt))
    entries = parsed["entries"]
    assert [(e["headword"], e["pos_code"]) for e in entries] == [
        ("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "INTJ"),
        ("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "NOUN"),
        ("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", "VERB"),
    ]
    assert len({e["entry_id"] for e in entries}) == 3
    assert [s["meaning_en"] for s in entries[0]["senses"]] == ["thank you"]
    assert [s["meaning_en"] for s in entries[1]["senses"]] == ["gratitude, thanks"]
    assert [s["meaning_en"] for s in entries[2]["senses"]] == ["to thank"]

    reasons = {exc["reason_code"] for exc in parsed["exclusions"]}
    assert "NON_TAMIL_SECTION_EXCLUDED" in reasons
    assert "PRONUNCIATION_SECTION_EXCLUDED" in reasons
    assert "TEMPLATE_TA_IPA_EXCLUDED" in reasons
    assert "USAGE_EXAMPLE_OR_SYNONYM_EXCLUDED" in reasons
    assert "CONJUGATION_TEMPLATE_EXCLUDED" in reasons


def test_kalaichol_placeholder_and_html_rejected() -> None:
    """Reject (கலைச்சொல்) placeholders, HTML tags, comments, and empty glosses fail-closed."""
    r1 = clean_sense_line("# (\u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd)")
    assert r1["ok"] is False
    assert r1["reason_code"] == "KALAICHOL_PLACEHOLDER_REJECTED"

    for bad in (
        "# gloss <ref>cite</ref>",
        "# <span class='x'>word</span>",
        "# word <!-- comment -->",
    ):
        res = clean_sense_line(bad)
        assert res["ok"] is False
        assert res["reason_code"] == "HTML_TAG_OR_COMMENT_REJECTED"

    empty = clean_sense_line("#   ")
    assert empty["ok"] is False
    assert empty["reason_code"] == "EMPTY_GLOSS_REJECTED"


def test_unexpanded_template_and_forbidden_claims_rejected() -> None:
    """Reject unknown/unexpanded templates, unverified Module:ta-IPA, *PDr/DEDR, and verb_conjugations."""
    unk = clean_sense_line("# {{unallowlisted-macro|foo|bar}}")
    assert unk["ok"] is False
    assert unk["reason_code"] == "UNEXPANDED_TEMPLATE_REJECTED:unallowlisted-macro"

    for bad_line, expected_reason in (
        ("# {{ta-IPA|foo}}", "FORBIDDEN_TA_IPA_TEMPLATE_REJECTED"),
        ("# Module:ta-IPA output", "FORBIDDEN_TA_IPA_MODULE_REJECTED"),
        ("# from *PDr-1234", "FORBIDDEN_SYNTHETIC_PDR_REJECTED"),
        ("# see DEDR 314", "FORBIDDEN_UNPINNED_DEDR_REJECTED"),
        ("# {{ta-conj|1}}", "FORBIDDEN_CONJUGATION_TEMPLATE_REJECTED"),
        ("# broken verb_conjugations row", "FORBIDDEN_VERB_CONJUGATION_CLAIM_REJECTED"),
    ):
        res = clean_sense_line(bad_line)
        assert res["ok"] is False
        assert res["reason_code"] == expected_reason


def test_tamil_script_in_english_gloss_rejected() -> None:
    """Reject any Tamil Unicode scalar leaking inside an English meaning_en gloss."""
    res = clean_sense_line("# meaning in English with \u0ba4\u0bae\u0bbf\u0bb4\u0bcd leaked")
    assert res["ok"] is False
    assert res["reason_code"] == "TAMIL_IN_ENGLISH_GLOSS_REJECTED"

    # Also ensure an entry whose only sense is rejected produces 0 clean entries.
    wt = "==Tamil==\n===Noun===\n# bad \u0ba4\u0bae\u0bbf\u0bb4\u0bcd gloss\n"
    parsed = parse_wiktionary_page(_make_page(wikitext=wt))
    assert parsed["entries"] == []
    assert any(e["reason_code"] == "ENTRY_NO_VALID_SENSES_REMAINING" for e in parsed["exclusions"])


def test_safe_template_unwrapping_and_pluricentric_pack_routing() -> None:
    """Unwrap safe markup, map TN/SL dialect & register labels, and partition PROPN/regional/core."""
    # 1. SL Jaffna dialect noun -> regional pack
    wt_sl = "\n".join([
        "==Tamil==",
        "===Noun===",
        "# {{lb|ta|Sri Lanka|Jaffna|colloquial}} [[bicycle]] {{defdate|20th c.}}",
        "# {{ng|{{q|literary}} Used as an honorific particle.}}",
    ])
    parsed_sl = parse_wiktionary_page(
        _make_page(pageid=2001, title="\u0b89\u0ba8\u0bcd\u0ba4\u0bc1\u0bb5\u0ba3\u0bcd\u0b9f\u0bbf", wikitext=wt_sl)
    )
    assert len(parsed_sl["entries"]) == 1
    ent_sl = parsed_sl["entries"][0]
    assert ent_sl["pack_id"] == "regional"
    assert ent_sl["senses"][0]["meaning_en"] == "(Sri Lanka, Jaffna, colloquial) bicycle [20th c.]"
    assert ent_sl["senses"][1]["component"] == "gloss"
    assert ent_sl["senses"][1]["meaning_en"] == "(literary) Used as an honorific particle."
    quals = {(q["dimension"], q["code"]) for s in ent_sl["senses"] for q in s["qualifiers"]}
    assert ("region", "SL") in quals
    assert ("region", "JAFFNA") in quals
    assert ("register", "colloquial") in quals
    assert ("register", "literary") in quals

    # 2. TN regional markers (Kongu / Chennai) -> regional pack
    for label_tok, expected_code in (
        ("Tamil Nadu", "TN"),
        ("Kongu", "KONGU"),
        ("Batticaloa", "BATTICALOA"),
        ("Vanni", "VANNI"),
        ("Up-Country", "UP_COUNTRY"),
    ):
        wt_reg = f"==Tamil==\n===Noun===\n# {{{{lb|ta|{label_tok}}}}} regional term\n"
        p_reg = parse_wiktionary_page(_make_page(pageid=2002, title="\u0b85\u0bae\u0bcd\u0bae\u0bbe", wikitext=wt_reg))
        assert p_reg["entries"][0]["pack_id"] == "regional"
        assert p_reg["entries"][0]["senses"][0]["qualifiers"][0]["code"] == expected_code

    # 3. PROPN -> names_taxa pack (even if regional tag is present, PROPN routes cleanly to names_taxa)
    wt_propn = "==Tamil==\n===Proper noun===\n# {{lb|ta|Sri Lanka}} a city in northern Sri Lanka\n"
    p_propn = parse_wiktionary_page(
        _make_page(
            pageid=2003,
            title="\u0baf\u0bbe\u0bb4\u0bcd\u0baa\u0bcd\u0baa\u0bbe\u0ba3\u0bae\u0bcd",
            wikitext=wt_propn,
            categories=["Category:Tamil proper nouns"],
        )
    )
    assert p_propn["entries"][0]["pos_code"] == "PROPN"
    assert p_propn["entries"][0]["pack_id"] == "names_taxa"

    # 4. Standard lemma without regional markers -> core pack
    wt_core = "==Tamil==\n===Adjective===\n# {{lb|ta|formal|archaic}} [[ancient]], [[old]]\n"
    p_core = parse_wiktionary_page(_make_page(pageid=2004, title="\u0baa\u0bb4\u0bc8\u0baf", wikitext=wt_core))
    assert p_core["entries"][0]["pos_code"] == "ADJ"
    assert p_core["entries"][0]["pack_id"] == "core"
    assert assign_pack(p_core["entries"][0])[0] == "core"

    # 5. Safe {{tcl}} and {{tlb}} and &!& separator filtering + grammar_system mapping
    wt_tcl = "\n".join([
        "==Tamil==",
        "===Noun===",
        "# {{tcl|ta|tiger|id=Q19939|nogloss=1|lb=uncommon}}, [[panther]]",
        "# {{tlb|ta|poetic|&!&|transitive}} [[pearl]]",
    ])
    p_tcl = parse_wiktionary_page(_make_page(pageid=2005, title="\u0baa\u0bc1\u0bb2\u0bbf", wikitext=wt_tcl))
    assert p_tcl["entries"][0]["senses"][0]["meaning_en"] == "(uncommon) tiger, panther"
    assert p_tcl["entries"][0]["senses"][1]["meaning_en"] == "(poetic, transitive) pearl"
    tcl_quals = {(q["dimension"], q["code"]) for s in p_tcl["entries"][0]["senses"] for q in s["qualifiers"]}
    assert ("period", "rare") in tcl_quals
    assert ("register", "poetic") in tcl_quals
    assert ("grammar_system", "transitive") in tcl_quals


def test_unicode_scalar_integrity_joiners_bom_controls_and_nfc() -> None:
    """Reject BOM, C0/C1 controls, and unexpected ZWJ/ZWNJ; normalize valid NFD Tamil to NFC."""
    zwnj = chr(0x200C)
    zwj = chr(0x200D)
    bom = chr(0xFEFF)

    # BOM rejected in headword and sense
    ok_bom, err_bom, _ = check_unicode_scalar_integrity(bom + "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf")
    assert ok_bom is False and err_bom == "UNICODE_BOM_REJECTED"

    # C0 control rejected
    ok_ctl, err_ctl, _ = check_unicode_scalar_integrity("bad\x07gloss")
    assert ok_ctl is False and err_ctl == "UNICODE_CONTROL_OR_FORMAT_REJECTED"

    # Unexpected ZWNJ / ZWJ rejected (never silently stripped)
    for joiner in (zwnj, zwj):
        ok_j, err_j, meta_j = check_unicode_scalar_integrity("\u0b95" + joiner + "\u0ba9\u0bcd")
        assert ok_j is False
        assert err_j == "UNEXPECTED_JOINER_REJECTED"
        assert len(meta_j["joiners"]) == 1

    wt_joiner = "==Tamil==\n===Noun===\n# gloss with " + zwj + " joiner\n"
    parsed_j = parse_wiktionary_page(_make_page(wikitext=wt_joiner))
    assert parsed_j["entries"] == []
    assert any(e["reason_code"] == "SENSE_UNEXPECTED_JOINER_REJECTED" for e in parsed_j["exclusions"])

    # Valid NFD Tamil headword is normalized to NFC
    nfd_tamil = unicodedata.normalize("NFD", "\u0b94\u0bb5\u0bc8")
    assert not unicodedata.is_normalized("NFC", nfd_tamil)
    ok_nfc, err_nfc, meta_nfc = check_unicode_scalar_integrity(nfd_tamil)
    assert ok_nfc is True and err_nfc is None
    assert meta_nfc["nfc_normalized"] is True
    assert unicodedata.is_normalized("NFC", meta_nfc["normalized_text"])


def test_dryrun_end_to_end_and_tamper_rejection(tmp_path: Path) -> None:
    """Verify end-to-end multi-pack dryrun from gzipped JSONL and SHA-256 tamper failure."""
    snap_dir = tmp_path / "snap"
    snap_dir.mkdir()
    pages = [
        _make_page(pageid=1, revid=10, title="\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", wikitext="==Tamil==\n===Noun===\n# gratitude\n===Interjection===\n# thank you\n"),
        _make_page(pageid=2, revid=20, title="\u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8", wikitext="==Tamil==\n===Proper noun===\n# Chennai\n", categories=["Category:Tamil proper nouns"]),
        _make_page(pageid=3, revid=30, title="\u0b95\u0bc1\u0bb0\u0bc1\u0bb5\u0bbf", wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Jaffna}} sparrow\n"),
    ]
    gz_path = snap_dir / "pages.jsonl.gz"
    with gz_path.open("wb") as raw:
        with gzip.GzipFile(filename="pages.jsonl", mode="wb", fileobj=raw, mtime=0) as gz:
            for p in pages:
                gz.write((json.dumps(p, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"))

    manifest = {
        "schema": "enwiktionary-tamil-bulk-snapshot-v1",
        "license": "CC-BY-SA-4.0 / GFDL",
        "pages_jsonl_gz_sha256": hashlib.sha256(gz_path.read_bytes()).hexdigest(),
        "total_fetched_pages": 3,
    }
    (snap_dir / "snapshots_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    out_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"
    report = run_bulk_dryrun(snap_dir, out_dir, report_path)
    assert report["pages_processed"] == 3
    assert report["total_clean_entries"] == 4
    assert report["total_clean_senses"] == 4
    assert report["multi_pos_homograph_headwords"] == 1
    assert report["packs"] == {
        "core": {"entries": 2, "senses": 2},
        "names_taxa": {"entries": 1, "senses": 1},
        "regional": {"entries": 1, "senses": 1},
    }

    # Tamper manifest SHA-256 -> fail closed
    manifest["pages_jsonl_gz_sha256"] = "f" * 64
    (snap_dir / "snapshots_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        run_bulk_dryrun(snap_dir, out_dir, report_path)


def test_promote_bulk_packs_preserves_poc_and_validates_multipack(tmp_path: Path) -> None:
    """Verify multi-pack deterministic promotion, PoC preservation, compact sources, and zero ID collisions."""
    repo_root = Path(__file__).resolve().parents[2]
    reviewed_dir = repo_root / "data/curation/wiktionary-core-reviewed"
    snap_dir = tmp_path / "snap"
    snap_dir.mkdir()
    pages = [
        # Duplicate of reviewed PoC (நன்றி NOUN & INTJ) -> must be skipped in core bulk!
        _make_page(
            pageid=1,
            revid=10,
            title="\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
            wikitext="==Tamil==\n===Noun===\n# gratitude bulk dup\n===Interjection===\n# thanks bulk dup\n",
        ),
        # Fresh core entry
        _make_page(
            pageid=2,
            revid=20,
            title="\u0b85\u0bae\u0bcd\u0bae\u0bbe",
            wikitext="==Tamil==\n===Noun===\n# mother\n",
        ),
        # names_taxa entry
        _make_page(
            pageid=3,
            revid=30,
            title="\u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8",
            wikitext="==Tamil==\n===Proper noun===\n# Chennai\n",
            categories=["Category:Tamil proper nouns"],
        ),
        # regional entry
        _make_page(
            pageid=4,
            revid=40,
            title="\u0b95\u0bc1\u0bb0\u0bc1\u0bb5\u0bbf",
            wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Jaffna}} sparrow\n",
        ),
    ]
    gz_path = snap_dir / "pages.jsonl.gz"
    with gz_path.open("wb") as raw:
        with gzip.GzipFile(filename="pages.jsonl", mode="wb", fileobj=raw, mtime=0) as gz:
            for p in pages:
                gz.write((json.dumps(p, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"))

    manifest = {
        "schema": "enwiktionary-tamil-bulk-snapshot-v1",
        "license": "CC-BY-SA-4.0 / GFDL",
        "pages_jsonl_gz_sha256": hashlib.sha256(gz_path.read_bytes()).hexdigest(),
        "total_fetched_pages": len(pages),
    }
    (snap_dir / "snapshots_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    curation_root = tmp_path / "curation"
    outputs = {
        "core": tmp_path / "canonical/dictionary",
        "names_taxa": tmp_path / "canonical/packs/names_taxa",
        "regional": tmp_path / "canonical/packs/regional",
    }
    result = promote_bulk_packs(
        snap_dir,
        curation_root=curation_root,
        reviewed_dir=reviewed_dir,
        output_dirs=outputs,
        check_native=False,
    )

    assert sorted(result["skipped_core_duplicates"]) == [
        "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf:INTJ",
        "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf:NOUN",
    ]
    poc_sources = list(read_rows(reviewed_dir / "sources.csv"))
    assert result["packs"]["core"]["reviewed_entries"] == 6
    assert result["packs"]["core"]["bulk_entries"] == 1
    assert result["packs"]["core"]["promoted_entries"] == 7
    assert result["packs"]["core"]["promoted_sources"] == len(poc_sources) + 1
    assert result["packs"]["names_taxa"]["promoted_entries"] == 1
    assert result["packs"]["names_taxa"]["promoted_sources"] == 1
    assert result["packs"]["regional"]["promoted_entries"] == 1
    assert result["packs"]["regional"]["promoted_sources"] == 1

    # Verify all 6 PoC entries + accepted_human decisions preserved verbatim
    poc_entries = list(read_rows(reviewed_dir / "entries.csv"))
    poc_entry_ids = {r["entry_id"] for r in poc_entries}
    core_entries = list(read_rows(outputs["core"] / "entries.csv"))
    assert poc_entry_ids <= {r["entry_id"] for r in core_entries}
    core_decisions = list(read_rows(outputs["core"] / "decisions.csv"))
    assert any(r["outcome"] == "accepted_human" for r in core_decisions)

    # Verify per-page provenance inside evidence.csv locator_json and zero ID collisions
    seen_ids_by_col: dict[str, set[str]] = {
        k: set()
        for k in ("entry_id", "form_id", "sense_id", "text_id", "entity_id", "assertion_id", "decision_id")
    }
    from tools.lexicon_wiktionary_bulk import SHARED_REGION_HIERARCHY

    expected_region_parent = {code: parent for code, parent, _disp in SHARED_REGION_HIERARCHY}
    canonical_region_parents: dict[str, str | None] = {}
    for pack_id, cdir in outputs.items():
        assert validate_canonical_dir(cdir) == []
        ws_cc_sha = hashlib.sha256((curation_root / f"wiktionary-{pack_id}-auto/notices/cc_by_sa_4_0_legalcode.txt").read_bytes()).hexdigest()
        assert ws_cc_sha == "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5"
        cc_sha = hashlib.sha256((cdir / "notices/CC-BY-SA-4.0.md").read_bytes()).hexdigest()
        assert cc_sha == "c43eb2bbda324657d313086b6f678e1ca40eace396b91bed1a24ba4f01c94010"
        notice_txt = (cdir / "notices/ATTRIBUTION_AND_LICENSE.md").read_text(encoding="utf-8")
        assert "C:\\" not in notice_txt and "/Users/" not in notice_txt and "/home/" not in notice_txt
        if pack_id == "core":
            assert "Preserved Human-Reviewed PoC Revisions" in notice_txt
            assert "| `1921` |" in notice_txt
            assert "| `32793` |" in notice_txt

        source_rows = list(read_rows(cdir / "sources.csv"))
        bulk_source_ids = {
            r["source_id"]
            for r in source_rows
            if str(r.get("label_json", "")).strip('"').startswith("enwiktionary_ta_bulk_")
        }
        assert len(bulk_source_ids) == 1
        for row in source_rows:
            assert row["evidence_verification_state"] == "verified"
            assert row["reuse_state"] == "permitted"

        bulk_ev_count = 0
        for ev in read_rows(cdir / "evidence.csv"):
            if ev["source_id"] in bulk_source_ids:
                bulk_ev_count += 1
                assert ev["evidence_role"] == "supports"
                loc = json.loads(ev["locator_json"])
                for key in ("pageid", "revid", "timestamp", "title", "wikitext_sha256", "history_url", "permalink", "license"):
                    assert key in loc
        assert bulk_ev_count > 0

        for tbl, col in (
            ("entries", "entry_id"),
            ("forms", "form_id"),
            ("senses", "sense_id"),
            ("texts", "text_id"),
            ("identities", "entity_id"),
            ("assertions", "assertion_id"),
            ("decisions", "decision_id"),
        ):
            ids = {r[col] for r in read_rows(cdir / f"{tbl}.csv")}
            assert not (seen_ids_by_col[col] & ids), f"Cross-pack ID collision in {tbl}.{col}"
            seen_ids_by_col[col].update(ids)

        for r in read_rows(cdir / "labels.csv"):
            if r["category"] == "region":
                prev = canonical_region_parents.setdefault(r["code"], r["parent_code"])
                assert prev == r["parent_code"]
                if r["code"] in expected_region_parent:
                    assert r["parent_code"] == expected_region_parent[r["code"]]

    assert canonical_region_parents.get("JAFFNA") == "SL"


def _pinned_kodi_page() -> dict:
    """Return pinned page for கோடி (pageid=50557, revid=88721939)."""
    return _make_page(
        pageid=50557,
        revid=88721939,
        title="\u0b95\u0bcb\u0b9f\u0bbf",
        wikitext="\n".join([
            "==Tamil==",
            "===Pronunciation===",
            "* {{ta-IPA}}",
            "===Etymology 1===",
            "====Noun====",
            "# [[end]], [[tip]], [[point]]",
            "# [[cape]], [[headland]], [[promontory]]",
            "=====Declension=====",
            "{{ta-decl}}",
            "===Etymology 2===",
            "====Numeral====",
            "# [[crore]], [[10,000,000]] = [[ten million]]",
            "====Adverb====",
            "{{ta-adv}} {{tlb|ta|[[w:Kanyakumari_district#Language|Kanyakumari dialect]]}}",
            "# [[very]]",
            "===Etymology 3===",
            "====Noun====",
            "# [[bend]], [[curve]]",
            "# [[garland]] worn on the head",
        ]),
    )


def _pinned_salli_page() -> dict:
    """Return pinned page for சல்லி (pageid=9679479, revid=85012070)."""
    return _make_page(
        pageid=9679479,
        revid=85012070,
        title="\u0b9a\u0bb2\u0bcd\u0bb2\u0bbf",
        wikitext="\n".join([
            "==Tamil==",
            "===Etymology 1===",
            "====Noun====",
            "# [[small]] [[piece]]s of [[stone]] or [[glass]], [[potsherd]]",
            "# {{lb|ta|colloquial}} a [[villain]]",
            "===Etymology 2===",
            "====Noun====",
            "{{ta-noun}} {{tlb|ta|Puducherry}}",
            "# {{lb|ta|architecture}} [[moulding]] [[work]]",
            "===Etymology 4===",
            "====Noun====",
            "{{ta-noun}} {{tlb|ta|archaic}}",
            "# a [[kind]] of [[drum]]",
            "===Etymology 5===",
            "====Noun====",
            "# [[liquorice]]",
        ]),
    )


def _pinned_neer_page() -> dict:
    """Return pinned page for நீர் (pageid=311163, revid=92074328)."""
    return _make_page(
        pageid=311163,
        revid=92074328,
        title="\u0ba8\u0bc0\u0bb0\u0bcd",
        categories=["Category:Tamil dialectal terms", "Category:Tamil lemmas"],
        wikitext="\n".join([
            "==Tamil==",
            "===Etymology 1===",
            "====Noun====",
            "{{ta-noun}} {{tlb|ta|uncountable}}",
            "# {{lb|ta|usually|formal}} [[water]]",
            "# [[fluid]], [[liquid]], [[juice]], [[succulence]]",
            "====Verb====",
            "{{ta-verb}} {{tlb|ta|intransitive}}",
            "# to become [[thin]] or [[watery]] (as liquid food in cooking)",
            "===Etymology 2===",
            "====Pronoun====",
            "{{head|ta|pronoun}} {{tlb|ta|higher register|or|dialectal}}",
            "# [[you all]]",
            "# {{lb|ta|honorific}} [[you]]",
            "=====Synonyms=====",
            "* {{l|ta|\u0ba4\u0bc0\u0bb0\u0bcd\u0ba4\u0bcd\u0ba4\u0bae\u0bcd<l:dialectal>}}",
        ]),
    )


def _pinned_ezhuththu_page() -> dict:
    """Return pinned page for எழுத்து (pageid=1009847, revid=87448475)."""
    return _make_page(
        pageid=1009847,
        revid=87448475,
        title="\u0b8e\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1",
        categories=["Category:Tamil dialectal terms", "Category:Tamil lemmas"],
        wikitext="\n".join([
            "==Tamil==",
            "===Noun===",
            "# [[writing]]",
            "# {{lb|ta|orthography}} [[letter]], [[character]] {{gloss|symbol}}",
            "# {{lb|ta|dialectal}} [[letter]]; [[post]]",
            "# {{lb|ta|now|rare}} [[painting]], [[picture]], [[drawing]]",
        ]),
    )


def _pinned_poo_page() -> dict:
    """Return pinned page for பூ (pageid=6363510, revid=88994575)."""
    return _make_page(
        pageid=6363510,
        revid=88994575,
        title="\u0baa\u0bc2",
        categories=["Category:Tamil dialectal terms", "Category:Tamil lemmas"],
        wikitext="\n".join([
            "==Tamil==",
            "===Etymology 1===",
            "====Noun====",
            "# [[flower]]",
            "# {{lb|ta|dialectal}} [[crop]]",
            "====Verb====",
            "# {{lb|ta|intransitive}} to [[blossom]], [[bloom]], [[flower]]",
            "===Etymology 2===",
            "====Noun====",
            "{{ta-noun}} {{tlb|ta|often|in compounds}}",
            "# [[earth]], [[world]]",
        ]),
    )


def _pinned_thattu_page() -> dict:
    """Return pinned page for தட்டு (pageid=7322016, revid=89879194)."""
    return _make_page(
        pageid=7322016,
        revid=89879194,
        title="\u0ba4\u0b9f\u0bcd\u0b9f\u0bc1",
        wikitext="\n".join([
            "==Tamil==",
            "===Etymology 1===",
            "====Verb====",
            "# {{lb|ta|transitive}} to [[knock]], [[tap]], [[pat]]",
            "# {{lb|ta|intransitive}} to be at [[fault]]; to [[fail]], [[halt]] {{q|as the hand in playing on an instrument, writing, performing an operation, as the tongue in reading or speaking, etc.}}",
            "===Etymology 2===",
            "====Noun====",
            "# [[plate]], [[dish]], [[platter]], [[tray]]",
        ]),
    )


def test_same_pos_multi_etymology_and_repeated_pos_preserve_distinct_entries() -> None:
    """Distinct same-POS headings across or within etymologies must emit separate entries and deterministic IDs."""
    # 1. Real pinned கோடி: 2 distinct Etymology Noun entries + NUM + ADV
    kodi = _pinned_kodi_page()
    parsed_kodi_1 = parse_wiktionary_page(kodi)
    parsed_kodi_2 = parse_wiktionary_page(kodi)
    assert parsed_kodi_1 == parsed_kodi_2

    kodi_entries = parsed_kodi_1["entries"]
    assert [(e["pos_code"], e["etymology_heading"], e["pos_occurrence_index"]) for e in kodi_entries] == [
        ("NOUN", "Etymology 1", 0),
        ("NUM", "Etymology 2", 0),
        ("ADV", "Etymology 2", 0),
        ("NOUN", "Etymology 3", 1),
    ]
    assert len({e["entry_id"] for e in kodi_entries}) == 4
    assert [s["meaning_en"] for s in kodi_entries[0]["senses"]] == ["end, tip, point", "cape, headland, promontory"]
    assert [s["meaning_en"] for s in kodi_entries[3]["senses"]] == ["bend, curve", "garland worn on the head"]
    assert [s["ordinal"] for s in kodi_entries[3]["senses"]] == [1, 2]

    # 2. Real pinned சல்லி: 4 distinct Etymology Noun entries
    salli = parse_wiktionary_page(_pinned_salli_page())
    salli_nouns = [e for e in salli["entries"] if e["pos_code"] == "NOUN"]
    assert len(salli_nouns) == 4
    assert len({e["entry_id"] for e in salli_nouns}) == 4
    assert [e["pos_occurrence_index"] for e in salli_nouns] == [0, 1, 2, 3]
    assert [e["senses"][0]["meaning_en"] for e in salli_nouns] == [
        "small pieces of stone or glass, potsherd",
        "(architecture) moulding work",
        "a kind of drum",
        "liquorice",
    ]

    # 3. Same-etymology repeated POS blocks must stay separate too
    vaadai = _make_page(
        pageid=7893754,
        revid=88000001,
        title="\u0bb5\u0bbe\u0b9f\u0bc8",
        categories=["Category:Tamil dialectal terms", "Category:Tamil lemmas"],
        wikitext="\n".join([
            "==Tamil==",
            "===Etymology===",
            "===Noun===",
            "# {{lb|ta|figurative}} [[sign]], [[presence]]",
            "===Noun===",
            "# {{lb|ta|dialectal}} [[row]] of [[house]]s",
        ]),
    )
    parsed_vaadai = parse_wiktionary_page(vaadai)
    assert len(parsed_vaadai["entries"]) == 2
    assert len({e["entry_id"] for e in parsed_vaadai["entries"]}) == 2
    assert [e["pos_occurrence_index"] for e in parsed_vaadai["entries"]] == [0, 1]
    assert [e["senses"][0]["ordinal"] for e in parsed_vaadai["entries"]] == [1, 1]


def test_category_tamil_dialectal_terms_and_isolated_entry_regional_routing() -> None:
    """Category:Tamil dialectal terms and other-POS/synonym tags never route core entries to regional."""
    for page in (_pinned_neer_page(), _pinned_ezhuththu_page(), _pinned_poo_page()):
        parsed = parse_wiktionary_page(page)
        assert len(parsed["entries"]) >= 1
        for ent in parsed["entries"]:
            assert ent["pack_id"] == "core", f"Expected core for {ent['headword']} ({ent['pos_code']}), got {ent['pack_id']} ({ent['pack_reason']})"

    # கோடி: ONLY Adverb has entry-level Kanyakumari qualifier -> regional; Nouns/Numeral -> core
    kodi = parse_wiktionary_page(_pinned_kodi_page())
    assert [e["pack_id"] for e in kodi["entries"]] == ["core", "core", "regional", "core"]
    assert kodi["entries"][2]["pack_reason"] == "entry_attested_region:KANYAKUMARI"
    assert ("region", "KANYAKUMARI") in {(q["dimension"], q["code"]) for q in kodi["entries"][2]["entry_qualifiers"]}

    # Negated headword qualifier ("rare|outside|Sri Lanka") must not invent SL regional restriction
    parai = _make_page(
        pageid=8050651,
        revid=89943257,
        title="\u0baa\u0bb1\u0bc8",
        wikitext="\n".join([
            "==Tamil==",
            "===Etymology 1===",
            "====Verb====",
            "{{ta-verb}} {{tlb|ta|rare|outside|Sri Lanka}}",
            "# {{lb|ta|transitive}} to [[speak]], [[say]]",
        ]),
    )
    parsed_parai = parse_wiktionary_page(parai)
    assert parsed_parai["entries"][0]["pack_id"] == "core"


def test_finite_qualifier_mapping_prose_preservation_and_label_aliases() -> None:
    """Stop arbitrary domain invention and comma-splitting; map conservative aliases only."""
    # 1. Comma-containing prose {{q|...}} in தட்டு must not be split or turned into domain codes
    thattu = parse_wiktionary_page(_pinned_thattu_page())
    verb_entry = thattu["entries"][0]
    prose_sense = verb_entry["senses"][1]
    assert (
        prose_sense["meaning_en"]
        == "(intransitive) to be at fault; to fail, halt (as the hand in playing on an instrument, writing, performing an operation, as the tongue in reading or speaking, etc.)"
    )
    assert [(q["dimension"], q["code"]) for q in prose_sense["qualifiers"]] == [("grammar_system", "intransitive")]
    assert len(prose_sense["unmapped_qualifiers"]) == 1
    assert (
        prose_sense["unmapped_qualifiers"][0]["raw_token"]
        == "as the hand in playing on an instrument, writing, performing an operation, as the tongue in reading or speaking, etc."
    )
    assert prose_sense["unmapped_qualifiers"][0]["status"] == "unstructured_pending_review"

    # 2. Long {{q|...}} alongside finite mapped domain {{lb|ta|Hinduism}} in யக்கியோபவீதம்
    yaj = _make_page(
        pageid=9393661,
        revid=89330304,
        title="\u0baf\u0b95\u0bcd\u0b95\u0bbf\u0baf\u0bcb\u0baa\u0bb5\u0bc0\u0ba4\u0bae\u0bcd",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Hinduism}} [[yajnopavita]] {{q|a [[sacred]] [[thread]] worn over the left shoulder and under the right arm by [[Brahmin]] men and boys}}\n",
    )
    parsed_yaj = parse_wiktionary_page(yaj)
    yaj_sense = parsed_yaj["entries"][0]["senses"][0]
    assert [(q["dimension"], q["code"]) for q in yaj_sense["qualifiers"]] == [("domain", "hinduism")]
    assert len(yaj_sense["unmapped_qualifiers"]) == 1
    assert "sacred thread worn over the left shoulder" in yaj_sense["unmapped_qualifiers"][0]["display_token"]

    # 3. Documented aliases (Nellai Tamil, Tirunelveli Tamil, Malaysian) vs unmapped localities (Puducherry, Pondicherry, Ramnad)
    rappojanam = _make_page(
        pageid=8727548,
        revid=89311145,
        title="\u0bb0\u0bbe\u0baa\u0bcd\u0baa\u0bcb\u0b9c\u0ba9\u0bae\u0bcd",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Christianity|Nellai Tamil}} [[holy]] [[communion]]; [[Eucharist]].\n",
    )
    p_rap = parse_wiktionary_page(rappojanam)
    assert p_rap["entries"][0]["pack_id"] == "regional"
    assert {(q["dimension"], q["code"]) for q in p_rap["entries"][0]["senses"][0]["qualifiers"]} == {
        ("domain", "christianity"),
        ("region", "NELLAI"),
    }

    makkal = _make_page(
        pageid=8808655,
        revid=91590002,
        title="\u0bae\u0b95\u0bcd\u0b95\u0bb3\u0bcd",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Tirunelveli Tamil|or|literary}} [[children]]\n",
    )
    p_makkal = parse_wiktionary_page(makkal)
    assert p_makkal["entries"][0]["pack_id"] == "regional"
    assert {(q["dimension"], q["code"]) for q in p_makkal["entries"][0]["senses"][0]["qualifiers"]} == {
        ("region", "NELLAI"),
        ("register", "literary"),
    }

    sataiyan = _make_page(
        pageid=8857398,
        revid=91653488,
        title="\u0b9a\u0b9f\u0bc8\u0baf\u0ba9\u0bcd",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Malaysian|derogatory}} a person of [[Chinese]] descent\n",
    )
    p_sat = parse_wiktionary_page(sataiyan)
    assert p_sat["entries"][0]["pack_id"] == "core"
    assert {(q["dimension"], q["code"]) for q in p_sat["entries"][0]["senses"][0]["qualifiers"]} == {
        ("region", "MY"),
        ("register", "derogatory"),
    }

    # Unmapped localities: Puducherry (headword in சல்லி), Pondicherry, Ramnad -> preserve literals, no invented domain or TN attestation
    p_salli = parse_wiktionary_page(_pinned_salli_page())
    puducherry_entry = p_salli["entries"][1]
    assert puducherry_entry["pack_id"] == "core"
    assert puducherry_entry["entry_qualifiers"] == []
    assert [u["raw_token"] for u in puducherry_entry["unmapped_entry_qualifiers"]] == ["Puducherry"]

    saaththu = _make_page(
        pageid=9713857,
        revid=86131389,
        title="\u0b9a\u0bbe\u0ba4\u0bcd\u0ba4\u0bc1",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Ramnad}} [[young]] [[plant]] [[transplanted]]\n",
    )
    p_saaththu = parse_wiktionary_page(saaththu)
    assert p_saaththu["entries"][0]["pack_id"] == "core"
    assert p_saaththu["entries"][0]["senses"][0]["qualifiers"] == []
    assert p_saaththu["entries"][0]["senses"][0]["meaning_en"] == "(Ramnad) young plant transplanted"
    assert [u["raw_token"] for u in p_saaththu["entries"][0]["senses"][0]["unmapped_qualifiers"]] == ["Ramnad"]

    # Display override syntax label!display renders display text cleanly without '!'
    bang_clean = clean_sense_line("# {{lb|ta|film!films|spiritualism!spiritual}} concept")
    assert bang_clean["ok"] is True
    assert bang_clean["meaning_en"] == "(films, spiritual) concept"
    assert "!" not in bang_clean["meaning_en"]


def test_promote_preserves_original_6_poc_payloads_and_deterministic_multi_etymology(tmp_path: Path) -> None:
    """Promotion preserves all 6 PoC entries/senses verbatim, keeps deterministic repeated-POS IDs, and prevents unmapped domain pollution."""
    repo_root = Path(__file__).resolve().parents[2]
    reviewed_dir = repo_root / "data/curation/wiktionary-core-reviewed"
    pages = [
        # All 5 real PoC pages (6 PoC entries in core)
        _make_page(
            pageid=4593930,
            revid=93647113,
            title="\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
            wikitext="==Tamil==\n===Interjection===\n# [[thanks]], [[thank you]]\n===Noun===\n# [[help]], [[kindness]]\n# [[gratitude]]\n",
        ),
        _make_page(
            pageid=11100687,
            revid=85842017,
            title="\u0b85\u0b9f\u0b9f\u0bbe",
            wikitext="==Tamil==\n===Interjection===\n# {{ng|an exclamation of [[surprise]].}}\n",
        ),
        _make_page(
            pageid=7769127,
            revid=89903937,
            title="\u0b85\u0ba8\u0bcd\u0ba8\u0bbf\u0bb2\u0bc8",
            wikitext="==Tamil==\n===Noun===\n# [[that]] [[moment]]\n",
        ),
        _make_page(
            pageid=9685129,
            revid=88382210,
            title="\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8",
            wikitext="==Tamil==\n===Noun===\n# [[notice]]\n# {{q|written}} [[appeal]]\n# {{lb|ta|catholicism}} [[confession]]\n",
        ),
        _make_page(
            pageid=7902117,
            revid=61485513,
            title="\u0b9a\u0bc6\u0baa\u0bcd\u0baa\u0bae\u0bcd",
            wikitext="==Tamil==\n===Noun===\n# [[straightness]]\n",
        ),
        # Multi-etymology, category-only, prose-q, and unmapped locality pages
        _pinned_kodi_page(),
        _pinned_salli_page(),
        _pinned_neer_page(),
        _pinned_thattu_page(),
        _make_page(
            pageid=9713857,
            revid=86131389,
            title="\u0b9a\u0bbe\u0ba4\u0bcd\u0ba4\u0bc1",
            wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Ramnad}} [[young]] [[plant]] [[transplanted]]\n",
        ),
        _make_page(
            pageid=3,
            revid=30,
            title="\u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8",
            wikitext="==Tamil==\n===Proper noun===\n# Chennai\n",
            categories=["Category:Tamil proper nouns"],
        ),
    ]

    snap_dir = tmp_path / "snap"
    snap_dir.mkdir()
    gz_path = snap_dir / "pages.jsonl.gz"
    with gz_path.open("wb") as raw:
        with gzip.GzipFile(filename="pages.jsonl", mode="wb", fileobj=raw, mtime=0) as gz:
            for p in pages:
                gz.write((json.dumps(p, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"))
    manifest = {
        "schema": "enwiktionary-tamil-bulk-snapshot-v1",
        "license": "CC-BY-SA-4.0 / GFDL",
        "pages_jsonl_gz_sha256": hashlib.sha256(gz_path.read_bytes()).hexdigest(),
        "total_fetched_pages": len(pages),
    }
    (snap_dir / "snapshots_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def _run_once(tag: str) -> tuple[dict, dict[str, Path], Path]:
        cur = tmp_path / f"curation_{tag}"
        outs = {
            "core": tmp_path / f"canonical_{tag}/dictionary",
            "names_taxa": tmp_path / f"canonical_{tag}/packs/names_taxa",
            "regional": tmp_path / f"canonical_{tag}/packs/regional",
        }
        res = promote_bulk_packs(snap_dir, curation_root=cur, reviewed_dir=reviewed_dir, output_dirs=outs, check_native=False)
        return res, outs, cur

    res1, outs1, cur1 = _run_once("a")
    res2, outs2, _cur2 = _run_once("b")

    for pid in ("core", "names_taxa", "regional"):
        assert validate_canonical_dir(outs1[pid]) == []
        for tbl in ("entries", "senses", "texts", "scopes", "identities"):
            assert (outs1[pid] / f"{tbl}.csv").read_bytes() == (outs2[pid] / f"{tbl}.csv").read_bytes()

    # Original 6 PoC entries/senses/texts preserved identically
    poc_entries = list(read_rows(reviewed_dir / "entries.csv"))
    poc_senses = list(read_rows(reviewed_dir / "senses.csv"))
    poc_texts = list(read_rows(reviewed_dir / "texts.csv"))
    core_entries_by_id = {r["entry_id"]: r for r in read_rows(outs1["core"] / "entries.csv")}
    core_senses_by_id = {r["sense_id"]: r for r in read_rows(outs1["core"] / "senses.csv")}
    core_texts_by_id = {r["text_id"]: r for r in read_rows(outs1["core"] / "texts.csv")}
    for r in poc_entries:
        assert core_entries_by_id[r["entry_id"]] == r
    for r in poc_senses:
        assert core_senses_by_id[r["sense_id"]] == r
    for r in poc_texts:
        assert core_texts_by_id[r["text_id"]] == r

    # Multi-etymology Noun occurrence allocation keys preserved via pos_occurrences
    core_idents = {r["entity_id"]: r["allocation_key"] for r in read_rows(outs1["core"] / "identities.csv") if r["kind"] == "entry"}
    kodi_core_keys = sorted(k for k in core_idents.values() if ":page:50557:" in k)
    assert kodi_core_keys == [
        "enwiktionary:pack:core:page:50557:rev:88721939:tam:NOUN:0",
        "enwiktionary:pack:core:page:50557:rev:88721939:tam:NOUN:1",
        "enwiktionary:pack:core:page:50557:rev:88721939:tam:NUM:0",
    ]
    assert res1["packs"]["regional"]["bulk_entries"] == 1  # ONLY கோடி Adverb!

    # No auto-invented prose/unmapped domain codes in vocabularies.toml
    core_vocab = (outs1["core"] / "vocabularies.toml").read_text(encoding="utf-8")
    for forbidden_slug in ("puducherry", "ramnad", "as_the_hand", "performing_an_operation"):
        assert forbidden_slug not in core_vocab

    # Curation workspace preserves unmapped qualifiers in findings + evidence without losing source text
    core_findings = list(read_rows(cur1 / "wiktionary-core-auto/findings.csv"))
    assert any(f["issue_code"] in {"UNMAPPED_QUALIFIER_REQUIRES_REVIEW", "UNMAPPED_ENTRY_QUALIFIER_REQUIRES_REVIEW"} for f in core_findings)
    core_ev = list(read_rows(outs1["core"] / "evidence.csv"))
    assert any("Puducherry" in ev["locator_json"] for ev in core_ev)
    assert any("Ramnad" in ev["locator_json"] for ev in core_ev)
    assert any("as the hand in playing on an instrument, writing" in ev["locator_json"] for ev in core_ev)


def test_ml_template_policy_boundary_with_pinned_gap_blockers() -> None:
    """Confirm ta m/l calls fail closed while safe en m/l literal links continue to work."""
    # Pinned gap-blocker fixtures from the 333 missing-snapshot pages: all use ta m/l + Tamil script.
    rupee_page = _make_page(
        pageid=65857,
        revid=93508862,
        title="\u0bb0\u0bc2\u0baa\u0bbe\u0baf\u0bcd",
        wikitext="==Tamil==\n===Noun===\n# The [[rupee]] (symbol: {{m|ta|\u0bf9}})\n",
    )
    aytham_page = _make_page(
        pageid=10046631,
        revid=92521670,
        title="\u0b85\u0b83\u0b95\u0bc7\u0ba9\u0bae\u0bcd",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|orthography}} {{ng|[[name]] of the [[letter]] {{l|ta|\u0b83}}}}\n",
    )
    theppam_page = _make_page(
        pageid=11419946,
        revid=89249734,
        title="\u0ba4\u0bc6\u0baa\u0bcd\u0baa\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bae\u0bcd",
        wikitext=(
            "==Tamil==\n===Noun===\n"
            "# {{w|temple tank}} {{gl|tank attached to a temple in which the deity is floated on rafts "
            "during {{m|ta|\u0ba4\u0bc6\u0baa\u0bcd\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bc1\u0bb5\u0bbf\u0bb4\u0bbe||float festival or {{w|theppotsavam}}}}}}\n"
        ),
    )

    for page, expected_rc in (
        (rupee_page, "UNEXPANDED_TEMPLATE_REJECTED:m"),
        (aytham_page, "UNEXPANDED_TEMPLATE_REJECTED:l"),
        (theppam_page, "UNEXPANDED_TEMPLATE_REJECTED:m"),
    ):
        parsed = parse_wiktionary_page(page)
        assert parsed["entries"] == []
        reasons = {exc["reason_code"] for exc in parsed["exclusions"]}
        assert expected_rc in reasons
        assert "ENTRY_NO_VALID_SENSES_REMAINING" in reasons

    # Foreign/alias variants remain fail-closed (only en m/l is allowlisted).
    for bad_line, expected_rc in (
        ("# {{m|ta|\u0bf9}}", "UNEXPANDED_TEMPLATE_REJECTED:m"),
        ("# {{l|ta|\u0b83}}", "UNEXPANDED_TEMPLATE_REJECTED:l"),
        ("# {{mention|ta|\u0bf9}}", "UNEXPANDED_TEMPLATE_REJECTED:mention"),
        ("# {{link|ta|\u0b83}}", "UNEXPANDED_TEMPLATE_REJECTED:link"),
        ("# {{l|mul|foo}}", "UNEXPANDED_TEMPLATE_REJECTED:l"),
        ("# {{l|en|\u0ba4\u0bae\u0bbf\u0bb4\u0bcd}}", "TAMIL_IN_ENGLISH_GLOSS_REJECTED"),
    ):
        res = clean_sense_line(bad_line)
        assert res["ok"] is False
        assert res["reason_code"] == expected_rc

    # Existing safe en m/l literal rendering remains intact.
    kalchedi = clean_sense_line("# {{lb|ta|botany}} {{l|en|lithops}} ({{taxfmt|Lithops|genus}} genus {{l|en|succulent|succulents}})")
    assert kalchedi["ok"] is True
    assert kalchedi["meaning_en"] == "(botany) lithops (Lithops genus succulents)"

    aamam = clean_sense_line("# {{m|en|yes}}, [[quite so]], [[indeed]]")
    assert aamam["ok"] is True
    assert aamam["meaning_en"] == "yes, quite so, indeed"


def test_workspace_and_notice_snapshot_date_override_validation_and_default_identity(tmp_path: Path) -> None:
    """Validate optional snapshot_date kwarg while preserving byte-identical 2026-11-15 default output."""
    repo_root = Path(__file__).resolve().parents[2]
    legalcode_src = repo_root / "data/curation/wiktionary-core-reviewed/notices/cc_by_sa_4_0_legalcode.txt"
    sample_page = _make_page(
        pageid=9100001,
        revid=92000001,
        title="\u0b95\u0bc1\u0bb0\u0bc1\u0bb5\u0bbf",
        wikitext="==Tamil==\n===Noun===\n# {{lb|ta|Jaffna}} sparrow\n",
    )
    parsed = parse_wiktionary_page(sample_page)
    assert len(parsed["entries"]) == 1
    candidates = [(sample_page["title"], parsed["entries"][0])]
    manifest = {
        "schema": "enwiktionary-tamil-bulk-snapshot-v1",
        "license": "CC-BY-SA-4.0 / GFDL",
        "pages_jsonl_gz_sha256": "a" * 64,
        "total_fetched_pages": 1,
    }

    # 1. Invalid snapshot_date values must fail closed without creating workspace files.
    for bad_date in ("", "20261116", "2026/11/16", "2026-02-30", "2026-13-01", "2026-11-16\n", "2026-11-16T00:00:00Z"):
        bad_ws = tmp_path / "ws_invalid"
        with pytest.raises(ValueError, match="snapshot_date"):
            _build_bulk_pack_workspace(
                "regional",
                candidates,
                manifest=manifest,
                workspace_dir=bad_ws,
                legalcode_src=legalcode_src,
                snapshot_date=bad_date,
            )
        assert not bad_ws.exists()
        with pytest.raises(ValueError, match="snapshot_date"):
            _build_pack_attribution_notice(
                "regional",
                manifest=manifest,
                entry_count=1,
                sense_count=1,
                reviewed_notice_path=None,
                snapshot_date=bad_date,
            )

    # 2. Default (2026-11-15) and explicit BULK_SNAPSHOT_DATE produce identical bytes and legacy source identity.
    ws_default = tmp_path / "ws_default"
    ws_explicit = tmp_path / "ws_explicit"
    _build_bulk_pack_workspace(
        "regional",
        candidates,
        manifest=manifest,
        workspace_dir=ws_default,
        legalcode_src=legalcode_src,
    )
    _build_bulk_pack_workspace(
        "regional",
        candidates,
        manifest=manifest,
        workspace_dir=ws_explicit,
        legalcode_src=legalcode_src,
        snapshot_date=BULK_SNAPSHOT_DATE,
    )

    expected_default_source_id = allocate_id("src", _pack_namespace("regional"), "enwiktionary_ta_bulk_20261115_regional")
    default_sources = list(read_rows(ws_default / "sources.csv"))
    assert len(default_sources) == 1
    assert default_sources[0]["source_id"] == expected_default_source_id
    assert default_sources[0]["label_json"] == "enwiktionary_ta_bulk_20261115_regional"

    for rel in sorted(p.relative_to(ws_default) for p in ws_default.rglob("*") if p.is_file()):
        assert (ws_default / rel).read_bytes() == (ws_explicit / rel).read_bytes()

    # 3. 2026-11-16 override updates source identity, metadata, decisions, labels, and notices consistently.
    ws_20261116 = tmp_path / "ws_20261116"
    _build_bulk_pack_workspace(
        "regional",
        candidates,
        manifest=manifest,
        workspace_dir=ws_20261116,
        legalcode_src=legalcode_src,
        snapshot_date="2026-11-16",
    )

    expected_new_source_id = allocate_id("src", _pack_namespace("regional"), "enwiktionary_ta_bulk_20261116_regional")
    assert expected_new_source_id != expected_default_source_id

    sources_16 = list(read_rows(ws_20261116 / "sources.csv"))
    assert len(sources_16) == 1
    src_row = sources_16[0]
    assert src_row["source_id"] == expected_new_source_id
    assert src_row["label_json"] == "enwiktionary_ta_bulk_20261116_regional"
    assert src_row["edition_json"].startswith("bulk-snapshot-2026-11-16;")
    assert json.loads(src_row["locator_json"])["snapshot_date"] == "2026-11-16"
    assert src_row["retrieval_date_json"] == "2026-11-16"
    assert "2026-11-16" in src_row["reuse_basis_json"]
    assert "2026-11-15" not in src_row["reuse_basis_json"]
    assert "2026-11-16" in src_row["attribution_text_json"]
    assert "2026-11-15" not in src_row["attribution_text_json"]

    decisions_16 = list(read_rows(ws_20261116 / "decisions.csv"))
    assert decisions_16
    assert all(d["decision_date"] == "2026-11-16" for d in decisions_16)

    labels_16 = list(read_rows(ws_20261116 / "labels.csv"))
    assert len(labels_16) >= 2  # JAFFNA and parent SL
    for lbl in labels_16:
        assert "2026-11-16" in lbl["definition_json"]
        assert "2026-11-15" not in lbl["definition_json"]

    notice_16 = (ws_20261116 / "notices/ATTRIBUTION_AND_LICENSE.md").read_text(encoding="utf-8")
    assert "- **Snapshot Date:** `2026-11-16`" in notice_16
    assert "2026-11-15" not in notice_16

    direct_notice_16 = _build_pack_attribution_notice(
        "regional",
        manifest=manifest,
        entry_count=1,
        sense_count=1,
        reviewed_notice_path=None,
        snapshot_date="2026-11-16",
    )
    assert direct_notice_16 == notice_16

    # 4. promote_bulk_packs accepts validated snapshot_date, rejects invalid dates, and preserves PoC rows.
    core_page = _make_page(
        pageid=9100002,
        revid=92000002,
        title="\u0b85\u0bae\u0bcd\u0bae\u0bbe",
        wikitext="==Tamil==\n===Noun===\n# mother\n",
    )
    snap_dir = tmp_path / "snap16"
    snap_dir.mkdir()
    gz_path = snap_dir / "pages.jsonl.gz"
    with gz_path.open("wb") as raw:
        with gzip.GzipFile(filename="pages.jsonl", mode="wb", fileobj=raw, mtime=0) as gz:
            for p in (sample_page, core_page):
                gz.write((json.dumps(p, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"))
    snap_manifest = {
        "schema": "enwiktionary-tamil-bulk-snapshot-v1",
        "license": "CC-BY-SA-4.0 / GFDL",
        "pages_jsonl_gz_sha256": hashlib.sha256(gz_path.read_bytes()).hexdigest(),
        "total_fetched_pages": 2,
    }
    (snap_dir / "snapshots_manifest.json").write_text(json.dumps(snap_manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="snapshot_date"):
        promote_bulk_packs(
            snap_dir,
            curation_root=tmp_path / "cur_bad",
            reviewed_dir=repo_root / "data/curation/wiktionary-core-reviewed",
            output_dirs={
                "core": tmp_path / "out_bad/dictionary",
                "names_taxa": tmp_path / "out_bad/packs/names_taxa",
                "regional": tmp_path / "out_bad/packs/regional",
            },
            check_native=False,
            snapshot_date="2026-02-30",
        )

    prom16 = promote_bulk_packs(
        snap_dir,
        packs=("core", "regional"),
        curation_root=tmp_path / "cur_16",
        reviewed_dir=repo_root / "data/curation/wiktionary-core-reviewed",
        output_dirs={
            "core": tmp_path / "out_16/dictionary",
            "names_taxa": tmp_path / "out_16/packs/names_taxa",
            "regional": tmp_path / "out_16/packs/regional",
        },
        check_native=False,
        snapshot_date="2026-11-16",
    )
    assert prom16["snapshot_date"] == "2026-11-16"
    assert validate_canonical_dir(tmp_path / "out_16/dictionary") == []
    assert validate_canonical_dir(tmp_path / "out_16/packs/regional") == []
    core_notice_16 = (tmp_path / "out_16/dictionary/notices/ATTRIBUTION_AND_LICENSE.md").read_text(encoding="utf-8")
    assert "- **Snapshot Date:** `2026-11-16`" in core_notice_16
    assert "Preserved Human-Reviewed PoC Revisions" in core_notice_16
    core_sources_16 = list(read_rows(tmp_path / "out_16/dictionary/sources.csv"))
    assert any(str(r.get("label_json", "")).strip('"') == "enwiktionary_ta_bulk_20261116_core" for r in core_sources_16)
    assert not any(str(r.get("label_json", "")).strip('"') == "enwiktionary_ta_bulk_20261115_core" for r in core_sources_16)
    reg_sources_16 = list(read_rows(tmp_path / "out_16/packs/regional/sources.csv"))
    assert [str(r.get("label_json", "")).strip('"') for r in reg_sources_16] == ["enwiktionary_ta_bulk_20261116_regional"]
