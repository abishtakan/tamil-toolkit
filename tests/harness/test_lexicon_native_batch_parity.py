from __future__ import annotations

from decimal import Decimal
from enum import IntEnum
import hashlib
from pathlib import Path
import subprocess
import sys
import pytest

from tamil_toolkit import _native, execute
from tools.lexicon import LexiconError, allocate_id, data_json, inventory, json_text, native_inspect
from tools.lexicon_cldf import _validate_cldf_offline, export_cldf
from tools.lexicon_packs import _check_public_text_safety
from tools.lexicon_proof import prove
from tools.lexicon_review import claim_revision, eligibility, evidence_hash, unicode_findings
from tools.lexicon_stage import _stage_claim_revision, stage
from tools.lexicon_tables import (
    _check_no_surrogates,
    is_intentional_control,
    validate_row,
    write_rows,
)
from tools.lexicon_validate import check_curated_csv


def _scalars(*codepoints: int) -> str:
    """Build intentional scalar edge cases without hidden source characters."""
    return "".join(chr(cp) for cp in codepoints)


class _SampleIntEnum(IntEnum):
    ONE = 1


class _CustomDict(dict):
    pass


class _CustomList(list):
    pass


def _ref_audit_text(text: str):
    if any(0xD800 <= ord(c) <= 0xDFFF for c in text):
        return None
    report = native_inspect(text)
    controls = [[pos, ord(ch)] for pos, ch in enumerate(text) if is_intentional_control(ord(ch))]
    other_tamil = any(
        letter["classification"] == "other" and any(0x0B80 <= ord(c) <= 0x0BDF for c in letter["text"])
        for letter in report["letters"]
    )
    return (bool(report["is_nfc"]), controls, bool(other_tamil))


def test_native_batch_audit_tamil_texts_exact_parity() -> None:
    samples = [
        "",
        "plain ascii 123",
        "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd",  # தமிழ் NFC
        "\u0bb8\u0bcd\u0bb0\u0bc0",  # ஸ்ரீ (TN/SL)
        "\u0bb6\u0bcd\u0bb0\u0bc0",  # ஶ்ரீ
        _scalars(0x0B95, 0x0BC6, 0x0BBE),  # NFD கொ (க + ெ + ா)
        _scalars(0x0B92, 0x0BD7),  # NFD ஔ
        _scalars(0x0B95, 0x200D, 0x0B9A),  # ZWJ
        _scalars(0x0B95, 0x200C, 0x0B9A),  # ZWNJ
        "a\u00adb\u2028c\u2029d\ufeff",  # intentional audit controls
        "\u0bcd",  # standalone pulli -> Tamil other cluster
        "\u0b82",  # Tamil anusvara -> other cluster
        "\U0001f600 \u0915",  # non-Tamil astral + Devanagari
        "\ud800",  # lone high surrogate
        "prefix\udfff",  # lone low surrogate
    ]
    got = _native.batch_audit_tamil_texts(samples)
    assert len(got) == len(samples)
    for text, actual in zip(samples, got):
        expected = _ref_audit_text(text)
        if expected is None:
            assert actual is None, f"expected None surrogate sentinel for {text!r}, got {actual!r}"
        else:
            exp_nfc, exp_ctrls, exp_other = expected
            act_nfc, act_ctrls, act_other = actual
            assert act_nfc is exp_nfc
            assert [list(pair) for pair in act_ctrls] == exp_ctrls
            assert act_other is exp_other


def test_native_batch_canonical_json_sha256_and_data_json_parity() -> None:
    standard_rows = [
        None,
        True,
        False,
        0,
        -1,
        2**62,
        -(2**62),
        "",
        "hello",
        _scalars(0x0000, 0x0008, 0x0009, 0x000A, 0x000C, 0x000D, 0x001F, 0x007F, 0x0080, 0x009F, 0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF, 0x0B85, 0x1F600),
        {"z": [1, True, None, "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"], "a": {"k": _scalars(0x007F, 0x200D)}},
        [{"b": 2, "a": 1}, []],
    ]
    got_hashes = _native.batch_canonical_json_sha256(standard_rows)
    got_data = _native.batch_data_json(standard_rows)
    for row, h, d in zip(standard_rows, got_hashes, got_data):
        exp_h = hashlib.sha256(json_text(row).encode("ascii")).hexdigest()
        exp_d = data_json(row)
        assert h == exp_h
        assert d == exp_d

    fallback_rows = [
        -0.0,
        1.5,
        1e308,
        float("nan"),
        float("inf"),
        10**500,
        2**63,
        _SampleIntEnum.ONE,
        (1, 2),
        _CustomDict({"a": 1}),
        _CustomList([1]),
        {1: "non-str-key"},
        Decimal("1.25"),
        "bad\ud800",
        {"k": ["\udfff"]},
    ]
    assert _native.batch_canonical_json_sha256(fallback_rows) == [None] * len(fallback_rows)
    assert _native.batch_data_json(fallback_rows) == [None] * len(fallback_rows)


def test_native_batch_check_no_surrogates_parity() -> None:
    valid_standard = [
        {"a": "tamil \u0ba4\u0bae\u0bbf\u0bb4\u0bcd", "b": [1, None, True, 1.5, 10**500]},
    ]
    assert _native.batch_check_no_surrogates(valid_standard) == [True]

    non_standard = [
        {"a": (1, 2)},
        {"a": _CustomDict({"x": 1})},
        {"a": {1: "v"}},
        {"a": float("nan")},
        {"a": _SampleIntEnum.ONE},
    ]
    assert _native.batch_check_no_surrogates(non_standard) == [False] * len(non_standard)

    for bad in [
        {"a": "\ud800"},
        {"\udfff": "x"},
        {"a": [{"b": ["\udc00"]}]},
        {"a": _CustomDict({"x": "\ud800"})},
    ]:
        with pytest.raises(ValueError, match="surrogate"):
            _native.batch_check_no_surrogates([bad])


def test_native_batch_cyclic_containers_fail_without_hanging() -> None:
    script = """
from tamil_toolkit import _native
for kind in ('list', 'dict'):
    cyclic = [] if kind == 'list' else {}
    if kind == 'list':
        cyclic.append(cyclic)
    else:
        cyclic['self'] = cyclic
    try:
        _native.batch_check_no_surrogates([cyclic])
    except RecursionError:
        pass
    else:
        raise AssertionError('cycle must fail')
shared = ['same']
assert _native.batch_check_no_surrogates([[shared, shared]]) == [True]
"""
    subprocess.run([sys.executable, "-c", script], check=True, timeout=5)


def test_native_batch_dict_subclass_items_accepts_pair_iterables() -> None:
    class ListPairs(dict):
        def items(self):
            return [[key, value] for key, value in super().items()]

    assert _native.batch_check_no_surrogates([ListPairs(a="safe")]) == [False]
    with pytest.raises(ValueError, match="surrogate"):
        _native.batch_check_no_surrogates([ListPairs(a="\ud800")])


def test_batch_adapters_use_reference_on_unoptimized_builds(monkeypatch) -> None:
    from tools.lexicon import (
        native_batch_canonical_json_sha256, native_batch_data_json,
        native_batch_check_no_surrogates,
    )

    rows = [{"text": _scalars(0x0B95, 0x200D), "n": 7}, {"big": 10**500}]
    expected_json = [data_json(row) for row in rows]
    expected_hashes = [hashlib.sha256(json_text(row).encode("ascii")).hexdigest() for row in rows]
    hash_batch = _native.batch_canonical_json_sha256
    json_batch = _native.batch_data_json
    scalar_batch = _native.batch_check_no_surrogates
    calls = []

    def record_hash(values):
        calls.append("hash")
        return hash_batch(values)

    def record_json(values):
        calls.append("json")
        return json_batch(values)

    def record_scalars(values):
        calls.append("scalars")
        return scalar_batch(values)

    monkeypatch.setattr(_native, "batch_canonical_json_sha256", record_hash)
    monkeypatch.setattr(_native, "batch_data_json", record_json)
    monkeypatch.setattr(_native, "batch_check_no_surrogates", record_scalars)
    monkeypatch.setattr(_native, "HOST_BATCH_OPTIMIZED", False, raising=False)
    assert native_batch_canonical_json_sha256(rows) == expected_hashes
    assert native_batch_data_json(rows) == expected_json
    assert native_batch_check_no_surrogates(rows) is None
    assert calls == []
    monkeypatch.setattr(_native, "HOST_BATCH_OPTIMIZED", True)
    assert native_batch_canonical_json_sha256(rows) == expected_hashes
    assert native_batch_data_json(rows) == expected_json
    assert native_batch_check_no_surrogates(rows) == [True, True]
    assert calls == ["hash", "json", "scalars"]


def test_unicode_findings_and_safety_preserve_edge_cases() -> None:
    nfd_text = _scalars(0x0B95, 0x0BC6, 0x0BBE)
    aid_nfd = allocate_id("ast", None, "test-nfd") if False else "ast_00000000000000000000000000000001"
    claim_base = {
        "assertion_id": aid_nfd,
        "subject_kind": "sense",
        "subject_id": "sen_00000000000000000000000000000001",
        "property_code": "definition",
        "value_json": {"txt": nfd_text, "ctrl": _scalars(0x0061, 0x200D, 0x0062), "bad": "\u0bcd"},
        "value_state": "known",
        "origin": "verbatim_source",
        "source_fidelity_state": "verified",
        "ambiguity_state": "unambiguous",
        "convention_reference": None,
        "algorithm_reference": None,
        "imported_status_json": None,
        "imported_confidence_json": None,
        "canonical_notes_json": None,
    }
    claim_base["claim_revision_sha256"] = claim_revision(claim_base)
    findings = unicode_findings(claim_base)
    codes = [f["issue_code"] for f in findings]
    assert "non_nfc_original" in codes
    assert "intentional_control" in codes
    assert "invalid_orthography" in codes

    claim_surrogate = dict(claim_base, value_json="\ud800bad")
    claim_surrogate["claim_revision_sha256"] = claim_revision(claim_surrogate)
    surrogate_findings = unicode_findings(claim_surrogate)
    assert any(f["issue_code"] == "invalid_scalar" and f["scalar_positions"] == [0] for f in surrogate_findings)

    safety_issues = []
    _check_public_text_safety(
        "clean " + nfd_text + _scalars(0x0020, 0x200D),
        "doc",
        "notices/test.md",
        lambda code, subj, reason: safety_issues.append((code, subj, reason)),
    )
    assert len(safety_issues) == 1
    assert safety_issues[0][0] == "NON_NFC_NOTICE"


def test_python_pipeline_json_stage_validate_and_edge_fallback(tmp_path: Path) -> None:
    edge_rows = [
        {"k": "bigint", "v": 10**500},
        {"k": "negzero", "v": -0.0},
        {"k": "bigfloat", "v": 1e308},
        {"k": "controls", "v": _scalars(0x007F, 0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF, 0x1F600)},
    ]
    for row in edge_rows:
        assert _check_no_surrogates(row, "edge") is True
    assert _stage_claim_revision(
        "ast_00000000000000000000000000000001",
        "entry",
        "ent_00000000000000000000000000000001",
        "definition",
        json_text({"big": 10**500, "z": -0.0}),
        None,
        None,
    ) == hashlib.sha256(
        json_text(
            {
                "algorithm_reference": None,
                "ambiguity_state": "unknown",
                "assertion_id": "ast_00000000000000000000000000000001",
                "convention_reference": None,
                "imported_confidence_json": None,
                "imported_status_json": None,
                "origin": "verbatim_source",
                "property_code": "definition",
                "source_fidelity_state": "unknown",
                "subject_id": "ent_00000000000000000000000000000001",
                "subject_kind": "entry",
                "value_json": json_text({"big": 10**500, "z": -0.0}),
                "value_state": "known",
            }
        ).encode("ascii")
    ).hexdigest()

    # Existing core operations stay untouched (no new public dispatcher operation added unasked).
    ops_resp = execute({"op": "inspect_tamil_string", "input": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"})
    assert ops_resp["is_nfc"] is True


def test_cldf_offline_validator_still_detects_fk_violation(tmp_path: Path) -> None:
    """Ensure removing redundant check_referential_integrity never weakens invalid FK detection."""
    repo_root = Path(__file__).resolve().parents[2]
    cldf_dir = tmp_path / "cldf_core"
    rep = export_cldf(
        canonical=repo_root / "lexicon/packs/regional",
        pack="regional",
        output=cldf_dir,
        check=True,
    )
    assert rep["cldf_valid"] is True
    assert rep["roundtrip_ok"] is True

    # Corrupt a foreign key in senses.csv (SenseTable Entry_ID -> missing entry).
    senses_path = cldf_dir / "senses.csv"
    lines = senses_path.read_text(encoding="utf-8").splitlines(keepends=True)
    header = lines[0].rstrip("\n").split(",")
    eid_idx = header.index("Entry_ID")
    cols = lines[1].rstrip("\n").split(",")
    cols[eid_idx] = "ent_ffffffffffffffffffffffffffffffff"
    lines[1] = ",".join(cols) + "\n"
    senses_path.write_text("".join(lines), encoding="utf-8")

    ok, findings = _validate_cldf_offline(cldf_dir, repo_root / "schemas/cldf")
    assert ok is False
    assert findings
