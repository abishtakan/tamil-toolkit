# Phase 0 Research — Tamil Word and Sentence Tokenization

## Reuse the Unicode baseline and original-text units

**Decision** — Reuse the workspace's `unicode-segmentation` 1.13.3 Unicode 17.0 baseline through `split_word_bound_indices()` and `split_sentence_bound_indices()`. Use `tamil_core::Letters::new` on the original input to determine allowed source endpoints. Record zero-based byte and unit ranges during segmentation.

**Rationale** — The full boundary iterators retain punctuation and whitespace for later classification. `get_letters` normalizes to NFC and can shorten the original byte representation. The core borrowed iterator preserves the original sequence and applies its literal atomic-letter tailoring. Interrupted compounds follow the original core units and preserve both joiners. [Cargo lockfile](../../Cargo.lock) · [Core letters](../../crates/tamil-core/src/lib.rs) · [UAX #29 revision 47](https://www.unicode.org/reports/tr29/tr29-47.html)

**Verification** — A temporary Rust probe using the workspace build matched all 1,944 Unicode 17 word-break rows and 512 sentence-break rows. A separate probe returned one unit for decomposed KSHA and two for the corresponding joiner-interrupted forms, preserving the joiner with the preceding pulli. The iterator also retained `0020 0300` and `000D 000A` as whole units. These results characterize the dependencies before Tamil tokenization is implemented. [Word break test](https://www.unicode.org/Public/17.0.0/ucd/auxiliary/WordBreakTest.txt) · [Sentence break test](https://www.unicode.org/Public/17.0.0/ucd/auxiliary/SentenceBreakTest.txt)

**Alternatives considered** — Filtered word or sentence iterators omit parts of the input. Normalizing the entire string would require a reversible offset map. Writing a second UAX #29 engine would duplicate the workspace dependency.

## Pin scalar properties and apply Tamil tailoring at explicit boundaries

**Decision** — Generate compact, merged ranges from pinned Unicode 17.0 data for the narrow properties the tailored profile consumes. Include `L*`, `M*`, `Nd`, `Cf`, `White_Space`, and the sentence classes needed to recognize terminators, continuations, and hard boundaries. Keep pinned test inputs and source hashes under the existing Unicode reference directory. Compile runtime ranges from their compact source and preserve Unicode license notices.

**Rationale** — Exact general categories and sentence properties are part of the contract. Rust's convenience predicates for alphabetic or numeric characters cover different sets. The abbreviation pass must explicitly insert word boundaries at both ends of a match, including when a baseline word spans a period. The sentence pass must associate a baseline break with its triggering full stop even when closing punctuation or spaces follow the period. Hard separators, end of text, and independent terminators retain precedence. [Derived general categories](https://www.unicode.org/Public/17.0.0/ucd/extracted/DerivedGeneralCategory.txt) · [White_Space property](https://www.unicode.org/Public/17.0.0/ucd/PropList.txt) · [Sentence break properties](https://www.unicode.org/Public/17.0.0/ucd/auxiliary/SentenceBreakProperty.txt) · [Reference layout](../../tests/reference/unicode-17.0.0/sources.json)

**Alternatives considered** — Removing only the break at the abbreviation's end byte misses breaks placed after closing punctuation or space. Masking punctuation in a second string risks changing separator behavior or losing source alignment. A general-purpose Unicode property dependency would still need an explicit version and payload review.

**Verification** — The Rust probe found the honorific directly before a Tamil name inside one baseline word span. The baseline sentence split after the honorific, at byte 13 without a space and byte 14 with one. A currency marker directly before `0035 0030 0030` produced separate baseline spans for the letters, period, and digits. The Tamil profile needs both merged abbreviation interiors and explicit endpoints. Measure long-input sentence behavior because the dependency's SB8 lookahead can revisit input.

## Use reviewed lexical data and independent annotations

**Decision** — Store abbreviation forms, contexts, provenance, and admitted stopwords in canonical TOML, then compile immutable sorted tables in `build.rs`. Keep the default `none` profile, a conservative subset, and a strict `broad` superset. Use the pinned Lucene Tamil list as a review pool. Use independently annotated Tamil Nadu and Sri Lankan passages to check missed and spurious word and sentence boundaries, with an exact result required on the reviewed cases.

**Rationale** — Regional attestation describes usage and applies one shared segmentation profile. Controlled continuations cover known abbreviation failures while keeping the engine independent of inference. Editorial review prevents inflected forms or content-bearing items from entering a search profile by default. The morning and afternoon markers both have Sri Lankan usage witnesses. [Module contract and evidence](../../docs/specs/tokenize-v0.1.md) · [Canonical data rules](../../docs/decisions/lexicon-text-storage.md)

**Alternatives considered** — Importing an upstream list wholesale would skip retrieval-oriented review. Whitespace splitting and generic punctuation heuristics miss adjacent abbreviations and produce avoidable punctuation count errors. Generated annotations would couple expected boundaries to the tool being evaluated.

## Place the model boundary outside Phase 9

**Decision** — Use linguistic spans for Phase 9. Keep model inference, model encoders, and model-budget chunking outside this feature.

**Rationale** — In a local run with `tiktoken` 0.14.0, `o200k_base` put `U+0BCD` in a separate token in `0BA4 0BAE 0BBF 0BB4 0BCD`. The repo's core groups it with `U+0BB4`. In a separate local run with Node 23.11.0 and ICU 76.1, `Intl.Segmenter("ta", { granularity: "sentence" })` split a composed example after the honorific `0BA4 0BBF 0BB0 0BC1 002E`. Phase 9 addresses the latter class of boundary errors and preserves the written unit in the former example. These observations measure encoder output and baseline boundaries. [OpenAI encoder reference](https://github.com/openai/tiktoken) · [Existing Word Add-in counting](../../integrations/office-word-addin/src/lib/tamil-engine.ts#L822)

**Alternatives considered** — A prompted segmenter would need a separate model and evaluation contract. Model-specific token counting applies a different vocabulary for each supported encoder. A future chunker can compose Phase 9 spans and apply a caller-supplied model measurement to each complete chunk.

## Stage the private engine and review archive integration

**Decision** — Develop the standalone Rank 2 crate with `publish.workspace = true` and a planned golden suite first. Verify real runtimes with planned vectors in an isolated candidate integration checkout. Land the facade and approved archive scope together after distinct fixture and release reviews.

**Rationale** — The release checker requires the public facade's internal dependencies to exactly match the approved crates. It rejects a private tokenizer dependency, including an optional one. Candidate-only wiring permits real parity evidence before activation without claiming the candidate passes the release-policy gate. Once the owner approves activation and reviews the package scope, the official gates can run against the coordinated candidate before landing. [Dependency closure check](../../tools/release_policy.py#L236) · [Publishing policy](../../docs/releases/policy.md) · [Planned fixture runners](../../tools/tasks.py#L1456)

**Alternatives considered** — Landing a private dependency in the public facade would fail the policy. An adapter-specific tokenizer would duplicate the engine. Temporarily marking the suite active would obscure what has been reviewed.
