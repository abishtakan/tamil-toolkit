# Project handoff

Updated: 2026-11-01. Branch: `master`. Current release source:
`9917a761365dafbaa21a8f0bda2923ad71e712c1` (`0.1.0-alpha.3`). This immutable
source SHA is tagged `v0.1.0-alpha.3`; post-release documentation commits do not
change the published packages. See the [alpha-3 release record](releases/alpha-3.md).

## Current status: alpha 3 released

The immutable artifact build passed in
[run 41304156907](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304156907).
The reviewed release is published on crates.io, npm, and PyPI, and tag
[`v0.1.0-alpha.3`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.3)
points to the release source.

- crates.io: `tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`,
  `tamil-codec`, and `tamil-toolkit`, all `0.1.0-alpha.3`.
- npm: [`tamil-toolkit@0.1.0-alpha.3`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.3)
  is published using the configured OIDC trusted publisher. A fresh public
  installation passed all 27,644 active golden rows through Node and
  browser-target WASM. The `alpha` tag points at alpha 3; `latest` remains alpha 1.

- PyPI: `tamil-toolkit 0.1.0a3`. OIDC publisher run
[41304851700](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304851700)
  passed the configured `pypi` reviewer gate. Public artifact digests matched
  the reviewed wheels/source archive; a fresh Windows CPython 3.13.7 install
  passed all 27,644 active golden rows.

Publisher run links, registry checksums, and the full artifact inventory are
recorded in [releases/alpha-3.md](releases/alpha-3.md). The prior
[alpha-2 release record](releases/alpha-2.md) remains available as history.

The alpha 3 source passed the complete agent gate, Dart checks, release-policy
and Unicode gates, and `just release-check`; see the release record for the
check results and public consumer verification.

## Scope and next development

Alpha 3 adds the bounded LT-TM / IndoWord 16-bit profile. Byte and CID profiles
do not claim automatic detection or complete historical-font coverage. The
current active golden suite contains 27,644 rows. Punarchi work is deferred at
user direction. Preliminary research and its open criteria remain documented
under [the v0.1 source and scope contract](specs/punarchi-v0.1.md). The
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
recorded in the [Punarchi source notes](specs/punarchi-source-notes.md). These
notes are provisional. When work resumes, exact conditions,
commentary/examples, Tamil grammar review, printed-page mapping, and variant
review remain open.
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

Pub.dev/Dart distribution and PostgreSQL packaging remain deferred. The next
active development action is to inspect the 31 unsupported PDF font names for
usable Unicode maps, as listed in the PDF extraction handoff below. Punarchi
remains deferred with no scheduled restart. When resumed, obtain and inspect
the Annamalai/Sundaramurthy 1992 third edition or the cataloged 1996 copy, then
compare its title page, preface, and relevant readings with the 1979 witness
and the 1996 variant apparatus. If no later copy is accessible, explicitly
retain 1979 only as a working citation witness. Continue the rule-level Nannūl
audit from sūtra 158 (100 of 107 remain), validate the provisional subject
ledgers, and record exact conditions, commentary, and examples; obtain
print-level pagination and variant evidence. Record citations and variants,
then obtain Tamil grammar review before writing merger fixtures. Keep lexical
splitting deferred until a suitable licensed lexicon is found.
Continue to follow
[development workflow](development.md),
[publishing policy](releases/policy.md), and the agent constitution.

### Punarchi handoff (2026-11-01; deferred)

- Scheduling: further Punarchi work is deferred at user direction. Keep the
  research and resume criteria here; do not treat this source audit as the next
  development milestone. No implementation or active fixture exists.
- Base: `master` at the alpha 3 release source listed above. The source
  contract and notes preserve the preliminary research; current scheduling
  status and resume criteria are recorded here. No rule engine or activated
  suite exists.
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
- Resume criteria: obtain the Annamalai/Sundaramurthy 1992 third edition or CICT's
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
  and Pallavar are not aliases. PDF parsing is now handled by the private
  utility described below; it does not automatically detect fonts.
- Checks completed: `just agent-pre-stop-gate` passed, including Clippy,
  25 Rust tests, doctests, 115 harness tests, and 27,644 Rust golden vectors;
  Python passed 27,656 cases; Vitest passed 27,654; `just test-dart` passed
  analysis and 27,654 host-FFI fixture tests. `just sync-bindings` rebuilt
  PyO3, Node/browser WASM, and TypeScript declarations. The initial Rust run
  caught a missing final virama in one expected phrase; the fixture was fixed
  and the complete gate rerun passed.
- Broader compatibility with all LT-TM font families remains unverified; do
  not claim Vanavil, AnuGraphics, or Pallavar aliases. This work is
  committed as `3255bd4`.

### PDF-aware extraction handoff (2026-11-01)

- Placement: private developer CLI package `tools/tamil-pdf-extract/`, not a
  Cargo crate and not in the public release allowlist. The package uses pypdf
  only for PDF structure and calls the existing Rust dispatcher for all
  LT-TM decoding. Its locked dependency set is local to the tool.
- Contract and limits: see [PDF extractor v0.1](specs/pdf-extract-v0.1.md).
  Decoding requires Type 0 `/Identity-H` plus an exact spot-checked face name:
  `LT-TM-Nehru`, `LT-TM-Nakkeran`, `LT-TM-Narmada`, `LT-TM-Nila,Bold`, or
  `LT-TM-Sindhu`; only an optional six-letter uppercase subset prefix is
  ignored. Other LT-TM styles/families and other font families are reported
  with original bytes and are not decoded. Default JSONL extraction does not
  OCR or reflow text.
- Source run: the local 2003 Tamilmann PDF (digest in the spec) has 351 pages,
  24,356 text-showing operations and 38 font names. The five allowed families
  decoded 103 runs with no strict errors. The remaining 24,253 runs across 31
  font names are retained as unsupported, including unverified LT-TM faces,
  TTC fonts and Times. The walk found one invoked image XObject, no inline
  images and no forms. Independent PDFium text-page extraction contained all
  103 raw CID sequences. Rendered pages 1, 3, 5, 6, 16, 17, 27, 40, 60 and 78
  were spot-checked; the title and visible decoded headings compared matched.
  The independent raw-code check does not validate Unicode mappings, and the
  visual review is not a full audit of every run. This does not establish
  complete extraction of the PDF or complete code-table validation for the
  allowed faces. The [Markdown review ledger](specs/codec-lt-tm-pdf-review.md)
  lists all 103 decoded runs with their raw CIDs and output scalars.
- Implementation: JSONL CLI records retain page, content/form path, operator,
  font metadata, raw bytes, Identity-H code units, status, and decoded text or
  error. Synthetic tests cover `Tj`, `TJ`, `'`, `"`, fragment joining, subset
  font names, unsupported faces, malformed codes, encrypted/invalid PDFs,
  forms/cycles, image counting and escaped CLI output.
- Checks: `just test-pdf-extract` passed (10 tests). The full
  `just agent-pre-stop-gate` passed: Clippy, 25 Rust tests and doctests,
  115 harness tests, 27,644 Rust golden vectors, 27,656 Python golden cases,
  27,654 Vitest cases, and the 10 PDF extractor tests. The locked Python
  binding, Node/browser WASM packages, and declarations were rebuilt. Dart was
  not changed by this tool-only work. This private tool is committed on `master`.
- OCR fallback update (2026-11-01): added an optional `--ocr-markdown` path
  using pypdfium2/Pillow plus a locally installed Tesseract Tamil model. It
  renders each page and writes a page-numbered, explicitly unverified OCR draft
  separately from JSONL. OCR output and joiners are preserved; no OCR text or
  PDF content is bundled. The Rust dispatcher and five-face decoder are
  unchanged.
- Updated checks: `just test-pdf-extract` passed (13 tests). A one-page PDFium
  render/Tesseract smoke run produced Tamil output and retained ZWNJ scalars.
  `just check-unicode` passed (27,644 active vectors; release copies
  verified). `just agent-post-edit` and `just agent-pre-stop-gate` were
  attempted but stopped immediately because Cargo is missing from this local
  shell; Clippy, Rust tests, and parity were not rerun.
- OCR quality spot-check (2026-11-01): used Tesseract 5.4.0.20240606 with its
  standard `tam` model on PDF pages 1, 81, and 290 rendered at 300 DPI, using
  page segmentation modes 3 and 6. The cover and one-column prose were mostly
  readable as drafts, with recognition and spacing errors. The two-column
  index page had fragmented/misordered lines and a misread heading. Mode 3
  emitted 15, 86, and 43 U+200C scalars on those pages respectively; mode 6
  emitted 14, 87, and 45. No verified ground truth was available, so CER/WER
  were not calculated. Tesseract is not accepted as a verified full-book
  transcription source; per the user's direction, no alternate OCR engine is
  being set up in this pass.
- Remaining: JSONL font decoding still leaves 24,253 runs unsupported; OCR is
  an unverified reading aid, not validated text. Keep the current Tesseract
  draft path as-is. Inspect the 31 unsupported
  font names for any PDF-backed Unicode maps and retain raw codes when none
  exist. The separate Punarchi source audit is deferred at user direction; its
  sources and resume criteria are preserved in the handoff above.

Never put registry credentials in the handoff, repository, build artifacts, or
chat. Do not claim complete linguistic support from the bootstrap suites.
