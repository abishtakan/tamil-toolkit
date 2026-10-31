# Bamini reference evidence

`sources.json` pins original bytes from two upstream MIT-licensed repositories:
ag-sanjjeev/app-tamil-fonts-unicode-converter at
`9faf6226e500b0d1ab2e83132e8f227232d4d05d`, and
Pakeetharan/unicode-bamini-converter at
`ee08d4360afadebaea4ef373ca1fad42025abb53`. Both original copyright/license
notices accompany the data. No font binary is included.
Upstream files retain their exact bytes, including existing whitespace.

`primary-table.json` is an unchanged extraction of the primary source's Bamini
object. `samples.json` contains 300 primary Unicode entries, the separately
sourced Aytham, and 31 word/vowel-matrix sequences. `secondary-results.json`
records those inputs passed through the secondary source's original encoder.
It is an independent implementation, not the toolkit's decoder or runtime table.
The 31 multi-key samples avoid ambiguous placeholders and differing profiles.

To reproduce the extraction and original encoder output locally, run Node from
the repository root with temporary output paths:

```sh
node tools/reference/BaminiReference.cjs tests/reference/codec-v0.1 target/primary-table.json tests/reference/codec-v0.1/samples.json target/secondary-results.json
```

Parse the two output JSON files and compare structurally with the frozen files
(frozen copies are formatted with ASCII escapes for scalar review). The helper
executes only the primary data declaration and the reviewed secondary encoder;
no UI code is invoked. Normal fixture checks are offline and use Python only:

```sh
uv run --locked python tools/generate_codec_golden.py --check
```

The compiler checks digests and reads these frozen facts, never the Rust decoder
or lexicon. Its finite concatenation examples have explicit expected parts; it
does not contain a second decoder. The scope, primary/secondary disagreements,
ambiguous `*`, and preservation policy are specified in `docs/specs/codec-v0.1.md`.

Reverse fixtures use the same frozen primary alias order and independent encoder
outputs, with additional structural key-prefix collision cases. They do not read
the runtime lexicon or call a toolkit encoder/decoder. Check them offline with
`python tools/generate_codec_reverse_golden.py --check`; their acceptance
contract is in `docs/specs/codec-reverse-v0.1.md`.
