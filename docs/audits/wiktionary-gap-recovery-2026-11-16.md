# Wiktionary gap recovery: first candidate packet

Date: 2026-11-16. This work starts the historical Wiktionary recovery queue from
the [source readiness report](lexicon-source-readiness-2026-11-16.md).

## Outcome and scope

All **410** exact absent spellings are accounted for. The old snapshot contains
333 of them, all blocked by the unchanged strict parser. Fresh exact-title API
requests for the other 77 returned 51 pinned revisions and 26 missing pages.
The same parser extracted **7 core candidates with 9 senses** from those fresh
revisions. The final queue is **7 recovered candidates + 377 parser-blocked
spellings + 26 currently missing pages = 410**.

These seven candidates have passed existing release and canonical validation
in an isolated pack, plus genuine CLDF validation and roundtrip. Its 25 claims
are `accepted_auto_source` with automated actors and decision date 2026-11-16.
They are not human-reviewed claims and do not approve any historical assertion.

**Current runtime packs and playground coverage remain unchanged.** The isolated
pack is a validation/review artifact, not a replacement for the 10,336-entry core.
It must be merged with the existing core, preserving its entries, provenance and
six human-reviewed entry payloads, before runtime coverage can increase. Final packet artifacts are under `target/lexicon/wiktionary-gaps-final/`; earlier directories preserve pre-review evidence. Do not
copy this seven-entry pack over `lexicon/dictionary/`.

## Recovered entries

Every definition/gloss comes from freshly pinned Wiktionary wikitext, never the
historical database. The historical `word_ids` / `meaning_ids` remain discovery
links in the queue, not source attribution.

| Written form | Source POS | Senses | Pinned source |
|---|---|---:|---|
| ஆயிற்று | VERB | 2 | [page 11226765, revision 88163490](https://en.wiktionary.org/w/index.php?title=%E0%AE%86%E0%AE%AF%E0%AE%BF%E0%AE%B1%E0%AF%8D%E0%AE%B1%E0%AF%81&oldid=88163490) |
| உன் | PRON | 1 | [page 6318007, revision 92196799](https://en.wiktionary.org/w/index.php?title=%E0%AE%89%E0%AE%A9%E0%AF%8D&oldid=92196799) |
| எனது | PRON | 2 | [page 10985955, revision 88294402](https://en.wiktionary.org/w/index.php?title=%E0%AE%8E%E0%AE%A9%E0%AE%A4%E0%AF%81&oldid=88294402) |
| தன் | PRON | 1 | [page 9006571, revision 92262241](https://en.wiktionary.org/w/index.php?title=%E0%AE%A4%E0%AE%A9%E0%AF%8D&oldid=92262241) |
| நம் | PRON | 1 | [page 8701128, revision 89350558](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%AE%E0%AF%8D&oldid=89350558) |
| நின் | PRON | 1 | [page 9376540, revision 92242460](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%BF%E0%AE%A9%E0%AF%8D&oldid=92242460) |
| வேண்டாம் | VERB | 1 | [page 11411977, revision 90036319](https://en.wiktionary.org/w/index.php?title=%E0%AE%B5%E0%AF%87%E0%AE%A3%E0%AF%8D%E0%AE%9F%E0%AE%BE%E0%AE%AE%E0%AF%8D&oldid=90036319) |

All seven were checked with the existing Rust-backed title inspection path.
No region is inferred; existing source-attested register labels are preserved.
No IPA, etymology, morphology, DEDR or additional translations were generated.
Unsupported senses on an otherwise recoverable page remain excluded and their
reason codes remain visible in the reconciliation record.

## Remaining blockers

The [complete escaped queue](wiktionary-gap-reconciliation-2026-11-16.json)
contains all 410 spellings, historical IDs, source locators and exact per-page
reason counts. These are source-extraction blockers, not linguistic invalidity.
A page can have multiple blockers, so the counts below must not be summed.

| Blocker among the 377 parser-blocked spellings | Affected pages | Next step |
|---|---:|---|
| `place` template | 134 | Pin template/module/rendering dependencies or capture attributable rendered output with hashes; preserve geographic qualifiers and alternatives. Do not invent place definitions from positional arguments. |
| `infl of` template | 32 | Record source-attested inflection relations and features; do not add a Python inflection engine or copy generated historical conjugations. |
| Number-to-word template | 29 | Establish source-backed rendering/lemma treatment separately; do not confuse lexicon coverage with existing Rust numeral algorithms. |
| HTML/comment rejection | 29 | Examine individual source spans and add sourced sanitization fixtures only for demonstrated safe markup; do not strip arbitrary markup globally. |
| `altform` template | 23 | Preserve source-attested variant relationship and target evidence; do not merge distinct entries or infer synonymy. |
| `m` links / `l` links | 19 / 15 | These are Tamil-language calls in English glosses. Current policy rejects them intentionally; English literal links are already supported. Any mixed-script text policy change needs its own specification and fixtures. |
| Given-name template | 17 | Pin actual upstream expansion and retain gender/usage distinctions; do not synthesize biographical facts. |
| Unmapped Participle heading | 13 | Specify how source-attested nonlemma forms map to the existing entry/POS contract before broadening extraction. |

The other recorded families include alternative/standard forms, category links,
nested labels, transcluded senses and unmapped subsections. Each remains closed.
The 26 exact titles returning `missing` require title/history reconciliation;
this result is not proof that the historical spelling is false or has no earlier
revision. No redirects or title-normalization aliases were silently followed.

## Artifacts and replay

- [Fresh source capture](../../data/sources/enwiktionary-tamil-gap-2026-11-16/README.md):
  four complete API response batches, capture timestamps, 51 revision records,
  exact wikitext/permalink/history locators, and hash manifest.
- [Reconciliation implementation](../../tools/lexicon_wiktionary_gaps.py) and
  [regressions](../../tests/harness/test_wiktionary_gaps.py).
- [Isolated validation proof](../reviews/wiktionary-gap-candidate-proof-2026-11-16.json):
  7 entries / 9 senses / 25 automated claims, no canonical findings,
  `cldf_valid=true`, `roundtrip_ok=true`, `runtime_integrated=false`.
- [Candidate canonical directory](../../target/lexicon/wiktionary-gaps-final/candidate-canonical/packs.toml),
  [workspace](../../target/lexicon/wiktionary-gaps-final/candidate-workspace/sources.csv),
  [CLDF export](../../target/lexicon/wiktionary-gaps-final/candidate-cldf).
- [Link-policy and date-parameter audit](wiktionary-link-template-recovery-2026-11-16.md).

```powershell
# Reconcile, reusing verified API captures without another network request:
uv run --locked python -m tools.lexicon_wiktionary_gaps `
  --package C:/Users/abish/Downloads/utlkd_reusable_package `
  --check-native --fetch-missing `
  --supplemental-dir data/sources/enwiktionary-tamil-gap-2026-11-16

# Stage and validate a new isolated candidate output directory:
uv run --locked python -m tools.lexicon_wiktionary_gaps `
  --package C:/Users/abish/Downloads/utlkd_reusable_package `
  --check-native --fetch-missing --stage-candidates `
  --supplemental-dir data/sources/enwiktionary-tamil-gap-2026-11-16 `
  --output-dir target/lexicon/wiktionary-gaps-replay
```

The first run needs network access for missing raw batches. Later runs verify
saved hashes and reject tampering. Partial fetches require fingerprinted checkpoints; unregistered batches and mixed-source/non-core staging inputs fail closed. API failures do not become missing-page
results. Outputs must stay under `target/lexicon`; supplements must be separate
from the original frozen inputs. Staging refuses existing output directories.
Replay intentionally checks the readiness report's original pack/database
fingerprints; after usable packs change, retain the initial queue and establish
a new explicitly reviewed baseline instead of recomputing away resolved items.

## Review corrections

The independent Hydrogen review confirmed the 410-way accounting, source pins,
historical non-approval and runtime isolation. Its five findings were corrected:

- Staging accepts only exact, unnormalized core candidates re-extracted from
  the verified supplemental capture; mixed generations/pack routes are rejected.
- Cache verification includes raw batches, JSON, compressed and uncompressed
  projections. Interrupted fetches require hash checkpoints; orphan or stale
  batches cannot silently become trusted source evidence.
- Batch filenames are confined; both original source directories remain
  protected even when a custom snapshot argument is used. Staging receives the
  resolved supplemental path.
- Candidate source metadata now identifies the official exact-title API query
  and capture manifest, rather than the original bulk category URL.
- The durable queue and candidate proof were refreshed from final artifacts,
  including the parser fingerprint. Two final canonical replays are byte-identical
  across all 20 files. No historical source or current pack changed.

Regression tests cover these guards. The earlier review is not represented as
an independent approval of the later corrections; the corrections were verified
locally with focused tests, replay, source/pack fingerprints and gates.

## Verification and integration boundary

- Tests-first reconciliation, exact spelling, digest/attribution, duplicate,
  cache-tamper and API-error regressions pass.
- Existing/new bulk parser and snapshot-date tests: 29 focused tests pass across
  the two suites. New snapshot dates are calendar-validated before file writes;
  default and explicit 2026-11-15 workspace outputs are byte-identical in the
  regression fixture. No template allowlist was broadened.
- Release, canonical and genuine offline CLDF checks pass for the isolated pack.
- Unicode/schema/release-copy checks pass; original 12 file hashes and current
  three-pack manifest fingerprints remain unchanged.
- Final full harness: **501 passed in 78.82s** (80.041s including runner startup).
  `agent-post-edit` passes in 37.151s, including Rust formatting, Unicode/schema,
  release-policy/release-copy checks and workspace/core compilation. Timings and
  logs are recorded in [checks.json](../../target/lexicon/wiktionary-gaps-final/checks.json).
- No bindings were rebuilt, no active golden vectors changed, and no current
  runtime/parity/archive coverage is claimed for these seven new candidates.
  Final merge requires source-backed integration fixtures, preservation checks,
  refreshed metadata/catalog, and the applicable runtime/archive acceptance.

The next recovery workstream is the 134 place-template pages, followed by
source-attested variants/inflections under explicitly specified contracts.
