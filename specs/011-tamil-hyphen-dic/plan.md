# Implementation Plan: Phonotactically Verified Hunspell / TeX Hyphenation Dictionary & LibreOffice Extension (`tamil-hyphen-dic`)

**Branch**: `011-tamil-hyphen-dic` | **Date**: 2026-11-06 | **Spec**: [specs/011-tamil-hyphen-dic/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/011-tamil-hyphen-dic/spec.md)

**Input**: Feature specification from `/specs/011-tamil-hyphen-dic/spec.md`

## Summary

Build an algorithmic pattern generation engine, automated Liang verification harness, LibreOffice `.oxt` extension packager, and web Playground download card powered by the `tamil-hyphen` phonotactic engine. The resulting `hyph_ta_IN.dic` achieves 100% compliance on the `hyphen_syllable.jsonl` golden corpus, completely eliminating legacy 2018 SMC defects (severed Grantha ligatures, single-letter orphan splits, and mid-cluster coda splits) across LibreOffice, Adobe InDesign, and Scribus for `ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, and generic `ta`.

## Technical Context

**Language/Version**: Modern Stable Rust (MSRV 1.83+) and TypeScript (ES2022 / React 18 for Playground).

**Primary Dependencies**: `tamil-core`, `tamil-hyphen`, `zip` (for `.oxt` archive creation in Rust), `clap` (for CLI subcommands), `serde` / `serde_json` (for golden corpus inspection).

**Storage**: File-based artifacts (`hyph_ta_IN.dic`, `tamil-hyphenation.oxt`, XML configuration files in `dist/`).

**Testing**: `cargo test -p tamil-hyphen`, `cargo test -p tamil-toolkit`, `vitest` in playground.

**Target Platform**: Cross-platform (Windows, macOS, Linux, Web/WASM). Output artifacts run in LibreOffice Writer, Adobe InDesign, and Scribus.

**Project Type**: Rust core library module + CLI tool + Desktop distribution bundle (`.oxt`) + Web UI integration.

**Performance Goals**: Pattern synthesis and dictionary serialization completes in < 50ms; automated verification of 120+ words completes in < 200ms.

**Constraints**: Dictionary file size < 30 KB; strictly zero broken diacritics or orphaned line-start characters.

**Scale/Scope**: Covers 100% of standard Tamil orthography, Grantha ligatures (`க்ஷ`, `ஸ்ரீ`), Aytham (`ஃ`), and all registered Tamil locales (`ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, `ta`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Rust Owns Linguistic Behavior**: **PASS**. Pattern synthesis algorithm is implemented purely in Rust (`crates/tamil-hyphen/src/dic.rs`). Web and packaging tools consume the compiled Rust output.
- **Principle II: Inspect Tamil by Scalars**: **PASS**. Pattern weights are strictly anchored to Unicode scalar codepoints (`\u{0BCD}`, `\u{0BBF}`, `\u{0BC0}`, etc.), never rendered visual approximations.
- **Principle III: Golden Vectors Precede Implementation**: **PASS**. Automated pattern simulator validates against `tests/golden/hyphen_syllable.jsonl`.
- **Principle IV: Separation of Lexical Data and Engine Logic**: **PASS**. Phonotactic patterns are synthesized algorithmically from Tamil grammar rules rather than unvetted static lists.
- **Principle V: Pluricentric Dialect Scope & Regional Invariance**: **PASS**. Registered across Indian and Sri Lankan locales (`ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, `ta`).
- **Principle VI: Platform-Conforming Distribution & Policy-Governed Releases**: **PASS**. Follows `.oxt` standard and upstream SMC `ta_IN` directory conventions.
- **Principle VII: Explicit Guarantees & Rigorous Quality Gates**: **PASS**. Quality gates verify 0 broken diacritics and benchmark against legacy SMC file.

## Project Structure

### Documentation (this feature)

```text
specs/011-tamil-hyphen-dic/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── cli-contract.md
│   └── bundle-schema.md
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
crates/tamil-hyphen/
├── src/
│   ├── dic.rs           # Algorithmic Liang pattern synthesizer & .dic serializer
│   ├── verify_dic.rs    # Simulated Liang pattern evaluator for tests
│   ├── oxt.rs           # .oxt ZIP archive packager (XML generator + ZIP writer)
│   ├── lib.rs           # Public exports (export_dictionary, package_oxt, verify_patterns)
│   └── ...
├── tests/
│   ├── dic_tests.rs     # Verification against tests/golden/hyphen_syllable.jsonl
│   └── legacy_comparison_tests.rs # Automated comparison against 2018 SMC dic
└── Cargo.toml           # Added zip dependency (with default-features = false, features = ["deflate"])

crates/tamil-toolkit/
├── src/
│   ├── bin/
│   │   └── tamil-toolkit.rs # CLI subcommands: `hyphen export-dic` and `package-oxt`
│   └── lib.rs

dist/
├── dictionaries/
│   └── hyph_ta_IN.dic   # Generated production dictionary
├── tamil-hyphenation.oxt# Built LibreOffice extension
└── upstream-smc/
    ├── ta_IN/
    │   └── hyph_ta_IN.dic # Upstream replacement drop-in
    └── UPSTREAM_PR.md   # Upstream contribution description and benchmark data

docs/integrations/
├── libreoffice.md       # LibreOffice installation & setup guide
├── indesign.md          # Adobe InDesign dictionary setup guide
└── scribus.md           # Scribus dictionary setup guide

playground/
├── src/
│   ├── components/
│   │   └── public-tools/
│   │       └── HyphenatorTool.tsx # Added "Integrations & Downloads" card (.oxt download)
│   └── lib/i18n.ts      # Bilingual labels for extension download & setup guide
```

**Structure Decision**: Integrated pattern generation and simulated verification directly into `tamil-hyphen` crate for zero-overhead validation against golden vectors; exposed CLI commands in `tamil-toolkit`; built extension `.oxt` output into `dist/` and provided web download in the Playground.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Adding `zip` dependency to `tamil-hyphen` | Creating `.oxt` extension requires standard deflate ZIP packaging directly from the toolkit engine | Shelling out to external `zip` CLI is non-portable across Windows/Linux/macOS |

## Long-Term Integration Roadmap: Word & Google Docs

Documented in [docs/integrations/word-googledocs-roadmap.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/docs/integrations/word-googledocs-roadmap.md) and repository [ROADMAP.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/ROADMAP.md):
- **Phase 1 (Live)**: Web Playground clipboard workflow with Unicode Soft Hyphens (`\u{00AD}`) maintaining zero-width on the same line and breaking dynamically under Justify (`Ctrl + J`).
- **Phase 2 (Target v0.2.0)**: Headless OpenXML DOCX batch processing via CLI (`tamil-toolkit hyphen process-docx`) and Python SDK.
- **Phase 3 (Target v0.3.0)**: Microsoft Word cross-platform Web Add-in (`Office.js` taskpane) powered by local WebAssembly.
- **Phase 4 (Target v0.4.0)**: Google Docs Workspace Add-on (Apps Script / canvas wrapper).
- **Phase 5 (Exploration)**: Windows Linguistic Services and macOS CoreText system proofing providers.
