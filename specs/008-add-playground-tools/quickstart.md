# Quickstart: Validating New Playground Tools

This guide outlines end-to-end verification steps for the three new interactive tools in the playground.

---

## 1. Prerequisites & Setup
Ensure dependencies and tools are built and available:

```bash
# Verify playground dependencies
pnpm --filter tamil-toolkit-playground test
```

---

## 2. Validation Scenarios

### Scenario 1: Traditional Fractions & Epigraphical Symbol Explorer
1. Navigate to **Public Tools** → **பழந்தமிழ் பின்னங்கள் & குறியீடுகள் (Fractions & Symbols)**.
2. Select the category **பின்னங்கள் (Fractions)**.
3. Click on the symbol `காணி` (`𑿀`).
4. **Expected**:
   - Inspector displays `𑿀` (Codepoint `U+11FC0`).
   - Rational fraction displays `1/80` (Decimal `0.0125`).
   - Tapping "Copy Symbol" copies `𑿀` to clipboard with a toast notification.
5. In the Search/Lookup input, type `0.75` or `3/4`.
6. **Expected**:
   - Matching traditional symbol `முக்கால்` (`¾` / traditional notation) is highlighted.

### Scenario 2: Tamil Letter & Uyirmei Morphological Decomposer
1. Navigate to **Developer Tools** → **சொல் & எழுத்து பகுப்பாய்வி (Letter & Syllable Analyzer)**.
2. Type or paste the word `தமிழ்நாடு`.
3. **Expected**:
   - Five distinct syllable chips appear: `த`, `மி`, `ழ்`, `நா`, `டு`.
   - Selecting `மி` reveals:
     - Base consonant: `ம்` (*மெய்*)
     - Vowel: `இ` (*உயிர்*)
     - Vowel sign: `ி` (*இகரக் குறி*)
     - Classification: *உயிர்மெய்*
   - Summary counter reports: 5 syllables (4 உயிர்மெய், 1 மெய்).

### Scenario 3: Tamil Unicode Text Normalizer
1. Navigate to **Developer Tools** → **ஒருங்குறி சீரமைப்பி (Unicode Normalizer)**.
2. Paste text with decomposed or anomalous diacritics.
3. **Expected**:
   - Normalizer automatically detects and applies NFC canonical normalization.
   - Diagnostic panel shows anomaly count and highlights repaired characters.
   - Tapping "Copy Normalized" copies clean canonical text.

---

## 3. Automated Verification Commands

```bash
# Run unit & ergonomics tests covering new tool components
pnpm --filter tamil-toolkit-playground test

# Verify production build compilation
pnpm --filter tamil-toolkit-playground build

# Run project quality gate
just agent-post-edit
```
