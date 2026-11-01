# Project handoff

Updated: 2026-11-01. Branch: `master`. Current release source:
`af11c96ddacd0fedda0cc8c346130a71f924c0b6` (`0.1.0-alpha.2`). Operational
workflow fixes are on master after that source commit; release artifacts remain
bound to the reviewed source SHA. See [alpha-2 release record](releases/alpha-2.md).

## Current status: alpha 2 released

The immutable artifact build passed in
[run 41237000066](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237000066).
The reviewed release is published on crates.io, npm and PyPI, and tag
[`v0.1.0-alpha.2`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.2)
points to the release source.

- crates.io: `tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`,
  `tamil-codec`, and `tamil-toolkit`, all `0.1.0-alpha.2`.
- npm: [`tamil-toolkit@0.1.0-alpha.2`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.2)
  is published using the configured OIDC trusted publisher. A fresh public
  installation passed all 26,957 active golden rows through Node and
  browser-target WASM. The `alpha` tag points at alpha 2; `latest` remains alpha 1.

- PyPI: `tamil-toolkit 0.1.0a2`. OIDC publisher run
  [41237423572](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237423572)
  passed the configured `pypi` reviewer gate. Public artifact digests matched
  the reviewed wheels/source archive; a fresh Windows CPython 3.13.7 install
  passed all 26,957 active golden rows.

Publisher run links, registry checksums, and the full artifact inventory are
recorded in [releases/alpha-2.md](releases/alpha-2.md). Earlier publisher
workflow run 41237404162 failed before upload because Cargo 1.95 removed the
dry-run crate archive. The workflow now runs `cargo package` to retain an
archive for comparison. The retry passed; the failed run published nothing.
The final Core Rust CI run
[41238338654](https://github.com/abishtakan/tamil-toolkit/actions/runs/41238338654)
passed after pinning actionlint's official release and verifying its SHA-256.

The local shell does not have Cargo on `PATH`, so its `just agent-post-edit`
attempt stopped with “Missing cargo”. The release source itself previously
passed the complete agent gate, Dart, workbench checks/build, Unicode and
release-policy checks, and `just release-check`; see `alpha-2.md` for details.

## Scope and next development

Alpha 2 adds bounded TSCII, TAB, TAM, and Anjal byte conversion. These profiles
do not claim automatic detection or complete historical font coverage. The
current active golden suite contains 27,644 rows. Punarchi source review has
started under [the v0.1 source and scope contract](specs/punarchi-v0.1.md). The
contract selects the Nannūl Eḻuttatikāram root text for the first named literary
profile, matching the toolkit's stated merger scope; Tolkāppiyam remains a
separate foundational comparison. The primary edition is A. Thamodaran's 1999
critical edition of the Nannūl root text with Sankara Namasivayar's Viruttiyurai,
corrected by Sivagnana Munivar. Its title page, editorial method, and formatted
HTML viewer text for sūtras 204–205 were inspected; the inspected pages contain
no scan image. Project Madurai's e-text of the Vavilla
1926 edition is retained as a contents/numbering cross-check. The three Nannūl
section ranges are verified. Page-indexed paraphrases, root-number locators,
and first-pass subject ledgers for sūtras 151–203, 204–239, and 240–257 are
recorded in the [Punarchi source notes](specs/punarchi-source-notes.md). The subject notes
are provisional; exact conditions, commentary/examples, and Tamil grammar
review remain open, along with printed-page mapping and variant review.
The TVA viewer provides formatted HTML text, not a scan in the inspected pages;
printed-page mapping and variants still need print-level verification.
Project Madurai's
complete 1926-based Unicode e-text is searchable and linked there; it is a
cross-check, not a duplicate or a replacement for the pinned edition. The
Tolkāppiyam comparison source audit has inspected the 1979 Annamalai
Iḷampūraṇar scan, the 2003 Tamilmann edition, and the 1982 WTRI Puṇariyal
commentary compilation. The 1979 title verso says second edition, August 1979;
it is only a provisional citation witness. A major variant resource is the
1996 *Textual Variation of Tolkappiyam: A Deep Study* (CICT's English catalog
title): its editors collate
manuscript and printed witnesses, but explicitly do not establish one base
reading. Use it as a variant apparatus, not a definitive root-text edition.
Thiagarajar lists a 1992 third edition of Sundaramurthy's Annamalai text;
CICT catalogs a matching 1996 record, but no title-page scan confirms whether
it is revised or reprinted. No sole Tolkāppiyam comparison edition is pinned.
No rule engine or active fixture was added. Existing repositories were
audited as non-authoritative leads; the review found incompatible/unclear
license declarations and upstream issue reports, so no code or data was
reused. The planned suite remains inactive pending rule-level source review
and sourced merger fixtures. A lexical splitter is deferred until its own
lexicon provenance/redistribution review.

Pub.dev/Dart distribution and PostgreSQL packaging remain deferred. Next,
obtain and inspect the Annamalai/Sundaramurthy 1992 third edition or the
cataloged 1996 copy, then compare its title page, preface, and relevant
readings with the 1979 witness and the 1996 variant apparatus. If no later copy
is accessible, explicitly retain 1979 only as a working citation witness.
Then continue the rule-level Nannūl audit from sūtra 158 (100 of 107 remain),
validate the provisional subject ledgers, and record exact conditions,
commentary, and examples; obtain print-level pagination and variant evidence.
Record citations and variants, then obtain Tamil grammar review before writing
merger fixtures. Keep lexical splitting deferred until a suitable licensed
lexicon is found.
Continue to follow
[development workflow](development.md),
[publishing policy](releases/policy.md), and the agent constitution.

### Punarchi handoff (2026-11-01)

- Base: `master` at the alpha 2 release source listed above; current Punarchi
  specification, source digest, handoff, changelog, and manifest edits are
  uncommitted.
- Completed: created the [v0.1 source and scope contract](specs/punarchi-v0.1.md)
  and a [page-indexed source digest, locators, and first-pass subject ledgers](specs/punarchi-source-notes.md)
  for Uyirīṟṟup Puṇariyal 151–203, Meyyīṟṟup Puṇariyal 204–239, and Urupu
  Puṇariyal 240–257 from the TVA HTML edition text,
  selected Thamodaran's 1999 Nannūl critical edition as the primary
  root-text/commentary witness, verified its editorial notes and representative
  sūtras, and verified all three Nannūl section ranges. An earlier draft had
  selected the CICT 1979 Iḷampūraṇar edition for Tolkāppiyam comparison; that
  selection was withdrawn after later publications were found. Follow-up
  source review inspected the 1979, 2003, and 1982 TVA scans plus CICT's 1996
  textual-variation volume. Added a provisional
  root/commentary/example audit for Nannūl sūtras 151–157 from TVA pages
  218–225. Existing implementation leads were reviewed. The suite remains
  planned; no fixtures, code, or external data were added.
- Checks: `git diff --check` completed without whitespace errors;
  `just check-unicode` passed (release policy, Unicode/schema gate with 26,957
  active vectors, and 34 generated source copies).
- Pending: obtain the Annamalai/Sundaramurthy 1992 third edition or CICT's
  matching 1996 cataloged copy and compare its title verso, preface, and
  readings with the inspected 1979 witness. CICT's 1996 *Textual Variation of
  Tolkappiyam: A Deep Study* is now inspected and documented as a rich
  variant apparatus, but its editors explicitly do not establish a single
  base reading. Keep it as a required cross-check, not the root-text authority.
  The 2003 Tamilmann source is a later commentary witness; the 1982 WTRI
  *Puṇariyal Uraivaḷam* is a commentary compilation. The CICT 2025 English
  monograph released in 2026 is a separate interpretation source. Also continue
  the rule-level Nannūl audit from sūtra 158 onward (100 of 107 remain),
  validate the provisional 151–257 subject ledgers, and record each rule's
  exact conditions, commentary, and examples; obtain print-level pagination
  and variant evidence. Only
  then add escaped, sourced merger vectors before implementation. Clarify
  upstream licenses before considering reuse. A lexical splitter remains a
  later milestone with separate lexicon review.
- Checks on the prior documentation pass: `just check-unicode` passed (26,957
  active vectors, planned suites validated separately, 34 generated release
  copies verified); `git diff --check` reported no whitespace errors. The
  source-comparison documentation edits in this handoff still need the gates
  rerun. No Rust code changed.
- Source-selection outcome: 1979 is confirmed as a second edition, August
  1979, and remains only a provisional witness. The 1992 third edition / 1996
  catalog date discrepancy is unresolved because no later title page or
  preface scan was found. The 1996 variant study publishes readings and
  manuscript/print witness discussion, while explicitly declining to establish
  a single base text. No Tolkāppiyam edition is pinned as sole authority. When
  a reviewed Nannūl rule requires comparison, record the exact passage,
  commentary layer, and material variants before deciding its relationship.

### LT-TM codec handoff (2026-11-01)

- The 2003 Tamilmann *Tolkāppiyam* PDF is digitally typeset text using embedded
  `LT-TM-*` font faces; it is not scan-only. The profile consumes 16-bit
  `/Identity-H` codes; ordinary extraction does not return reliable Tamil
  Unicode. Several page-one font runs and the title were checked against the
  rendered page.
- `lexicon/lt_tm.toml` is the canonical, normalized 332-entry mapping
  projection. The build compiles a CID trie and reverse Unicode trie. Rust
  exposes code-array and legacy code-valued text conversion through the shared
  dispatcher, so Python, Node/browser WASM, and Dart use the same engine.
- `tests/golden/codec_lt_tm.jsonl` contains 687 escaped, sourced vectors: all
  mapping entries in both directions plus PDF, normalization, fallback, and
  error cases. The owner reviewed [the profile contract](specs/codec-lt-tm.md)
  and activated the suite; it now counts as parity coverage.
- The source projection is based on the Azhagi+ Portable LT-TM configuration;
  its digest and bundled terms are recorded in the contract. The toolkit MIT
  license does not replace those terms. This is a bounded profile and does not
  establish that every LT-TM/IndoWord font is equivalent. Vanavil, AnuGraphics,
  and Pallavar are not aliases; there is no PDF parser or automatic detection.
- Checks completed: `just agent-pre-stop-gate` passed, including Clippy,
  25 Rust tests, doctests, 115 harness tests, and 27,644 Rust golden vectors;
  Python passed 27,656 cases; Vitest passed 27,654; `just test-dart` passed
  analysis and 27,654 host-FFI fixture tests. `just sync-bindings` rebuilt
  PyO3, Node/browser WASM, and TypeScript declarations. The initial Rust run
  caught a missing final virama in one expected phrase; the fixture was fixed
  and the complete gate rerun passed.
- Broader compatibility with all LT-TM font families remains unverified; do
  not claim Vanavil, AnuGraphics, or Pallavar aliases. This work is
  uncommitted on `master`; no commit was created.

Never put registry credentials in the handoff, repository, build artifacts, or
chat. Do not claim complete linguistic support from the bootstrap suites.
