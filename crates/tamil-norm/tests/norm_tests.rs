#![forbid(unsafe_code)]

use tamil_norm::{normalize_nfc, normalize_nfd};

#[test]
fn test_canonical_nfc_nfd_equivalence() {
    let precomposed = "\u{0B95}\u{0BCA}";
    let decomposed: String = [0x0B95, 0x0BC6, 0x0BBE]
        .into_iter()
        .filter_map(char::from_u32)
        .collect();

    assert_eq!(normalize_nfc(&decomposed), precomposed);
    assert_eq!(normalize_nfd(precomposed), decomposed);
    assert_eq!(normalize_nfc(precomposed), precomposed);
    assert_eq!(normalize_nfd(&decomposed), decomposed);
}

#[test]
fn test_joiner_preservation() {
    let zwj = char::from_u32(0x200D).unwrap();
    let zwnj = char::from_u32(0x200C).unwrap();
    let with_zwj = format!("தமிழ்{zwj}நாடு");
    let with_zwnj = format!("தமிழ்{zwnj}நாடு");

    assert_eq!(normalize_nfc(&with_zwj), with_zwj);
    assert_eq!(normalize_nfd(&with_zwj), with_zwj);
    assert_eq!(normalize_nfc(&with_zwnj), with_zwnj);
    assert_eq!(normalize_nfd(&with_zwnj), with_zwnj);
}

#[test]
fn test_mixed_scripts_passthrough() {
    let mixed = "Tamil 123 தமிழ்! 🎉";
    assert_eq!(normalize_nfc(mixed), mixed);
    assert_eq!(normalize_nfd(mixed), mixed);
}

mod nfc_nfd_validation {
    use proptest::prelude::*;
    use tamil_norm::{
        fold_for_search, normalize_nfc, normalize_nfd, repair_tamil_text, FoldingProfile,
        RepairOptions,
    };

    fn scalars(codes: &[u32]) -> String {
        codes.iter().filter_map(|&c| char::from_u32(c)).collect()
    }

    const BASES: &[&str] = &[
        "\u{0b95}",
        "\u{0b99}",
        "\u{0b9a}",
        "\u{0b9e}",
        "\u{0b9f}",
        "\u{0ba3}",
        "\u{0ba4}",
        "\u{0ba8}",
        "\u{0baa}",
        "\u{0bae}",
        "\u{0baf}",
        "\u{0bb0}",
        "\u{0bb2}",
        "\u{0bb5}",
        "\u{0bb4}",
        "\u{0bb3}",
        "\u{0bb1}",
        "\u{0ba9}",
        "\u{0b9c}",
        "\u{0bb7}",
        "\u{0bb8}",
        "\u{0bb9}",
        "\u{0b95}\u{0bcd}\u{0bb7}",
    ];

    const SPLIT_VOWELS: &[(u32, [u32; 2])] = &[
        (0x0bca, [0x0bc6, 0x0bbe]),
        (0x0bcb, [0x0bc7, 0x0bbe]),
        (0x0bcc, [0x0bc6, 0x0bd7]),
    ];

    #[test]
    fn two_part_tamil_vowels_round_trip() {
        let au_nfd = scalars(&[0x0b92, 0x0bd7]);
        let au_nfc = scalars(&[0x0b94]);
        assert_eq!(normalize_nfc(&au_nfd), au_nfc);
        assert_eq!(normalize_nfd(&au_nfc), au_nfd);

        for base in BASES {
            for &(nfc_c, ref nfd_codes) in SPLIT_VOWELS {
                let nfc = format!("{base}{}", char::from_u32(nfc_c).unwrap());
                let nfd = format!("{base}{}", scalars(nfd_codes));
                assert_eq!(normalize_nfc(&nfd), nfc);
                assert_eq!(normalize_nfc(&nfc), nfc);
                assert_eq!(normalize_nfd(&nfc), nfd);
                assert_eq!(normalize_nfd(&nfd), nfd);
            }
        }
    }

    #[test]
    fn ccc_mark_reordering_in_nfc_and_nfd() {
        // Virama (CCC=9) followed by combining acute (CCC=230) must reorder when inverted
        let non_canonical = scalars(&[0x0b95, 0x0301, 0x0bcd]);
        let canonical = scalars(&[0x0b95, 0x0bcd, 0x0301]);
        assert_eq!(normalize_nfc(&non_canonical), canonical);
        assert_eq!(normalize_nfd(&non_canonical), canonical);

        // Combined acute (CCC=230) + dot below (CCC=220) + pulli (CCC=9)
        let mixed = scalars(&[0x0b95, 0x0301, 0x0323, 0x0bcd]);
        let ordered = scalars(&[0x0b95, 0x0bcd, 0x0323, 0x0301]);
        assert_eq!(normalize_nfd(&mixed), ordered);
    }

    #[test]
    fn format_control_and_joiner_barriers_preserved() {
        let with_zwnj = scalars(&[0x0bb4, 0x0bcd, 0x200c, 0x0b95]);
        let with_zwj = scalars(&[0x0b95, 0x0bcd, 0x0bb7, 0x200d]);
        let with_bom_shy = scalars(&[0xfeff, 0x0ba4, 0x00ad, 0x0bae, 0x0bbf, 0x0bb4, 0x0bcd]);

        assert_eq!(normalize_nfc(&with_zwnj), with_zwnj);
        assert_eq!(normalize_nfd(&with_zwnj), with_zwnj);
        assert_eq!(normalize_nfc(&with_zwj), with_zwj);
        assert_eq!(normalize_nfd(&with_zwj), with_zwj);
        assert_eq!(normalize_nfc(&with_bom_shy), with_bom_shy);
        assert_eq!(normalize_nfd(&with_bom_shy), with_bom_shy);

        // CCC=0 ZWJ barrier between split vowel parts prevents canonical composition
        let barrier = scalars(&[0x0b95, 0x0bc6, 0x200d, 0x0bbe]);
        assert_eq!(normalize_nfc(&barrier), barrier);
        assert_eq!(normalize_nfd(&barrier), barrier);
    }

    #[test]
    fn shri_distinction_and_malformed_sequences_unrepaired() {
        let shri_sa = "\u{0bb8}\u{0bcd}\u{0bb0}\u{0bc0}";
        let shri_sha = "\u{0bb6}\u{0bcd}\u{0bb0}\u{0bc0}";
        assert_eq!(normalize_nfc(shri_sa), shri_sa);
        assert_eq!(normalize_nfc(shri_sha), shri_sha);
        assert_ne!(normalize_nfc(shri_sa), normalize_nfc(shri_sha));
        assert_ne!(normalize_nfd(shri_sa), normalize_nfd(shri_sha));

        // Double vowel sequence from intake Entry 4848 must remain untouched
        let malformed = "\u{0ba4}\u{0bc1}\u{0bbe}";
        assert_eq!(normalize_nfc(malformed), malformed);
        assert_eq!(normalize_nfd(malformed), malformed);
    }

    #[test]
    fn empty_and_mixed_script_invariance() {
        assert_eq!(normalize_nfc(""), "");
        assert_eq!(normalize_nfd(""), "");
        assert_eq!(normalize_nfc("   "), "   ");
        let mixed_nfd = format!("Tamil {} 2026!", scalars(&[0x0b95, 0x0bc6, 0x0bbe]));
        let mixed_nfc = "Tamil \u{0b95}\u{0bca} 2026!";
        assert_eq!(normalize_nfc(&mixed_nfd), mixed_nfc);
        assert_eq!(normalize_nfd(mixed_nfc), mixed_nfd);
    }

    fn tamil_normalization_string() -> impl Strategy<Value = String> {
        let token = prop_oneof![
            Just(0x0b95u32),
            Just(0x0b9a),
            Just(0x0ba4),
            Just(0x0baa),
            Just(0x0bb4),
            Just(0x0bb8),
            Just(0x0bb6),
            Just(0x0bb0),
            Just(0x0bb7),
            Just(0x0b92),
            Just(0x0b94),
            Just(0x0bcd),
            Just(0x0bc6),
            Just(0x0bc7),
            Just(0x0bbe),
            Just(0x0bd7),
            Just(0x0bca),
            Just(0x0bcb),
            Just(0x0bcc),
            Just(0x0bc0),
            Just(0x0301),
            Just(0x200c),
            Just(0x200d),
            Just(0xfeff),
            Just(0x00ad),
            Just(0x0061),
            Just(0x0020),
        ];
        prop::collection::vec(token, 0..16).prop_map(|codes| scalars(&codes))
    }

    fn count_format_controls(s: &str) -> [usize; 4] {
        let zwnj = char::from_u32(0x200c).unwrap();
        let zwj = char::from_u32(0x200d).unwrap();
        let bom = char::from_u32(0xfeff).unwrap();
        let shy = char::from_u32(0x00ad).unwrap();
        [
            s.matches(zwnj).count(),
            s.matches(zwj).count(),
            s.matches(bom).count(),
            s.matches(shy).count(),
        ]
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn prop_nfc_nfd_canonical_invariants(input in tamil_normalization_string()) {
            let nfc = normalize_nfc(&input);
            let nfd = normalize_nfd(&input);

            prop_assert_eq!(&normalize_nfc(&nfc), &nfc);
            prop_assert_eq!(&normalize_nfd(&nfd), &nfd);
            prop_assert_eq!(&normalize_nfc(&nfd), &nfc);
            prop_assert_eq!(&normalize_nfd(&nfc), &nfd);
            prop_assert_eq!(count_format_controls(&nfc), count_format_controls(&input));
            prop_assert_eq!(count_format_controls(&nfd), count_format_controls(&input));

            for profile in [
                FoldingProfile::Mayangoli,
                FoldingProfile::Grantha,
                FoldingProfile::Comprehensive,
            ] {
                prop_assert_eq!(
                    fold_for_search(&nfc, profile),
                    fold_for_search(&nfd, profile)
                );
            }

            let rep_nfc = repair_tamil_text(&nfc, &RepairOptions::default());
            let rep_nfd = repair_tamil_text(&nfd, &RepairOptions::default());
            prop_assert_eq!(rep_nfc.text, rep_nfd.text);
            prop_assert_eq!(rep_nfc.diagnostics.total_repairs, rep_nfd.diagnostics.total_repairs);
        }
    }
}
