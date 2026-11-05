//! Automatic legacy Tamil encoding detection and candidate ranking.
#![forbid(unsafe_code)]

#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};

pub mod bytes;
pub mod cids;
pub mod signatures;

/// Maximum number of bytes or code units to sample during detection.
pub const MAX_SAMPLE_BYTES: usize = 4096;

/// High-level status of an encoding detection attempt.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[cfg_attr(feature = "serde", serde(rename_all = "lowercase"))]
pub enum DetectionStatus {
    Detected,
    Uncertain,
}

impl DetectionStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Detected => "detected",
            Self::Uncertain => "uncertain",
        }
    }
}

/// An evaluated encoding candidate with its normalized confidence score.
#[derive(Debug, Clone, PartialEq)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
pub struct EncodingCandidate {
    pub encoding: String,
    pub confidence: f64,
}

/// The comprehensive outcome of an encoding detection attempt.
#[derive(Debug, Clone, PartialEq)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
pub struct DetectionResult {
    pub status: DetectionStatus,
    pub encoding: Option<String>,
    pub confidence: f64,
    pub reason: Option<String>,
    pub candidates: Vec<EncodingCandidate>,
}

impl DetectionResult {
    /// Creates an uncertain detection result with an explicit reason.
    pub fn uncertain(reason: impl Into<String>, candidates: Vec<EncodingCandidate>) -> Self {
        let mut sorted = candidates;
        sorted.sort_by(|a, b| {
            b.confidence
                .total_cmp(&a.confidence)
                .then_with(|| a.encoding.cmp(&b.encoding))
        });
        let confidence = sorted.first().map_or(0.0, |c| c.confidence);
        Self {
            status: DetectionStatus::Uncertain,
            encoding: None,
            confidence,
            reason: Some(reason.into()),
            candidates: sorted,
        }
    }

    /// Evaluates candidate rankings and produces either a Detected or Uncertain result.
    pub fn from_scored_candidates(mut candidates: Vec<EncodingCandidate>) -> Self {
        candidates.sort_by(|a, b| {
            b.confidence
                .total_cmp(&a.confidence)
                .then_with(|| a.encoding.cmp(&b.encoding))
        });

        let (top_conf, second_conf) = match candidates.as_slice() {
            [] => (0.0, 0.0),
            [first] => (first.confidence, 0.0),
            [first, second, ..] => (first.confidence, second.confidence),
        };

        if candidates.is_empty() || top_conf < 0.60 {
            return Self {
                status: DetectionStatus::Uncertain,
                encoding: None,
                confidence: top_conf,
                reason: Some("low confidence".into()),
                candidates,
            };
        }

        if candidates.len() > 1 && (top_conf - second_conf) < 0.15 {
            return Self {
                status: DetectionStatus::Uncertain,
                encoding: None,
                confidence: top_conf,
                reason: Some("conflicting candidates".into()),
                candidates,
            };
        }

        let top_encoding = candidates[0].encoding.clone();
        Self {
            status: DetectionStatus::Detected,
            encoding: Some(top_encoding),
            confidence: top_conf,
            reason: None,
            candidates,
        }
    }
}
