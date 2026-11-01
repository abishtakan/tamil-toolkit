# tamil-codec expansion: plan and source inventory

Status: the unreleased source includes bounded TSCII, TAB, TAM and Anjal byte conversion
alongside the published `bamini-v1` profile. Further profiles remain planned.
See the codec contracts for limits and the TAB mapping-source conflicts.

## Delivery order

1. Audit sources, versions, licensing, and independent references for TSCII,
   TAB, TAM, Anjal, and Vanavil. Select the first profile based on usable
   mapping evidence; preserve disagreements rather than guess.
2. Specify its byte/text representation, variant, conversion directions,
   normalization, unsupported input, errors, and round-trip guarantees. Add
   sourced, escaped golden vectors before Rust code. Keep the suite planned
   until its contract and fixtures are reviewed.
3. Implement the profile in Rust using declarative mapping data and expose thin
   Python, WASM, and Dart bindings. Run the same active fixtures through each
   runtime and document any ambiguity or unsupported forms.
4. Repeat for remaining profiles. Define detection separately, including an
   explicit uncertain result for inputs shared by multiple encodings. Treat
   historic orthography as a separately sourced transformation.

## Acceptance for each profile

- A pinned source, version, digest, license and attribution are recorded, with
  an independent reference and documented mapping disagreements.
- The specification defines supported variants, byte versus Unicode-string
  inputs, direction-specific guarantees, and precise error behavior.
- Golden vectors cover the declared mapping inventory, multi-symbol sequences,
  malformed inputs, ambiguous mappings, normalization, joiners, and TN/SL
  invariance. Unresolved cases remain explicit errors or planned cases.
- Rust and all supported bindings pass the same active vectors; relevant full
  gates and host Dart checks pass. Existing Bamini fixtures remain unchanged.

## Research leads, 2026-10-31

| Profile | Primary reference | Reuse status and next check |
| --- | --- | --- |
| TSCII 1.7 | [Unicode Technical Note 15](https://www.unicode.org/notes/tn15/) and [IANA registration draft](https://data.iana.org/archive/ietf-charsets/pdf00000.pdf) | The note states copyright and permission conditions. Audit alternative licensed mapping data and independent agreement before copying. |
| TAB | [Unicode Technical Note 17](https://www.unicode.org/notes/tn17/) and [Tamil Nadu standards](https://www.tamilvu.org/ta/Tamilnet99-tabtam-341628) | Review exact reuse terms, mapping version and byte coverage. |
| TAM | [Unicode Technical Note 18](https://www.unicode.org/notes/tn18/tn18-1.html) and the same Tamil Nadu standards | The note states copyright and permission conditions. Review alternative licensed mapping data before copying. |
| Anjal / Vanavil | [open-tamil converter inventory](https://github.com/Ezhil-Language-Foundation/open-tamil/blob/main/tamil/txt2unicode/README.md) | Identify each mapping's origin, version, and applicable file-level license; the inventory alone is not a verified mapping source. |
| LT-TM / IndoWord | [TVA legacy font list](https://www.tamilvu.org/en/tamil-softwares-old), [Azhagi converter inventory](https://www.azhagi.com/tamil-fonts-converter.php) | Identified in the 2003 Tamilmann Tolkāppiyam PDF. Azhagi's public configuration matches a PDF title sequence but its bundled license restricts derivatives; independently derive the map and settle CID input/aliases. See [source assessment](codec-lt-tm.md). |

An additional [Android TamilUtil repository](https://github.com/mayooresan/Android-TamilUtil)
claims mappings for TSCII, TAB, TAM and Anjal. Its [license](https://github.com/mayooresan/Android-TamilUtil/blob/master/LICENSE)
is MIT for the library and explicitly excludes the example fonts. Its README
also credits external conversion code, so provenance and the exact relevant
files still need examination. No table from these leads has been copied or
approved for redistribution by this audit.

## TSCII candidate comparison

The user identified [aril-core](https://crates.io/crates/aril-core). Its
[repository](https://github.com/digital-tamil/aril) at commit
`1c732a9c1db0ac91ace9987b27e5d308c54fecc5` declares `MIT OR Apache-2.0` and
acknowledges Open-Tamil as a mapping source. Its `tscii.rs` has SHA-256
`26170d4cba7e26d3a039fdd1a04a966d8ce80d12a41756a438814acb6b358260`.
The examined checkout does not contain the license files linked in its README.

An offline structural comparison found all 339 rows (320 distinct pairs)
identical to Open-Tamil's `encode2utf8.py` at commit
`5ce20bd727a6a9d1e5969b212ab8fdae571b132f`. That file's header states GPL-3.0
or later even though the repository root has an MIT license. Aril is useful as
a comparison implementation; table reuse needs a provenance/terms review.
This observation does not itself establish a legal conclusion about either
project. The table contains both C1 controls and Windows-1252 characters,
so its string representation must not be treated as raw TSCII bytes.

Android TamilUtil's TSCII encoder at commit
`1f659e70eabed0bcdb0e6e37e10cea99a57f5056` has source SHA-256
`fbc2e9fc85b83ae9bb617a860629941707711a1de1e23f7233af1bc3178a5753`.
Its repository declares MIT for the library, excluding example fonts. A
structural comparison found 285 exact NFC-normalized pairs shared with Aril,
27 only in the Android source, and 35 only in Aril. These differences and
the Android source's third-party credits require review before adopting data.

As a separate investigation, interpreting each representable source scalar
as Windows-1252, with C1 controls represented by their same-valued byte,
produces 312 distinct Android byte/output pairs and 319 Aril pairs. Of those,
300 agree, 12 occur only in Android, 19 only in Aril, and shared byte keys
have no conflicting outputs. One Aril pair uses U+2219, which this byte
interpretation cannot encode. One Android key begins with byte `0x5C` because
the Java source contains an escaped backslash; it needs independent review.
These counts are an audit convention, not a chosen API or a complete standard.

TSCII was the first candidate for a bounded profile because the IANA
registration draft and two existing implementations provide inspectable
evidence. The draft identifies both byte `0xAD` and byte `0xFE` as the third
vowel, with the former deprecated. Pin the intended standard version, settle
all byte/string representation rules, and review source rights and mismatches
before marking a complete mapping profile ready for implementation.

The LT-TM / IndoWord profile is the next mapping-derivation candidate. Do not
merge it with Vanavil, AnuGraphics, or Pallavar until code tables are compared.
The PDF CID representation and whole-document coverage still need verification;
no fixtures or decoder are active. Azhagi's configuration is a comparison lead,
not data to copy into the toolkit.
