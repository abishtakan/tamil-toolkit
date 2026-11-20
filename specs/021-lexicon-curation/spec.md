# Feature Specification: Professional Tamil Lexicon Curation

**Feature Branch**: `master` (existing branch; no branch hook configured)

**Created**: 2026-11-13

**Status**: Reviewed six-entry / 19-sense core passes L1–L3 and bounded L4 functional, performance, full integration and isolated archive checks. Owner activation approval was recorded on 2026-11-15 for the 44 core-profile vectors. Historical bulk-source rights remain unverified.

**Input**: Prioritize the supplied Tamil lexicon before numerals; organize it to professional lexicographic standards, preserve its sources, and make reviewed data reusable by tamil-toolkit. Use the existing audit and update the project roadmaps.

## Storage decision — 2026-11-14

Large lexicon CSV datasets retain ordinary UTF-8 Tamil. Use the versioned
`json-string-utf8-v1` cell codec with reversible JSON/control escaping, rather
than expanding every non-ASCII character. Golden tests and exact scalar
inspection remain escaped; future runtime artifacts use a measured compact
format. This follows the user's storage/readability direction and the narrow
Constitution 2.0.0 amendment. See
[decision and migration acceptance](../../docs/decisions/lexicon-text-storage.md).
Uncommitted legacy staging and temporary copies were deleted with no legacy
archive retained; the clean `json-string-utf8-v1` rebuild, exact source-content
equality ([source-content-proof-final.json](../../target/lexicon/source-content-proof-final.json)),
pre-projection replay ([us1-proof.json](../../target/lexicon/us1-proof.json)),
739-record structural pilot ([l2-acceptance.json](../../target/lexicon/l2-acceptance.json),
[structural-final.json](../../target/lexicon/structural-final.json)), fail-closed
release guard ([release-rejection-final.json](../../target/lexicon/release-rejection-final.json)),
and full `just agent-pre-stop-gate` ([pre-stop-utf8-final-retry.log](../../target/lexicon/pre-stop-utf8-final-retry.log))
are complete (`0` accepted decisions, `0` eligible assertions).
L2 unblocks Phase 6 numerals scheduling. The separate revision-pinned six-entry
core now satisfies L3 source/reuse/human review and bounded L4 runtime acceptance;
the historical merged-source intake remains quarantined.

## Clarifications

### Session 2026-11-13

- Q: What review should lexical content require before it becomes eligible for a public data pack? → A: B — Unchanged, source-verified content may pass automated checks; corrections, inferred annotations, and ambiguous cases require human review. Automated acceptance and human linguistic review remain distinct states; source attribution and reuse requirements apply to both.
- Q: Should exact lookup match canonically equivalent Unicode encodings of the same Tamil spelling? → A: A — Compare lookup input and accepted canonical spellings after NFC normalization, retaining original source text. Canonical equivalence does not authorize orthographic repair, lossy folding, or removal of format controls.
- Q: When a user filters lookup to a region such as Jaffna, which entries should be returned? → A: A — Include entries attested for the requested region and entries explicitly reviewed as geographically unrestricted; exclude unknown geographic coverage. Unrestricted status requires affirmative evidence and review rather than an absent region label.
- Q: What must the lexicon pilot deliver before numerals work resumes? → A: C — Complete the pilot's structural review and record dispositions even if no content is release-eligible. Keep sampling minima and full accounting; unresolved source, rights, and linguistic evidence can remain quarantined. This scheduling gate grants no data-release or runtime approval.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trace and assess imported material (Priority: P1)

As a curator, I can trace imported records to their sources, extraction history, and reuse evidence, so I can distinguish material eligible for distribution from material requiring investigation.

**Why this priority**: A merged dataset cannot support trustworthy editorial decisions without evidence of origin and transformations.

**Independent Test**: Inventory all supplied files and record a source disposition for every imported record without changing the originals or requiring a public dictionary release.

**Acceptance Scenarios**:

1. **Given** the 12 supplied files and their intake checksums, **When** intake is catalogued, **Then** every file remains byte-identical and its records have stable source locators.
2. **Given** a label such as `TVA_KALAICHOL` without an exact source reference, **When** its records are assessed, **Then** the missing evidence remains explicit and those assertions are ineligible for public distribution until resolved.
3. **Given** publicly accessible source material extracted through scripts, **When** reuse eligibility is assessed, **Then** accessibility, attribution, and redistribution evidence are recorded separately, with unresolved status permitted.

---

### User Story 2 - Curate entries without losing linguistic distinctions (Priority: P1)

As an editor, I can organize entries, forms, senses, translations, examples, and relationships while retaining original text and recording each editorial decision.

**Why this priority**: Existing records sometimes contain multiple numbered meanings and mixed dictionary components; identical spellings can represent distinct entries.

**Independent Test**: Curate the representative pilot defined below, trace every output to source records, and review corrections independently of runtime lookup.

**Acceptance Scenarios**:

1. **Given** one spelling with distinct parts of speech, **When** entries are organized, **Then** each retains its identity and senses rather than being merged solely by spelling.
2. **Given** a record with mixed-language definitions, numbered meanings, and citations, **When** it is reviewed, **Then** each accepted component is separately identified and ambiguous material remains in a review queue with its original text.
3. **Given** an imported `verified` label and confidence `1.0` without review evidence, **When** it is curated, **Then** these are preserved as source assertions without implying completed linguistic review.
4. **Given** a spelling correction or part-of-speech correction, **When** it is accepted, **Then** stable entry identity, legacy references, and the reason and evidence for the change remain available.
5. **Given** unchanged content faithfully reproduced from a verified source, **When** its provenance, reuse eligibility, and validation checks pass, **Then** it may be accepted automatically with its method recorded; a correction, inferred annotation, or ambiguous interpretation instead requires a recorded human review decision before inclusion.

---

### User Story 3 - Retrieve all reviewed matches (Priority: P2)

As a toolkit consumer, I can retrieve every reviewed entry for a spelling, its approved senses, and available evidence, with explicit coverage and review status.

**Why this priority**: The supplied index maps each spelling to one entry ID and cannot alone expose every homographic entry.

**Independent Test**: Query an approved pilot containing homographs, variants, regional labels, and missing annotations; verify that all eligible matches are returned through each supported language interface.

**Acceptance Scenarios**:

1. **Given** an approved spelling with multiple entries, **When** exact lookup is performed, **Then** every matching eligible entry is returned in documented stable order without silent deduplication.
2. **Given** an unknown spelling, **When** exact lookup is performed, **Then** the result is empty without inventing an entry or applying unrequested spelling repair or lossy folding.
3. **Given** a requested region filter, **When** lookup is performed, **Then** only eligible entries attested for that region or explicitly reviewed as geographically unrestricted are returned; unknown geographic coverage is excluded and remains distinct from an attested regional absence.
4. **Given** a non-distributable or unreviewed assertion, **When** a public data pack is built, **Then** that assertion is excluded without silently removing its intake history.
5. **Given** canonically equivalent Unicode encodings of an accepted spelling, **When** exact lookup is performed, **Then** both return the same eligible entries in the same order after NFC normalization, while original source text remains unchanged.

---

### User Story 4 - Maintain a reproducible lexicon release (Priority: P2)

As a maintainer, I can validate changes, account for every imported record, and regenerate selected data packs and lookup indexes from a versioned reviewed dataset.

**Why this priority**: Repeatable validation and builds prevent silent loss, stale indexes, and accidental expansion of public guarantees.

**Independent Test**: Rebuild the same approved pack twice, compare its results, then introduce an invalid reference and verify that validation rejects it.

**Acceptance Scenarios**:

1. **Given** unchanged approved inputs and declared build settings, **When** the same pack is generated twice, **Then** the resulting artifacts are byte-identical and carry matching version and source manifests.
2. **Given** an imported row that is merged, split, corrected, excluded, or quarantined, **When** import accounting is inspected, **Then** its disposition and resulting identifiers can be traced in both directions.
3. **Given** a basic dictionary consumer, **When** its data packs are selected, **Then** technical terminology, proper names/taxa, and regional extensions can be omitted without breaking retained references.
4. **Given** pilot sampling and structural review are complete but no content is release-eligible, **When** all selected records have valid dispositions and unresolved material is quarantined, **Then** the L2 scheduling gate can be accepted and numerals work can resume; data-pack and runtime approval remain pending.

### Edge Cases

- Identical spelling with different parts of speech, multiple senses, or conflicting source definitions.
- Same spelling and part of speech with distinct historical homographs; identity is not reducible to a spelling/POS key.
- One source row splits into several senses; multiple source rows support one assertion.
- A headword is NFC yet has an invalid vowel-sign sequence; source transcription and corrections must remain distinct.
- Intentional ZWJ/ZWNJ, U+FEFF, decomposed text, whitespace, and mixed-script text; no silent deletion or conflation.
- Imported derived counts disagree with project conventions, including KSHA tailoring; conventions must be reconciled before values are replaced.
- A relationship names an entry with several senses, or the source meaning of its target is unresolved.
- Technical translation pairs lack definitions; literary quotations are presented as definitions or examples without locators.
- A regional label is unknown, overlaps another label, or describes social usage rather than geography.
- Correcting an entry invalidates a link, or removing an optional pack would leave a dangling reference.
- Source evidence cannot be recovered, or different sources have incompatible reuse terms.
- Generated annotation cannot be distinguished from manually reviewed annotation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preserve all original source files and their checksums; edits MUST occur in separately versioned curated records with reversible mappings to originals.
- **FR-002**: Catalogue each source with its identity, exact location or bibliographic locator, edition/snapshot where applicable, retrieval information where known, extraction method/version, and reuse evidence; unknown values MUST remain explicit.
- **FR-003**: Link every accepted lexical assertion to source records and its transformation/review history. A public assertion MUST have an established reuse basis and required attribution; unresolved assertions MUST remain excluded from public packs.
- **FR-004**: Distinguish lexical entries, written/pronounced forms, senses, definitions, glosses, translation equivalents, examples, citations, and typed relationships. Retain unparsed source text for unresolved structures.
- **FR-005**: Allocate stable entry, sense, and source identifiers independent of mutable spelling, part of speech, ordering, and source row position; retain legacy IDs, merge/split mappings, and tombstones for retired identities.
- **FR-006**: Define required/optional fields, missing-value semantics, cardinalities, reference constraints, and versioned controlled vocabularies for all curated records. Unknown MUST be distinguishable from not applicable.
- **FR-007**: Preserve imported review labels and confidence as source assertions; separately track annotation origin, evidence, review state, reviewer or automated method, and decision date. Unchanged content faithfully reproduced from a verified source MAY become release-eligible after automated provenance, reuse-eligibility, and validation checks pass. Corrections, inferred annotations, and ambiguous cases MUST receive a recorded human review decision before inclusion. Automated acceptance MUST remain distinguishable from human linguistic review and MUST NOT imply independent linguistic adjudication. A confidence score MUST state its method and MUST NOT substitute for review evidence.
- **FR-008**: Separate original spelling, accepted canonical spelling, variants, and any search representation. Validate Unicode scalars, normalization, and orthographic anomalies separately, retaining intentional controls and explicit correction reasons.
- **FR-009**: Record the convention, version, and origin of derived counts and annotations; discrepancies MUST become reviewable findings. Imported IPA, roots, verb classes, frequency tiers, and Punarchi descriptions MUST NOT be presented as validated linguistic facts without evidence.
- **FR-010**: Distinguish language, geographic variety, register, historical period, domain, and social usage. Document TN and SL scope, including Jaffna, Batticaloa, Vanni, and Up-Country coverage as attested, unreviewed, or absent from the dataset; never infer equivalent coverage.
- **FR-011**: Support typed entry- or sense-level relationship endpoints, documented directionality/inverses, and evidence. Validate references and flag ambiguous semantic targets rather than selecting by spelling alone.
- **FR-012**: Account for every imported record as mapped, merged, split, excluded with reason, or quarantined; no source record may silently disappear. Imported datasets and generated exports MUST NOT be double-counted as additional vocabulary.
- **FR-013**: Exact lookup MUST compare input and accepted canonical spellings after NFC normalization, return all eligible entries for that canonical spelling, preserve homographic entry identities, document stable ordering, and provide explicit not-found and unsupported-request outcomes. Canonically equivalent inputs MUST return the same entries in the same order. Original source text MUST remain unchanged; exact lookup MUST NOT perform orthographic repair, lossy folding, or removal of format controls.
- **FR-014**: Return approved senses, annotations, provenance, and coverage/review status with documented filtering behavior. A region filter MUST include eligible entries attested for the requested region and entries explicitly reviewed as geographically unrestricted, and MUST exclude entries with unknown geographic coverage. Unrestricted status MUST have affirmative evidence and a review decision; an absent region label MUST NOT imply unrestricted usage. Unknown annotations MUST remain unknown rather than being synthesized during lookup. Without a region filter, otherwise eligible entries MUST NOT be excluded solely because their geographic coverage is unknown, and their unknown status MUST remain visible.
- **FR-015**: Release selection MUST support a core dictionary and optional terminology, name/taxon, and regional content. Selection MUST enforce reference closure or explicitly documented omission semantics.
- **FR-016**: Validation MUST reject invalid identities, broken references, schema violations, and unauthorized release inclusion, and generate actionable review queues for unresolved content and Unicode findings.
- **FR-017**: Repeated builds from identical declared inputs MUST produce identical curated exports and indexes, with manifests identifying dataset/schema versions, sources, settings, tool versions, and artifact checksums.
- **FR-018**: Define an exchange mapping aligned with the CLDF Dictionary entry/sense/example/source model, preserving Tamil-specific annotations and unsupported distinctions in documented extensions. Do not claim conformance without validating an export. TEI Lex-0 exchange is a later optional extension.
- **FR-019**: Complete a structurally reviewed pilot of at least 100 distinct primary entries plus at least 20 distinct records from each of the seven secondary datasets. Include at least 10 multi-entry spellings with all associated entries, 10 verbs, 10 mixed/numbered-sense records, 10 technical MWEs, 10 regional records spanning TN and Jaffna, and all observed Unicode/count discrepancy classes. Categories may overlap. L2 acceptance requires every sampling minimum, completed structural review, valid dispositions for every selected source record, and zero unresolved blocking errors in disposition/accounting records or any curated records. Unresolved source, reuse, or linguistic-review conditions MUST be recorded with the affected material quarantined or excluded; they do not block L2 acceptance, even when no content is release-eligible. L2 acceptance permits numerals work to resume without granting data-release or runtime approval.
- **FR-020**: Approve source-backed acceptance cases before implementing consumer behavior. All supported language interfaces MUST return the same entries, order, status, and errors for unchanged acceptance cases, including homographs, controls, region filters, missing values, and exclusions.
- **FR-021**: Preserve the project's single linguistic engine, dependency boundaries, and separate data ownership. This feature MUST NOT introduce guessed morphology, pronunciation, sandhi, or dialect transformation, or imply those capabilities from dictionary lookup.
- **FR-022**: Track intake, structural pilot review, approved data packs, bulk accounting, runtime verification, suite activation, and publication as distinct milestones. L2 is a structural/accounting and scheduling gate only; consumers claiming lexical support MUST use a relevant subset meeting L3 source/review/release-eligibility requirements. Runtime acceptance MUST demonstrate a nonempty approved pack and homograph cases; an empty pack or quarantined pilot MUST NOT count as verified lookup support. Updating this specification MUST NOT itself activate a data pack or authorize publication.

### Key Entities *(include if feature involves data)*

- **Source / Snapshot**: Identifiable publication or dataset, captured version, locations, extraction history, and reuse/attribution evidence.
- **Imported Record / Disposition**: Original file locator and legacy ID, mapped curated identities, and reviewed inclusion, split, merge, exclusion, or quarantine decision.
- **Lexical Entry / Form**: Stable lexical identity with spelling/pronunciation representations and grammatical characterization; homographic entries remain distinguishable.
- **Sense / Text Component**: One meaning and its language-tagged definitions, glosses, equivalents, examples, citations, usage, and evidence.
- **Assertion / Review**: A claim about an entry, sense, form, or relationship with origin, evidence, editorial state, and decision history.
- **Relation**: Typed link between identified entries or senses with directionality and supporting evidence.
- **Variety / Usage Label**: Controlled geographic or social scope with stated coverage and source support.
- **Data Pack / Release Manifest**: Versioned eligible selection with reference closure, build provenance, and checksums.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 12 intake files retain their recorded checksums throughout curation; 100% of imported records have an explicit disposition and traceable curated mappings or exclusion reasons (FR-001, FR-005, FR-012).
- **SC-002**: Every assertion included in a public pack has recorded source evidence, reuse disposition, required attribution, and the applicable FR-007 acceptance decision. Every included correction, inferred annotation, or ambiguous case has a human reviewer and dated decision; unchanged source-verified content accepted automatically identifies its method and passed checks. Zero unresolved-rights assertions are included, and zero automated decisions are labeled as human linguistic review (FR-002, FR-003, FR-007).
- **SC-003**: The pilot meets every FR-019 sampling minimum and 100% of its selected records have structurally validated dispositions with zero unaccounted records or unresolved blocking errors in accounting or curated records. All unresolved source, reuse, and linguistic findings are explicitly quarantined or excluded. Zero release-eligible entries is an acceptable L2 result and does not prevent numerals work from resuming; it grants no data-pack or runtime approval (FR-004, FR-006, FR-008–FR-011, FR-019, FR-022).
- **SC-004**: Every approved homographic entry in the chosen pack is returned by exact spelling lookup, with no extra ineligible matches. Every canonically equivalent input pair returns identical ordered entries after NFC normalization without altering source text or removing controls. Region-filter acceptance cases include attested matches and reviewed unrestricted entries, exclude unknown coverage and other-region-only entries, and preserve otherwise eligible unknown-coverage entries in unfiltered lookup. All defined not-found, filter, and error cases pass unchanged across supported interfaces (FR-013, FR-014, FR-020).
- **SC-005**: Two builds from identical declared inputs produce identical artifacts and manifests; all selected packs have zero unresolved reference-closure violations (FR-015–FR-017).
- **SC-006**: Every Unicode, count-convention, annotation-origin, and mixed-sense issue class identified by the intake audit has a documented resolution policy and pilot examples; no corrections silently change source text (FR-008–FR-010, FR-016).
- **SC-007**: At L3/L4, maintainers can export a nonempty approved lexical subset with all entries, senses, evidence references, and documented Tamil extensions preserved; a round-trip comparison finds no unaccounted identity or content loss. A structurally accepted L2 pilot with no eligible content does not satisfy this later exchange milestone (FR-018, FR-022).
- **SC-008**: The handoff and both project roadmaps identify the lexicon track, its current evidence, next gate, and dependent consumers without marking unbuilt linguistic functionality or unpublished data as complete (FR-021, FR-022).

## Assumptions

- This feature is the next priority before new Phase 6 numerals work. Phase 6 resumes after the structurally reviewed and fully accounted pilot (roadmap L2) is accepted and recorded in the handoff, even if no content is release-eligible; source recovery, linguistic review, approved data packs, and consumer work may continue alongside independent phases. Relevant L3-approved subsets remain required for consumers claiming lexical support. Existing Phase 0–17 identifiers remain stable; a named lexicon data track supplies explicit consumer gates.
- The baseline is the [2026-11-13 audit](../../docs/audits/lexicon-2026-11-13.md): 44,229 primary entries, 63,633 supplied sense records, 19,849 relationships, and 120,482 technical records. These are intake counts, not verified linguistic coverage or final release targets.
- The owner reports combining public online material using Python extraction. Exact sources, extraction scripts, annotation origins, and source-specific reuse evidence still require recovery. Missing external evidence blocks affected acceptance milestones, not writing this specification or curating independently supported material.
- Primary users are curators, linguistic reviewers, maintainers, and toolkit consumers. A new dictionary website, editorial application, and general-purpose search service are outside this feature.
- Initial consumer behavior is reviewed exact lookup and retrieval. Folded/prefix/fuzzy search, automatic inflection, spellchecking, phonetic synthesis, dialect transformation, and automatic dictionary writing are deferred to separate contracts.
- Source evidence is preferred over invented completeness: unavailable definitions, examples, pronunciations, and regional coverage remain explicitly unknown.
- The project constitution and existing release policy remain authoritative. Storage layouts, Rust ownership placement, build tooling, interface names, and pack sizes are planning decisions; no new public crate or release approval is implied.
