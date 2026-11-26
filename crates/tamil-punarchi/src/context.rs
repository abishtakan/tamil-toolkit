//! Domain types, two-level grammatical context, result structures, and exact contract validation.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Maximum UTF-8 byte length accepted by `punarchi_split_candidates`.
pub const MAX_SPLIT_SURFACE_BYTES: usize = 256;

/// Named, versioned grammatical tradition governing Sandhi rule selection.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize)]
pub enum PunarchiProfile {
    #[default]
    #[serde(rename = "nannool-v1")]
    NannoolV1,
}

impl PunarchiProfile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::NannoolV1 => "nannool-v1",
        }
    }

    pub fn parse(raw: &str) -> Result<Self, PunarchiError> {
        match raw {
            "nannool-v1" => Ok(Self::NannoolV1),
            _ => Err(PunarchiError::UnsupportedProfile),
        }
    }
}

/// Five chapters covered by the 117-sutra `nannool-v1` inventory.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PunarchiChapter {
    Ezhuttiyal,
    Padaviyal,
    Uyireeru,
    Meyyeeru,
    Urupu,
}

impl PunarchiChapter {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Ezhuttiyal => "ezhuttiyal",
            Self::Padaviyal => "padaviyal",
            Self::Uyireeru => "uyireeru",
            Self::Meyyeeru => "meyyeeru",
            Self::Urupu => "urupu",
        }
    }

    pub fn parse(raw: &str) -> Result<Self, PunarchiError> {
        match raw {
            "ezhuttiyal" => Ok(Self::Ezhuttiyal),
            "padaviyal" => Ok(Self::Padaviyal),
            "uyireeru" => Ok(Self::Uyireeru),
            "meyyeeru" => Ok(Self::Meyyeeru),
            "urupu" => Ok(Self::Urupu),
            _ => Err(PunarchiError::UnsupportedChapter),
        }
    }
}

/// Coarse grammatical relation between *Nilaimozhi* and *Varumozhi* (Nannool 152).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GrammaticalRelation {
    #[default]
    Unspecified,
    Vetrumai,
    Alvazhi,
}

impl GrammaticalRelation {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Unspecified => "unspecified",
            Self::Vetrumai => "vetrumai",
            Self::Alvazhi => "alvazhi",
        }
    }

    pub fn parse(raw: &str) -> Result<Self, PunarchiError> {
        match raw {
            "unspecified" => Ok(Self::Unspecified),
            "vetrumai" => Ok(Self::Vetrumai),
            "alvazhi" => Ok(Self::Alvazhi),
            _ => Err(PunarchiError::UnsupportedRelation),
        }
    }
}

/// Fine-grained grammatical subtype (Cases 2-7 + Nannool 152 Alvazhi subtypes + specific triggers).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContextSubtype {
    // Vetrumai (cases 2-7)
    Case2,
    Case3,
    Case4,
    Case5,
    Case6,
    Case7,
    // Alvazhi Thogainilai (5)
    Vinaithogai,
    Panputhogai,
    Uvamaithogai,
    Ummaithogai,
    Anmozhi,
    // Alvazhi Thogaanilai (9)
    Ezhuvai,
    Vili,
    Peyarecham,
    Vinaiyecham,
    VinaiMutru,
    KurippuVinaiMutru,
    Idaiccol,
    Uriccol,
    Adukkuthodar,
    // Specific verb/compound triggers (5)
    Imperative,
    SecondPersonVerb,
    Viyankol,
    Distributive,
    Ilakkanappoli,
}

impl ContextSubtype {
    pub fn is_vetrumai(self) -> bool {
        matches!(
            self,
            Self::Case2 | Self::Case3 | Self::Case4 | Self::Case5 | Self::Case6 | Self::Case7
        )
    }

    pub fn is_compatible_with(self, relation: GrammaticalRelation) -> bool {
        match relation {
            GrammaticalRelation::Unspecified => true,
            GrammaticalRelation::Vetrumai => self.is_vetrumai(),
            GrammaticalRelation::Alvazhi => !self.is_vetrumai(),
        }
    }

    pub fn case_number(self) -> Option<u8> {
        match self {
            Self::Case2 => Some(2),
            Self::Case3 => Some(3),
            Self::Case4 => Some(4),
            Self::Case5 => Some(5),
            Self::Case6 => Some(6),
            Self::Case7 => Some(7),
            _ => None,
        }
    }

    pub fn parse(raw: &str) -> Result<Self, PunarchiError> {
        match raw {
            "case_2" => Ok(Self::Case2),
            "case_3" => Ok(Self::Case3),
            "case_4" => Ok(Self::Case4),
            "case_5" => Ok(Self::Case5),
            "case_6" => Ok(Self::Case6),
            "case_7" => Ok(Self::Case7),
            "vinaithogai" => Ok(Self::Vinaithogai),
            "panputhogai" => Ok(Self::Panputhogai),
            "uvamaithogai" => Ok(Self::Uvamaithogai),
            "ummaithogai" => Ok(Self::Ummaithogai),
            "anmozhi" => Ok(Self::Anmozhi),
            "ezhuvai" => Ok(Self::Ezhuvai),
            "vili" => Ok(Self::Vili),
            "peyarecham" => Ok(Self::Peyarecham),
            "vinaiyecham" => Ok(Self::Vinaiyecham),
            "vinai_mutru" => Ok(Self::VinaiMutru),
            "kurippu_vinai_mutru" => Ok(Self::KurippuVinaiMutru),
            "idaiccol" => Ok(Self::Idaiccol),
            "uriccol" => Ok(Self::Uriccol),
            "adukkuthodar" => Ok(Self::Adukkuthodar),
            "imperative" => Ok(Self::Imperative),
            "second_person_verb" => Ok(Self::SecondPersonVerb),
            "viyankol" => Ok(Self::Viyankol),
            "distributive" => Ok(Self::Distributive),
            "ilakkanappoli" => Ok(Self::Ilakkanappoli),
            _ => Err(PunarchiError::UnsupportedOrIncompatibleSubtype),
        }
    }
}

/// Optional semantic/morphological lexical class tags gated by audited Tier C sutras (27 tags).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LexicalClass {
    RationalNoun,
    NonRationalNoun,
    CommonNoun,
    TreeName,
    TastePuli,
    MeasureWord,
    QuantityWord,
    NumberWord,
    DirectionWord,
    Pronoun,
    Demonstrative,
    Interrogative,
    BranchName,
    QualityNoun,
    VerbalNounRoot,
    VerbalNounDerived,
    NegationStem,
    CliticParticle,
    LocativeParticle,
    TemporalParticle,
    NegativePluralVerb,
    PassiveActionCompound,
    FoodSesame,
    SwanEkin,
    DiceVal,
    CloudSel,
    SmithKol,
}

impl LexicalClass {
    pub fn parse(raw: &str) -> Result<Self, PunarchiError> {
        match raw {
            "rational_noun" => Ok(Self::RationalNoun),
            "non_rational_noun" => Ok(Self::NonRationalNoun),
            "common_noun" => Ok(Self::CommonNoun),
            "tree_name" => Ok(Self::TreeName),
            "taste_puli" => Ok(Self::TastePuli),
            "measure_word" => Ok(Self::MeasureWord),
            "quantity_word" => Ok(Self::QuantityWord),
            "number_word" => Ok(Self::NumberWord),
            "direction_word" => Ok(Self::DirectionWord),
            "pronoun" => Ok(Self::Pronoun),
            "demonstrative" => Ok(Self::Demonstrative),
            "interrogative" => Ok(Self::Interrogative),
            "branch_name" => Ok(Self::BranchName),
            "quality_noun" => Ok(Self::QualityNoun),
            "verbal_noun_root" => Ok(Self::VerbalNounRoot),
            "verbal_noun_derived" => Ok(Self::VerbalNounDerived),
            "negation_stem" => Ok(Self::NegationStem),
            "clitic_particle" => Ok(Self::CliticParticle),
            "locative_particle" => Ok(Self::LocativeParticle),
            "temporal_particle" => Ok(Self::TemporalParticle),
            "negative_plural_verb" => Ok(Self::NegativePluralVerb),
            "passive_action_compound" => Ok(Self::PassiveActionCompound),
            "food_sesame" => Ok(Self::FoodSesame),
            "swan_ekin" => Ok(Self::SwanEkin),
            "dice_val" => Ok(Self::DiceVal),
            "cloud_sel" => Ok(Self::CloudSel),
            "smith_kol" => Ok(Self::SmithKol),
            _ => Err(PunarchiError::UnsupportedLexicalClass),
        }
    }
}

/// Optional two-level grammatical context passed to `punarchi_join`.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct PunarchiContext {
    #[serde(default)]
    pub relation: GrammaticalRelation,
    #[serde(default)]
    pub subtype: Option<ContextSubtype>,
    #[serde(default)]
    pub lexical_class: Option<LexicalClass>,
    #[serde(default)]
    pub poetic: bool,
}

impl PunarchiContext {
    /// Validate that `subtype` (if supplied) is compatible with `relation`.
    pub fn validate(&self) -> Result<(), PunarchiError> {
        if let Some(sub) = self.subtype {
            if !sub.is_compatible_with(self.relation) {
                return Err(PunarchiError::UnsupportedOrIncompatibleSubtype);
            }
        }
        Ok(())
    }

    /// Return the effective grammatical relation, inferring from `subtype` when `relation == Unspecified`.
    pub fn effective_relation(&self) -> GrammaticalRelation {
        if self.relation != GrammaticalRelation::Unspecified {
            return self.relation;
        }
        match self.subtype {
            Some(sub) if sub.is_vetrumai() => GrammaticalRelation::Vetrumai,
            Some(_) => GrammaticalRelation::Alvazhi,
            None => GrammaticalRelation::Unspecified,
        }
    }
}

/// Four classical Nannool Sandhi alteration classes (Sutras 153-154).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AlterationKind {
    Iyalbu,
    Thonral,
    Thirithal,
    Keduthal,
}

impl AlterationKind {
    pub fn parse_str(raw: &str) -> Self {
        match raw {
            "iyalbu" => Self::Iyalbu,
            "thonral" => Self::Thonral,
            "thirithal" => Self::Thirithal,
            "keduthal" => Self::Keduthal,
            _ => Self::Iyalbu,
        }
    }
}

/// Single ordered rule application in a forward join or reverse split trace.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DerivationStep {
    pub sutra: u16,
    pub rule_id: String,
    pub stage: u8,
    pub transform: AlterationKind,
    pub before: String,
    pub after: String,
}

/// Secondary valid joined form surfaced when context is omitted or Nannool permits optional variants.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct JoinAlternative {
    pub surface: String,
    pub transform: AlterationKind,
    pub steps: Vec<DerivationStep>,
    pub required_context: Option<String>,
    pub optional_variant: bool,
    pub poetic: bool,
}

/// Complete deterministic result of `punarchi_join`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PunarchiJoinResult {
    pub profile: PunarchiProfile,
    pub surface: String,
    pub transform: AlterationKind,
    pub steps: Vec<DerivationStep>,
    pub alternatives: Vec<JoinAlternative>,
}

/// Single-boundary two-part reverse split candidate returned by `punarchi_split_candidates`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SplitCandidate {
    pub first: String,
    pub second: String,
    pub sutra: u16,
    pub rule_id: String,
    pub transform: AlterationKind,
    pub steps: Vec<DerivationStep>,
    pub split_byte: usize,
    pub split_unit: usize,
}

/// Exact contract validation errors shared across Rust, Python, JS/WASM, and Dart (`contracts/punarchi.md` §2).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PunarchiError {
    ExpectedInputObject,
    ExpectedStringInput,
    EmptyInput,
    SurfaceTooLong,
    ExpectedProfileString,
    UnsupportedProfile,
    ExpectedContextObject,
    UnsupportedRelation,
    UnsupportedOrIncompatibleSubtype,
    UnsupportedLexicalClass,
    ExpectedPoeticBoolean,
    UnsupportedChapter,
    SutraOutOfRange,
}

impl PunarchiError {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ExpectedInputObject => "expected punarchi input object",
            Self::ExpectedStringInput => "expected a string input",
            Self::EmptyInput => "punarchi: input components must not be empty",
            Self::SurfaceTooLong => "punarchi: surface input exceeds maximum length",
            Self::ExpectedProfileString => "expected profile to be a string",
            Self::UnsupportedProfile => "unsupported punarchi profile",
            Self::ExpectedContextObject => "expected punarchi context object",
            Self::UnsupportedRelation => "unsupported punarchi relation",
            Self::UnsupportedOrIncompatibleSubtype => {
                "unsupported or incompatible punarchi subtype"
            }
            Self::UnsupportedLexicalClass => "unsupported punarchi lexical class",
            Self::ExpectedPoeticBoolean => "expected poetic to be a boolean",
            Self::UnsupportedChapter => "unsupported punarchi chapter",
            Self::SutraOutOfRange => "punarchi sutra out of range",
        }
    }
}

impl fmt::Display for PunarchiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

impl std::error::Error for PunarchiError {}
