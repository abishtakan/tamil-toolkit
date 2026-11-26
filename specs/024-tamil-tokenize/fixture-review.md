# Phase 9 tokenizer fixture review

This view shows all 54 planned rows from [the golden suite](../../tests/golden/tokenize_v01.jsonl). Each expected word or sentence span is shown in order. The golden file carries the exact offsets, token kinds, sources, and Unicode exceptions.

∅ denotes empty text or an empty result. Bracketed labels show otherwise invisible characters. A decomposed label identifies a representation whose vowel signs can look the same as the composed spelling.

## Word tokens

| Fixture | Input | Expected spans |
| --- | --- | --- |
| `tokenize_empty` | ∅ | ∅ |
| `tokenize_whitespace` | `[SPACE][TAB][CR][LF]` | ∅ |
| `tokenize_decomposed_mixed` | `x கொ. 😀` (decomposed) | `x` · `கொ` (decomposed) · `.` · `😀` |
| `tokenize_ligatures` | `க்ஷொ ஶ்ரீ ஸ்ரீ க்[ZWJ]ஷ க்[ZWNJ]ஷ` (decomposed) | `க்ஷொ` (decomposed) · `ஶ்ரீ` · `ஸ்ரீ` · `க்[ZWJ]ஷ` · `க்[ZWNJ]ஷ` |
| `tokenize_mixed_symbols` | `[U+0BCD] 12.5 ௧௨ 👩[ZWJ]💻 ,` | `[U+0BCD]` · `12.5` · `௧௨` · `👩[ZWJ]💻` · `,` |
| `tokenize_space_with_attached_mark` | `[SPACE][U+0300]` | `[SPACE][U+0300]` |
| `tokenize_inflection` | `மரத்தில்` | `மரத்தில்` |
| `tokenize_honorific_word` | `திரு.குமார்` | `திரு.` · `குமார்` |
| `tokenize_initials_word` | `மு.க.குமார்` | `மு.க.` · `குமார்` |
| `tokenize_afternoon_word` | `பி.ப. 500` | `பி.ப.` · `500` |
| `tokenize_morning_word` | `மு.ப. 500` | `மு.ப.` · `500` |
| `tokenize_example_word` | `எ.கா. குமார்` | `எ.கா.` · `குமார்` |
| `tokenize_currency_word` | `ரூ.500` | `ரூ.` · `500` |
| `tokenize_stop_none` | `மற்றும் போன்ற மரத்தில்!` · `none` profile | `மற்றும்` · `போன்ற` · `மரத்தில்` · `!` |
| `tokenize_stop_conservative` | `மற்றும் போன்ற மரத்தில்!` · `conservative` profile | `போன்ற` · `மரத்தில்` · `!` |
| `tokenize_stop_broad` | `மற்றும் போன்ற மரத்தில்!` · `broad` profile | `மரத்தில்` · `!` |
| `tokenize_canonical_stop` | `போன்ற போன்ற[ZWJ] மற்றும்இ` (decomposed) · `broad` profile | `போன்ற[ZWJ]` · `மற்றும்இ` |
| `tokenize_stop_default` | `மற்றும்` | `மற்றும்` |

## Sentences

| Fixture | Input | Expected spans |
| --- | --- | --- |
| `tokenize_sentence_whitespace` | `[CR][LF][SPACE][TAB]` | ∅ |
| `tokenize_honorific_continuation` | `திரு.குமார்.` | `திரு.குமார்.` |
| `tokenize_honorific_hard` | `திரு.[CR][LF]குமார்.` | `திரு.` · `குமார்.` |
| `tokenize_honorific_fallback` | `திரு. X.` | `திரு.` · `X.` |
| `tokenize_initials_continuation` | `மு.க.குமார்.` | `மு.க.குமார்.` |
| `tokenize_initials_hard` | `மு.க.[CR][LF]குமார்.` | `மு.க.` · `குமார்.` |
| `tokenize_initials_fallback` | `மு.க. X.` | `மு.க.` · `X.` |
| `tokenize_afternoon_continuation` | `பி.ப. 500.` | `பி.ப. 500.` |
| `tokenize_afternoon_hard` | `பி.ப.[CR][LF]500.` | `பி.ப.` · `500.` |
| `tokenize_afternoon_fallback` | `பி.ப. X.` | `பி.ப.` · `X.` |
| `tokenize_morning_continuation` | `மு.ப. 500.` | `மு.ப. 500.` |
| `tokenize_morning_hard` | `மு.ப.[CR][LF]500.` | `மு.ப.` · `500.` |
| `tokenize_morning_fallback` | `மு.ப. X.` | `மு.ப.` · `X.` |
| `tokenize_example_continuation` | `எ.கா. குமார்.` | `எ.கா. குமார்.` |
| `tokenize_example_hard` | `எ.கா.[CR][LF]குமார்.` | `எ.கா.` · `குமார்.` |
| `tokenize_example_fallback` | `எ.கா. X.` | `எ.கா.` · `X.` |
| `tokenize_currency_continuation` | `ரூ.500.` | `ரூ.500.` |
| `tokenize_currency_hard` | `ரூ.[CR][LF]500.` | `ரூ.` · `500.` |
| `tokenize_currency_fallback` | `ரூ. X.` | `ரூ.` · `X.` |
| `tokenize_example_colon` | `எ.கா.: க.` | `எ.கா.: க.` |
| `tokenize_independent_terminator` | `திரு.! க.` | `திரு.!` · `க.` |
| `tokenize_decimal_quote` | `3.14!" க` | `3.14!"` · `க` |
| `tokenize_unknown_dotted` | `க. X.` | `க.` · `X.` |
| `tokenize_invariance_tn` | `மரத்தில்.[CR][LF]க` | `மரத்தில்.` · `க` |
| `tokenize_invariance_jaffna` | `மரத்தில்.[CR][LF]க` | `மரத்தில்.` · `க` |
| `tokenize_invariance_batticaloa` | `மரத்தில்.[CR][LF]க` | `மரத்தில்.` · `க` |
| `tokenize_invariance_vanni` | `மரத்தில்.[CR][LF]க` | `மரத்தில்.` · `க` |
| `tokenize_invariance_up_country` | `மரத்தில்.[CR][LF]க` | `மரத்தில்.` · `க` |
| `tokenize_sentence_profile_ignored` | `X.` · `broad` profile | `X.` |

## Invalid requests

| Fixture | Input | Expected error |
| --- | --- | --- |
| `tokenize_word_input` | `[]` | `expected tokenizer input object` |
| `tokenize_sentence_input` | `null` | `expected tokenizer input object` |
| `tokenize_word_text` | `{"text": false, "stopword_profile": "unknown"}` | `expected a string input` |
| `tokenize_sentence_text` | `{}` | `expected a string input` |
| `tokenize_word_profile_null` | `{"text": "", "stopword_profile": null}` | `expected stopword_profile to be a string` |
| `tokenize_word_profile_number` | `{"text": "", "stopword_profile": 4}` | `expected stopword_profile to be a string` |
| `tokenize_word_profile_unknown` | `{"text": "", "stopword_profile": "unknown"}` | `unsupported stopword profile` |
