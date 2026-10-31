# TSCII reference evidence

`TamilUtil.java` and `LICENSE.txt` are the unmodified Android TamilUtil source
and MIT license from commit `1f659e70eabed0bcdb0e6e37e10cea99a57f5056`:
https://github.com/mayooresan/Android-TamilUtil

The source SHA-256 is
`fbc2e9fc85b83ae9bb617a860629941707711a1de1e23f7233af1bc3178a5753`.
The repository credits Tamil Visai, Suratha and Mauran; its license explicitly
excludes example fonts. No font files are included here.

The IANA TSCII registration draft is independent standard evidence:
https://data.iana.org/archive/ietf-charsets/pdf00000.pdf
The `0xAD` alias and correction of the reference's literal backslash before
`0x88` follow that draft. See `docs/specs/codec-tscii-draft.md` and
`docs/specs/codec-roadmap.md` for the bounded profile and source differences.

Regenerate fixtures and data with `python tools/generate_tscii_golden.py
fixtures` and `python tools/generate_tscii_golden.py lexicon`. The generator
checks the pinned digest before reading the reference.
