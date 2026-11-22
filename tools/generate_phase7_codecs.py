"""Generate Phase 7B canonical TOML tables (from Azhagi+ Portable) and golden JSONL suites."""

import argparse
import hashlib
import json
import sys
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.toml_utf8 import escape_toml_utf8  # noqa: E402
AZHAGI_DIR = (
    ROOT
    / "target/codec-research/azhagi/AzhagiPlus-Porto/azXMLs/Tamil/Tamil-All-PhoneticTransliteration"
)
LEGACY_OUTPUT = ROOT / "tests/golden/codec_phase7_legacy.jsonl"
BRAILLE_OUTPUT = ROOT / "tests/golden/codec_braille.jsonl"

PROFILES = [
    ("senthamil", "Senthamil", "senthamil-cid-v1", "Stmzh"),
    ("shree_tam", "Shree-Tam", "shree-tam-cid-v1", "Shree"),
    ("softview", "Softview", "softview-amudham-cid-v1", "Amudham"),
    ("tbo", "TBO", "tbo-tboomi-cid-v1", "TBoomiS"),
]


def escape_toml_str(text: str) -> str:
    return escape_toml_utf8(text)


def build_legacy_tomls():
    uni_path = AZHAGI_DIR / "AzhagiPlus-Tamil-Unicode-PhoneticTransliteration.txt"
    uni_lines = uni_path.read_bytes().decode("utf-16").splitlines()
    summary = {}
    for slug, label, profile_id, az_name in PROFILES:
        src_path = AZHAGI_DIR / f"AzhagiPlus-Tamil-{az_name}-PhoneticTransliteration.txt"
        raw = src_path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        grid = raw.decode("utf-16").splitlines()
        pairs = {}
        rev = {}
        for u_line, f_line in zip(uni_lines, grid):
            u_toks, f_toks = u_line.split(), f_line.split()
            if len(u_toks) != len(f_toks):
                continue
            for u, f in zip(u_toks, f_toks):
                u_nfc = unicodedata.normalize("NFC", u)
                if not all(0x0B80 <= ord(c) <= 0x0BFF for c in u_nfc):
                    continue
                if len(u_nfc) == 1 and (
                    0x0BBE <= ord(u_nfc) <= 0x0BCD or 0x0BE6 <= ord(u_nfc) <= 0x0BEF
                ):
                    continue
                cids = tuple(ord(c) for c in f)
                if len(cids) > 3:
                    continue
                if cids in pairs or u_nfc in rev:
                    continue
                pairs[cids] = u_nfc
                rev[u_nfc] = cids

        lines = [
            f"# {label} CID profile projected from Azhagi+ Portable ({src_path.name})",
            "# See docs/specs/codec-phase7-legacy.md for provenance and contract.",
            f'profile = "{profile_id}"',
            f'source = "Azhagi+ Portable {src_path.name}"',
            'source_url = "https://www.azhagi.com/portable"',
            f'source_sha256 = "{sha}"',
            "max_key_cids = 3",
            "",
        ]
        for cids, u_nfc in sorted(pairs.items()):
            cid_list = ", ".join(f"0x{c:04X}" for c in cids)
            lines.append("[[mappings]]")
            lines.append(f"cids = [{cid_list}]")
            lines.append(f'unicode = "{escape_toml_str(u_nfc)}"')
            lines.append("")
        out_path = ROOT / f"lexicon/{slug}.toml"
        out_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        summary[slug] = (profile_id, sha, len(pairs))
    return summary


def row(identifier, op, inp, expected, source, tags, *, error=False, nfd=False):
    obj = {
        "id": identifier,
        "op": op,
        "input": inp,
        "expected_error" if error else "expected": expected,
        "dialect": "COMMON",
        "tags": tags,
        "source": source,
    }
    if nfd:
        obj["unicode_exceptions"] = [
            {
                "path": "/input/text",
                "kind": "non_nfc",
                "reason": "Intentional NFD input verifies encoder NFC normalization.",
            }
        ]
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


def generate_legacy_golden():
    lines = []
    for slug, label, profile_id, _ in PROFILES:
        data = tomllib.loads((ROOT / f"lexicon/{slug}.toml").read_text(encoding="utf-8"))
        assert data["profile"] == profile_id
        src = f"{data['source']}, SHA-256 {data['source_sha256']}; docs/specs/codec-phase7-legacy.md"
        contract_src = f"{label} CID profile contract; docs/specs/codec-phase7-legacy.md"
        rev = {m["unicode"]: m["cids"] for m in data["mappings"]}

        # Every single mapping: decode + encode
        for m in data["mappings"]:
            codes = m["cids"]
            key = "".join(f"{c:04x}" for c in codes)
            lines.append(
                row(
                    f"codec_{slug}_dec_{key}",
                    f"{slug}_codes_to_unicode",
                    {"codes": codes},
                    m["unicode"],
                    src,
                    [slug, "mapping", "decode"],
                )
            )
            lines.append(
                row(
                    f"codec_{slug}_enc_{key}",
                    f"unicode_to_{slug}_codes",
                    {"text": m["unicode"]},
                    codes,
                    src,
                    [slug, "mapping", "encode"],
                )
            )

        # Phrase round-trip using Tamil word "தமிழ்" (\u0ba4 \u0bae\u0bbf \u0bb4\u0bcd)
        tamil_parts = ["\u0ba4", "\u0bae\u0bbf", "\u0bb4\u0bcd"]
        if all(p in rev for p in tamil_parts):
            word = "".join(tamil_parts)
            word_codes = [c for p in tamil_parts for c in rev[p]]
            word_text = "".join(chr(c) for c in word_codes)
            lines.append(
                row(
                    f"codec_{slug}_word_tamil_dec",
                    f"{slug}_text_to_unicode",
                    {"text": word_text},
                    word,
                    src,
                    [slug, "word", "legacy_text"],
                )
            )
            lines.append(
                row(
                    f"codec_{slug}_word_tamil_enc",
                    f"unicode_to_{slug}_text",
                    {"text": word},
                    word_text,
                    src,
                    [slug, "word", "legacy_text"],
                )
            )

        # NFD encode, preserve unknown, strict errors
        if "\u0ba4\u0bca" in rev:
            lines.append(
                row(
                    f"codec_{slug}_nfd_enc",
                    f"unicode_to_{slug}_codes",
                    {"text": unicodedata.normalize("NFD", "\u0ba4\u0bca")},
                    rev["\u0ba4\u0bca"],
                    contract_src,
                    [slug, "nfc"],
                    nfd=True,
                )
            )
        lines.extend(
            [
                row(
                    f"codec_{slug}_preserve_unknown",
                    f"{slug}_codes_to_unicode",
                    {"codes": [0x2603], "errors": "preserve"},
                    "\u2603",
                    contract_src,
                    [slug, "preserve"],
                ),
                row(
                    f"codec_{slug}_unmapped_strict",
                    f"{slug}_codes_to_unicode",
                    {"codes": [0x2603]},
                    f"unsupported {label} code at offset 0: U+2603",
                    contract_src,
                    [slug, "error"],
                    error=True,
                ),
                row(
                    f"codec_{slug}_surrogate_err",
                    f"{slug}_codes_to_unicode",
                    {"codes": [0xD800]},
                    f"invalid {label} code unit at offset 0: 0xD800",
                    contract_src,
                    [slug, "error"],
                    error=True,
                ),
                row(
                    f"codec_{slug}_unencodable_err",
                    f"unicode_to_{slug}_codes",
                    {"text": "\U0001f642"},
                    f"unsupported Unicode scalar for {label} at NFC byte 0: U+1F642",
                    contract_src,
                    [slug, "error"],
                    error=True,
                ),
            ]
        )
    return "\n".join(lines) + "\n"


def generate_braille_golden():
    data = tomllib.loads((ROOT / "lexicon/braille.toml").read_text(encoding="utf-8"))
    src = f"{data['source']}; docs/specs/codec-braille.md"
    pulli = data["pulli_cell"]
    space = data["space_cell"]
    vowels = {v["independent"]: v["cell"] for v in data["vowels"]}
    dep_vowels = {v["dependent"]: v["cell"] for v in data["vowels"] if v["dependent"]}
    cons = {c["unicode"]: c["cell"] for c in data["consonants"]}

    def enc(text: str) -> str:
        s = unicodedata.normalize("NFC", text)
        out = []
        i = 0
        while i < len(s):
            if s.startswith("\u0b95\u0bcd\u0bb7\u0bcd", i):
                out.append(pulli + data["ksha_cell"])
                i += 4
            elif s.startswith("\u0b95\u0bcd\u0bb7", i):
                out.append(data["ksha_cell"])
                i += 3
                if i < len(s) and s[i] in dep_vowels:
                    out.append(dep_vowels[s[i]])
                    i += 1
            elif s[i] in cons:
                c = cons[s[i]]
                i += 1
                if i < len(s) and s[i] == "\u0bcd":
                    out.append(pulli + c)
                    i += 1
                elif i < len(s) and s[i] in dep_vowels:
                    out.append(c + dep_vowels[s[i]])
                    i += 1
                else:
                    out.append(c)
            elif s[i] in vowels:
                out.append(vowels[s[i]])
                i += 1
            elif s[i] == data["aytham_unicode"]:
                out.append(data["aytham_cell"])
                i += 1
            elif s[i] == " ":
                out.append(space)
                i += 1
            elif s[i] in "\t\r\n":
                out.append(s[i])
                i += 1
            else:
                raise ValueError(f"cannot encode {s[i]!r}")
        return "".join(out)

    lines = []
    # All 12 independent vowels + Aytham
    for idx, v in enumerate(data["vowels"]):
        u, b = v["independent"], v["cell"]
        lines.append(row(f"codec_braille_v_{idx:02}_enc", "unicode_to_braille", {"text": u}, b, src, ["braille", "vowel", "encode"]))
        lines.append(row(f"codec_braille_v_{idx:02}_dec", "braille_to_unicode", {"text": b}, u, src, ["braille", "vowel", "decode"]))
    lines.append(row("codec_braille_aytham_enc", "unicode_to_braille", {"text": "\u0b83"}, data["aytham_cell"], src, ["braille", "aytham", "encode"]))
    lines.append(row("codec_braille_aytham_dec", "braille_to_unicode", {"text": data["aytham_cell"]}, "\u0b83", src, ["braille", "aytham", "decode"]))

    # All 23 consonants (inherent a + pulli mei)
    for idx, c in enumerate(data["consonants"]):
        u, b = c["unicode"], c["cell"]
        lines.append(row(f"codec_braille_c_{idx:02}_enc", "unicode_to_braille", {"text": u}, b, src, ["braille", "consonant", "encode"]))
        lines.append(row(f"codec_braille_c_{idx:02}_dec", "braille_to_unicode", {"text": b}, u, src, ["braille", "consonant", "decode"]))
        um, bm = u + "\u0bcd", pulli + b
        lines.append(row(f"codec_braille_m_{idx:02}_enc", "unicode_to_braille", {"text": um}, bm, src, ["braille", "mei", "encode"]))
        lines.append(row(f"codec_braille_m_{idx:02}_dec", "braille_to_unicode", {"text": bm}, um, src, ["braille", "mei", "decode"]))

    # Ksha + Ksha pulli + Ksha uyirmei
    for tag, sample in [("ksha", "\u0b95\u0bcd\u0bb7"), ("ksh_mei", "\u0b95\u0bcd\u0bb7\u0bcd"), ("kshi", "\u0b95\u0bcd\u0bb7\u0bbf")]:
        b = enc(sample)
        lines.append(row(f"codec_braille_{tag}_enc", "unicode_to_braille", {"text": sample}, b, src, ["braille", "conjunct", "encode"]))
        lines.append(row(f"codec_braille_{tag}_dec", "braille_to_unicode", {"text": b}, sample, src, ["braille", "conjunct", "decode"]))

    # All 11 dependent vowel signs on ka
    for idx, dep in enumerate(dep_vowels.keys()):
        sample = "\u0b95" + dep
        b = enc(sample)
        lines.append(row(f"codec_braille_ka_v_{idx:02}_enc", "unicode_to_braille", {"text": sample}, b, src, ["braille", "uyirmei", "encode"]))
        lines.append(row(f"codec_braille_ka_v_{idx:02}_dec", "braille_to_unicode", {"text": b}, sample, src, ["braille", "uyirmei", "decode"]))

    # Real Tamil words and sentences
    phrases = [
        ("tamil", "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"),
        ("vanakkam", "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd"),
        ("sentence", "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd \u0bae\u0bca\u0bb4\u0bbf \u0b87\u0ba9\u0bbf\u0ba4\u0bc1"),
        ("multiline", "\u0b85\u0bae\u0bcd\u0bae\u0bbe\n\u0b85\u0baa\u0bcd\u0baa\u0bbe"),
    ]
    for tag, phrase in phrases:
        b = enc(phrase)
        lines.append(row(f"codec_braille_phrase_{tag}_enc", "unicode_to_braille", {"text": phrase}, b, src, ["braille", "phrase", "encode"]))
        lines.append(row(f"codec_braille_phrase_{tag}_dec", "braille_to_unicode", {"text": b}, phrase, src, ["braille", "phrase", "decode"]))

    # NFD equivalence, preserve, and strict errors
    lines.extend(
        [
            row(
                "codec_braille_nfd_enc",
                "unicode_to_braille",
                {"text": unicodedata.normalize("NFD", "\u0ba4\u0bca")},
                enc("\u0ba4\u0bca"),
                src,
                ["braille", "nfc"],
                nfd=True,
            ),
            row(
                "codec_braille_enc_preserve",
                "unicode_to_braille",
                {"text": "\u0ba4!", "errors": "preserve"},
                enc("\u0ba4") + "!",
                src,
                ["braille", "preserve"],
            ),
            row(
                "codec_braille_dec_preserve",
                "braille_to_unicode",
                {"text": enc("\u0ba4") + "!", "errors": "preserve"},
                "\u0ba4!",
                src,
                ["braille", "preserve"],
            ),
            row(
                "codec_braille_enc_strict_err",
                "unicode_to_braille",
                {"text": "A"},
                "unsupported Unicode scalar for Braille at NFC byte 0: U+0041",
                src,
                ["braille", "error"],
                error=True,
            ),
            row(
                "codec_braille_dec_strict_err",
                "braille_to_unicode",
                {"text": "A"},
                "unsupported Braille scalar at character 0: U+0041",
                src,
                ["braille", "error"],
                error=True,
            ),
            row(
                "codec_braille_dec_dangling_pulli",
                "braille_to_unicode",
                {"text": pulli},
                "invalid Braille pulli sequence at character 0",
                src,
                ["braille", "error"],
                error=True,
            ),
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-azhagi", action="store_true", help="Regenerate lexicon TOMLs from Azhagi+ Portable")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.from_azhagi:
        info = build_legacy_tomls()
        for k, v in info.items():
            print(f"lexicon/{k}.toml: profile={v[0]} sha256={v[1]} keys={v[2]}")
    legacy_content = generate_legacy_golden()
    braille_content = generate_braille_golden()
    if args.check:
        if LEGACY_OUTPUT.read_text(encoding="utf-8") != legacy_content:
            raise SystemExit("codec_phase7_legacy.jsonl differs")
        if BRAILLE_OUTPUT.read_text(encoding="utf-8") != braille_content:
            raise SystemExit("codec_braille.jsonl differs")
    else:
        LEGACY_OUTPUT.write_text(legacy_content, encoding="utf-8", newline="\n")
        BRAILLE_OUTPUT.write_text(braille_content, encoding="utf-8", newline="\n")
    print(f"{LEGACY_OUTPUT.name}: {len(legacy_content.splitlines())} vectors")
    print(f"{BRAILLE_OUTPUT.name}: {len(braille_content.splitlines())} vectors")
