use unicode_segmentation::UnicodeSegmentation;

fn verify(source: &str, segment: impl Fn(&str) -> Vec<usize>) {
    assert_eq!(unicode_segmentation::UNICODE_VERSION, (17, 0, 0));
    for (line, raw) in source.lines().enumerate() {
        let pattern = raw.split('#').next().unwrap().trim();
        if pattern.is_empty() {
            continue;
        }
        let mut text = String::new();
        let mut expected = Vec::new();
        for field in pattern.split_whitespace() {
            match field {
                "\u{00f7}" => expected.push(text.len()),
                "\u{00d7}" => (),
                hex => text.push(char::from_u32(u32::from_str_radix(hex, 16).unwrap()).unwrap()),
            }
        }
        assert_eq!(segment(&text), expected, "reference row {}", line + 1);
    }
}

#[test]
fn unicode_17_word_boundaries() {
    verify(
        include_str!("../../../tests/reference/unicode-17.0.0/WordBreakTest.txt"),
        |text| {
            text.split_word_bound_indices()
                .map(|(offset, _)| offset)
                .chain([text.len()])
                .collect()
        },
    );
}

#[test]
fn unicode_17_sentence_boundaries() {
    verify(
        include_str!("../../../tests/reference/unicode-17.0.0/SentenceBreakTest.txt"),
        |text| {
            text.split_sentence_bound_indices()
                .map(|(offset, _)| offset)
                .chain([text.len()])
                .collect()
        },
    );
}
