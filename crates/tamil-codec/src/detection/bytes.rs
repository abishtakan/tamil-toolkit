//! 8-bit legacy encoding detection algorithms and scoring.
#![forbid(unsafe_code)]

use super::{
    signatures::{
        bamini_signature_score, english_word_density, native_utf8_tamil_ratio,
        tamil_orthographic_quality,
    },
    DetectionResult, EncodingCandidate, MAX_SAMPLE_BYTES,
};
use crate::{
    anjal_bytes_to_unicode, bamini_to_unicode, tab_bytes_to_unicode, tam_bytes_to_unicode,
    tscii_bytes_to_unicode, ErrorPolicy,
};

/// Detects 8-bit encodings (Bamini, TSCII, TAB, TAM, Anjal, and native UTF-8) from raw bytes.
pub fn detect_8bit_encoding(input: &[u8]) -> DetectionResult {
    let sample = if input.len() > MAX_SAMPLE_BYTES {
        &input[..MAX_SAMPLE_BYTES]
    } else {
        input
    };

    if sample.is_empty() {
        return DetectionResult::uncertain("empty input", Vec::new());
    }

    let non_whitespace = sample.iter().filter(|b| !b.is_ascii_whitespace()).count();
    if non_whitespace < 4 {
        return DetectionResult::uncertain("insufficient input length", Vec::new());
    }

    // 1. Check for native UTF-8 Tamil text
    let utf8_ratio = native_utf8_tamil_ratio(sample);
    if utf8_ratio > 0.05 {
        if let Ok(s) = std::str::from_utf8(sample) {
            let quality = tamil_orthographic_quality(s);
            if quality >= 0.80 {
                let candidates = vec![
                    EncodingCandidate {
                        encoding: "utf-8".into(),
                        confidence: 1.0,
                    },
                    EncodingCandidate {
                        encoding: "tscii-1.7-v1".into(),
                        confidence: 0.0,
                    },
                    EncodingCandidate {
                        encoding: "tab-v1".into(),
                        confidence: 0.0,
                    },
                    EncodingCandidate {
                        encoding: "tam-v1".into(),
                        confidence: 0.0,
                    },
                    EncodingCandidate {
                        encoding: "anjal-v1".into(),
                        confidence: 0.0,
                    },
                    EncodingCandidate {
                        encoding: "bamini-v1".into(),
                        confidence: 0.0,
                    },
                ];
                return DetectionResult::from_scored_candidates(candidates);
            }
        }
    }

    let mut candidates = Vec::with_capacity(6);
    candidates.push(EncodingCandidate {
        encoding: "utf-8".into(),
        confidence: 0.0,
    });

    let high_bytes_count = sample.iter().filter(|&&b| b >= 0x80).count();

    // 2. Score high-byte standards if non-ASCII bytes exist
    if high_bytes_count > 0 {
        // TSCII 1.7
        let tscii_score = match tscii_bytes_to_unicode(sample) {
            Ok(decoded) => tamil_orthographic_quality(&decoded),
            Err(_) => 0.0,
        };
        candidates.push(EncodingCandidate {
            encoding: "tscii-1.7-v1".into(),
            confidence: tscii_score,
        });

        // TAB
        let mut tab_score = match tab_bytes_to_unicode(sample) {
            Ok(decoded) => tamil_orthographic_quality(&decoded),
            Err(_) => 0.0,
        };

        // TAM
        let mut tam_score = match tam_bytes_to_unicode(sample) {
            Ok(decoded) => tamil_orthographic_quality(&decoded),
            Err(_) => 0.0,
        };

        // Disambiguate TAB (bilingual decomposed high-bytes) vs TAM (monolingual precomposed)
        if tab_score > 0.60 && tam_score > 0.60 {
            let has_tam_precomposed = sample
                .iter()
                .any(|&b| (0x41..=0x7E).contains(&b) || (0x80..=0x9F).contains(&b));
            let has_tab_decomposed_markers = sample
                .iter()
                .any(|&b| matches!(b, 0xA2 | 0xA3 | 0xA4 | 0xA6 | 0xA7 | 0xA8));
            if has_tab_decomposed_markers && !has_tam_precomposed {
                tam_score *= 0.70;
            } else if has_tam_precomposed {
                tab_score *= 0.70;
            }
        }

        candidates.push(EncodingCandidate {
            encoding: "tab-v1".into(),
            confidence: tab_score,
        });

        candidates.push(EncodingCandidate {
            encoding: "tam-v1".into(),
            confidence: tam_score,
        });

        // Anjal
        let anjal_score = match anjal_bytes_to_unicode(sample) {
            Ok(decoded) => tamil_orthographic_quality(&decoded),
            Err(_) => 0.0,
        };
        candidates.push(EncodingCandidate {
            encoding: "anjal-v1".into(),
            confidence: anjal_score,
        });
    } else {
        candidates.push(EncodingCandidate {
            encoding: "tscii-1.7-v1".into(),
            confidence: 0.0,
        });
        candidates.push(EncodingCandidate {
            encoding: "tab-v1".into(),
            confidence: 0.0,
        });
        candidates.push(EncodingCandidate {
            encoding: "tam-v1".into(),
            confidence: 0.0,
        });
        candidates.push(EncodingCandidate {
            encoding: "anjal-v1".into(),
            confidence: 0.0,
        });
    }

    // 3. Score Bamini (typewriter layout on ASCII keys)
    let eng_density = english_word_density(sample);
    let bamini_sig = bamini_signature_score(sample);

    let bamini_conf = if eng_density >= 0.10 || bamini_sig < 0.04 {
        0.0
    } else if let Ok(s) = std::str::from_utf8(sample) {
        match bamini_to_unicode(s, ErrorPolicy::Strict) {
            Ok(decoded) => {
                let quality = tamil_orthographic_quality(&decoded);
                if quality >= 0.80 {
                    ((quality * 0.7 + bamini_sig * 0.3) * (1.0 - eng_density * 2.0)).clamp(0.0, 1.0)
                } else {
                    0.0
                }
            }
            Err(_) => 0.0,
        }
    } else {
        0.0
    };

    candidates.push(EncodingCandidate {
        encoding: "bamini-v1".into(),
        confidence: bamini_conf,
    });

    let result = DetectionResult::from_scored_candidates(candidates);
    if result.status == crate::detection::DetectionStatus::Uncertain
        && result.reason == Some("low confidence".into())
        && (eng_density > 0.0 || (high_bytes_count == 0 && utf8_ratio == 0.0))
    {
        return DetectionResult::uncertain("no legacy tamil patterns detected", result.candidates);
    }
    result
}
