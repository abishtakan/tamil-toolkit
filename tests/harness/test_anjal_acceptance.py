"""Verify Anjal source generation, conflicts and distribution data."""
import pytest
from tools import generate_anjal_data as source


def test_anjal_generation_and_distribution_copy():
    table, ambiguous = source.mappings()
    assert len(table) == 309
    assert len(source.canonical(table)) == 302
    assert len(ambiguous) == 4
    assert (source.ROOT / "tests/golden/codec_anjal.jsonl").read_text(encoding="utf-8") == source.fixtures(table, ambiguous)
    assert (source.ROOT / "lexicon/anjal.toml").read_text(encoding="utf-8") == source.lexicon(table, ambiguous)
    assert (source.ROOT / "crates/tamil-codec/lexicon/anjal.toml").read_bytes() == (source.ROOT / "lexicon/anjal.toml").read_bytes()


def test_source_ambiguities_and_longer_unambiguous_key():
    table, ambiguous = source.mappings()
    assert set(ambiguous) == {bytes([byte]) for byte in (0xe5, 0xe6, 0xe7, 0xe8)}
    assert table[bytes.fromhex("e5f5")] == "\u0bb7\u0bbe"
    assert all(len(values) == 2 for values in ambiguous.values())
    assert chr(0x0ba3) + chr(0x0bc0) not in source.canonical(table)


def test_source_digest_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr(source, "SHA256", "0" * 64)
    with pytest.raises(ValueError, match="digest mismatch"):
        source.mappings()
