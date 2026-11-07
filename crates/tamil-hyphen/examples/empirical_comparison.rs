use std::collections::HashSet;
use std::fs::File;
use std::io::{BufRead, BufReader};
use tamil_core::Letters;
use tamil_hyphen::syllable::{classify_letter, is_syllable_nucleus, LetterClass};
use tamil_norm::normalize_nfc;

#[derive(Debug, Clone)]
pub struct WordAnalysis {
    pub word: String,
    pub letters: Vec<String>,
    pub letter_classes: Vec<LetterClass>,
    pub letter_count: usize,
    pub syllable_count: usize,
    pub scalar_count: usize,
}

pub fn analyze_word(word: &str) -> WordAnalysis {
    let nfc = normalize_nfc(word);
    let letters: Vec<String> = Letters::new(&nfc).map(|s| s.to_string()).collect();
    let letter_classes: Vec<LetterClass> = letters.iter().map(|l| classify_letter(l)).collect();
    let syllable_count = letter_classes
        .iter()
        .filter(|&&c| is_syllable_nucleus(c))
        .count();
    let scalar_count = nfc.chars().count();
    let letter_count = letters.len();

    WordAnalysis {
        word: nfc,
        letters,
        letter_classes,
        letter_count,
        syllable_count,
        scalar_count,
    }
}

#[derive(Debug, Clone)]
pub struct BreakOpportunity {
    pub letter_index: usize,
    pub left_segment: String,
    pub right_segment: String,
    pub left_letters: usize,
    pub right_letters: usize,
    pub left_syllables: usize,
    pub right_syllables: usize,
    pub left_scalars: usize,
    pub right_scalars: usize,
    pub left_ends_with_mei: bool,
    pub right_starts_with_uyirmei_or_uyir: bool,
}

pub fn find_all_phonotactic_breaks(analysis: &WordAnalysis) -> Vec<BreakOpportunity> {
    let mut breaks = Vec::new();
    let total_letters = analysis.letter_count;
    if total_letters < 2 {
        return breaks;
    }

    let mut has_nucleus_before = vec![false; total_letters];
    let mut running_nucleus = false;
    for (i, &class) in analysis.letter_classes.iter().enumerate() {
        if is_syllable_nucleus(class) {
            running_nucleus = true;
        }
        has_nucleus_before[i] = running_nucleus;
    }

    let mut has_nucleus_after = vec![false; total_letters];
    running_nucleus = false;
    for (i, &class) in analysis.letter_classes.iter().enumerate().rev() {
        if is_syllable_nucleus(class) {
            running_nucleus = true;
        }
        has_nucleus_after[i] = running_nucleus;
    }

    for i in 0..(total_letters - 1) {
        if !has_nucleus_before[i] || !has_nucleus_after[i + 1] {
            continue;
        }

        let curr_class = analysis.letter_classes[i];
        let next_class = analysis.letter_classes[i + 1];

        if next_class == LetterClass::Mei || next_class == LetterClass::Aytham {
            continue;
        }
        if !is_syllable_nucleus(next_class) {
            continue;
        }

        let left_letters = i + 1;
        let right_letters = total_letters - left_letters;

        let left_syllables = analysis.letter_classes[..=i]
            .iter()
            .filter(|&&c| is_syllable_nucleus(c))
            .count();
        let right_syllables = analysis.letter_classes[(i + 1)..]
            .iter()
            .filter(|&&c| is_syllable_nucleus(c))
            .count();

        let left_seg: String = analysis.letters[..=i].concat();
        let right_seg: String = analysis.letters[(i + 1)..].concat();

        let left_scalars = left_seg.chars().count();
        let right_scalars = right_seg.chars().count();

        breaks.push(BreakOpportunity {
            letter_index: left_letters,
            left_segment: left_seg,
            right_segment: right_seg,
            left_letters,
            right_letters,
            left_syllables,
            right_syllables,
            left_scalars,
            right_scalars,
            left_ends_with_mei: curr_class == LetterClass::Mei,
            right_starts_with_uyirmei_or_uyir: is_syllable_nucleus(next_class),
        });
    }

    breaks
}

pub fn get_hyphenated(
    analysis: &WordAnalysis,
    breaks: &[BreakOpportunity],
    l_min: usize,
    r_min: usize,
    unit: &str,
) -> String {
    let valid_indices: Vec<usize> = breaks
        .iter()
        .filter(|b| match unit {
            "letter" => b.left_letters >= l_min && b.right_letters >= r_min,
            "syllable" => b.left_syllables >= l_min && b.right_syllables >= r_min,
            "scalar" => b.left_scalars >= l_min && b.right_scalars >= r_min,
            _ => false,
        })
        .map(|b| b.letter_index)
        .collect();

    if valid_indices.is_empty() {
        return "[UNBROKEN]".to_string();
    }

    let mut out = Vec::new();
    let mut last = 0;
    for &idx in &valid_indices {
        out.push(analysis.letters[last..idx].concat());
        last = idx;
    }
    out.push(analysis.letters[last..].concat());
    out.join("-")
}

fn main() {
    let golden_path = "tests/golden/hyphen_syllable.jsonl";
    let f = File::open(golden_path).expect("open golden file");
    let reader = BufReader::new(f);
    let mut golden_words = Vec::new();
    for line in reader.lines() {
        let l = line.unwrap();
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(&l) {
            if v["op"] == "hyphenate_word" {
                if let Some(w) = v["input"]["word"].as_str() {
                    golden_words.push((v["id"].as_str().unwrap_or("").to_string(), w.to_string()));
                }
            }
        }
    }

    let word_doc_raw = "முடிவுகள் பாதுகாப்பு சேவை மதிப்பு எதிர்காலம் டிஜிட்டல் நேரம் உலகம் அமைப்பு கலாச்சாரம் அறிவியல் மாற்றம் சமூகம் வணிகம் தரவு அமைப்பு குழு உலகம் எதிர்காலம் அறிவு திட்டம் அமைப்பு குடும்பம் திறன் தரம் செயல்முறை நம்பிக்கை மதிப்பு ஆரோக்கியம் தொடர்பு மொழி அறிவு கலாச்சாரம் குழு முடிவு தொழில்நுட்பம் திட்டம் படைப்பாற்றல் தொழில் அறிவு தீர்வு கல்வி வரலாறு தலைமை உற்பத்தி செயல்முறை கல்வி வளர்ச்சி கண்டுபிடிப்பு வணிகம் தாக்கம்";
    let word_doc_words: Vec<String> = word_doc_raw.split_whitespace().map(String::from).collect();

    let mut seen = HashSet::new();
    let mut unique_word_doc: Vec<String> = Vec::new();
    for w in &word_doc_words {
        if seen.insert(w.clone()) {
            unique_word_doc.push(w.clone());
        }
    }

    // Write a comprehensive JSON report with all raw data for inspection
    let _report = serde_json::json!({
        "golden_count": golden_words.len(),
        "word_doc_tokens": word_doc_words.len(),
        "word_doc_unique": unique_word_doc.len(),
    });

    // Let's generate a full markdown report file
    let mut md = String::new();
    md.push_str("# Empirical Comparison Data Dump\n\n");

    // 1. Dataset stats
    let configs = vec![
        ("Letter 2/2", 2, 2, "letter"),
        ("Letter 2/3", 2, 3, "letter"),
        ("Letter 3/2", 3, 2, "letter"),
        ("Letter 3/3", 3, 3, "letter"),
        ("Syllable 2/2", 2, 2, "syllable"),
        ("Syllable 2/3", 2, 3, "syllable"),
        ("Syllable 3/2", 3, 2, "syllable"),
        ("Syllable 3/3", 3, 3, "syllable"),
        ("Scalar 2/2 (TeX/Hunspell)", 2, 2, "scalar"),
        ("Scalar 3/3 (TeX/Hunspell)", 3, 3, "scalar"),
        ("Scalar 4/4 (TeX/Hunspell)", 4, 4, "scalar"),
    ];

    md.push_str("## 1. Summary Statistics Across All Configurations\n\n");
    md.push_str("| Configuration | Golden (122 words) Hyphenated | Golden Total Breaks | Word Doc (38 unique) Hyphenated | Word Doc Total Breaks |\n");
    md.push_str("|---|---|---|---|---|\n");

    for &(name, l_min, r_min, unit) in &configs {
        // Golden
        let mut g_hyphenated = 0;
        let mut g_breaks = 0;
        for (_, w) in &golden_words {
            let a = analyze_word(w);
            let b = find_all_phonotactic_breaks(&a);
            let count = b
                .iter()
                .filter(|x| match unit {
                    "letter" => x.left_letters >= l_min && x.right_letters >= r_min,
                    "syllable" => x.left_syllables >= l_min && x.right_syllables >= r_min,
                    "scalar" => x.left_scalars >= l_min && x.right_scalars >= r_min,
                    _ => false,
                })
                .count();
            if count > 0 {
                g_hyphenated += 1;
                g_breaks += count;
            }
        }

        // Word doc
        let mut d_hyphenated = 0;
        let mut d_breaks = 0;
        for w in &unique_word_doc {
            let a = analyze_word(w);
            let b = find_all_phonotactic_breaks(&a);
            let count = b
                .iter()
                .filter(|x| match unit {
                    "letter" => x.left_letters >= l_min && x.right_letters >= r_min,
                    "syllable" => x.left_syllables >= l_min && x.right_syllables >= r_min,
                    "scalar" => x.left_scalars >= l_min && x.right_scalars >= r_min,
                    _ => false,
                })
                .count();
            if count > 0 {
                d_hyphenated += 1;
                d_breaks += count;
            }
        }

        md.push_str(&format!(
            "| **{}** | {}/122 ({:.1}%) | {} | {}/38 ({:.1}%) | {} |\n",
            name,
            g_hyphenated,
            (g_hyphenated as f64 / 122.0) * 100.0,
            g_breaks,
            d_hyphenated,
            (d_hyphenated as f64 / 38.0) * 100.0,
            d_breaks,
        ));
    }

    md.push_str("\n\n## 2. Word Document (38 Unique Words) Full Breakdown\n\n");
    md.push_str("| # | Word | Letters | Syllables | Scalars | Letter 2/2 | Letter 3/3 | Syllable 2/2 | Syllable 3/3 |\n");
    md.push_str("|---|---|---|---|---|---|---|---|---|\n");

    for (idx, w) in unique_word_doc.iter().enumerate() {
        let a = analyze_word(w);
        let b = find_all_phonotactic_breaks(&a);
        let l22 = get_hyphenated(&a, &b, 2, 2, "letter");
        let l33 = get_hyphenated(&a, &b, 3, 3, "letter");
        let s22 = get_hyphenated(&a, &b, 2, 2, "syllable");
        let s33 = get_hyphenated(&a, &b, 3, 3, "syllable");
        md.push_str(&format!(
            "| {} | **{}** | {} | {} | {} | `{}` | `{}` | `{}` | `{}` |\n",
            idx + 1,
            w,
            a.letter_count,
            a.syllable_count,
            a.scalar_count,
            l22,
            l33,
            s22,
            s33
        ));
    }

    std::fs::write("target/empirical_study_dump.md", md).expect("write output");
    println!("Output saved to target/empirical_study_dump.md successfully!");
}
