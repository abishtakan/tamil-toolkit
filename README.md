# tamil-toolkit

A Rust-first Tamil linguistic toolkit monorepo with thin Python, TypeScript/WASM,
and Dart bindings, deterministic Unicode inspection, and shared golden fixtures.
The MIT-licensed public alpha is available from PyPI, crates.io, and npm.
Implemented modules have bounded, verified contracts; planned modules are
excluded from the alpha SDK.

## Alpha release status

The `0.1.0-alpha.2` release is published on all three registries. The six
finished Rust crates are on [crates.io](https://crates.io/crates/tamil-toolkit),
the [npm package](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.2)
and [PyPI package](https://pypi.org/project/tamil-toolkit/0.1.0a2/) are live,
and tag [`v0.1.0-alpha.2`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.2)
points at the reviewed source. npm's `alpha` tag points to alpha 2; `latest`
remains alpha 1. See the [alpha 2 release record](docs/releases/alpha-2.md)
and [release runbook](docs/releases/README.md).

`just release-check` builds six Cargo archives, an abi3 Python wheel and source
distribution, and an npm package containing Node/browser WASM and types. It
installs the artifacts in isolated consumers and executes every active golden
row. Artifacts and SHA-256 digests are written under `target/alpha/`.
The alpha artifact workflow also prepares Linux, Windows, and macOS wheel jobs;
local verification alone does not establish support on those remote platforms.

## Start here

Read [current status](docs/status.md), [development workflow](docs/development.md),
and [publishing policy](docs/releases/policy.md) for the next task and release
rules. `just release-status` lists approved packages; `just check-release-policy`
checks versions, scope, and channel without building distributions.

Install Rust through rustup (the repository pins 1.95.0), Python 3.11+, uv,
Node 22.16+, pnpm 11.5.0, and [just](https://just.systems/). Rust host builds on
Windows require MSVC Build Tools. Ensure Cargo's bin directory is on PATH; for
this Windows account it is `C:\Users\abish\.cargo\bin`.

```sh
just doctor
just bootstrap
just agent-pre-stop-gate
```

`just` dispatches through a cross-platform Python task runner. Dependency locks
are checked in for Cargo, uv, pnpm, and Dart. `bootstrap` installs the locked
dependencies and builds a real editable PyO3 extension plus Node/browser WASM.
`cargo-nextest` is optional: `test-rust` uses it when available, otherwise clearly
reports its fallback to Cargo's test runner. Both execute the same properties.

## Local package workbench

Run `pnpm dev` from the repository root and open `http://127.0.0.1:5173/`.
The Vite app, configuration, package manifest, and TypeScript config live in
`workbench/`; root commands delegate to that package. The dev command builds
browser WASM first. UI and style edits use Vite hot reload;
Rust or lexicon edits rebuild the browser WASM and refresh the page. Select any
implemented package to enter values and see its operations update live as you
type. Results show the returned text or JSON plus Unicode scalar values. Python
and Dart selections call their native adapters from the local dev server. The
`tamil-codec` workbench supports live Bamini conversion in both directions and
bounded TSCII, TAB, TAM and Anjal byte conversion in both directions. The
unreleased LT-TM CID profile is available through Rust and the shared dispatcher;
its 687-vector parity suite passed Rust, Python, WASM, and Dart verification.
The workbench does not expose it yet.
Planned packages remain visibly unimplemented. Golden vectors and native test suites are
available in a collapsed optional section below the manual controls.
`pnpm run check:workbench` type-checks the app; `pnpm run build:workbench`
verifies a production bundle.

For Dart, install a Dart SDK compatible with `bindings/dart-flutter/pubspec.lock`
(3.11+ for this lock) and run `just test-dart`. The shared library is built for
the host; mobile library bundling is future work.

## Implemented bootstrap

- `get_letters`: NFC-normalized Unicode clusters, tailored for Sri and KSHA.
- `split_uyirmei` / `compose_uyirmei`: consonant/vowel decomposition and assembly.
- `normalize_nfc` / `normalize_nfd`: canonical normalization preserving joiners.
- `inspect_tamil_string`: normalization, letter count, and phonetic classification.
- `compare` / `sort_words`: traditional Mei-first Agara comparison and stable
  sorting, preserving original spellings and duplicates.
- `sort_key` / `search_key`: versioned canonical numeric keys for ordering and
  exact normalized matching; see the explicit Agara/fallback profile below.
- `to_words`: signed integer spellings with formal TN/SL lexical profiles.
- `format_currency` / `currency_to_words`: exact INR/LKR minor-unit amounts,
  grouped numeric display, and cardinal words with denomination labels.
- `format_fraction` / `fraction_to_words` / `fraction_symbol`: exact reduced
  rationals, common names/division readings, and traditional Unicode symbols.
- `format_date`: Tamil Gregorian dates in four styles with Latin/Tamil digits.
- `bamini_to_unicode`: explicit `bamini-v1` decoding with longest matching,
  strict/preserve policies, and NFC output.
- `unicode_to_bamini`: canonical strict encoding that returns ASCII only after
  decoding it reproduces the NFC input.
- `anjal_bytes_to_unicode` / `unicode_to_anjal_bytes`: bounded Anjal conversion with strict ambiguity errors.
- `tam_bytes_to_unicode` / `unicode_to_tam_bytes`: bounded monolingual TAM byte conversion.
- `tab_bytes_to_unicode` / `unicode_to_tab_bytes`: bounded TAB byte conversion.
- `unicode_to_tscii_bytes`: strict bounded TSCII encoding with round-trip validation.
- `tscii_bytes_to_unicode`: bounded TSCII byte decoding with explicit errors
  for unsupported bytes and NFC output.
- Local MCP tools for scalar inspection, scalar diffs, and fixture validation.
- **27,644 active golden vectors**, including 1,698 shared error cases, across Rust,
  Python, Node/browser-target WASM, and host Dart.
- Independent Unicode 17 fixtures cover all 247 traditional letters, the full
  288-form supported consonant/vowel matrix, both Shri spellings, and 766 UAX 29
  boundary cases. Reference files include source digests and licensing.
- Nineteen core/collation/numeral/codec properties with **10,000 cases each**, plus invalid-input checks.

```python
import tamil_toolkit as tamil

letters = tamil.get_letters("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")
assert letters == ["\u0ba4", "\u0bae\u0bbf", "\u0bb4\u0bcd"]
assert tamil.compare("\u0b95\u0bcd", "\u0b95") == -1  # Mei sorts before its vowel forms.
assert tamil.format_currency(102550, "LKR", "SL") == "LKR 1,025.50"
words = tamil.to_words(1025, "SL")
assert tamil.format_fraction(2, 4) == "1/2"
date = tamil.format_date(2024, 2, 29, "SL", "full", "tamil")
assert tamil.bamini_to_unicode("jkpo;") == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"
assert tamil.unicode_to_bamini("".join(letters)) == "jkpo;"
assert tamil.tscii_bytes_to_unicode(bytes([0xba, 0xa2, 0xc5, 0xfd])) == "\u0b9a\u0bbf\u0bb5\u0ba9\u0bcd"
```

```ts
import { get_letters } from "tamil-toolkit";
const letters = get_letters("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
// Browser entry: import { init, get_letters } from 'tamil-toolkit/web'; await init();
```

See [the bootstrap specification](docs/specs/bootstrap.md) for exact behavior,
allocation guarantees, Unicode sources, and unsupported inputs.
The [core v0.1 plan and acceptance results](docs/specs/core-v0.1.md) record its
completed engineering criteria and local-verification limits.
The [collation v0.1 plan and contract](docs/specs/collate-v0.1.md) define
`agara-v1`, stable NFC/NFD ties, Grantha handling, scalar fallback, and key
versioning. Search keys provide canonical exact matching. The profile does not
implement full ICU/UCA collation or fuzzy linguistic search.
The [numerals v0.1 contract](docs/specs/numerals-v0.1.md) defines CLDR 49
integer spellings through +/-999,999,999 and money through +/-99,999,999,999
minor units. Money APIs take integers (100 minor units per rupee); they apply
no rounding. TN/SL share Tamil 3-2 digit grouping.
The [numeral completion contract](docs/specs/numerals-v0.2.md) covers reduced
fractions with exact bounded components, three common fraction names and a
general division-expression reading, all 18 Unicode Tamil fraction values,
and Gregorian civil dates for years 1..9999. Date formatting supports four
CLDR styles and Latin/Tamil decimal digits. This completes the documented
numeral feature families; Tamil solar-calendar conversion and broader spoken
regional morphology are outside that contract.
The [codec v0.1 contract](docs/specs/codec-v0.1.md) defines a pinned Bamini
profile with 298 unambiguous keys. Strict mode rejects unsupported input and the
source table's ambiguous `*`; `errors="preserve"` retains them and preserves
joiners. Callers must select Bamini text runs: English shares the same character
codes. Automatic detection, other encodings, and five
ambiguous Tamil forms remain outside this milestone.
The [reverse encoding contract](docs/specs/codec-reverse-v0.1.md) adds strict
Unicode â†’ Bamini with canonical aliases and NFC input. It rejects unsupported
scalars and letter combinations whose legacy keys would change the text when
decoded. Every accepted input round-trips to its NFC spelling.
The [TSCII decoder contract](docs/specs/codec-tscii-draft.md) defines a bounded
313-key byte profile, ASCII pass-through, longest matching, and explicit byte
errors. It does not yet provide reverse conversion or automatic detection.

## Package map

| Package          | State                                  | Responsibility                                                                |
| ---------------- | -------------------------------------- | ----------------------------------------------------------------------------- |
| `tamil-toolkit`  | Working bootstrap                      | Rust umbrella and common JSON dispatcher; Python/npm distribution name        |
| `tamil-core`     | v0.1 contract verified locally         | Ezhuthu segmentation, Mei/Uyir, Unicode inspection                            |
| `tamil-norm`     | Working facade                         | Re-export core normalization for SDK/PostgreSQL consumers                     |
| `tamil-collate`  | agara-v1 verified locally              | Mei-first Agara sorting and canonical sort/search keys                        |
| `tamil-numerals` | v0.2 feature families verified locally | Integer words, exact INR/LKR amounts, fractions, Gregorian dates              |
| `tamil-codec`    | bounded profiles                       | Bamini, TSCII/TAB/TAM/Anjal; unreleased LT-TM CID codes (suite active)       |
| `tamil-punarchi` | Planned                                | Sourced Nannool sandhi and compound splitting                                 |
| `tamil-morph`    | Planned                                | FST stemming, lemmatization, suffix/case analysis                             |
| `tamil-dialect`  | Planned                                | TN/SL regional spoken-to-literary normalization                               |
| `tamil-hyphen`   | Planned                                | Syllable/morpheme boundary hyphenation                                        |
| `tamil-yaappu`   | Planned                                | Prosody and meter                                                             |
| `pg_tamil`       | Integration scaffold                   | Separate pgrx extension; full-text search waits on morphology                 |

Public distributions use `tamil-*`. Python imports and Pub use `tamil_toolkit`
because those platforms require identifier-compatible names. Internal Rust FFI
packages are `tamil-python`, `tamil-wasm`, and `tamil-dart`. The Python umbrella
is on PyPI, the six finished Rust crates are on crates.io, and the JavaScript /
WASM package is on npm.

## Harness layout

```text
AGENTS.md / CLAUDE.md       cross-agent constitution and entry point
.claude/                   specialist roles, slash commands, guardrail hooks
.cursor/rules/             always-on Rust/data and Unicode rules
.mcp.json                  local stdio oracle registration
tools/mcp-tamil-oracle/     deterministic inspection, diffs, Unicode check
tests/golden/              JSON schema, manifest, shared JSONL vectors
tests/harness/             validation, hook, and real MCP protocol tests
tests/reference/           pinned independent Unicode evidence and acceptance profile
lexicon/                   declarative TOML/CSV only
crates/tamil-*/             algorithms, umbrella, and planned module scaffolds
bindings/                  thin PyO3, WASM, and Dart FFI adapters
extensions/pg_tamil/        isolated PostgreSQL integration scaffold
justfile                   shared developer and agent commands
```

`just check-unicode` validates raw source and decoded fixtures, exact Unicode
exceptions, required dialect metadata, globally unique IDs, and suite inventory.
`just test-parity` rebuilds bindings first and executes every active fixture;
missing bindings and unknown operations fail. Planned suites are validated and
reported separately. Numeral suites use the pinned evidence described in their
module contracts.

Claude's Stop adapter turns failures into blocking exit 2. Specialist role hooks
restrict edits and shell commands through Claude's tool interface; they are not
OS permissions. See [agent harness details](docs/agent-harness.md). Cold checks
can take minutes. The fast GitHub push/PR gate runs core Rust and Unicode checks
on Ubuntu. The full cross-runtime, harness, and Dart gates remain available
locally; the alpha artifact workflow checks release packages across supported
platforms on explicit dispatch.

Original code is [MIT licensed](LICENSE); upstream data and mapping notices are
preserved in [third-party notices](THIRD_PARTY_NOTICES.md). Contributions are
welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). The PyPI, Rust, and npm alpha
packages are live.

The TSCII, TAB, TAM and Anjal byte conversions are included in all alpha.2
packages. The published Python alpha.1 package does not include them.
The LT-TM / IndoWord CID profile is an unreleased source change and is not part
of the alpha.2 distributions.
