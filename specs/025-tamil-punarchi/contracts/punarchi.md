# Interface Contract — Tamil Sandhi (`tamil-punarchi`)

**Status** — Proposed Phase 10 interface for `nannool-v1` (*Nannūl Eḻuttatikāram* **117 sūtras**: mandatory prerequisites `93–94`, `102–108`, `136` + Puṇariyal `151–257`). The [data model](../data-model.md) defines all entity invariants and the [precedence & inverse matrix](../research/05-precedence-and-inverse-matrix.md) defines stage ordering.

## 1. Dispatcher Operations

Use the existing `{ "op": string, "input": object }` envelope and existing success/error transports across Rust, Python, Node/Browser WASM, Dart, and `tamil-oracle`.

| Operation | Input | Result |
| --- | --- | --- |
| `punarchi_join` | Required `first: string`, `second: string`. Optional `profile: string` (default `"nannool-v1"`). Optional `context: object` (`relation?`, `subtype?`, `lexical_class?`, `poetic?`). | `PunarchiJoinResult` object with `profile`, `surface`, `transform`, `steps`, and `alternatives`. |
| `punarchi_split_candidates` | Required `surface: string`. Optional `profile: string` (default `"nannool-v1"`). Optional `poetic: boolean` (default `false`). | Array of dual-pruned `SplitCandidate` objects (`first`, `second`, `sutra`, `rule_id`, `transform`, `steps`, `split_byte`, `split_unit`). |
| `punarchi_rules` | Optional `profile: string` (default `"nannool-v1"`), optional `chapter: "ezhuttiyal" \| "padaviyal" \| "uyireeru" \| "meyyeeru" \| "urupu"`, optional `sutra: integer`. | Array of `SutraInventoryEntry` objects covering all matching sūtras from the 117-sūtra inventory (`93–94, 102–108, 136, 151..=257`). |

### Example `punarchi_join` Request & Response

Request:
```json
{
  "op": "punarchi_join",
  "input": {
    "first": "மரம்",
    "second": "ஐ",
    "profile": "nannool-v1",
    "context": { "relation": "vetrumai", "subtype": "case_2" }
  }
}
```

Response (`மரம் + ஐ → மரத்தை`, including Sūtra **252** *அத்தின் அகரம்* before Sūtra **164**):
```json
{
  "profile": "nannool-v1",
  "surface": "மரத்தை",
  "transform": "thirithal",
  "steps": [
    {
      "sutra": 219,
      "rule_id": "nannool_219_magara_elision",
      "stage": 1,
      "transform": "keduthal",
      "before": "மரம் + ஐ",
      "after": "மர + ஐ"
    },
    {
      "sutra": 244,
      "rule_id": "nannool_244_chariyai_attu",
      "stage": 2,
      "transform": "thonral",
      "before": "மர + ஐ",
      "after": "மர + அத்து + ஐ"
    },
    {
      "sutra": 252,
      "rule_id": "nannool_252_attin_akaram",
      "stage": 3,
      "transform": "keduthal",
      "before": "மர + அத்து",
      "after": "மரத்து"
    },
    {
      "sutra": 164,
      "rule_id": "nannool_164_kurriyalugaram_elision",
      "stage": 3,
      "transform": "keduthal",
      "before": "மரத்து + ஐ",
      "after": "மரத்த் + ஐ"
    },
    {
      "sutra": 204,
      "rule_id": "nannool_204_udalmel_uyir",
      "stage": 4,
      "transform": "iyalbu",
      "before": "மரத்த் + ஐ",
      "after": "மரத்தை"
    }
  ],
  "alternatives": [
    {
      "surface": "மரத்தினை",
      "transform": "thirithal",
      "steps": [],
      "required_context": null,
      "optional_variant": true,
      "poetic": false
    }
  ]
}
```
*(Note: `alternatives` carries the attested Sūtra 243 stacked-chariyai variant `மரத்தினை` with its full `steps` trace populated at runtime.)*

### Example `punarchi_split_candidates` Request & Response

Request:
```json
{
  "op": "punarchi_split_candidates",
  "input": {
    "surface": "கல்லடி",
    "profile": "nannool-v1"
  }
}
```

Response includes `{ "first": "கல்", "second": "அடி", "sutra": 205, "rule_id": "nannool_205_thanikkuril_otru", "transform": "thonral", "split_byte": 9, "split_unit": 2, ... }` alongside any other valid dual-pruned (phonotactically legal per `102–108` and forward-verified) rule-backed inversions.

## 2. Validation Order & Exact Error Messages

Validate input object first, then required string fields, then optional `profile`, then optional `context`/`chapter`/`sutra`. One Rust validator owns every message across all bindings.

| Invalid request | Exact error message |
| --- | --- |
| `input` is not a JSON object | `expected punarchi input object` |
| `first`, `second`, or `surface` is missing or not a string | `expected a string input` |
| `first` or `second` in `punarchi_join` is empty or whitespace-only | `punarchi: input components must not be empty` |
| `surface` in `punarchi_split_candidates` exceeds bounded limit (256 UTF-8 bytes) | `punarchi: surface input exceeds maximum length` |
| `profile` is present and not a string | `expected profile to be a string` |
| `profile` is an unsupported string (e.g., `"tolkappiyam-v1"`, `"unknown"`) | `unsupported punarchi profile` |
| `context` is present and not an object | `expected punarchi context object` |
| `context.relation` is not a valid string (`unspecified`, `vetrumai`, `alvazhi`) | `unsupported punarchi relation` |
| `context.subtype` is not a supported subtype or contradicts `relation` | `unsupported or incompatible punarchi subtype` |
| `context.lexical_class` is not a supported lexical class tag | `unsupported punarchi lexical class` |
| `context.poetic` or `poetic` is present and not a boolean | `expected poetic to be a boolean` |
| `chapter` in `punarchi_rules` is invalid | `unsupported punarchi chapter` |
| `sutra` in `punarchi_rules` is not in the 117-sūtra `nannool-v1` inventory | `punarchi sutra out of range` |

Additional unknown fields on the input object follow the existing dispatcher convention and are ignored.

## 3. Language Surfaces

- **Rust (`crates/tamil-punarchi`, re-exported as `tamil_toolkit::punarchi` after review):**
  - `punarchi_join(first: &str, second: &str, context: &PunarchiContext, profile: PunarchiProfile) -> Result<PunarchiJoinResult, PunarchiError>`
  - `punarchi_split_candidates(surface: &str, profile: PunarchiProfile, poetic: bool) -> Result<Vec<SplitCandidate>, PunarchiError>`
  - `punarchi_rules(profile: PunarchiProfile) -> &'static [SutraInventoryEntry]`
- **Python (`bindings/python`):**
  - `punarchi_join(first: str, second: str, *, profile: PunarchiProfile = "nannool-v1", context: PunarchiContext | None = None) -> PunarchiJoinResult`
  - `punarchi_split_candidates(surface: str, *, profile: PunarchiProfile = "nannool-v1", poetic: bool = False) -> list[SplitCandidate]`
  - `punarchi_rules(*, profile: PunarchiProfile = "nannool-v1", chapter: PunarchiChapter | None = None, sutra: int | None = None) -> list[SutraInventoryEntry]`
- **Node & Browser WASM (`bindings/js-wasm`):**
  - `punarchi_join(first: string, second: string, options?: { profile?: PunarchiProfile; context?: PunarchiContext }): PunarchiJoinResult`
  - `punarchi_split_candidates(surface: string, options?: { profile?: PunarchiProfile; poetic?: boolean }): SplitCandidate[]`
  - `punarchi_rules(options?: { profile?: PunarchiProfile; chapter?: PunarchiChapter; sutra?: number }): SutraInventoryEntry[]`
- **Dart (`bindings/dart-flutter`):**
  - `punarchiJoin(String first, String second, {String profile = 'nannool-v1', Map<String, Object?>? context})`
  - `punarchiSplitCandidates(String surface, {String profile = 'nannool-v1', bool poetic = false})`
  - `punarchiRules({String profile = 'nannool-v1', String? chapter, int? sutra})`
