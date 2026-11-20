//! Host-only canonical JSON formatting and SHA-256 helpers for Python batch bindings.
//! Not part of the cross-runtime `OPERATIONS` dispatcher.

use sha2::{Digest, Sha256};

const HEX: &[u8; 16] = b"0123456789abcdef";

#[inline]
fn push_u4_hex(buf: &mut Vec<u8>, v: u16) {
    buf.extend_from_slice(&[
        b'\\',
        b'u',
        HEX[((v >> 12) & 0xF) as usize],
        HEX[((v >> 8) & 0xF) as usize],
        HEX[((v >> 4) & 0xF) as usize],
        HEX[(v & 0xF) as usize],
    ]);
}

#[inline]
fn push_common_escape(buf: &mut Vec<u8>, cp: u32) -> bool {
    match cp {
        0x22 => buf.extend_from_slice(b"\\\""),
        0x5C => buf.extend_from_slice(b"\\\\"),
        0x08 => buf.extend_from_slice(b"\\b"),
        0x0C => buf.extend_from_slice(b"\\f"),
        0x0A => buf.extend_from_slice(b"\\n"),
        0x0D => buf.extend_from_slice(b"\\r"),
        0x09 => buf.extend_from_slice(b"\\t"),
        _ => return false,
    }
    true
}

/// Append a JSON-quoted ASCII string matching CPython `json.dumps(..., ensure_ascii=True)`.
pub fn push_ascii_json_str(buf: &mut Vec<u8>, s: &str) {
    buf.push(b'"');
    if s.bytes()
        .all(|b| (0x20..=0x7E).contains(&b) && b != b'"' && b != b'\\')
    {
        buf.extend_from_slice(s.as_bytes());
        buf.push(b'"');
        return;
    }
    for ch in s.chars() {
        let cp = ch as u32;
        if push_common_escape(buf, cp) {
            continue;
        }
        if (0x20..=0x7E).contains(&cp) {
            buf.push(cp as u8);
        } else if cp <= 0xFFFF {
            push_u4_hex(buf, cp as u16);
        } else {
            let n = cp - 0x10000;
            let hi = (0xD800 + (n >> 10)) as u16;
            let lo = (0xDC00 + (n & 0x3FF)) as u16;
            push_u4_hex(buf, hi);
            push_u4_hex(buf, lo);
        }
    }
    buf.push(b'"');
}

#[inline]
const fn is_data_json_extra_escape(cp: u32) -> bool {
    (cp >= 0x7F && cp <= 0x9F) || matches!(cp, 0x00AD | 0x200C | 0x200D | 0x2028 | 0x2029 | 0xFEFF)
}

/// Append a JSON-quoted UTF-8 string matching `tools.lexicon.data_json`.
pub fn push_data_json_str(buf: &mut Vec<u8>, s: &str) {
    buf.push(b'"');
    if s.bytes()
        .all(|b| (0x20..=0x7E).contains(&b) && b != b'"' && b != b'\\')
    {
        buf.extend_from_slice(s.as_bytes());
        buf.push(b'"');
        return;
    }
    let mut utf8_tmp = [0u8; 4];
    for ch in s.chars() {
        let cp = ch as u32;
        if push_common_escape(buf, cp) {
            continue;
        }
        if cp < 0x20 || is_data_json_extra_escape(cp) {
            push_u4_hex(buf, cp as u16);
        } else {
            buf.extend_from_slice(ch.encode_utf8(&mut utf8_tmp).as_bytes());
        }
    }
    buf.push(b'"');
}

/// Compute lowercase hex SHA-256 digest.
pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut out = String::with_capacity(64);
    for byte in digest {
        out.push(HEX[(byte >> 4) as usize] as char);
        out.push(HEX[(byte & 0xF) as usize] as char);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ascii_and_data_json_str_match_cpython_escaping() {
        // Construct intentional codec controls by scalar, without source joiners.
        let sample: String = [
            0x00, 0x08, 0x09, 0x0a, 0x0c, 0x0d, 0x1f, 0x7f, 0x80, 0x9f, 0xad, 0x200c, 0x200d,
            0x2028, 0x2029, 0xfeff, 0x0b85, 0x1f600,
        ]
        .into_iter()
        .map(|cp| char::from_u32(cp).unwrap())
        .collect();
        let mut ascii = Vec::new();
        push_ascii_json_str(&mut ascii, &sample);
        assert_eq!(
            String::from_utf8(ascii).unwrap(),
            concat!(
                r#""\u0000\b\t\n\f\r\u001f\u007f\u0080\u009f\u00ad\u"#,
                r#"200c\u"#,
                r#"200d\u2028\u2029\ufeff\u0b85\ud83d\ude00""#
            )
        );

        let mut data = Vec::new();
        push_data_json_str(&mut data, &sample);
        assert_eq!(
            String::from_utf8(data).unwrap(),
            concat!(
                "\"\\u0000\\b\\t\\n\\f\\r\\u001f\\u007f\\u0080\\u009f\\u00ad\\u",
                "200c\\u",
                "200d\\u2028\\u2029\\ufeff\u{0b85}\u{1f600}\""
            )
        );
    }

    #[test]
    fn sha256_hex_known_digest() {
        assert_eq!(
            sha256_hex(b"[]"),
            "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
        );
    }
}
