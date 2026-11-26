mod support;

use std::collections::{BTreeMap, BTreeSet};
use std::time::Instant;
use tamil_tokenize::{segment_sentences, tokenize_words, StopwordProfile};
use unicode_segmentation::UnicodeSegmentation;

type Boundary = (usize, bool);

fn endpoints(start: usize, end: usize) -> [Boundary; 2] {
    [(start, true), (end, false)]
}

#[test]
fn annotated_boundaries() {
    let mut counts = BTreeMap::<(String, String), (usize, usize, usize)>::new();
    for row in support::rows().filter(|row| {
        row.get("expected").is_some() && row["input"].get("stopword_profile").is_none()
    }) {
        let op = row["op"].as_str().unwrap();
        let group = row["tags"][0].as_str().unwrap();
        let text = row["input"]["text"].as_str().unwrap();
        let is_word = op == "tokenize_words";
        let expected: BTreeSet<_> = row["expected"]
            .as_array()
            .unwrap()
            .iter()
            .flat_map(|span| {
                endpoints(
                    span["start_byte"].as_u64().unwrap() as usize,
                    span["end_byte"].as_u64().unwrap() as usize,
                )
            })
            .collect();
        let tailored = if is_word {
            tokenize_words(text, StopwordProfile::None)
                .into_iter()
                .map(|token| token.span)
                .collect()
        } else {
            segment_sentences(text)
        };
        let actual: BTreeSet<_> = tailored
            .iter()
            .flat_map(|span| endpoints(span.start_byte, span.end_byte))
            .collect();
        assert_eq!(actual, expected, "{}", row["id"]);

        let raw: Vec<_> = if is_word {
            text.split_word_bound_indices().collect()
        } else {
            text.split_sentence_bound_indices().collect()
        };
        let default: BTreeSet<_> = raw
            .into_iter()
            .filter_map(|(offset, chunk)| {
                let units: Vec<_> = tamil_core::Letters::new(chunk).collect();
                let whitespace = |unit: &&str| unit.chars().all(char::is_whitespace);
                let leading: usize = units
                    .iter()
                    .take_while(|unit| whitespace(unit))
                    .map(|unit| unit.len())
                    .sum();
                if leading == chunk.len() {
                    return None;
                }
                let trailing: usize = units
                    .iter()
                    .rev()
                    .take_while(|unit| whitespace(unit))
                    .map(|unit| unit.len())
                    .sum();
                Some(endpoints(offset + leading, offset + chunk.len() - trailing))
            })
            .flatten()
            .collect();
        let count = counts.entry((op.to_owned(), group.to_owned())).or_default();
        count.0 += expected.intersection(&default).count();
        count.1 += expected.difference(&default).count();
        count.2 += default.difference(&expected).count();
    }
    for ((op, group), (matched, missed, spurious)) in counts {
        println!("{op}/{group}: baseline {matched} matched, {missed} missed, {spurious} spurious; tailored exact");
    }
}

#[test]
fn observe_mixed_and_punctuation_costs() {
    for (label, text) in [
        (
            "mixed",
            "\u{0ba4}\u{0bbf}\u{0bb0}\u{0bc1}. \u{0b95}\u{0bc1} plus 42! \u{1f600} ".repeat(4096),
        ),
        ("punctuation", "X. (( 123, 456 ))! ... \r\n".repeat(4096)),
    ] {
        let start = Instant::now();
        let words = tokenize_words(&text, StopwordProfile::None);
        let word_time = start.elapsed();
        let sentences = segment_sentences(&text);
        println!(
            "{label}: {} bytes, {} word tokens in {word_time:?}, {} sentences in {:?}",
            text.len(),
            words.len(),
            sentences.len(),
            start.elapsed() - word_time
        );
    }
}
