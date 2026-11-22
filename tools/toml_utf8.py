"""Canonical UTF-8 Tamil TOML string formatter, converter, and validator.

Policy (docs/decisions/lexicon-text-storage.md):
- Canonical `lexicon/*.toml` files use UTF-8 without BOM and LF line endings.
- Assigned Tamil-block characters (U+0B80..U+0BFF) are stored as literal NFC
  UTF-8, EXCEPT detached Tamil combining marks (U+0B82, U+0BBE..U+0BC2,
  U+0BC6..U+0BC8, U+0BCA..U+0BCD, U+0BD7) that are not preceded in the same
  contiguous Tamil letter-and-mark run by a Tamil letter.
- Non-Tamil Unicode (e.g. Braille U+2800..U+28FF, Tamil Supplement
  U+11FC0..U+11FFF, NBSP U+00A0, traditional minus U+2212, controls) stays
  explicitly escaped as \\uXXXX / \\UXXXXXXXX.
"""

from __future__ import annotations

import re
import tomllib
import unicodedata
from pathlib import Path

DETACHED_TAMIL_MARKS = frozenset(
    {
        0x0B82,
        0x0BBE,
        0x0BBF,
        0x0BC0,
        0x0BC1,
        0x0BC2,
        0x0BC6,
        0x0BC7,
        0x0BC8,
        0x0BCA,
        0x0BCB,
        0x0BCC,
        0x0BCD,
        0x0BD7,
    }
)

_TOML_ESCAPE_RE = re.compile(r"\\(?:u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8})|([\"\\btnfr]))")


def is_tamil_block(cp: int) -> bool:
    return 0x0B80 <= cp <= 0x0BFF


def is_tamil_mark(cp: int) -> bool:
    return cp in DETACHED_TAMIL_MARKS


def is_tamil_letter(ch: str) -> bool:
    cp = ord(ch)
    return is_tamil_block(cp) and not is_tamil_mark(cp) and unicodedata.category(ch).startswith("L")


def escape_toml_utf8(text: str) -> str:
    """Format the interior of a TOML basic string using the canonical UTF-8 Tamil policy."""
    if not unicodedata.is_normalized("NFC", text):
        raise ValueError(f"non-NFC Tamil TOML string: {text!r}")
    out: list[str] = []
    in_tamil_letter_run = False
    for ch in text:
        cp = ord(ch)
        if is_tamil_letter(ch):
            out.append(ch)
            in_tamil_letter_run = True
        elif is_tamil_mark(cp):
            if in_tamil_letter_run:
                out.append(ch)
            else:
                out.append(f"\\u{cp:04X}")
        elif is_tamil_block(cp):
            out.append(ch)
            in_tamil_letter_run = False
        else:
            in_tamil_letter_run = False
            if ch == '"':
                out.append('\\"')
            elif ch == "\\":
                out.append("\\\\")
            elif ch == "\b":
                out.append("\\b")
            elif ch == "\t":
                out.append("\\t")
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\f":
                out.append("\\f")
            elif ch == "\r":
                out.append("\\r")
            elif 0x20 <= cp <= 0x7E:
                out.append(ch)
            elif cp <= 0xFFFF:
                out.append(f"\\u{cp:04X}")
            else:
                out.append(f"\\U{cp:08X}")
    return "".join(out)


def format_toml_string(text: str) -> str:
    """Return a quoted TOML basic string formatted with the canonical UTF-8 Tamil policy."""
    return f'"{escape_toml_utf8(text)}"'


def iter_toml_basic_strings(source: str):
    """Yield (start, end, line_number) spans of single-line TOML basic string tokens."""
    i = 0
    n = len(source)
    line = 1
    while i < n:
        ch = source[i]
        if ch == "\n":
            line += 1
            i += 1
        elif ch == "#":
            nl = source.find("\n", i)
            if nl == -1:
                break
            i = nl
        elif source.startswith('"""', i):
            i += 3
            while i < n:
                if source[i] == "\n":
                    line += 1
                    i += 1
                elif source[i] == "\\":
                    i += 2
                elif source.startswith('"""', i):
                    i += 3
                    break
                else:
                    i += 1
        elif source.startswith("'''", i):
            i += 3
            while i < n:
                if source[i] == "\n":
                    line += 1
                    i += 1
                elif source.startswith("'''", i):
                    i += 3
                    break
                else:
                    i += 1
        elif ch == "'":
            i += 1
            while i < n and source[i] != "'" and source[i] != "\n":
                i += 1
            if i < n and source[i] == "'":
                i += 1
        elif ch == '"':
            start = i
            start_line = line
            i += 1
            while i < n:
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    yield (start, i, start_line)
                    break
                elif source[i] == "\n":
                    line += 1
                    i += 1
                    break
                else:
                    i += 1
        else:
            i += 1


def convert_toml_source(source: str) -> tuple[str, int]:
    """Rewrite Tamil basic strings in a TOML document to canonical UTF-8 Tamil.

    Returns (updated_source, converted_token_count). Non-Tamil strings, comments,
    keys, literal strings, and layout are preserved verbatim.
    """
    pieces: list[str] = []
    last = 0
    converted = 0
    for start, end, _ in iter_toml_basic_strings(source):
        token = source[start:end]
        decoded = tomllib.loads(f"v = {token}")["v"]
        if any(is_tamil_block(ord(c)) for c in decoded):
            replacement = format_toml_string(decoded)
            if replacement != token:
                pieces.append(source[last:start])
                pieces.append(replacement)
                last = end
                converted += 1
    pieces.append(source[last:])
    return "".join(pieces), converted


def check_toml_file(path: Path) -> list[str]:
    """Validate UTF-8 no-BOM, LF endings, NFC, and canonical Tamil spelling in a TOML file."""
    failures: list[str] = []
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append(f"{path}: UTF-8 BOM is not permitted in lexicon TOML")
    if b"\r\n" in raw:
        failures.append(f"{path}: CRLF line endings are not permitted in lexicon TOML (use LF)")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"{path}: invalid UTF-8: {exc}"]
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        failures.append(f"{path}: invalid TOML: {exc}")
        return failures

    for start, end, line_no in iter_toml_basic_strings(text):
        token = text[start:end]
        decoded = tomllib.loads(f"v = {token}")["v"]
        if not any(is_tamil_block(ord(c)) for c in decoded):
            continue
        if not unicodedata.is_normalized("NFC", decoded):
            failures.append(f"{path}:{line_no}: decoded Tamil TOML string is not NFC")
            continue
        expected = format_toml_string(decoded)
        # Compare Tamil-only spelling: allow existing non-Tamil escape case/style if non-Tamil chars exist,
        # while strictly enforcing that every Tamil scalar matches the canonical attached/detached rule.
        if token != expected:
            # Verify whether the difference is actually in a Tamil scalar (escaped letter/attached mark or literal detached mark)
            inner = token[1:-1]
            in_run = False
            pos = 0
            token_ok = True
            while pos < len(inner):
                if inner[pos] == "\\":
                    m = _TOML_ESCAPE_RE.match(inner, pos)
                    if not m:
                        pos += 2
                        in_run = False
                        continue
                    hex4, hex8, simple = m.groups()
                    pos = m.end()
                    if simple is not None:
                        in_run = False
                        continue
                    cp = int(hex4 or hex8, 16)
                    ch = chr(cp)
                    if is_tamil_letter(ch):
                        token_ok = False
                        failures.append(
                            f"{path}:{line_no}: Tamil letter U+{cp:04X} must be literal UTF-8 in lexicon TOML"
                        )
                        in_run = True
                    elif is_tamil_mark(cp):
                        if in_run:
                            token_ok = False
                            failures.append(
                                f"{path}:{line_no}: attached Tamil mark U+{cp:04X} must be literal UTF-8 in lexicon TOML"
                            )
                    elif is_tamil_block(cp):
                        token_ok = False
                        failures.append(
                            f"{path}:{line_no}: Tamil character U+{cp:04X} must be literal UTF-8 in lexicon TOML"
                        )
                        in_run = False
                    else:
                        in_run = False
                else:
                    ch = inner[pos]
                    cp = ord(ch)
                    pos += 1
                    if is_tamil_letter(ch):
                        in_run = True
                    elif is_tamil_mark(cp):
                        if not in_run:
                            token_ok = False
                            failures.append(
                                f"{path}:{line_no}: detached Tamil mark U+{cp:04X} must be \\u{cp:04X}-escaped in lexicon TOML"
                            )
                    elif is_tamil_block(cp):
                        in_run = False
                    else:
                        in_run = False
            if not token_ok:
                continue
    return failures
