"""Verify TAM data generation and monolingual byte behavior."""
from tools import generate_tam_data as source
from tools import generate_tab_data as tab


def test_tam_generation_and_distribution_copy():
    table = source.mappings()
    assert len(table) == 407
    assert len(source.canonical(table)) == 331
    assert (source.ROOT / "tests/golden/codec_tam.jsonl").read_text(encoding="utf-8") == source.fixtures(table)
    assert (source.ROOT / "lexicon/tam.toml").read_text(encoding="utf-8") == source.lexicon(table)
    assert (source.ROOT / "crates/tamil-codec/lexicon/tam.toml").read_bytes() == (source.ROOT / "lexicon/tam.toml").read_bytes()


def test_monolingual_assignments_and_undefined_bytes():
    table = source.mappings()
    assert table[bytes([0x41])] == "\u0b95\u0bbf"
    assert table[bytes([0x73])] == "\u0bf3"
    assert table[bytes([0x82])] == "\u0b95\u0bcd"
    assert table[bytes([0xad])] == "\u0bfa"
    assert all(bytes([byte]) not in table for byte in (0x80, 0x81, 0x8d, 0x8e, 0x8f, 0x90, 0x9d, 0x9e))
    assert all(table[key] == value for key, value in tab.mappings().items())
    assert source.canonical(table)["\u0b95\u0bbf"] == bytes([0x41])
