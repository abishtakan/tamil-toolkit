use proptest::prelude::*;
use tamil_tokenize::SourceSpan;

pub fn documents() -> impl Strategy<Value = String> {
    let relevant = prop::sample::select(vec![
        'a',
        '3',
        '.',
        ':',
        '!',
        ')',
        ' ',
        '\r',
        '\n',
        '\t',
        '\u{0085}',
        '\u{2028}',
        '\u{2029}',
        '\u{0b95}',
        '\u{0bb7}',
        '\u{0bbe}',
        '\u{0bc6}',
        '\u{0bcd}',
        '\u{0be7}',
        '\u{0300}',
        '\u{1f600}',
    ]);
    prop::collection::vec(prop_oneof![5 => relevant, 1 => any::<char>()], 0..96)
        .prop_map(|scalars| scalars.into_iter().collect())
}

pub fn verify<'a>(
    text: &str,
    spans: impl IntoIterator<Item = SourceSpan<'a>>,
) -> Result<(), TestCaseError> {
    let units: Vec<_> = tamil_core::Letters::new(text).collect();
    let mut used = vec![false; units.len()];
    let mut end = 0;
    for span in spans {
        prop_assert!(span.start_unit >= end && span.end_unit > span.start_unit);
        prop_assert_eq!(text.get(span.start_byte..span.end_byte), Some(span.text));
        prop_assert_eq!(units[span.start_unit..span.end_unit].concat(), span.text);
        used[span.start_unit..span.end_unit].fill(true);
        end = span.end_unit;
    }
    for (unit, used) in units.iter().zip(used) {
        prop_assert!(used || unit.chars().all(char::is_whitespace));
    }
    Ok(())
}
