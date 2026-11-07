use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use tamil_hyphen::dic::{generate_patterns, DicExportOptions};
use tamil_hyphen::types::{DicHeader, HyphenDictionary, LiangPattern};
use tamil_hyphen::verify_dic::LiangEvaluator;

fn load_smc_legacy_dictionary() -> HyphenDictionary {
    let path = Path::new("tests/fixtures/smc_2018_hyph_ta_IN.dic");
    let file = match File::open(path) {
        Ok(f) => f,
        Err(_) => File::open("crates/tamil-hyphen/tests/fixtures/smc_2018_hyph_ta_IN.dic")
            .expect("Could not locate smc_2018_hyph_ta_IN.dic fixture"),
    };

    let reader = BufReader::new(file);
    let mut patterns = Vec::new();
    let mut left_min = 1; // SMC legacy did not specify min margins, defaults to 1
    let mut right_min = 1;

    for line in reader.lines() {
        let line = line.expect("Failed to read line");
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('%') {
            continue;
        }
        if trimmed == "UTF-8" {
            continue;
        }
        if let Some(val) = trimmed.strip_prefix("LEFTHYPHENMIN ") {
            left_min = val.parse().unwrap_or(1);
            continue;
        }
        if let Some(val) = trimmed.strip_prefix("RIGHTHYPHENMIN ") {
            right_min = val.parse().unwrap_or(1);
            continue;
        }
        if let Some(p) = LiangPattern::parse(trimmed) {
            patterns.push(p);
        }
    }

    HyphenDictionary {
        header: DicHeader {
            encoding: "UTF-8".to_string(),
            left_hyphen_min: left_min,
            right_hyphen_min: right_min,
            license_notice: "Legacy SMC 2018".to_string(),
        },
        patterns,
    }
}

#[test]
fn test_comparative_benchmark_legacy_smc_vs_tamil_toolkit() {
    let smc_dict = load_smc_legacy_dictionary();
    let smc_evaluator = LiangEvaluator::new(&smc_dict);

    let toolkit_options = DicExportOptions {
        left_hyphen_min: 2,
        right_hyphen_min: 2,
    };
    let toolkit_dict = generate_patterns(&toolkit_options);
    let toolkit_evaluator = LiangEvaluator::new(&toolkit_dict);

    // 1. Defect Category: Single-Letter Orphan Prefix Splits in Legacy SMC
    // SMC patterns lack LEFTHYPHENMIN 2 and declare 1C / 1Uyir1 rules, creating illegal 1-character splits
    let single_letter_words = [
        "தமிழ்நாடு",
        "வணக்கம்",
        "அறிவியல்",
        "இலக்கியம்",
        "தமிழ்",
        "மரம்",
        "அரசாங்கம்",
        "கணினி",
    ];

    let mut smc_single_letter_failures = 0;
    let mut toolkit_single_letter_failures = 0;

    for word in &single_letter_words {
        let (smc_res, _) = smc_evaluator.hyphenate_word(word, "-");
        let (toolkit_res, _) = toolkit_evaluator.hyphenate_word(word, "-");

        let smc_has_1char_prefix =
            smc_res.chars().count() > 2 && smc_res.chars().nth(1) == Some('-');
        let toolkit_has_1char_prefix =
            toolkit_res.chars().count() > 2 && toolkit_res.chars().nth(1) == Some('-');

        if smc_has_1char_prefix {
            smc_single_letter_failures += 1;
        }
        if toolkit_has_1char_prefix {
            toolkit_single_letter_failures += 1;
        }

        println!("Word '{word}': legacy SMC='{smc_res}' | tamil-toolkit='{toolkit_res}'");
    }

    assert_eq!(
        smc_single_letter_failures,
        single_letter_words.len(),
        "Legacy SMC should have exhibited 1-character breaks across all sample words"
    );
    assert_eq!(
        toolkit_single_letter_failures, 0,
        "tamil-toolkit must have 0 1-character prefix breaks"
    );

    // 2. Defect Category: Explicit Grantha Ligature Protection in tamil-toolkit
    // tamil-toolkit explicitly encodes 2க்2ஷ2 and 2ஸ்ரீ2 rules into the dictionary
    let grantha_words = ["தக்ஷிணம்", "லக்ஷ்மி", "மோக்ஷம்", "அக்ஷரம்", "ஸ்ரீரங்கம்"];
    for word in &grantha_words {
        let (toolkit_res, toolkit_segs) = toolkit_evaluator.hyphenate_word(word, "-");

        assert!(
            !toolkit_res.contains("க்-ஷ"),
            "tamil-toolkit severed Grantha ligature in '{}': got '{}'",
            word,
            toolkit_res
        );

        for seg in &toolkit_segs {
            assert!(
                !seg.ends_with("க்") || !seg.starts_with('ஷ'),
                "Found severed ligature in segment '{}' of '{}'",
                seg,
                word
            );
        }
    }

    // 3. Defect Category: Coda Cluster & Virama Integrity
    let cluster_words = ["துர்ப்பிரயோகம்", "பல்கலைக்கழகம்", "செம்மொழி"];
    for word in &cluster_words {
        let (toolkit_res, toolkit_segs) = toolkit_evaluator.hyphenate_word(word, "-");

        for seg in &toolkit_segs {
            assert!(
                !seg.starts_with('\u{0BCD}'),
                "Segment '{}' starts with naked virama in '{}'",
                seg,
                word
            );
            // Verify no segment starts with an illegal pure consonant
            let chars: Vec<char> = seg.chars().collect();
            if chars.len() >= 2 && chars[1] == '\u{0BCD}' {
                let is_sri = (chars[0] == '\u{0BB8}' || chars[0] == '\u{0BB6}')
                    && chars.len() >= 4
                    && chars[2] == '\u{0BB0}'
                    && chars[3] == '\u{0BC0}';
                let is_ksha = chars[0] == '\u{0B95}'
                    && chars.len() >= 3
                    && chars[2] == '\u{0BB7}'
                    && (chars.len() == 3 || chars[3] != '\u{0BCD}');

                assert!(
                    is_sri || is_ksha,
                    "Segment '{}' illegally begins with a pure consonant in word '{}'! Full: '{}'",
                    seg,
                    word,
                    toolkit_res
                );
            }
        }
    }

    println!("Comparative benchmark passed: 100% resolution of legacy SMC 1-letter breaks and robust Grantha/Coda protection!");
}
