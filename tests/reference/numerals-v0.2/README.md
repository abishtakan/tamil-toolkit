# Fraction and Gregorian date evidence

Unicode 17 numeric properties supply all 20 Tamil fraction characters (18
distinct rational values) and decimal digits. CLDR 49 calendar XML fragments
retain the published month/day/pattern facts; the metadata records the hashes
of both the upstream XML and extracted bytes. Unicode/CLDR data uses the license
in `../unicode-17.0.0/LICENSE.txt` (Unicode-3.0).
CLDR data copyright: 1991–2026 Unicode, Inc.; the original upstream notices and
source URLs are retained through this attribution and the reference manifest.

ICU4J 79.1 reports bundled CLDR `49.0.0.0`. `calendar-data.json` records its
resolved Tamil calendar symbols, including inherited abbreviated month names.
`icu-dates.jsonl` freezes 154 civil dates, every style, TN/SL locale, and
Latin/tamldec digits. Its GregorianCalendar has its cutover set to the earliest
possible instant, UTC time zone, and strict validation. Python's independent
Gregorian date implementation verifies the resulting weekdays.

`fraction-inputs.json` is an exact-rational acceptance domain. Python Fraction
reduces those values; `icu-components.jsonl` freezes independent CLDR spellout
of all components. `profile.json` records three common lexical names and the
explicit division-reading template, with primary sources. Only lexical facts
were extracted; no government/textbook/software-help prose or images are
redistributed. Common names are region invariant; other readings reuse the
existing TN/SL spellout profiles. No generic Tamil inflection engine is hidden
in fixture generation.

Normal CI/development requires no Java or ICU. Regenerate/check goldens offline:

```sh
uv run --locked python tools/generate_numerals_formats_golden.py --check
```

To reproduce calendar evidence, obtain and verify the ICU jar pinned in
`sources.json`, write the frozen rows' dates to a newline-separated ISO date file,
then run from the repository root:

```sh
java -cp /path/to/icu4j-79.1.jar tools/reference/CalendarReference.java dates.txt target/calendar-data.json target/icu-dates.jsonl
```

Compare the calendar data structurally and the date JSONL byte for byte. The
existing `tools/reference/NumeralReference.java` reproduces component spellings
using the pinned CLDR 49 TN/SL rules described in the v0.1 evidence README;
its integer input is the sorted set of absolute reduced numerator/denominator
values. Use an empty money-input file for that reference run. Production code,
bindings, and the oracle continue to execute only the Rust implementation.
