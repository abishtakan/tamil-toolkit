"""Verify the pinned TAB mapping, generated files and documented conflicts."""
from tools import generate_tab_data as source


def test_tab_generation_and_distribution_copy():
    table = source.mappings()
    assert len(table) == 332
    assert len(source.canonical(table)) == 323
    assert (source.ROOT / "tests/golden/codec_tab.jsonl").read_text(encoding="utf-8") == source.fixtures(table)
    assert (source.ROOT / "lexicon/tab.toml").read_text(encoding="utf-8") == source.lexicon(table)
    assert (source.ROOT / "crates/tamil-codec/lexicon/tab.toml").read_bytes() == (source.ROOT / "lexicon/tab.toml").read_bytes()


def test_tab_reference_conflicts_and_aliases():
    table = source.mappings()
    assert table[bytes([0xc3])] == "\u0b95\u0bc2"
    assert bytes([0x98]) not in table
    assert source.canonical(table)["\u0b9f\u0bbf"] == bytes([0xae])
    assert source.canonical(table)["\u2022"] == bytes([0x95])
    assert table[bytes([0xca])] == table[bytes([0xa0])] == "\u00a0"
