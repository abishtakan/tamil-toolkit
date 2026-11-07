# Phase 0 Research: TeX/Hunspell Liang Patterns & LibreOffice OXT Packaging

**Feature**: `011-tamil-hyphen-dic`
**Date**: 2026-11-06
**Status**: Completed

## 1. Liang Hyphenation Pattern Mechanics for Tamil

### Background & Mechanism
The Frank Liang hyphenation algorithm (developed for TeX82 and adopted by Hunspell / `libhyphen` in LibreOffice, Adobe InDesign, and Scribus) uses substring patterns interleaved with integer weights (`0`-`9`).
- **Odd digits** (e.g. `1`, `3`, `5`) represent permissible hyphenation break points.
- **Even digits** (e.g. `2`, `4`) represent forbidden break points (inhibition weights).
- Higher digits strictly override lower digits (e.g., in a conflict between `1` and `2`, `2` wins and prevents the break).

### Legacy SMC Defects Identified
Our analysis of the legacy 2018 SMC `hyph_ta_IN.dic` revealed three major orthographic failure modes:
1. **Broken Grantha Conjuncts**: SMC contains `2க1` and `1ஷ`, with `2க்1` followed by `1`. This permits breaking inside the atomic ligature `க்ஷ` (`க்-ஷ`), destroying the character.
2. **One-Letter Orphan Breaks**: SMC declares patterns like `1அ1`, `1ஆ1` without enforcing `LEFTHYPHENMIN 2` in the header. If unconstrained, this permits awkward one-letter splits like `அ-ம்மா`.
3. **Multi-Consonant Coda Splits**: In consonant clusters (e.g., `ர்ப்ப்` in `துர்ப்பிரயோகம்`), SMC rules break after the first consonant with virama (`துர்-ப்பயன்பாடு`), which violates Tamil grammatical rules where all coda consonants belong to the preceding syllable nucleus.

### Algorithmic Pattern Design Strategy
Rather than statistical `patgen` training (which requires massive training corpora and often misses low-frequency clusters), `tamil-hyphen` will programmatically generate the minimal, complete set of Liang patterns from phonotactic rules:
- **Independent Vowels (Uyir)**: `1<Uyir>` (break before vowel if following a complete syllable, but never after an isolated first letter).
- **Consonants & Nuclei (Uyirmei)**: Break allowed before an onset consonant + vowel (`1C`), but inhibited before virama (`2C\u0BCD`).
- **Coda Sequences**: Pure consonants (`Mei`) get `2<Mei>` before and `1` only after the complete cluster when followed by a vowel or onset.
- **Grantha Ligatures**: Explicit blocking weights `2க்ஷ2`, `2க்ஷ`, `2ஸ்ரீ2` ensure ligatures are treated as atomic units.
- **Aytham**: `2ஃ` (break never permitted before Aytham).
- **Format Controls**: `2\u200D2` (never break around ZWJ).

---

## 2. LibreOffice Extension (.oxt) Architecture

### Bundle Specification
A LibreOffice extension (`.oxt`) is a standard ZIP archive with a specific XML structure:
```text
tamil-hyphenation.oxt
├── META-INF/
│   └── manifest.xml        # Declares extension configuration entrypoints
├── dictionaries.xcu        # Binds hyph_ta_IN.dic to linguistic service & locales
├── description.xml         # Extension name, version, publisher, display icons
├── hyph_ta_IN.dic          # Generated Liang pattern dictionary
└── LICENSE.txt             # MIT / LGPL / GPL tri-license
```

### Locale Binding (`dictionaries.xcu`)
To satisfy Clarification Q1 (multi-locale support across India, Sri Lanka, and the diaspora), `dictionaries.xcu` registers the hyphenation service for:
```xml
<prop oor:name="Locales" oor:type="oor:string-list">
    <value>ta-IN ta-LK ta-SG ta-MY ta</value>
</prop>
```
This guarantees LibreOffice Writer activates the hyphenator regardless of whether the document language is set to Tamil (India), Tamil (Sri Lanka), Tamil (Singapore), or unadorned Tamil.

---

## 3. Adobe InDesign & Scribus Integration

### Adobe InDesign
- InDesign uses `libhyphen` (Hunspell hyphenator).
- **Integration Path**: Users copy `hyph_ta_IN.dic` into InDesign's dictionary path (e.g. `Presets/Hunspell/` or application user data), or configure Hunspell hyphenation preferences in *Preferences > Dictionary > Tamil*.
- Once configured, setting paragraph text to Tamil and enabling InDesign's Paragraph Hyphenation applies our verified patterns with zero broken diacritics.

### Scribus
- Scribus natively uses `hyph_*.dic` files.
- Users place `hyph_ta_IN.dic` in Scribus's `share/scribus/dicts/` or `~/.scribus/dicts/`.
- Scribus immediately surfaces "Tamil (India)" under *Document Setup > Hyphenator*.

---

## 4. Upstream SMC Contribution Bundle

Upstream repository: `github.com/smc/hyphenation` (subpath `ta_IN/`).
We will prepare a clean PR kit in `dist/upstream-smc/`:
- `ta_IN/hyph_ta_IN.dic`: Drop-in replacement for upstream `ta_IN/hyph_ta_IN.dic`.
- `UPSTREAM_PR.md`:
  - Detailed rationale explaining why 1-letter breaks and split `க்ஷ` violate W3C Tamil Layout Requirements (tam-lreq).
  - Benchmark comparison table demonstrating 100% resolution of legacy defects.
  - Verification test instructions using standard TeX/Hunspell test tools.
