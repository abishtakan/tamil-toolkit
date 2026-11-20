"""Explicit pending/rejection ingestion never manufactures an acceptance."""

import pytest

from tools.lexicon import LexiconError, inventory, stage


def test_pending_decision_ingestion_is_idempotent_and_stale_is_rejected(tmp_path):
    from tools.lexicon_ingest import ingest
    from tools.lexicon_tables import read_rows, write_rows
    from tools.lexicon_review import evidence_hash
    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta\n1,example\n", encoding="utf-8")
    inv, ws = tmp_path / "inventory", tmp_path / "ws"
    inventory(source, inv)
    stage(inv, ws)
    claim = next(read_rows(ws / "assertions.csv"))
    evidence = list(read_rows(ws / "evidence.csv"))
    row = {"decision_id":"dec_test_pending", "assertion_id":claim["assertion_id"], "assertion_revision_sha256":claim["claim_revision_sha256"],
        "evidence_bundle_sha256":evidence_hash(evidence), "outcome":"pending", "actor_type":"automated", "actor_id":None,
        "method_version":"structural-test-v1", "decision_date":"2026-11-14", "note_json":"Synthetic pending fixture", "predecessor_decision_id":None}
    path = tmp_path / "decisions.csv"
    write_rows(path, "decisions", [row])
    assert ingest(ws, "decisions", path)["inserted"] == 1
    assert ingest(ws, "decisions", path)["inserted"] == 0
    row.update(decision_id="dec_stale", assertion_revision_sha256="0"*64)
    write_rows(path,"decisions",[row])
    with pytest.raises(LexiconError, match="stale"):
        ingest(ws,"decisions",path)
    assert len(list(read_rows(ws / "decisions.csv"))) == 1


def test_ingest_evidence_uses_five_tuple_key_and_verifies_source_record_id(tmp_path):
    from tools.lexicon_ingest import ingest
    from tools.lexicon_tables import read_rows, write_rows

    source = tmp_path / "source"
    source.mkdir()
    (source / "primary_lemmas.csv").write_text("word_id,headword_ta\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe\n", encoding="utf-8")
    inv, ws = tmp_path / "inventory", tmp_path / "ws"
    inventory(source, inv)
    stage(inv, ws)

    base_ev = next(read_rows(ws / "evidence.csv"))
    sup_ev = dict(base_ev, evidence_role="supports")
    ev_in = tmp_path / "ev_supports.csv"
    write_rows(ev_in, "evidence", [sup_ev])
    assert ingest(ws, "evidence", ev_in)["inserted"] == 1
    assert len(list(read_rows(ws / "evidence.csv"))) == 2

    # Same 5-tuple with altered extraction metadata must fail rather than append a duplicate.
    conflict_ev = dict(sup_ev, extraction_version="v2-conflicting")
    write_rows(ev_in, "evidence", [conflict_ev])
    with pytest.raises(LexiconError, match="conflicting"):
        ingest(ws, "evidence", ev_in)

    # Unknown source_record_id must be rejected.
    bad_rec_ev = dict(sup_ev, source_record_id="rec_nonexistent", locator_json="other:1")
    write_rows(ev_in, "evidence", [bad_rec_ev])
    with pytest.raises(LexiconError, match="source_record"):
        ingest(ws, "evidence", ev_in)


def _setup_extended_ingest_workspace(tmp_path):
    import hashlib
    from tools.lexicon import NAMESPACE, allocate_id, json_text
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_tables import write_rows

    ws = tmp_path / "ws_ext"
    ws.mkdir()
    snap_id = allocate_id("snp", NAMESPACE, "ingest-snap")
    src_id = allocate_id("src", NAMESPACE, "ingest-src")
    rec_id = allocate_id("rec", NAMESPACE, "ingest-rec")
    ent_id = allocate_id("ent", NAMESPACE, "ingest-ent")
    ent2_id = allocate_id("ent", NAMESPACE, "ingest-ent-2")
    frm_id = allocate_id("frm", NAMESPACE, "ingest-frm")
    sen_id = allocate_id("sen", NAMESPACE, "ingest-sen")
    txt_id = allocate_id("txt", NAMESPACE, "ingest-txt")
    ast_hw = allocate_id("ast", NAMESPACE, "ingest-ast-hw")
    ast_pos = allocate_id("ast", NAMESPACE, "ingest-ast-pos")
    ast_def = allocate_id("ast", NAMESPACE, "ingest-ast-def")
    ast_scp = allocate_id("ast", NAMESPACE, "ingest-ast-scp")
    ast_zwj = allocate_id("ast", NAMESPACE, "ingest-ast-zwj")
    ast_pos2 = allocate_id("ast", NAMESPACE, "ingest-ast-pos-2")
    zero_sha = hashlib.sha256(b"ingest-content").hexdigest()

    write_rows(ws / "snapshots.csv", "snapshots", [{
        "snapshot_id": snap_id, "dataset_id": "synthetic-ingest", "relative_path": "primary_lemmas.csv",
        "byte_length": 64, "sha256": zero_sha, "media_type": "text/csv", "logical_row_count": 2,
    }])
    write_rows(ws / "sources.csv", "sources", [{
        "source_id": src_id, "label_json": "Ingest Source", "publication_json": "Synthetic",
        "url_json": None, "edition_json": None, "locator_json": "primary_lemmas.csv:2",
        "snapshot_id": snap_id, "retrieval_date_state": "known", "retrieval_date_json": "2026-11-14",
        "extraction_method": "synthetic", "extraction_version": "1",
        "evidence_verification_state": "verified", "reuse_basis_json": "Synthetic permissive test basis",
        "reuse_state": "permitted", "attribution_text_json": "Synthetic Attribution",
        "attribution_reference_json": None,
    }])
    write_rows(ws / "source_records.csv", "source_records", [{
        "record_id": rec_id, "snapshot_id": snap_id, "ordinal": 2, "physical_line_start": 2,
        "physical_line_end": 2, "legacy_key_json": "1", "raw_row_sha256": zero_sha,
    }])

    def make_claim(aid, skind, sid, prop, val):
        row = {
            "assertion_id": aid, "subject_kind": skind, "subject_id": sid, "property_code": prop,
            "value_state": "known", "value_json": val, "origin": "verbatim_source",
            "source_fidelity_state": "verified", "ambiguity_state": "unambiguous",
            "algorithm_reference": None, "convention_reference": None,
            "imported_status_json": None, "imported_confidence_json": None,
        }
        row["claim_revision_sha256"] = claim_revision(row)
        return row

    zwj_val = "\u0b85\u0bae\u0bcd\u0bae\u0bbe " + chr(0x200D)
    claims = [
        make_claim(ast_hw, "form", frm_id, "headword", "\u0b85\u0bae\u0bcd\u0bae\u0bbe"),
        make_claim(ast_pos, "entry", ent_id, "part_of_speech", "NOUN"),
        make_claim(ast_pos2, "entry", ent_id, "part_of_speech", "PROPN"),
        make_claim(ast_def, "text", txt_id, "definition", "mother"),
        make_claim(ast_scp, "entry", ent_id, "region_scope", "LK-JAFFNA"),
        make_claim(ast_zwj, "entry", ent_id, "variant_note", zwj_val),
    ]
    ev_rows = [{
        "assertion_id": c["assertion_id"], "source_id": src_id, "source_record_id": rec_id,
        "locator_json": json_text({"ordinal": 2, "prop": c["property_code"], "aid": c["assertion_id"]}),
        "evidence_role": "supports", "extraction_version": "1", "extraction_sha256": zero_sha,
    } for c in claims]
    ev_by_aid = {e["assertion_id"]: [e] for e in ev_rows}
    dec_scp = allocate_id("dec", NAMESPACE, "ingest-dec-scp")
    dec_zwj = allocate_id("dec", NAMESPACE, "ingest-dec-zwj")
    dec_chg = allocate_id("dec", NAMESPACE, "ingest-dec-chg")
    dec_id = allocate_id("dec", NAMESPACE, "ingest-dec-succ")
    decisions = [
        {
            "decision_id": dec_scp, "assertion_id": ast_scp,
            "assertion_revision_sha256": claims[4]["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash(ev_by_aid[ast_scp]),
            "outcome": "accepted_human", "actor_type": "human", "actor_id": "human.reviewer",
            "method_version": None, "decision_date": "2026-11-14",
            "note_json": "Synthetic scope review", "predecessor_decision_id": None,
        },
        {
            "decision_id": dec_zwj, "assertion_id": ast_zwj,
            "assertion_revision_sha256": claims[5]["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash(ev_by_aid[ast_zwj]),
            "outcome": "accepted_human", "actor_type": "human", "actor_id": "human.reviewer",
            "method_version": None, "decision_date": "2026-11-14",
            "note_json": "Synthetic ZWJ review", "predecessor_decision_id": None,
        },
        {
            "decision_id": dec_chg, "assertion_id": ast_pos2,
            "assertion_revision_sha256": claims[2]["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash(ev_by_aid[ast_pos2]),
            "outcome": "accepted_human", "actor_type": "human", "actor_id": "human.reviewer",
            "method_version": None, "decision_date": "2026-11-14",
            "note_json": "Synthetic POS change", "predecessor_decision_id": None,
        },
        {
            "decision_id": dec_id, "assertion_id": ast_pos,
            "assertion_revision_sha256": claims[1]["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash(ev_by_aid[ast_pos]),
            "outcome": "accepted_human", "actor_type": "human", "actor_id": "human.reviewer",
            "method_version": None, "decision_date": "2026-11-14",
            "note_json": "Synthetic merge decision", "predecessor_decision_id": None,
        },
    ]
    ent_rev = hashlib.sha256(b"entry-rev-1").hexdigest()
    write_rows(ws / "identities.csv", "identities", [
        {"entity_id": ent_id, "kind": "entry", "allocation_key": "k1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": ent2_id, "kind": "entry", "allocation_key": "k2", "lifecycle": "merged", "identity_decision_id": dec_id},
        {"entity_id": frm_id, "kind": "form", "allocation_key": "f1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_id, "kind": "sense", "allocation_key": "s1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_id, "kind": "text", "allocation_key": "t1", "lifecycle": "active", "identity_decision_id": None},
    ])
    write_rows(ws / "entries.csv", "entries", [{
        "entry_id": ent_id, "language_id": "tam", "variety_id": None, "canonical_form_id": frm_id,
        "pos_assertion_id": ast_pos, "structural_kind": "synthetic", "revision": ent_rev,
    }])
    write_rows(ws / "forms.csv", "forms", [{
        "form_id": frm_id, "entry_id": ent_id, "representation": "written", "role": "canonical",
        "text_assertion_id": ast_hw, "convention_assertion_id": None,
    }])
    write_rows(ws / "senses.csv", "senses", [{
        "sense_id": sen_id, "entry_id": ent_id, "display_order": 1, "parent_sense_id": None,
    }])
    write_rows(ws / "texts.csv", "texts", [{
        "text_id": txt_id, "owner_kind": "sense", "owner_id": sen_id, "component": "definition",
        "language_id": "eng", "text_assertion_id": ast_def, "paired_translation_id": None,
        "cited_source_locator_json": None,
    }])
    write_rows(ws / "assertions.csv", "assertions", claims)
    write_rows(ws / "evidence.csv", "evidence", ev_rows)
    write_rows(ws / "decisions.csv", "decisions", decisions)
    write_rows(ws / "findings.csv", "findings", [])
    return ws, {
        "ent_id": ent_id, "ent2_id": ent2_id, "ent_rev": ent_rev,
        "ast_pos": ast_pos, "ast_pos2": ast_pos2, "ast_scp": ast_scp, "ast_zwj": ast_zwj,
        "dec_scp": dec_scp, "dec_zwj": dec_zwj, "dec_chg": dec_chg, "dec_id": dec_id,
        "zwj_val": zwj_val,
    }


def test_ingest_pack_members_labels_scopes_validates_fks_revisions_and_conflicts(tmp_path):
    from tools.lexicon import main as lexicon_main
    from tools.lexicon_ingest import ingest
    from tools.lexicon_tables import write_rows

    ws, ids = _setup_extended_ingest_workspace(tmp_path)
    ext = tmp_path / "external"
    ext.mkdir()

    # 1. labels ingest (parent first, then child) + idempotence + conflict/FK errors
    lbl_parent = {
        "registry_id": "reg_geo", "registry_version": "1", "code": "LK", "category": "region",
        "display_label_json": "Sri Lanka", "definition_json": "Sri Lanka region",
        "evidence_reference": ids["ast_scp"], "parent_code": None,
    }
    lbl_child = {
        "registry_id": "reg_geo", "registry_version": "1", "code": "LK-JAFFNA", "category": "region",
        "display_label_json": "Jaffna", "definition_json": "Jaffna Tamil region",
        "evidence_reference": ids["ast_scp"], "parent_code": "LK",
    }
    lbl_in = ext / "labels.csv"
    write_rows(lbl_in, "labels", [lbl_parent, lbl_child])
    assert ingest(ws, "labels", lbl_in)["inserted"] == 2
    assert ingest(ws, "labels", lbl_in)["inserted"] == 0

    write_rows(lbl_in, "labels", [dict(lbl_child, display_label_json="Changed Jaffna")])
    with pytest.raises(LexiconError, match="conflicting"):
        ingest(ws, "labels", lbl_in)

    write_rows(lbl_in, "labels", [dict(lbl_child, code="LK-BAD", parent_code="MISSING")])
    with pytest.raises(LexiconError):
        ingest(ws, "labels", lbl_in)

    # 2. scopes ingest + idempotence + invalid/conflicting scope rejection
    scp_row = {
        "subject_kind": "entry", "subject_id": ids["ent_id"], "dimension": "region",
        "state": "attested", "label_code": "LK-JAFFNA",
        "supporting_assertion_id": ids["ast_scp"], "decision_id": ids["dec_scp"],
    }
    scp_in = ext / "scopes.csv"
    write_rows(scp_in, "scopes", [scp_row])
    assert lexicon_main(["review-ingest", "--workspace", str(ws), "--table", "scopes", "--input", str(scp_in)]) == 0
    assert ingest(ws, "scopes", scp_in)["inserted"] == 0

    write_rows(scp_in, "scopes", [dict(scp_row, state="unrestricted", label_code=None)])
    with pytest.raises(LexiconError):
        ingest(ws, "scopes", scp_in)

    write_rows(scp_in, "scopes", [dict(scp_row, label_code="UNKNOWN_REGION")])
    with pytest.raises(LexiconError):
        ingest(ws, "scopes", scp_in)

    # 3. pack_members ingest + idempotence + revision/cross-pack conflict rejection
    pm_row = {
        "pack_id": "core", "entry_id": ids["ent_id"],
        "included_revision": ids["ent_rev"], "relation_inclusion_policy": "omit_cross_pack",
    }
    pm_in = ext / "pack_members.csv"
    write_rows(pm_in, "pack_members", [pm_row])
    assert ingest(ws, "pack_members", pm_in)["inserted"] == 1
    assert ingest(ws, "pack_members", pm_in)["inserted"] == 0

    write_rows(pm_in, "pack_members", [dict(pm_row, pack_id="regional", included_revision="0" * 64)])
    with pytest.raises(LexiconError):
        ingest(ws, "pack_members", pm_in)

    write_rows(pm_in, "pack_members", [dict(pm_row, pack_id="unknown_pack")])
    with pytest.raises(LexiconError):
        ingest(ws, "pack_members", pm_in)


def test_ingest_unicode_exceptions_changes_and_successors_validate_history_and_conflicts(tmp_path):
    import hashlib
    from tools.lexicon_ingest import ingest
    from tools.lexicon_review import claim_revision
    from tools.lexicon_tables import read_rows, write_rows

    ws, ids = _setup_extended_ingest_workspace(tmp_path)
    ext = tmp_path / "external"
    ext.mkdir()

    zwj_claim = next(r for r in read_rows(ws / "assertions.csv") if r["assertion_id"] == ids["ast_zwj"])
    exc_row = {
        "assertion_id": ids["ast_zwj"],
        "claim_revision_sha256": claim_revision(zwj_claim),
        "value_sha256": hashlib.sha256(ids["zwj_val"].encode("utf-8")).hexdigest(),
        "kind": "intentional_control",
        "scalar_sequence": [0x200D],
        "scalar_position": ids["zwj_val"].index(chr(0x200D)),
        "reason_json": "Preserve ZWJ",
        "decision_id": ids["dec_zwj"],
    }
    exc_in = ext / "unicode_exceptions.csv"
    write_rows(exc_in, "unicode_exceptions", [exc_row])
    assert ingest(ws, "unicode_exceptions", exc_in)["inserted"] == 1
    assert ingest(ws, "unicode_exceptions", exc_in)["inserted"] == 0

    write_rows(exc_in, "unicode_exceptions", [dict(exc_row, scalar_position=0)])
    with pytest.raises(LexiconError):
        ingest(ws, "unicode_exceptions", exc_in)

    chg_row = {
        "change_id": "chg_pos_1", "subject_id": ids["ent_id"],
        "old_assertion_id": ids["ast_pos"], "new_assertion_id": ids["ast_pos2"],
        "reason_json": "Corrected POS", "evidence_reference": ids["ast_pos2"],
        "decision_id": ids["dec_chg"], "inverse_change_id": None,
    }
    chg_in = ext / "changes.csv"
    write_rows(chg_in, "changes", [chg_row])
    assert ingest(ws, "changes", chg_in)["inserted"] == 1
    assert ingest(ws, "changes", chg_in)["inserted"] == 0

    write_rows(chg_in, "changes", [dict(chg_row, change_id="chg_broken", old_assertion_id=ids["ast_pos"])])
    with pytest.raises(LexiconError):
        ingest(ws, "changes", chg_in)

    succ_row = {
        "retired_id": ids["ent2_id"], "successor_id": ids["ent_id"],
        "role": "merge", "identity_decision_id": ids["dec_id"],
    }
    succ_in = ext / "successors.csv"
    write_rows(succ_in, "successors", [succ_row])
    assert ingest(ws, "successors", succ_in)["inserted"] == 1
    assert ingest(ws, "successors", succ_in)["inserted"] == 0

    write_rows(succ_in, "successors", [dict(succ_row, role="split")])
    with pytest.raises(LexiconError):
        ingest(ws, "successors", succ_in)
