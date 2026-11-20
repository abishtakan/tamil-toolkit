"""Synthetic editorial fixtures only; these tests approve no source content."""

from copy import deepcopy
import hashlib

import pytest

from tools.lexicon import LexiconError
from tools import lexicon_review as review


def bundle(**updates):
    claim = dict(assertion_id="a1", subject_kind="entry", subject_id="e1",
                 property_code="headword", value_state="known", value_json="sample",
                 origin="verbatim_source", source_fidelity_state="verified",
                 ambiguity_state="unambiguous", algorithm_reference=None,
                 convention_reference=None, imported_status_json=None,
                 imported_confidence_json=None)
    claim.update(updates)
    claim["claim_revision_sha256"] = review.claim_revision(claim)
    evidence = [dict(assertion_id="a1", source_id="s1", source_record_id=None,
                     locator_json="synthetic page 1", evidence_role="supports",
                     extraction_version="fixture-v1", extraction_sha256="1" * 64)]
    sources = [dict(source_id="s1", evidence_verification_state="verified",
                    reuse_state="permitted", reuse_basis_json="synthetic fixture only",
                    attribution_text_json="synthetic", attribution_reference_json=None)]
    decision = dict(decision_id="d1", assertion_id="a1",
                    assertion_revision_sha256=claim["claim_revision_sha256"],
                    evidence_bundle_sha256=review.evidence_hash(evidence),
                    outcome="accepted_auto_source", actor_type="automated", actor_id=None,
                    method_version="fixture-v1", decision_date="2026-11-14",
                    note_json="synthetic", predecessor_decision_id=None)
    return claim, evidence, sources, [decision]


def human(decisions):
    decisions[0].update(outcome="accepted_human", actor_type="human", actor_id="fixture_reviewer")


def codes(findings):
    return {f["issue_code"] for f in findings}


@pytest.mark.parametrize("text", ["sample", "e" + chr(0x0301), "a" + chr(0x200D)])
def test_unicode_without_exceptions_does_not_scan_unrelated_decisions(text):
    claim, _, _, decisions = bundle(value_json=text)

    class CountedDecisions:
        visits = 0

        def __iter__(self):
            for row in decisions * 1000:
                self.visits += 1
                yield row

    counted = CountedDecisions()
    expected = review.unicode_findings(claim)
    assert review.unicode_findings(claim, iter(()), counted) == expected
    assert counted.visits == 0


def test_review_schema_checks_use_shared_validator_with_reference_parity(monkeypatch):
    claim, evidence, _, decisions = bundle()
    exception = dict(assertion_id="a1", claim_revision_sha256=claim["claim_revision_sha256"],
                     kind="intentional_control", scalar_sequence=[0x200D], scalar_position=0,
                     value_sha256="1" * 64, reason_json="synthetic fixture", decision_id="d1")
    cases = []
    for table, row in (("assertions", claim), ("evidence", evidence[0]),
                       ("decisions", decisions[0]), ("unicode_exceptions", exception)):
        variants = [row, dict(row, unexpected=True)]
        for key in row:
            missing = dict(row)
            missing.pop(key)
            variants.append(missing)
            variants.extend(dict(row, **{key: value}) for value in (None, [], {}, 1, ""))
        for variant in variants:
            cases.append((table, variant, review._validator(table).is_valid(variant)))

    def reject_reference_recompilation(_table):
        raise AssertionError("review must reuse the shared compiled row validator")

    monkeypatch.setattr(review, "_validator", reject_reference_recompilation)
    for table, row, expected in cases:
        assert review._valid(table, row) == expected, (table, row)


def test_hashes_are_stable_and_bind_all_content_without_mutation():
    claim, evidence, sources, decisions = bundle()
    before = deepcopy((claim, evidence, sources, decisions))
    assert review.claim_revision(dict(reversed(list(claim.items())))) == claim["claim_revision_sha256"]
    assert review.claim_revision(dict(claim, claim_revision_sha256="ignored")) == claim["claim_revision_sha256"]
    assert review.claim_revision(dict(claim, convention_reference="v2")) != claim["claim_revision_sha256"]
    other = dict(evidence[0], locator_json="page 2")
    assert review.evidence_hash([other, *evidence]) == review.evidence_hash([*evidence, other])
    assert review.evidence_hash([other]) != review.evidence_hash(evidence)
    assert review.eligibility(claim, evidence, sources, decisions) == dict(eligible=True, status="accepted_auto_source", reasons=[])
    assert (claim, evidence, sources, decisions) == before


@pytest.mark.parametrize("updates", [dict(origin=x) for x in ["correction", "inferred", "derived", "editorial"]] + [dict(ambiguity_state="ambiguous"), dict(ambiguity_state="unknown"), dict(source_fidelity_state="changed")])
def test_auto_cannot_accept_changed_inferred_or_ambiguous_claims(updates):
    args = bundle(**updates)
    assert not review.eligibility(*args)["eligible"]
    human(args[3])
    assert review.eligibility(*args)["eligible"]


@pytest.mark.parametrize("source_updates", [dict(reuse_state="unknown"), dict(reuse_basis_json=None), dict(evidence_verification_state="unknown"), dict(attribution_text_json=None)])
def test_human_cannot_waive_source_reuse_or_attribution(source_updates):
    args = bundle()
    human(args[3])
    args[2][0].update(source_updates)
    assert not review.eligibility(*args)["eligible"]


@pytest.mark.parametrize("mutation", ["claim", "evidence", "locator", "role", "actor", "date", "method", "unknown", "empty", "blocking"])
def test_eligibility_fails_closed(mutation):
    claim, evidence, sources, decisions = bundle()
    findings = []
    if mutation == "claim":
        claim["value_json"] = "changed"
    elif mutation == "evidence":
        evidence[0]["extraction_sha256"] = "2" * 64
    elif mutation == "locator":
        evidence[0]["locator_json"] = ""
    elif mutation == "role":
        evidence[0]["evidence_role"] = "transcribes"
    elif mutation == "actor":
        human(decisions)
        decisions[0]["actor_id"] = None
    elif mutation == "date":
        decisions[0]["decision_date"] = "2026-02-30"
    elif mutation == "method":
        decisions[0]["method_version"] = ""
    elif mutation == "unknown":
        claim.update(value_state="unknown", value_json=None)
    elif mutation == "empty":
        claim["value_json"] = ""
    else:
        findings = [dict(assertion_id="a1", issue_code="unresolved", severity="error", status="open")]
    assert not review.eligibility(claim, evidence, sources, decisions, findings)["eligible"]


def test_recomputed_claim_still_requires_new_decision_and_rejection_supersedes():
    claim, evidence, sources, decisions = bundle()
    claim["convention_reference"] = "v2"
    claim["claim_revision_sha256"] = review.claim_revision(claim)
    assert not review.eligibility(claim, evidence, sources, decisions)["eligible"]
    claim, evidence, sources, decisions = bundle()
    decisions.append(dict(decisions[0], decision_id="d2", predecessor_decision_id="d1", outcome="rejected"))
    assert not review.eligibility(claim, evidence, sources, decisions)["eligible"]


def identity(entity_id, lifecycle="active"):
    return dict(entity_id=entity_id, kind="entry", allocation_key=entity_id,
                lifecycle=lifecycle, identity_decision_id="d1" if lifecycle != "active" else None)


def test_history_split_merge_cycles_dangling_and_reused_ids():
    claim, _, _, decisions = bundle()
    ids = [identity("e1", "split"), identity("e2"), identity("e3")]
    edges = [dict(retired_id="e1", successor_id=x, role="split", identity_decision_id="d1") for x in ["e2", "e3"]]
    assert review.validate_history(ids, [], edges, [claim], decisions) == []
    assert "split_cardinality" in codes(review.validate_history(ids, [], edges[:1], [claim], decisions))
    assert "reused_id" in codes(review.validate_history(ids + [identity("e1")], [], edges, [claim], decisions))
    bad = edges + [dict(retired_id="e2", successor_id="e1", role="merge", identity_decision_id="missing")]
    found = codes(review.validate_history(ids, [], bad, [claim], decisions))
    assert {"successor_cycle", "dangling_id"} <= found
    merge_ids = [identity("e1", "merged"), identity("e2")]
    merge = [dict(retired_id="e1", successor_id="e2", role="merge", identity_decision_id="d1")]
    assert review.validate_history(merge_ids, [], merge, [claim], decisions) == []


def test_history_compensating_reversal_and_revision_invalidation():
    claim, _, _, decisions = bundle()
    changed = dict(claim, assertion_id="a2", value_json="corrected")
    changed["claim_revision_sha256"] = review.claim_revision(changed)
    change = dict(change_id="c1", subject_id="e1", old_assertion_id="a1", new_assertion_id="a2",
                  reason_json="synthetic correction", evidence_reference="fixture", decision_id="d1", inverse_change_id=None)
    reversal = dict(change, change_id="c2", old_assertion_id="a2", new_assertion_id="a1", inverse_change_id="c1")
    assert review.validate_history([identity("e1")], [change, reversal], [], [claim, changed], decisions) == []
    reversal["new_assertion_id"] = "a2"
    assert "invalid_reversal" in codes(review.validate_history([identity("e1")], [change, reversal], [], [claim, changed], decisions))
    transferred = dict(decisions[0], assertion_id="a2")
    assert "stale_decision_revision" in codes(review.validate_history([identity("e1")], [], [], [claim, changed], [transferred]))


def test_unicode_uses_native_rust_and_preserves_controls_and_malformed_input():
    claim, *_ = bundle(value_json="".join(map(chr, [0x0B95, 0x0BC6, 0x0BBE, 0x200D])))
    before = deepcopy(claim)
    assert {"non_nfc_original", "intentional_control", "invalid_orthography"} <= codes(review.unicode_findings(claim))
    assert claim == before
    clean, *_ = bundle(value_json="\u0b95\u0bca")
    assert review.unicode_findings(clean) == []
    malformed, *_ = bundle(value_json="\u0b95\u0bcd\u0bcd")
    assert "invalid_orthography" in codes(review.unicode_findings(malformed))


def test_unicode_exception_requires_exact_revision_value_position_and_human_decision():
    claim, _, _, decisions = bundle(value_json="sample" + chr(0x200D))
    human(decisions)
    exception = dict(assertion_id="a1", claim_revision_sha256=claim["claim_revision_sha256"],
                     value_sha256=hashlib.sha256(claim["value_json"].encode("utf-8")).hexdigest(),
                     kind="intentional_control", scalar_sequence=[0x200D], scalar_position=6,
                     reason_json="synthetic preservation test", decision_id="d1")
    assert "intentional_control" not in codes(review.unicode_findings(claim, [exception], decisions))
    for key, value in [("claim_revision_sha256", "0" * 64), ("value_sha256", "0" * 64), ("scalar_position", 0), ("reason_json", ""), ("decision_id", "absent")]:
        assert "invalid_unicode_exception" in codes(review.unicode_findings(claim, [dict(exception, **{key: value})], decisions))
    unused = dict(exception, kind="non_nfc_original", scalar_sequence=[ord("s")], scalar_position=0)
    assert "unused_unicode_exception" in codes(review.unicode_findings(claim, [unused], decisions))


def test_invalid_scalar_cannot_be_waived_and_missing_native_is_a_prerequisite_error(monkeypatch):
    claim, *_ = bundle(value_json="\ud800")
    assert "invalid_scalar" in codes(review.unicode_findings(claim))
    claim, *_ = bundle()
    def unavailable(text):
        raise LexiconError("native Rust adapter unavailable")
    monkeypatch.setattr(review, "native_inspect", unavailable)
    with pytest.raises(LexiconError, match="native Rust"):
        review.unicode_findings(claim)


def test_superseded_human_decision_cannot_authorize_unicode_exception():
    claim, _, _, decisions = bundle(value_json="sample" + chr(0x200D))
    human(decisions)
    exception = dict(assertion_id="a1", claim_revision_sha256=claim["claim_revision_sha256"],
                     value_sha256=hashlib.sha256(claim["value_json"].encode()).hexdigest(),
                     kind="intentional_control", scalar_sequence=[0x200D], scalar_position=6,
                     reason_json="synthetic preservation", decision_id="d1")
    decisions.append(dict(decisions[0], decision_id="d2", outcome="rejected", predecessor_decision_id="d1"))
    assert "invalid_unicode_exception" in codes(review.unicode_findings(claim, [exception], decisions))


def test_history_rejects_broken_transition_chain_and_unrecorded_reversal():
    claim, _, _, decisions = bundle()
    second = dict(claim, assertion_id="a2", value_json="second")
    third = dict(claim, assertion_id="a3", value_json="third")
    for row in [second, third]:
        row["claim_revision_sha256"] = review.claim_revision(row)
    first = dict(change_id="c1", subject_id="e1", old_assertion_id="a1", new_assertion_id="a2",
                 reason_json="synthetic edit", evidence_reference="fixture", decision_id="d1", inverse_change_id=None)
    broken = dict(first, change_id="c2", new_assertion_id="a3")
    assert "broken_change_chain" in codes(review.validate_history([identity("e1")], [first, broken], [], [claim, second, third], decisions))
    reversal = dict(first, change_id="c2", old_assertion_id="a2", new_assertion_id="a1")
    assert "invalid_reversal" in codes(review.validate_history([identity("e1")], [first, reversal], [], [claim, second], decisions))


def test_unicode_valid_tamil_symbol_is_not_mislabeled_as_bad_orthography():
    claim, *_ = bundle(value_json="\u0bf9")
    assert review.unicode_findings(claim) == []


def test_eligibility_checks_each_gate_with_current_hashes():
    for field, value, expected in [("value_state", "unknown", "unknown_value"),
                                   ("value_json", "", "empty_required_claim")]:
        args = bundle(**{field: value})
        assert expected in review.eligibility(*args)["reasons"]
    args = bundle()
    args[1][0]["evidence_role"] = "transcribes"
    args[3][0]["evidence_bundle_sha256"] = review.evidence_hash(args[1])
    assert "missing_verified_support" in review.eligibility(*args)["reasons"]


def test_eligibility_scopes_record_level_findings_without_blocking_unrelated_assertions():
    claim, evidence, sources, decisions = bundle()
    evidence[0]["source_record_id"] = "rec_1"
    decisions[0]["evidence_bundle_sha256"] = review.evidence_hash(evidence)

    unrelated_finding = dict(
        finding_id="fnd_other",
        record_id="rec_2",
        assertion_id=None,
        issue_code="IMPORTED_COUNT_WARNING",
        severity="error",
        scalar_positions=[],
        status="open",
        resolution_reason_json=None,
    )
    assert review.eligibility(claim, evidence, sources, decisions, [unrelated_finding])["eligible"]

    linked_finding = dict(unrelated_finding, finding_id="fnd_linked", record_id="rec_1")
    res_linked = review.eligibility(claim, evidence, sources, decisions, [linked_finding])
    assert not res_linked["eligible"]
    assert "blocking_findings" in res_linked["reasons"]

    global_finding = dict(unrelated_finding, finding_id="fnd_global", record_id=None, assertion_id=None)
    res_global = review.eligibility(claim, evidence, sources, decisions, [global_finding])
    assert not res_global["eligible"]
    assert "blocking_findings" in res_global["reasons"]


@pytest.mark.parametrize("cp", [0x2028, 0x2029])
def test_unicode_findings_includes_line_and_paragraph_separators_in_intentional_controls(cp):
    claim, _, _, decisions = bundle(value_json="a" + chr(cp) + "b")
    assert "intentional_control" in codes(review.unicode_findings(claim))
    human(decisions)
    exception = dict(
        assertion_id="a1",
        claim_revision_sha256=claim["claim_revision_sha256"],
        value_sha256=hashlib.sha256(claim["value_json"].encode("utf-8")).hexdigest(),
        kind="intentional_control",
        scalar_sequence=[cp],
        scalar_position=1,
        reason_json="line/paragraph separator test",
        decision_id="d1",
    )
    assert review.unicode_findings(claim, [exception], decisions) == []
