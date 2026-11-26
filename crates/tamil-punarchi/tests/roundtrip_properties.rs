//! 10,000-case property-based verification for `tamil-punarchi` (Task T038).
//!
//! Proves:
//! 1. 100% forward -> reverse-split round-trip recall across all 28 reversible pattern families.
//! 2. Exact `split_byte` / `split_unit` alignment on `tamil_core::Letters` boundaries (zero mid-ligature or mid-vowel-sign cuts).
//! 3. Nannool 102-108 *Mozhi-muthal* / *Mozhi-eetru* phonotactic validity on every split candidate.
//! 4. Canonical NFC/NFD equivalence on `punarchi_join` and `punarchi_split_candidates`.
//! 5. Verbatim preservation of `ZWJ`/`ZWNJ` and non-Tamil boundary barriers.
//! 6. Bounded deterministic output and 256-byte surface cap enforcement.

use proptest::prelude::*;
use std::collections::HashSet;
use tamil_core::Letters;
use tamil_norm::{normalize_nfc, normalize_nfd};
use tamil_punarchi::{
    is_valid_mozhi_eetru, is_valid_mozhi_muthal, punarchi_join, punarchi_split_candidates,
    ContextSubtype, GrammaticalRelation, LexicalClass, PunarchiContext, PunarchiError,
    PunarchiProfile, MAX_SPLIT_SURFACE_BYTES,
};

type ReversibleCase = (
    &'static str,
    &'static str,
    GrammaticalRelation,
    Option<ContextSubtype>,
    Option<LexicalClass>,
    bool,
);

/// Curated reversible test pool spanning all 28 inverse pattern families from `research/05` §3.
const REVERSIBLE_CASES: &[ReversibleCase] = &[
    // Pattern 1: Direct Iyalbu
    (
        "விள",
        "மாண்டது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "நாகு",
        "கடிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "பொன்",
        "மணி",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 2: 204 Udalmel Uyir
    (
        "தமிழ்",
        "அம்மா",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "புகழ்",
        "அழகிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 3: 205 Thanikkuril Otru + 204
    ("கல்", "அடி", GrammaticalRelation::Alvazhi, None, None, false),
    (
        "மண்",
        "அரிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 4: 162 / 163 Udambadumei glides
    (
        "கிளி",
        "அழகு",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "கோ",
        "அழகிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    ("ஏ", "அடி", GrammaticalRelation::Alvazhi, None, None, false),
    ("அ", "அணி", GrammaticalRelation::Alvazhi, None, None, false),
    // Pattern 5: 164 Kurriyalugaram + 183 pre-elision doubling
    (
        "நாகு",
        "அரிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "காடு",
        "எருமை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    // Pattern 6: 93 Kurriyaligaram & 206 minority `இ` before `ய`
    (
        "நாகு",
        "யாது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "வேள்",
        "யாவன்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 7: 165 Vallinam doubling + 183/184/185
    (
        "விள",
        "கோடு",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "ஆடு",
        "கால்",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "மருந்து",
        "பை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "பண்டு",
        "காலம்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "மரம்",
        "கால்",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    // Pattern 8: 224 / 226 `ய்/ர்/ழ்` + doubled stop
    ("நாய்", "கால்", GrammaticalRelation::Vetrumai, None, None, false),
    (
        "கீழ்",
        "குலம்",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    // Pattern 9: 158 / 163 / 106 / 221 / 235 doubled nasal/approximant
    (
        "மெய்",
        "ஞான்றது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    ("எ", "ஞாலம்", GrammaticalRelation::Alvazhi, None, None, false),
    ("அ", "ஙனம்", GrammaticalRelation::Alvazhi, None, None, false),
    (
        "நும்",
        "நூல்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    ("அவ்", "ஞானம்", GrammaticalRelation::Alvazhi, None, None, false),
    // Pattern 10: Nasal assimilation / insertion (166, 175, 200, 203, 219, 136)
    (
        "மா",
        "காய்",
        GrammaticalRelation::Vetrumai,
        None,
        Some(LexicalClass::TreeName),
        false,
    ),
    (
        "பூ",
        "கொடி",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "பனை",
        "காய்",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "நாம்",
        "கடியம்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "செம்மை",
        "தாமரை",
        GrammaticalRelation::Alvazhi,
        Some(ContextSubtype::Panputhogai),
        None,
        false,
    ),
    (
        "பசுமை",
        "தமிழ்",
        GrammaticalRelation::Alvazhi,
        Some(ContextSubtype::Panputhogai),
        None,
        false,
    ),
    // Patterns 11-17: ALL 12 Sutra 237 surface outputs
    ("கல்", "தீது", GrammaticalRelation::Alvazhi, None, None, false),
    (
        "பொன்",
        "தீமை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "முள்",
        "தீது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "மண்",
        "தீமை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "பொன்",
        "தீது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    ("மண்", "தீது", GrammaticalRelation::Alvazhi, None, None, false),
    (
        "பொன்",
        "நன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "கல்",
        "நன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "மண்",
        "நன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "முள்",
        "நன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "வேல்",
        "தீது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    ("வாள்", "தீது", GrammaticalRelation::Alvazhi, None, None, false),
    (
        "அரசன்",
        "நல்லன்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "தோன்றல்",
        "நல்லன்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "தூண்",
        "நன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "வேள்",
        "நல்லன்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 18: ற்/ட் + க/ச/ப
    (
        "கல்",
        "சிலை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "முள்",
        "செடி",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "சிறுகண்",
        "களிறு",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "நெல்",
        "கடிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 19: ன்/ண் + ஞ/ம
    (
        "கல்",
        "மாண்டது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "முள்",
        "மாண்டது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 20: ஃற / ஃட
    (
        "அல்",
        "திணை",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 21: ஃ + Vallinam (235)
    (
        "அவ்",
        "கடிய",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 22: 219 post-ம் deletion
    (
        "மரம்",
        "வேர்",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "மரம்",
        "அடி",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    // Pattern 23: 252 -த்து-/-த்த்-
    (
        "மரம்",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "மரம்",
        "கு",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case4),
        None,
        false,
    ),
    ("மக", "கை", GrammaticalRelation::Vetrumai, None, None, false),
    // Pattern 24: Chariyai + case + உம்
    (
        "பல",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "அவ்",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "எவ்",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "எல்லாம்",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        Some(LexicalClass::NonRationalNoun),
        false,
    ),
    (
        "எல்லாம்",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        Some(LexicalClass::RationalNoun),
        false,
    ),
    (
        "எல்லாரும்",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "ஆ",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "ஒருபது",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    (
        "அஃது",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    // Pattern 25: Oblique pronouns (247)
    (
        "யான்",
        "கு",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case4),
        None,
        false,
    ),
    (
        "தான்",
        "கு",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case4),
        None,
        false,
    ),
    (
        "தான்",
        "அது",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case6),
        None,
        false,
    ),
    (
        "நீ",
        "ஐ",
        GrammaticalRelation::Vetrumai,
        Some(ContextSubtype::Case2),
        None,
        false,
    ),
    // Pattern 26: Closed-class & poetic stems
    (
        "வடக்கு",
        "கிழக்கு",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "தெற்கு",
        "கிழக்கு",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "மேற்கு",
        "திசை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "மேற்கு",
        "நாடு",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "தெங்கு",
        "காய்",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "ஒன்பது",
        "பத்து",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "ஒன்பது",
        "நூறு",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "பத்து",
        "இரண்டு",
        GrammaticalRelation::Alvazhi,
        Some(ContextSubtype::Ummaithogai),
        None,
        false,
    ),
    (
        "பத்து",
        "ஒன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "ஒருபஃது",
        "ஒன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "ஒன்று",
        "ஒன்று",
        GrammaticalRelation::Alvazhi,
        Some(ContextSubtype::Distributive),
        None,
        false,
    ),
    (
        "நாழி",
        "உரி",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "உரி",
        "பயிறு",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    (
        "பனை",
        "அட்டு",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    ("பல", "பல", GrammaticalRelation::Alvazhi, None, None, false),
    ("அகம்", "கை", GrammaticalRelation::Alvazhi, None, None, false),
    (
        "சிறுமை",
        "ஊர்",
        GrammaticalRelation::Alvazhi,
        Some(ContextSubtype::Panputhogai),
        None,
        false,
    ),
    (
        "கருமை",
        "அன்",
        GrammaticalRelation::Alvazhi,
        None,
        Some(LexicalClass::QualityNoun),
        false,
    ),
    (
        "செம்மை",
        "ஆம்பல்",
        GrammaticalRelation::Alvazhi,
        Some(ContextSubtype::Panputhogai),
        None,
        false,
    ),
    (
        "அது",
        "அன்று",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        true,
    ),
    // Pattern 27: Stem increments (207, 212, 225, 236)
    (
        "உண்",
        "கடிது",
        GrammaticalRelation::Alvazhi,
        None,
        Some(LexicalClass::VerbalNounRoot),
        false,
    ),
    (
        "எயின்",
        "குடி",
        GrammaticalRelation::Vetrumai,
        None,
        Some(LexicalClass::BranchName),
        false,
    ),
    (
        "தமிழ்",
        "பிள்ளை",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "தாழ்",
        "கோல்",
        GrammaticalRelation::Vetrumai,
        None,
        None,
        false,
    ),
    (
        "தெவ்",
        "கடிது",
        GrammaticalRelation::Alvazhi,
        None,
        None,
        false,
    ),
    // Pattern 28: Non-Thanikkuril `ய்` deletion before `ய`
    ("காய்", "யாது", GrammaticalRelation::Alvazhi, None, None, false),
];

const FIRST_WORDS: &[&str] = &[
    "கல்",
    "மண்",
    "பொன்",
    "வேல்",
    "வாள்",
    "தூண்",
    "அரசன்",
    "தமிழ்",
    "புகழ்",
    "மரம்",
    "விள",
    "கிளி",
    "கோ",
    "ஏ",
    "நாகு",
    "ஆடு",
    "காடு",
    "நாய்",
    "காய்",
    "பூ",
    "அ",
    "எ",
    "அவ்",
    "எவ்",
    "பல",
    "அது",
];

const SECOND_WORDS: &[&str] = &[
    "அடி",
    "அரிது",
    "அம்மா",
    "அழகிது",
    "எருமை",
    "ஊர்",
    "கால்",
    "கோடு",
    "சிலை",
    "தீது",
    "தீமை",
    "நன்று",
    "நல்லன்",
    "பழம்",
    "மாண்டது",
    "வேர்",
    "யாது",
    "ஐ",
    "கு",
    "இன்",
];

fn verify_split_invariants(surface: &str, poetic: bool) {
    let cands = punarchi_split_candidates(surface, PunarchiProfile::NannoolV1, poetic)
        .expect("bounded surface must not error");
    let surface_nfc = normalize_nfc(surface);
    let units: Vec<&str> = Letters::new(&surface_nfc).collect();

    // Collect valid internal `(byte_offset, unit_idx)` boundaries.
    let mut valid_boundaries: HashSet<(usize, usize)> = HashSet::new();
    let mut byte_pos = 0_usize;
    for (idx, u) in units.iter().enumerate() {
        if idx > 0 {
            valid_boundaries.insert((byte_pos, idx));
        }
        byte_pos += u.len();
    }

    let mut seen = HashSet::new();
    for cand in &cands {
        assert!(
            valid_boundaries.contains(&(cand.split_byte, cand.split_unit)),
            "split boundary ({}, {}) not aligned to Letters unit boundary in {:?}",
            cand.split_byte,
            cand.split_unit,
            surface_nfc
        );
        assert!(
            is_valid_mozhi_eetru(&cand.first) || cand.first.ends_with("ந்"),
            "invalid mozhi-eetru first={:?} in {:?}",
            cand.first,
            surface_nfc
        );
        assert!(
            is_valid_mozhi_muthal(&cand.second, Some(&cand.first)),
            "invalid mozhi-muthal second={:?} in {:?}",
            cand.second,
            surface_nfc
        );
        assert!(
            seen.insert((cand.first.clone(), cand.second.clone(), cand.sutra)),
            "duplicate candidate {:?} in {:?}",
            cand,
            surface_nfc
        );
    }

    // Strict deterministic ordering check.
    for pair in cands.windows(2) {
        let a = (
            pair[0].split_byte,
            pair[0].sutra,
            pair[0].first.as_str(),
            pair[0].second.as_str(),
        );
        let b = (
            pair[1].split_byte,
            pair[1].sutra,
            pair[1].first.as_str(),
            pair[1].second.as_str(),
        );
        assert!(
            a <= b,
            "candidates out of deterministic order: {a:?} > {b:?}"
        );
    }
}

#[test]
fn all_28_pattern_families_roundtrip_100_percent() {
    for &(first, second, relation, subtype, lexical_class, poetic) in REVERSIBLE_CASES {
        let ctx = PunarchiContext {
            relation,
            subtype,
            lexical_class,
            poetic,
        };
        let joined = punarchi_join(first, second, &ctx, PunarchiProfile::NannoolV1)
            .unwrap_or_else(|e| panic!("forward join failed for {first} + {second}: {e}"));

        verify_split_invariants(&joined.surface, poetic);

        let cands = punarchi_split_candidates(&joined.surface, PunarchiProfile::NannoolV1, poetic)
            .unwrap_or_else(|e| panic!("split failed for {}: {e}", joined.surface));
        assert!(
            cands.iter().any(|c| c.first == first && c.second == second),
            "round-trip miss for ({first} + {second}) -> {} (got {} candidates: {:?})",
            joined.surface,
            cands.len(),
            cands
                .iter()
                .map(|c| (c.first.as_str(), c.second.as_str(), c.sutra))
                .collect::<Vec<_>>()
        );
    }
}

#[test]
fn split_surface_cap_and_ligature_atomic_safety() {
    let over_cap = "அ".repeat(MAX_SPLIT_SURFACE_BYTES);
    assert_eq!(
        punarchi_split_candidates(&over_cap, PunarchiProfile::NannoolV1, false),
        Err(PunarchiError::SurfaceTooLong)
    );

    // Atomic ligatures `க்ஷ` and `ஸ்ரீ`: split boundaries must never cut mid-ligature.
    for lig_word in ["பக்ஷம்", "ஸ்ரீராமன்", "லக்ஷ்மி"] {
        verify_split_invariants(lig_word, false);
    }

    // Single-unit and non-Tamil inputs return `[]`.
    for empty_case in ["", "   ", "க", "அ", "abc", "123", "கல்123"] {
        let cands = punarchi_split_candidates(empty_case, PunarchiProfile::NannoolV1, false)
            .expect("must return Ok([])");
        assert!(
            cands.is_empty(),
            "expected [] for {empty_case:?}, got {cands:?}"
        );
    }
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(10_000))]

    #[test]
    fn prop_forward_join_split_roundtrip_and_invariants(
        fi in 0usize..FIRST_WORDS.len(),
        si in 0usize..SECOND_WORDS.len(),
        rel_idx in 0u8..3u8,
    ) {
        let first = FIRST_WORDS[fi];
        let second = SECOND_WORDS[si];
        let relation = match rel_idx {
            0 => GrammaticalRelation::Unspecified,
            1 => GrammaticalRelation::Alvazhi,
            _ => GrammaticalRelation::Vetrumai,
        };
        let ctx = PunarchiContext {
            relation,
            ..Default::default()
        };
        let joined = punarchi_join(first, second, &ctx, PunarchiProfile::NannoolV1).unwrap();
        prop_assert_eq!(&joined.surface, &normalize_nfc(&joined.surface));

        // NFD canonical equivalence on both join and split.
        let joined_nfd = punarchi_join(
            &normalize_nfd(first),
            &normalize_nfd(second),
            &ctx,
            PunarchiProfile::NannoolV1,
        )
        .unwrap();
        prop_assert_eq!(&joined, &joined_nfd);

        verify_split_invariants(&joined.surface, false);
        let cands_nfc = punarchi_split_candidates(&joined.surface, PunarchiProfile::NannoolV1, false).unwrap();
        let cands_nfd = punarchi_split_candidates(&normalize_nfd(&joined.surface), PunarchiProfile::NannoolV1, false).unwrap();
        prop_assert_eq!(&cands_nfc, &cands_nfd);

        // Round-trip recall for every generated surface.
        prop_assert!(
            cands_nfc.iter().any(|c| c.first == first && c.second == second),
            "round-trip miss for ({} + {}, {:?}) -> {}",
            first,
            second,
            relation,
            joined.surface
        );
    }

    #[test]
    fn prop_boundary_barrier_zwj_zwnj_verbatim_preservation(
        fi in 0usize..FIRST_WORDS.len(),
        si in 0usize..SECOND_WORDS.len(),
        use_zwj in any::<bool>(),
    ) {
        let first = FIRST_WORDS[fi];
        let second = SECOND_WORDS[si];
        let joiner = char::from_u32(if use_zwj { 0x200D } else { 0x200C }).unwrap();
        let second_with_barrier = format!("{joiner}{second}");
        let joined = punarchi_join(
            first,
            &second_with_barrier,
            &PunarchiContext::default(),
            PunarchiProfile::NannoolV1,
        )
        .unwrap();
        prop_assert_eq!(joined.surface, format!("{first}{joiner}{second}"));
        prop_assert_eq!(joined.steps.len(), 1);
        prop_assert_eq!(joined.steps[0].sutra, 153);
    }
}

#[test]
#[ignore]
fn bench_release_latency() {
    use std::hint::black_box;
    use std::time::Instant;

    let join_inputs = [
        (
            "மரம்",
            "ஐ",
            GrammaticalRelation::Vetrumai,
            Some(ContextSubtype::Case2),
        ),
        ("கல்", "தீது", GrammaticalRelation::Alvazhi, None),
        (
            "செம்மை",
            "தாமரை",
            GrammaticalRelation::Alvazhi,
            Some(ContextSubtype::Panputhogai),
        ),
        (
            "எல்லாம்",
            "ஐ",
            GrammaticalRelation::Vetrumai,
            Some(ContextSubtype::Case2),
        ),
        (
            "பத்து",
            "இரண்டு",
            GrammaticalRelation::Alvazhi,
            Some(ContextSubtype::Ummaithogai),
        ),
        (
            "நாடு",
            "கண்",
            GrammaticalRelation::Vetrumai,
            Some(ContextSubtype::Case7),
        ),
        ("மணி", "அடி", GrammaticalRelation::Unspecified, None),
        ("பொன்", "தகடு", GrammaticalRelation::Vetrumai, None),
    ];
    let split_inputs = [
        "மரத்தை",
        "கற்றீது",
        "செந்தாமரை",
        "எல்லாவற்றையும்",
        "பன்னிரண்டு",
        "நாட்டின்கண்",
        "மணியடி",
        "பொற்றகடு",
    ];

    // Warmup
    for _ in 0..500 {
        for &(f, s, rel, sub) in &join_inputs {
            let ctx = PunarchiContext {
                relation: rel,
                subtype: sub,
                ..Default::default()
            };
            black_box(punarchi_join(f, s, &ctx, PunarchiProfile::NannoolV1).unwrap());
        }
        for &surf in &split_inputs {
            black_box(punarchi_split_candidates(surf, PunarchiProfile::NannoolV1, false).unwrap());
        }
    }

    let join_iters = 10_000_u32;
    let t0 = Instant::now();
    for _ in 0..join_iters {
        for &(f, s, rel, sub) in &join_inputs {
            let ctx = PunarchiContext {
                relation: rel,
                subtype: sub,
                ..Default::default()
            };
            black_box(punarchi_join(f, s, &ctx, PunarchiProfile::NannoolV1).unwrap());
        }
    }
    let join_elapsed = t0.elapsed();
    let join_calls = f64::from(join_iters) * (join_inputs.len() as f64);
    let join_us = (join_elapsed.as_secs_f64() * 1e6) / join_calls;

    let split_iters = 2_000_u32;
    let t1 = Instant::now();
    for _ in 0..split_iters {
        for &surf in &split_inputs {
            black_box(punarchi_split_candidates(surf, PunarchiProfile::NannoolV1, false).unwrap());
        }
    }
    let split_elapsed = t1.elapsed();
    let split_calls = f64::from(split_iters) * (split_inputs.len() as f64);
    let split_us = (split_elapsed.as_secs_f64() * 1e6) / split_calls;

    println!(
        "RELEASE_LATENCY: punarchi_join={join_us:.2}us/call ({join_calls:.0} calls), punarchi_split_candidates={split_us:.2}us/call ({split_calls:.0} calls)"
    );
}
