# `tamil-translit` v0.1: Orthographic Romanization & Deterministic Offline Input

Status: Phase 8 engineering contract (2026-11-22). Crate: `crates/tamil-translit`
(Rank 2, depending only on `tamil-core` Rank 0 and `tamil-norm` Rank 1).

## 1. Supported Schemes

| Scheme ID | Category | Directions | Description |
| --- | --- | --- | --- |
| `iso-15919` | Scholarly | `to_latin`, `to_tamil` | Lossless ISO 15919 Tamil orthographic romanization (`ā, ī, ū, ē, ō, ḵ, ṅ, ñ, ṭ, ṇ, ṉ, ṟ, ḷ, ḻ, ś, ṣ`). |
| `madras-lexicon` | Scholarly | `to_latin`, `to_tamil` | Lossless University of Madras *Tamil Lexicon* (MTL) scheme (`ā, ī, ū, ē, ō, ḥ, ṅ, ñ, ṭ, ṇ, ṉ, ṟ, ḷ, ḻ, ś, ṣ`). |
| `itrans` | Scholarly (ASCII) | `to_latin`, `to_tamil` | Lossless ASCII ITRANS 5.3 Tamil scheme (`aa, ii, uu, E, O, q, ~N, ch, ~n, T, N, ^n, R, L, zh, sh, Sh`). |
| `harvard-kyoto` | Scholarly (ASCII) | `to_latin`, `to_tamil` | Lossless ASCII Harvard-Kyoto Tamil scheme (`A, I, U, E, O, H, G, J, T, N, X, R, L, Z, M, S`). |
| `tamil99` | Keyboard Layout | `to_tamil` | Official Government of Tamil Nadu TamilNet'99 stateful keyboard layout (auto-pulli gemination & homorganic nasal+stop rules). |
| `anjal-phonetic` | Phonetic Input | `to_tamil` | Deterministic Anjal / Murasu phonetic Roman-to-Tamil input (`ng, nj, th, zh, R, L, N`, positional `n` -> `ந`/`ன`). |
| `suratha-bamini` | Keyboard Layout | `to_tamil` | Deterministic Suratha Bamini live keystroke-to-Unicode composer (left-kombu `n`/`N`/`i` reordering, `;` pulli). |
| `phonetic-v1` | Phonetic / Tanglish | `to_tamil`, `to_latin` | Deterministic rule-based Phonetic/Tanglish v1 input and readable ASCII Tamil Romanization (statistical/noisy disambiguation stays in Phase 17). |

## 2. Public Operations

- `transliterate { text, scheme, direction } -> string`
  - `text`: required string (missing/non-string -> `"expected a string input"`).
  - `scheme`: required scheme ID from the table above (unknown -> `"unsupported transliteration scheme"`).
  - `direction`: `"to_tamil"` or `"to_latin"` (unknown -> `"unsupported transliteration direction"`).
  - Requesting `"to_latin"` on keyboard-only schemes (`tamil99`, `anjal-phonetic`, `suratha-bamini`) returns `"reverse transliteration is not supported for keyboard layout"`.
- `transliterate_schemes {} -> array`
  - Returns metadata objects `{ id, category, directions }` for all 8 schemes in deterministic order.

## 3. Guarantees & Boundaries

- All Tamil outputs are NFC-normalized.
- Non-Tamil punctuation, digits, whitespace, and invisible joiners (`ZWJ`, `ZWNJ`) are preserved and never silently dropped.
- Every Tamil vowel (`அ..ஔ`), Aytham (`ஃ`), consonant (18 native + 5 Grantha), `க்ஷ`, uyirmei, and mei form round-trips losslessly across all 4 scholarly schemes (`to_tamil(to_latin(s)) == normalize_nfc(s)`).
- TN and SL orthography is invariant for all 8 schemes (`dialect: "COMMON"`).
- Declarative tables live in `lexicon/translit.toml` (uniform readable NFC UTF-8 Tamil per Constitution 3.0.0) and compile at build time via `crates/tamil-translit/build.rs`.
