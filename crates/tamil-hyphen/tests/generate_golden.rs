use std::fs::File;
use std::io::Write;
use std::path::PathBuf;
use tamil_hyphen::{
    hyphenate_text, hyphenate_word, hyphenation_points, wrap_text, HyphenationConfig,
};

fn escape_ascii(s: &str) -> String {
    let mut out = String::new();
    for c in s.chars() {
        if (c as u32) > 127 {
            if (c as u32) <= 0xFFFF {
                out.push_str(&format!("\\u{:04x}", c as u32));
            } else {
                let code = c as u32 - 0x10000;
                let hi = 0xD800 + (code >> 10);
                let lo = 0xDC00 + (code & 0x3FF);
                out.push_str(&format!("\\u{:04x}\\u{:04x}", hi, lo));
            }
        } else {
            out.push(c);
        }
    }
    out
}

#[derive(serde::Serialize)]
struct GoldenVector {
    id: String,
    op: String,
    input: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    expected: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    expected_error: Option<String>,
    dialect: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    region: Option<String>,
    tags: Vec<String>,
    source: String,
}

#[test]
fn generate_golden_suite() {
    let mut rows: Vec<GoldenVector> = Vec::new();
    let mut counter = 1;

    // Helper macro to add row
    let mut add_word = |word: &str, delimiter: &str, left_min: usize, right_min: usize, dialect: &str, region: Option<&str>, tags: Vec<&str>| {
        let cfg = HyphenationConfig {
            delimiter: delimiter.to_string(),
            left_min,
            right_min,
        };
        let res = hyphenate_word(word, Some(&cfg)).unwrap();
        let id = format!("hyphen_{:03}", counter);
        counter += 1;

        let input_val = if delimiter == "-" && left_min == 2 && right_min == 2 {
            serde_json::json!({
                "word": word,
                "delimiter": "-",
                "left_min": 2,
                "right_min": 2
            })
        } else {
            serde_json::json!({
                "word": word,
                "delimiter": delimiter,
                "left_min": left_min,
                "right_min": right_min
            })
        };

        rows.push(GoldenVector {
            id,
            op: "hyphenate_word".to_string(),
            input: input_val,
            expected: Some(serde_json::to_value(&res).unwrap()),
            expected_error: None,
            dialect: dialect.to_string(),
            region: region.map(|s| s.to_string()),
            tags: tags.into_iter().map(|s| s.to_string()).collect(),
            source: "W3C tam-lreq syllable hyphenation rules".to_string(),
        });
    };

    // 1. Common vocabulary with default margins (delimiter = "-")
    let common_words = vec![
        "தமிழ்நாடு", "பல்கலைக்கழகம்", "துர்ப்பிரயோகம்", "வணக்கம்", "நன்றி",
        "மகிழ்ச்சி", "வெற்றி", "கற்றல்", "செந்தமிழ்", "முக்காலம்",
        "அம்மா", "அப்பா", "தம்பி", "தங்கை", "அண்ணன்",
        "பாப்பா", "புத்தகம்", "பள்ளிக்கூடம்", "அரசாங்கம்", "மின்னஞ்சல்",
        "கணினி", "இணையம்", "தொழில்நுட்பம்", "அறிவியல்", "ஆராய்ச்சி",
        "மருத்துவம்", "விவசாயம்", "வானூர்தி", "செயற்கைக்கோள்", "நாளிதழ்",
        "கட்டுரை", "கவிதை", "இலக்கியம்", "வரலாறு", "பூகோளம்",
        "பொருளாதாரம்", "அரசியல்", "சமூகம்", "கலாச்சாரம்", "பாரம்பரியம்",
        "தலைமுறை", "எதிர்காலம்", "முன்னேற்றம்", "வளர்ச்சி", "ஒற்றுமை",
        "அமைதி", "சுதந்திரம்", "மக்களாட்சி", "நீதிமன்றம்", "காவல்துறை"
    ];

    for w in common_words {
        add_word(w, "-", 2, 2, "COMMON", None, vec!["common", "syllable"]);
    }

    // 2. Consonant clusters and multi-pulli sequences
    let cluster_words = vec![
        "பார்த்தான்", "சேர்த்தார்", "வாழ்த்துகள்", "எழுத்தாளர்", "பார்க்கலாம்",
        "கேட்கலாம்", "செய்தார்கள்", "நினைத்தேன்", "முயற்சி", "பயிற்சி",
        "உணர்ச்சி", "வளர்ச்சி", "ஆராய்ச்சி", "பேராசிரியர்", "சொற்பொழிவு",
        "நாடகத்துறை", "விளையாட்டு", "நீச்சல்", "ஓட்டப்பந்தயம்", "பாய்ச்சல்"
    ];

    for w in cluster_words {
        add_word(w, "-", 2, 2, "COMMON", None, vec!["cluster", "coda_binding"]);
    }

    // 3. Grantha onsets and conjuncts
    let grantha_words = vec![
        "புஷ்பம்", "வர்ஷம்", "லக்ஷ்மி", "கஷ்டம்", "நஷ்டம்",
        "விஷயம்", "ஸ்ரீரங்கம்", "ஹரிஹரன்", "ஜாக்கிரதை", "ஷண்முகம்"
    ];

    for w in grantha_words {
        add_word(w, "-", 2, 2, "COMMON", None, vec!["grantha"]);
    }

    // 4. Tamil Nadu regional vocabulary (dialect: "TN", region: "TN")
    let tn_words = vec![
        "சென்னை", "கோயம்புத்தூர்", "மதுரை", "திருச்சிராப்பள்ளி", "திருநெல்வேலி",
        "தூத்துக்குடி", "தஞ்சாவூர்", "திண்டுக்கல்", "காஞ்சிபுரம்", "வேலூர்",
        "ஈரோடு", "திருப்பூர்", "நாகப்பட்டினம்", "கன்னியாகுமரி", "விழுப்புரம்"
    ];

    for w in tn_words {
        add_word(w, "-", 2, 2, "TN", Some("TN"), vec!["tn", "regional"]);
    }

    // 5. Sri Lanka regional vocabulary (dialect: "SL", region: "JAFFNA" / "BATTICALOA")
    let sl_words = vec![
        ("யாழ்ப்பாணம்", "JAFFNA"), ("மட்டக்களப்பு", "BATTICALOA"),
        ("திருகோணமலை", "JAFFNA"), ("கொழும்பு", "JAFFNA"),
        ("வவுனியா", "JAFFNA"), ("மன்னார்", "JAFFNA"),
        ("முல்லைத்தீவு", "JAFFNA"), ("கிளிநொச்சி", "JAFFNA"),
        ("நுவரெலியா", "UP_COUNTRY"), ("அம்பாறை", "BATTICALOA"),
        ("புத்தளம்", "JAFFNA"), ("கல்முனை", "BATTICALOA"),
        ("காங்கேசன்துறை", "JAFFNA"), ("பருத்தித்துறை", "JAFFNA"),
        ("காரைநகர்", "JAFFNA")
    ];

    for (w, r) in sl_words {
        add_word(w, "-", 2, 2, "SL", Some(r), vec!["sl", "regional"]);
    }

    // 6. Safe margin edge cases (short words, custom margins)
    let margin_cases = vec![
        ("தமிழ்", 2, 2, vec!["short_word", "margin_enforced"]),
        ("கல்வி", 2, 2, vec!["short_word", "margin_enforced"]),
        ("நாடு", 2, 2, vec!["short_word", "margin_enforced"]),
        ("மரம்", 2, 2, vec!["short_word", "margin_enforced"]),
        ("தமிழ்நாடு", 1, 1, vec!["margin_1_1"]),
        ("பல்கலைக்கழகம்", 3, 3, vec!["margin_3_3"]),
        ("துர்ப்பிரயோகம்", 1, 1, vec!["margin_1_1"]),
        ("முக்காலம்", 3, 3, vec!["margin_3_3"]),
        ("கற்றல்", 1, 1, vec!["margin_1_1"]),
        ("வெற்றி", 1, 1, vec!["margin_1_1"]),
    ];

    for (w, lm, rm, tags) in margin_cases {
        add_word(w, "-", lm, rm, "COMMON", None, tags);
    }

    // 7. Error cases
    let error_cases = vec![
        ("தமிழ்நாடு", 0, 2, "left_min must be at least 1"),
        ("தமிழ்நாடு", 2, 0, "right_min must be at least 1"),
    ];

    for (w, lm, rm, err) in error_cases {
        let id = format!("hyphen_{:03}", counter);
        counter += 1;
        rows.push(GoldenVector {
            id,
            op: "hyphenate_word".to_string(),
            input: serde_json::json!({
                "word": w,
                "left_min": lm,
                "right_min": rm
            }),
            expected: None,
            expected_error: Some(err.to_string()),
            dialect: "COMMON".to_string(),
            region: None,
            tags: vec!["error".to_string(), "validation".to_string()],
            source: "Parameter boundary validation contract".to_string(),
        });
    }

    // 8. Hyphenation points operation
    let pts_words = vec![
        "தமிழ்நாடு", "பல்கலைக்கழகம்", "துர்ப்பிரயோகம்", "வணக்கம்", "யாழ்ப்பாணம்", "கோயம்புத்தூர்"
    ];

    for w in pts_words {
        let pts = hyphenation_points(w, None).unwrap();
        let id = format!("hyphen_{:03}", counter);
        counter += 1;
        rows.push(GoldenVector {
            id,
            op: "hyphenation_points".to_string(),
            input: serde_json::json!({
                "word": w,
                "left_min": 2,
                "right_min": 2
            }),
            expected: Some(serde_json::to_value(&pts).unwrap()),
            expected_error: None,
            dialect: "COMMON".to_string(),
            region: None,
            tags: vec!["points".to_string()],
            source: "W3C tam-lreq syllable hyphenation points".to_string(),
        });
    }

    // 9. Text soft-hyphenation (hyphenate_text)
    let text_cases = vec![
        ("தமிழ்நாடு மற்றும் பல்கலைக்கழகம் ஆகிய இரண்டும் செழித்து வளர்கின்றன.", "COMMON", vec!["paragraph", "soft_hyphen"]),
        ("Welcome to சென்னை! தமிழ் வாழ்க.", "TN", vec!["mixed_script", "tn"]),
        ("யாழ்ப்பாணம் மற்றும் கொழும்பு இலங்கை நகரங்கள்.", "SL", vec!["paragraph", "sl"]),
        ("Visit https://tamil.org for தமிழ் தகவல்கள் மற்றும் செய்திகள்.", "COMMON", vec!["url_preservation", "paragraph"]),
    ];

    for (txt, dia, tags) in text_cases {
        let res = hyphenate_text(txt, None).unwrap();
        let id = format!("hyphen_{:03}", counter);
        counter += 1;
        rows.push(GoldenVector {
            id,
            op: "hyphenate_text".to_string(),
            input: serde_json::json!({
                "text": txt,
                "delimiter": "\u{00AD}",
                "left_min": 2,
                "right_min": 2
            }),
            expected: Some(serde_json::json!(res)),
            expected_error: None,
            dialect: dia.to_string(),
            region: if dia == "TN" { Some("TN".to_string()) } else if dia == "SL" { Some("JAFFNA".to_string()) } else { None },
            tags: tags.into_iter().map(|s| s.to_string()).collect(),
            source: "W3C tam-lreq text paragraph hyphenation contract".to_string(),
        });
    }

    // 10. Wrap text (wrap_text)
    let wrap_cases = vec![
        ("தமிழ்நாடு ஒரு அழகான மாநிலம் ஆகும்.", 10, "COMMON", vec!["wrap", "line_break"]),
        ("பல்கலைக்கழகம் சிறந்த கல்வியை வழங்குகிறது.", 12, "COMMON", vec!["wrap", "line_break"]),
        ("சென்னையில் உள்ள மெரினா கடற்கரை அழகானது.", 15, "TN", vec!["wrap", "tn"]),
        ("யாழ்ப்பாணத்து மாம்பழம் மிகவும் இனிப்பானது.", 15, "SL", vec!["wrap", "sl"]),
    ];

    for (txt, width, dia, tags) in wrap_cases {
        let res = wrap_text(txt, width, None).unwrap();
        let id = format!("hyphen_{:03}", counter);
        counter += 1;
        rows.push(GoldenVector {
            id,
            op: "wrap_text".to_string(),
            input: serde_json::json!({
                "text": txt,
                "max_width": width,
                "delimiter": "-",
                "left_min": 2,
                "right_min": 2
            }),
            expected: Some(serde_json::to_value(&res).unwrap()),
            expected_error: None,
            dialect: dia.to_string(),
            region: if dia == "TN" { Some("TN".to_string()) } else if dia == "SL" { Some("JAFFNA".to_string()) } else { None },
            tags: tags.into_iter().map(|s| s.to_string()).collect(),
            source: "Deterministic line wrapping contract".to_string(),
        });
    }

    assert!(rows.len() >= 120, "Must have at least 120 vectors, got {}", rows.len());

    // Write to tests/golden/hyphen_syllable.jsonl with proper Unicode escaping
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().parent().unwrap().to_path_buf();
    let golden_path = repo_root.join("tests").join("golden").join("hyphen_syllable.jsonl");

    let mut file = File::create(&golden_path).expect("Failed to create hyphen_syllable.jsonl");
    for row in &rows {
        let json_str = serde_json::to_string(row).unwrap();
        let escaped = escape_ascii(&json_str);
        writeln!(file, "{}", escaped).expect("Failed to write line");
    }

    println!("Successfully generated {} golden vectors to {:?}", rows.len(), golden_path);
}
