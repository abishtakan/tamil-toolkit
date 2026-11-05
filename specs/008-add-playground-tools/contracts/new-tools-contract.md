# Contract: Additional Playground Tools Component & Dispatcher Contract

## 1. Dispatcher Operation Contracts

All three new tools communicate with the local Rust engine compiled to WebAssembly via the unified `execute(request: string): string` dispatcher.

### 1.1 Traditional Symbols & Fractions Contract
- **Operation**: `"symbol_info"`
  - Input: `{"op": "symbol_info", "input": text}`
  - Output: `{"codepoint": string, "name": string, "kind": string, "rational": {"numerator": number, "denominator": number} | null, "canonical_alternative": string | null, "source_version": string}`
- **Operation**: `"parse_fraction_symbol"`
  - Input: `{"op": "parse_fraction_symbol", "input": {"text": symbolChar}}`
  - Output: `{"numerator": number, "denominator": number}`
- **Operation**: `"format_mixed_fraction"`
  - Input: `{"op": "format_mixed_fraction", "input": {"negative": boolean, "whole": number, "numerator": number, "denominator": number, "digits": "tamil" | "ascii"}}`
  - Output: `string` (e.g. `"௧ 𑿀"` or `"1 ¾"`)

### 1.2 Letter & Uyirmei Analysis Contract
- **Operation**: `"get_letters"`
  - Input: `{"op": "get_letters", "input": text}`
  - Output: `string[]` (array of individual Tamil syllables / grapheme clusters)
- **Operation**: `"split_uyirmei"`
  - Input: `{"op": "split_uyirmei", "input": letter}`
  - Output: `[mei: string, uyir: string]` (e.g. `["த்", "இ"]` for `"தி"`, or `null` if not an uyirmei)
- **Operation**: `"compose_uyirmei"`
  - Input: `{"op": "compose_uyirmei", "input": {"mei": meiStr, "uyir": uyirStr}}`
  - Output: `string` (e.g. `"தி"`)
- **Operation**: `"inspect_tamil_string"`
  - Input: `{"op": "inspect_tamil_string", "input": text}`
  - Output: Diagnostic classification structure detailing letter counts and Unicode properties.

### 1.3 Normalizer Contract
- **Operation**: `"normalize_nfc"`
  - Input: `{"op": "normalize_nfc", "input": text}`
  - Output: `string` (canonical decomposed-to-composed standard Unicode)
- **Operation**: `"normalize_nfd"`
  - Input: `{"op": "normalize_nfd", "input": text}`
  - Output: `string` (canonical composed-to-decomposed standard Unicode)

---

## 2. Component Contract & Placement

```text
playground/src/components/
├── public-tools/
│   ├── CodecConverter.tsx
│   ├── NumeralFormatter.tsx
│   ├── CalendarExplorer.tsx
│   ├── TextSorter.tsx
│   └── SymbolsExplorer.tsx      <-- [NEW: Public Tool 5]
├── developer-tools/
│   ├── ScalarInspector.tsx
│   ├── LetterAnalyzer.tsx       <-- [NEW: Developer Tool 2]
│   ├── NormalizerTool.tsx       <-- [NEW: Developer Tool 3]
│   ├── DispatcherSandbox.tsx
│   ├── CodeGenerator.tsx
│   └── BatchProcessor.tsx
```

### UI Interaction Constraints
- Every tool MUST provide a top-right single-tap Copy button (`CopyButton`).
- On mobile viewports (<640px), primary actions MUST remain accessible in the thumb zone without clipping.
- State transitions MUST use 1px hairline border color transitions (`border-[var(--color-semman)]` or `border-[var(--color-sandhanam)]`) over 120–150ms.
- Strictly NO `scale-105` or bouncy hover transforms.
- All copy strings MUST be declared in `playground/src/lib/i18n.ts` under both `ta` and `en` dictionaries.
