# Tasks: Canonical Prosodic & Syllabic Tamil Hyphenation Rules (`015-canonical-tamil-hyphenation`)

**Input**: Design documents from `/specs/015-canonical-tamil-hyphenation/`
**Prerequisites**: [plan.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/plan.md) (required), [spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/spec.md) (required), [research.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/research.md), [data-model.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/data-model.md), [contracts/hyphenation-api.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/contracts/hyphenation-api.md), [quickstart.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/quickstart.md)

**Organization**: Tasks are grouped by user story (`US1`, `US2`, `US3`) to enable independent implementation and verification of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- All tasks include exact repository-relative file paths.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline configuration and synchronize module documentation headers before updating core algorithms and golden vectors.

- [X] T001 Inspect baseline hyphenation golden test corpus and schema in `tests/golden/hyphen.jsonl`
- [X] T002 [P] Update canonical hyphenation specification defaults (`left_min = 3, right_min = 3`, `MIN_WORD_LETTERS = 6`) and 5-step *Asai* rules in `docs/specs/hyphen.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration defaults (`left_min = 3, right_min = 3`) and `RawSyllable` / `AsaiSegment` structures that MUST be in place before user story verification.

**⚠️ CRITICAL**: No user story work can be finalized until this phase is complete.

- [X] T003 Update `HyphenationConfig::default()` (`left_min: 3, right_min: 3`, `delimiter: "\u{00AD}"`, both `>= 1`) and `DicHeader::default()` (`left_hyphen_min: 3, right_hyphen_min: 3`) in `crates/tamil-hyphen/src/types.rs`
- [X] T004 [P] Define `RawSyllable` (`letters`, `start_letter_idx`, `end_letter_idx`, `has_coda`) and `AsaiSegment` (`letters`, `start_letter_idx`, `end_letter_idx`, `letter_count`) helper structures in `crates/tamil-hyphen/src/syllable.rs`
- [X] T005 [P] Update golden test vectors in `tests/golden/hyphen.jsonl` so all entries reflect `left_min = 3, right_min = 3` and the 5-step Tamil *Asai* + 3-letter minimum segment rules across `ta-IN` and `ta-LK` words

**Checkpoint**: Foundation ready — user story implementation and verification can now proceed.

---

## Phase 3: User Story 1 - Eliminating Short-Word Breaks & 2-Letter Next-Line Orphans (`left_min = 3, right_min = 3`) (Priority: P1) 🎯 MVP

**Goal**: Keep 100% of short words ($< 6$ tailored Tamil letters, e.g., `உலகம்`, `சமூகம்`, `வணிகம்`, `திட்டம்`, `வரலாறு`, `அறிவியல்`, `பாதுகாக்க`) unbroken, and prevent any 2-letter orphan suffix (`-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`) from wrapping onto the next line.

**Independent Test**: Verify across all 53 benchmark words and `tests/golden/hyphen.jsonl` that zero words $< 6$ tailored Tamil letters break under default settings (`left_min = 3, right_min = 3`) and 100% of broken words have $\ge 3$ tailored letters on both the first and final segments.

### Implementation for User Story 1

- [X] T006 [US1] Enforce minimum word threshold (`total_letters < cfg.left_min + cfg.right_min`, default `6`) and next-line tail merge (`< cfg.right_min`) / current-line head merge (`< cfg.left_min`) in `crates/tamil-hyphen/src/syllable.rs`
- [X] T007 [P] [US1] Enforce `DEFAULT_LEFT_MIN = 3`, `DEFAULT_RIGHT_MIN = 3`, `DEFAULT_MIN_WORD_LETTERS = 6`, next-line tail merge (`< rightMin`), and current-line head merge (`< leftMin`) in `integrations/office-word-addin/engine.js`
- [X] T008 [P] [US1] Update default `leftMin = 3` and `rightMin = 3` in `integrations/office-word-addin/commands.js`, `integrations/office-word-addin/taskpane.js`, and `integrations/office-word-addin/index.html`
- [X] T009 [P] [US1] Enforce `leftMin = 3, rightMin = 3` defaults, `minWordLetters = 6`, and next-line tail / current-line head merges in `playground/src/lib/engine.ts` and `playground/src/components/public-tools/HyphenatorTool.tsx`

**Checkpoint**: User Story 1 is complete and independently testable across Rust, Word Add-in, and Playground.

---

## Phase 4: User Story 2 - 5-Step Tamil *Asai* (`நேரசை` / `நிரையசை`) + 3-Letter Segment Grouping (Priority: P2)

**Goal**: Partition bigger words ($\ge 6$ tailored Tamil letters) at natural Tamil *Asai* boundaries using the 5-step algorithm (1. Raw phonetic syllable extraction with contiguous *Mei* `\u0BCD` / *Aytham* `\u0B83` codas, 2. Word-initial `CVC + u/i` participle stem binding, 3. Forward *Nirai-asai* grouping for 1-letter open syllables, 4. Tail/head merges, 5. Internal segment merge `< min(left_min, right_min)`).

**Independent Test**: Verify that `பல்கலைக்கழகம்` $\rightarrow$ `பல்கலைக்-கழகம்`, `பல்கலைக்கழகங்களில்` $\rightarrow$ `பல்கலைக்-கழகங்-களில்`, `தொழில்நுட்பம்` $\rightarrow$ `தொழில்-நுட்பம்`, `படைப்பாற்றல்` $\rightarrow$ `படைப்-பாற்றல்`, `கண்டுபிடிப்பு` $\rightarrow$ `கண்டு-பிடிப்பு`, `இன்றியமையாத` $\rightarrow$ `இன்றி-யமையாத`, `திருச்சிராப்பள்ளி` $\rightarrow$ `திருச்-சிராப்-பள்ளி`, `ஒருங்கிணைக்கப்பட்ட` $\rightarrow$ `ஒருங்-கிணைக்-கப்பட்ட`, and `வாழ்த்துகள்` $\rightarrow$ `வாழ்த்-துகள்`.

### Implementation for User Story 2

- [X] T010 [US2] Implement Step 1 (contiguous *Mei* `\u{0BCD}` / *Aytham* `\u{0B83}` coda binding), Step 2 (word-initial `CVC + u/i` stem binding for `\u{0BC1}` / `\u{0BBF}`), Step 3 (forward *Nirai-asai* grouping of 1-letter open syllables), and Step 5 (internal `< min(left_min, right_min)` segment merge preferring open neighbors) in `crates/tamil-hyphen/src/syllable.rs`
- [X] T011 [P] [US2] Implement `getRawSyllables` and `getTamilSyllables` with Steps 1–5 (`CVC + u/i` stem binding, forward *Nirai-asai* grouping, tail/head/internal $\ge 3$-letter merges, and contiguous pulli coda binding) in `integrations/office-word-addin/engine.js`
- [X] T012 [P] [US2] Implement `getRawSyllables` and `getTamilSyllables` with Steps 1–5 in `playground/src/lib/engine.ts`
- [X] T013 [US2] Update unit tests in `crates/tamil-hyphen/src/dic.rs`, `crates/tamil-hyphen/src/docx.rs`, `crates/tamil-hyphen/src/text.rs`, and `crates/tamil-hyphen/tests/` to align with the 5-step Tamil *Asai* + `left_min = 3, right_min = 3` rules

**Checkpoint**: User Stories 1 and 2 work identically across Rust, Word Add-in, and Playground.

---

## Phase 5: User Story 3 - Automatic Healing & Cache Invalidation in the Word Add-in (Priority: P3)

**Goal**: Automatically strip pre-existing soft hyphens (`U+00AD`, `U+001F`, `U+200B`) and `<w:softHyphen/>` tags before re-hyphenating, and bust the Office WebView cache so existing Word documents heal in a single click.

**Independent Test**: Pass OOXML containing `<w:t>உல</w:t><w:softHyphen/><w:t>கம்</w:t>` into `hyphenateOoxml()` and verify it heals to `<w:t>உலகம்</w:t>` with `0` `<w:softHyphen/>` tags.

### Implementation for User Story 3

- [X] T014 [P] [US3] Strip pre-existing `\u{00AD}`, `\u{001F}`, and `\u{200B}` characters before computing break points in `crates/tamil-hyphen/src/syllable.rs` and `crates/tamil-hyphen/src/docx.rs`
- [X] T015 [P] [US3] Strip pre-existing `\u00AD`, `\u001F`, `\u200B`, and `<w:softHyphen/>` tags before re-evaluating words in `integrations/office-word-addin/engine.js` and `playground/src/lib/engine.ts`
- [X] T016 [P] [US3] Bump cache-busting query string (`?v=5`) and manifest version (`1.5.0.0`) in `integrations/office-word-addin/commands.html` and `integrations/office-word-addin/manifest.xml`

**Checkpoint**: All three user stories are complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Synchronize FFI bindings (`bindings/python`, `bindings/js-wasm`) and run all workspace quality gates.

- [X] T017 [P] Update default `left_min = 3, right_min = 3` parameters and docstrings in `bindings/python/src/lib.rs`, `bindings/python/python/tamil_toolkit/__init__.pyi`, and `bindings/js-wasm/src/lib.rs`
- [X] T018 Run `cargo test -p tamil-hyphen` and verify all unit and golden vector tests pass in `crates/tamil-hyphen/`
- [X] T019 Run quickstart validation commands from `specs/015-canonical-tamil-hyphenation/quickstart.md` across Rust and Node.js

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS** all user stories (`T003`–`T005`).
- **User Story 1 (Phase 3, P1 🎯 MVP)**: Depends on Phase 2 (`T006`–`T009`).
- **User Story 2 (Phase 4, P2)**: Depends on Phase 2 and integrates with US1 in `syllable.rs` / `engine.js` / `engine.ts` (`T010`–`T013`).
- **User Story 3 (Phase 5, P3)**: Depends on Phase 2 (`T014`–`T016`).
- **Polish (Phase 6)**: Depends on Phases 3–5 (`T017`–`T019`).

### Parallel Opportunities

- **Phase 2**: `T004` (`syllable.rs` structs) and `T005` (`tests/golden/hyphen.jsonl`) can run in parallel.
- **Phase 3 (US1)**: `T006` (Rust), `T007`/`T008` (Office Word Add-in), and `T009` (Playground) touch disjoint directories and can run in parallel.
- **Phase 4 (US2)**: `T010` (Rust), `T011` (Office Word Add-in), and `T012` (Playground) can run in parallel.
- **Phase 5 (US3)**: `T014` (Rust), `T015` (JS/TS engines), and `T016` (Word Add-in HTML/manifest) can run in parallel.

---

## Parallel Example: User Story 1 & User Story 2

```bash
# Run Rust core, Word Add-in, and Playground engine tasks in parallel:
Task T006/T010: "Implement 5-step Tamil Asai + left_min=3, right_min=3 in crates/tamil-hyphen/src/syllable.rs"
Task T007/T011: "Implement 5-step Tamil Asai + left_min=3, right_min=3 in integrations/office-word-addin/engine.js"
Task T009/T012: "Implement 5-step Tamil Asai + left_min=3, right_min=3 in playground/src/lib/engine.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 Core)

1. Complete Phase 1: Setup (`T001`–`T002`)
2. Complete Phase 2: Foundational (`T003`–`T005`)
3. Complete Phase 3 (US1) & Phase 4 (US2) (`T006`–`T013`)
4. **STOP and VALIDATE**: Verify zero short-word breaks and zero 2-letter next-line orphans across all 53 benchmark words and `tests/golden/hyphen.jsonl`.
5. Complete Phase 5 (US3) & Phase 6 (Polish) (`T014`–`T019`).
