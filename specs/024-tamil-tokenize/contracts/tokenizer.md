# Interface Contract — Tamil Word and Sentence Tokenization

**Status** — Proposed Phase 9 interface. The [module contract](../../../docs/specs/tokenize-v0.1.md) defines how the boundaries are chosen.

## Dispatcher requests

Use the existing `{ "op": string, "input": object }` envelope and the existing success and error transports.

| Operation | Input | Result |
| --- | --- | --- |
| `tokenize_words` | Required `text` string. Optional `stopword_profile` string with one of `none`, `conservative`, or `broad`. Omission selects `none`. | Array of token objects, each containing a source span and a `kind`. |
| `segment_sentences` | Required `text` string. | Array of source span objects. Sentence segmentation is independent of word filtering. |

The source span fields are `text`, `start_byte`, `end_byte`, `start_unit`, and `end_unit`. Integers are absolute zero-based offsets into the original input, with exclusive ends. `kind` is one of `abbreviation`, `word`, `number`, or `other`. Each span belongs to one result list. Consumers can rely on its original positions after stopword filtering.

For `tokenize_words` with `input.text` equal to `x \u0b95\u0bc6\u0bbe. \ud83d\ude00` in JSON, the first Tamil token has this shape:

```json
{
  "text": "\u0b95\u0bc6\u0bbe",
  "start_byte": 2,
  "end_byte": 11,
  "start_unit": 2,
  "end_unit": 3,
  "kind": "word"
}
```

Empty or whitespace-only input returns `[]` for both operations. With `none`, non-whitespace text remains addressable even if the written sequence is malformed.

## Validation and errors

Validate the input object, then `text`, then the optional profile for `tokenize_words`. Keep the dispatcher’s existing missing-envelope errors. Use one Rust validator and preserve the message through each runtime’s existing error transport.

| Invalid request | Exact message |
| --- | --- |
| `input` is present and is anything other than an object | `expected tokenizer input object` |
| `text` is missing or is anything other than a string | `expected a string input` |
| `stopword_profile` is present and is anything other than a string, including `null` | `expected stopword_profile to be a string` |
| `stopword_profile` is an unsupported string | `unsupported stopword profile` |

Additional object fields follow the existing dispatcher convention and are ignored. The text contract covers Unicode scalar strings. Raw invalid JSON or a lone surrogate goes through existing transport validation. Those are transport cases outside the escaped tokenizer fixtures.

## Language surfaces

- **Rust** — `tamil_tokenize::tokenize_words(text, profile)` and `tamil_tokenize::segment_sentences(text)` accept borrowed text. A typed `StopwordProfile` represents the admitted options. Results own their collections and may borrow each span’s substring. NFC comparison and adapter serialization can allocate. The reviewed facade re-exports the crate and routes both operation names through `execute` and its operation inventory.
- **Python** — `tokenize_words(text, *, stopword_profile="none")` and `segment_sentences(text)` dispatch the requests and expose typed result mappings through the wrapper and its stubs.
- **Node and browser WASM** — `tokenize_words(text, stopwordProfile?)` and `segment_sentences(text)` share typed records in `createApi` and export from both entry points. Offsets are UTF-8 byte and written-unit offsets in JavaScript too.
- **Dart** — `tokenizeWords(text, {String? stopwordProfile})` and `segmentSentences(text)` deserialize typed records through the existing JSON C ABI. Omit an unspecified profile and forward a supplied string for Rust validation. This design introduces no new native entry points.

The same operation requests serve the oracle and the golden runners. Model encoders, prompt inference, and chunk budgeting have separate interfaces if pursued.
