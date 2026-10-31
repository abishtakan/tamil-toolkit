//! Explicit Bamini conversion and bounded TSCII byte decoding.
//! See the codec specifications for coverage, ambiguity, and non-reversibility.
#![forbid(unsafe_code)]

use tamil_core::normalize_nfc;

#[derive(Clone, Copy)]
enum Terminal {
    Text(&'static str),
    Ambiguous,
}
struct Node {
    edges: &'static [(u8, usize)],
    terminal: Option<Terminal>,
}
mod tables {
    use super::{Node, Terminal};
    include!(concat!(env!("OUT_DIR"), "/bamini_tables.rs"));
}
mod tscii_tables {
    use super::{Node, Terminal};
    include!(concat!(env!("OUT_DIR"), "/tscii_tables.rs"));
}
pub use tables::PROFILE;
pub use tscii_tables::PROFILE as TSCII_PROFILE;
pub const ROUNDTRIP_ERROR: &str = "Bamini encoding is not reversible for this input";

/// Strict fails at the first unsupported/ambiguous scalar. Preserve retains it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorPolicy {
    Strict,
    Preserve,
}
impl ErrorPolicy {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "strict" => Ok(Self::Strict),
            "preserve" => Ok(Self::Preserve),
            _ => Err("unsupported codec error policy".into()),
        }
    }
}

fn longest_match(input: &[u8], nodes: &[Node], maximum: usize) -> Option<(usize, Terminal)> {
    let mut current = 0;
    let mut found = None;
    for (index, byte) in input.iter().take(maximum).enumerate() {
        let node = &nodes[current];
        let edge = match node.edges.binary_search_by_key(byte, |&(key, _)| key) {
            Ok(edge) => edge,
            Err(_) => break,
        };
        current = node.edges[edge].1;
        if let Some(terminal) = nodes[current].terminal {
            found = Some((index + 1, terminal));
        }
    }
    found
}

/// Decode a bounded TSCII byte profile, preserving ASCII and returning NFC.
/// Unsupported bytes fail with their original byte offset.
pub fn tscii_bytes_to_unicode(bytes: &[u8]) -> Result<String, String> {
    let mut position = 0;
    let mut output = String::with_capacity(bytes.len());
    while position < bytes.len() {
        let byte = bytes[position];
        if byte < 0x80 {
            output.push(char::from(byte));
            position += 1;
        } else if let Some((length, Terminal::Text(value))) =
            longest_match(&bytes[position..], tscii_tables::NODES, 3)
        {
            output.push_str(value);
            position += length;
        } else {
            return Err(format!(
                "unsupported TSCII byte at offset {position}: 0x{byte:02X}"
            ));
        }
    }
    Ok(normalize_nfc(&output))
}

/// Convert explicitly selected Bamini text. Allocates and normalizes output to NFC.
/// Latin/English text shares the encoding's character codes and is not detected.
pub fn bamini_to_unicode(text: &str, errors: ErrorPolicy) -> Result<String, String> {
    let mut position = 0;
    let mut output = String::with_capacity(text.len());
    while position < text.len() {
        let tail = &text[position..];
        match longest_match(tail.as_bytes(), tables::NODES, tables::MAX_KEY_BYTES) {
            Some((length, Terminal::Text(value))) => {
                output.push_str(value);
                position += length;
            }
            Some((length, Terminal::Ambiguous)) => {
                if errors == ErrorPolicy::Strict {
                    // Build-time validation restricts ambiguous keys to one ASCII byte.
                    return Err(format!(
                        "ambiguous Bamini sequence at byte {position}: U+{:04X}",
                        u32::from(tail.as_bytes()[0])
                    ));
                }
                output.push_str(&tail[..length]);
                position += length;
            }
            None => {
                let scalar = tail.chars().next().expect("non-empty UTF-8 tail");
                if errors == ErrorPolicy::Strict && !tables::PASSTHROUGH.contains(scalar) {
                    return Err(format!(
                        "unsupported Bamini scalar at byte {position}: U+{:04X}",
                        u32::from(scalar)
                    ));
                }
                output.push(scalar);
                position += scalar.len_utf8();
            }
        }
    }
    Ok(normalize_nfc(&output))
}

/// Canonical Unicode -> ASCII Bamini. Every accepted input round-trips to its NFC.
/// Unsupported scalars and key-boundary collisions fail without partial output.
pub fn unicode_to_bamini(text: &str) -> Result<String, String> {
    let normalized = normalize_nfc(text);
    let mut position = 0;
    let mut output = String::with_capacity(normalized.len());
    while position < normalized.len() {
        let tail = &normalized[position..];
        if let Some((length, Terminal::Text(value))) = longest_match(
            tail.as_bytes(),
            tables::ENCODE_NODES,
            tables::MAX_UNICODE_KEY_BYTES,
        ) {
            output.push_str(value);
            position += length;
        } else {
            let scalar = tail
                .chars()
                .next()
                .expect("non-empty normalized UTF-8 tail");
            if !tables::PASSTHROUGH.contains(scalar) {
                return Err(format!(
                    "unsupported Unicode scalar for Bamini at NFC byte {position}: U+{:04X}",
                    u32::from(scalar)
                ));
            }
            output.push(scalar);
            position += scalar.len_utf8();
        }
    }
    match bamini_to_unicode(&output, ErrorPolicy::Strict) {
        Ok(decoded) if decoded == normalized => Ok(output),
        _ => Err(ROUNDTRIP_ERROR.into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_utf8_never_panics(text in ".{0,96}") {
            let _ = bamini_to_unicode(&text, ErrorPolicy::Strict);
            prop_assert!(bamini_to_unicode(&text, ErrorPolicy::Preserve).is_ok());
        }
        #[test]
        fn arbitrary_tscii_bytes_never_panic(bytes in prop::collection::vec(any::<u8>(), 0..128)) {
            let _ = tscii_bytes_to_unicode(&bytes);
        }
        #[test]
        fn preserve_output_is_nfc_and_keeps_joiners(text in ".{0,96}", zwj in any::<bool>()) {
            let joiner = char::from_u32(if zwj { 0x200d } else { 0x200c }).unwrap();
            let text = format!("{text}{joiner}f{joiner}h");
            let output = bamini_to_unicode(&text, ErrorPolicy::Preserve).unwrap();
            prop_assert_eq!(&output, &normalize_nfc(&output));
            for code in [0x200c, 0x200d] {
                prop_assert_eq!(text.chars().filter(|c| u32::from(*c) == code).count(), output.chars().filter(|c| u32::from(*c) == code).count());
            }
        }
        #[test]
        fn passthrough_text_stays_exact(indices in prop::collection::vec(0_usize..tables::PASSTHROUGH.len(), 0..128)) {
            let input: String = indices.iter().map(|&index| tables::PASSTHROUGH.as_bytes()[index] as char).collect();
            let strict = bamini_to_unicode(&input, ErrorPolicy::Strict).unwrap();
            prop_assert_eq!(strict.as_str(), input.as_str());
            prop_assert_eq!(bamini_to_unicode(&input, ErrorPolicy::Preserve).unwrap(), input);
        }
        #[test]
        fn arbitrary_utf8_encoding_never_panics(text in ".{0,96}") {
            if let Ok(encoded) = unicode_to_bamini(&text) {
                prop_assert!(encoded.is_ascii());
                prop_assert_eq!(bamini_to_unicode(&encoded, ErrorPolicy::Strict).unwrap(), normalize_nfc(&text));
            }
        }
        #[test]
        fn supported_sequences_roundtrip_or_report_collision(letters in prop::collection::vec(prop::sample::select(tables::ENCODABLE_TEXT.to_vec()), 0..32)) {
            let text = letters.concat();
            let result = unicode_to_bamini(&text);
            prop_assert_eq!(&result, &unicode_to_bamini(&tamil_core::normalize_nfd(&text)));
            match result {
                Ok(encoded) => {
                    prop_assert!(encoded.is_ascii());
                    prop_assert_eq!(bamini_to_unicode(&encoded, ErrorPolicy::Strict).unwrap(), normalize_nfc(&text));
                }
                Err(error) => prop_assert_eq!(error, ROUNDTRIP_ERROR),
            }
        }
    }
}
