# Independent core acceptance evidence

`unicode-17.0.0/` freezes official Unicode data for reproducible offline tests.
`sources.json` records each source URL, upstream SHA-256, checked-in SHA-256, and
any extraction. UnicodeData-Tamil.txt contains verbatim Tamil and Tamil Supplement
records selected from UnicodeData.txt; all other files are preserved whole.
Unicode data is redistributed under the accompanying Unicode License V3.

`core-profile.json` records the explicit acceptance scope and consonant-group
labels using Unicode sequence names. Native groups are sourced from the Tamil
Virtual Academy's Advanced Ebook, printed page 26, and its online lesson:
https://www.tamilvu.org/courses/degree/c021/c0211/html/c0211331.htm
The profile records facts; no textbook prose or images are copied here.

`tools/generate_core_golden.py` compiles these references into checked-in JSONL.
It must never read runtime lexicon tables or call the Rust engine, bindings, or
oracle to generate expected results. Unicode normalization in this offline
fixture compiler uses Python's independent standard-library implementation;
this is evidence preparation, not a second public Tamil implementation.

Regenerate deliberately with `uv run --locked python tools/generate_core_golden.py`.
Check without writing with the same command plus `--check`. Updating a reference,
profile, or generated fixture requires reviewing the v0.1 acceptance specification.
