"""Verify pinned TSCII source, generated fixtures and distribution data."""

import hashlib
import json
import unicodedata

import pytest

from tools import generate_tscii_golden as source


def test_reference_and_generated_files_match():
    table = source.mappings()
    assert len(table) == 341
    assert hashlib.sha256(source.SOURCE.read_bytes()).hexdigest() == source.SHA256
    assert (source.ROOT / "tests/golden/codec_tscii_bytes.jsonl").read_text(encoding="utf-8") == source.fixtures(table)
    assert (source.ROOT / "lexicon/tscii.toml").read_text(encoding="utf-8") == source.lexicon(table)
    assert (source.ROOT / "crates/tamil-codec/lexicon/tscii.toml").read_bytes() == (source.ROOT / "lexicon/tscii.toml").read_bytes()
    reference = source.ROOT / "tests/reference/codec-tscii"
    for item in json.loads((reference / "sources.json").read_text(encoding="utf-8"))["files"]:
        assert hashlib.sha256((reference / item["file"]).read_bytes()).hexdigest() == item["sha256"]


def test_standard_alias_and_java_backslash_correction():
    table = source.mappings()
    assert table[bytes([0xad])] == table[bytes([0xfe])] == "\u0b87"
    assert table[bytes([0x88])] == "\u0b9c\u0bcd"
    assert bytes([0x5c, 0x88]) not in table
    assert bytes([0xa0]) not in table and bytes([0xff]) not in table


def test_reference_digest_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr(source, "SHA256", "0" * 64)
    with pytest.raises(ValueError, match="digest mismatch"):
        source.mappings()


def test_audited_iana_corrections():
    table = source.mappings()
    assert table[bytes.fromhex("86")] == "\u0bb9"
    assert table[bytes.fromhex("8b")] == "\u0bb9\u0bcd"
    assert bytes.fromhex("8686") not in table
    assert bytes.fromhex("8686a1") not in table
    assert bytes.fromhex("8b8b20") not in table


def test_all_iana_assigned_high_bytes_are_present():
    table = source.mappings()
    assert {byte for byte in range(0x80, 0x100) if bytes([byte]) not in table} == {0xa0, 0xff}


def test_iana_preposed_vowels_cover_every_consonant_base():
    table = source.mappings()
    bases = list(range(0x83, 0x88)) + list(range(0xb8, 0xca))
    forms = [([0xa6], [], "\u0bc6"), ([0xa7], [], "\u0bc7"),
             ([0xa8], [], "\u0bc8"), ([0xa6], [0xa1], "\u0bca"),
             ([0xa7], [0xa1], "\u0bcb"), ([0xa6], [0xaa], "\u0bcc")]
    for byte in bases:
        base = table[bytes([byte])]
        for prefix, suffix, vowel in forms:
            assert table[bytes(prefix + [byte] + suffix)] == unicodedata.normalize("NFC", base + vowel)
