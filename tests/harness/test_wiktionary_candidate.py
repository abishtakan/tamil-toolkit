"""Focused integrity, pin, exclusion, replay, and negative tamper tests for wiktionary-candidate."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tools.lexicon import ROOT, digest
from tools.lexicon_packs import load_canonical_pack, promote, validate_canonical_dir
from tools.lexicon_review import eligibility, validate_history
from tools.lexicon_tables import read_rows, write_rows
from tools.lexicon_wiktionary_candidate import (
    CANDIDATE_DIR,
    DEFAULT_APPROVAL_RECEIPT,
    HOMOGRAPH_DIR,
    REVIEWED_DIR,
    build_candidate_workspace,
    build_reviewed_workspace,
    check_idempotent_replay,
    check_reviewed_idempotent_replay,
    verify_candidate_workspace,
    verify_reviewed_workspace,
)


@pytest.mark.xdist_group("real_lexicon_packs")
def test_candidate_workspace_verified_and_pending_only(
    real_candidate_verification: dict,
) -> None:
    """Candidate workspace validates against all 21 schemas with zero accepted or runtime claims."""
    result = real_candidate_verification
    assert result["ok"] is True
    assert result["original_12_verified"] is True
    assert result["original_12_count"] == 12
    assert result["snapshot_count"] == 4
    assert result["entry_count"] == 4
    assert result["sense_count"] == 16
    assert result["form_count"] == 4
    assert result["ipa_form_count"] == 0
    assert result["accepted_decisions"] == 0
    assert result["decision_outcomes"] == {"needs_review": 24, "pending": 4, "rejected": 2}
    assert result["validation"]["findings"] == []

    guard = result["release_guard"]
    assert guard["eligible_assertions"] == 0
    assert guard["l2_structural_accepted"] is False
    assert guard["l3_pack_eligible"] is False
    assert guard["runtime_verified"] is None
    assert guard["findings"][0]["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED"


def test_candidate_excludes_unpinned_templates_ipa_and_synthetic_legacy() -> None:
    """No template-generated IPA, usage examples, etymologies, DEDR, or synthetic proto-forms enter tables."""
    forbidden_markers = ("{{ta-IPA", "{{ux", "{{ety", "DEDR", "*PDr", "*a", "Argh")
    for table in ("assertions", "forms", "texts", "entries", "labels", "scopes"):
        for row in read_rows(CANDIDATE_DIR / f"{table}.csv", table):
            blob = json.dumps(row, ensure_ascii=True, sort_keys=True)
            for marker in forbidden_markers:
                if marker == "*a":
                    assert "*a\\u1e6f" not in blob and "*a\u1e6f" not in blob
                else:
                    assert marker not in blob, f"Forbidden marker {marker!r} leaked into {table}.csv"

    exclusions = json.loads((CANDIDATE_DIR / "provenance/exclusions.json").read_text(encoding="utf-8"))
    assert len(exclusions["entries"]) == 4
    provenance = json.loads((CANDIDATE_DIR / "provenance/extraction_provenance.json").read_text(encoding="utf-8"))
    assert provenance["entry_count"] == 4
    assert provenance["sense_count"] == 16
    assert [e["revid"] for e in provenance["entries"]] == [85842017, 89903937, 88382210, 61485513]


def test_candidate_idempotent_replay() -> None:
    """Offline projection from checked-in snapshots is byte-for-byte deterministic."""
    replay = check_idempotent_replay(CANDIDATE_DIR)
    assert replay["ok"] is True
    assert replay["checked_files"] == 25
    assert replay["diffs"] == []


def test_existing_main_workspace_remains_separate_and_untouched() -> None:
    """Separate namespace avoids mixing candidate IDs into data/curation/tamil-lexicon/."""
    pilot_toml = (ROOT / "data/curation/tamil-lexicon/pilot-selection.toml").read_text(encoding="utf-8")
    cand_toml = (CANDIDATE_DIR / "dataset.toml").read_text(encoding="utf-8")
    assert 'dataset_id = "wiktionary-en-tamil-candidate"' in cand_toml
    cand_ids = {r["entry_id"] for r in read_rows(CANDIDATE_DIR / "entries.csv", "entries")}
    for eid in cand_ids:
        assert eid not in pilot_toml


def test_negative_snapshot_tamper_rejected(tmp_path: Path) -> None:
    """Tampering with a checked-in snapshot byte fails SHA-256 verification."""
    work = tmp_path / "wiktionary-candidate"
    shutil.copytree(CANDIDATE_DIR / "snapshots", work / "snapshots")
    wt_file = work / "snapshots/enwikt_rev_61485513_ceppam.wikitext"
    wt_file.write_text(wt_file.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        build_candidate_workspace(work)


def test_negative_unpinned_revid_rejected(tmp_path: Path) -> None:
    """Replacing a pinned revid with an unpinned revid fails immediately."""
    work = tmp_path / "wiktionary-candidate"
    shutil.copytree(CANDIDATE_DIR / "snapshots", work / "snapshots")
    manifest_path = work / "snapshots/snapshots_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entries"][0]["revid"] = 999999999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Unpinned revid rejected"):
        build_candidate_workspace(work)


def test_negative_template_ipa_in_sense_rejected(tmp_path: Path) -> None:
    """Injecting {{ta-IPA}} inside a sense line cannot sneak past extraction validation."""
    work = tmp_path / "wiktionary-candidate"
    shutil.copytree(CANDIDATE_DIR / "snapshots", work / "snapshots")
    manifest_path = work / "snapshots/snapshots_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = manifest["entries"][1]

    api_path = work / "snapshots" / target["api_response_file"]
    wt_path = work / "snapshots" / target["wikitext_file"]
    bad_wt = wt_path.read_text(encoding="utf-8").replace("# [[that]] [[moment]]", "# {{ta-IPA}}")
    wt_bytes = bad_wt.encode("utf-8")
    wt_path.write_bytes(wt_bytes)

    api_obj = json.loads(api_path.read_text(encoding="utf-8"))
    api_obj["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"] = bad_wt
    api_bytes = json.dumps(api_obj).encode("utf-8")
    api_path.write_bytes(api_bytes)

    import hashlib

    from tools.lexicon_wiktionary_candidate import PINNED_ALLOWLIST

    target["wikitext_sha256"] = hashlib.sha256(wt_bytes).hexdigest()
    target["api_response_sha256"] = hashlib.sha256(api_bytes).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Even if manifest were updated without touching allowlist, hash pin rejects first;
    # temporarily bypassing the pin sha1/sha256 still rejects {{ta-IPA}} inside sense parsing.
    orig_pin = dict(PINNED_ALLOWLIST[target["revid"]])
    try:
        PINNED_ALLOWLIST[target["revid"]]["wikitext_sha256"] = target["wikitext_sha256"]
        PINNED_ALLOWLIST[target["revid"]]["wikitext_sha1"] = hashlib.sha1(wt_bytes).hexdigest()
        api_obj["query"]["pages"][0]["revisions"][0]["sha1"] = PINNED_ALLOWLIST[target["revid"]]["wikitext_sha1"]
        api_bytes = json.dumps(api_obj).encode("utf-8")
        api_path.write_bytes(api_bytes)
        target["api_response_sha256"] = hashlib.sha256(api_bytes).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="Forbidden unpinned template"):
            build_candidate_workspace(work)
    finally:
        PINNED_ALLOWLIST[target["revid"]].update(orig_pin)


@pytest.mark.xdist_group("real_lexicon_packs")
def test_negative_auto_accept_forbidden_for_changed_or_restricted_claims(
    real_candidate_verification: dict,
) -> None:
    """Even if a decision claimed accepted_auto_source, eligibility rejects changed/restricted/open-finding claims."""
    assertions = list(read_rows(CANDIDATE_DIR / "assertions.csv", "assertions"))
    evidence = list(read_rows(CANDIDATE_DIR / "evidence.csv", "evidence"))
    sources = list(read_rows(CANDIDATE_DIR / "sources.csv", "sources"))
    decisions = list(read_rows(CANDIDATE_DIR / "decisions.csv", "decisions"))
    findings = list(read_rows(CANDIDATE_DIR / "findings.csv", "findings"))

    changed_claim = next(a for a in assertions if a["source_fidelity_state"] == "changed")
    aid = changed_claim["assertion_id"]
    spoofed_decisions = []
    for d in decisions:
        row = dict(d)
        if row["assertion_id"] == aid:
            row["outcome"] = "accepted_auto_source"
        spoofed_decisions.append(row)

    status = eligibility(changed_claim, evidence, sources, spoofed_decisions, findings)
    assert status["eligible"] is False
    assert real_candidate_verification["accepted_decisions"] == 0


def test_rebuild_preserves_editorial_changes_before_any_writes(tmp_path: Path) -> None:
    work = tmp_path / "candidate"
    shutil.copytree(CANDIDATE_DIR, work)
    decisions = work / "decisions.csv"
    from tools.lexicon_tables import write_rows

    rows = list(read_rows(decisions, "decisions"))
    rows[0]["note_json"] = "Owner editorial correction; preserve this note."
    write_rows(decisions, "decisions", rows)
    before = {p.name: p.read_bytes() for p in work.glob("*.csv")}
    with pytest.raises(ValueError, match="Conflicting candidate edits"):
        build_candidate_workspace(work)
    assert before == {p.name: p.read_bytes() for p in work.glob("*.csv")}


@pytest.mark.parametrize("relative", ["data/sources/tamil-lexicon", "data/curation/tamil-lexicon"])
def test_build_rejects_protected_workspace_before_reading_snapshots(relative: str) -> None:
    from tools.lexicon import LexiconError

    with pytest.raises(LexiconError, match="overlap"):
        build_candidate_workspace(ROOT / relative)


def test_arikkai_qualifiers_preserved_with_change_history() -> None:
    """Qualifier templates on arikkai senses 3 and 4 remain explicit without blind scope acceptance."""
    tables = {
        name: list(read_rows(CANDIDATE_DIR / f"{name}.csv", name))
        for name in ("identities", "changes", "successors", "assertions", "decisions", "labels", "scopes", "texts")
    }
    assert validate_history(
        tables["identities"],
        tables["changes"],
        tables["successors"],
        tables["assertions"],
        tables["decisions"],
    ) == []

    active_text_aids = {r["text_id"]: r["text_assertion_id"] for r in tables["texts"]}
    assertions_by_id = {r["assertion_id"]: r for r in tables["assertions"]}
    assert assertions_by_id[active_text_aids["txt_61630435-ebc8-5d61-b2e6-c3dcb745bab2"]]["value_json"] == "(written) appeal; announcement"
    assert assertions_by_id[active_text_aids["txt_42a3e955-b4e7-51bc-a533-d34db434abc3"]]["value_json"] == "(catholicism) confession"

    assert len(tables["changes"]) == 2
    assert {(c["old_assertion_id"], c["new_assertion_id"]) for c in tables["changes"]} == {
        ("ast_fe25618c-674e-58cf-9cda-ac8e65aa0ef7", active_text_aids["txt_61630435-ebc8-5d61-b2e6-c3dcb745bab2"]),
        ("ast_90a3b38c-927b-5ec0-a9d7-1eb9963062b4", active_text_aids["txt_42a3e955-b4e7-51bc-a533-d34db434abc3"]),
    }

    assert {lbl["code"]: lbl["category"] for lbl in tables["labels"]} == {
        "written": "register",
        "catholicism": "domain",
    }
    sense_scopes = [s for s in tables["scopes"] if s["subject_kind"] == "sense"]
    assert {(s["subject_id"], s["dimension"], s["state"]) for s in sense_scopes} == {
        ("sen_64d6c824-9c3d-52bf-abae-78e9c5d9ff3c", "register", "unknown"),
        ("sen_28f47fad-a25a-5f7b-8a52-d80aecf26084", "domain", "unknown"),
    }


@pytest.mark.xdist_group("real_lexicon_packs")
def test_homograph_workspace_verified_and_pending_only(
    real_homograph_verification: dict,
) -> None:
    """Single-page multi-POS companion homograph workspace validates with 2 entries and 0 accepted claims."""
    result = real_homograph_verification
    assert result["ok"] is True
    assert result["snapshot_count"] == 1
    assert result["entry_count"] == 2
    assert result["sense_count"] == 3
    assert result["form_count"] == 2
    assert result["ipa_form_count"] == 0
    assert result["accepted_decisions"] == 0
    assert result["decision_outcomes"] == {"needs_review": 5, "pending": 2}
    assert result["validation"]["findings"] == []
    assert result["release_guard"]["l3_pack_eligible"] is False
    assert result["release_guard"]["eligible_assertions"] == 0

    assertions = {r["assertion_id"]: r for r in read_rows(HOMOGRAPH_DIR / "assertions.csv", "assertions")}
    entries = list(read_rows(HOMOGRAPH_DIR / "entries.csv", "entries"))
    assert len({e["entry_id"] for e in entries}) == 2
    assert {assertions[e["pos_assertion_id"]]["value_json"] for e in entries} == {"INTJ", "NOUN"}
    forms = list(read_rows(HOMOGRAPH_DIR / "forms.csv", "forms"))
    assert {assertions[f["text_assertion_id"]]["value_json"] for f in forms} == {"\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf"}


def test_homograph_idempotent_replay_and_excludes_unpinned_templates() -> None:
    """Homograph replay is byte-identical and excludes {{ta-IPA}}, quotations, etymology, and synonyms."""
    replay = check_idempotent_replay(HOMOGRAPH_DIR, dataset="homograph")
    assert replay["ok"] is True
    assert replay["checked_files"] == 25
    assert replay["diffs"] == []

    for table in ("assertions", "forms", "texts", "entries"):
        for row in read_rows(HOMOGRAPH_DIR / f"{table}.csv", table):
            blob = json.dumps(row, ensure_ascii=True, sort_keys=True)
            for marker in ("{{ta-IPA", "{{quote-", "{{syn", "{{ta-decl", "{{col", "*nal"):
                assert marker not in blob


def test_core_review_packet_json_matches_workspace_hashes() -> None:
    """Machine-readable core_review_packet.json and markdown packet match verified CSV hashes."""
    packet_path = CANDIDATE_DIR / "provenance/core_review_packet.json"
    doc_path = ROOT / "docs/reviews/wiktionary-core-candidate.md"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    doc_text = doc_path.read_text(encoding="utf-8")

    assert packet["accepted_decisions_count"] == 0
    assert packet["reuse_state_in_sources_csv"] == "restricted"
    assert len(packet["candidate_entries"]) == 4
    assert len(packet["homograph_entries"]) == 2

    cand_ast = {r["assertion_id"]: r for r in read_rows(CANDIDATE_DIR / "assertions.csv", "assertions")}
    homo_ast = {r["assertion_id"]: r for r in read_rows(HOMOGRAPH_DIR / "assertions.csv", "assertions")}

    for entry in packet["candidate_entries"]:
        assert entry["entry_id"] in doc_text
        for sense in entry["senses"]:
            assert cand_ast[sense["assertion_id"]]["claim_revision_sha256"] == sense["claim_revision_sha256"]

    for entry in packet["homograph_entries"]:
        assert entry["entry_id"] in doc_text
        for sense in entry["senses"]:
            assert homo_ast[sense["assertion_id"]]["claim_revision_sha256"] == sense["claim_revision_sha256"]


@pytest.mark.xdist_group("real_lexicon_packs")
def test_reviewed_workspace_verified_and_l3_eligible(
    tmp_path: Path,
    real_reviewed_verification: dict,
) -> None:
    """Merged reviewed workspace binds all 31 receipt approvals, keeps scopes/v1 excluded, and promotes cleanly."""
    result = real_reviewed_verification
    assert result["ok"] is True
    assert result["original_12_verified"] is True
    assert result["original_12_count"] == 12
    assert result["snapshot_count"] == 5
    assert result["entry_count"] == 6
    assert result["sense_count"] == 19
    assert result["form_count"] == 6
    assert result["ipa_form_count"] == 0
    assert result["pack_member_count"] == 6
    assert result["eligible_assertions"] == 31
    assert result["ineligible_assertions"] == 4
    assert result["accepted_human_decisions"] == 31
    assert result["rejected_current_decisions"] == 2
    assert result["needs_review_current_decisions"] == 2
    assert result["open_findings"] == 2
    assert result["reviewer_id"] == "abish"
    assert result["decision_date"] == "2026-11-14"
    assert result["validation"]["findings"] == []

    guard = result["release_guard"]
    assert guard["pack"] == "core"
    assert guard["l3_pack_eligible"] is True
    assert guard["eligible_assertions"] == 31
    assert guard["included_entries"] == 6
    assert guard["findings"] == []

    out_dir = tmp_path / "core-canonical"
    promo = promote(REVIEWED_DIR, pack="core", output=out_dir)
    assert promo["l3_pack_eligible"] is True
    assert promo["entry_count"] == 6
    assert promo["sense_count"] == 19
    assert validate_canonical_dir(out_dir) == []
    loaded = load_canonical_pack(out_dir)
    assert len(loaded["tables"]["entries"]) == 6
    assert len(loaded["tables"]["assertions"]) == 31
    assert len(loaded["tables"]["senses"]) == 19


def test_reviewed_idempotent_replay_and_pending_workspaces_untouched(
    small_core_canonical: Path,
) -> None:
    """Reviewed closure replay is deterministic while pending workspaces & packet stay untouched."""
    replay = check_reviewed_idempotent_replay(REVIEWED_DIR, canonical=small_core_canonical)
    assert replay["ok"] is True
    assert replay["checked_files"] == 28
    assert replay["diffs"] == []

    assert verify_candidate_workspace(CANDIDATE_DIR, canonical=small_core_canonical)["accepted_decisions"] == 0
    assert (
        verify_candidate_workspace(HOMOGRAPH_DIR, dataset="homograph", canonical=small_core_canonical)[
            "accepted_decisions"
        ]
        == 0
    )
    assert (
        digest(CANDIDATE_DIR / "provenance/core_review_packet.json")
        == "0b2168d07e9b45b5316994c1d97648ebf5de3ad666de050b10afbe5dfa58695b"
    )


def test_negative_reviewed_receipt_and_claim_tamper_rejected(
    tmp_path: Path,
    small_core_canonical: Path,
) -> None:
    """Tampering receipt digest, claim revision, or evidence bundle is rejected."""
    receipt = json.loads(DEFAULT_APPROVAL_RECEIPT.read_text(encoding="utf-8"))

    bad_packet_receipt = tmp_path / "bad_packet_receipt.json"
    tampered = dict(receipt)
    tampered["review_packet_sha256"] = "0" * 64
    bad_packet_receipt.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="review_packet_sha256 mismatch"):
        build_reviewed_workspace(
            tmp_path / "out1",
            receipt_path=bad_packet_receipt,
            canonical=small_core_canonical,
        )

    bad_claim_receipt = tmp_path / "bad_claim_receipt.json"
    tampered = json.loads(DEFAULT_APPROVAL_RECEIPT.read_text(encoding="utf-8"))
    tampered["approved_claims"][0]["claim_revision_sha256"] = "f" * 64
    bad_claim_receipt.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="claim_revision_sha256 mismatch"):
        build_reviewed_workspace(
            tmp_path / "out2",
            receipt_path=bad_claim_receipt,
            canonical=small_core_canonical,
        )

    bad_ev_receipt = tmp_path / "bad_ev_receipt.json"
    tampered = json.loads(DEFAULT_APPROVAL_RECEIPT.read_text(encoding="utf-8"))
    tampered["approved_claims"][0]["evidence_bundle_sha256"] = "e" * 64
    bad_ev_receipt.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="Evidence bundle SHA-256 mismatch"):
        build_reviewed_workspace(
            tmp_path / "out3",
            receipt_path=bad_ev_receipt,
            canonical=small_core_canonical,
        )

    reviewed_copy = tmp_path / "reviewed_copy"
    shutil.copytree(REVIEWED_DIR, reviewed_copy)
    ev_rows = list(read_rows(reviewed_copy / "evidence.csv", "evidence"))
    ev_rows[0]["locator_json"] = "tampered"
    write_rows(reviewed_copy / "evidence.csv", "evidence", ev_rows)
    with pytest.raises(ValueError, match="Evidence bundle SHA-256 mismatch"):
        verify_reviewed_workspace(reviewed_copy, canonical=small_core_canonical)


def test_reviewed_rebuild_conflict_and_protected_paths(
    tmp_path: Path,
    small_core_canonical: Path,
) -> None:
    """Reviewed rebuild refuses overwriting manual edits and never touches protected source trees."""
    from tools.lexicon import LexiconError

    reviewed_copy = tmp_path / "reviewed_edit"
    shutil.copytree(REVIEWED_DIR, reviewed_copy)
    rows = list(read_rows(reviewed_copy / "decisions.csv", "decisions"))
    rows[-1]["note_json"] = "Manual reviewer addendum; must not be overwritten."
    write_rows(reviewed_copy / "decisions.csv", "decisions", rows)
    before = {p.name: p.read_bytes() for p in reviewed_copy.glob("*.csv")}
    with pytest.raises(ValueError, match="Conflicting reviewed edits"):
        build_reviewed_workspace(reviewed_copy, canonical=small_core_canonical)
    assert before == {p.name: p.read_bytes() for p in reviewed_copy.glob("*.csv")}

    for rel in (
        "data/sources/tamil-lexicon",
        "data/curation/tamil-lexicon",
        "data/curation/wiktionary-candidate",
        "data/curation/wiktionary-homograph-candidate",
    ):
        with pytest.raises(LexiconError, match="overlap"):
            build_reviewed_workspace(ROOT / rel, canonical=small_core_canonical)


def test_canonical_parameter_isolates_small_pack_and_rejects_tamper(
    tmp_path: Path,
    small_core_canonical: Path,
) -> None:
    """Narrow optional canonical= decouples tests safely without disabling canonical validation."""
    import inspect

    assert validate_canonical_dir(small_core_canonical) == []
    assert small_core_canonical.resolve() != (ROOT / "lexicon/dictionary").resolve()

    for fn in (
        build_reviewed_workspace,
        verify_reviewed_workspace,
        check_reviewed_idempotent_replay,
        verify_candidate_workspace,
    ):
        assert inspect.signature(fn).parameters["canonical"].default is None

    # Small promoted canonical validates reviewed workspace end-to-end without scanning 10k rows.
    res = verify_reviewed_workspace(REVIEWED_DIR, canonical=small_core_canonical)
    assert res["ok"] is True
    assert res["eligible_assertions"] == 31

    # Passing a tampered or empty canonical directory must fail loudly (never bypassed).
    bad_canon = tmp_path / "bad_canon"
    shutil.copytree(small_core_canonical, bad_canon)
    (bad_canon / "packs.toml").write_text("tampered = true\n", encoding="utf-8")
    with pytest.raises((ValueError, Exception)):
        verify_reviewed_workspace(REVIEWED_DIR, canonical=bad_canon)
    with pytest.raises((ValueError, Exception)):
        verify_candidate_workspace(CANDIDATE_DIR, canonical=bad_canon)
