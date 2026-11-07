# Quickstart: Tamil Hyphenation Dictionary & LibreOffice Extension

This guide details how to build, verify, package, and install the phonotactically verified Tamil hyphenation dictionary.

## 1. Prerequisites

- Modern Stable Rust (MSRV 1.83+)
- Node.js & pnpm (for playground web interface)
- LibreOffice (for end-to-end verification in Writer)

---

## 2. Generate the Dictionary (`hyph_ta_IN.dic`)

Run the export command from the repository root:
```bash
cargo run -p tamil-toolkit --bin tamil-toolkit -- hyphen export-dic --output dist/dictionaries/hyph_ta_IN.dic
```

**Expected Outcome**:
- `dist/dictionaries/hyph_ta_IN.dic` is generated (< 20 KB).
- Contains UTF-8 header, `LEFTHYPHENMIN 2`, `RIGHTHYPHENMIN 2`, and complete phonotactic rules.

---

## 3. Automated Verification Against Golden Corpus

Run the verification test suite:
```bash
cargo test -p tamil-hyphen --test dic_tests
```

**Validation Checks Performed**:
- Loads `hyph_ta_IN.dic`.
- Evaluates Liang pattern weights across 120+ words in `tests/golden/hyphen_syllable.jsonl`.
- Asserts **0 illegal line starts** (no initial `\u0BCD`, `\u0BBF`, `\u0BC0`, `\u0BBE`-`\u0BCC`, or `\u0B83`).
- Asserts **0 broken Grantha ligatures** (protecting `க்ஷ` and `ஸ்ரீ`).
- Asserts **0 one-letter orphan splits** (`அ-ம்மா`).

---

## 4. Benchmark Against Legacy SMC Dictionary

Run the automated comparative benchmark:
```bash
cargo test -p tamil-hyphen --test legacy_comparison_tests -- --nocapture
```

**Expected Output**:
```text
=== Tamil Hyphenation Dictionary Benchmark ===
Corpus: tests/golden/hyphen_syllable.jsonl (124 words)
Legacy 2018 SMC (hyph_ta_IN.dic):
  - Defective/Illegal breaks detected: 28
  - Broken Grantha ligatures (க்-ஷ): 4
  - Single-letter prefix breaks (அ-): 6
  - Mid-cluster coda splits: 18
Tamil Toolkit 2026 (hyph_ta_IN.dic):
  - Defective/Illegal breaks detected: 0 (100% compliant)
  - Broken Grantha ligatures: 0
  - Single-letter prefix breaks: 0
  - Mid-cluster coda splits: 0
```

---

## 5. Package the LibreOffice Extension (`tamil-hyphenation.oxt`)

Package the extension ZIP archive:
```bash
cargo run -p tamil-toolkit --bin tamil-toolkit -- hyphen package-oxt --input dist/dictionaries/hyph_ta_IN.dic --output dist/tamil-hyphenation.oxt
```

---

## 6. End-to-End Installation in LibreOffice Writer

1. **Install Extension**:
   - In LibreOffice, navigate to `Tools > Extension Manager...`
   - Click **Add...**, select `dist/tamil-hyphenation.oxt`, and accept.
   - Restart LibreOffice.
2. **Verify Hyphenation**:
   - Open LibreOffice Writer and paste a long Tamil paragraph (e.g. from the Playground sample).
   - Set language to **Tamil** (*Format > Character > Language: Tamil*).
   - Set alignment to **Justified** (*Format > Paragraph > Alignment: Justified*).
   - Turn on Hyphenation (*Format > Paragraph > Text Flow > Automatically*).
   - Notice that words break cleanly at syllable boundaries with **no awkward gaps and no broken pulli letters on newlines**.
