"""L2 fail-closed release-guard tests (Feature 021 T034)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.lexicon import NAMESPACE, SOURCE, LexiconError, allocate_id, json_text, write_table

ROOT = Path(__file__).resolve().parents[2]
ALL_PACKS = ("core", "terminology", "names_taxa", "regional")


def _encode_schema_row(row: dict) -> dict[str, str]:
    """Encode a decoded row dict into CSV cells matching schemas/lexicon/*.schema.json."""
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
    write_table(workspace / f"{table_name}.csv", columns, [_encode_schema_row(r) for r in rows])


def _canonical_claim_sha(claim_without_digest: dict) -> str:
    try:
        from tools.lexicon_review import claim_revision

        return claim_revision(claim_without_digest)
    except ImportError:
        payload = {k: v for k, v in claim_without_digest.items() if k != "claim_revision_sha256"}
        return hashlib.sha256(json_text(payload).encode("ascii")).hexdigest()


def _evidence_bundle_sha(evidence_rows: list[dict]) -> str:
    canonical = sorted(
        (
            {
                "assertion_id": r["assertion_id"],
                "source_id": r["source_id"],
                "source_record_id": r["source_record_id"],
                "locator_json": r["locator_json"],
                "evidence_role": r["evidence_role"],
                "extraction_version": r["extraction_version"],
                "extraction_sha256": r["extraction_sha256"],
            }
            for r in evidence_rows
        ),
        key=lambda item: (item["source_id"], item["source_record_id"], item["evidence_role"], item["extraction_sha256"]),
    )
    return hashlib.sha256(json_text(canonical).encode("ascii")).hexdigest()


def _build_synthetic_workspace(
    workspace: Path,
    *,
    verified_source: bool = False,
    reuse_permitted: bool = False,
    decision_outcome: str | None = None,
    claim_origin: str = "verbatim_source",
    source_fidelity: str = "unknown",
    ambiguity_state: str = "unknown",
    evidence_role: str = "transcribes",
    stale_decision_revision: bool = False,
    add_pack_member: bool = False,
    pack_id: str = "core",
    open_error_finding: bool = False,
    value_json: str = "\u0b85\u0bae\u0bcd\u0bae\u0bbe",
    unicode_exceptions: list[dict] | None = None,
    extra_findings: list[dict] | None = None,
) -> Path:
    """Create a schema-valid synthetic workspace with zero approved source data."""
    workspace.mkdir(parents=True, exist_ok=True)
    snap_id = allocate_id("snp", NAMESPACE, "synthetic-snapshot")
    src_id = allocate_id("src", NAMESPACE, "synthetic-source")
    rec_id = allocate_id("rec", NAMESPACE, "synthetic-record-1")
    ent_id = allocate_id("ent", NAMESPACE, "synthetic-entry-1")
    ast_id = allocate_id("ast", NAMESPACE, "synthetic-assertion-1")
    dec_id = allocate_id("dec", NAMESPACE, "synthetic-decision-1")
    fnd_id = allocate_id("fnd", NAMESPACE, "synthetic-finding-1")
    zero_sha = hashlib.sha256(b"synthetic-content").hexdigest()
    empty_sha = hashlib.sha256(b"[]").hexdigest()

    snapshots = [{
        "snapshot_id": snap_id,
        "dataset_id": "synthetic-lexicon",
        "relative_path": "primary_lemmas.csv",
        "byte_length": 128,
        "sha256": zero_sha,
        "media_type": "text/csv",
        "logical_row_count": 2,
    }]
    sources = [{
        "source_id": src_id,
        "label_json": "Synthetic fixture source",
        "publication_json": "Synthetic fixture",
        "url_json": None,
        "edition_json": None,
        "locator_json": json_text({"relative_path": "primary_lemmas.csv", "snapshot_id": snap_id}),
        "snapshot_id": snap_id,
        "retrieval_date_state": "known",
        "retrieval_date_json": "2026-11-14",
        "extraction_method": "synthetic-stage",
        "extraction_version": "1",
        "evidence_verification_state": "verified" if verified_source else "unverified",
        "reuse_basis_json": "Synthetic permissive test basis" if reuse_permitted else None,
        "reuse_state": "permitted" if reuse_permitted else "unknown",
        "attribution_text_json": "Synthetic Attribution" if reuse_permitted else None,
        "attribution_reference_json": None,
    }]
    identities = [{
        "entity_id": ent_id,
        "kind": "entry",
        "allocation_key": "synthetic-entry-1",
        "lifecycle": "active",
        "identity_decision_id": None,
    }]
    source_records = [{
        "record_id": rec_id,
        "snapshot_id": snap_id,
        "ordinal": 2,
        "physical_line_start": 2,
        "physical_line_end": 2,
        "legacy_key_json": "1",
        "raw_row_sha256": zero_sha,
    }]
    is_quarantined = decision_outcome is None
    dispositions = [{
        "record_id": rec_id,
        "disposition": "quarantined" if is_quarantined else "mapped",
        "structural_state": "validated",
        "reason_code": "SOURCE_AND_REUSE_UNVERIFIED" if is_quarantined else "MAPPED_SYNTHETIC",
        "note_json": "Synthetic record disposition.",
        "finding_set_sha256": empty_sha,
        "method": "lexicon-host",
        "method_version": "1",
    }]
    record_targets = [] if is_quarantined else [{
        "record_id": rec_id,
        "entity_id": ent_id,
        "target_role": "primary",
    }]

    claim = {
        "assertion_id": ast_id,
        "subject_kind": "entry",
        "subject_id": ent_id,
        "property_code": "written_form" if not is_quarantined else "unparsed_source_record",
        "value_state": "known",
        "value_json": value_json,
        "origin": claim_origin,
        "source_fidelity_state": source_fidelity,
        "ambiguity_state": ambiguity_state,
        "algorithm_reference": None,
        "convention_reference": None,
        "imported_status_json": "verified",
        "imported_confidence_json": "1.0",
    }
    claim_sha = _canonical_claim_sha(claim)
    claim["claim_revision_sha256"] = claim_sha

    ev_row = {
        "assertion_id": ast_id,
        "source_id": src_id,
        "source_record_id": rec_id,
        "locator_json": json_text({"snapshot_id": snap_id, "ordinal": 2}),
        "evidence_role": evidence_role,
        "extraction_version": "1",
        "extraction_sha256": zero_sha,
    }
    ev_sha = _evidence_bundle_sha([ev_row])

    decisions = []
    if decision_outcome is not None:
        is_human = decision_outcome == "accepted_human"
        decisions.append({
            "decision_id": dec_id,
            "assertion_id": ast_id,
            "assertion_revision_sha256": hashlib.sha256(b"stale").hexdigest() if stale_decision_revision else claim_sha,
            "evidence_bundle_sha256": ev_sha,
            "outcome": decision_outcome,
            "actor_type": "human" if is_human else "automated",
            "actor_id": "human.reviewer" if is_human else None,
            "method_version": None if is_human else "1",
            "decision_date": "2026-11-14",
            "note_json": "Synthetic decision.",
            "predecessor_decision_id": None,
        })

    findings = []
    if open_error_finding:
        findings.append({
            "finding_id": fnd_id,
            "record_id": rec_id,
            "assertion_id": ast_id,
            "issue_code": "SYNTHETIC_BLOCKING_ERROR",
            "severity": "error",
            "scalar_positions": [0],
            "status": "open",
            "resolution_reason_json": None,
        })

    if extra_findings:
        findings.extend(extra_findings)

    pack_members = []
    if add_pack_member:
        pack_members.append({
            "pack_id": pack_id,
            "entry_id": ent_id,
            "included_revision": claim_sha,
            "relation_inclusion_policy": "evidence_only_external",
        })

    _write_workspace_table(workspace, "snapshots", ["snapshot_id", "dataset_id", "relative_path", "byte_length", "sha256", "media_type", "logical_row_count"], snapshots)
    _write_workspace_table(workspace, "sources", ["source_id", "label_json", "publication_json", "url_json", "edition_json", "locator_json", "snapshot_id", "retrieval_date_state", "retrieval_date_json", "extraction_method", "extraction_version", "evidence_verification_state", "reuse_basis_json", "reuse_state", "attribution_text_json", "attribution_reference_json"], sources)
    _write_workspace_table(workspace, "identities", ["entity_id", "kind", "allocation_key", "lifecycle", "identity_decision_id"], identities)
    _write_workspace_table(workspace, "source_records", ["record_id", "snapshot_id", "ordinal", "physical_line_start", "physical_line_end", "legacy_key_json", "raw_row_sha256"], source_records)
    _write_workspace_table(workspace, "dispositions", ["record_id", "disposition", "structural_state", "reason_code", "note_json", "finding_set_sha256", "method", "method_version"], dispositions)
    _write_workspace_table(workspace, "record_targets", ["record_id", "entity_id", "target_role"], record_targets)
    _write_workspace_table(workspace, "assertions", ["assertion_id", "subject_kind", "subject_id", "property_code", "value_state", "value_json", "origin", "source_fidelity_state", "ambiguity_state", "algorithm_reference", "convention_reference", "imported_status_json", "imported_confidence_json", "claim_revision_sha256"], [claim])
    _write_workspace_table(workspace, "evidence", ["assertion_id", "source_id", "source_record_id", "locator_json", "evidence_role", "extraction_version", "extraction_sha256"], [ev_row])
    _write_workspace_table(workspace, "decisions", ["decision_id", "assertion_id", "assertion_revision_sha256", "evidence_bundle_sha256", "outcome", "actor_type", "actor_id", "method_version", "decision_date", "note_json", "predecessor_decision_id"], decisions)
    _write_workspace_table(workspace, "findings", ["finding_id", "record_id", "assertion_id", "issue_code", "severity", "scalar_positions", "status", "resolution_reason_json"], findings)
    _write_workspace_table(workspace, "pack_members", ["pack_id", "entry_id", "included_revision", "relation_inclusion_policy"], pack_members)
    if unicode_exceptions is not None:
        _write_workspace_table(
            workspace,
            "unicode_exceptions",
            ["assertion_id", "claim_revision_sha256", "value_sha256", "kind", "scalar_sequence", "scalar_position", "reason_json", "decision_id"],
            unicode_exceptions,
        )
    return workspace


def test_release_guard_rejects_all_quarantine_workspace_across_all_packs(tmp_path):
    from tools.lexicon_pilot import release_guard

    ws = _build_synthetic_workspace(tmp_path / "ws_quarantine")
    for idx, pack in enumerate(ALL_PACKS):
        out_path = tmp_path / "reports" / f"release-{pack}-{idx}.json"
        r1 = release_guard(ws, pack=pack, output=out_path)
        r2 = release_guard(ws, pack=pack)

        assert r1 == r2
        assert r1["command"] == "release"
        assert r1["pack"] == pack
        assert r1["l3_pack_eligible"] is False
        assert r1["eligible_assertions"] == 0
        assert r1["runtime_verified"] is None

        error_codes = {f["code"] for f in r1["findings"] if f["severity"] == "error"}
        assert "NONEMPTY_ELIGIBLE_PACK_REQUIRED" in error_codes
        assert not any("UNSUPPORTED" in code for code in error_codes)

        raw = out_path.read_bytes()
        assert raw.decode("ascii") and raw.isascii()
        assert json.loads(raw) == r1


def test_release_guard_computes_zero_eligible_when_trust_or_decision_guards_fail(tmp_path):
    from tools.lexicon_pilot import release_guard

    # 1. accepted_auto_source + pack_members, but unverified source & unknown reuse
    ws_unverified = _build_synthetic_workspace(
        tmp_path / "ws_unverified",
        verified_source=False,
        reuse_permitted=False,
        decision_outcome="accepted_auto_source",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        add_pack_member=True,
    )
    # 2. verified + permitted source, but inferred origin cannot use accepted_auto_source
    ws_inferred = _build_synthetic_workspace(
        tmp_path / "ws_inferred",
        verified_source=True,
        reuse_permitted=True,
        decision_outcome="accepted_auto_source",
        claim_origin="inferred",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        add_pack_member=True,
    )
    # 3. accepted_human on verified/permitted verbatim_source, but stale revision sha256
    ws_stale = _build_synthetic_workspace(
        tmp_path / "ws_stale",
        verified_source=True,
        reuse_permitted=True,
        decision_outcome="accepted_human",
        claim_origin="verbatim_source",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        stale_decision_revision=True,
        add_pack_member=True,
    )

    for ws in (ws_unverified, ws_inferred, ws_stale):
        report = release_guard(ws, pack="core")
        assert report["l3_pack_eligible"] is False
        assert report["eligible_assertions"] == 0
        assert report["runtime_verified"] is None
        assert "NONEMPTY_ELIGIBLE_PACK_REQUIRED" in {
            f["code"] for f in report["findings"] if f["severity"] == "error"
        }


def test_release_guard_never_marks_l3_pack_eligible_before_full_l3_implementation(tmp_path):
    from tools.lexicon_pilot import release_guard

    ws = _build_synthetic_workspace(
        tmp_path / "ws_human_candidate",
        verified_source=True,
        reuse_permitted=True,
        decision_outcome="accepted_human",
        claim_origin="verbatim_source",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        add_pack_member=True,
    )
    report = release_guard(ws, pack="core")
    assert report["l3_pack_eligible"] is False
    assert report["runtime_verified"] is None
    assert any(f["severity"] == "error" for f in report["findings"])


def test_release_guard_rejects_unknown_pack_missing_workspace_or_overlapping_output(tmp_path):
    from tools.lexicon_pilot import release_guard

    ws = _build_synthetic_workspace(tmp_path / "ws_valid")

    with pytest.raises(LexiconError) as exc_pack:
        release_guard(ws, pack="nonexistent_pack")
    assert exc_pack.value.code == 2

    with pytest.raises(LexiconError) as exc_missing:
        release_guard(tmp_path / "missing_workspace", pack="core")
    assert exc_missing.value.code == 2

    (ws / "assertions.csv").unlink()
    with pytest.raises(LexiconError) as exc_table:
        release_guard(ws, pack="core")
    assert exc_table.value.code == 2

    ws2 = _build_synthetic_workspace(tmp_path / "ws_overlap")
    with pytest.raises(LexiconError) as exc_ws_out:
        release_guard(ws2, pack="core", output=ws2 / "release-report.json")
    assert exc_ws_out.value.code == 2

    with pytest.raises(LexiconError) as exc_src_out:
        release_guard(ws2, pack="core", output=SOURCE / "release-report.json")
    assert exc_src_out.value.code == 2


def test_release_guard_respects_unicode_exceptions_scoped_findings_and_cli_exit_1(tmp_path):
    from tools.lexicon import main as lexicon_main
    from tools.lexicon_pilot import release_guard
    from tools.lexicon_tables import read_rows

    # Claim contains an intentional ZWJ separated by space; only an exact exception + human decision clears it.
    zwj_word = "\u0b85\u0bae\u0bcd\u0bae\u0bbe " + chr(0x200D)
    unrelated_rec = allocate_id("rec", NAMESPACE, "unrelated-record")
    ws_base = _build_synthetic_workspace(
        tmp_path / "ws_base_exc",
        verified_source=True,
        reuse_permitted=True,
        decision_outcome="accepted_human",
        claim_origin="verbatim_source",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        add_pack_member=True,
        value_json=zwj_word,
    )
    claim_row = next(read_rows(ws_base / "assertions.csv"))
    dec_row = next(read_rows(ws_base / "decisions.csv"))
    rec_row = next(read_rows(ws_base / "source_records.csv"))
    exc_row = {
        "assertion_id": claim_row["assertion_id"],
        "claim_revision_sha256": claim_row["claim_revision_sha256"],
        "value_sha256": hashlib.sha256(zwj_word.encode("utf-8")).hexdigest(),
        "kind": "intentional_control",
        "scalar_sequence": [0x200D],
        "scalar_position": zwj_word.index(chr(0x200D)),
        "reason_json": "Synthetic intentional ZWJ preservation test",
        "decision_id": dec_row["decision_id"],
    }

    # Unrelated open error finding on another record_id does not block the excepted claim.
    ws_excepted = _build_synthetic_workspace(
        tmp_path / "ws_excepted",
        verified_source=True,
        reuse_permitted=True,
        decision_outcome="accepted_human",
        claim_origin="verbatim_source",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        add_pack_member=True,
        value_json=zwj_word,
        unicode_exceptions=[exc_row],
        extra_findings=[{
            "finding_id": allocate_id("fnd", NAMESPACE, "unrelated-finding"),
            "record_id": unrelated_rec,
            "assertion_id": None,
            "issue_code": "UNRELATED_RECORD_FINDING",
            "severity": "error",
            "scalar_positions": [],
            "status": "open",
            "resolution_reason_json": None,
        }],
    )
    rep_exc = release_guard(ws_excepted, pack="core")
    assert rep_exc["eligible_assertions"] == 1
    assert rep_exc["l3_pack_eligible"] is False
    assert rep_exc["runtime_verified"] is None
    exc_error_codes = {f["code"] for f in rep_exc["findings"] if f["severity"] == "error"}
    assert exc_error_codes
    assert "NONEMPTY_ELIGIBLE_PACK_REQUIRED" not in exc_error_codes

    # CLI release mode still exits 1 on early guard even when eligible_assertions > 0.
    out_pos = tmp_path / "cli-positive-early-guard.json"
    assert lexicon_main([
        "validate",
        "--workspace", str(ws_excepted),
        "--mode", "release",
        "--pack", "core",
        "--output", str(out_pos),
    ]) == 1
    assert json.loads(out_pos.read_text(encoding="ascii"))["eligible_assertions"] == 1

    # Without unicode_exceptions.csv, unicode_findings blocks eligibility (0 eligible).
    rep_no_exc = release_guard(ws_base, pack="core")
    assert rep_no_exc["eligible_assertions"] == 0
    assert rep_no_exc["l3_pack_eligible"] is False
    assert "NONEMPTY_ELIGIBLE_PACK_REQUIRED" in {
        f["code"] for f in rep_no_exc["findings"] if f["severity"] == "error"
    }

    # An open error finding on the evidence-linked record_id DOES block eligibility.
    ws_linked_err = _build_synthetic_workspace(
        tmp_path / "ws_linked_err",
        verified_source=True,
        reuse_permitted=True,
        decision_outcome="accepted_human",
        claim_origin="verbatim_source",
        source_fidelity="verified",
        ambiguity_state="unambiguous",
        evidence_role="supports",
        add_pack_member=True,
        value_json=zwj_word,
        unicode_exceptions=[exc_row],
        extra_findings=[{
            "finding_id": allocate_id("fnd", NAMESPACE, "linked-finding"),
            "record_id": rec_row["record_id"],
            "assertion_id": None,
            "issue_code": "LINKED_RECORD_BLOCKER",
            "severity": "error",
            "scalar_positions": [],
            "status": "open",
            "resolution_reason_json": None,
        }],
    )
    rep_linked = release_guard(ws_linked_err, pack="core")
    assert rep_linked["eligible_assertions"] == 0
    assert rep_linked["l3_pack_eligible"] is False

    # CLI release mode exits 1 on zero-eligible all-quarantined workspace.
    ws_quarantine = _build_synthetic_workspace(tmp_path / "ws_quarantine_cli")
    out_q = tmp_path / "cli-quarantine-release.json"
    assert lexicon_main([
        "validate",
        "--workspace", str(ws_quarantine),
        "--mode", "release",
        "--pack", "core",
        "--output", str(out_q),
    ]) == 1
    assert json.loads(out_q.read_text(encoding="ascii"))["eligible_assertions"] == 0


# ---------------------------------------------------------------------------
# T040 & T041: Full release closure validation & deterministic promotion
# ---------------------------------------------------------------------------


def _build_full_synthetic_workspace(
    workspace: Path,
    *,
    relation_policy: str | None = "omit_cross_pack",
    cross_pack_revision_conflict: bool = False,
    omit_canonical_form: bool = False,
    omit_pos: bool = False,
    ineligible_pos: bool = False,
    only_unparsed_sense: bool = False,
    accepted_unparsed: bool = False,
    accepted_entry_text: bool = False,
    accepted_optional_only: bool = False,
    stale_scope_assertion: bool = False,
    create_sense_cycle: bool = False,
    create_label_cycle: bool = False,
    bad_source_reuse: bool = False,
    declare_vocabularies: bool = True,
    unknown_vocab_pos: bool = False,
    unknown_vocab_region: bool = False,
    include_optional_pending_ipa: bool = True,
) -> dict:
    """Create a complete synthetic L3-capable workspace (clearly synthetic, non-approved)."""
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_tables import write_rows

    workspace.mkdir(parents=True, exist_ok=True)
    snap_id = allocate_id("snp", NAMESPACE, "full-syn-snap")
    src_id = allocate_id("src", NAMESPACE, "full-syn-src")
    rec_1 = allocate_id("rec", NAMESPACE, "full-syn-rec-1")
    rec_2 = allocate_id("rec", NAMESPACE, "full-syn-rec-2")
    rec_3 = allocate_id("rec", NAMESPACE, "full-syn-rec-3")
    ent_1 = allocate_id("ent", NAMESPACE, "full-syn-ent-1")
    ent_2 = allocate_id("ent", NAMESPACE, "full-syn-ent-2")
    ent_3 = allocate_id("ent", NAMESPACE, "full-syn-ent-3")
    frm_1 = allocate_id("frm", NAMESPACE, "full-syn-frm-1")
    frm_1_ipa = allocate_id("frm", NAMESPACE, "full-syn-frm-1-ipa")
    frm_2 = allocate_id("frm", NAMESPACE, "full-syn-frm-2")
    frm_3 = allocate_id("frm", NAMESPACE, "full-syn-frm-3")
    sen_1a = allocate_id("sen", NAMESPACE, "full-syn-sen-1a")
    sen_1b = allocate_id("sen", NAMESPACE, "full-syn-sen-1b")
    sen_2 = allocate_id("sen", NAMESPACE, "full-syn-sen-2")
    sen_3 = allocate_id("sen", NAMESPACE, "full-syn-sen-3")
    txt_1a = allocate_id("txt", NAMESPACE, "full-syn-txt-1a")
    txt_1a_ex = allocate_id("txt", NAMESPACE, "full-syn-txt-1a-ex")
    txt_1b = allocate_id("txt", NAMESPACE, "full-syn-txt-1b")
    txt_1_unparsed = allocate_id("txt", NAMESPACE, "full-syn-txt-1-unparsed")
    txt_1_entry = allocate_id("txt", NAMESPACE, "full-syn-txt-1-entry")
    txt_2 = allocate_id("txt", NAMESPACE, "full-syn-txt-2")
    txt_3 = allocate_id("txt", NAMESPACE, "full-syn-txt-3")
    rel_internal = allocate_id("rel", NAMESPACE, "full-syn-rel-int")
    rel_cross = allocate_id("rel", NAMESPACE, "full-syn-rel-cross")
    zero_sha = hashlib.sha256(b"full-synthetic-payload").hexdigest()

    (workspace / "dataset.toml").write_text(
        'schema_version = 1\n'
        'dataset_id = "synthetic-l3-test"\n'
        'dataset_version = "1"\n'
        f'id_namespace = "{NAMESPACE}"\n'
        'text_codec = "json-string-utf8-v1"\n'
        'registry_version = 1\n',
        encoding="ascii",
    )

    if declare_vocabularies:
        (workspace / "vocabularies.toml").write_text(
            'schema_version = 1\n'
            'vocabulary_version = "1"\n'
            'language_ids = ["eng", "tam"]\n'
            'parts_of_speech = ["NOUN", "VERB"]\n'
            'relation_codes = ["related_to", "synonym"]\n'
            'annotation_properties = ["root_word"]\n'
            'registers = ["formal"]\n'
            '[[regions]]\n'
            'code = "LK"\n'
            '[[regions]]\n'
            'code = "LK-JAFFNA"\n'
            'parent_code = "LK"\n',
            encoding="ascii",
        )

    snapshots = [{
        "snapshot_id": snap_id, "dataset_id": "synthetic-l3-test", "relative_path": "primary_lemmas.csv",
        "byte_length": 256, "sha256": zero_sha, "media_type": "text/csv", "logical_row_count": 4,
    }]
    sources = [{
        "source_id": src_id, "label_json": "Synthetic Verified Source", "publication_json": "Synthetic Pub",
        "url_json": None, "edition_json": None, "locator_json": "synthetic:1",
        "snapshot_id": snap_id, "retrieval_date_state": "known", "retrieval_date_json": "2026-11-14",
        "extraction_method": "synthetic-extractor", "extraction_version": "1",
        "evidence_verification_state": "verified",
        "reuse_basis_json": "CC0-1.0 synthetic test fixture",
        "reuse_state": "restricted" if bad_source_reuse else "permitted",
        "attribution_text_json": "Synthetic Test Attribution",
        "attribution_reference_json": None,
    }]
    source_records = [
        {"record_id": rec_1, "snapshot_id": snap_id, "ordinal": 2, "physical_line_start": 2, "physical_line_end": 2, "legacy_key_json": "1", "raw_row_sha256": zero_sha},
        {"record_id": rec_2, "snapshot_id": snap_id, "ordinal": 3, "physical_line_start": 3, "physical_line_end": 3, "legacy_key_json": "2", "raw_row_sha256": zero_sha},
        {"record_id": rec_3, "snapshot_id": snap_id, "ordinal": 4, "physical_line_start": 4, "physical_line_end": 4, "legacy_key_json": "3", "raw_row_sha256": zero_sha},
    ]
    dispositions = [
        {"record_id": rec_1, "disposition": "mapped", "structural_state": "validated", "reason_code": "MAPPED", "note_json": "Synthetic", "finding_set_sha256": hashlib.sha256(b"[]").hexdigest(), "method": "lexicon", "method_version": "1"},
        {"record_id": rec_2, "disposition": "mapped", "structural_state": "validated", "reason_code": "MAPPED", "note_json": "Synthetic", "finding_set_sha256": hashlib.sha256(b"[]").hexdigest(), "method": "lexicon", "method_version": "1"},
        {"record_id": rec_3, "disposition": "mapped", "structural_state": "validated", "reason_code": "MAPPED", "note_json": "Synthetic", "finding_set_sha256": hashlib.sha256(b"[]").hexdigest(), "method": "lexicon", "method_version": "1"},
    ]
    record_targets = [
        {"record_id": rec_1, "entity_id": ent_1, "target_role": "primary"},
        {"record_id": rec_2, "entity_id": ent_2, "target_role": "primary"},
        {"record_id": rec_3, "entity_id": ent_3, "target_role": "primary"},
    ]
    identities = [
        {"entity_id": ent_1, "kind": "entry", "allocation_key": "e1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": ent_2, "kind": "entry", "allocation_key": "e2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": ent_3, "kind": "entry", "allocation_key": "e3", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": frm_1, "kind": "form", "allocation_key": "f1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": frm_2, "kind": "form", "allocation_key": "f2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": frm_3, "kind": "form", "allocation_key": "f3", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_1a, "kind": "sense", "allocation_key": "s1a", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_1b, "kind": "sense", "allocation_key": "s1b", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_2, "kind": "sense", "allocation_key": "s2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_3, "kind": "sense", "allocation_key": "s3", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_1a, "kind": "text", "allocation_key": "t1a", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_1a_ex, "kind": "text", "allocation_key": "t1a_ex", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_1b, "kind": "text", "allocation_key": "t1b", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_1_unparsed, "kind": "text", "allocation_key": "t1u", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_2, "kind": "text", "allocation_key": "t2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_3, "kind": "text", "allocation_key": "t3", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": rel_internal, "kind": "relation", "allocation_key": "ri", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": rel_cross, "kind": "relation", "allocation_key": "rc", "lifecycle": "active", "identity_decision_id": None},
    ]
    if include_optional_pending_ipa:
        identities.append({"entity_id": frm_1_ipa, "kind": "form", "allocation_key": "f1ipa", "lifecycle": "active", "identity_decision_id": None})
    if accepted_entry_text:
        identities.append({"entity_id": txt_1_entry, "kind": "text", "allocation_key": "t1e", "lifecycle": "active", "identity_decision_id": None})

    assertions = []
    evidence = []
    decisions = []

    def add_claim(
        aid, skind, sid, prop, val, rec,
        *, origin="verbatim_source", fidelity="verified", ambiguity="unambiguous",
        outcome="accepted_human", actor_id="human.reviewer:1", method=None,
        stale_dec=False,
    ):
        row = {
            "assertion_id": aid, "subject_kind": skind, "subject_id": sid, "property_code": prop,
            "value_state": "known", "value_json": val, "origin": origin,
            "source_fidelity_state": fidelity, "ambiguity_state": ambiguity,
            "algorithm_reference": None, "convention_reference": None,
            "imported_status_json": None, "imported_confidence_json": None,
        }
        rev = claim_revision(row)
        row["claim_revision_sha256"] = rev
        assertions.append(row)
        ev = {
            "assertion_id": aid, "source_id": src_id, "source_record_id": rec,
            "locator_json": json_text({"record": rec, "aid": aid}),
            "evidence_role": "supports", "extraction_version": "1", "extraction_sha256": zero_sha,
        }
        evidence.append(ev)
        if outcome is not None:
            is_human = outcome == "accepted_human"
            decisions.append({
                "decision_id": allocate_id("dec", NAMESPACE, "dec:" + aid),
                "assertion_id": aid,
                "assertion_revision_sha256": ("0" * 64) if stale_dec else rev,
                "evidence_bundle_sha256": evidence_hash([ev]),
                "outcome": outcome,
                "actor_type": "human" if is_human else "automated",
                "actor_id": actor_id if is_human else None,
                "method_version": None if is_human else (method or "source-check:v1"),
                "decision_date": "2026-11-14",
                "note_json": "Private editorial note that must not leak",
                "predecessor_decision_id": None,
            })
        return row

    tamil_word = "\u0b85\u0bae\u0bcd\u0bae\u0bbe"  # அம்மா (NFC)
    pos_val = "FAKE_POS" if unknown_vocab_pos else "NOUN"
    ast_hw1 = add_claim(allocate_id("ast", NAMESPACE, "hw1"), "form", frm_1, "headword", tamil_word, rec_1)
    ast_hw2 = add_claim(
        allocate_id("ast", NAMESPACE, "hw2"), "form", frm_2, "headword", tamil_word, rec_2,
        outcome="accepted_auto_source", actor_id=None, method="source-check:v1",
    )
    ast_hw3 = add_claim(allocate_id("ast", NAMESPACE, "hw3"), "form", frm_3, "headword", "\u0ba8\u0bc0\u0bb0\u0bcd", rec_3)

    ast_pos1 = add_claim(
        allocate_id("ast", NAMESPACE, "pos1"), "entry", ent_1, "part_of_speech", pos_val, rec_1,
        outcome="pending" if (ineligible_pos or accepted_optional_only) else "accepted_human",
    )
    ast_pos2 = add_claim(
        allocate_id("ast", NAMESPACE, "pos2"), "entry", ent_2, "part_of_speech", "VERB", rec_2,
        outcome="accepted_auto_source", actor_id=None, method="source-check:v1",
    )
    ast_pos3 = add_claim(allocate_id("ast", NAMESPACE, "pos3"), "entry", ent_3, "part_of_speech", "NOUN", rec_3)

    ast_def1a = add_claim(
        allocate_id("ast", NAMESPACE, "def1a"), "text", txt_1a, "definition", "mother", rec_1,
        outcome="pending" if only_unparsed_sense else "accepted_human",
    )
    ast_ex1a = add_claim(allocate_id("ast", NAMESPACE, "ex1a"), "text", txt_1a_ex, "example", "\u0b85\u0bae\u0bcd\u0bae\u0bbe \u0bb5\u0ba8\u0bcd\u0ba4\u0bbe\u0bb0\u0bcd", rec_1)
    ast_def1b = add_claim(
        allocate_id("ast", NAMESPACE, "def1b"), "text", txt_1b, "gloss", "matron", rec_1,
        outcome="pending" if only_unparsed_sense else "accepted_human",
    )
    ast_unp = add_claim(
        allocate_id("ast", NAMESPACE, "unp1"), "text", txt_1_unparsed, "unparsed_text", "raw 1. 2. note", rec_1,
        outcome="accepted_human" if accepted_unparsed else "pending",
    )
    ast_def2 = add_claim(
        allocate_id("ast", NAMESPACE, "def2"), "text", txt_2, "definition", "exclaim in surprise", rec_2,
        outcome="accepted_auto_source", actor_id=None, method="source-check:v1",
    )
    ast_def3 = add_claim(allocate_id("ast", NAMESPACE, "def3"), "text", txt_3, "definition", "water", rec_3)

    ast_rel_int = add_claim(allocate_id("ast", NAMESPACE, "rel-int"), "relation", rel_internal, "relation_code", "related_to", rec_1)
    ast_rel_cross = add_claim(allocate_id("ast", NAMESPACE, "rel-cross"), "relation", rel_cross, "relation_code", "synonym", rec_1)

    ast_root1 = add_claim(allocate_id("ast", NAMESPACE, "root1"), "entry", ent_1, "root_word", "\u0b85\u0bae\u0bcd", rec_1)
    ast_scp_reg = add_claim(
        allocate_id("ast", NAMESPACE, "scp-reg"), "entry", ent_1, "region_scope", "LK-JAFFNA", rec_1,
        stale_dec=stale_scope_assertion,
    )
    ast_scp_reg_unr = add_claim(allocate_id("ast", NAMESPACE, "scp-unr"), "entry", ent_2, "region_scope", "unrestricted", rec_2)
    ast_scp_reg_f = add_claim(allocate_id("ast", NAMESPACE, "scp-f"), "entry", ent_1, "register_scope", "formal", rec_1)

    if include_optional_pending_ipa:
        ast_ipa1 = add_claim(
            allocate_id("ast", NAMESPACE, "ipa1"), "form", frm_1_ipa, "pronunciation_ipa", "amma\u02d0", rec_1,
            outcome="pending",
        )
    if accepted_entry_text:
        ast_et = add_claim(allocate_id("ast", NAMESPACE, "et1"), "text", txt_1_entry, "citation", "TLS p.1", rec_1)

    ent_rev_1 = hashlib.sha256(b"ent-rev-1").hexdigest()
    ent_rev_2 = hashlib.sha256(b"ent-rev-2").hexdigest()
    ent_rev_3 = hashlib.sha256(b"ent-rev-3").hexdigest()
    entries = [
        {"entry_id": ent_1, "language_id": "tam", "variety_id": None, "canonical_form_id": None if omit_canonical_form else frm_1, "pos_assertion_id": None if omit_pos else ast_pos1["assertion_id"], "structural_kind": "synthetic", "revision": ent_rev_1},
        {"entry_id": ent_2, "language_id": "tam", "variety_id": None, "canonical_form_id": frm_2, "pos_assertion_id": ast_pos2["assertion_id"], "structural_kind": "synthetic", "revision": ent_rev_2},
        {"entry_id": ent_3, "language_id": "tam", "variety_id": None, "canonical_form_id": frm_3, "pos_assertion_id": ast_pos3["assertion_id"], "structural_kind": "synthetic", "revision": ent_rev_3},
    ]
    forms = [
        {"form_id": frm_2, "entry_id": ent_2, "representation": "written", "role": "canonical", "text_assertion_id": ast_hw2["assertion_id"], "convention_assertion_id": None},
        {"form_id": frm_3, "entry_id": ent_3, "representation": "written", "role": "canonical", "text_assertion_id": ast_hw3["assertion_id"], "convention_assertion_id": None},
    ]
    if not omit_canonical_form:
        forms.append({"form_id": frm_1, "entry_id": ent_1, "representation": "written", "role": "canonical", "text_assertion_id": ast_hw1["assertion_id"], "convention_assertion_id": None})
    if include_optional_pending_ipa:
        forms.append({"form_id": frm_1_ipa, "entry_id": ent_1, "representation": "ipa", "role": "variant", "text_assertion_id": ast_ipa1["assertion_id"], "convention_assertion_id": None})

    senses = [
        {"sense_id": sen_1a, "entry_id": ent_1, "display_order": 1, "parent_sense_id": sen_1b if create_sense_cycle else None},
        {"sense_id": sen_1b, "entry_id": ent_1, "display_order": 2, "parent_sense_id": sen_1a},
        {"sense_id": sen_2, "entry_id": ent_2, "display_order": 1, "parent_sense_id": None},
        {"sense_id": sen_3, "entry_id": ent_3, "display_order": 1, "parent_sense_id": None},
    ]
    texts = [
        {"text_id": txt_1a, "owner_kind": "sense", "owner_id": sen_1a, "component": "definition", "language_id": "eng", "text_assertion_id": ast_def1a["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_1a_ex, "owner_kind": "sense", "owner_id": sen_1a, "component": "example", "language_id": "tam", "text_assertion_id": ast_ex1a["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_1b, "owner_kind": "sense", "owner_id": sen_1b, "component": "gloss", "language_id": "eng", "text_assertion_id": ast_def1b["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_1_unparsed, "owner_kind": "sense", "owner_id": sen_1a, "component": "unparsed", "language_id": "eng", "text_assertion_id": ast_unp["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_2, "owner_kind": "sense", "owner_id": sen_2, "component": "definition", "language_id": "eng", "text_assertion_id": ast_def2["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_3, "owner_kind": "sense", "owner_id": sen_3, "component": "definition", "language_id": "eng", "text_assertion_id": ast_def3["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None},
    ]
    if accepted_entry_text:
        texts.append({"text_id": txt_1_entry, "owner_kind": "entry", "owner_id": ent_1, "component": "citation", "language_id": "eng", "text_assertion_id": ast_et["assertion_id"], "paired_translation_id": None, "cited_source_locator_json": None})

    relations = [
        {"relation_id": rel_internal, "source_kind": "sense", "source_id": sen_1a, "target_kind": "entry", "target_id": ent_2, "relation_code_assertion_id": ast_rel_int["assertion_id"], "directionality": "undirected", "inverse_relation_id": None},
        {"relation_id": rel_cross, "source_kind": "sense", "source_id": sen_1a, "target_kind": "entry", "target_id": ent_3, "relation_code_assertion_id": ast_rel_cross["assertion_id"], "directionality": "directed", "inverse_relation_id": None},
    ]
    labels = [
        {"registry_id": "reg", "registry_version": "1", "code": "LK", "category": "region", "display_label_json": "Sri Lanka", "definition_json": "Sri Lanka", "evidence_reference": ast_scp_reg["assertion_id"], "parent_code": "LK-JAFFNA" if create_label_cycle else None},
        {"registry_id": "reg", "registry_version": "1", "code": "LK-JAFFNA", "category": "region", "display_label_json": "Jaffna", "definition_json": "Jaffna", "evidence_reference": ast_scp_reg["assertion_id"], "parent_code": "LK"},
        {"registry_id": "reg", "registry_version": "1", "code": "formal", "category": "register", "display_label_json": "Formal", "definition_json": "Formal", "evidence_reference": ast_scp_reg_f["assertion_id"], "parent_code": None},
    ]
    if unknown_vocab_region:
        labels.append({"registry_id": "reg", "registry_version": "1", "code": "LK-UNKNOWN-NEW", "category": "region", "display_label_json": "Unknown", "definition_json": "Not in vocabularies.toml", "evidence_reference": ast_scp_reg["assertion_id"], "parent_code": "LK"})

    dec_by_aid = {d["assertion_id"]: d["decision_id"] for d in decisions}
    scopes = [
        {"subject_kind": "entry", "subject_id": ent_1, "dimension": "region", "state": "attested", "label_code": "LK-UNKNOWN-NEW" if unknown_vocab_region else "LK-JAFFNA", "supporting_assertion_id": ast_scp_reg["assertion_id"], "decision_id": dec_by_aid[ast_scp_reg["assertion_id"]]},
        {"subject_kind": "entry", "subject_id": ent_1, "dimension": "register", "state": "attested", "label_code": "formal", "supporting_assertion_id": ast_scp_reg_f["assertion_id"], "decision_id": dec_by_aid[ast_scp_reg_f["assertion_id"]]},
        {"subject_kind": "entry", "subject_id": ent_2, "dimension": "region", "state": "unrestricted", "label_code": None, "supporting_assertion_id": ast_scp_reg_unr["assertion_id"], "decision_id": dec_by_aid[ast_scp_reg_unr["assertion_id"]]},
        {"subject_kind": "entry", "subject_id": ent_2, "dimension": "register", "state": "unknown", "label_code": None, "supporting_assertion_id": None, "decision_id": None},
    ]
    pack_members = [
        {"pack_id": "core", "entry_id": ent_1, "included_revision": ent_rev_1, "relation_inclusion_policy": relation_policy},
        {"pack_id": "core", "entry_id": ent_2, "included_revision": ent_rev_2, "relation_inclusion_policy": relation_policy},
        {"pack_id": "regional", "entry_id": ent_3, "included_revision": ent_rev_3, "relation_inclusion_policy": relation_policy},
    ]
    if cross_pack_revision_conflict:
        pack_members.append({"pack_id": "regional", "entry_id": ent_1, "included_revision": "0" * 64, "relation_inclusion_policy": relation_policy})

    write_rows(workspace / "snapshots.csv", "snapshots", snapshots)
    write_rows(workspace / "sources.csv", "sources", sources)
    write_rows(workspace / "identities.csv", "identities", identities)
    write_rows(workspace / "source_records.csv", "source_records", source_records)
    write_rows(workspace / "dispositions.csv", "dispositions", dispositions)
    write_rows(workspace / "record_targets.csv", "record_targets", record_targets)
    write_rows(workspace / "entries.csv", "entries", entries)
    write_rows(workspace / "forms.csv", "forms", forms)
    write_rows(workspace / "senses.csv", "senses", senses)
    write_rows(workspace / "texts.csv", "texts", texts)
    write_rows(workspace / "relations.csv", "relations", relations)
    write_rows(workspace / "assertions.csv", "assertions", assertions)
    write_rows(workspace / "evidence.csv", "evidence", evidence)
    write_rows(workspace / "decisions.csv", "decisions", decisions)
    write_rows(workspace / "findings.csv", "findings", [])
    write_rows(workspace / "labels.csv", "labels", labels)
    write_rows(workspace / "scopes.csv", "scopes", scopes)
    write_rows(workspace / "pack_members.csv", "pack_members", pack_members)
    return {
        "ent_1": ent_1, "ent_2": ent_2, "ent_3": ent_3,
        "rel_internal": rel_internal, "rel_cross": rel_cross,
        "ast_root1": ast_root1["assertion_id"], "src_id": src_id,
    }


def test_release_validate_passes_complete_synthetic_closure_and_cli_exit_0(tmp_path):
    from tools.lexicon import main as lexicon_main
    from tools.lexicon_pilot import release_guard

    ws = tmp_path / "ws_full"
    meta = _build_full_synthetic_workspace(ws)
    out = tmp_path / "release-pass.json"
    rc = lexicon_main([
        "validate", "--workspace", str(ws), "--mode", "release", "--pack", "core", "--output", str(out),
    ])
    assert rc == 0
    rep = json.loads(out.read_text(encoding="ascii"))
    assert rep == dict(release_guard(ws, pack="core"), command="validate")
    assert rep["l3_pack_eligible"] is True
    assert rep["l2_structural_accepted"] is False
    assert rep["runtime_verified"] is None
    assert rep["eligible_assertions"] > 0
    assert rep["findings"] == []
    assert rep["omitted_relation_count"] == 1
    assert rep["omitted_relations"][0]["relation_id"] == meta["rel_cross"]
    assert rep["omitted_relations"][0]["policy"] == "omit_cross_pack"


@pytest.mark.parametrize("kwargs", [
    {"omit_canonical_form": True},
    {"omit_pos": True},
    {"ineligible_pos": True},
    {"only_unparsed_sense": True},
    {"accepted_unparsed": True},
    {"accepted_entry_text": True},
    {"accepted_optional_only": True},
    {"stale_scope_assertion": True},
    {"create_sense_cycle": True},
    {"create_label_cycle": True},
    {"cross_pack_revision_conflict": True},
    {"relation_policy": None},
    {"bad_source_reuse": True},
    {"unknown_vocab_pos": True},
    {"unknown_vocab_region": True},
])
def test_release_validate_rejects_incomplete_or_tampered_closure(tmp_path, kwargs):
    from tools.lexicon_pilot import release_guard

    ws = tmp_path / "ws_bad"
    _build_full_synthetic_workspace(ws, **kwargs)
    rep = release_guard(ws, pack="core")
    assert rep["l3_pack_eligible"] is False
    assert rep["l2_structural_accepted"] is False
    assert rep["runtime_verified"] is None
    assert any(f["severity"] == "error" for f in rep["findings"])


def test_promote_deterministic_byte_idempotent_and_offline_canonical_validation(tmp_path):
    from tools.lexicon import main as lexicon_main
    from tools.lexicon_packs import build_lookup_entry_projection, promote
    from tools.lexicon_tables import read_rows
    from tools.lexicon_validate import check_curated_csv

    ws = tmp_path / "ws_promote"
    meta = _build_full_synthetic_workspace(ws)
    out1 = tmp_path / "can1"
    out2 = tmp_path / "can2"

    r1 = promote(ws, pack="core", output=out1)
    assert lexicon_main(["promote", "--workspace", str(ws), "--pack", "core", "--output", str(out2)]) == 0

    assert r1["l3_pack_eligible"] is True
    assert r1["l2_structural_accepted"] is False
    assert r1["runtime_verified"] is None
    assert not any(out1.glob("*.json"))
    for fname in ("packs.toml", "vocabularies.toml", "schema.toml", "ATTRIBUTION_AND_TERMS.md"):
        assert (out1 / fname).is_file()

    files1 = {p.relative_to(out1).as_posix(): p.read_bytes() for p in sorted(out1.rglob("*")) if p.is_file()}
    files2 = {p.relative_to(out2).as_posix(): p.read_bytes() for p in sorted(out2.rglob("*")) if p.is_file()}
    assert files1 == files2

    # Idempotent re-run onto same destination preserves exact bytes.
    promote(ws, pack="core", output=out1)
    assert {p.relative_to(out1).as_posix(): p.read_bytes() for p in sorted(out1.rglob("*")) if p.is_file()} == files1

    # Quarantined/pending/cross-pack items do not leak into canonical tables.
    can_entries = {r["entry_id"] for r in read_rows(out1 / "entries.csv")}
    assert can_entries == {meta["ent_1"], meta["ent_2"]}
    can_forms = list(read_rows(out1 / "forms.csv"))
    assert all(f["representation"] == "written" for f in can_forms)
    can_texts = list(read_rows(out1 / "texts.csv"))
    assert all(t["component"] != "unparsed" and t["owner_kind"] == "sense" for t in can_texts)
    can_rels = list(read_rows(out1 / "relations.csv"))
    assert [r["relation_id"] for r in can_rels] == [meta["rel_internal"]]
    can_decs = list(read_rows(out1 / "decisions.csv"))
    assert all(d["note_json"] == "" and d["predecessor_decision_id"] is None for d in can_decs)

    # Canonical check_curated_csv passes offline.
    assert check_curated_csv(workspace=ws, canonical=out1)["findings"] == []

    # LookupResponse-compatible projection helper honors undirected->symmetric, provenance, and actor_id rules.
    schema = json.loads((ROOT / "specs/021-lexicon-curation/contracts/lookup-response.schema.json").read_text(encoding="utf-8"))
    from jsonschema import Draft202012Validator
    projected_entries = [build_lookup_entry_projection(out1, eid) for eid in sorted(can_entries)]
    resp = {
        "schema_version": 1,
        "status": "matched",
        "canonical_query": "\u0b85\u0bae\u0bcd\u0bae\u0bbe",
        "packs": [r1["pack_info"]],
        "entries": projected_entries,
    }
    Draft202012Validator(schema).validate(resp)
    rels = [rel for e in projected_entries for s in e["senses"] for rel in s["relations"]]
    assert rels[0]["directionality"] == "symmetric"
    assert projected_entries[1]["provenance"][0]["acceptance"]["actor_id"] is None


def test_promote_rejects_overlap_ineligible_and_conflicting_canonical_edits(tmp_path):
    from tools.lexicon import main as lexicon_main
    from tools.lexicon_packs import promote

    ws_bad = tmp_path / "ws_bad"
    _build_full_synthetic_workspace(ws_bad, bad_source_reuse=True)
    out_bad = tmp_path / "can_bad"
    assert lexicon_main(["promote", "--workspace", str(ws_bad), "--pack", "core", "--output", str(out_bad)]) == 1
    assert not out_bad.exists()

    ws = tmp_path / "ws_ok"
    _build_full_synthetic_workspace(ws)
    out = tmp_path / "can_ok"
    promote(ws, pack="core", output=out)

    # Overlap with workspace or frozen source fails with code 2.
    with pytest.raises(LexiconError) as exc_ws:
        promote(ws, pack="core", output=ws / "sub")
    assert exc_ws.value.code == 2
    with pytest.raises(LexiconError) as exc_src:
        promote(ws, pack="core", output=SOURCE / "can")
    assert exc_src.value.code == 2

    # Simulated human edit in canonical output must not be overwritten.
    notes_path = out / "ATTRIBUTION_AND_TERMS.md"
    edited_text = notes_path.read_text(encoding="utf-8") + "\nManual canonical edit\n"
    notes_path.write_text(edited_text, encoding="utf-8")
    with pytest.raises(LexiconError, match="conflict"):
        promote(ws, pack="core", output=out)
    assert notes_path.read_text(encoding="utf-8") == edited_text


def test_canonical_check_curated_csv_catches_tamper_and_stale_manifest(tmp_path):
    from tools.lexicon_packs import promote
    from tools.lexicon_tables import read_rows, write_rows
    from tools.lexicon_validate import check_curated_csv

    ws = tmp_path / "ws_can_chk"
    _build_full_synthetic_workspace(ws)
    out = tmp_path / "can_chk"
    promote(ws, pack="core", output=out)
    assert check_curated_csv(workspace=ws, canonical=out)["findings"] == []

    # Tampering with a canonical CSV breaks packs.toml digest check.
    texts = list(read_rows(out / "texts.csv"))
    (out / "ATTRIBUTION_AND_TERMS.md").write_text("tampered\n", encoding="utf-8")
    assert check_curated_csv(workspace=ws, canonical=out)["findings"]

    # Missing packs.toml fails canonical check.
    (out / "packs.toml").unlink()
    assert check_curated_csv(workspace=ws, canonical=out)["findings"]
    assert len(texts) >= 1


def test_release_and_canonical_notice_closure_enforces_local_files_cc_legal_and_safe_paths(tmp_path):
    from tools.lexicon_packs import promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows
    from tools.lexicon_validate import check_curated_csv

    # 1. Missing referenced local notice file fails L3 release closure and promotion.
    ws_missing = tmp_path / "ws_notice_missing"
    _build_full_synthetic_workspace(ws_missing)
    srcs = list(read_rows(ws_missing / "sources.csv"))
    srcs[0]["attribution_reference_json"] = "notices/ATTRIBUTION_AND_LICENSE.md"
    write_rows(ws_missing / "sources.csv", "sources", srcs)
    rep_missing = validate_release(ws_missing, pack="core")
    assert rep_missing["l3_pack_eligible"] is False
    assert any(f["code"] == "MISSING_SOURCE_NOTICE_FILE" for f in rep_missing["findings"])

    # 2. Traversal / absolute Windows path / private JSON notice reference is rejected safely.
    for bad_ref in ("../escape.md", "C:\\Windows\\system32\\notice.md", "notices/fetch_manifest.json"):
        ws_bad_ref = tmp_path / ("ws_bad_" + hashlib.sha256(bad_ref.encode("utf-8")).hexdigest()[:8])
        _build_full_synthetic_workspace(ws_bad_ref)
        bsrcs = list(read_rows(ws_bad_ref / "sources.csv"))
        bsrcs[0]["attribution_reference_json"] = bad_ref
        write_rows(ws_bad_ref / "sources.csv", "sources", bsrcs)
        rep_bad = validate_release(ws_bad_ref, pack="core")
        assert rep_bad["l3_pack_eligible"] is False
        assert any(f["code"] == "UNSAFE_ATTRIBUTION_REFERENCE" for f in rep_bad["findings"])

    # 3. URL and bibliographic locators never trigger network or local file failure.
    for safe_ref in ("https://example.org/license/cc-by-sa-4.0", "Madras Tamil Lexicon Vol. I Prefatory Note"):
        ws_ref_ok = tmp_path / ("ws_ok_" + hashlib.sha256(safe_ref.encode("utf-8")).hexdigest()[:8])
        _build_full_synthetic_workspace(ws_ref_ok)
        ok_srcs = list(read_rows(ws_ref_ok / "sources.csv"))
        ok_srcs[0]["attribution_reference_json"] = safe_ref
        write_rows(ws_ref_ok / "sources.csv", "sources", ok_srcs)
        assert validate_release(ws_ref_ok, pack="core")["l3_pack_eligible"] is True

    # 4. Positive notice closure with local notice Markdown + CC-BY-SA-4.0 legal text:
    #    projects clean .md notices, strips private .json references, preserves source hash/URI,
    #    passes offline canonical check, and catches missing/tampered notice files.
    ws_full = tmp_path / "ws_notice_full"
    _build_full_synthetic_workspace(ws_full)
    fsrcs = list(read_rows(ws_full / "sources.csv"))
    fsrcs[0]["reuse_basis_json"] = "CC-BY-SA-4.0 synthetic test pack"
    fsrcs[0]["attribution_reference_json"] = "notices/ATTRIBUTION_AND_LICENSE.md"
    write_rows(ws_full / "sources.csv", "sources", fsrcs)
    notices = ws_full / "notices"
    notices.mkdir()
    legal_text = "Attribution-ShareAlike 4.0 International\nSynthetic CC-BY-SA-4.0 full legal code body.\n"
    (notices / "cc_by_sa_4_0_legalcode.txt").write_bytes(legal_text.encode("utf-8"))
    legal_sha = hashlib.sha256(legal_text.encode("utf-8")).hexdigest()
    (notices / "wikimedia_tou_api.json").write_text('{"private": true}\n', encoding="utf-8")
    (notices / "fetch_manifest.json").write_text('{"internal": true}\n', encoding="utf-8")
    (notices / "ATTRIBUTION_AND_LICENSE.md").write_text(
        "# Attribution and License Notices\n\n"
        "- Synthetic contributor attribution for \u0b85\u0bae\u0bcd\u0bae\u0bbe (CC BY-SA 4.0).\n\n"
        "## 3. Preserved Official Notice Files\n\n"
        "- `cc_by_sa_4_0_legalcode.txt`\n"
        "- `wikimedia_tou_api.json`\n"
        "- `fetch_manifest.json`\n",
        encoding="utf-8",
    )

    out = tmp_path / "can_notice_full"
    res = promote(ws_full, pack="core", output=out)
    assert res["l3_pack_eligible"] is True
    all_files = [p for p in out.rglob("*") if p.is_file()]
    assert {p.suffix for p in all_files} <= {".csv", ".toml", ".md"}
    assert (out / "notices/ATTRIBUTION_AND_LICENSE.md").is_file()
    assert (out / "notices/CC-BY-SA-4.0.md").is_file()
    proj_notice = (out / "notices/ATTRIBUTION_AND_LICENSE.md").read_text(encoding="utf-8")
    assert "fetch_manifest.json" not in proj_notice
    assert "wikimedia_tou_api.json" not in proj_notice
    assert "CC-BY-SA-4.0.md" in proj_notice
    cc_md = (out / "notices/CC-BY-SA-4.0.md").read_text(encoding="utf-8")
    assert legal_sha in cc_md
    assert "https://creativecommons.org/licenses/by-sa/4.0/legalcode" in cc_md
    assert "Synthetic CC-BY-SA-4.0 full legal code body." in cc_md
    assert check_curated_csv(workspace=ws_full, canonical=out)["findings"] == []

    # Tampering or removing canonical notice file fails offline validation.
    saved = (out / "notices/CC-BY-SA-4.0.md").read_text(encoding="utf-8")
    (out / "notices/CC-BY-SA-4.0.md").write_text(saved + "tamper\n", encoding="utf-8")
    assert validate_canonical_dir(out)
    (out / "notices/CC-BY-SA-4.0.md").unlink()
    assert validate_canonical_dir(out)
    (out / "notices/ATTRIBUTION_AND_LICENSE.md").unlink()
    assert any("notices/ATTRIBUTION_AND_LICENSE.md" in f for f in validate_canonical_dir(out))


def _resign_canonical_pack(cdir, pack: str = "core") -> None:
    """Recompute file digests, row counts, and manifest_sha256 in packs.toml after synthetic fixture edits."""
    import tomllib
    from tools.lexicon import json_text
    from tools.lexicon_packs import _render_packs_toml
    from tools.lexicon_tables import read_rows

    packs_path = cdir / "packs.toml"
    packs_data = tomllib.loads(packs_path.read_text(encoding="utf-8"))
    file_entries = []
    digest_basis = []
    for rel_path in sorted(p.relative_to(cdir).as_posix() for p in cdir.rglob("*") if p.is_file()):
        if rel_path == "packs.toml":
            continue
        raw = (cdir / rel_path).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        size = len(raw)
        rows = len(list(read_rows(cdir / rel_path))) if rel_path.endswith(".csv") else None
        file_entries.append({"path": rel_path, "sha256": sha, "bytes": size, "rows": rows})
        digest_basis.append({"path": rel_path, "sha256": sha, "bytes": size})

    manifest_sha = hashlib.sha256(json_text(digest_basis).encode("ascii")).hexdigest()
    dataset_version = f"0.1.0+{manifest_sha[:12]}"
    tables = {
        tbl: list(read_rows(cdir / f"{tbl}.csv", tbl))
        for tbl in ("entries", "senses", "forms", "texts", "relations", "assertions")
    }
    rendered = _render_packs_toml(
        pack=pack,
        dataset_version=dataset_version,
        vocabulary_version=packs_data["vocabulary_version"],
        manifest_sha256=manifest_sha,
        file_entries=file_entries,
        entries=tables["entries"],
        senses=tables["senses"],
        forms=tables["forms"],
        texts=tables["texts"],
        relations=tables["relations"],
        assertions=tables["assertions"],
        entry_revisions=packs_data["entry_revisions"],
        coverage=packs_data["coverage"],
        omitted_relations=packs_data.get("omitted_relations", []),
    )
    packs_path.write_text(rendered, encoding="ascii", newline="\n")


def _build_rich_promoted_pack(tmp_path):
    """Promote a deterministic synthetic pack containing POS, relation, annotation, region, and register."""
    from tools.lexicon_packs import promote, validate_canonical_dir
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_tables import read_rows, write_rows

    ws = tmp_path / "ws_rich"
    _build_full_synthetic_workspace(ws)
    out = tmp_path / "can_rich"
    res = promote(ws, pack="core", output=out)
    assert res["l3_pack_eligible"] is True
    assert validate_canonical_dir(out) == []
    return ws, out


def test_validate_canonical_dir_enforces_empty_finite_vocabularies(tmp_path):
    from tools.lexicon_packs import validate_canonical_dir

    _, base_out = _build_rich_promoted_pack(tmp_path)
    base_vocab = (base_out / "vocabularies.toml").read_text(encoding="utf-8")

    # Sanity check: rich promoted pack actually contains POS, relation, annotation, language, region, register.
    cases = [
        ("empty_language_ids", lambda txt: _replace_toml_list(txt, "language_ids", "[]"), "language_id"),
        ("empty_parts_of_speech", lambda txt: _replace_toml_list(txt, "parts_of_speech", "[]"), "POS"),
        ("empty_relation_codes", lambda txt: _replace_toml_list(txt, "relation_codes", "[]"), "relation"),
        ("empty_annotation_properties", lambda txt: _replace_toml_list(txt, "annotation_properties", "[]"), "annotation property"),
        ("empty_registers", lambda txt: _replace_toml_list(txt, "registers", "[]"), "register"),
        ("empty_regions", lambda txt: txt.split("[[regions]]")[0], "region"),
    ]

    import shutil
    for name, mutator, expected_fragment in cases:
        case_dir = tmp_path / f"case_{name}"
        shutil.copytree(base_out, case_dir)
        mutated_vocab = mutator(base_vocab)
        assert mutated_vocab != base_vocab, f"Mutator {name} did not change vocabularies.toml"
        (case_dir / "vocabularies.toml").write_text(mutated_vocab, encoding="ascii", newline="\n")
        _resign_canonical_pack(case_dir, pack="core")
        failures = validate_canonical_dir(case_dir)
        assert any(
            "vocabularies.toml:" in msg and expected_fragment in msg for msg in failures
        ), f"Expected empty vocab check failure for {name} ({expected_fragment}), got: {failures}"


def _replace_toml_list(text: str, key: str, new_val: str) -> str:
    out_lines = []
    for line in text.splitlines():
        if line.startswith(f"{key} = "):
            out_lines.append(f"{key} = {new_val}")
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + "\n"


def test_build_lookup_entry_projection_sense_inherits_and_preserves_overrides():
    from tools.lexicon_packs import build_lookup_entry_projection
    from tools.lexicon_review import claim_revision, evidence_hash

    src_id = "src:1"
    rec_id = "rec:1"
    ent_id = "ent:1"
    frm_id = "frm:1"
    s_inherit = "sen:inherit"
    s_unk = "sen:unk"
    s_na = "sen:na"

    assertions = []
    evidence = []
    decisions = []

    def add_claim(aid, skind, sid, prop, val):
        row = {
            "assertion_id": aid,
            "subject_kind": skind,
            "subject_id": sid,
            "property_code": prop,
            "value_state": "known",
            "value_json": val,
            "origin": "verbatim_source",
            "source_fidelity_state": "verified",
            "ambiguity_state": "unambiguous",
            "algorithm_reference": None,
            "convention_reference": None,
            "imported_status_json": None,
            "imported_confidence_json": None,
        }
        rev = claim_revision(row)
        row["claim_revision_sha256"] = rev
        assertions.append(row)
        eh = evidence_hash([row]) if False else hashlib.sha256(aid.encode("utf-8")).hexdigest()
        ev_item = {
            "assertion_id": aid,
            "source_id": src_id,
            "source_record_id": rec_id,
            "locator_json": "test:1",
            "evidence_role": "supports",
            "extraction_method": "synthetic-extractor",
            "extraction_version": "1",
            "extraction_sha256": hashlib.sha256(b"test").hexdigest(),
        }
        evidence.append(ev_item)
        eh = evidence_hash([ev_item])
        decisions.append({
            "decision_id": f"dec:{aid}",
            "assertion_id": aid,
            "claim_revision_sha256": rev,
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": "human:1",
            "method": None,
            "method_version": None,
            "rationale_code": "VERIFIED",
            "rationale_note_json": None,
            "evidence_hash_set_sha256": eh,
            "decision_date": "2026-11-15",
        })

    add_claim("a:pos", "entry", ent_id, "part_of_speech", "NOUN")
    add_claim("a:hw", "form", frm_id, "headword", "\u0b85\u0bae\u0bcd\u0bae\u0bbe")
    add_claim("a:t1", "text", "txt:1", "gloss", "mother")
    add_claim("a:t2", "text", "txt:2", "gloss", "madam")
    add_claim("a:t3", "text", "txt:3", "gloss", "goddess")
    add_claim("a:ereg", "entry", ent_id, "region_scope", "LK-JAFFNA")
    add_claim("a:eregister", "entry", ent_id, "register_scope", "literary")

    tables = {
        "entries": [{
            "entry_id": ent_id,
            "language_id": "tam",
            "variety_id": None,
            "canonical_form_id": frm_id,
            "pos_assertion_id": "a:pos",
            "structural_kind": "lexical_entry",
            "revision": "rev1",
        }],
        "forms": [{
            "form_id": frm_id,
            "entry_id": ent_id,
            "representation": "written",
            "role": "canonical",
            "text_assertion_id": "a:hw",
            "convention_assertion_id": None,
        }],
        "senses": [
            {"sense_id": s_inherit, "entry_id": ent_id, "display_order": 1, "parent_sense_id": None},
            {"sense_id": s_unk, "entry_id": ent_id, "display_order": 2, "parent_sense_id": None},
            {"sense_id": s_na, "entry_id": ent_id, "display_order": 3, "parent_sense_id": None},
        ],
        "texts": [
            {"text_id": "txt:1", "owner_kind": "sense", "owner_id": s_inherit, "component": "gloss", "language_id": "eng", "text_assertion_id": "a:t1", "paired_translation_id": None, "cited_source_locator_json": "test:1"},
            {"text_id": "txt:2", "owner_kind": "sense", "owner_id": s_unk, "component": "gloss", "language_id": "eng", "text_assertion_id": "a:t2", "paired_translation_id": None, "cited_source_locator_json": "test:1"},
            {"text_id": "txt:3", "owner_kind": "sense", "owner_id": s_na, "component": "gloss", "language_id": "eng", "text_assertion_id": "a:t3", "paired_translation_id": None, "cited_source_locator_json": "test:1"},
        ],
        "relations": [],
        "scopes": [
            {"subject_kind": "entry", "subject_id": ent_id, "dimension": "region", "state": "attested", "label_code": "LK-JAFFNA", "supporting_assertion_id": "a:ereg", "decision_id": "dec:a:ereg"},
            {"subject_kind": "entry", "subject_id": ent_id, "dimension": "register", "state": "attested", "label_code": "literary", "supporting_assertion_id": "a:eregister", "decision_id": "dec:a:eregister"},
            # s_inherit: NO region row, NO register row -> inherits both from entry.
            # s_unk: explicit unknown overrides for both region and register.
            {"subject_kind": "sense", "subject_id": s_unk, "dimension": "region", "state": "unknown", "label_code": None, "supporting_assertion_id": None, "decision_id": None},
            {"subject_kind": "sense", "subject_id": s_unk, "dimension": "register", "state": "unknown", "label_code": None, "supporting_assertion_id": None, "decision_id": None},
            # s_na: no region row (inherits LK-JAFFNA), explicit not_applicable override for register.
            {"subject_kind": "sense", "subject_id": s_na, "dimension": "register", "state": "not_applicable", "label_code": None, "supporting_assertion_id": None, "decision_id": None},
        ],
        "assertions": assertions,
        "evidence": evidence,
        "decisions": decisions,
    }

    proj = build_lookup_entry_projection({"tables": tables}, ent_id)
    assert proj["region"]["state"] == "attested"
    assert proj["region"]["codes"] == ["LK-JAFFNA"]
    assert proj["register"]["availability"] == "available"
    assert proj["register"]["value"] == "literary"

    by_sid = {s["sense_id"]: s for s in proj["senses"]}
    assert by_sid[s_inherit]["region"]["state"] == "attested"
    assert by_sid[s_inherit]["region"]["codes"] == ["LK-JAFFNA"]
    assert len(by_sid[s_inherit]["region"]["provenance"]) == 1
    assert by_sid[s_inherit]["register"]["availability"] == "available"
    assert by_sid[s_inherit]["register"]["value"] == "literary"
    assert len(by_sid[s_inherit]["register"]["provenance"]) == 1

    assert by_sid[s_unk]["region"] == {"state": "unknown", "codes": [], "provenance": []}
    assert by_sid[s_unk]["register"] == {"availability": "unknown", "value": None, "convention": None, "provenance": []}

    assert by_sid[s_na]["region"]["state"] == "attested"
    assert by_sid[s_na]["region"]["codes"] == ["LK-JAFFNA"]
    assert by_sid[s_na]["register"] == {"availability": "not_applicable", "value": None, "convention": None, "provenance": []}


def test_compute_coverage_counts_absent_entry_region_rows_as_unknown(tmp_path):
    from tools.lexicon_packs import _compute_coverage, promote
    from tools.lexicon_tables import read_rows, write_rows
    import tomllib

    entries = [{"entry_id": "e1", "language_id": "tam"}, {"entry_id": "e2", "language_id": "tam"}, {"entry_id": "e3", "language_id": "tam"}]
    scopes = [
        {"subject_kind": "entry", "subject_id": "e1", "dimension": "region", "state": "attested", "label_code": "LK-JAFFNA"},
        {"subject_kind": "entry", "subject_id": "e2", "dimension": "region", "state": "unknown", "label_code": None},
        # e3 has only a register row and NO region row -> must still count as unknown_region_entries.
        {"subject_kind": "entry", "subject_id": "e3", "dimension": "register", "state": "attested", "label_code": "literary"},
    ]
    cov = _compute_coverage(entries, scopes)
    assert cov["unknown_region_entries"] == 2

    # End-to-end check via promote(): removing an entry's region scope row causes it to count as unknown_region_entries.
    ws = tmp_path / "ws_cov"
    _build_full_synthetic_workspace(ws)
    orig_scopes = list(read_rows(ws / "scopes.csv"))
    stripped_scopes = [sc for sc in orig_scopes if not (sc["subject_kind"] == "entry" and sc["dimension"] == "region" and sc["state"] == "unrestricted")]
    assert len(stripped_scopes) < len(orig_scopes)
    write_rows(ws / "scopes.csv", "scopes", stripped_scopes)

    out = tmp_path / "can_cov"
    promote(ws, pack="core", output=out)
    packs_toml = tomllib.loads((out / "packs.toml").read_text(encoding="utf-8"))
    # Synthetic core pack has 2 entries: 1 attested LK-JAFFNA and 1 with absent region row.
    assert packs_toml["coverage"]["unknown_region_entries"] == 1


def test_scope_cardinality_conflicting_states_and_relation_typed_endpoints(tmp_path):
    from tools.lexicon_packs import validate_canonical_dir, validate_release
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_tables import read_rows, write_rows
    import shutil

    # 1. Multiple attested register rows on same subject violate single-value cardinality.
    ws_reg, base_out = _build_rich_promoted_pack(tmp_path / "reg_multi")
    labels = list(read_rows(ws_reg / "labels.csv"))
    existing_reg_label = next(l for l in labels if l["category"] == "register")
    labels.append({
        "registry_id": existing_reg_label["registry_id"],
        "registry_version": existing_reg_label["registry_version"],
        "code": "colloquial",
        "category": "register",
        "display_label_json": "Colloquial",
        "definition_json": "Colloquial Tamil register",
        "evidence_reference": existing_reg_label["evidence_reference"],
        "parent_code": None,
    })
    write_rows(ws_reg / "labels.csv", "labels", labels)
    scopes = list(read_rows(ws_reg / "scopes.csv"))
    ev = list(read_rows(ws_reg / "evidence.csv"))
    decs = list(read_rows(ws_reg / "decisions.csv"))
    asrts = list(read_rows(ws_reg / "assertions.csv"))
    existing_reg_scope = next(sc for sc in scopes if sc["dimension"] == "register" and sc["state"] == "attested")
    aid2 = "asrt:extra:reg2"
    did2 = "dec:extra:reg2"
    a2 = {
        "assertion_id": aid2,
        "subject_kind": existing_reg_scope["subject_kind"],
        "subject_id": existing_reg_scope["subject_id"],
        "property_code": "register_scope",
        "value_state": "known",
        "value_json": "colloquial",
        "origin": "verbatim_source",
        "source_fidelity_state": "verified",
        "ambiguity_state": "unambiguous",
        "algorithm_reference": None,
        "convention_reference": None,
        "imported_status_json": None,
        "imported_confidence_json": None,
    }
    a2["claim_revision_sha256"] = claim_revision(a2)
    asrts.append(a2)
    ev_tpl = dict(ev[0])
    dec_tpl = dict(decs[0])
    ev2 = dict(ev_tpl)
    ev2.update({
        "assertion_id": aid2,
        "locator_json": "synthetic:extra2",
    })
    ev.append(ev2)
    eh2 = evidence_hash([ev2])
    dec2 = dict(dec_tpl)
    dec2.update({
        "decision_id": did2,
        "assertion_id": aid2,
        "assertion_revision_sha256": a2["claim_revision_sha256"],
        "outcome": "accepted_human",
        "actor_type": "human",
        "actor_id": "human.reviewer:1",
        "note_json": "Second register",
        "evidence_bundle_sha256": eh2,
    })
    decs.append(dec2)
    scopes.append({
        "subject_kind": existing_reg_scope["subject_kind"],
        "subject_id": existing_reg_scope["subject_id"],
        "dimension": "register",
        "state": "attested",
        "label_code": "colloquial",
        "supporting_assertion_id": aid2,
        "decision_id": did2,
    })
    write_rows(ws_reg / "assertions.csv", "assertions", asrts)
    write_rows(ws_reg / "evidence.csv", "evidence", ev)
    write_rows(ws_reg / "decisions.csv", "decisions", decs)
    write_rows(ws_reg / "scopes.csv", "scopes", scopes)
    (ws_reg / "vocabularies.toml").write_text(
        _replace_toml_list((ws_reg / "vocabularies.toml").read_text(encoding="utf-8"), "registers", '["formal", "colloquial"]'),
        encoding="ascii",
        newline="\n",
    )
    rep_reg = validate_release(ws_reg, pack="core")
    assert rep_reg["l3_pack_eligible"] is False
    assert any(f["code"] == "CONFLICTING_SCOPE_STATES" for f in rep_reg["findings"])

    can_multi_reg = tmp_path / "can_multi_reg"
    shutil.copytree(base_out, can_multi_reg)
    write_rows(can_multi_reg / "labels.csv", "labels", list(read_rows(ws_reg / "labels.csv")))
    c_asrts = list(read_rows(can_multi_reg / "assertions.csv")) + [a2]
    c_ev = list(read_rows(can_multi_reg / "evidence.csv")) + [ev[-1]]
    c_decs = list(read_rows(can_multi_reg / "decisions.csv")) + [decs[-1]]
    c_scopes = list(read_rows(can_multi_reg / "scopes.csv")) + [scopes[-1]]
    write_rows(can_multi_reg / "assertions.csv", "assertions", c_asrts)
    write_rows(can_multi_reg / "evidence.csv", "evidence", c_ev)
    write_rows(can_multi_reg / "decisions.csv", "decisions", c_decs)
    write_rows(can_multi_reg / "scopes.csv", "scopes", c_scopes)
    (can_multi_reg / "vocabularies.toml").write_text(
        _replace_toml_list((can_multi_reg / "vocabularies.toml").read_text(encoding="utf-8"), "registers", '["formal", "colloquial"]'),
        encoding="ascii",
        newline="\n",
    )
    _resign_canonical_pack(can_multi_reg, pack="core")
    assert validate_canonical_dir(can_multi_reg)

    # 2. Scope subject_kind/subject_id mismatch fails workspace release checks.
    ws_skind = tmp_path / "ws_skind"
    _build_full_synthetic_workspace(ws_skind)
    core_eids = {r["entry_id"] for r in read_rows(ws_skind / "pack_members.csv") if r["pack_id"] == "core"}
    ws_senses = list(read_rows(ws_skind / "senses.csv"))
    core_sid = next(s["sense_id"] for s in ws_senses if s["entry_id"] in core_eids)
    ws_scopes = list(read_rows(ws_skind / "scopes.csv"))
    target_sc = next(sc for sc in ws_scopes if sc["subject_kind"] == "entry" and sc["state"] == "unknown")
    target_sc["subject_id"] = core_sid
    write_rows(ws_skind / "scopes.csv", "scopes", ws_scopes)
    rep_skind = validate_release(ws_skind, pack="core")
    assert rep_skind["l3_pack_eligible"] is False
    assert any(f["code"] == "SCOPE_SUBJECT_KIND_MISMATCH" for f in rep_skind["findings"])

    # 3. Relation typed endpoint kind mismatch fails workspace release, and wrong relation assertion property fails canonical check.
    ws_rel = tmp_path / "ws_rel"
    _build_full_synthetic_workspace(ws_rel)
    rel_rows = list(read_rows(ws_rel / "relations.csv"))
    pm_entry_ids = {r["entry_id"] for r in read_rows(ws_rel / "pack_members.csv") if r["pack_id"] == "core"}
    ws_sense_ids = {r["sense_id"] for r in read_rows(ws_rel / "senses.csv") if r["entry_id"] in pm_entry_ids}
    same_pack_rel = next(r for r in rel_rows if r["source_id"] in pm_entry_ids or r["source_id"] in ws_sense_ids)
    same_pack_rel["source_kind"] = "sense" if same_pack_rel["source_kind"] == "entry" else "entry"
    write_rows(ws_rel / "relations.csv", "relations", rel_rows)
    rep_rel = validate_release(ws_rel, pack="core")
    assert rep_rel["l3_pack_eligible"] is False

    can_bad_rel_prop = tmp_path / "can_bad_rel_prop"
    shutil.copytree(base_out, can_bad_rel_prop)
    r_rows = list(read_rows(can_bad_rel_prop / "relations.csv"))
    a_rows = list(read_rows(can_bad_rel_prop / "assertions.csv"))
    e_rows = list(read_rows(can_bad_rel_prop / "evidence.csv"))
    d_rows = list(read_rows(can_bad_rel_prop / "decisions.csv"))
    target_rel_aid = r_rows[0]["relation_code_assertion_id"]
    for a in a_rows:
        if a["assertion_id"] == target_rel_aid:
            a["property_code"] = "part_of_speech"
            a["value_json"] = "NOUN"
            new_rev = claim_revision(a)
            a["claim_revision_sha256"] = new_rev
            rel_evs = [ev_row for ev_row in e_rows if ev_row["assertion_id"] == target_rel_aid]
            new_eh = evidence_hash(rel_evs)
            for d_row in d_rows:
                if d_row["assertion_id"] == target_rel_aid:
                    d_row["assertion_revision_sha256"] = new_rev
                    d_row["evidence_bundle_sha256"] = new_eh
    write_rows(can_bad_rel_prop / "assertions.csv", "assertions", a_rows)
    write_rows(can_bad_rel_prop / "evidence.csv", "evidence", e_rows)
    write_rows(can_bad_rel_prop / "decisions.csv", "decisions", d_rows)
    _resign_canonical_pack(can_bad_rel_prop, pack="core")
    assert validate_canonical_dir(can_bad_rel_prop)


def test_notice_safety_and_canonical_source_permissions(tmp_path):
    from tools.lexicon_packs import promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows
    import shutil

    # 1. Empty notice markdown or private workspace path leak fails release and canonical validation.
    for tag, bad_md in [
        ("empty", "   \n\t\n"),
        ("curation_path", "# Notice\n\nInternal path: data/curation/wiktionary/snapshot.csv\n"),
        ("jsonl_leak", "# Notice\n\nLoaded from dump_records.jsonl\n"),
    ]:
        ws = tmp_path / f"ws_{tag}"
        _build_full_synthetic_workspace(ws)
        srcs = list(read_rows(ws / "sources.csv"))
        srcs[0]["attribution_reference_json"] = "notices/ATTRIBUTION_AND_LICENSE.md"
        write_rows(ws / "sources.csv", "sources", srcs)
        (ws / "notices").mkdir()
        (ws / "notices" / "ATTRIBUTION_AND_LICENSE.md").write_text(bad_md, encoding="utf-8")
        rep = validate_release(ws, pack="core")
        assert rep["l3_pack_eligible"] is False, f"Expected notice safety failure for {tag}"

    # 2. Canonical directory with empty/leaking notice file or unpermitted source fails validate_canonical_dir.
    _, base_out = _build_rich_promoted_pack(tmp_path / "notice_can")
    can_empty_attr = tmp_path / "can_empty_attr"
    shutil.copytree(base_out, can_empty_attr)
    (can_empty_attr / "ATTRIBUTION_AND_TERMS.md").write_text("   \n", encoding="utf-8")
    _resign_canonical_pack(can_empty_attr, pack="core")
    empty_attr_failures = validate_canonical_dir(can_empty_attr)
    assert any("ATTRIBUTION_AND_TERMS.md" in f and "empty" in f.lower() for f in empty_attr_failures), empty_attr_failures

    can_bad_src = tmp_path / "can_bad_src"
    shutil.copytree(base_out, can_bad_src)
    c_srcs = list(read_rows(can_bad_src / "sources.csv"))
    c_srcs[0]["reuse_state"] = "restricted"
    write_rows(can_bad_src / "sources.csv", "sources", c_srcs)
    _resign_canonical_pack(can_bad_src, pack="core")
    bad_src_failures = validate_canonical_dir(can_bad_src)
    assert any("sources.csv" in f and ("reuse_state" in f or "permitted" in f) for f in bad_src_failures), bad_src_failures

    can_non_md_notice = tmp_path / "can_non_md"
    shutil.copytree(base_out, can_non_md_notice)
    (can_non_md_notice / "notices").mkdir(exist_ok=True)
    (can_non_md_notice / "notices" / "raw.txt").write_text("Non-markdown notice\n", encoding="utf-8")
    _resign_canonical_pack(can_non_md_notice, pack="core")
    non_md_failures = validate_canonical_dir(can_non_md_notice)
    assert any("raw.txt" in f and ".md" in f for f in non_md_failures), non_md_failures


def test_cc_by_sa_legal_notice_required_regardless_of_attribution_reference(tmp_path: Path) -> None:
    """CC-BY-SA-4.0 sources must always ship notices/CC-BY-SA-4.0.md regardless of attribution_reference_json."""
    import shutil

    from tools.lexicon_packs import CC_BY_SA_URL, promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    valid_cc_md = (
        "# CC BY-SA 4.0\n\n"
        "Attribution-ShareAlike 4.0 International\n\n"
        f"Canonical legal code: {CC_BY_SA_URL}\n"
    )
    variants = [
        ("url_ref", "https://creativecommons.org/licenses/by-sa/4.0/", "Synthetic CC-BY-SA source"),
        ("bib_ref", "Wiktionary contributors, Tamil Wiktionary", "Synthetic CC-BY-SA source"),
        ("no_ref", None, "Synthetic CC-BY-SA source"),
    ]
    for name, attr_ref, attr_text in variants:
        ws = tmp_path / f"ws_{name}"
        _build_full_synthetic_workspace(ws)
        src_rows = list(read_rows(ws / "sources.csv", "sources"))
        for row in src_rows:
            row["reuse_basis_json"] = "CC-BY-SA-4.0"
            row["attribution_reference_json"] = attr_ref
            row["attribution_text_json"] = attr_text
        write_rows(ws / "sources.csv", "sources", src_rows)

        # Missing notices/CC-BY-SA-4.0.md must fail L3 release validation.
        missing_report = validate_release(ws, pack="core")
        assert missing_report["l3_pack_eligible"] is False, (name, missing_report)
        assert any(f["code"] == "MISSING_CC_LEGAL_CODE" for f in missing_report["findings"]), (
            name,
            missing_report["findings"],
        )

        # Incomplete notices/CC-BY-SA-4.0.md (missing canonical URI) must also fail.
        notices_dir = ws / "notices"
        notices_dir.mkdir(exist_ok=True)
        cc_notice = notices_dir / "CC-BY-SA-4.0.md"
        cc_notice.write_text("# Incomplete notice\nAttribution-ShareAlike 4.0 International\n", encoding="utf-8")
        incomplete_report = validate_release(ws, pack="core")
        assert incomplete_report["l3_pack_eligible"] is False, (name, incomplete_report)
        assert any(f["code"] == "MISSING_CC_LEGAL_CODE" for f in incomplete_report["findings"]), (
            name,
            incomplete_report["findings"],
        )

        # Valid notices/CC-BY-SA-4.0.md succeeds through promote + validate_canonical_dir.
        cc_notice.write_text(valid_cc_md, encoding="utf-8")
        ok_report = validate_release(ws, pack="core")
        assert ok_report["l3_pack_eligible"] is True, (name, ok_report["findings"])
        out_dir = tmp_path / f"out_{name}"
        promote(ws, pack="core", output=out_dir)
        assert validate_canonical_dir(out_dir) == []

        # Tampering the canonical pack to drop notices/CC-BY-SA-4.0.md must fail validate_canonical_dir.
        dropped = tmp_path / f"dropped_{name}"
        shutil.copytree(out_dir, dropped)
        (dropped / "notices" / "CC-BY-SA-4.0.md").unlink()
        _resign_canonical_pack(dropped, pack="core")
        dropped_failures = validate_canonical_dir(dropped)
        assert any("CC-BY-SA-4.0.md" in f for f in dropped_failures), (name, dropped_failures)

        # Incomplete canonical CC-BY-SA-4.0.md (missing canonical URI) must also fail validate_canonical_dir.
        incomplete_can = tmp_path / f"incomplete_can_{name}"
        shutil.copytree(out_dir, incomplete_can)
        (incomplete_can / "notices" / "CC-BY-SA-4.0.md").write_text(
            "# Incomplete\nAttribution-ShareAlike 4.0 International\n",
            encoding="utf-8",
        )
        _resign_canonical_pack(incomplete_can, pack="core")
        incomplete_can_failures = validate_canonical_dir(incomplete_can)
        assert any("CC-BY-SA-4.0.md" in f for f in incomplete_can_failures), (name, incomplete_can_failures)


def test_attribution_reference_only_source_remains_valid(tmp_path: Path) -> None:
    """Sources with attribution_text_json=None and non-empty attribution_reference_json stay valid."""
    from tools.lexicon_packs import CC_BY_SA_URL, promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    # Case 1: CC0 source with URL-only attribution_reference_json and attribution_text_json=None.
    ws_url = tmp_path / "ws_cc0_url_only"
    _build_full_synthetic_workspace(ws_url)
    src_rows = list(read_rows(ws_url / "sources.csv", "sources"))
    for row in src_rows:
        row["reuse_basis_json"] = "CC0-1.0 synthetic test fixture"
        row["attribution_text_json"] = None
        row["attribution_reference_json"] = "https://example.org/synthetic-cc0"
    write_rows(ws_url / "sources.csv", "sources", src_rows)

    rep_url = validate_release(ws_url, pack="core")
    assert rep_url["l3_pack_eligible"] is True, rep_url["findings"]
    out_url = tmp_path / "out_cc0_url_only"
    promote(ws_url, pack="core", output=out_url)
    assert validate_canonical_dir(out_url) == []

    # Case 2: CC-BY-SA-4.0 source with local .md attribution_reference_json only + CC legal code.
    ws_local = tmp_path / "ws_cc_local_only"
    _build_full_synthetic_workspace(ws_local)
    src_local = list(read_rows(ws_local / "sources.csv", "sources"))
    for row in src_local:
        row["reuse_basis_json"] = "CC-BY-SA-4.0"
        row["attribution_text_json"] = None
        row["attribution_reference_json"] = "notices/source-attribution.md"
    write_rows(ws_local / "sources.csv", "sources", src_local)
    notices = ws_local / "notices"
    notices.mkdir(exist_ok=True)
    (notices / "source-attribution.md").write_text("# Source Attribution\nSynthetic Contributors\n", encoding="utf-8")
    (notices / "CC-BY-SA-4.0.md").write_text(
        "# CC BY-SA 4.0\n\nAttribution-ShareAlike 4.0 International\n\n"
        f"Canonical legal code: {CC_BY_SA_URL}\n",
        encoding="utf-8",
    )

    rep_local = validate_release(ws_local, pack="core")
    assert rep_local["l3_pack_eligible"] is True, rep_local["findings"]
    out_local = tmp_path / "out_cc_local_only"
    promote(ws_local, pack="core", output=out_local)
    assert validate_canonical_dir(out_local) == []


def _append_accepted_workspace_claim(
    ws: Path,
    assertion_id: str,
    subject_kind: str,
    subject_id: str,
    property_code: str,
    value_json: object,
) -> tuple[str, str]:
    """Append an accepted_human assertion backed by the workspace's first verified source."""
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_tables import read_rows, write_rows

    sources = list(read_rows(ws / "sources.csv", "sources"))
    assertions = list(read_rows(ws / "assertions.csv", "assertions"))
    evidence = list(read_rows(ws / "evidence.csv", "evidence"))
    decisions = list(read_rows(ws / "decisions.csv", "decisions"))

    src_id = sources[0]["source_id"]
    dec_id = f"dec_{assertion_id}"
    claim = {
        "assertion_id": assertion_id,
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "property_code": property_code,
        "value_state": "known",
        "value_json": value_json,
        "origin": "editorial",
        "source_fidelity_state": "verified",
        "ambiguity_state": "unambiguous",
        "algorithm_reference": None,
        "convention_reference": None,
        "imported_status_json": None,
        "imported_confidence_json": None,
    }
    claim["claim_revision_sha256"] = claim_revision(claim)
    ev_row = {
        "assertion_id": assertion_id,
        "source_id": src_id,
        "source_record_id": None,
        "locator_json": f"synthetic:{assertion_id}",
        "evidence_role": "supports",
        "extraction_version": "1",
        "extraction_sha256": hashlib.sha256(assertion_id.encode("ascii")).hexdigest(),
    }
    dec_row = {
        "decision_id": dec_id,
        "assertion_id": assertion_id,
        "assertion_revision_sha256": claim["claim_revision_sha256"],
        "evidence_bundle_sha256": evidence_hash([ev_row]),
        "outcome": "accepted_human",
        "actor_type": "human",
        "actor_id": "human.reviewer",
        "method_version": None,
        "decision_date": "2026-11-15",
        "note_json": "Synthetic review decision.",
        "predecessor_decision_id": None,
    }
    assertions.append(claim)
    evidence.append(ev_row)
    decisions.append(dec_row)
    write_rows(ws / "assertions.csv", "assertions", assertions)
    write_rows(ws / "evidence.csv", "evidence", evidence)
    write_rows(ws / "decisions.csv", "decisions", decisions)
    return assertion_id, dec_id


def test_validate_relations_propagates_cycles_fk_and_global_id_collisions(tmp_path: Path) -> None:
    """Both validate_release and validate_canonical_dir must propagate validate_relations error findings."""
    import shutil

    from tools.lexicon_packs import promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    ws_base = tmp_path / "ws_base"
    _build_full_synthetic_workspace(ws_base)
    can_base = tmp_path / "can_base"
    promote(ws_base, pack="core", output=can_base)
    assert validate_canonical_dir(can_base) == []

    # 1. Cyclic label parent hierarchy.
    ws_cycle = tmp_path / "ws_cycle"
    shutil.copytree(ws_base, ws_cycle)
    lbls = list(read_rows(ws_cycle / "labels.csv", "labels"))
    lbl_ev = lbls[0]["evidence_reference"]
    lbls.extend([
        {
            "registry_id": "test.cyc",
            "registry_version": "1",
            "code": "cyc_a",
            "category": "domain",
            "display_label_json": "Cycle A",
            "definition_json": "Cycle A",
            "evidence_reference": lbl_ev,
            "parent_code": "cyc_b",
        },
        {
            "registry_id": "test.cyc",
            "registry_version": "1",
            "code": "cyc_b",
            "category": "domain",
            "display_label_json": "Cycle B",
            "definition_json": "Cycle B",
            "evidence_reference": lbl_ev,
            "parent_code": "cyc_a",
        },
    ])
    write_rows(ws_cycle / "labels.csv", "labels", lbls)
    rep_cycle = validate_release(ws_cycle, pack="core")
    assert rep_cycle["l3_pack_eligible"] is False
    assert any("LABEL_PARENT_CYCLE" in f["code"] or "LABEL_HIERARCHY_CYCLE" in f["code"] for f in rep_cycle["findings"]), rep_cycle["findings"]

    can_cycle = tmp_path / "can_cycle"
    shutil.copytree(can_base, can_cycle)
    can_lbls = list(read_rows(can_cycle / "labels.csv", "labels"))
    can_ev = can_lbls[0]["evidence_reference"]
    can_lbls.extend([
        {
            "registry_id": "test.cyc",
            "registry_version": "1",
            "code": "cyc_a",
            "category": "domain",
            "display_label_json": "Cycle A",
            "definition_json": "Cycle A",
            "evidence_reference": can_ev,
            "parent_code": "cyc_b",
        },
        {
            "registry_id": "test.cyc",
            "registry_version": "1",
            "code": "cyc_b",
            "category": "domain",
            "display_label_json": "Cycle B",
            "definition_json": "Cycle B",
            "evidence_reference": can_ev,
            "parent_code": "cyc_a",
        },
    ])
    write_rows(can_cycle / "labels.csv", "labels", can_lbls)
    _resign_canonical_pack(can_cycle, pack="core")
    cyc_failures = validate_canonical_dir(can_cycle)
    assert any("cyclic" in f.lower() or "cycle" in f.lower() for f in cyc_failures), cyc_failures

    # 2. Dangling FK on an unused canonical/workspace form text_assertion_id or global ID collision.
    ws_fk = tmp_path / "ws_fk"
    shutil.copytree(ws_base, ws_fk)
    f_rows = list(read_rows(ws_fk / "forms.csv", "forms"))
    f_rows[0]["text_assertion_id"] = "ast_nonexistent_fk"
    write_rows(ws_fk / "forms.csv", "forms", f_rows)
    rep_fk = validate_release(ws_fk, pack="core")
    assert rep_fk["l3_pack_eligible"] is False
    assert any("DANGLING_REFERENCE" in f["code"] for f in rep_fk["findings"]), rep_fk["findings"]

    # 3. Global ID collision across tables (text_id reusing existing form_id).
    ws_gid = tmp_path / "ws_gid"
    shutil.copytree(ws_base, ws_gid)
    colliding_fid = read_rows(ws_gid / "forms.csv", "forms").__next__()["form_id"]
    t_rows = list(read_rows(ws_gid / "texts.csv", "texts"))
    t_rows[0]["text_id"] = colliding_fid
    write_rows(ws_gid / "texts.csv", "texts", t_rows)
    rep_gid = validate_release(ws_gid, pack="core")
    assert rep_gid["l3_pack_eligible"] is False
    assert any("DUPLICATE_ID" in f["code"] for f in rep_gid["findings"]), rep_gid["findings"]

    can_gid = tmp_path / "can_gid"
    shutil.copytree(can_base, can_gid)
    can_fid = next(read_rows(can_gid / "forms.csv", "forms"))["form_id"]
    can_t = list(read_rows(can_gid / "texts.csv", "texts"))
    can_t[0]["text_id"] = can_fid
    write_rows(can_gid / "texts.csv", "texts", can_t)
    _resign_canonical_pack(can_gid, pack="core")
    gid_failures = validate_canonical_dir(can_gid)
    assert any("collision" in f.lower() or "duplicate" in f.lower() for f in gid_failures), gid_failures


def test_closed_vocabularies_period_parent_code_and_entry_variety_id(tmp_path: Path) -> None:
    """Omitted/empty vocab keys reject undeclared attested codes; period aligns to temporals; region parent_code & variety_id validate."""
    import shutil

    from tools.lexicon_packs import promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    # 1. Workspace with NO domains/temporals/varieties in vocabularies.toml rejects attested domain & period scopes.
    for dim, code, prop in (
        ("domain", "botany", "domain_scope"),
        ("period", "classical", "period_scope"),
    ):
        ws = tmp_path / f"ws_omitted_{dim}"
        _build_full_synthetic_workspace(ws)
        core_eid = next(r["entry_id"] for r in read_rows(ws / "pack_members.csv", "pack_members") if r["pack_id"] == "core")
        aid, did = _append_accepted_workspace_claim(ws, f"ast_dim_{dim}", "entry", core_eid, prop, code)
        lbls = list(read_rows(ws / "labels.csv", "labels"))
        lbls.append({
            "registry_id": "test.reg",
            "registry_version": "1",
            "code": code,
            "category": dim,
            "display_label_json": code,
            "definition_json": f"{dim} {code}",
            "evidence_reference": aid,
            "parent_code": None,
        })
        write_rows(ws / "labels.csv", "labels", lbls)
        sc_rows = list(read_rows(ws / "scopes.csv", "scopes"))
        sc_rows.append({
            "subject_kind": "entry",
            "subject_id": core_eid,
            "dimension": dim,
            "state": "attested",
            "label_code": code,
            "supporting_assertion_id": aid,
            "decision_id": did,
        })
        write_rows(ws / "scopes.csv", "scopes", sc_rows)

        rep_omit = validate_release(ws, pack="core")
        assert rep_omit["l3_pack_eligible"] is False, (dim, rep_omit["findings"])
        assert any(f["code"] == "UNKNOWN_VOCABULARY_SCOPE_LABEL" for f in rep_omit["findings"]), rep_omit["findings"]

    # 2. Promoting a workspace WITHOUT vocabularies.toml populates temporals from period scope & varieties from entry.variety_id,
    #    and validate_canonical_dir enforces domains, temporals (period), variety_id, and region parent_code agreement.
    ws_auto = tmp_path / "ws_auto"
    _build_full_synthetic_workspace(ws_auto)
    (ws_auto / "vocabularies.toml").unlink()
    e_rows = list(read_rows(ws_auto / "entries.csv", "entries"))
    core_eid = next(r["entry_id"] for r in read_rows(ws_auto / "pack_members.csv", "pack_members") if r["pack_id"] == "core")
    for e in e_rows:
        if e["entry_id"] == core_eid:
            e["variety_id"] = "jaffna_tamil"
    write_rows(ws_auto / "entries.csv", "entries", e_rows)

    p_aid, p_did = _append_accepted_workspace_claim(ws_auto, "ast_period_auto", "entry", core_eid, "period_scope", "classical")
    d_aid, d_did = _append_accepted_workspace_claim(ws_auto, "ast_domain_auto", "entry", core_eid, "domain_scope", "botany")
    lbls = list(read_rows(ws_auto / "labels.csv", "labels"))
    lbls.extend([
        {
            "registry_id": "test.reg",
            "registry_version": "1",
            "code": "classical",
            "category": "period",
            "display_label_json": "Classical",
            "definition_json": "Classical period",
            "evidence_reference": p_aid,
            "parent_code": None,
        },
        {
            "registry_id": "test.reg",
            "registry_version": "1",
            "code": "botany",
            "category": "domain",
            "display_label_json": "Botany",
            "definition_json": "Botany domain",
            "evidence_reference": d_aid,
            "parent_code": None,
        },
    ])
    write_rows(ws_auto / "labels.csv", "labels", lbls)
    sc_rows = list(read_rows(ws_auto / "scopes.csv", "scopes"))
    sc_rows.extend([
        {
            "subject_kind": "entry",
            "subject_id": core_eid,
            "dimension": "period",
            "state": "attested",
            "label_code": "classical",
            "supporting_assertion_id": p_aid,
            "decision_id": p_did,
        },
        {
            "subject_kind": "entry",
            "subject_id": core_eid,
            "dimension": "domain",
            "state": "attested",
            "label_code": "botany",
            "supporting_assertion_id": d_aid,
            "decision_id": d_did,
        },
    ])
    write_rows(ws_auto / "scopes.csv", "scopes", sc_rows)

    out_auto = tmp_path / "out_auto"
    promote(ws_auto, pack="core", output=out_auto)
    vocab_text = (out_auto / "vocabularies.toml").read_text(encoding="utf-8")
    assert 'temporals = ["classical"]' in vocab_text, vocab_text
    assert 'domains = ["botany"]' in vocab_text, vocab_text
    assert 'varieties = ["jaffna_tamil"]' in vocab_text, vocab_text
    assert validate_canonical_dir(out_auto) == []

    # Removing temporals from canonical vocabularies.toml must fail validate_canonical_dir.
    can_no_temp = tmp_path / "can_no_temp"
    shutil.copytree(out_auto, can_no_temp)
    (can_no_temp / "vocabularies.toml").write_text(
        vocab_text.replace('temporals = ["classical"]\n', ""),
        encoding="utf-8",
    )
    _resign_canonical_pack(can_no_temp, pack="core")
    temp_failures = validate_canonical_dir(can_no_temp)
    assert any("period" in f and "classical" in f for f in temp_failures), temp_failures

    # Removing varieties from canonical vocabularies.toml must reject entry variety_id.
    can_no_var = tmp_path / "can_no_var"
    shutil.copytree(out_auto, can_no_var)
    (can_no_var / "vocabularies.toml").write_text(
        vocab_text.replace('varieties = ["jaffna_tamil"]\n', ""),
        encoding="utf-8",
    )
    _resign_canonical_pack(can_no_var, pack="core")
    var_failures = validate_canonical_dir(can_no_var)
    assert any("variety_id" in f and "jaffna_tamil" in f for f in var_failures), var_failures

    # Workspace entry.variety_id also rejects undeclared variety_id when vocabularies.toml is present.
    ws_bad_var = tmp_path / "ws_bad_var"
    _build_full_synthetic_workspace(ws_bad_var)
    bad_entries = list(read_rows(ws_bad_var / "entries.csv", "entries"))
    bad_core_eid = next(r["entry_id"] for r in read_rows(ws_bad_var / "pack_members.csv", "pack_members") if r["pack_id"] == "core")
    for e in bad_entries:
        if e["entry_id"] == bad_core_eid:
            e["variety_id"] = "undeclared_var"
    write_rows(ws_bad_var / "entries.csv", "entries", bad_entries)
    rep_bad_var = validate_release(ws_bad_var, pack="core")
    assert rep_bad_var["l3_pack_eligible"] is False
    assert any(f["code"] == "UNKNOWN_VOCABULARY_VARIETY" for f in rep_bad_var["findings"]), rep_bad_var["findings"]

    # Region parent_code mismatch between labels.csv and vocabularies.toml fails validate_canonical_dir too.
    can_bad_parent = tmp_path / "can_bad_parent"
    shutil.copytree(out_auto, can_bad_parent)
    (can_bad_parent / "vocabularies.toml").write_text(
        vocab_text.replace('parent_code = "LK"\n', ""),
        encoding="utf-8",
    )
    _resign_canonical_pack(can_bad_parent, pack="core")
    parent_failures = validate_canonical_dir(can_bad_parent)
    assert any("parent_code" in f for f in parent_failures), parent_failures


def test_structural_scope_properties_and_temporal_alias_not_exposed_as_annotations(tmp_path: Path) -> None:
    """All structural scope properties + temporal_scope alias are accepted and never emitted in annotations or annotation_properties."""
    from tools.lexicon_packs import build_lookup_entry_projection, promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    ws = tmp_path / "ws_struct_scopes"
    _build_full_synthetic_workspace(ws)
    (ws / "vocabularies.toml").unlink()
    core_eid = next(r["entry_id"] for r in read_rows(ws / "pack_members.csv", "pack_members") if r["pack_id"] == "core")
    core_sid = next(s["sense_id"] for s in read_rows(ws / "senses.csv", "senses") if s["entry_id"] == core_eid)

    aid_per, did_per = _append_accepted_workspace_claim(ws, "ast_tmp_alias", "entry", core_eid, "temporal_scope", "sangam")
    aid_soc, did_soc = _append_accepted_workspace_claim(ws, "ast_soc_scope", "entry", core_eid, "social_usage_scope", "honorific")
    aid_grm, did_grm = _append_accepted_workspace_claim(ws, "ast_grm_scope", "entry", core_eid, "grammar_system_scope", "nannul")
    aid_att, did_att = _append_accepted_workspace_claim(ws, "ast_att_scope", "sense", core_sid, "scope_attestation", "spoken_jaffna")

    lbls = list(read_rows(ws / "labels.csv", "labels"))
    reg_jaffna = next(l for l in lbls if l["category"] == "region" and l["code"] == "LK-JAFFNA")
    lbls.extend([
        {"registry_id": "test.reg", "registry_version": "1", "code": "sangam", "category": "period", "display_label_json": "Sangam", "definition_json": "Sangam", "evidence_reference": aid_per, "parent_code": None},
        {"registry_id": "test.reg", "registry_version": "1", "code": "honorific", "category": "social_usage", "display_label_json": "Honorific", "definition_json": "Honorific", "evidence_reference": aid_soc, "parent_code": None},
        {"registry_id": "test.reg", "registry_version": "1", "code": "nannul", "category": "grammar_system", "display_label_json": "Nannul", "definition_json": "Nannul", "evidence_reference": aid_grm, "parent_code": None},
        {"registry_id": reg_jaffna["registry_id"], "registry_version": reg_jaffna["registry_version"], "code": "spoken_jaffna", "category": "region", "display_label_json": "Spoken Jaffna", "definition_json": "Spoken Jaffna", "evidence_reference": aid_att, "parent_code": "LK-JAFFNA"},
    ])
    write_rows(ws / "labels.csv", "labels", lbls)

    sc_rows = list(read_rows(ws / "scopes.csv", "scopes"))
    sc_rows.extend([
        {"subject_kind": "entry", "subject_id": core_eid, "dimension": "period", "state": "attested", "label_code": "sangam", "supporting_assertion_id": aid_per, "decision_id": did_per},
        {"subject_kind": "entry", "subject_id": core_eid, "dimension": "social_usage", "state": "attested", "label_code": "honorific", "supporting_assertion_id": aid_soc, "decision_id": did_soc},
        {"subject_kind": "entry", "subject_id": core_eid, "dimension": "grammar_system", "state": "attested", "label_code": "nannul", "supporting_assertion_id": aid_grm, "decision_id": did_grm},
        {"subject_kind": "sense", "subject_id": core_sid, "dimension": "region", "state": "attested", "label_code": "spoken_jaffna", "supporting_assertion_id": aid_att, "decision_id": did_att},
    ])
    write_rows(ws / "scopes.csv", "scopes", sc_rows)

    rep = validate_release(ws, pack="core")
    assert rep["l3_pack_eligible"] is True, rep["findings"]
    out = tmp_path / "out_struct_scopes"
    promote(ws, pack="core", output=out)
    assert validate_canonical_dir(out) == []

    vocab_txt = (out / "vocabularies.toml").read_text(encoding="utf-8")
    for structural_prop in ("temporal_scope", "period_scope", "social_usage_scope", "grammar_system_scope", "scope_attestation"):
        assert structural_prop not in vocab_txt, vocab_txt

    proj = build_lookup_entry_projection(out, core_eid)
    entry_ann_props = {a["property"] for a in proj["annotations"]}
    sense_ann_props = {a["property"] for s in proj["senses"] for a in s["annotations"]}
    assert entry_ann_props <= {"root_word"}
    assert "temporal_scope" not in entry_ann_props
    assert "social_usage_scope" not in entry_ann_props
    assert "grammar_system_scope" not in entry_ann_props
    assert "scope_attestation" not in sense_ann_props


def test_entry_source_relations_rejected_at_release_canonical_and_projection(tmp_path: Path) -> None:
    """Eligible entry-source relations are rejected cleanly at release/canonical/projection, while unapproved editorial entry relations remain allowed."""
    import shutil

    from tools.lexicon_packs import build_lookup_entry_projection, promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    # 1. Pending (raw/editorial) entry-sourced relation in workspace must not block core release.
    ws_pending = tmp_path / "ws_pending_entry_rel"
    _build_full_synthetic_workspace(ws_pending)
    pm_eids = sorted(r["entry_id"] for r in read_rows(ws_pending / "pack_members.csv", "pack_members") if r["pack_id"] == "core")
    src_id = next(read_rows(ws_pending / "sources.csv", "sources"))["source_id"]
    from tools.lexicon_review import claim_revision

    pending_claim = {
        "assertion_id": "ast_pending_entry_rel",
        "subject_kind": "relation",
        "subject_id": "rel_pending_entry",
        "property_code": "relation_code",
        "value_state": "known",
        "value_json": "related_to",
        "origin": "editorial",
        "source_fidelity_state": "unknown",
        "ambiguity_state": "unknown",
        "algorithm_reference": None,
        "convention_reference": None,
        "imported_status_json": None,
        "imported_confidence_json": None,
    }
    pending_claim["claim_revision_sha256"] = claim_revision(pending_claim)
    a_rows = list(read_rows(ws_pending / "assertions.csv", "assertions"))
    a_rows.append(pending_claim)
    write_rows(ws_pending / "assertions.csv", "assertions", a_rows)
    ev_rows = list(read_rows(ws_pending / "evidence.csv", "evidence"))
    ev_rows.append({
        "assertion_id": "ast_pending_entry_rel",
        "source_id": src_id,
        "source_record_id": None,
        "locator_json": "synthetic:pending_rel",
        "evidence_role": "transcribes",
        "extraction_version": "1",
        "extraction_sha256": hashlib.sha256(b"pending").hexdigest(),
    })
    write_rows(ws_pending / "evidence.csv", "evidence", ev_rows)
    id_rows = list(read_rows(ws_pending / "identities.csv", "identities"))
    id_rows.append({"entity_id": "rel_pending_entry", "kind": "relation", "allocation_key": "pending_entry_rel", "lifecycle": "active", "identity_decision_id": None})
    write_rows(ws_pending / "identities.csv", "identities", id_rows)
    rel_rows = list(read_rows(ws_pending / "relations.csv", "relations"))
    rel_rows.append({
        "relation_id": "rel_pending_entry",
        "source_kind": "entry",
        "source_id": pm_eids[0],
        "target_kind": "entry",
        "target_id": pm_eids[1],
        "relation_code_assertion_id": "ast_pending_entry_rel",
        "directionality": "directed",
        "inverse_relation_id": None,
    })
    write_rows(ws_pending / "relations.csv", "relations", rel_rows)
    rep_pending = validate_release(ws_pending, pack="core")
    assert rep_pending["l3_pack_eligible"] is True, rep_pending["findings"]

    # 2. Eligible (accepted) entry-sourced relation fails release gate clearly.
    ws_acc = tmp_path / "ws_acc_entry_rel"
    shutil.copytree(ws_pending, ws_acc)
    from tools.lexicon_review import evidence_hash

    acc_ev_rows = list(read_rows(ws_acc / "evidence.csv", "evidence"))
    for er in acc_ev_rows:
        if er["assertion_id"] == "ast_pending_entry_rel":
            er["evidence_role"] = "supports"
    write_rows(ws_acc / "evidence.csv", "evidence", acc_ev_rows)
    acc_ev = [e for e in acc_ev_rows if e["assertion_id"] == "ast_pending_entry_rel"]
    decs = list(read_rows(ws_acc / "decisions.csv", "decisions"))
    decs.append({
        "decision_id": "dec_acc_entry_rel",
        "assertion_id": "ast_pending_entry_rel",
        "assertion_revision_sha256": pending_claim["claim_revision_sha256"],
        "evidence_bundle_sha256": evidence_hash(acc_ev),
        "outcome": "accepted_human",
        "actor_type": "human",
        "actor_id": "human.reviewer",
        "method_version": None,
        "decision_date": "2026-11-15",
        "note_json": "Accept relation.",
        "predecessor_decision_id": None,
    })
    write_rows(ws_acc / "decisions.csv", "decisions", decs)
    rep_acc = validate_release(ws_acc, pack="core")
    assert rep_acc["l3_pack_eligible"] is False
    assert any(f["code"] == "UNSUPPORTED_RELATION_SOURCE_KIND" for f in rep_acc["findings"]), rep_acc["findings"]

    # 3. Canonical pack with source_kind="entry" fails validate_canonical_dir AND fails build_lookup_entry_projection (no silent drop).
    ws_clean = tmp_path / "ws_clean_rel"
    _build_full_synthetic_workspace(ws_clean)
    can_rel = tmp_path / "can_entry_rel"
    promote(ws_clean, pack="core", output=can_rel)
    c_rels = list(read_rows(can_rel / "relations.csv", "relations"))
    c_eids = sorted(r["entry_id"] for r in read_rows(can_rel / "entries.csv", "entries"))
    c_rels[0]["source_kind"] = "entry"
    c_rels[0]["source_id"] = c_eids[0]
    write_rows(can_rel / "relations.csv", "relations", c_rels)
    _resign_canonical_pack(can_rel, pack="core")
    can_failures = validate_canonical_dir(can_rel)
    assert any("source_kind" in f and "sense" in f for f in can_failures), can_failures

    with pytest.raises(LexiconError, match="sense-anchored"):
        build_lookup_entry_projection(can_rel, c_eids[0])


def test_register_not_applicable_scope_csv_roundtrip_promote_and_projection(tmp_path: Path) -> None:
    """Explicit register not_applicable sense override survives CSV roundtrip -> promote -> canonical -> projection."""
    import shutil

    from tools.lexicon_packs import build_lookup_entry_projection, promote, validate_canonical_dir, validate_release
    from tools.lexicon_tables import read_rows, write_rows

    ws = tmp_path / "ws_reg_na"
    _build_full_synthetic_workspace(ws)
    e_rows = list(read_rows(ws / "entries.csv", "entries"))
    s_rows = list(read_rows(ws / "senses.csv", "senses"))
    # ent_1 in _build_full_synthetic_workspace already has multiple senses (sen_1a, sen_1b) and entry register=formal.
    target_eid = next(s["entry_id"] for s in s_rows if sum(1 for x in s_rows if x["entry_id"] == s["entry_id"]) >= 2)
    target_sid = sorted(s["sense_id"] for s in s_rows if s["entry_id"] == target_eid)[1]

    sc_rows = list(read_rows(ws / "scopes.csv", "scopes"))
    sc_rows = [
        r for r in sc_rows
        if not (r["subject_kind"] == "sense" and r["subject_id"] == target_sid and r["dimension"] == "register")
    ]
    sc_rows.append({
        "subject_kind": "sense",
        "subject_id": target_sid,
        "dimension": "register",
        "state": "not_applicable",
        "label_code": None,
        "supporting_assertion_id": None,
        "decision_id": None,
    })
    write_rows(ws / "scopes.csv", "scopes", sc_rows)

    rep = validate_release(ws, pack="core")
    assert rep["l3_pack_eligible"] is True, rep["findings"]
    out = tmp_path / "out_reg_na"
    promote(ws, pack="core", output=out)
    assert validate_canonical_dir(out) == []

    proj = build_lookup_entry_projection(out, target_eid)
    by_sid = {s["sense_id"]: s for s in proj["senses"]}
    assert by_sid[target_sid]["register"] == {
        "availability": "not_applicable",
        "value": None,
        "convention": None,
        "provenance": [],
    }


def test_cross_pack_omission_precedes_published_shape_and_vocabulary_checks(tmp_path: Path) -> None:
    """External relations targeting pack entries omit cleanly before published shape/vocab checks; internal unsupported still rejects."""
    import shutil
    import tomllib

    from tools.lexicon_packs import promote, validate_canonical_dir, validate_release
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_tables import read_rows, write_rows

    def _add_external_relation(
        ws: Path,
        rel_id: str,
        *,
        source_kind: str,
        source_id: str,
        target_kind: str,
        target_id: str,
        relation_code: str,
        bad_claim_prop: bool = False,
    ) -> None:
        src_id = next(read_rows(ws / "sources.csv", "sources"))["source_id"]
        aid = f"ast_{rel_id}"
        did = f"dec_{rel_id}"
        claim = {
            "assertion_id": aid,
            "subject_kind": "relation",
            "subject_id": rel_id,
            "property_code": "part_of_speech" if bad_claim_prop else "relation_code",
            "value_state": "known",
            "value_json": relation_code,
            "origin": "editorial",
            "source_fidelity_state": "verified",
            "ambiguity_state": "unambiguous",
            "algorithm_reference": None,
            "convention_reference": None,
            "imported_status_json": None,
            "imported_confidence_json": None,
        }
        claim["claim_revision_sha256"] = claim_revision(claim)
        ev_row = {
            "assertion_id": aid,
            "source_id": src_id,
            "source_record_id": None,
            "locator_json": f"synthetic:{rel_id}",
            "evidence_role": "supports",
            "extraction_version": "1",
            "extraction_sha256": hashlib.sha256(rel_id.encode("ascii")).hexdigest(),
        }
        dec_row = {
            "decision_id": did,
            "assertion_id": aid,
            "assertion_revision_sha256": claim["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash([ev_row]),
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": "human.reviewer",
            "method_version": None,
            "decision_date": "2026-11-15",
            "note_json": "Accept cross-pack test relation.",
            "predecessor_decision_id": None,
        }
        id_rows = list(read_rows(ws / "identities.csv", "identities"))
        id_rows.append({"entity_id": rel_id, "kind": "relation", "allocation_key": f"alloc_{rel_id}", "lifecycle": "active", "identity_decision_id": None})
        write_rows(ws / "identities.csv", "identities", id_rows)
        a_rows = list(read_rows(ws / "assertions.csv", "assertions")) + [claim]
        write_rows(ws / "assertions.csv", "assertions", a_rows)
        e_rows = list(read_rows(ws / "evidence.csv", "evidence")) + [ev_row]
        write_rows(ws / "evidence.csv", "evidence", e_rows)
        d_rows = list(read_rows(ws / "decisions.csv", "decisions")) + [dec_row]
        write_rows(ws / "decisions.csv", "decisions", d_rows)
        r_rows = list(read_rows(ws / "relations.csv", "relations"))
        r_rows.append({
            "relation_id": rel_id,
            "source_kind": source_kind,
            "source_id": source_id,
            "target_kind": target_kind,
            "target_id": target_id,
            "relation_code_assertion_id": aid,
            "directionality": "directed",
            "inverse_relation_id": None,
        })
        write_rows(ws / "relations.csv", "relations", r_rows)

    # 1. External entry-sourced + foreign relation_code targeting core entry under omit_cross_pack must omit cleanly.
    ws_omit = tmp_path / "ws_ext_omit"
    meta_omit = _build_full_synthetic_workspace(ws_omit, relation_policy="omit_cross_pack")
    _add_external_relation(
        ws_omit,
        "rel_ext_entry_src",
        source_kind="entry",
        source_id=meta_omit["ent_3"],
        target_kind="entry",
        target_id=meta_omit["ent_1"],
        relation_code="foreign_regional_rel",
    )
    rep_omit = validate_release(ws_omit, pack="core")
    assert rep_omit["l3_pack_eligible"] is True, rep_omit["findings"]
    assert rep_omit["findings"] == []
    omitted_ids = {r["relation_id"]: r for r in rep_omit["omitted_relations"]}
    assert {meta_omit["rel_cross"], "rel_ext_entry_src"} <= set(omitted_ids)
    assert omitted_ids["rel_ext_entry_src"]["policy"] == "omit_cross_pack"

    can_omit = tmp_path / "can_ext_omit"
    promo_omit = promote(ws_omit, pack="core", output=can_omit)
    assert promo_omit["l3_pack_eligible"] is True
    assert validate_canonical_dir(can_omit) == []
    can_rel_ids = {r["relation_id"] for r in read_rows(can_omit / "relations.csv", "relations")}
    assert can_rel_ids == {meta_omit["rel_internal"]}
    packs_meta = tomllib.loads((can_omit / "packs.toml").read_text(encoding="utf-8"))
    assert any(r["relation_id"] == "rel_ext_entry_src" for r in packs_meta.get("omitted_relations", []))
    vocab_meta = tomllib.loads((can_omit / "vocabularies.toml").read_text(encoding="utf-8"))
    assert "foreign_regional_rel" not in vocab_meta["relation_codes"]

    # 2. Same external relation under evidence_only_external also omits cleanly.
    ws_ev_only = tmp_path / "ws_ext_ev_only"
    meta_ev = _build_full_synthetic_workspace(ws_ev_only, relation_policy="evidence_only_external")
    _add_external_relation(
        ws_ev_only,
        "rel_ext_ev_only",
        source_kind="entry",
        source_id=meta_ev["ent_3"],
        target_kind="entry",
        target_id=meta_ev["ent_1"],
        relation_code="foreign_regional_rel",
    )
    rep_ev = validate_release(ws_ev_only, pack="core")
    assert rep_ev["l3_pack_eligible"] is True, rep_ev["findings"]
    assert any(r["relation_id"] == "rel_ext_ev_only" and r["policy"] == "evidence_only_external" for r in rep_ev["omitted_relations"])

    # 3. Non-omitting policy (require_same_pack) still rejects cross-pack relation.
    ws_req_same = tmp_path / "ws_ext_req_same"
    meta_req = _build_full_synthetic_workspace(ws_req_same, relation_policy="require_same_pack")
    _add_external_relation(
        ws_req_same,
        "rel_ext_req_same",
        source_kind="entry",
        source_id=meta_req["ent_3"],
        target_kind="entry",
        target_id=meta_req["ent_1"],
        relation_code="foreign_regional_rel",
    )
    rep_req = validate_release(ws_req_same, pack="core")
    assert rep_req["l3_pack_eligible"] is False
    assert any(f["code"] == "CROSS_PACK_RELATION_UNRESOLVED" for f in rep_req["findings"])

    # 4. Basic editorial integrity still rejects broken relation_code assertion even on cross-pack relation.
    ws_bad_editorial = tmp_path / "ws_ext_bad_editorial"
    meta_ed = _build_full_synthetic_workspace(ws_bad_editorial, relation_policy="omit_cross_pack")
    _add_external_relation(
        ws_bad_editorial,
        "rel_ext_bad_prop",
        source_kind="entry",
        source_id=meta_ed["ent_3"],
        target_kind="entry",
        target_id=meta_ed["ent_1"],
        relation_code="NOUN",
        bad_claim_prop=True,
    )
    rep_ed = validate_release(ws_bad_editorial, pack="core")
    assert rep_ed["l3_pack_eligible"] is False
    assert any(f["code"] == "INVALID_RELATION_ASSERTION" for f in rep_ed["findings"])

    # 5. Legitimate internal unsupported entry-source and foreign relation_code still reject.
    ws_int_entry = tmp_path / "ws_int_entry"
    meta_ie = _build_full_synthetic_workspace(ws_int_entry, relation_policy="omit_cross_pack")
    _add_external_relation(
        ws_int_entry,
        "rel_int_entry_src",
        source_kind="entry",
        source_id=meta_ie["ent_1"],
        target_kind="entry",
        target_id=meta_ie["ent_2"],
        relation_code="related_to",
    )
    rep_ie = validate_release(ws_int_entry, pack="core")
    assert rep_ie["l3_pack_eligible"] is False
    assert any(f["code"] == "UNSUPPORTED_RELATION_SOURCE_KIND" and f["subject_id"] == "rel_int_entry_src" for f in rep_ie["findings"])

    ws_int_vocab = tmp_path / "ws_int_vocab"
    meta_iv = _build_full_synthetic_workspace(ws_int_vocab, relation_policy="omit_cross_pack")
    sen_1a = next(s["sense_id"] for s in read_rows(ws_int_vocab / "senses.csv", "senses") if s["entry_id"] == meta_iv["ent_1"])
    _add_external_relation(
        ws_int_vocab,
        "rel_int_foreign_code",
        source_kind="sense",
        source_id=sen_1a,
        target_kind="entry",
        target_id=meta_iv["ent_2"],
        relation_code="foreign_internal_rel",
    )
    rep_iv = validate_release(ws_int_vocab, pack="core")
    assert rep_iv["l3_pack_eligible"] is False
    assert any(f["code"] == "UNKNOWN_VOCABULARY_RELATION" and f["subject_id"] == "rel_int_foreign_code" for f in rep_iv["findings"])




