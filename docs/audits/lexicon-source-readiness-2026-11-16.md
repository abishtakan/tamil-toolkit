# Historical lexicon: source-by-source readiness

Date: 2026-11-16. Scope: the frozen 12-file historical bundle, the recovered
UTLKD package, and exact spelling overlap with the three current runtime packs.
This is a readiness audit, not a promotion, source approval, or legal opinion.

## Decision

Keep all historical assertions quarantined. Use the existing bundle as a
candidate-discovery index; recover or freshly extract evidence one source at a
time. Start with the 410 absent spellings in the Wiktionary-labelled meaning
slice, while pursuing source/permission recovery for the much larger technical
slice in parallel. Do not automatically import definitions, examples, regional
labels, IPA, morphology, or etymology from either slice.

The original 307,243 figure counts CSV records, including repeated exports,
meanings and relationships. Across the explicitly identified headword/phrase
columns there are **177,606 distinct nonempty scalar strings**: **8,968** already
occur in current written forms and **168,638** do not. This is not a count of
linguistically distinct words or approved additions. Phrase cells, variant lists,
noncanonical spellings, duplicate senses and names can all affect this count.

Current runtime coverage remains **9,403 distinct written forms, 11,370 entries,
25,733 senses**. An overlapping spelling does not establish the same POS,
homograph, meaning, source, or region. No historical assertion was approved here.

## Reproducible inventory

[Machine-readable measurements](lexicon-source-readiness-2026-11-16.json) include
all 12 original byte counts/SHA-256 values, pack-manifest fingerprints, per-file
counts, source-code subdivisions, historical note groups and overlap counts.
The collector [audit_lexicon_readiness.py](../../tools/audit_lexicon_readiness.py)
opens the recovered database read-only and verifies all 12 recovered exports
against the frozen originals. It performs exact decoded string comparisons:
**no trimming, Unicode normalization, or inferred linguistic matching**. Empty
headwords and boundary whitespace are counted separately; both are zero in the
measured headword columns. This does not certify other Unicode or schema rules.

```powershell
uv run --locked python tools/audit_lexicon_readiness.py `
  --package C:/Users/abish/Downloads/utlkd_reusable_package `
  --output docs/audits/lexicon-source-readiness-2026-11-16.json
```

The optional external package is needed only for recovered SQLite note groups;
without it, file/source-code inventories and spelling overlap still work. The
JSON stores its database fingerprint, not a portable copy of that database.
Frozen-source verification fails on a changed byte count or digest. The report
can be regenerated as the canonical packs change; this dated report describes
only the recorded fingerprints.

| Historical file | CSV rows | Distinct spelling cells | Already represented | Absent candidates |
|---|---:|---:|---:|---:|
| `primary_lemmas.csv` | 44,229 | 43,831 | 8,708 | 35,123 |
| `primary_meanings.csv` | 63,633 | 43,831 | 8,708 | 35,123 |
| `primary_relationships.csv` | 19,849 | Not a headword table | Not a headword table | Not a headword table |
| `secondary_archaic_literary_terms.csv` | 495 | 495 | 5 | 490 |
| `secondary_dialect_colloquialisms.csv` | 1,323 | 1,323 | 515 | 808 |
| `secondary_phrases_mwes.csv` | 10,719 | 10,719 | 131 | 10,588 |
| `secondary_proper_names_toponyms.csv` | 484 | 484 | 73 | 411 |
| `secondary_scientific_taxa.csv` | 193 | 192 | 100 | 92 |
| `secondary_specialized_technical_terms.csv` | 120,482 | 120,482 | 305 | 120,177 |
| `secondary_transliterations_loanwords.csv` | 1,607 | 1,607 | 74 | 1,533 |
| `unified_master_30col.csv` | 44,229 | 43,831 | 8,708 | 35,123 |

Do not sum the spelling columns: the same spelling occurs across files. The
44,229 master rows repeat primary entities; the 63,633 meaning rows refer to the
same 43,831 primary spellings. The binary FST is not another row collection. Its
recovered builder collapses duplicate spellings and loses 398 primary entries
across 389 multi-entry headwords; regenerate indexes from accepted canonical
records rather than importing it.

## Primary dictionary source slices

The CSV export omits source notes. The following groups come from the recovered
`word_meanings.notes` joined to `tamil_words.headword_ta`, not from verified
upstream attribution. A group label is a recovery lead, never evidence that its
content is reusable. Groups partition meaning rows but can share spellings.

| Historical note group | Meaning rows | Distinct spellings | Already represented | Absent candidates |
|---|---:|---:|---:|---:|
| DSAL_Madras_label | 15,347 | 14,157 | 481 | 13,676 |
| Oxford_label | 6,676 | 6,676 | 445 | 6,231 |
| Wiktionary_label | 26,138 | 8,544 | 8,134 | 410 |
| no_note | 12,772 | 12,772 | 34 | 12,738 |
| other_unresolved | 2,700 | 2,548 | 60 | 2,488 |

The 8,544 Wiktionary-labelled spellings here differ from the earlier audit's
8,575 Wiktionary-linked word IDs: one measures distinct spellings attached to two
meaning-note labels; the other measures a broader source-link union and includes
separate identities. Neither count should replace the other.

| Source/lead | Readiness | Specific blocker | Required recovery / next action |
|---|---|---|---|
| Wiktionary: 26,138 labelled meanings | Fresh extraction candidate; old rows blocked | Original dump/version and transformation trace missing; historical POS collapsing, mixed-source senses and cross-page folding documented | Match the 410 absent spellings to the pinned 10,799-page snapshot first. Record absent-page, unsupported-heading, unsafe-template and already-covered results separately. Fetch new pinned revisions only for unresolved pages. Emit new evidence-backed claims, preserve each etymology/POS occurrence, and reconcile overlapping senses without copying unverified historical text. |
| DSAL / Madras: 15,347 labelled meanings | Source/terms closure required | Digitized-source terms and applicability to this unknown extraction unresolved; recovered labels are not permission | Identify exact edition, record/page locators, acquisition method and applicable digitization terms. Obtain suitable permission or freshly transcribe from an independently verified reusable edition. Do not assume the age of the printed work licenses the digital extraction. |
| Oxford / Apple: 6,676 meanings; additional examples and phrases | Hold from distributed packs | Extractor recovered, but project redistribution permission has not been established | Separate all Oxford-derived senses, 11,055 historically traced examples and 2,187 phrase rows. Seek a suitable grant or replace claims with independently sourced material. Local OS availability is not reuse evidence. |
| Sorkuvai-labelled primary senses: 1,754 | Source recovery required | Source label alone lacks record-level provenance and applicable reuse grant | Recover exact URLs, edition/snapshot, extractors and permission evidence together with the technical-term workstream. |
| Cre-A-labelled meanings: 12; Tamilcube-labelled meanings: 12 | Hold pending source-specific permission or replacement | No applicable redistribution basis recovered | Keep these claims separate; recover terms/permission or independently re-source each claim. |
| No note: 12,772 meanings | Editorial triage required | 12,021 definitions merely repeat the headword with a technical-term tag; remaining 751 have no note-based provenance | Treat placeholders as candidate identifiers, not definitions. Recover original technical glossary entries, then validate actual meaning, POS and domain. Do not fill missing definitions with generated prose. |
| Other unresolved labels: 2,700 meanings | Mixed; per-claim triage | Includes 606 Tolkappiyan-derived rows, generic verification labels, Karefo and internal master references | Recover the original upstream record and distinguish literal text from derived output. A self-reference to the merged database is not independent evidence. |
| Primary lemmas, relationships and master-derived fields | Not independently ready | 22,128 lemmas marked promoted from secondary candidates have no recovered promotion trace; 19,849 relationships lack sufficient source lineage | Recover identity/promotion mapping and evidence for each relation endpoint/code. Recompute supported Unicode measurements with Rust. Keep unsupported IPA, DEDR, etymology, sandhi and morphology claims excluded until separately specified and evidenced. |

## Secondary collections

These source-code and region labels are observed CSV values, not validated
regional attestations or upstream permissions.

All 120,482 technical rows have a nonempty `english_term`; both `definition_ta`
and `definition_en` are empty in every row. This is a bilingual term-equivalence
collection, not 120,482 full dictionary definitions. The phrase table has 10,311
nonempty English glosses and 408 empty ones. A nonempty field is not proof of a
correct translation; supported unavailable fields should stay unavailable.

| Collection | Measured subdivisions | Readiness and next action |
|---|---|---|
| Technical terms: 120,482 rows / 120,177 absent spellings | `TVA_KALAICHOL`: 117,121 rows, 116,908 absent; `sorkuvai_technical`: 3,361 rows, 3,269 absent | Largest discovery opportunity. Recover source endpoints, exact glossary editions, record keys, extraction scripts and written reuse basis. Separate TVA from Sorkuvai instead of assuming identical rights. Validate English/Tamil equivalence and finite domains; missing definitions may remain explicitly unavailable under the contract. Use `terminology` only after its own approved pack and profile acceptance. |
| Phrases / MWEs: 10,719 rows / 10,588 absent spellings | Tamilcube 2,981; Oxford 2,187; other processing/glossary labels 5,551 | Hold restricted-source slices. The remaining labels mostly describe transformations, not sources: 2,336 technical-compound, 1,715 exhaustive-compound and 942 glued-phrase deconstructions need original attestations and generator traces. Do not split/concatenate phrases into purported attested entries. |
| Archaic/literary: 495 rows / 490 absent spellings | All carry `literary_source=Thirukkural` | Small re-sourcing pilot. Pin an identifiable edition and verse/line locators; distinguish attested form, editor's definition and modern translation with their own reuse evidence. A classical title does not clear modern editorial text. |
| Dialect/colloquial: 1,323 rows / 808 absent spellings | Kongu 469; Madras 342; Jaffna 310; General Spoken 106; Gen-Z/Cinema 39; Madurai 34; Nellai 23 | Require per-sense attestation and source-specific terms, with Tamil Nadu and Sri Lankan review where relevant. Prior package documentation describes AI-assisted curation; database model tags are absent and authorship cannot be inferred. Do not promote the IPA/example prose or infer region from a table label. |
| Names/toponyms: 484 rows / 411 absent spellings | Mixed proper-name categories | Re-source with authoritative stable identifiers and exact locators. Separate a name's occurrence from biographical/gloss prose and unsupported etymology. |
| Scientific taxa: 193 rows / 192 distinct Tamil-name cells / 92 absent | Scientific name is the upstream unique key; Tamil names repeat | Verify Tamil common-name-to-taxon mapping against dated authoritative records and reuse terms. Preserve one-to-many names/taxa; a shared Tamil spelling is not a duplicate taxon. |
| Loanwords/transliterations: 1,607 rows / 1,533 absent spellings | `Foreign` is recorded for 1,074 rows; English 427; other language labels 106 | Treat source-language labels as unverified. Require lexical attestation, established spelling and separate etymological evidence; do not turn mechanical transliterations into attested loans. |

## Release gates for every recovered slice

1. Freeze upstream bytes and locators, extraction version, retrieval date and
   source-specific reuse/attribution evidence. A fresh source creates new claims;
   it does not retroactively verify the old record.
2. Reconcile exact IDs and homographs; review normalized-key collisions using
   Rust without rewriting source text. Classify overlap as same claim, new sense,
   new POS/etymology, conflicting claim, or unresolved; never deduplicate by spelling.
3. Retain independent provenance for each definition, example, relation and scope.
   Leave unsupported fields unknown or withheld. Distinguish genuine human review
   from source-backed automated acceptance; an agent cannot manufacture approval.
4. Run existing structural and release validation, deterministic promotion and
   genuine CLDF validation/roundtrip. Register source-backed vectors before new
   linguistic behavior. Sync distribution copies and verify the relevant runtime
   and isolated archive profiles before claiming usable coverage.
5. Report net new written forms, entries, senses, rejected/withheld claims and
   exact source counts. Do not claim the 168,638 absent strings are a release target
   or that successful structural validation establishes linguistic validity.

## Ordered work queue and deliverables

1. **Wiktionary gap reconciliation**: an ID-based queue for all 410 absent
   spellings, with pinned-page matches and explicit rejection reasons. First
   inspect current snapshot coverage; unsupported parser cases require sourced
   fixtures before changing extraction behavior. No assumed yield.
2. **TVA/Sorkuvai evidence packet**: two separate extraction/rights manifests for
   the 117,121 and 3,361 technical rows, including endpoint/record recovery and
   original permission evidence. If unresolved, keep blocked and investigate
   independently reusable terminology sources.
3. **Small literary/taxa/name pilots**: bounded candidate slices with exact
   record locators and claim-level acceptance, allowing useful increments while
   larger source questions remain unresolved.
4. **Historical mixed-claim mapping**: recover the 22,128 secondary-promotion
   mapping and separate Oxford/Tamilcube/Cre-A/unknown-origin material; do not
   republish it by relabelling the enclosing lemma as Wiktionary.

Nothing in this report changes canonical data, Cargo defaults, profile fixtures,
release allowlists or publication scope. The six reviewed entries and fresh
source-backed bulk packs remain separate from the blocked historical claims.

## Evidence and verification boundary

### Current upstream evidence check

Hydrogen independently checked official-source pages on 2026-11-16. Current
terms do not prove which terms governed an unknown historical extraction.
The evidence below supports recovery decisions, not a definitive legal finding.

| Source | Official evidence checked | Result / remaining uncertainty |
|---|---|---|
| Wiktionary | [Copyrights](https://en.wiktionary.org/wiki/Wiktionary:Copyrights), [Wikimedia terms, section 7](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Pages accessible. Original contributed text has CC BY-SA / GFDL reuse routes, subject to applicable attribution and license obligations; external material can have separate terms. Recover per-record revision/evidence. |
| DSAL Tamil Lexicon | [Edition/database page](https://dsal.uchicago.edu/dictionaries/tamil-lex/), [linked CC BY-NC-ND 2.0](https://creativecommons.org/licenses/by-nc-nd/2.0/) | Pages accessible; this digitized edition links restrictive NC/ND terms. The historical database's public-domain label does not resolve the applicable edition, acquisition route or terms. |
| TVA / Sorkuvai | [TVA policies](https://www.tamilvu.org/en/website-policies), [Sorkuvai](https://sorkuvai.tn.gov.in/) | TVA policy direct fetch returned 522; indexed text describes prior permission and acknowledgment. Sorkuvai timed out. Treat current direct policy evidence as incomplete; recover both separately and obtain the applicable grant. |
| Tamilcube | [Dictionary](https://dictionary.tamilcube.com/), [terms](https://shop.tamilcube.com/terms/) | Accessible pages describe personal-use limits and permission for republication. No grant applicable to this project was recovered. |
| Cre-A | [Recorded verb-table URL](https://www.crea.in/verb-table), [publisher](https://www.crea.in/), [DSAL Cre-A edition](https://dsal.uchicago.edu/dictionaries/crea/) | Verb-table URL returned 404; publisher site has no usable open-license evidence. DSAL's separate 1992 edition records permission restrictions. Do not assume it establishes the exact terms of the missing verb-table snapshot. |
| Oxford / Apple | [Apple license inventory](https://www.apple.com/legal/sla/), [rights/permissions](https://www.apple.com/legal/contact/rights-permissions.html), [OUP notice](https://languages.oup.com/legal-notice/) | Apple pages accessible; OUP direct fetch returned 403. Exact in-app dictionary notice remains unavailable to this check. Indexed OUP text is only a lead; no project redistribution grant was recovered. |
| Wikisource | [Tamil Wikisource](https://ta.wikisource.org/wiki/Main_Page), [Wikimedia terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) | Accessible footers link CC BY-SA 4.0; local guidance also retains older license text. Underlying print works and modern editorial additions need separate per-edition checks and revision attribution. |

Other leads, including Winslow, Kaniyam, Tirukkural editions, DEDR, Nannool and
IndoWordNet, have not received a new source-specific rights investigation here.
Their presence in old metadata is not approval. Literary/taxa/name pilots above
are proposed recovery work, not claims that these collections are ready now.

- [Primary provenance audit](primary-dictionary-provenance-2026-11-14.md),
  [recovered-package lineage](utlkd-package-lineage-2026-11-14.md) and
  [Wiktionary recovery audit](wiktionary-snapshot-recovery-2026-11-14.md) contain
  earlier record-level investigations. Historical permission assertions in those
  audits are leads requiring applicability checks, not blanket approval here.
- [Curation contract](../../specs/021-lexicon-curation/contracts/curation.md)
  defines source/reuse evidence and nonempty release closure.
- All 12 frozen files and their recovered-package copies were hash-verified for
  this inventory. No source, curation, canonical, runtime or binding file changed.
- The collector was replayed for byte-identical JSON output; row/group totals,
  set partitions and pack counts were checked independently. Existing runtime
  parity and archive results were not rerun for this reporting-only work.
