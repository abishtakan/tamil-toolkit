"""Read-only editorial review checks for Feature 021.

Inputs are decoded schema row dictionaries (JSON cells decoded exactly once).
Hashes use canonical ASCII JSON; evidence rows are sorted, with duplicates retained.
Unicode exception value hashes cover the original string's UTF-8 bytes. Nothing
here creates decisions, edits claims, repairs text, or establishes source rights.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import date
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from tools.lexicon import LexiconError, json_text, native_audit_batch, native_batch_canonical_json_sha256, native_inspect
from tools.lexicon_tables import is_intentional_control, validate_row

_ORIG_NATIVE_INSPECT = native_inspect


def _hash(value):
    return hashlib.sha256(json_text(value).encode("ascii")).hexdigest()


def claim_revision(assertion):
    """Bind every supplied claim field except its self-referential digest."""
    if "claim_revision_sha256" in assertion:
        assertion = {k: v for k, v in assertion.items() if k != "claim_revision_sha256"}
    return _hash(assertion)


def evidence_hash(evidence):
    """Hash an order-independent multiset of complete decoded evidence rows."""
    return _hash(sorted(evidence, key=json_text))


@lru_cache(maxsize=None)
def _validator(table):
    root = Path(__file__).resolve().parents[1] / "schemas/lexicon"
    common = json.loads((root / "common.schema.json").read_text(encoding="utf-8"))
    review = json.loads((root / "review.schema.json").read_text(encoding="utf-8"))
    registry = Registry().with_resource("common.schema.json", Resource.from_contents(common))
    return Draft202012Validator(review["$defs"][table], registry=registry, format_checker=FormatChecker())


def _valid(table, row):
    try:
        validate_row(table, row)
    except LexiconError:
        return False
    return True


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _actor_valid(decision, human=False):
    if not _valid("decisions", decision):
        return False
    try:
        if date.fromisoformat(decision["decision_date"]).isoformat() != decision["decision_date"]:
            return False
    except (ValueError, TypeError):
        return False
    if human or decision.get("outcome") == "accepted_human":
        return decision.get("actor_type") == "human" and _nonempty(decision.get("actor_id"))
    return decision.get("actor_type") == "automated" and _nonempty(decision.get("method_version"))


def _source_valid(source):
    return (source.get("evidence_verification_state") == "verified"
            and source.get("reuse_state") == "permitted"
            and _nonempty(source.get("reuse_basis_json"))
            and (_nonempty(source.get("attribution_text_json"))
                 or _nonempty(source.get("attribution_reference_json"))))


def _current_decisions(decisions):
    """Require a single unambiguous terminal in an explicit predecessor chain."""
    index = {d.get("decision_id"): d for d in decisions}
    if len(index) != len(decisions) or None in index:
        return []
    superseded = set()
    for decision in decisions:
        predecessor = decision.get("predecessor_decision_id")
        visited = {decision.get("decision_id")}
        while predecessor:
            if predecessor not in index or predecessor in visited:
                return []
            visited.add(predecessor)
            superseded.add(predecessor)
            predecessor = index[predecessor].get("predecessor_decision_id")
    return [d for key, d in index.items() if key not in superseded]


def eligibility(
    assertion,
    evidence,
    sources,
    decisions,
    findings=(),
    *,
    _revision=None,
    _assertion_valid=None,
    _source_index=None,
    _evidence_valid=None,
):
    """Compute claim eligibility, never trusting an imported approval boolean.

    Structural dependency closure and Unicode findings are supplied by the
    caller. This helper checks decoded claim/evidence/decision rows and source
    rights metadata; it does not retrieve publications or authenticate actors.
    """
    reasons = []
    assertion_id = assertion.get("assertion_id")
    revision = claim_revision(assertion) if _revision is None else _revision
    assertion_valid = _valid("assertions", assertion) if _assertion_valid is None else _assertion_valid
    if not assertion_valid:
        reasons.append("invalid_assertion")
    if assertion.get("claim_revision_sha256") != revision:
        reasons.append("claim_revision_mismatch")
    value = assertion.get("value_json")
    if assertion.get("value_state") != "known" or value is None:
        reasons.append("unknown_value")
    if assertion.get("property_code") in {"headword", "definition"} and not _nonempty(value):
        reasons.append("empty_required_claim")
    rows = [e for e in evidence if e.get("assertion_id") == assertion_id]
    if _source_index is not None:
        source_index = _source_index
    else:
        source_rows = list(sources.values()) if isinstance(sources, dict) else list(sources)
        source_index = {s.get("source_id"): s for s in source_rows}
        if len(source_index) != len(source_rows):
            reasons.append("duplicate_source_id")
    supporting = False
    for row in rows:
        source = source_index.get(row.get("source_id"), {})
        ev_valid = _valid("evidence", row) if _evidence_valid is None else _evidence_valid
        if not ev_valid or not _nonempty(row.get("locator_json")):
            reasons.append("invalid_evidence")
        if not _source_valid(source):
            reasons.append("unverified_source_or_reuse_attribution")
        elif row.get("evidence_role") == "supports" and ev_valid:
            supporting = True
    if not supporting:
        reasons.append("missing_verified_support")
    linked_records = {r.get("source_record_id") for r in rows if r.get("source_record_id")}
    for finding in findings:
        finding_aid = finding.get("assertion_id")
        finding_rid = finding.get("record_id")
        if finding_aid not in (None, ""):
            if finding_aid != assertion_id:
                continue
        elif finding_rid not in (None, "") and finding.get("scope") != "global":
            if finding_rid not in linked_records:
                continue
        if finding.get("severity") == "error" and (finding.get("status", "open") != "resolved"
                                                     or not _nonempty(finding.get("resolution_reason_json"))):
            reasons.append("blocking_findings")
    relevant = [d for d in decisions if d.get("assertion_id") == assertion_id]
    current = _current_decisions(relevant)
    decision = current[0] if len(current) == 1 else None
    status = "needs_review"
    if decision is None:
        reasons.append("missing_or_conflicting_decision")
    else:
        outcome = decision.get("outcome")
        if (decision.get("assertion_revision_sha256") != revision
                or decision.get("evidence_bundle_sha256") != evidence_hash(rows)):
            reasons.append("stale_decision")
        if not _actor_valid(decision):
            reasons.append("invalid_decision_actor_or_date")
        if outcome not in {"accepted_auto_source", "accepted_human"}:
            reasons.append("decision_not_accepted")
            status = outcome if outcome in {"pending", "rejected", "needs_review"} else "needs_review"
        elif outcome == "accepted_auto_source":
            if (assertion.get("origin") != "verbatim_source"
                    or assertion.get("source_fidelity_state") != "verified"
                    or assertion.get("ambiguity_state") != "unambiguous"
                    or any(e.get("evidence_role") == "contradicts" for e in rows)):
                reasons.append("human_review_required")
        if not reasons and outcome in {"accepted_auto_source", "accepted_human"}:
            status = outcome
    reasons = sorted(set(reasons))
    return {"eligible": not reasons, "status": status if not reasons or status == "rejected" else "quarantined", "reasons": reasons}


def _finding(code, subject, reason, positions=(), assertion_id=None):
    """Schema-shaped deterministic diagnostics, without including source text."""
    return dict(finding_id="finding_" + _hash([code, subject, reason, list(positions)])[:24],
                record_id=None, assertion_id=assertion_id, issue_code=code,
                severity="error", scalar_positions=list(positions), status="open",
                resolution_reason_json=None, entity_id=subject, reason=reason)


def validate_history(identities, changes, successors, assertions, decisions):
    """Check supplied immutable snapshots and append-ordered compensating changes.

    A single snapshot cannot prove that rows were never deleted in an earlier
    workspace. Evidence-bundle invalidation is checked by eligibility instead.
    """
    result = []

    def issue(code, subject, reason):
        result.append(_finding(code, subject, reason))

    def index(rows, key):
        indexed = {}
        for row in rows:
            identity = row.get(key)
            if not identity:
                issue("dangling_id", key, "Required identity is missing")
            elif identity in indexed:
                issue("reused_id", identity, "Identity occurs more than once")
            else:
                indexed[identity] = row
        return indexed

    ids = index(identities, "entity_id")
    claims = index(assertions, "assertion_id")
    reviews = index(decisions, "decision_id")
    edits = index(changes, "change_id")
    allocations = {}
    for key, row in ids.items():
        allocation = (row.get("kind"), row.get("allocation_key"))
        if not allocation[1] or allocation in allocations:
            issue("reused_id", key, "Immutable allocation is empty or assigned more than once")
        allocations[allocation] = key
        reference = row.get("identity_decision_id")
        if reference and reference not in reviews:
            issue("dangling_id", key, "Identity decision is missing")
        if row.get("lifecycle") != "active" and not reference:
            issue("dangling_id", key, "Tombstone requires an identity decision")
    for key, claim in claims.items():
        if claim.get("subject_id") not in ids:
            issue("dangling_id", key, "Assertion subject is missing")
        if claim.get("claim_revision_sha256") != claim_revision(claim):
            issue("claim_revision_mismatch", key, "Claim content changed without a new revision")
    for key, decision in reviews.items():
        claim = claims.get(decision.get("assertion_id"))
        if claim is None:
            issue("dangling_id", key, "Decision assertion is missing")
        elif decision.get("assertion_revision_sha256") != claim_revision(claim):
            issue("stale_decision_revision", key, "Acceptance cannot transfer to changed claim content")
        predecessor = decision.get("predecessor_decision_id")
        if predecessor and predecessor not in reviews:
            issue("dangling_id", key, "Predecessor decision is missing")
        elif predecessor and reviews[predecessor].get("assertion_id") != decision.get("assertion_id"):
            issue("invalid_decision_history", key, "Predecessor belongs to another assertion")
    if reviews and not _current_decisions(list(reviews.values())):
        # Multiple independent claims can have multiple terminal decisions; an
        # empty result specifically indicates a cycle or broken predecessor.
        issue("invalid_decision_history", "decisions", "Decision history has a cycle or missing predecessor")

    graph = defaultdict(set)
    seen_edges = set()
    for edge in successors:
        old, new = edge.get("retired_id"), edge.get("successor_id")
        if old not in ids or new not in ids or edge.get("identity_decision_id") not in reviews:
            issue("dangling_id", old, "Successor endpoint or identity decision is missing")
        role = edge.get("role")
        signature = (old, new, role)
        if signature in seen_edges:
            issue("duplicate_successor", old, "Successor edge occurs more than once")
        seen_edges.add(signature)
        graph[old].add(new)
        if old in ids:
            expected = {"merge": "merged", "split": "split"}.get(role)
            if expected is None or ids[old].get("lifecycle") != expected:
                issue("reused_id", old, "Successor origin must retain its matching tombstone")
            if edge.get("identity_decision_id") != ids[old].get("identity_decision_id"):
                issue("invalid_identity_decision", old, "Successor decision differs from tombstone decision")
        if old in ids and new in ids:
            if ids[old].get("kind") not in {"entry", "sense"} or ids[new].get("kind") != ids[old].get("kind"):
                issue("invalid_successor_kind", old, "Successors must preserve entry or sense kind")
    for key, row in ids.items():
        count = len(graph.get(key, ()))
        if row.get("lifecycle") == "merged" and count != 1:
            issue("merge_cardinality", key, "A merged identity requires exactly one successor")
        if row.get("lifecycle") == "split" and count < 2:
            issue("split_cardinality", key, "A split identity requires at least two distinct successors")
    nodes = set(graph) | {n for targets in graph.values() for n in targets}
    indegree = dict.fromkeys(nodes, 0)
    for targets in graph.values():
        for node in targets:
            indegree[node] += 1
    queue = deque(n for n in nodes if indegree[n] == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in graph.get(node, ()):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(nodes):
        issue("successor_cycle", "successors", "Successor graph must be acyclic")

    prior = set()
    current_claim = {}
    seen_claims = defaultdict(set)
    for change in changes:
        key, subject = change.get("change_id"), change.get("subject_id")
        if not _valid("changes", change):
            issue("invalid_change", key, "Change row does not match the decoded schema")
        if subject not in ids or change.get("decision_id") not in reviews:
            issue("dangling_id", key, "Change subject or decision is missing")
        old, new = change.get("old_assertion_id"), change.get("new_assertion_id")
        reference_claim = claims.get(old) or claims.get(new) or {}
        chain = (subject, reference_claim.get("property_code"))
        if chain in current_claim and current_claim[chain] != old:
            issue("broken_change_chain", key, "Old assertion is not the preceding change's new assertion")
        for reference in (old, new):
            if reference and reference not in claims:
                issue("dangling_id", key, "Change assertion is missing")
            elif reference and claims[reference].get("subject_id") != subject:
                issue("invalid_change", key, "Change assertion belongs to another subject")
        if old and new and old in claims and new in claims:
            if claims[old].get("property_code") != claims[new].get("property_code"):
                issue("invalid_change", key, "Change cannot replace a different property")
        inverse = change.get("inverse_change_id")
        if inverse:
            original = edits.get(inverse)
            if original is None:
                issue("dangling_id", key, "Compensated change is missing")
            if (inverse not in prior or original is None or original.get("subject_id") != subject
                    or original.get("old_assertion_id") != new or original.get("new_assertion_id") != old
                    or old == new):
                issue("invalid_reversal", key, "Reversal must compensate an earlier change with swapped assertions")
        elif old == new:
            issue("invalid_change", key, "A change must alter an assertion reference")
        elif new and new in seen_claims[chain]:
            issue("invalid_reversal", key, "Restoring an earlier assertion requires an explicit compensating reversal")
        if old:
            seen_claims[chain].add(old)
        if new:
            seen_claims[chain].add(new)
        current_claim[chain] = new
        prior.add(key)
    return sorted(result, key=json_text)


def _collect_strings(node, out_strings: list[str], seen_strings: set[str]) -> None:
    stack = [node]
    while stack:
        cur = stack.pop()
        t = type(cur)
        if t is str:
            if cur not in seen_strings:
                seen_strings.add(cur)
                out_strings.append(cur)
        elif isinstance(cur, str):
            s = str(cur)
            if s not in seen_strings:
                seen_strings.add(s)
                out_strings.append(s)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, dict):
            stack.extend(cur.values())


def build_text_audit_cache(assertions, chunk_size: int = 8192) -> dict[str, tuple[bool, list[tuple[int, int]], bool] | None]:
    """Batch-audit all unique string leaves across assertion `value_json` trees in bounded chunks."""
    if native_inspect is not _ORIG_NATIVE_INSPECT:
        return {}
    unique_texts: list[str] = []
    seen: set[str] = set()
    for assertion in assertions:
        _collect_strings(assertion.get("value_json"), unique_texts, seen)
    audit_cache: dict[str, tuple[bool, list[tuple[int, int]], bool] | None] = {}
    for start in range(0, len(unique_texts), chunk_size):
        chunk = unique_texts[start : start + chunk_size]
        for text, audited in zip(chunk, native_audit_batch(chunk)):
            audit_cache[text] = audited
    return audit_cache


def batch_claim_revisions(assertions, chunk_size: int = 4096) -> list[str]:
    """Compute canonical claim_revision digests in bounded batches via Rust host helper."""
    payloads = [
        ({k: v for k, v in a.items() if k != "claim_revision_sha256"} if "claim_revision_sha256" in a else a)
        for a in assertions
    ]
    out: list[str] = []
    for start in range(0, len(payloads), chunk_size):
        out.extend(native_batch_canonical_json_sha256(payloads[start : start + chunk_size]))
    return out


def unicode_findings(assertion, exceptions=(), decisions=(), *, _audit_cache=None, _revision=None):
    """Inspect original decoded strings; Rust owns normalization and orthography.

    Scalar positions are zero-based. Non-NFC exceptions identify the complete
    original scalar sequence at position zero. Controls are matched individually.
    Numeric count claims require their related text assertion at the caller's
    dependency-validation layer; this API never guesses a text from a count.
    """
    assertion_id = assertion.get("assertion_id")
    value = assertion.get("value_json")
    revision = claim_revision(assertion) if _revision is None else _revision
    result, anomalies = [], []

    def issue(code, reason, positions=()):
        result.append(_finding(code, assertion_id, reason, positions, assertion_id))

    if _audit_cache is None and isinstance(value, (dict, list)):
        _audit_cache = build_text_audit_cache((assertion,))

    def inspect(text):
        if native_inspect is not _ORIG_NATIVE_INSPECT:
            invalid = [i for i, scalar in enumerate(text) if 0xD800 <= ord(scalar) <= 0xDFFF]
            if invalid:
                issue("invalid_scalar", "Lone surrogates are not Unicode scalars", invalid)
                return None
            report = native_inspect(text)
            if not report["is_nfc"]:
                anomalies.append(("non_nfc_original", text, 0, list(map(ord, text))))
            for position, scalar in enumerate(text):
                cp = ord(scalar)
                if is_intentional_control(cp):
                    anomalies.append(("intentional_control", text, position, [cp]))
            if any(letter["classification"] == "other" and any(0x0B80 <= ord(c) <= 0x0BDF for c in letter["text"])
                   for letter in report["letters"]):
                issue("invalid_orthography", "Rust classified a Tamil-containing cluster as other")
            return report
        cached = _audit_cache.get(text) if _audit_cache is not None else None
        if cached is not None or (_audit_cache is not None and text in _audit_cache):
            audited = cached
        else:
            audited = native_audit_batch((text,))[0]
        if audited is None:
            invalid = [i for i, scalar in enumerate(text) if 0xD800 <= ord(scalar) <= 0xDFFF]
            issue("invalid_scalar", "Lone surrogates are not Unicode scalars", invalid)
            return None
        is_nfc, ctrls, other_tamil = audited
        if not is_nfc:
            anomalies.append(("non_nfc_original", text, 0, list(map(ord, text))))
        for position, cp in ctrls:
            anomalies.append(("intentional_control", text, position, [cp]))
        # Native 'other' clusters containing Tamil alphabetic scalars are
        # review findings. The scalar filter excludes Tamil numbers/symbols,
        # which Rust legitimately classifies as 'other'. No re-segmentation.
        if other_tamil:
            issue("invalid_orthography", "Rust classified a Tamil-containing cluster as other")
        return audited

    # Registered claim shapes are validated elsewhere. Inspect every decoded
    # string rather than treating a numeric or explicitly absent claim as text.
    def walk(node):
        if isinstance(node, str):
            inspect(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for key, item in sorted(node.items()):
                if not key.isascii() or any(0xD800 <= ord(c) <= 0xDFFF for c in key):
                    issue("invalid_value_key", "Object keys must be ASCII schema keys")
                walk(item)

    walk(value)
    used = set()
    for exception_number, exception in enumerate(exceptions):
        # Decisions authorize exceptions, not ordinary Unicode inspection. Build
        # the complete index only when an exception actually needs checking.
        if exception_number == 0:
            decision_rows = list(decisions)
            decision_index = {d.get("decision_id"): d for d in decision_rows}
            current = _current_decisions([d for d in decision_rows if d.get("assertion_id") == assertion_id])
            terminal_id = current[0].get("decision_id") if len(current) == 1 else None
        decision = decision_index.get(exception.get("decision_id"), {})
        matches = []
        for number, (kind, text, position, sequence) in enumerate(anomalies):
            if (kind == exception.get("kind") and position == exception.get("scalar_position")
                    and sequence == exception.get("scalar_sequence")
                    and hashlib.sha256(text.encode("utf-8")).hexdigest() == exception.get("value_sha256")):
                matches.append(number)
        valid = (_valid("unicode_exceptions", exception)
                 and exception.get("assertion_id") == assertion_id
                 and exception.get("claim_revision_sha256") == revision
                 and assertion.get("claim_revision_sha256") == revision
                 and _nonempty(exception.get("reason_json"))
                 and decision.get("assertion_id") == assertion_id
                 and decision.get("assertion_revision_sha256") == revision
                 and decision.get("outcome") == "accepted_human"
                 and exception.get("decision_id") == terminal_id
                 and _actor_valid(decision, human=True)
                 and len(decision_index) == len(decision_rows))
        if not valid:
            issue("invalid_unicode_exception", f"Exception {exception_number} lacks exact revision or human decision")
        elif not matches:
            # Distinguish a malformed locator/hash from a valid but unused kind.
            if any(kind == exception.get("kind") for kind, *_ in anomalies):
                issue("invalid_unicode_exception", f"Exception {exception_number} does not match original scalar position/value")
            else:
                issue("unused_unicode_exception", f"Exception {exception_number} has no corresponding anomaly")
        elif any(number in used for number in matches):
            issue("unused_unicode_exception", f"Exception {exception_number} duplicates an already consumed exception")
        else:
            used.update(matches)
    for number, (kind, _, position, sequence) in enumerate(anomalies):
        if number not in used:
            issue(kind, "Original value requires an exact reviewed Unicode exception", range(position, position + len(sequence)))
    return sorted(result, key=json_text)
