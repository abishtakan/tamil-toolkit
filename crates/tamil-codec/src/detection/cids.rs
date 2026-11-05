//! 16-bit CID font code units detection algorithms (LT-TM and Vanavil Avvaiyar).
#![forbid(unsafe_code)]

use super::{
    signatures::tamil_orthographic_quality, DetectionResult, EncodingCandidate, MAX_SAMPLE_BYTES,
};
use crate::{cid_fallback, lt_tm_codes_to_unicode, vanavil_codes_to_unicode, ErrorPolicy};

/// Detects 16-bit CID font profiles from code units.
pub fn detect_cid_encoding(input: &[u16]) -> DetectionResult {
    let sample = if input.len() > MAX_SAMPLE_BYTES {
        &input[..MAX_SAMPLE_BYTES]
    } else {
        input
    };

    if sample.is_empty() {
        return DetectionResult::uncertain("empty input", Vec::new());
    }

    let non_whitespace = sample
        .iter()
        .filter(|&&c| !matches!(c, 0x0009..=0x000D | 0x0020))
        .count();
    if non_whitespace < 4 {
        return DetectionResult::uncertain("insufficient input length", Vec::new());
    }

    let non_fallback = sample.iter().filter(|&&c| !cid_fallback(c)).count();

    let mut lt_tm_score = match lt_tm_codes_to_unicode(sample, ErrorPolicy::Strict) {
        Ok(decoded) => tamil_orthographic_quality(&decoded),
        Err(_) => 0.0,
    };

    let mut vanavil_score = match vanavil_codes_to_unicode(sample, ErrorPolicy::Strict) {
        Ok(decoded) => tamil_orthographic_quality(&decoded),
        Err(_) => 0.0,
    };

    if lt_tm_score > 0.60 && vanavil_score > 0.60 {
        // Disambiguate LT-TM vs Vanavil on distinctive CIDs:
        // LT-TM uses 0x00C0..=0x00CF for short 'i' uyirmei (e.g. 0x00C4 for 'mi')
        // Vanavil uses 0x00E0..=0x00EF for short 'i' uyirmei (e.g. 0x00E4 for 'mi')
        let has_lt_tm_short_i = sample.iter().any(|&c| (0x00C0..=0x00CF).contains(&c));
        let has_vanavil_short_i = sample.iter().any(|&c| (0x00E0..=0x00EF).contains(&c));

        if has_lt_tm_short_i && !has_vanavil_short_i {
            vanavil_score *= 0.70;
        } else if has_vanavil_short_i && !has_lt_tm_short_i {
            lt_tm_score *= 0.70;
        } else {
            // Check dictionary word match delta
            let lt_decoded =
                lt_tm_codes_to_unicode(sample, ErrorPolicy::Strict).unwrap_or_default();
            let va_decoded =
                vanavil_codes_to_unicode(sample, ErrorPolicy::Strict).unwrap_or_default();
            let lt_hits = crate::detection::signatures::COMMON_TAMIL_WORDS
                .iter()
                .filter(|&&w| lt_decoded.contains(w))
                .count();
            let va_hits = crate::detection::signatures::COMMON_TAMIL_WORDS
                .iter()
                .filter(|&&w| va_decoded.contains(w))
                .count();
            if lt_hits > va_hits {
                vanavil_score *= 0.70;
            } else if va_hits > lt_hits {
                lt_tm_score *= 0.70;
            }
        }
    }

    let candidates = vec![
        EncodingCandidate {
            encoding: "lt-tm-cid-v1".into(),
            confidence: lt_tm_score,
        },
        EncodingCandidate {
            encoding: "vanavil-avvaiyar-cid-v1".into(),
            confidence: vanavil_score,
        },
    ];

    let result = DetectionResult::from_scored_candidates(candidates);
    if result.status == crate::detection::DetectionStatus::Uncertain
        && result.reason == Some("low confidence".into())
        && non_fallback == 0
    {
        return DetectionResult::uncertain("no legacy tamil patterns detected", result.candidates);
    }
    result
}
