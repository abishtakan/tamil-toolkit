# Independent numeral evidence

`sources.json` pins CLDR 49 input bytes/extracted facts and ICU4J 79.1 output
digests. CLDR data uses the Unicode license at `../unicode-17.0.0/LICENSE.txt`.
`profile.json` declares the toolkit's range, labels, and SL lakh-stem override;
the linguistic sources and limits are in `docs/specs/numerals-v0.1.md`.

The golden compiler reads frozen ICU results. It does not execute a Python
number-spelling implementation, import Rust, or read the runtime lexicon.
Normal development and CI need neither Java nor ICU. Regenerate/check goldens:

```sh
uv run --locked python tools/generate_numerals_golden.py --check
```

To independently reproduce the ICU evidence, obtain the pinned ICU4J jar from
the URL in `sources.json`, verify its SHA-256, and use Java 25 source-file mode
(or compile the Java source with a compatible JDK). Extract the `rbnfRules` text
from `ta-rbnf.xml`'s SpelloutRules group into a UTF-8 TN rules file. Create SL
rules by applying exactly `profile.json`'s `sl_lakh_from` -> `sl_lakh_to` override
to those rules. Write `integer_values()` and `money_values()` from the golden
compiler into two newline-separated integer files, then run:

```sh
java -cp /path/to/icu4j-79.1.jar tools/reference/NumeralReference.java rules-TN.txt rules-SL.txt values.txt money.txt icu-integers.jsonl icu-money.jsonl
```

Compare both output digests with the manifest before replacing evidence. The
reference tool normalizes strings to NFC and serializes scalar escapes. It uses
ICU RBNF for standalone and noun/cardinal spellings, and ICU DecimalFormat with
exact BigDecimal minor units for 3-2 numeric grouping. Runtime rules and expected
output share the published linguistic specification, but use separate engines.
