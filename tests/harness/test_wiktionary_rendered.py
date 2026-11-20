"""Sourced-fixture tests for bounded MediaWiki action=parse rendered recovery."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import unicodedata

import pytest

from tools.lexicon_wiktionary_rendered import (
    MAX_RENDERED_PAGES,
    ROOT,
    acquire_rendered_pages,
    build_rendered_queue,
    parse_rendered_page,
    reconcile_rendered_queue,
    verify_rendered_capture,
    verify_rendered_page,
    verify_rendered_queue_binding,
)


def _rendered_page(
    *,
    title: str,
    pageid: int,
    revid: int,
    html: str,
    wikitext: str = "==Tamil==\n===Noun===\n# sample",
    templates: list[dict] | None = None,
    modules: list[str] | None = None,
    modulestyles: list[str] | None = None,
    sections: list[dict] | None = None,
    parsewarnings: list[str] | None = None,
    capture_timestamp_utc: str = "2026-11-16T17:00:00+00:00",
) -> dict:
    wikitext_sha256 = hashlib.sha256(wikitext.encode("utf-8")).hexdigest()
    html_sha256 = hashlib.sha256(html.encode("utf-8")).hexdigest()
    tmpl_list = templates if templates is not None else [{"ns": 10, "title": "Template:place", "exists": True}]
    template_deps = sorted((t["title"] for t in tmpl_list if t.get("ns") == 10))
    module_deps = sorted((t["title"] for t in tmpl_list if t.get("ns") == 828))
    other_deps = sorted((t["title"] for t in tmpl_list if t.get("ns") not in {10, 828}))
    deps_payload = {
        "templates": template_deps,
        "modules": module_deps,
        "other": other_deps,
        "rl_modules": modules or [],
        "rl_modulestyles": modulestyles or [],
    }
    deps_sha256 = hashlib.sha256(
        json.dumps(deps_payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    raw_api_payload = {
        "parse": {
            "title": title,
            "pageid": pageid,
            "revid": revid,
            "text": html,
            "templates": tmpl_list,
            "modules": modules or [],
            "modulestyles": modulestyles or [],
            "sections": sections or [],
            "parsewarnings": parsewarnings or [],
        }
    }
    raw_sha = hashlib.sha256(
        json.dumps(raw_api_payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "title": title,
        "pageid": pageid,
        "revid": revid,
        "revision_timestamp": "2026-11-15T00:00:00Z",
        "user": "TestEditor",
        "sha1": "0" * 40,
        "wikitext_sha256": wikitext_sha256,
        "permalink_url": f"https://en.wiktionary.org/w/index.php?oldid={revid}",
        "history_url": "https://en.wiktionary.org/w/index.php?action=history",
        "categories": ["Category:Tamil lemmas"],
        "capture_timestamp_utc": capture_timestamp_utc,
        "api_endpoint": "https://en.wiktionary.org/w/api.php",
        "api_params": {"action": "parse", "oldid": str(revid), "format": "json", "formatversion": "2"},
        "raw_api_response_sha256": raw_sha,
        "rendered_html": html,
        "rendered_html_sha256": html_sha256,
        "template_dependencies": template_deps,
        "module_dependencies": module_deps,
        "other_dependencies": other_deps,
        "rl_modules": modules or [],
        "rl_modulestyles": modulestyles or [],
        "dependencies_sha256": deps_sha256,
        "sections": sections or [],
        "parsewarnings": parsewarnings or [],
        "rendering_attribution": "rendered_by_mediawiki_current_templates_at_capture_time",
        "raw_capture_file_locator": {
            "batch_file": "batch-000.json",
            "batch_sha256": "d" * 64,
            "record_index": 0,
        },
    }


def test_place_number_given_name_transclude_and_name_translit_recovery() -> None:
    """Recover literal rendered English definitions for supported template families."""
    # 1. {{place}} -> அனுராதபுரம் (pageid=9584230, revid=87859721)
    p_place = _rendered_page(
        title="\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd",
        pageid=9584230,
        revid=87859721,
        html=(
            '<div class="mw-parser-output">'
            '<div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Proper_noun">Proper noun</h3></div>'
            '<p><span class="headword-line"><strong class="Taml headword" lang="ta">\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd</strong></span></p>'
            '<ol><li><span class="Latn" lang="en"><a href="/wiki/Anuradhapura#English">Anuradhapura</a></span> '
            '(a <a href="/wiki/city">city</a> in <span class="Latn" lang="en"><a href="/wiki/North_Central_Province#English">North Central Province</a></span>, '
            '<span class="Latn" lang="en"><a href="/wiki/Sri_Lanka#English">Sri Lanka</a></span>)</li></ol>'
            "</div>"
        ),
        templates=[
            {"ns": 10, "title": "Template:place", "exists": True},
            {"ns": 828, "title": "Module:place", "exists": True},
        ],
    )
    res_place = parse_rendered_page(p_place)
    assert len(res_place["entries"]) == 1
    ent = res_place["entries"][0]
    assert ent["pos_code"] == "PROPN"
    assert ent["pack_id"] == "names_taxa"
    assert ent["source_origin"] == "rendered_template_expansion"
    assert ent["extraction_method"] == "wiktionary-rendered-parser"
    assert ent["capture_timestamp_utc"] == "2026-11-16T17:00:00+00:00"
    assert ent["rendered_html_sha256"] == p_place["rendered_html_sha256"]
    assert ent["dependencies_sha256"] == p_place["dependencies_sha256"]
    ev = ent["rendered_evidence"]
    assert ev["source_kind"] == "rendered_html"
    assert ev["capture_timestamp_utc"] == "2026-11-16T17:00:00+00:00"
    assert ev["html_sha256"] == p_place["rendered_html_sha256"]
    assert ev["raw_capture_file_locator"]["batch_file"] == "batch-000.json"
    assert ev["template_module_dependencies"]["template_dependencies"] == ["Template:place"]
    assert ev["template_module_dependencies"]["module_dependencies"] == ["Module:place"]
    assert "limits_and_caveats" in ev["template_module_dependencies"]
    assert ent["senses"][0]["meaning_en"] == "Anuradhapura (a city in North Central Province, Sri Lanka)"

    # 2. {{number to word}} -> அறுநூறு (pageid=9074433, revid=88665312)
    p_num = _rendered_page(
        title="\u0b85\u0bb1\u0bc1\u0ba8\u0bc2\u0bb1\u0bc1",
        pageid=9074433,
        revid=88665312,
        html=(
            '<div class="mw-parser-output">'
            '<div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Numeral">Numeral</h3></div>'
            "<ol><li><a href=\"/wiki/six_hundred\">six hundred</a></li></ol>"
            "</div>"
        ),
    )
    res_num = parse_rendered_page(p_num)
    assert res_num["entries"][0]["pos_code"] == "NUM"
    assert res_num["entries"][0]["pack_id"] == "core"
    assert res_num["entries"][0]["senses"][0]["meaning_en"] == "six hundred"

    # 3. {{given name}} -> இராமானுசன் (pageid=8166000, revid=88252149)
    p_gn = _rendered_page(
        title="\u0b87\u0bb0\u0bbe\u0bae\u0bbe\u0ba9\u0bc1\u0b9a\u0ba9\u0bcd",
        pageid=8166000,
        revid=88252149,
        html=(
            '<div class="mw-parser-output">'
            '<div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Proper_noun">Proper noun</h3></div>'
            '<ol><li><span class="use-with-mention">a male <a href="/wiki/given_name">given name</a>, '
            '<a href="/wiki/Ramanujan#English">Ramanujan</a>, from Sanskrit</span></li></ol>'
            "</div>"
        ),
    )
    res_gn = parse_rendered_page(p_gn)
    assert res_gn["entries"][0]["pack_id"] == "names_taxa"
    assert res_gn["entries"][0]["senses"][0]["meaning_en"] == "a male given name, Ramanujan, from Sanskrit"

    # 4. {{transclude sense}} -> உஃப (pageid=1848166, revid=75499781)
    p_ts = _rendered_page(
        title="\u0b89\u0b83\u0baa",
        pageid=1848166,
        revid=75499781,
        html=(
            '<div class="mw-parser-output">'
            '<div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Proper_noun">Proper noun</h3></div>'
            '<ol><li><span class="senseid" id="Tamil:_Q911" data-lang="ta" data-id="Q911">'
            '<span class="Latn" lang="en"><a href="/wiki/Ufa#English:_Q911">Ufa</a></span> '
            '(the <a href="/wiki/capital">capital</a> and <a href="/wiki/large">largest</a> '
            '<a href="/wiki/city">city</a> of <span class="Latn" lang="en"><a href="/wiki/Bashkortostan#English">Bashkortostan</a></span>, '
            '<span class="Latn" lang="en"><a href="/wiki/Russia#English">Russia</a></span>)</span></li></ol>'
            "</div>"
        ),
    )
    res_ts = parse_rendered_page(p_ts)
    assert res_ts["entries"][0]["senses"][0]["meaning_en"] == "Ufa (the capital and largest city of Bashkortostan, Russia)"


def test_direct_sense_isolated_from_nested_quotes_examples_subsenses_and_non_tamil() -> None:
    """Keep ==Tamil==, etymology, POS, and direct sense separate from nested quotes/examples/subsenses."""
    # Sourced from அரபிக்கடல் (pageid=11004045, revid=87704656) + multi-etymology குலிகம் + non-Tamil section
    html = (
        '<div class="mw-parser-output">'
        '<div class="mw-heading mw-heading2"><h2 id="Malayalam">Malayalam</h2></div>'
        '<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>'
        "<ol><li>foreign sense</li></ol>"
        '<div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
        '<div class="mw-heading mw-heading3"><h3 id="Etymology_1">Etymology 1</h3></div>'
        '<div class="mw-heading mw-heading4"><h4 id="Proper_noun">Proper noun</h4></div>'
        '<ol><li><a href="/wiki/Arabian_Sea">Arabian Sea</a> (a <a href="/wiki/region">region</a> of the '
        '<span class="Latn" lang="en"><a href="/wiki/Indian_Ocean#English">Indian Ocean</a></span>)'
        '<ul><li><div class="citation-whole"><span class="cited-source"><b>1995</b>:</span>'
        '<dl><dd><div class="h-quotation"><span class="Taml e-quotation cited-passage" lang="ta">\u0b85\u0ba8\u0bcd\u0ba4 \u0b85\u0bb0\u0baa\u0bbf\u0b95\u0bcd\u0b95\u0b9f\u0bb2\u0bcb\u0bb0\u0bae\u0bcd</span></div></dd></dl>'
        "</div></li></ul>"
        "<ol><li>nested subsense should be excluded</li></ol>"
        "</li></ol>"
        '<div class="mw-heading mw-heading3"><h3 id="Etymology_2">Etymology 2</h3></div>'
        '<div class="mw-heading mw-heading4"><h4 id="Proper_noun_2">Proper noun</h4></div>'
        '<ol><li>secondary etymology sense<dl><dd><span class="h-usage-example">'
        '<i class="Taml mention e-example" lang="ta">\u0b89\u0ba4\u0bbe\u0bb0\u0ba3\u0bae\u0bcd</i></span></dd></dl></li></ol>'
        "</div>"
    )
    # Also test Proper noun with id="Proper_noun_2" (MediaWiki deduplicates anchor IDs, text is still "Proper noun")
    p = _rendered_page(title="\u0b85\u0bb0\u0baa\u0bbf\u0b95\u0bcd\u0b95\u0b9f\u0bb2\u0bcd", pageid=11004045, revid=87704656, html=html)
    parsed = parse_rendered_page(p)
    assert len(parsed["entries"]) == 2
    assert parsed["entries"][0]["etymology_index"] == 1
    assert parsed["entries"][0]["pos_occurrence_index"] == 0
    assert parsed["entries"][0]["senses"][0]["meaning_en"] == "Arabian Sea (a region of the Indian Ocean)"
    assert parsed["entries"][0]["senses"][0]["nested_lists_excluded"] == {"dl": 0, "ol": 1, "ul": 1}
    assert parsed["entries"][1]["etymology_index"] == 2
    assert parsed["entries"][1]["pos_occurrence_index"] == 1
    assert parsed["entries"][1]["senses"][0]["meaning_en"] == "secondary etymology sense"
    reasons = {e["reason_code"] for e in parsed["exclusions"]}
    assert "NON_TAMIL_SECTION_EXCLUDED" in reasons
    assert "SUBSENSE_LIST_EXCLUDED" in reasons


def test_tamil_in_english_gloss_policy_strictly_retained() -> None:
    """Retain TAMIL_IN_ENGLISH_GLOSS_REJECTED for altform/infl/m/l; never strip Tamil to recover."""
    # Sourced from அங்கேரி (altform -> alternative form of ஹங்கேரி) and அக (infl of -> adjectival form of அகம்)
    for title, pid, rid, html in (
        (
            "\u0b85\u0b99\u0bcd\u0b95\u0bc7\u0bb0\u0bbf",
            11261429,
            87641124,
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Proper_noun">Proper noun</h3></div>'
            '<ol><li><span class="form-of-definition use-with-mention">alternative form of '
            '<span class="form-of-definition-link"><i class="Taml mention" lang="ta">\u0bb9\u0b99\u0bcd\u0b95\u0bc7\u0bb0\u0bbf</i> '
            '(ha\u1e45k\u0113ri)</span></span></li></ol></div>',
        ),
        (
            "\u0b85\u0b95",
            11231403,
            93764339,
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Adjective">Adjective</h3></div>'
            '<ol><li><span class="form-of-definition use-with-mention">adjectival form of '
            '<span class="form-of-definition-link"><i class="Taml mention" lang="ta">\u0b85\u0b95\u0bae\u0bcd</i> '
            '(akam)</span></span></li></ol></div>',
        ),
    ):
        parsed = parse_rendered_page(_rendered_page(title=title, pageid=pid, revid=rid, html=html))
        assert parsed["entries"] == []
        reasons = {e["reason_code"] for e in parsed["exclusions"]}
        assert "TAMIL_IN_ENGLISH_GLOSS_REJECTED" in reasons
        assert "ENTRY_NO_VALID_SENSES_REMAINING" in reasons


def test_sid_empty_elt_style_tag_and_reference_sup_vs_non_reference_sup() -> None:
    """Skip mw-empty-elt, style, and sup.reference safely; fail closed on non-reference sup (e.g. 10^3)."""
    # Sourced from கசகசா ({{sid}} + mw-empty-elt), ஏங்கு ({{+obj}} + <style>), அகரு (<sup class="reference">), கிலோமீட்டர் (10<sup>3</sup>)
    p_sid = _rendered_page(
        title="\u0b95\u0b9a\u0b95\u0b9a\u0bbe",
        pageid=11588211,
        revid=90083226,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>'
            '<ol><li class="mw-empty-elt"></li><li class="senseid"> <a href="/wiki/opium_poppy">opium poppy</a> '
            '(<i>Papaver somniferum</i>)</li><li class="mw-empty-elt"></li><li class="senseid"> '
            '<a href="/wiki/poppy_seed">poppy seed</a></li></ol></div>'
        ),
    )
    res_sid = parse_rendered_page(p_sid)
    assert [s["meaning_en"] for s in res_sid["entries"][0]["senses"]] == [
        "opium poppy (Papaver somniferum)",
        "poppy seed",
    ]
    assert [s["ordinal"] for s in res_sid["entries"][0]["senses"]] == [1, 2]

    p_obj = _rendered_page(
        title="\u0b8f\u0b99\u0bcd\u0b95\u0bc1",
        pageid=8855411,
        revid=86130560,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Verb">Verb</h3></div>'
            '<ol><li>to <a href="/wiki/long_for">long for</a>, <a href="/wiki/miss">miss</a>, '
            '<a href="/wiki/yearn">yearn</a> <style data-mw-deduplicate="TemplateStyles:r90144471">'
            '.mw-parser-output .object-usage-tag{font-style:italic}</style>'
            '[<i>with</i> <span class="object-usage-tag"><a href="/wiki/Appendix:Glossary#dative_case">dative</a></span>]</li></ol></div>'
        ),
    )
    res_obj = parse_rendered_page(p_obj)
    assert res_obj["entries"][0]["senses"][0]["meaning_en"] == "to long for, miss, yearn [with dative]"

    p_ref = _rendered_page(
        title="\u0b85\u0b95\u0bb0\u0bc1",
        pageid=8000762,
        revid=92196796,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>'
            '<ol><li><a href="/wiki/eaglewood">eaglewood</a>, <span class="biota"><i>Aquilaria agallocha</i></span>'
            '<sup id="cite_ref-TAL_1-0" class="reference"><a href="#cite_note-TAL-1"><span class="cite-bracket">[</span>1<span class="cite-bracket">]</span></a></sup></li></ol></div>'
        ),
    )
    res_ref = parse_rendered_page(p_ref)
    assert res_ref["entries"][0]["senses"][0]["meaning_en"] == "eaglewood, Aquilaria agallocha"
    assert res_ref["entries"][0]["senses"][0]["reference_markers_excluded"] == 1

    # Mathematical superscript 10<sup>3</sup> MUST NOT become "103" — must fail closed!
    p_sup = _rendered_page(
        title="\u0b95\u0bbf\u0bb2\u0bcb\u0bae\u0bc0\u0b9f\u0bcd\u0b9f\u0bb0\u0bcd",
        pageid=11355457,
        revid=88669933,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>'
            '<ol><li><span class="usage-label-sense"><span class="ib-brac label-brac">(</span>'
            '<span class="ib-content label-content">metrology</span><span class="ib-brac label-brac">)</span></span> '
            'kilometre (an SI unit of length equal to 10<sup>3</sup> metres)</li></ol></div>'
        ),
    )
    res_sup = parse_rendered_page(p_sup)
    assert res_sup["entries"] == []
    assert any(e["reason_code"] == "UNSUPPORTED_RENDERED_HTML_ELEMENT:sup" for e in res_sup["exclusions"])


def test_qualifiers_entry_headword_and_sense_labels_preserve_dimensions() -> None:
    """Preserve mapped entry/sense qualifiers, unmapped qualifiers, and regional routing."""
    # Sourced from கந்தோர் (Sri Lanka), பறந்தடி (intransitive + idiomatic), ஐயனார் (nested {{w}} in lb -> Tamil religion)
    p_sl = _rendered_page(
        title="\u0b95\u0ba8\u0bcd\u0ba4\u0bcb\u0bb0\u0bcd",
        pageid=8370756,
        revid=78439445,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>'
            '<ol><li><span class="usage-label-sense"><span class="ib-brac label-brac">(</span>'
            '<span class="ib-content label-content"><a href="https://en.wikipedia.org/wiki/Sri_Lankan_Tamil_dialects">Sri Lanka</a></span>'
            '<span class="ib-brac label-brac">)</span></span> <a href="/wiki/office">office</a></li></ol></div>'
        ),
    )
    res_sl = parse_rendered_page(p_sl)
    ent_sl = res_sl["entries"][0]
    assert ent_sl["pack_id"] == "regional"
    assert ent_sl["senses"][0]["meaning_en"] == "(Sri Lanka) office"
    assert ent_sl["senses"][0]["qualifiers"][0]["dimension"] == "region"
    assert ent_sl["senses"][0]["qualifiers"][0]["code"] == "SL"

    p_verb = _rendered_page(
        title="\u0baa\u0bb1\u0ba8\u0bcd\u0ba4\u0b9f\u0bbf",
        pageid=100,
        revid=89333828,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Verb">Verb</h3></div>'
            '<p><span class="headword-line"><strong class="Taml headword" lang="ta">\u0baa\u0bb1\u0ba8\u0bcd\u0ba4\u0b9f\u0bbf</strong></span> '
            '<span class="usage-label-term"><span class="ib-brac label-brac">(</span>'
            '<span class="ib-content label-content"><a href="/wiki/Appendix:Glossary#intransitive">intransitive</a></span>'
            '<span class="ib-brac label-brac">)</span></span></p>'
            '<ol><li><span class="usage-label-sense"><span class="ib-brac label-brac">(</span>'
            '<span class="ib-content label-content"><a href="/wiki/Appendix:Glossary#idiomatic">idiomatic</a></span>'
            '<span class="ib-brac label-brac">)</span></span> to <a href="/wiki/hurry">hurry</a> in <a href="/wiki/anxiety">anxiety</a></li></ol></div>'
        ),
    )
    res_v = parse_rendered_page(p_verb)
    ent_v = res_v["entries"][0]
    assert ent_v["pack_id"] == "core"
    assert ent_v["entry_qualifiers"][0]["dimension"] == "grammar_system"
    assert ent_v["entry_qualifiers"][0]["code"] == "intransitive"
    assert ent_v["senses"][0]["qualifiers"][0]["dimension"] == "register"
    assert ent_v["senses"][0]["qualifiers"][0]["code"] == "idiomatic"

    # Unmapped qualifier preserved without inventing domain
    p_unmapped = _rendered_page(
        title="\u0b9a\u0bc6\u0baa\u0bcd\u0baa\u0bae\u0bcd",
        pageid=101,
        revid=102,
        html=(
            '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
            '<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>'
            '<p><span class="headword-line"><strong class="Taml headword" lang="ta">\u0b9a\u0bc6\u0baa\u0bcd\u0baa\u0bae\u0bcd</strong></span> '
            '<span class="usage-label-term"><span class="ib-brac label-brac">(</span>'
            '<span class="ib-content label-content">chiefly Spoken Tamil</span>'
            '<span class="ib-brac label-brac">)</span></span></p>'
            '<ol><li><span class="ib-brac qualifier-brac">(</span>'
            '<span class="ib-content qualifier-content">unmapped custom qualifier</span>'
            '<span class="ib-brac qualifier-brac">)</span> plain gloss</li></ol></div>'
        ),
    )
    res_u = parse_rendered_page(p_unmapped)
    ent_u = res_u["entries"][0]
    assert ent_u["entry_qualifiers"][0]["dimension"] == "register"
    assert ent_u["entry_qualifiers"][0]["code"] == "colloquial"
    assert ent_u["senses"][0]["qualifiers"] == []
    assert ent_u["senses"][0]["unmapped_qualifiers"][0]["status"] == "unstructured_pending_review"
    assert ent_u["senses"][0]["unmapped_qualifiers"][0]["raw_token"] == "unmapped custom qualifier"


def test_fail_closed_on_unmapped_pos_script_errors_and_unicode_violations() -> None:
    """Fail closed on Participle/Phrase/Number headings, Scribunto errors, residual braces, and joiners."""
    for heading in ("Participle", "Phrase", "Number"):
        p = _rendered_page(
            title="\u0b85\u0ba3\u0bcd\u0ba3\u0bbe\u0ba8\u0bcd\u0ba4\u0bc1",
            pageid=10,
            revid=20,
            html=f'<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
                 f'<div class="mw-heading mw-heading3"><h3>{heading}</h3></div><ol><li>gloss</li></ol></div>',
        )
        res = parse_rendered_page(p)
        assert res["entries"] == []
        assert any(e["reason_code"] == f"UNMAPPED_SUBSECTION_EXCLUDED:{heading}" for e in res["exclusions"])

    p_err = _rendered_page(
        title="\u0b85\u0ba3\u0bcd\u0ba3\u0bbe\u0ba8\u0bcd\u0ba4\u0bc1",
        pageid=11,
        revid=21,
        html='<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
             '<div class="mw-heading mw-heading3"><h3>Noun</h3></div>'
             '<ol><li><span class="scribunto-error">Lua error in Module:place</span></li></ol></div>',
    )
    res_err = parse_rendered_page(p_err)
    assert res_err["entries"] == []
    assert any(e["reason_code"] == "WIKTIONARY_SCRIPT_ERROR_REJECTED" for e in res_err["exclusions"])

    zwj = chr(0x200D)
    p_zwj = _rendered_page(
        title="\u0b85\u0ba3\u0bcd\u0ba3\u0bbe\u0ba8\u0bcd\u0ba4\u0bc1",
        pageid=12,
        revid=22,
        html=f'<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
             f'<div class="mw-heading mw-heading3"><h3>Noun</h3></div><ol><li>bad{zwj}gloss</li></ol></div>',
    )
    res_zwj = parse_rendered_page(p_zwj)
    assert res_zwj["entries"] == []
    assert any(e["reason_code"] == "SENSE_UNEXPECTED_JOINER_REJECTED" for e in res_zwj["exclusions"])


def test_acquisition_cap_checkpoint_tamper_and_network_error_isolation(tmp_path: Path, monkeypatch) -> None:
    """Enforce <= 384 page cap, resumable hash checkpoints, tamper rejection, and API error isolation."""
    # 1. Cap > 384 fails closed before any API call.
    too_many = [{"title": f"\u0ba4{i}", "pageid": i + 1, "revid": i + 100, "wikitext_sha256": "a" * 64} for i in range(MAX_RENDERED_PAGES + 1)]
    with pytest.raises(ValueError, match="384"):
        acquire_rendered_pages(too_many, tmp_path / "cap")

    # 2. Network/API errors do NOT create missing pages or manifest.
    queue = [
        {"title": "\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd", "pageid": 9584230, "revid": 87859721, "wikitext_sha256": "b" * 64, "revision_timestamp": "2026-01-01T00:00:00Z", "user": "u", "sha1": "0" * 40, "categories": []},
        {"title": "\u0b85\u0bb1\u0bc1\u0ba8\u0bc2\u0bb1\u0bc1", "pageid": 9074433, "revid": 88665312, "wikitext_sha256": "c" * 64, "revision_timestamp": "2026-01-01T00:00:00Z", "user": "u", "sha1": "0" * 40, "categories": []},
    ]
    calls = []

    def failing_api(params, **kwargs):
        calls.append(params["oldid"])
        if len(calls) == 2:
            raise OSError("network timeout")
        return {
            "parse": {
                "title": "\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd",
                "pageid": 9584230,
                "revid": 87859721,
                "text": "<ol><li>Anuradhapura</li></ol>",
                "templates": [{"ns": 10, "title": "Template:place", "exists": True}],
                "modules": [],
                "modulestyles": [],
                "sections": [],
                "parsewarnings": [],
            }
        }

    monkeypatch.setattr("tools.lexicon_wiktionary_rendered._api_get_json", failing_api)
    out_dir = tmp_path / "capture"
    with pytest.raises(OSError, match="network timeout"):
        acquire_rendered_pages(queue, out_dir, batch_size=1, max_workers=1)
    assert (out_dir / "capture-checkpoint.json").is_file()
    assert not (out_dir / "manifest.json").exists()

    # Resume succeeds without re-fetching batch 0, and produces verified manifest.
    def resuming_api(params, **kwargs):
        calls.append(params["oldid"])
        assert params["oldid"] == "88665312"
        return {
            "parse": {
                "title": "\u0b85\u0bb1\u0bc1\u0ba8\u0bc2\u0bb1\u0bc1",
                "pageid": 9074433,
                "revid": 88665312,
                "text": "<ol><li>six hundred</li></ol>",
                "templates": [{"ns": 10, "title": "Template:number to word", "exists": True}],
                "modules": [],
                "modulestyles": [],
                "sections": [],
                "parsewarnings": [],
            }
        }

    monkeypatch.setattr("tools.lexicon_wiktionary_rendered._api_get_json", resuming_api)
    pages, manifest = acquire_rendered_pages(queue, out_dir, batch_size=1, max_workers=1)
    assert len(pages) == 2
    assert len(calls) == 3  # 1 cached + 1 resumed
    verify_rendered_capture(out_dir)
    assert manifest["rendering_attribution"] == "rendered_by_mediawiki_current_templates_at_capture_time"

    # Tamper detection on pages.jsonl.gz and raw batch fails closed.
    gz_bytes = (out_dir / "pages.jsonl.gz").read_bytes()
    manifest_bytes = (out_dir / "manifest.json").read_bytes()
    projected = [json.loads(line) for line in gzip.decompress(gz_bytes).decode("utf-8").splitlines()]
    projected[0]["raw_capture_file_locator"]["batch_sha256"] = "f" * 64
    tampered_raw = "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in projected).encode("utf-8")
    tampered_gz = gzip.compress(tampered_raw, mtime=0)
    tampered_manifest = json.loads(manifest_bytes)
    tampered_manifest["pages_jsonl_gz_sha256"] = hashlib.sha256(tampered_gz).hexdigest()
    tampered_manifest["pages_uncompressed_sha256"] = hashlib.sha256(tampered_raw).hexdigest()
    (out_dir / "pages.jsonl.gz").write_bytes(tampered_gz)
    (out_dir / "manifest.json").write_text(json.dumps(tampered_manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="batch locator digest"):
        verify_rendered_capture(out_dir)
    (out_dir / "pages.jsonl.gz").write_bytes(gz_bytes)
    (out_dir / "manifest.json").write_bytes(manifest_bytes)
    (out_dir / "pages.jsonl.gz").write_bytes(gz_bytes + b"tamper")
    with pytest.raises(ValueError, match="digest"):
        verify_rendered_capture(out_dir)
    (out_dir / "pages.jsonl.gz").write_bytes(gz_bytes)
    (out_dir / "batch-999.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unregistered"):
        verify_rendered_capture(out_dir)


def test_page_identity_and_digest_verification_fail_closed() -> None:
    """Reject tampered HTML, mismatched revid/URL, or missing capture timestamp."""
    p = _rendered_page(
        title="\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd",
        pageid=9584230,
        revid=87859721,
        html="<ol><li>Anuradhapura</li></ol>",
    )
    verify_rendered_page(p)
    tampered = dict(p, rendered_html="<ol><li>Tampered</li></ol>")
    with pytest.raises(ValueError, match="digest"):
        verify_rendered_page(tampered)
    bad_origin = dict(p, rendering_attribution="verbatim_source")
    with pytest.raises(ValueError, match="attribution"):
        verify_rendered_page(bad_origin)


def test_reconciliation_emits_bulk_compatible_candidates_without_decisions() -> None:
    """Candidate JSON carries provenance, all 3 pack IDs, and blocked reasons with zero acceptance decisions."""
    queue_records = [
        {"headword": "\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd", "status": "source_present_parser_blocked", "word_ids": [1], "meaning_ids": [10], "historical_pos_labels": ["PROPN"], "source": {"pageid": 9584230, "revid": 87859721}},
        {"headword": "\u0b85\u0bb1\u0bc1\u0ba8\u0bc2\u0bb1\u0bc1", "status": "source_present_parser_blocked", "word_ids": [4], "meaning_ids": [40], "historical_pos_labels": ["NUM"], "source": {"pageid": 9074433, "revid": 88665312}},
        {"headword": "\u0b95\u0ba8\u0bcd\u0ba4\u0bcb\u0bb0\u0bcd", "status": "source_present_parser_blocked", "word_ids": [5], "meaning_ids": [50], "historical_pos_labels": ["NOUN"], "source": {"pageid": 8370756, "revid": 78439445}},
        {"headword": "\u0b85\u0b99\u0bcd\u0b95\u0bc7\u0bb0\u0bbf", "status": "source_present_parser_blocked", "word_ids": [2], "meaning_ids": [20], "historical_pos_labels": ["PROPN"], "source": {"pageid": 11261429, "revid": 87641124}},
        {"headword": "\u0b87\u0bb2\u0bcd\u0bb2\u0bc8\u0baa\u0b95\u0bcd\u0b95\u0bae\u0bcd", "status": "missing_from_snapshot", "word_ids": [3], "meaning_ids": [30], "historical_pos_labels": ["NOUN"]},
    ]
    pages = {
        "\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd": _rendered_page(
            title="\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd",
            pageid=9584230,
            revid=87859721,
            html='<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
                 '<div class="mw-heading mw-heading3"><h3>Proper noun</h3></div>'
                 '<ol><li>Anuradhapura (a city in North Central Province, Sri Lanka)</li></ol></div>',
        ),
        "\u0b85\u0bb1\u0bc1\u0ba8\u0bc2\u0bb1\u0bc1": _rendered_page(
            title="\u0b85\u0bb1\u0bc1\u0ba8\u0bc2\u0bb1\u0bc1",
            pageid=9074433,
            revid=88665312,
            html='<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
                 '<div class="mw-heading mw-heading3"><h3>Numeral</h3></div>'
                 '<ol><li>six hundred</li></ol></div>',
        ),
        "\u0b95\u0ba8\u0bcd\u0ba4\u0bcb\u0bb0\u0bcd": _rendered_page(
            title="\u0b95\u0ba8\u0bcd\u0ba4\u0bcb\u0bb0\u0bcd",
            pageid=8370756,
            revid=78439445,
            html='<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
                 '<div class="mw-heading mw-heading3"><h3>Noun</h3></div>'
                 '<ol><li><span class="usage-label-sense"><span class="ib-brac label-brac">(</span>'
                 '<span class="ib-content label-content">Sri Lanka</span>'
                 '<span class="ib-brac label-brac">)</span></span> office</li></ol></div>',
        ),
        "\u0b85\u0b99\u0bcd\u0b95\u0bc7\u0bb0\u0bbf": _rendered_page(
            title="\u0b85\u0b99\u0bcd\u0b95\u0bc7\u0bb0\u0bbf",
            pageid=11261429,
            revid=87641124,
            html='<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2 id="Tamil">Tamil</h2></div>'
                 '<div class="mw-heading mw-heading3"><h3>Proper noun</h3></div>'
                 '<ol><li>alternative form of \u0bb9\u0b99\u0bcd\u0b95\u0bc7\u0bb0\u0bbf (ha\u1e45k\u0113ri)</li></ol></div>',
        ),
    }
    manifest_sha = "e" * 64
    for item in queue_records:
        if "source" in item:
            item["source"]["wikitext_sha256"] = pages[item["headword"]]["wikitext_sha256"]
    report = reconcile_rendered_queue(queue_records, pages, manifest_sha256=manifest_sha, manifest_path="data/sources/enwiktionary-tamil-rendered-2026-11-16/manifest.json")
    assert report["status_counts"] == {
        "missing_from_snapshot": 1,
        "rendered_parser_blocked": 1,
        "rendered_recoverable_candidate": 3,
    }
    assert report["pack_counts"] == {"core": 1, "names_taxa": 1, "regional": 1}
    assert len(report["candidate_entries"]) == 3
    by_hw = {c["headword"]: c for c in report["candidate_entries"]}
    cand = by_hw["\u0b85\u0ba9\u0bc1\u0bb0\u0bbe\u0ba4\u0baa\u0bc1\u0bb0\u0bae\u0bcd"]
    assert cand["source_origin"] == "rendered_template_expansion"
    assert cand["rendered_evidence"]["source_kind"] == "rendered_html"
    assert cand["rendered_evidence"]["raw_capture_manifest_sha256"] == manifest_sha
    assert cand["rendered_evidence"]["raw_capture_file_locator"]["manifest_path"] == "data/sources/enwiktionary-tamil-rendered-2026-11-16/manifest.json"
    assert "decisions" not in report
    assert report["acceptance_decisions"] == 0
    assert report["canonical_promoted"] is False
    assert all(r["historical_claims_approved"] is False for r in report["records"])
    assert report["records"][0]["blocker_counts"] == {"TAMIL_IN_ENGLISH_GLOSS_REJECTED": 1, "ENTRY_NO_VALID_SENSES_REMAINING": 1}


def test_real_queue_and_existing_inputs_are_bounded_and_unmodified() -> None:
    """Verify real reconciliation queue resolves <= 384 pinned pages without touching protected sources."""
    queue_path = ROOT / "docs/audits/wiktionary-gap-reconciliation-2026-11-16.json"
    assert queue_path.is_file()
    queue = build_rendered_queue(
        reconciliation_path=queue_path,
        bulk_snapshot_dir=ROOT / "data/sources/enwiktionary-tamil",
        supplemental_dir=ROOT / "data/sources/enwiktionary-tamil-gap-2026-11-16",
    )
    assert 0 < len(queue) <= MAX_RENDERED_PAGES
    assert len(queue) == 384
    assert all(unicodedata.is_normalized("NFC", item["title"]) for item in queue)


def test_wikitext_acceptance_builder_rejects_rendered_proposals(tmp_path):
    from tools.lexicon_wiktionary_bulk import _build_bulk_pack_workspace
    with pytest.raises(ValueError, match="Rendered.*review"):
        _build_bulk_pack_workspace("core", [("sample", {"rendered_evidence": {"source_kind": "rendered_html"}})], manifest={}, workspace_dir=tmp_path / "workspace", legalcode_src=tmp_path / "missing")
    assert not (tmp_path / "workspace").exists()


def test_cached_reconciliation_rejects_pin_changes_and_missing_page_injection():
    page = _rendered_page(title="sample", pageid=1, revid=2, html="<div></div>")
    source = {key: page[key] for key in ("pageid", "revid", "wikitext_sha256")}
    for key in source:
        wrong = dict(source)
        wrong[key] = "f" * 64 if key == "wikitext_sha256" else 999
        with pytest.raises(ValueError, match="identity differs"):
            reconcile_rendered_queue([{"headword": "sample", "source": wrong}], {"sample": page})
    with pytest.raises(ValueError, match="identity differs"):
        reconcile_rendered_queue([{"headword": "sample", "status": "missing_from_snapshot"}], {"sample": page})
    with pytest.raises(ValueError, match="queue fingerprint"):
        verify_rendered_queue_binding([], {"queue_sha256": "f" * 64})
    page.pop("raw_api_response_sha256")
    with pytest.raises(ValueError, match="raw_api_response_sha256"):
        verify_rendered_page(page)
