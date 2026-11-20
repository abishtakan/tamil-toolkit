# Wiktionary historical-gap source capture

This is a fresh, separate capture from the official English Wiktionary API on
2026-11-16. It does not modify or validate the frozen historical Tamil bundle or
the 2026-11-15 bulk snapshot.

The readiness inventory identified 410 historical Wiktionary-labelled spellings
absent from the current usable packs. Of these, 333 exact titles already exist
in the pinned bulk snapshot. This supplement queries the other 77 exact titles
without following redirects: 51 revisions were pinned and 26 pages were missing
at capture time. Missing pages are not proof that the spelling is linguistically
invalid or that it never appeared upstream.

`batch-*.json` preserve complete API responses, requested titles and capture
timestamps. `manifest.json` records their hashes and per-title outcomes.
`pages.json` and deterministic `pages.jsonl.gz` project the 51 revision records
with page/revision IDs, timestamps, authors, exact wikitext hashes, permalinks
and history links. No template expansion or historical definition is imported
into these source records. The manifest fingerprints the projections.

## Attribution and reuse

Text is by the English Wiktionary contributors credited in each page's revision
history. Use each record's `permalink_url` for the pinned article and
`history_url` for contributor attribution. Extracted lexical data follows the
project's CC-BY-SA-4.0 data route, separate from MIT engine code. This capture
selects and serializes official revision text; later extraction changes must be
identified separately. External material can carry separate terms.

- [Wiktionary copyright policy](https://en.wiktionary.org/wiki/Wiktionary:Copyrights)
- [Wikimedia Terms of Use, section 7](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use)
- [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- [Preserved legal code](../enwiktionary-tamil/notices/cc_by_sa_4_0_legalcode.txt)

The preserved bulk-snapshot notice captures remain available in
`../enwiktionary-tamil/notices/`. No human acceptance is claimed, and this source
directory is not consumed by the runtime or public release archives.
