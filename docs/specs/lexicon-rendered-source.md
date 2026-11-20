# Lexicon Rendered Wiktionary Source Specification

Status: Draft specification for source-backed recovery of blocked Wiktionary gap
pages using official MediaWiki `action=parse` rendered HTML evidence.

## 1. Purpose and Scope

This specification defines a bounded, fail-closed pipeline to capture and parse
official English Wiktionary rendered HTML (`action=parse&oldid=<revid>`) for
pinned revisions in the 410-spelling historical Wiktionary reconciliation queue
(`docs/audits/wiktionary-gap-reconciliation-2026-11-16.json`) that were blocked by
the strict wikitext-only bulk parser (`tools/lexicon_wiktionary_bulk.py`).

Goals:
1. Recover clean, source-backed English definitions/glosses emitted by Wiktionary
   template/Lua modules (e.g., `{{place}}`, `{{number to word}}`, `{{given name}}`,
   `{{transclude sense}}`, `{{name translit}}`, `{{c}}`, `{{lbl}}`, `{{sid}}`,
   `{{+obj}}`, `{{angbr}}`, `<ref>` citations, and nested safe links inside labels
   and qualifiers) without inventing template expansions in Python.
2. Preserve strict language (`==Tamil==`), etymology, POS, and direct-sense vs.
   nested-example/quote/subsense boundaries.
3. Retain the existing policy rejecting Tamil Unicode scalars (`U+0B80..U+0BFF`)
   inside English glosses (`TAMIL_IN_ENGLISH_GLOSS_REJECTED`): never strip or
   discard Tamil script to recover variant/inflection/link templates (`altform`,
   `infl of`, `standard form of`, `alternative form of`, `synonym of`, `m|ta`,
   `l|ta`, etc.).
4. Emit bulk-compatible candidate JSON with complete capture provenance and
   blocked reasons, with **zero** acceptance decisions and **zero** canonical
   promotion.

Non-goals:
- No modifications to `data/sources/enwiktionary-tamil/`,
  `data/sources/enwiktionary-tamil-gap-2026-11-16/`, `data/sources/tamil-lexicon/`,
  `data/curation/`, `lexicon/`, or existing bulk/gap tools.
- No canonical merge or runtime pack changes.
- No new Tamil linguistic algorithms or morphological/inflection engines.
- No recovery of the 26 `missing_from_snapshot` spellings without separate
  title/history evidence.

## 2. Bounded Acquisition Contract (`action=parse`)

Source directory: `data/sources/enwiktionary-tamil-rendered-2026-11-16/`.

1. **Queue and hard cap**:
   - Input candidates are exact pinned `(title, pageid, revid, wikitext_sha256)`
     records from the 410-spelling gap queue (at most `MAX_RENDERED_PAGES = 384`,
     covering the 377 `source_present_parser_blocked` pages and optionally the 7
     already-recoverable pinned pages).
   - Requests exceeding 384 pages fail closed before any network call.
   - No category crawling, no redirect following, no title normalization, and no
     unbounded scraping.
   - Historical bundle permission records: the user confirmed **none** (`0`
     historical acceptance decisions; no rights waived). Historical `word_id`
     and `meaning_id` links serve strictly as discovery queue references, never
     as source text or licensing approval.

2. **Official API parameters**:
   - Endpoint: `https://en.wiktionary.org/w/api.php`
   - Query parameters per pinned revision:
     - `action=parse`
     - `oldid=<revid>`
     - `prop=text|templates|modules|revid|displaytitle|sections|parsewarnings|properties`
     - `disableeditsection=1`
     - `disablelimitreport=1`
     - `format=json`
     - `formatversion=2`
   - Bounded HTTP timeouts (`<= 20s` per request), bounded retries (`<= 3` with
     exponential backoff on transient `429`/`5xx`/socket errors), and bounded
     worker concurrency (`<= 4`).

3. **Identity, integrity, and resumable caching**:
   - Raw API responses are saved in deterministic batch files (`batch-NNN.json`)
     with per-item `capture_timestamp_utc`, `raw_api_response_sha256`, and
     exact `api_params`.
   - `capture-checkpoint.json` records the fingerprinted requested revision queue
     and SHA-256 digests of every completed batch so interrupted runs resume
     without losing or trusting unverified partial batches.
   - Finalized artifacts: `pages.jsonl.gz` (deterministic `mtime=0` gzip),
     `manifest.json` (recording batch hashes, compressed/uncompressed digests,
     capture dates, endpoint, license evidence, and per-title outcomes), and
     `README.md`.
   - Every response is verified against expected `revid`, `pageid`, and `title`,
     and cross-linked to the pinned `wikitext_sha256` from the input snapshot.
     Any mismatch fails closed.
   - Network errors, HTTP failures, and API errors (`error` payload such as
     `maxlag`) raise and abort rather than recording any page as missing.

## 3. Provenance, Attribution Truthfulness, and Verification Boundary

MediaWiki `action=parse&oldid=<revid>` renders pinned revision wikitext using
**current** upstream templates and Lua modules at capture time. Rendered HTML is
**not** original wikitext verbatim and must never be attributed as
`verbatim_source` or `wiktionary-bulk-parser`.

Every captured source record and every extracted candidate entry MUST record a
per-entry `rendered_evidence` object containing:
- `source_kind`: `"rendered_html"`
- `source_origin`: `"rendered_template_expansion"`
- `extraction_method`: `"wiktionary-rendered-parser"`
- `extraction_version`: `"wiktionary-rendered-v1+utf8-v1"`
- `rendering_attribution`: `"rendered_by_mediawiki_current_templates_at_capture_time"`
- `capture_timestamp_utc`: exact ISO-8601 UTC timestamp of the `action=parse` call
- `html_sha256`: SHA-256 of the captured `parse.text` HTML string
- `raw_api_response_sha256`: SHA-256 of the captured raw `action=parse` JSON payload
- `raw_capture_manifest_sha256`: SHA-256 of the capture `manifest.json`
- `raw_capture_file_locator`: object identifying `manifest_path`,
  `pages_jsonl_gz_sha256`, `batch_file`, `batch_sha256`, and `record_index`
- `template_module_dependencies`: object containing `dependencies_sha256`,
  `template_dependencies` (`ns == 10`), `module_dependencies` (`ns == 828`),
  `other_dependencies`, `rl_modules`, `rl_modulestyles`, and explicit
  `limits_and_caveats` noting that MediaWiki evaluates live templates/modules
  at capture time without individual template/module `oldid` pinning.

Upstream revision identity (`pageid`, `revid`, `revision_timestamp`, `user`,
`sha1`, `wikitext_sha256`, `permalink_url`, `history_url`) and `CC-BY-SA-4.0`
attribution are also preserved on every entry.

### Extraction-Ready / Proposed vs. Actual Source Verification

- **Extraction-ready / proposed (unaccepted)**: Candidates emitted by this tool
  are automated rendered-HTML extractions with `acceptance_decisions: 0` and
  `canonical_promoted: false`. Because `origin=verbatim_source` is forbidden for
  `rendered_html` and current automated eligibility requires `verbatim_source`,
  rendered candidates MUST remain unaccepted pending genuine human review and
  source-policy review before any canonical promotion. Never weaken
  auto/human acceptance rules or fabricate a reviewer.
- **Actual source verification**: Canonical eligibility requires root staging
  under distinct rendered provenance (`tools/lexicon_merge.py`), validation
  against canonical schemas/vocabularies, and genuine human/policy review.
  Nothing in this specification approves historical bundle records (zero
  permission records confirmed; no rights waived) or promotes canonical packs.

The existing wikitext acceptance builder rejects rendered proposals before
writing any workspace. A caller must not route captured HTML through that path
to acquire `accepted_auto_source` decisions or original-wikitext attribution.

## 4. DOM Parsing and Fail-Closed Rules

Parsing operates on a deterministic DOM tree constructed via Python stdlib
`html.parser.HTMLParser(convert_charrefs=True)` over `parse.text`:

1. **Unicode and headword checks**:
   - Headword passes `check_unicode_scalar_integrity` (rejecting BOM, C0/C1/extra
     format controls, lone surrogates, unexpected ZWJ/ZWNJ) and must contain a
     Tamil scalar (`U+0B80..U+0BFF`).
   - Optional `--check-native` enforces Rust `native_inspect(headword)["is_nfc"]`.

2. **Section and etymology isolation**:
   - Only content under `<h2>` with text `"Tamil"` is parsed, ending at the next
     `<h2>` or top-level `<hr>` separating L2 language sections. Non-Tamil L2
     sections emit `NON_TAMIL_SECTION_EXCLUDED`.
   - Subheadings (`<h3>`..`<h6>`) strip numbered suffixes (`Etymology 1` ->
     `Etymology`) to track `etymology_index` and `etymology_heading`.
   - Headings matching `POS_HEADING_MAP` (`Noun`, `Proper noun`, `Verb`,
     `Adjective`, `Adverb`, `Interjection`, `Pronoun`, `Postposition`,
     `Preposition`, `Particle`, `Numeral`, `Conjunction`, `Determiner`) open a
     candidate entry scoped to `(pageid, revid, pos_code, etymology_index, pos_occurrence_index)`.
   - Unmapped headings (`Participle`, `Phrase`, `Number`, `Note`, etc.) and
     `NON_DEFINITION_SECTIONS` close the active POS scope and emit
     `UNMAPPED_SUBSECTION_EXCLUDED:<base_heading>` or the mapped non-definition
     exclusion code.

3. **Entry-level headword qualifiers**:
   - Within an active POS section, `<p>` blocks containing `<span class="headword-line">`
     are inspected for `<span class="usage-label-term">` labels (`{{tlb}}`).
   - Label text inside `<span class="ib-content label-content">` is split into
     tokens and classified through the finite reviewed vocabularies (`region`,
     `register`, `grammar_system`, `period`, `social_usage`, `domain`) while
     honoring negating prefixes (`outside`, `except`, `except in`, `not`).
   - Leading ignore-words (`chiefly`, `especially`, `usually`, `often`, `rarely`,
     `sometimes`, `now`, `also`, `or`) attached without commas in rendered HTML
     (e.g., `"chiefly Spoken Tamil"`) may be stripped only when the suffix maps
     to an exact reviewed label and no negating prefix is active.
   - Unmapped tokens stay in `unmapped_entry_qualifiers` with `unknown`
     unavailable dimension semantics preserved.

4. **Direct sense vs. nested structures**:
   - Only top-level `<ol>` blocks (excluding `references`) inside an active POS
     section yield senses.
   - Empty `<li class="mw-empty-elt">` elements (emitted by `{{sid}}`) are
     skipped without incrementing sense ordinals.
   - Inside each `<li>`:
     - Any `<span class="scribunto-error">` or `<strong class="error">` fails
       closed with `WIKTIONARY_SCRIPT_ERROR_REJECTED`.
     - Nested `<ol>` elements are excluded as `SUBSENSE_LIST_EXCLUDED`.
     - Nested `<dl>` and `<ul>` elements (examples `h-usage-example`, quotes
       `citation-whole`, `nyms` synonyms/antonyms) are excluded from direct
       sense text and counted in `nested_lists_excluded`.
     - `<style>` elements (`TemplateStyles`) are excluded so CSS never leaks into
       glosses.
     - `<sup class="reference">` footnote markers (`<ref>`) are excluded and
       counted in `reference_markers_excluded`.
     - Any other `<sup>` (e.g., `10<sup>3</sup>`), `<sub>`, `<script>`, `<table>`,
       `<figure>`, `<math>`, `<img>`, `<audio>`, `<video>`, or unexpected `<div>`
       in the direct sense body fails closed with
       `UNSUPPORTED_RENDERED_HTML_ELEMENT:<tag>`.
     - Sense-level `<span class="usage-label-sense">` (`{{lb}}`/`{{lbl}}`) and
       `<span class="ib-content qualifier-content">` (`{{q}}`) tokens are
       extracted and classified into `qualifiers` and `unmapped_qualifiers`
       while keeping the visible parenthesized text in `meaning_en`.

5. **Gloss validation**:
   - Normalize runs of whitespace to single ASCII spaces and trim ends.
   - Reject empty glosses (`EMPTY_GLOSS_REJECTED`).
   - Reject residual `{{`, `}}`, `[[`, `]]`, `<!--` (`RESIDUAL_MARKUP_REJECTED`).
   - Reject forbidden markers (`FORBIDDEN_SENSE_MARKERS`, e.g., `(கலைச்சொல்)`,
     `*PDr`, `DEDR`, `verb_conjugations`).
   - **Reject Tamil script inside English gloss** (`TAMIL_IN_ENGLISH_GLOSS_REJECTED`):
     any `U+0B80..U+0BFF` scalar anywhere in the extracted direct sense text
     causes the sense to fail closed.
   - Enforce `check_unicode_scalar_integrity` on the final gloss (`SENSE_*`).
   - Entries left with zero valid senses emit `ENTRY_NO_VALID_SENSES_REMAINING`
     and are omitted from `candidate_entries`.

6. **Pack routing and output**:
   - Deterministic `entry_id` allocated under a dedicated rendered namespace
     (`RENDERED_NAMESPACE`) scoped to `(pageid, revid, pos_code, etymology_index, pos_occurrence_index)`.
   - Pack routing reuses `assign_pack` (`PROPN` -> `names_taxa`, attested
     TN/SL regional scope -> `regional`, otherwise `core`).
   - Output JSON contains `records` (all queue items with `status`, `blocker_counts`,
     extracted counts, and provenance), `candidate_entries` (bulk-compatible
     schema + rendered provenance), `status_counts`, `blocker_counts`, and
     source/parser digests. No acceptance decisions or promotion tables are
     generated.
