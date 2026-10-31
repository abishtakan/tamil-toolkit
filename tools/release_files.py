"""Synchronize distributable data/license copies; canonical sources stay at root."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0-alpha.1"
PUBLIC = ("tamil-core", "tamil-norm", "tamil-collate", "tamil-numerals", "tamil-codec", "tamil-toolkit")
INPUTS = {
    "tamil-core": ("core.toml",),
    "tamil-collate": ("collate.toml",),
    "tamil-numerals": ("numerals.toml", "numerals-formats.toml"),
    "tamil-codec": ("bamini.toml",),
}
SUMMARIES = {
    "tamil-core": "Unicode normalization, tailored Ezhuthu iteration, Mei/Uyir composition and scalar inspection.",
    "tamil-norm": "Normalization facade for the Rust-owned Tamil toolkit.",
    "tamil-collate": "Versioned Mei-first Agara dictionary ordering and canonical sort/search keys.",
    "tamil-numerals": "Bounded TN/SL integers, exact INR/LKR amounts, rational fractions and Gregorian date formatting.",
    "tamil-codec": "Explicit Bamini decoding and strict round-trip-checked Unicode encoding.",
    "tamil-toolkit": "Unified entry point for the implemented core, normalization, collation, numerals and Bamini modules.",
}


def notices():
    text = """# Third-party notices

Original tamil-toolkit code is MIT licensed. The following upstream data and
mapping notices retain their original terms; the project MIT license does not
replace them. Generated lexicon copies are checked against the canonical data.

Unicode 17 and CLDR 49 data: https://www.unicode.org/ and https://cldr.unicode.org/
Bamini mapping sources: https://github.com/ag-sanjjeev/app-tamil-fonts-unicode-converter
and https://github.com/Pakeetharan/unicode-bamini-converter
Exact sources, revisions, digests and profile limits are recorded at:
https://github.com/abishtakan/tamil-toolkit/tree/HEAD/tests/reference
and https://github.com/abishtakan/tamil-toolkit/tree/HEAD/docs/specs

Binary distributions also include THIRD_PARTY_LICENSES.txt, generated from the
locked Rust dependency graph with the complete upstream license texts.

"""
    for title, source in (
        ("Unicode License V3", "tests/reference/unicode-17.0.0/LICENSE.txt"),
        ("ag-sanjjeev Bamini source (MIT)", "tests/reference/codec-v0.1/LICENSE-ag.txt"),
        ("Pakeetharan Balasubramaniam Bamini reference (MIT)", "tests/reference/codec-v0.1/LICENSE-pakeetharan.txt"),
    ):
        text += f"## {title}\n\n```text\n{(ROOT / source).read_text(encoding='utf-8').strip()}\n```\n\n"
    return text.encode("utf-8")


def expected_files():
    notice = notices()
    files = {ROOT / "THIRD_PARTY_NOTICES.md": notice}
    license_bytes = (ROOT / "LICENSE").read_bytes()
    destinations = [ROOT / "crates" / name for name in PUBLIC]
    destinations += [ROOT / "bindings" / name for name in ("python", "js-wasm", "dart-flutter")]
    for destination in destinations:
        files[destination / "LICENSE"] = license_bytes
        files[destination / "THIRD_PARTY_NOTICES.md"] = notice
    for name in PUBLIC:
        text = f"""# {name}

{SUMMARIES[name]}

Experimental alpha `{VERSION}`. APIs may change before stability. This package
does not implement all Tamil linguistic conventions. Read the bounded module
contracts and examples in the [project documentation](https://github.com/abishtakan/tamil-toolkit#readme).

```toml
[dependencies]
{name} = \"={VERSION}\"
```

Original code is MIT licensed; see LICENSE and THIRD_PARTY_NOTICES.md.
Bundled `lexicon/` files are generated copies of the repository's canonical
declarative data, checked byte for byte by `just check-release-files`.
Contributions are welcome at https://github.com/abishtakan/tamil-toolkit.
"""
        files[ROOT / "crates" / name / "README.md"] = text.encode("utf-8")
    for name, inputs in INPUTS.items():
        for filename in inputs:
            files[ROOT / "crates" / name / "lexicon" / filename] = (ROOT / "lexicon" / filename).read_bytes()
    return files


def sync(check=False):
    stale = []
    for path, expected in expected_files().items():
        if path.is_file() and path.read_bytes() == expected:
            continue
        stale.append(str(path.relative_to(ROOT)))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if check and stale:
        raise ValueError("Stale release copies; run just sync-release-files: " + ", ".join(stale))
    print(f"Release source copies {'verified' if check else 'synchronized'} ({len(expected_files())} files).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    sync(parser.parse_args().check)
