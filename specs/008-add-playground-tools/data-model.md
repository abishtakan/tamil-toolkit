# Data Model: Additional Interactive Linguistic & Epigraphical Tools

## 1. Traditional Fraction & Epigraphical Symbol Entity

### TraditionalSymbol
Represents a historic Tamil fraction or epigraphical measurement glyph.

```typescript
export interface TraditionalSymbol {
  codepoint: string;          // Hex escape, e.g. "U+11FC0" or "\u{11FC0}"
  glyph: string;              // Rendered Unicode character, e.g. "𑿀"
  name_ta: string;            // Classical Tamil name, e.g. "காணி"
  name_en: string;            // Transliterated / English name, e.g. "Kani"
  category: "fraction" | "land" | "volume" | "currency";
  rational: {
    numerator: number;
    denominator: number;
  } | null;
  decimal_value: number | null; // e.g. 0.0125
  period_usage: string;       // Historical context, e.g. "Sangam / Chola inscriptional"
}
```

### SymbolSearchFilter
State for searching and filtering the epigraphical catalog.

```typescript
export interface SymbolSearchFilter {
  query: string;              // Free-text query (name, number, or codepoint)
  category: "all" | "fraction" | "land" | "volume" | "currency";
  viewMode: "grid" | "table";
}
```

---

## 2. Letter & Uyirmei Morphological Decomposition Entity

### AnalyzedSyllable
Represents the structural deconstruction of a single Tamil grapheme cluster.

```typescript
export type TamilCharKind =
  | "uyir"          // Pure vowel (அ, ஆ, ...)
  | "mei"           // Pure consonant with pulli (க், ங், ...)
  | "uyirmei"       // Syllabic consonant + vowel (க, கா, ...)
  | "aaytham"       // Visarga / Aytham (ஃ)
  | "grantha"       // Grantha consonant / syllable (ஜ, ஷ, ...)
  | "numeral"       // Tamil digit / number glyph
  | "symbol"        // Traditional fraction / punctuation / Latin
  | "other";

export interface AnalyzedSyllable {
  index: number;
  raw: string;                // The composite letter, e.g. "பொ"
  kind: TamilCharKind;
  base_consonant: string | null; // e.g. "ப்"
  vowel: string | null;          // e.g. "ஒ"
  vowel_sign: string | null;     // e.g. "ொ"
  vowel_sign_name_ta: string | null; // e.g. "ஒகரக் குறுக்கம் / இரட்டைக்கொம்பு + துணைக்கால்"
  codepoints: string[];          // e.g. ["U+0BAA", "U+0BCA"]
}

export interface WordAnalysisReport {
  word: string;
  syllables: AnalyzedSyllable[];
  total_letters: number;
  vowel_count: number;
  consonant_count: number;
  uyirmei_count: number;
  grantha_count: number;
  has_anomalies: boolean;
}
```

---

## 3. Unicode Normalizer Diagnostic Entity

### NormalizationDiff
Represents the audit result of normalizing and repairing text.

```typescript
export interface NormalizationAnomaly {
  position: number;
  type: "duplicate_pulli" | "split_vowel" | "stray_format_control" | "non_nfc";
  description_ta: string;
  description_en: string;
  original_snippet: string;
  repaired_snippet: string;
}

export interface NormalizationResult {
  originalText: string;
  normalizedTextNFC: string;
  normalizedTextNFD: string;
  isClean: boolean;
  anomalyCount: number;
  anomalies: NormalizationAnomaly[];
  processingLatencyMs: number;
}
```
