"""Readable UTF-8 storage with reversible control and literal-backslash handling."""

import json
import random

import pytest

from tools.lexicon import NAMESPACE, data_json, digest, inventory, json_text, stage


_LEGACY_AUDIT = {0x200C, 0x200D, 0xFEFF, 0x00AD, 0x2028, 0x2029}


def test_surrogate_guard_preserves_every_boundary_and_nested_keys():
    from tools.lexicon import LexiconError
    from tools.lexicon_tables import _check_no_surrogates

    valid = "".join(chr(cp) for cp in (0xD7FF, 0xE000, 0x10000, 0x10FFFF, 0x0BA4))
    _check_no_surrogates({valid: [valid, (valid,)]})
    for cp in range(0xD800, 0xE000):
        invalid = valid + chr(cp) + valid
        for document in (invalid, {"nested": [invalid]}, {invalid: "key"}):
            with pytest.raises(LexiconError, match="invalid Unicode scalar: lone surrogate"):
                _check_no_surrogates(document)


def _legacy_data_json(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "".join(f"\\u{ord(c):04x}" if ord(c) in _LEGACY_AUDIT or 0x7F <= ord(c) <= 0x9F else c for c in text)


def test_utf8_stage_preserves_content_controls_ids_and_repeatability(tmp_path):
    from tools.lexicon_tables import read_rows
    source = tmp_path / "source"
    source.mkdir()
    tamil = chr(0x0BA4) * 100
    text = tamil + chr(0x200D) + r"\u0ba4" + chr(0x1F600)
    path = source / "primary_lemmas.csv"
    path.write_text("word_id,headword_ta\n1," + text + "\n", encoding="utf-8")
    frozen_hash = digest(path)
    inv, ws = tmp_path / "inventory", tmp_path / "workspace"
    ws.mkdir()
    (ws / "dataset.toml").write_text(f'schema_version = 1\ntext_codec = "json-string-utf8-v1"\nid_namespace = "{NAMESPACE}"\n', encoding="ascii")
    inventory(source, inv)
    stage(inv, ws)
    claim = next(read_rows(ws / "assertions.csv"))
    assert json.loads(claim["value_json"])["headword_ta"] == text
    raw = (ws / "assertions.csv").read_bytes()
    assert tamil.encode("utf-8") in raw
    assert chr(0x200D).encode("utf-8") not in raw
    before = {p.name:p.read_bytes() for p in ws.glob("*.csv")}
    stage(inv, ws)
    assert before == {p.name:p.read_bytes() for p in ws.glob("*.csv")}
    assert digest(path) == frozen_hash
    assert len(data_json(text).encode("utf-8")) < len(json_text(text).encode("ascii"))


def test_data_cells_roundtrip_utf8_without_second_decoding():
    text = chr(0x0BA4) + r"\u0ba4" + chr(0x200C) + "\n" + chr(0x1F600)
    encoded = data_json(text)
    assert chr(0x0BA4) in encoded
    assert chr(0x200C) not in encoded
    assert json.loads(encoded) == text


def test_data_json_matches_legacy_across_all_controls_and_boundaries():
    control_and_boundary_cps = (
        list(range(0x00, 0x20))
        + list(range(0x7E, 0xA2))
        + [0x00AC, 0x00AD, 0x00AE, 0x200B, 0x200C, 0x200D, 0x200E, 0x2027, 0x2028, 0x2029, 0x202A, 0xFEFE, 0xFEFF, 0xFF00]
    )
    audit_cps = set(_LEGACY_AUDIT) | set(range(0x7F, 0xA0))
    for cp in control_and_boundary_cps:
        ch = chr(cp)
        payload = {"ch": ch, "wrapped": f"a{ch}b", "tamil": chr(0x0BA4) + ch + chr(0x0BAE)}
        actual = data_json(payload)
        expected = _legacy_data_json(payload)
        assert actual == expected
        assert actual.encode("utf-8") == expected.encode("utf-8")
        assert json.loads(actual) == payload
        if cp in audit_cps:
            assert ch not in actual
            assert f"\\u{cp:04x}" in actual
        elif cp >= 0x20:
            assert ch in actual


def test_data_json_matches_legacy_for_random_valid_scalar_strings_and_determinism():
    rng = random.Random(20261114)
    tamil_pool = [chr(cp) for cp in (0x0B85, 0x0B86, 0x0B87, 0x0B95, 0x0BA4, 0x0BAE, 0x0BBF, 0x0BCD)]
    audit_pool = [chr(cp) for cp in (*range(0x7F, 0xA0), *_LEGACY_AUDIT)]
    c0_pool = [chr(cp) for cp in range(0x00, 0x20)]
    supp_pool = [chr(cp) for cp in (0x10000, 0x11FC0, 0x1D11E, 0x1F600, 0x10FFFF)]
    ascii_pool = ["a", "Z", "0", " ", '"', "\\", "/", "\\" + "u200d", "\\\\" + "u0085"]

    for idx in range(200):
        parts = []
        for _ in range(rng.randint(1, 24)):
            bucket = rng.choice((tamil_pool, tamil_pool, audit_pool, c0_pool, supp_pool, ascii_pool))
            parts.append(rng.choice(bucket))
        text = "".join(parts)
        assert not any(0xD800 <= ord(c) <= 0xDFFF for c in text)
        assert data_json(text).encode("utf-8") == _legacy_data_json(text).encode("utf-8")
        assert json.loads(data_json(text)) == text

        record = {
            "z_note": text,
            "a_id": idx,
            "m_flags": [True, False, None, 1.5],
            "nested": {"k2": text + "\\", "k1": "".join(tamil_pool[:3])},
        }
        actual = data_json(record)
        expected = _legacy_data_json(record)
        assert actual == expected
        assert actual.encode("utf-8") == expected.encode("utf-8")
        assert json.loads(actual) == record

    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            data_json({"bad": bad})
