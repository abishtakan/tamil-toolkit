# South Indian 60-year name cycle v1

Status: planned calendar operation. The year-name mapping is sourced, but no
calendar suite activation or owner review is implied.

`tamil_year_cycle_info` accepts exactly
`{definition_id,solar_year,context}` and returns the selected definition,
solar-year identifier, one-based cycle index, romanized cycle name, anchor,
source identifier, source digest, regional scope, source description and
reference URLs. The year-enumeration response embeds the same metadata except
for the enclosing `definition_id`. Its
solar-year identifier is the same Gregorian year containing Chithirai 1 used
by `tamil_year_info`. The operation validates the selected profile context and
its declared year range before returning a name. Context validation occurs
before range validation. Thirukanitham allows solar-year identifiers 2023–2027
for its declared TN/SL coordinate boxes; Vakiya allows 1–9999 only at the
Ujjain reference station and uses Asia/Kolkata or Asia/Colombo for civil labels.
The cycle formula does not broaden these source-profile domains. It does not
derive or display a Thiruvalluvar-era year.

The canonical sequence uses the roman titles printed in *South Indian
Chronological Tables* (1889), Table C, printed pp. 18–19 / PDF pp. 30–31.
That table numbers one full cycle 1–60, identifies the Tamil solar-year
commencement, and anchors cycle index 1 (Prabhava) to English year 187. The
mapping is therefore
`index = 1 + (solar_year - 187) mod 60`, using Euclidean modulo. Source spellings
are exposed as plain-ASCII romanization of the table's roman labels; the scan's
footnote variants are documented in the source ledger. The table itself prints
the same roman label at rows 13 and 47, so the one-based index disambiguates
those positions. No publisher-specific modern Tamil spelling is asserted.

The anchor and sequence are checked against the Government of Madras *Census
of India 1941* circulars, Appendix VII, printed p. 19 / PDF p. 152 (1880 is
14 Vikrama; 1941 is 15 Vishu), and the Central Institute of Classical Tamil
three-page Tamil cycle table (including 1927–28 Prabhava, 1987–88 Prabhava,
2023–24 Sobhakrit and 2024–25 Krodhi). Source scan digests and exact locators
are kept in the source research ledger. The common cycle definition does not
choose an almanac publisher or alter either profile's solar ingress dates.

The suite `calendar_year_cycle.jsonl` remains planned. Current vectors cover
Thirukanitham in Chennai and Colombo and the Ujjain Vakiya civil definition.
The suite also covers negative/out-of-range years and invalid station context.
Unsupported profile names, malformed context shapes, and solar years outside
the selected profile's domain return explicit errors.
