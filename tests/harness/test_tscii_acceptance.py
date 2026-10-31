"""Verify pinned TSCII source, generated fixtures and distribution data."""

import hashlib
import json

import pytest

from tools import generate_tscii_golden as source


def test_reference_and_generated_files_match():
    table = source.mappings()
    assert len(table) == 313
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
