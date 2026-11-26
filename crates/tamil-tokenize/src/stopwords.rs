use std::str::FromStr;

use crate::tables::{BROAD, CONSERVATIVE};

/// Opt-in matching against a versioned list of complete words.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum StopwordProfile {
    #[default]
    None,
    Conservative,
    Broad,
}

impl FromStr for StopwordProfile {
    type Err = &'static str;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "none" => Ok(Self::None),
            "conservative" => Ok(Self::Conservative),
            "broad" => Ok(Self::Broad),
            _ => Err("unsupported stopword profile"),
        }
    }
}

impl StopwordProfile {
    pub(super) fn contains(self, text: &str) -> bool {
        let list = match self {
            Self::None => return false,
            Self::Conservative => CONSERVATIVE,
            Self::Broad => BROAD,
        };
        list.binary_search(&tamil_norm::normalize_nfc(text).as_str())
            .is_ok()
    }
}
