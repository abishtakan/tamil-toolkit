"""Regression parity tests for Feature 021 remaining structural speedups."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import uuid

import pytest

from tools.lexicon import (
    DEFAULT_SORT_BATCH_SIZE,
    NAMESPACE,
    LexiconError,
    inventory,
    stage,
    allocate_id,
)
from tools.lexicon_proof import _iter_csv_columns, verify_source_payloads
from tools.lexicon_review import claim_revision
from tools.lexicon_tables import (
    _RS_PATTERN_REWRITES,
    SCHEMA_DIR,
    TableRowWriter,
    _table_registry,
    read_rows,
    validate_row,
    write_rows,
)
from tools.lexicon_validate import check_curated_csv, validate_projection

ZERO_SHA = "0" * 64
ONE_SHA = "1" * 64


def _collect_schema_patterns(node, found: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_schema_patterns(item, found)
    elif isinstance(node, dict):
        pat = node.get("pattern")
        if isinstance(pat, str):
            found.add(pat)
        for val in node.values():
            _collect_schema_patterns(val, found)


def test_rs_pattern_rewrites_cover_all_schemas_and_match_python_edge_cases():
    discovered: set[str] = set()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        _collect_schema_patterns(json.loads(path.read_text(encoding="utf-8")), discovered)
    assert discovered <= set(_RS_PATTERN_REWRITES)

    reg = _table_registry()
    base_snap = {
        "snapshot_id": "snap_1",
        "dataset_id": "ds_1",
        "relative_path": "intake/source.csv",
        "byte_length": 42,
        "sha256": ZERO_SHA,
        "media_type": "text/csv",
        "logical_row_count": 2,
    }
    for rel in (
        "a/b.csv",
        "a/b.csv\n",
        "\n",
        "C:bad.csv",
        "/abs.csv",
        "\\win.csv",
        "../up.csv",
        "a/../b.csv",
        "a\n/../b.csv",
        "good\nline.csv",
    ):
        row = {**base_snap, "relative_path": rel}
        assert reg["snapshots"].fast_validator.is_valid(row) == reg["snapshots"].validator.is_valid(row)

    base_entry = {
        "entry_id": "ent_1",
        "language_id": "tam",
        "variety_id": None,
        "canonical_form_id": "frm_1",
        "pos_assertion_id": "asr_pos",
        "structural_kind": "lexeme",
        "revision": ZERO_SHA,
    }
    for eid, rev in (
        ("ent_1", ZERO_SHA),
        ("ent_1\n", ZERO_SHA),
        ("ent_1\nx", ZERO_SHA),
        ("ent_1", ZERO_SHA + "\n"),
        ("ent_1", "g" * 64),
    ):
        row = {**base_entry, "entry_id": eid, "revision": rev}
        assert reg["entries"].fast_validator.is_valid(row) == reg["entries"].validator.is_valid(row)


def test_allocate_id_fast_path_matches_uuid5_reference():
    custom_ns = uuid.uuid5(uuid.NAMESPACE_URL, "https://example.invalid/lexicon-test")
    for ns in (NAMESPACE, str(NAMESPACE), custom_ns, str(custom_ns)):
        ns_uuid = ns if isinstance(ns, uuid.UUID) else uuid.UUID(str(ns))
        for key in ("plain", "primary:word:\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", "k:1:2", 42):
            expected = f"ent_{uuid.uuid5(ns_uuid, str(key))}"
            assert allocate_id("ent", ns, key) == expected

    with pytest.raises(LexiconError):
        allocate_id("", NAMESPACE, "k")
    with pytest.raises(LexiconError):
        allocate_id("ent", "not-a-uuid", "k")


def test_table_row_writer_chunked_merge_matches_single_batch_and_is_atomic(tmp_path):
    assert DEFAULT_SORT_BATCH_SIZE >= 4096
    rows = []
    for idx in reversed(range(11)):
        claim = {
            "assertion_id": f"asr_{idx:02d}",
            "subject_kind": "entry",
            "subject_id": f"ent_{idx:02d}",
            "property_code": "misc",
            "value_state": "known",
            "value_json": {"order": idx, "text": f"\u0ba4\u0bae\u0bbf\u0bb4\u0bcd-{idx}"},
            "origin": "verbatim_source",
            "source_fidelity_state": "verified",
            "ambiguity_state": "unambiguous",
            "algorithm_reference": None,
            "convention_reference": None,
            "imported_status_json": None,
            "imported_confidence_json": None,
        }
        claim["claim_revision_sha256"] = claim_revision(claim)
        rows.append(claim)

    single_path = tmp_path / "single.csv"
    chunked_path = tmp_path / "chunked.csv"
    write_rows(single_path, "assertions", rows)
    with TableRowWriter(chunked_path, "assertions", batch_size=3) as writer:
        for row in rows:
            writer.write_row(row)
        writer.finish()

    expected_bytes = single_path.read_bytes()
    assert chunked_path.read_bytes() == expected_bytes
    assert [r["assertion_id"] for r in read_rows(chunked_path, "assertions")] == [f"asr_{i:02d}" for i in range(11)]

    with pytest.raises(LexiconError):
        with TableRowWriter(chunked_path, "assertions", batch_size=2) as writer:
            writer.write_row(rows[0])
            writer.write_row({**rows[1], "subject_kind": "not_a_kind"})
            writer.finish()
    assert chunked_path.read_bytes() == expected_bytes


def test_check_curated_csv_preloaded_projection_matches_transitive_assertions(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe\n", encoding="utf-8")
    inv, ws = tmp_path / "inventory", tmp_path / "workspace"
    can = tmp_path / "canonical"
    can.mkdir()
    inventory(source, inv)
    stage(inv, ws)

    base_res = check_curated_csv(workspace=ws, canonical=can)
    assert base_res["findings"] == []
    assert list(base_res["counts"]) == [str(p.relative_to(ws.parent)) for p in sorted(ws.glob("*.csv"))]

    # Corrupt an identity lifecycle without a decision ID: both validate_projection and check_curated_csv must catch it.
    bad_ws = tmp_path / "bad_ws"
    bad_ws.mkdir()
    for p in ws.iterdir():
        bad_ws.joinpath(p.name).write_bytes(p.read_bytes())
    id_rows = list(read_rows(bad_ws / "identities.csv"))
    id_rows[0]["lifecycle"] = "merged"
    # Bypass the writer deliberately to exercise malformed-file fallback.
    with (bad_ws / "identities.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(id_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: "" if v is None else v for k, v in row.items()} for row in id_rows)
    with pytest.raises(LexiconError, match="identity_decision_id"):
        validate_projection(bad_ws)
    chk_res = check_curated_csv(workspace=bad_ws, canonical=can)
    assert any("identity_decision_id" in msg for msg in chk_res["findings"])

    # Transitive assertion-on-assertion link (`asr_scope` -> `asr_00`) where child sorts after target or missing target.
    trans_ws = tmp_path / "trans_ws"
    trans_ws.mkdir()
    snap_id = "snap_1"
    src_id = "src_1"
    ent_id = "ent_1"
    frm_id = "frm_1"
    asr_hw = {
        "assertion_id": "asr_b_hw",
        "subject_kind": "form",
        "subject_id": frm_id,
        "property_code": "headword",
        "value_state": "known",
        "value_json": "\u0b85\u0bae\u0bcd\u0bae\u0bbe",
        "origin": "verbatim_source",
        "source_fidelity_state": "verified",
        "ambiguity_state": "unambiguous",
        "algorithm_reference": None,
        "convention_reference": None,
        "imported_status_json": None,
        "imported_confidence_json": None,
    }
    asr_hw["claim_revision_sha256"] = claim_revision(asr_hw)
    asr_meta = {
        "assertion_id": "asr_a_meta",
        "subject_kind": "assertion",
        "subject_id": "asr_z_target",
        "property_code": "note",
        "value_state": "known",
        "value_json": "chained",
        "origin": "editorial",
        "source_fidelity_state": "unknown",
        "ambiguity_state": "unambiguous",
        "algorithm_reference": None,
        "convention_reference": None,
        "imported_status_json": None,
        "imported_confidence_json": None,
    }
    asr_meta["claim_revision_sha256"] = claim_revision(asr_meta)
    asr_target = {**asr_hw, "assertion_id": "asr_z_target", "subject_kind": "entry", "subject_id": ent_id, "property_code": "pos", "value_json": "NOUN"}
    asr_target["claim_revision_sha256"] = claim_revision(asr_target)

    write_rows(trans_ws / "snapshots.csv", "snapshots", [{"snapshot_id": snap_id, "dataset_id": "ds", "relative_path": "p.csv", "byte_length": 1, "sha256": ZERO_SHA, "media_type": "text/csv", "logical_row_count": 2}])
    write_rows(trans_ws / "sources.csv", "sources", [{"source_id": src_id, "label_json": "S", "publication_json": None, "url_json": None, "edition_json": None, "locator_json": None, "snapshot_id": snap_id, "retrieval_date_state": "unknown", "retrieval_date_json": None, "extraction_method": "m", "extraction_version": "1", "evidence_verification_state": "verified", "reuse_basis_json": "CC0", "reuse_state": "permitted", "attribution_text_json": "Attr", "attribution_reference_json": None}])
    write_rows(trans_ws / "identities.csv", "identities", [
        {"entity_id": ent_id, "kind": "entry", "allocation_key": "e1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": frm_id, "kind": "form", "allocation_key": "f1", "lifecycle": "active", "identity_decision_id": None},
    ])
    write_rows(trans_ws / "assertions.csv", "assertions", [asr_meta, asr_hw, asr_target])
    write_rows(trans_ws / "scopes.csv", "scopes", [{"subject_kind": "assertion", "subject_id": "asr_a_meta", "dimension": "register", "state": "attested", "label_code": "STD", "supporting_assertion_id": "asr_b_hw", "decision_id": "dec_missing"}])
    direct_codes = sorted({f.get("code") or f.get("issue_code") for f in validate_projection(trans_ws)})
    via_check = check_curated_csv(workspace=trans_ws, canonical=can)
    for code in direct_codes:
        assert any(code in f for f in via_check["findings"])


def test_verify_source_payloads_and_iter_csv_columns_edge_cases(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe\n", encoding="utf-8")
    inv, ws = tmp_path / "inventory", tmp_path / "workspace"
    inventory(source, inv)
    stage(inv, ws)
    res = verify_source_payloads(ws, source)
    assert res["matching_raw_assertions"] == 1

    # Escaped lone surrogate inside inner JSON string must still be caught despite backslash-u fast guard.
    tampered = ws / "assertions.csv"
    orig_rows = list(read_rows(tampered))
    inner_bad_esc = '{"headword_ta":"\\ud800","word_id":"1"}'
    for r in orig_rows:
        r["value_json"] = inner_bad_esc
        r["claim_revision_sha256"] = claim_revision(r)
    write_rows(tampered, "assertions", orig_rows)
    with pytest.raises(LexiconError, match="lone surrogate"):
        verify_source_payloads(ws, source)

    # _iter_csv_columns handles empty files, missing columns, and short rows cleanly.
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8", newline="\n")
    assert list(_iter_csv_columns(empty_csv, ("a",))) == []

    short_csv = tmp_path / "short.csv"
    short_csv.write_text("a,b,c\n1,2\n", encoding="utf-8", newline="\n")
    assert list(_iter_csv_columns(short_csv, ("a", "c"))) == [("1", None)]
    with pytest.raises(KeyError):
        list(_iter_csv_columns(short_csv, ("missing_col",)))


def test_uuid5_uses_nonsecurity_sha1(monkeypatch):
    import hashlib
    from tools import lexicon
    original = hashlib.sha1
    def restricted(data=b"", *, usedforsecurity=True):
        if usedforsecurity:
            raise ValueError("FIPS rejects security SHA1")
        return original(data, usedforsecurity=False)
    monkeypatch.setattr(hashlib, "sha1", restricted)
    ns = uuid.UUID("516a4194-9252-4fc4-9b15-d0d26abf0617")
    lexicon._namespace_sha1.cache_clear()
    assert allocate_id("ent", ns, "key") == "ent_" + str(uuid.uuid5(ns, "key"))


def test_dict_subclass_uses_reference_validation(tmp_path):
    from tools.lexicon import ROOT
    row = next(read_rows(ROOT / "data/curation/wiktionary-core-reviewed/snapshots.csv"))
    class Overridden(dict):
        def __getitem__(self, key):
            return "invalid integer" if key == "byte_length" else super().__getitem__(key)
        def keys(self):
            return list(super().keys())
    with pytest.raises(LexiconError, match="schema error"):
        write_rows(tmp_path / "snapshots.csv", "snapshots", [Overridden(row)])


def test_json_text_and_data_json_differential_parity():
    from tools import lexicon as lex

    ref_ascii = json.JSONEncoder(ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode
    ref_utf8 = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode

    def ref_data_json(value):
        text = ref_utf8(value)
        return text.translate(lex._DATA_JSON_TRANSLATE) if lex._DATA_JSON_AUDIT_RE.search(text) else text

    class StrSub(str):
        pass

    class DictSub(dict):
        pass

    samples = [
        None,
        True,
        False,
        0,
        -1,
        1.5,
        -0.0,
        "",
        "hello \"quoted\" \\ \n\t line",
        "\u0b85\u0bae\u0bcd\u0bae\u0bbe",
        f"zwj:{chr(0x200D)} zwnj:{chr(0x200C)} bom:{chr(0xFEFF)} shy:{chr(0x00AD)} ls:{chr(0x2028)} ps:{chr(0x2029)} del:\x7f c1:\x85",
        StrSub("sub\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"),
        [],
        [1, None, True, {"z": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", "a": [1, 2]}],
        {"b": "two", "a": None, "c": {"\u0b85": "\x9f", "inner": [False, True]}},
        DictSub({"k": f"v{chr(0x200C)}"}),
    ]
    for sample in samples:
        assert lex.json_text(sample) == ref_ascii(sample)
        assert lex.data_json(sample) == ref_data_json(sample)

    for bad in (float("nan"), float("inf"), float("-inf"), [float("nan")]):
        with pytest.raises(ValueError):
            lex.json_text(bad)
        with pytest.raises(ValueError):
            lex.data_json(bad)

    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    cyclic_dict: dict = {}
    cyclic_dict["self"] = cyclic_dict
    for cyclic in (cyclic_list, cyclic_dict):
        with pytest.raises(ValueError):
            lex.json_text(cyclic)
        with pytest.raises(ValueError):
            lex.data_json(cyclic)


def test_external_sort_writer_pickle_chunks_byte_exact_and_atomic(tmp_path):
    from tools.lexicon import _ExternalSortWriter

    hdr = ["k", "text"]
    rows = []
    # Exceed 1024-row pickle frame size and trigger multiple spilled chunk merges.
    for idx in range(2500, 0, -1):
        ch = "\u0b85\u0bae\u0bcd\u0bae\u0bbe" if idx % 3 == 0 else f"plain,{idx}\n\"q\""
        rows.append((f"{idx:06d}", "" if idx % 5 == 0 else ch))

    single = tmp_path / "single.csv"
    with _ExternalSortWriter(single, hdr, batch_size=10000) as w:
        for row in rows:
            w.add_tuple(row)
        w.finish()

    chunked = tmp_path / "chunked.csv"
    with _ExternalSortWriter(chunked, hdr, batch_size=1100) as w:
        for row in rows:
            w.add_tuple(row)
        w.finish()

    assert chunked.read_bytes() == single.read_bytes()
    assert not list(tmp_path.glob(".lexicon-*"))

    guarded = tmp_path / "guarded.csv"
    guarded.write_bytes(b"ORIGINAL_BYTES\n")
    with pytest.raises(RuntimeError, match="abort"):
        with _ExternalSortWriter(guarded, hdr, batch_size=5) as w:
            for row in rows[:20]:
                w.add_tuple(row)
            raise RuntimeError("abort mid-stream")

    assert guarded.read_bytes() == b"ORIGINAL_BYTES\n"
    assert not list(tmp_path.glob(".lexicon-*"))


def test_stage_claim_revision_matches_review_claim_revision():
    from tools.lexicon import data_json
    from tools.lexicon_stage import _stage_claim_revision

    cases = [
        ("ent", "entry", "unparsed_source_record", {"word_id": "1", "headword": "\u0b85\u0bae\u0bcd\u0bae\u0bbe"}, None, None),
        ("sen", "sense", "unparsed_source_record", {"id": "s\"1\\2", "note": f"a\nb{chr(0x200D)}"}, "accepted", "0.95"),
        ("rel", "relation", "imported_master_fields", {"w": "\ufeff\x7f", "k": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"}, "\u0ba8\u0ba9\u0bcd\u0bb1\u0bc1", None),
    ]
    for kind, subject_kind, prop, raw_row, status_val, conf_val in cases:
        aid = allocate_id("ast", NAMESPACE, f"{kind}:{prop}")
        sub = allocate_id(kind, NAMESPACE, f"k:{prop}")
        vjson = data_json(raw_row)
        assertion = {
            "assertion_id": aid,
            "subject_kind": subject_kind,
            "subject_id": sub,
            "property_code": prop,
            "value_state": "known",
            "value_json": vjson,
            "origin": "verbatim_source",
            "source_fidelity_state": "unknown",
            "ambiguity_state": "unknown",
            "algorithm_reference": None,
            "convention_reference": None,
            "imported_status_json": status_val,
            "imported_confidence_json": conf_val,
        }
        assert _stage_claim_revision(aid, subject_kind, sub, prop, vjson, status_val, conf_val) == claim_revision(assertion)


def test_deserialize_json_cell_scan_once_edge_cases():
    from tools.lexicon_tables import _deserialize_json_cell

    assert _deserialize_json_cell("c", "null") is None
    assert _deserialize_json_cell("c", "true") is True
    assert _deserialize_json_cell("c", "false") is False
    assert _deserialize_json_cell("c", "[1,2]") == [1, 2]
    assert _deserialize_json_cell("c", "[1, 2] ") == [1, 2]
    assert _deserialize_json_cell("c", ' "hi" ') == "hi"
    assert _deserialize_json_cell("c", '"\u0b85\u0bae\u0bcd\u0bae\u0bbe"') == "\u0b85\u0bae\u0bcd\u0bae\u0bbe"

    for bad in ("", "truefoo", "[1,2] x", "NaN", "[Infinity]", "xyz", '"\\ud800"', '"\x7f"', f'"{chr(0x200D)}"', '"\t"'):
        with pytest.raises(LexiconError):
            _deserialize_json_cell("c", bad)


def test_verify_source_payloads_chunk_batching_duplicates_and_failures(tmp_path, monkeypatch):
    from tools import lexicon_proof

    monkeypatch.setattr(lexicon_proof, "_SQL_QUERY_CHUNK", 2)
    monkeypatch.setattr(
        lexicon_proof,
        "_SELECT_EXPECTED_FULL",
        lexicon_proof._SELECT_EXPECTED_PREFIX + "?,?)",
    )

    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text(
        "word_id,headword_ta\n"
        "1,\u0b85\u0bae\u0bcd\u0bae\u0bbe\n"
        "2,\u0b85\u0baa\u0bcd\u0baa\u0bbe\n"
        "3,\u0b85\u0ba9\u0bcd\u0baa\u0bc1\n",
        encoding="utf-8",
    )
    (source / "unified_master_30col.csv").write_text(
        "word_id,headword_ta\n"
        "1,\u0b85\u0bae\u0bcd\u0bae\u0bbe\n"
        "2,\u0b85\u0baa\u0bcd\u0baa\u0bbe\n",
        encoding="utf-8",
    )
    inv, ws = tmp_path / "inventory", tmp_path / "workspace"
    inventory(source, inv)
    stage(inv, ws)

    ok = verify_source_payloads(ws, source)
    assert ok["source_records"] == 5
    assert ok["master_records"] == 2
    assert ok["matching_raw_assertions"] == 5

    assertions_path = ws / "assertions.csv"
    base_rows = list(read_rows(assertions_path))

    # Duplicate row within/across chunk boundary plus missing last row -> duplicates=1, missing=1.
    dup_rows = [base_rows[0], base_rows[0], base_rows[1], base_rows[2], base_rows[3]]
    write_rows(assertions_path, "assertions", dup_rows)
    with pytest.raises(LexiconError, match="missing=1, duplicates=1"):
        verify_source_payloads(ws, source)

    # Unexpected assertion ID.
    extra_row = {**base_rows[0], "assertion_id": "ast_" + "0" * 8 + "-0000-5000-8000-" + "0" * 12}
    extra_row["claim_revision_sha256"] = claim_revision(extra_row)
    write_rows(assertions_path, "assertions", base_rows + [extra_row])
    with pytest.raises(LexiconError, match="unexpected=1"):
        verify_source_payloads(ws, source)

    # Subject and property mismatches.
    bad_meta = list(base_rows)
    bad_meta[0] = {**bad_meta[0], "subject_id": bad_meta[1]["subject_id"]}
    bad_meta[0]["claim_revision_sha256"] = claim_revision(bad_meta[0])
    write_rows(assertions_path, "assertions", bad_meta)
    with pytest.raises(LexiconError, match="subject_mismatches=1"):
        verify_source_payloads(ws, source)

