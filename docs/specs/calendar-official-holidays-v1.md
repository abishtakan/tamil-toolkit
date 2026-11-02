# Official annual holiday schedules v1

Status: implemented as a bounded source-data operation; its golden suite remains
planned pending calendar-owner review. This operation publishes the four
authority/year schedules named below. It is not a panchangam or observance
engine and does not calculate future holiday dates.

## Operation

`calendar_official_holidays` accepts exactly:

```json
{"jurisdiction":"TN","year":2025}
```

`jurisdiction` is `TN` or `SL`. Only the following pairs are available:

| Jurisdiction | Years | Authority and scope |
| --- | --- | --- |
| `TN` | 2025, 2026 | Tamil Nadu Government annual public-holiday orders for state government offices and commercial/co-operative banks |
| `SL` | 2026, 2027 | Central Bank of Sri Lanka annual Bank/Public/Mercantile holiday table |

Success returns `jurisdiction`, `year`, `schedule_id`, `source_id`, source
description, `source_url`, `source_sha256`, `scope_note`, and an ordered
`reuse_terms_status`, and `holidays` array. The terms field is currently
`unverified` for every schedule; it does not grant a reuse license. Each entry contains a validated Gregorian `date`, the
authority's published English name, and the authority's applicability
`categories`. Same-date rows remain separate when the authority lists separate
holidays. Names are not translated, normalized to a different publisher, or
merged. Sri Lankan category codes map directly as B=`bank`, P=`public`, and
M=`mercantile`; Tamil Nadu entries use `state_government`, `commercial_banks`,
and `cooperative_banks`. The bank-account closing day is categorized only for
commercial and co-operative banks.

Tamil Nadu orders state that their named holidays are in addition to Sundays.
The Sri Lankan table separately says Saturdays and Sundays are bank holidays.
Those weekly rules are reported in `scope_note`; the operation does not expand
them into dated entries. The data does not infer a holiday from a festival,
religious observance, lunar limb, or another year.

Validation order is exact object shape, supported jurisdiction, safe integer
year, then schedule lookup. Errors are `invalid calendar input`,
`unsupported calendar jurisdiction`, `expected an integer in the supported
range`, or `official holiday schedule unavailable for jurisdiction/year`.
Years outside the four authority/year pairs fail explicitly. No inferred or
empty schedule is returned.

## Provenance and coverage limits

Canonical rows live in `lexicon/calendar-official-holidays.toml`; `build.rs`
validates jurisdiction, year, date, category, source URL, and source metadata,
then compiles static tables into Rust. Python, Node/browser WASM, and Dart call
the shared Rust dispatcher.

The 2025 Tamil Nadu source is Government of Tamil Nadu, G.O. Ms. No. 792,
Public (Miscellaneous), 22 November 2024, Annexure in Extraordinary issue 375,
PDF pages 1–3. The 2026 source is G.O. Ms. No. 708, 11 November 2025,
Annexure in Extraordinary issue 721, PDF pages 1–3. The official PDF URLs are
retained in the data. The Government publication viewer exposed their pages,
but direct official-host download timed out during this acquisition; no local
PDF digest is claimed, so both return `source_sha256: null`.

The Sri Lanka sources are the Central Bank of Sri Lanka's [Bank Holidays for
2026](https://www.cbsl.gov.lk/en/about/about-the-bank/bank-holidays-2026) and
[Bank Holidays for
2027](https://www.cbsl.gov.lk/en/about/about-the-bank/bank-holidays-2027)
tables. The downloaded official HTML bytes are pinned respectively as
`5d2c3f0b4e83786479acd30335347c5e7f0bc7d7c2d5af8e67cebddfe0590c84` and
`9071010e6d253e72aee4cdd40057cebc2dfc98e45e713de65ceb9d209cb09eb9`.

Reuse terms have not been established for any of these four sources. The
projection retains this as `reuse_terms_status: "unverified"`; no source
license or government open-data license is implied.

The schedule sizes are TN 2025: 24 named rows, TN 2026: 24, SL 2026: 26, and
SL 2027: 25. TN 2025/2026 source copies and Tamil Nadu archive bytes remain
unavailable for independent re-hashing. No other state, jurisdiction, year,
issuer, work-closure policy, or legal interpretation is covered. Holiday
edition changes need a new schedule ID and source record; existing schedule
IDs are immutable snapshots. The suite `calendar_official_holidays.jsonl`
contains four full schedule expectations plus unsupported-year and invalid
jurisdiction cases and remains `planned`.
