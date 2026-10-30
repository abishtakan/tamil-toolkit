# tamil-toolkit

A Rust-first Tamil linguistic toolkit monorepo with thin Python, TypeScript/WASM,
and Dart bindings, deterministic Unicode inspection, and shared golden fixtures.
This repository is an unpublished bootstrap, not a complete linguistic SDK.

## Start here

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
- Local MCP tools for scalar inspection, scalar diffs, and fixture validation.
- **5,545 active golden vectors**, including 146 shared error cases, across Rust,
  Python, Node/browser-target WASM, and host Dart.
- Independent Unicode 17 fixtures cover all 247 traditional letters, the full
  288-form supported consonant/vowel matrix, both Shri spellings, and 766 UAX 29
  boundary cases. Reference files include source digests and licensing.
- Five core/collation properties with **10,000 cases each**, plus invalid-input checks.

```python
import tamil_toolkit as tamil

letters = tamil.get_letters("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")
assert letters == ["\u0ba4", "\u0bae\u0bbf", "\u0bb4\u0bcd"]
assert tamil.compare("\u0b95\u0bcd", "\u0b95") == -1  # Mei sorts before its vowel forms.
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

## Package map

| Package | State | Responsibility |
| --- | --- | --- |
| `tamil-toolkit` | Working bootstrap | Rust umbrella and common JSON dispatcher; Python/npm distribution name |
| `tamil-core` | v0.1 contract verified locally | Ezhuthu segmentation, Mei/Uyir, Unicode inspection |
| `tamil-norm` | Working facade | Re-export core normalization for SDK/PostgreSQL consumers |
| `tamil-collate` | agara-v1 verified locally | Mei-first Agara sorting and canonical sort/search keys |
| `tamil-numerals` | Planned | Words, fractions, dates, LKR/INR formatting |
| `tamil-codec` | Planned | Bamini, TSCII, Anjal, Vanavil, TAB, TAM, historic orthography |
| `tamil-punarchi` | Planned | Sourced Nannool sandhi and compound splitting |
| `tamil-morph` | Planned | FST stemming, lemmatization, suffix/case analysis |
| `tamil-dialect` | Planned | TN/SL regional spoken-to-literary normalization |
| `tamil-hyphen` | Planned | Syllable/morpheme boundary hyphenation |
| `tamil-yaappu` | Planned | Prosody and meter |
| `pg_tamil` | Integration scaffold | Separate pgrx extension; full-text search waits on morphology |

Public distributions use `tamil-*`. Python imports and Pub use `tamil_toolkit`
because those platforms require identifier-compatible names. Internal Rust FFI
packages are `tamil-python`, `tamil-wasm`, and `tamil-dart`. All publication is
disabled; registry availability, ownership, and licensing remain release tasks.

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
reported separately. The seeded numeral examples are unreviewed brief examples,
not validated currency rules.

Claude's Stop adapter turns failures into blocking exit 2. Specialist role hooks
restrict edits and shell commands through Claude's tool interface; they are not
OS permissions. See [agent harness details](docs/agent-harness.md). Cold checks
can take minutes. CI config runs the gate on Ubuntu and Windows and includes
Dart; those remote jobs run after this repository is pushed.

The directory was initialized without an existing Git repository. No remote,
registry publication, release license, or deployment is configured here.
