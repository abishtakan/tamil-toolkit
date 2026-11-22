# Phase 7 legacy Tamil CID profiles: Senthamil, Shree-Tam, Softview & TBO

Status: Phase 7B engineering contract (2026-11-22).

## Provenance and profile inventory

Each canonical mapping table is a normalized 1:1 Tamil Unicode projection from
the public `AzhagiPlus-Portable.zip` archive (SHA-256
`e5fbf4b1f9a5533ac70021119641c51ddfa1df99c54162b9fa74e32ae1c1d510`, the same
archive documented in [LT-TM](codec-lt-tm.md) and [Vanavil](codec-vanavil.md)).
Original archive files are not bundled; upstream terms remain in effect.

| Profile | Canonical Lexicon | Azhagi+ Source File | Source SHA-256 | Keys |
| --- | --- | --- | --- | ---: |
| `senthamil-cid-v1` | `lexicon/senthamil.toml` | `AzhagiPlus-Tamil-Stmzh-PhoneticTransliteration.txt` | `17b8dbbb52bcbb99...` | 308 |
| `shree-tam-cid-v1` | `lexicon/shree_tam.toml` | `AzhagiPlus-Tamil-Shree-PhoneticTransliteration.txt` | `8735d58b67f5dc18...` | 316 |
| `softview-amudham-cid-v1` | `lexicon/softview.toml` | `AzhagiPlus-Tamil-Amudham-PhoneticTransliteration.txt` | `146f5c0155dbcbc9...` | 313 |
| `tbo-tboomi-cid-v1` | `lexicon/tbo.toml` | `AzhagiPlus-Tamil-TBoomiS-PhoneticTransliteration.txt` | `c039c54eba2452ee...` | 316 |

Full 64-hex SHA-256 digests are pinned inside each `lexicon/*.toml` file and
verified at build time by `crates/tamil-codec/build.rs`.

## Shared CID API contract

All four profiles follow the exact same 16-bit CID/text contract as
`vanavil-avvaiyar-cid-v1` and `lt-tm-indoword-cid-v1`:

- **Senthamil:** `senthamil_codes_to_unicode`, `senthamil_text_to_unicode`,
  `unicode_to_senthamil_codes`, `unicode_to_senthamil_text`
- **Shree-Tam:** `shree_tam_codes_to_unicode`, `shree_tam_text_to_unicode`,
  `unicode_to_shree_tam_codes`, `unicode_to_shree_tam_text`
- **Softview:** `softview_codes_to_unicode`, `softview_text_to_unicode`,
  `unicode_to_softview_codes`, `unicode_to_softview_text`
- **TBO:** `tbo_codes_to_unicode`, `tbo_text_to_unicode`,
  `unicode_to_tbo_codes`, `unicode_to_tbo_text`

- Longest-key matching with `max_key_cids = 3` and NFC output.
- Default `errors = "strict"`; `errors = "preserve"` retains unmapped valid
  non-surrogate BMP code points unchanged (joiners are never stripped).
- Encoding normalizes to NFC, uses greedy longest match, and verifies a strict
  decode round trip before returning.
- TN and SL dialects are invariant (`dialect: "COMMON"`).
