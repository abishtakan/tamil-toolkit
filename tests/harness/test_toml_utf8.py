"""Unit and compliance tests for the canonical UTF-8 Tamil TOML policy."""

from pathlib import Path
import tomllib

from tools.toml_utf8 import check_toml_file, convert_toml_source, format_toml_string

ROOT = Path(__file__).resolve().parents[2]


def test_attached_and_detached_tamil_marks():
    assert format_toml_string("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD") == '"தமிழ்"'
    assert format_toml_string("\u0BC7\u0B95\u0BBE\u0BB2\u0BCD") == '"\\u0BC7கால்"'
    assert format_toml_string("\u0BCD") == '"\\u0BCD"'
    assert format_toml_string("\u0B95\u0BCD\u0BB7\u0BBF") == '"க்ஷி"'


def test_rbnf_boundaries_keep_marks_after_syntax_escaped():
    pattern = "\u0B87\u0BB0\u0BC1\u0BAA\u0BA4[\u0BCD\u0BA4\u0BC1 >>|\u0BC1]"
    formatted = format_toml_string(pattern)
    assert formatted == '"இருபத[\\u0BCDது >>|\\u0BC1]"'
    assert tomllib.loads(f"v = {formatted}")["v"] == pattern


def test_non_tamil_escapes_and_backslashes_preserved():
    assert format_toml_string("\u2805") == '"\\u2805"'
    assert format_toml_string("\U00011FD0") == '"\\U00011FD0"'
    assert format_toml_string("\u2212") == '"\\u2212"'
    assert format_toml_string("a\\u0BA4") == '"a\\\\u0BA4"'


def test_check_toml_file_rejects_bom_crlf_and_policy_violations(tmp_path: Path):
    bom = tmp_path / "bom.toml"
    bom.write_bytes(b'\xef\xbb\xbfk = "\xe0\xae\xa4"\n')
    assert any("BOM" in e for e in check_toml_file(bom))

    crlf = tmp_path / "crlf.toml"
    crlf.write_bytes('k = "தமிழ்"\r\n'.encode("utf-8"))
    assert any("CRLF" in e for e in check_toml_file(crlf))

    escaped_letter = tmp_path / "escaped.toml"
    escaped_letter.write_bytes('k = "\\u0BA4"\n'.encode("utf-8"))
    assert any("literal UTF-8" in e for e in check_toml_file(escaped_letter))

    raw_detached = tmp_path / "detached.toml"
    raw_detached.write_bytes('k = "\u0BC7கால்"\n'.encode("utf-8"))
    assert any("detached Tamil mark" in e for e in check_toml_file(raw_detached))


def test_convert_toml_source_is_idempotent():
    src = '# comment\nword = "\\u0BA4\\u0BAE\\u0BBF\\u0BB4\\u0BCD"\nsuffix = "\\u0BC7\\u0B95\\u0BBE\\u0BB2\\u0BCD"\n'
    first, n1 = convert_toml_source(src)
    assert n1 == 2
    assert 'word = "தமிழ்"' in first
    assert 'suffix = "\\u0BC7கால்"' in first
    second, n2 = convert_toml_source(first)
    assert second == first and n2 == 0


def test_all_canonical_lexicon_tomls_pass_policy():
    tomls = sorted((ROOT / "lexicon").glob("*.toml"))
    assert len(tomls) >= 24
    for path in tomls:
        assert check_toml_file(path) == [], f"Policy failure in {path}"
