#![forbid(unsafe_code)]

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::exit;

use serde_json::json;
use tamil_hyphen::docx::process_docx_file;
use tamil_hyphen::types::HyphenationConfig;
use tamil_hyphen::{
    export_dic_file, generate_patterns, package_oxt, DicExportOptions, LiangEvaluator,
};

fn print_usage() {
    eprintln!(
        r#"tamil-toolkit CLI

USAGE:
    tamil-toolkit <COMMAND> <SUBCOMMAND> [OPTIONS] [ARGUMENTS]

COMMANDS:
    core        Tamil Unicode primitives, segmentation, and inspection
    norm        Unicode normalization (NFC/NFD), repair, and search folding
    codec       Legacy font encodings conversion and detection
    collate     Tamil alphabetical collation and sort keys
    numerals    Tamil numerals, number words, and fractions
    calendar    Tamil calendar, solar-lunar conversion, and panchangam
    hyphen      Syllable breakdown, word hyphenation, and document processing
    lexicon     Exact compiled lexicon lookup and pack metadata
    help        Print this message

Run 'tamil-toolkit <COMMAND> --help' for command-specific options.
"#
    );
}

// ==========================================
// Hyphen Handlers & Help
// ==========================================

fn print_hyphen_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit hyphen <SUBCOMMAND> [OPTIONS]

SUBCOMMANDS:
    word <WORD> [OPTIONS]           Hyphenate a single Tamil word
    text <TEXT> [OPTIONS]           Hyphenate paragraph text with soft hyphens
    wrap <TEXT> -w <WIDTH>          Wrap paragraph text at specified width
    export-dic [OPTIONS]            Export Frank Liang hyphenation dictionary (.dic)
    package-oxt [OPTIONS]           Package LibreOffice extension (.oxt)
    process-docx [OPTIONS]          Batch-hyphenate OpenXML Word (.docx) document
    -h, --help                      Print help information
"#
    );
}

fn handle_hyphen(args: &[String]) {
    if args.is_empty() {
        print_hyphen_usage();
        exit(1);
    }
    match args[0].as_str() {
        "word" => handle_hyphen_word(&args[1..]),
        "text" => handle_hyphen_text(&args[1..]),
        "wrap" => handle_hyphen_wrap(&args[1..]),
        "export-dic" => handle_export_dic(&args[1..]),
        "package-oxt" => handle_package_oxt(&args[1..]),
        "process-docx" => handle_process_docx(&args[1..]),
        "-h" | "--help" => print_hyphen_usage(),
        other => {
            eprintln!("Error: Unknown hyphen subcommand '{other}'.");
            print_hyphen_usage();
            exit(1);
        }
    }
}

fn handle_hyphen_word(args: &[String]) {
    let mut word: Option<String> = None;
    let mut delimiter = "\u{00AD}".to_string();
    let mut left_min = 3usize;
    let mut right_min = 3usize;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-d" | "--delimiter" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --delimiter requires a string argument.");
                    exit(1);
                }
                delimiter = args[i + 1].clone();
                i += 2;
            }
            "-l" | "--left-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --left-min requires an integer.");
                    exit(1);
                }
                left_min = args[i + 1].parse().unwrap_or(3);
                i += 2;
            }
            "-r" | "--right-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --right-min requires an integer.");
                    exit(1);
                }
                right_min = args[i + 1].parse().unwrap_or(3);
                i += 2;
            }
            arg if !arg.starts_with('-') && word.is_none() => {
                word = Some(arg.to_string());
                i += 1;
            }
            _ => {
                i += 1;
            }
        }
    }

    let input_word = match word {
        Some(w) => w,
        None => {
            eprintln!("Error: Missing required word argument.");
            eprintln!("Usage: tamil-toolkit hyphen word <WORD> [-l N] [-r N] [-d DELIM]");
            exit(1);
        }
    };

    let cfg = HyphenationConfig {
        delimiter,
        left_min,
        right_min,
    };

    match tamil_hyphen::hyphenate_word(&input_word, Some(&cfg)) {
        Ok(res) => println!("{}", res.hyphenated),
        Err(e) => {
            eprintln!("Error hyphenating word: {e}");
            exit(1);
        }
    }
}

fn handle_hyphen_text(args: &[String]) {
    let mut text: Option<String> = None;
    let mut delimiter = "\u{00AD}".to_string();
    let mut left_min = 3usize;
    let mut right_min = 3usize;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-d" | "--delimiter" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --delimiter requires an argument.");
                    exit(1);
                }
                delimiter = args[i + 1].clone();
                i += 2;
            }
            "-l" | "--left-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --left-min requires an integer.");
                    exit(1);
                }
                left_min = args[i + 1].parse().unwrap_or(3);
                i += 2;
            }
            "-r" | "--right-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --right-min requires an integer.");
                    exit(1);
                }
                right_min = args[i + 1].parse().unwrap_or(3);
                i += 2;
            }
            arg if !arg.starts_with('-') && text.is_none() => {
                text = Some(arg.to_string());
                i += 1;
            }
            _ => {
                i += 1;
            }
        }
    }

    let input_text = match text {
        Some(t) => t,
        None => {
            eprintln!("Error: Missing required text argument.");
            eprintln!("Usage: tamil-toolkit hyphen text <TEXT> [-l N] [-r N] [-d DELIM]");
            exit(1);
        }
    };

    let cfg = HyphenationConfig {
        delimiter,
        left_min,
        right_min,
    };

    match tamil_hyphen::hyphenate_text(&input_text, Some(&cfg)) {
        Ok(res) => println!("{res}"),
        Err(e) => {
            eprintln!("Error hyphenating text: {e}");
            exit(1);
        }
    }
}

fn handle_hyphen_wrap(args: &[String]) {
    let mut text: Option<String> = None;
    let mut width: usize = 40;
    let mut delimiter = "-".to_string();
    let mut left_min = 3usize;
    let mut right_min = 3usize;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-w" | "--width" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --width requires an integer.");
                    exit(1);
                }
                width = args[i + 1].parse().unwrap_or(40);
                i += 2;
            }
            "-d" | "--delimiter" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --delimiter requires an argument.");
                    exit(1);
                }
                delimiter = args[i + 1].clone();
                i += 2;
            }
            "-l" | "--left-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --left-min requires an integer.");
                    exit(1);
                }
                left_min = args[i + 1].parse().unwrap_or(3);
                i += 2;
            }
            "-r" | "--right-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --right-min requires an integer.");
                    exit(1);
                }
                right_min = args[i + 1].parse().unwrap_or(3);
                i += 2;
            }
            arg if !arg.starts_with('-') && text.is_none() => {
                text = Some(arg.to_string());
                i += 1;
            }
            _ => {
                i += 1;
            }
        }
    }

    let input_text = match text {
        Some(t) => t,
        None => {
            eprintln!("Error: Missing required text argument.");
            eprintln!(
                "Usage: tamil-toolkit hyphen wrap <TEXT> -w <WIDTH> [-l N] [-r N] [-d DELIM]"
            );
            exit(1);
        }
    };

    let cfg = HyphenationConfig {
        delimiter,
        left_min,
        right_min,
    };

    match tamil_hyphen::wrap_text(&input_text, width, Some(&cfg)) {
        Ok(res) => println!("{}", res.lines.join("\n")),
        Err(e) => {
            eprintln!("Error wrapping text: {e}");
            exit(1);
        }
    }
}

fn handle_export_dic(args: &[String]) {
    let mut output = PathBuf::from("hyph_ta_IN.dic");
    let mut left_min = 3usize;
    let mut right_min = 3usize;
    let mut verify = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-o" | "--output" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --output requires a file path.");
                    exit(1);
                }
                output = PathBuf::from(&args[i + 1]);
                i += 2;
            }
            "-l" | "--lefthyphenmin" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --lefthyphenmin requires a number.");
                    exit(1);
                }
                left_min = args[i + 1].parse().unwrap_or_else(|_| {
                    eprintln!("Error: Invalid integer for --lefthyphenmin");
                    exit(1);
                });
                i += 2;
            }
            "-r" | "--righthyphenmin" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --righthyphenmin requires a number.");
                    exit(1);
                }
                right_min = args[i + 1].parse().unwrap_or_else(|_| {
                    eprintln!("Error: Invalid integer for --righthyphenmin");
                    exit(1);
                });
                i += 2;
            }
            "--verify" => {
                verify = true;
                i += 1;
            }
            "-h" | "--help" => {
                eprintln!(
                    r#"USAGE:
    tamil-toolkit hyphen export-dic [OPTIONS]

OPTIONS:
    -o, --output <PATH>         Destination filepath [default: hyph_ta_IN.dic]
    -l, --lefthyphenmin <N>     Minimum characters before hyphen [default: 3]
    -r, --righthyphenmin <N>    Minimum characters after hyphen [default: 3]
    --verify                    Run verification after export
    -h, --help                  Print help information
"#
                );
                return;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}'");
                exit(1);
            }
        }
    }

    let options = DicExportOptions {
        left_hyphen_min: left_min,
        right_hyphen_min: right_min,
    };

    let dict = generate_patterns(&options);
    if let Err(e) = export_dic_file(&dict, &output) {
        eprintln!("Failed to export dictionary to {}: {e}", output.display());
        exit(1);
    }

    println!(
        "Successfully exported Frank Liang hyphenation dictionary to {} ({} patterns)",
        output.display(),
        dict.patterns.len()
    );

    if verify {
        println!("Verifying exported dictionary patterns against phonotactic boundaries...");
        let evaluator = LiangEvaluator::new(&dict);
        let sample_words = [
            "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}\u{0BA8}\u{0bbe}\u{0B9F}\u{0BC1}",
            "\u{0BAA}\u{0BB2}\u{0BCD}\u{0B95}\u{0BB2}\u{0BC8}\u{0B95}\u{0BCD}\u{0B95}\u{0BB4}\u{0B95}\u{0BAE}\u{0BCD}",
            "\u{0BA4}\u{0BC1}\u{0bb7}\u{0BCD}\u{0BAA}\u{0bbf}\u{0bb0}\u{0baf}\u{0bcb}\u{0b95}\u{0bae}\u{0bcd}",
            "\u{0BB5}\u{0BA3}\u{0B95}\u{0BCD}\u{0B95}\u{0BAE}\u{0BCD}",
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0Bbf}",
            "\u{0BAE}\u{0B95}\u{0Bbf}\u{0BB4}\u{0BCD}\u{0B9a}\u{0BCD}\u{0B9a}\u{0Bbf}",
        ];
        let mut passed = 0;
        for word in &sample_words {
            let (hyphenated, segs) = evaluator.hyphenate_word(word, "-");
            let mut valid = true;
            for seg in &segs {
                if seg.starts_with('\u{0BCD}') {
                    valid = false;
                }
                let chars: Vec<char> = seg.chars().collect();
                if chars.len() >= 2 && chars[1] == '\u{0BCD}' {
                    let is_grantha_cluster = (chars[0] == '\u{0BB8}' || chars[0] == '\u{0BB6}')
                        && chars.len() >= 4
                        && chars[2] == '\u{0BB0}'
                        && chars[3] == '\u{0BC0}';
                    let is_ksha_cluster = chars[0] == '\u{0B95}'
                        && chars.len() >= 3
                        && chars[2] == '\u{0BB7}'
                        && (chars.len() == 3 || chars[3] != '\u{0BCD}');

                    if !is_grantha_cluster && !is_ksha_cluster {
                        valid = false;
                    }
                }
            }
            if valid {
                passed += 1;
            } else {
                eprintln!("Verification failure on word '{word}': {hyphenated}");
            }
        }
        println!(
            "Verified {passed}/{} sample words with zero orthographic violations.",
            sample_words.len()
        );
    }
}

fn handle_package_oxt(args: &[String]) {
    let mut input = PathBuf::from("hyph_ta_IN.dic");
    let mut output = PathBuf::from("dist/tamil-hyphenation.oxt");
    let mut version = "0.1.0-alpha.6".to_string();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-i" | "--input" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --input requires a file path.");
                    exit(1);
                }
                input = PathBuf::from(&args[i + 1]);
                i += 2;
            }
            "-o" | "--output" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --output requires a file path.");
                    exit(1);
                }
                output = PathBuf::from(&args[i + 1]);
                i += 2;
            }
            "-v" | "--version" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --version requires a string.");
                    exit(1);
                }
                version = args[i + 1].clone();
                i += 2;
            }
            "-h" | "--help" => {
                eprintln!(
                    r#"USAGE:
    tamil-toolkit hyphen package-oxt [OPTIONS]

OPTIONS:
    -i, --input <PATH>          Source .dic file to bundle [default: hyph_ta_IN.dic]
    -o, --output <PATH>         Destination .oxt path [default: dist/tamil-hyphenation.oxt]
    -v, --version <VER>         Extension version [default: 0.1.0-alpha.6]
    -h, --help                  Print help information
"#
                );
                return;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}'");
                exit(1);
            }
        }
    }

    if !input.exists() {
        eprintln!(
            "Input dictionary file '{}' does not exist. Generating default patterns first...",
            input.display()
        );
        let options = DicExportOptions::default();
        let dict = generate_patterns(&options);
        if let Err(e) = export_dic_file(&dict, &input) {
            eprintln!("Failed to generate dictionary at {}: {e}", input.display());
            exit(1);
        }
    }

    if let Err(e) = package_oxt(&input, &output, &version) {
        eprintln!("Failed to package OXT extension: {e}");
        exit(1);
    }

    println!(
        "Successfully packaged LibreOffice extension to {} (version: {})",
        output.display(),
        version
    );
    println!("Registered locales: ta-IN ta-LK ta-SG ta-MY ta");
}

fn handle_process_docx(args: &[String]) {
    let mut input: Option<PathBuf> = None;
    let mut output: Option<PathBuf> = None;
    let mut inplace = false;
    let mut left_min = 3usize;
    let mut right_min = 3usize;
    let mut verbose = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-i" | "--input" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --input requires a file path.");
                    exit(1);
                }
                input = Some(PathBuf::from(&args[i + 1]));
                i += 2;
            }
            "-o" | "--output" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --output requires a file path.");
                    exit(1);
                }
                output = Some(PathBuf::from(&args[i + 1]));
                i += 2;
            }
            "--inplace" => {
                inplace = true;
                i += 1;
            }
            "-l" | "--left-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --left-min requires a number.");
                    exit(1);
                }
                left_min = args[i + 1].parse().unwrap_or_else(|_| {
                    eprintln!("Error: Invalid integer for --left-min");
                    exit(1);
                });
                i += 2;
            }
            "-r" | "--right-min" => {
                if i + 1 >= args.len() {
                    eprintln!("Error: --right-min requires a number.");
                    exit(1);
                }
                right_min = args[i + 1].parse().unwrap_or_else(|_| {
                    eprintln!("Error: Invalid integer for --right-min");
                    exit(1);
                });
                i += 2;
            }
            "-v" | "--verbose" => {
                verbose = true;
                i += 1;
            }
            "-h" | "--help" => {
                eprintln!(
                    r#"USAGE:
    tamil-toolkit hyphen process-docx [OPTIONS] --input <PATH>

OPTIONS:
    -i, --input <PATH>          Source .docx file to process
    -o, --output <PATH>         Destination .docx path (required unless --inplace is set)
    --inplace                   Overwrite input file atomically
    -l, --left-min <N>          Minimum characters before hyphen [default: 3]
    -r, --right-min <N>         Minimum characters after hyphen [default: 3]
    -v, --verbose               Print detailed processing statistics
    -h, --help                  Print help information
"#
                );
                return;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}'");
                exit(1);
            }
        }
    }

    let input_path = match input {
        Some(p) => p,
        None => {
            eprintln!("Error: Missing required option --input <PATH>.");
            exit(1);
        }
    };

    if !input_path.exists() {
        eprintln!("Error: Input file does not exist: {}", input_path.display());
        exit(2);
    }

    let target_output = if inplace {
        input_path.clone()
    } else {
        match output {
            Some(p) => p,
            None => {
                eprintln!("Error: Either --output <PATH> or --inplace must be specified.");
                exit(1);
            }
        }
    };

    let config = HyphenationConfig {
        delimiter: "\u{00AD}".to_string(),
        left_min,
        right_min,
    };

    match process_docx_file(&input_path, &target_output, Some(&config)) {
        Ok(stats) => {
            println!(
                "Successfully processed docx: {} -> {}",
                input_path.display(),
                target_output.display()
            );
            if verbose || stats.soft_hyphens_inserted > 0 {
                println!("  Parts updated: {}", stats.parts_updated);
                println!("  Paragraphs scanned: {}", stats.paragraphs_processed);
                println!("  Tamil words evaluated: {}", stats.words_hyphenated);
                println!(
                    "  Soft hyphens (U+00AD) injected: {}",
                    stats.soft_hyphens_inserted
                );
            }
        }
        Err(e) => {
            eprintln!("Failed to process docx file: {e}");
            exit(3);
        }
    }
}

// ==========================================
// Core Handlers
// ==========================================

fn print_core_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit core <SUBCOMMAND> [OPTIONS] [ARGUMENTS]

SUBCOMMANDS:
    letters <TEXT> [--json]                 Split text into tailored Tamil letters
    inspect <TEXT>                          Inspect normalization, counts, and classifications
    split-uyirmei <LETTER>                  Decompose Uyirmei into Mei and Uyir
    compose-uyirmei <MEI> <UYIR>            Compose Mei and independent Uyir into Uyirmei
    -h, --help                              Print help information
"#
    );
}

fn handle_core(args: &[String]) {
    if args.is_empty() {
        print_core_usage();
        exit(1);
    }
    match args[0].as_str() {
        "letters" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for letters.");
                exit(1);
            }
            let text = &args[1];
            let json_mode = args.iter().any(|a| a == "--json");
            let letters = tamil_core::get_letters(text);
            if json_mode {
                println!("{}", serde_json::to_string(&letters).unwrap());
            } else {
                println!("{}", letters.join(" "));
            }
        }
        "inspect" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for inspect.");
                exit(1);
            }
            let text = &args[1];
            let inspected = tamil_core::inspect_tamil_string(text);
            println!(
                "{}",
                serde_json::to_string_pretty(&json!(inspected)).unwrap()
            );
        }
        "split-uyirmei" => {
            if args.len() < 2 {
                eprintln!("Error: Missing letter argument for split-uyirmei.");
                exit(1);
            }
            let letter = &args[1];
            match tamil_core::split_uyirmei(letter) {
                Ok(parts) => println!("{}", serde_json::to_string(&parts).unwrap()),
                Err(e) => {
                    eprintln!("Error: {e}");
                    exit(1);
                }
            }
        }
        "compose-uyirmei" => {
            if args.len() < 3 {
                eprintln!("Error: compose-uyirmei requires <MEI> and <UYIR> arguments.");
                exit(1);
            }
            let mei = &args[1];
            let uyir = &args[2];
            match tamil_core::compose_uyirmei(mei, uyir) {
                Ok(res) => println!("{res}"),
                Err(e) => {
                    eprintln!("Error: {e}");
                    exit(1);
                }
            }
        }
        "-h" | "--help" => print_core_usage(),
        other => {
            eprintln!("Error: Unknown core subcommand '{other}'.");
            print_core_usage();
            exit(1);
        }
    }
}

// ==========================================
// Norm Handlers
// ==========================================

fn print_norm_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit norm <SUBCOMMAND> [ARGUMENTS]

SUBCOMMANDS:
    nfc <TEXT>                              Canonical Unicode NFC normalization
    nfd <TEXT>                              Canonical Unicode NFD normalization
    repair <TEXT> [--json]                  Repair text corruption with diagnostics
    fold <TEXT> [--profile PROFILE]         Fold string for search (mayangoli/grantha)
    -h, --help                              Print help information
"#
    );
}

fn handle_norm(args: &[String]) {
    if args.is_empty() {
        print_norm_usage();
        exit(1);
    }
    match args[0].as_str() {
        "nfc" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for nfc.");
                exit(1);
            }
            println!("{}", tamil_norm::normalize_nfc(&args[1]));
        }
        "nfd" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for nfd.");
                exit(1);
            }
            println!("{}", tamil_norm::normalize_nfd(&args[1]));
        }
        "repair" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for repair.");
                exit(1);
            }
            let text = &args[1];
            let json_mode = args.iter().any(|a| a == "--json");
            let rep = tamil_norm::repair_tamil_text(text, &tamil_norm::RepairOptions::default());
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string(&json!({
                        "text": rep.text,
                        "diagnostics": {
                            "duplicate_pulli_count": rep.diagnostics.duplicate_pulli_count,
                            "visual_kombu_count": rep.diagnostics.visual_kombu_count,
                            "stripped_control_count": rep.diagnostics.stripped_control_count,
                            "total_repairs": rep.diagnostics.total_repairs,
                        }
                    }))
                    .unwrap()
                );
            } else {
                println!("{}", rep.text);
            }
        }
        "fold" => {
            let mut text: Option<&str> = None;
            let mut profile = tamil_norm::FoldingProfile::Comprehensive;
            let mut i = 1;
            while i < args.len() {
                if args[i] == "--profile" {
                    let Some(val) = args.get(i + 1) else {
                        eprintln!("Error: Missing value for --profile.");
                        exit(1);
                    };
                    profile = tamil_norm::FoldingProfile::parse(val).unwrap_or_else(|| {
                        eprintln!(
                            "Error: Unknown folding profile '{val}'. Expected: mayangoli, grantha, comprehensive."
                        );
                        exit(1);
                    });
                    i += 2;
                } else if args[i].starts_with('-') {
                    eprintln!("Error: Unknown option '{}' for fold.", args[i]);
                    exit(1);
                } else if text.is_none() {
                    text = Some(&args[i]);
                    i += 1;
                } else {
                    eprintln!("Error: Unexpected extra argument '{}' for fold.", args[i]);
                    exit(1);
                }
            }
            let Some(text) = text else {
                eprintln!("Error: Missing text argument for fold.");
                exit(1);
            };
            println!("{}", tamil_norm::fold_for_search(text, profile));
        }
        "-h" | "--help" => print_norm_usage(),
        other => {
            eprintln!("Error: Unknown norm subcommand '{other}'.");
            print_norm_usage();
            exit(1);
        }
    }
}

// ==========================================
// Codec Handlers
// ==========================================

fn print_codec_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit codec <SUBCOMMAND> [OPTIONS] [ARGUMENTS]

SUBCOMMANDS:
    convert <TEXT> --from <ENC> --to <ENC>   Convert legacy font text
    detect <TEXT>                           Detect legacy encoding
    -h, --help                              Print help information
"#
    );
}

fn handle_codec(args: &[String]) {
    if args.is_empty() {
        print_codec_usage();
        exit(1);
    }
    match args[0].as_str() {
        "convert" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for convert.");
                exit(1);
            }
            let text = &args[1];
            let mut from_enc = "unicode".to_string();
            let mut to_enc = "unicode".to_string();

            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--from" if i + 1 < args.len() => {
                        from_enc = args[i + 1].to_lowercase();
                        i += 2;
                    }
                    "--to" if i + 1 < args.len() => {
                        to_enc = args[i + 1].to_lowercase();
                        i += 2;
                    }
                    _ => {
                        i += 1;
                    }
                }
            }

            // Convert via dispatcher
            let req = if from_enc == "unicode" {
                match to_enc.as_str() {
                    "bamini" => json!({"op": "unicode_to_bamini", "input": text}),
                    "tscii" => json!({"op": "unicode_to_tscii_bytes", "input": text}),
                    "tam" => json!({"op": "unicode_to_tam_bytes", "input": text}),
                    "tab" => json!({"op": "unicode_to_tab_bytes", "input": text}),
                    "anjal" => json!({"op": "unicode_to_anjal_bytes", "input": text}),
                    _ => json!({"op": "normalize_nfc", "input": text}),
                }
            } else {
                match from_enc.as_str() {
                    "bamini" => json!({"op": "bamini_to_unicode", "input": text}),
                    _ => json!({"op": "normalize_nfc", "input": text}),
                }
            };

            match tamil_toolkit::execute(&req) {
                Ok(val) => {
                    if let Some(s) = val.as_str() {
                        println!("{s}");
                    } else {
                        println!("{val}");
                    }
                }
                Err(e) => {
                    eprintln!("Codec conversion error: {e}");
                    exit(1);
                }
            }
        }
        "detect" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for detect.");
                exit(1);
            }
            let text = &args[1];
            let req = json!({"op": "detect_encoding", "input": text});
            match tamil_toolkit::execute(&req) {
                Ok(val) => println!("{val}"),
                Err(e) => {
                    eprintln!("Detection error: {e}");
                    exit(1);
                }
            }
        }
        "-h" | "--help" => print_codec_usage(),
        other => {
            eprintln!("Error: Unknown codec subcommand '{other}'.");
            print_codec_usage();
            exit(1);
        }
    }
}

// ==========================================
// Collate Handlers
// ==========================================

fn print_collate_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit collate <SUBCOMMAND> [ARGUMENTS]

SUBCOMMANDS:
    compare <STR1> <STR2> [--profile PROFILE]            Compare two Tamil strings (-1, 0, 1)
    key <TEXT> [--profile PROFILE]                       Generate collation sort key
    search-key <TEXT> [--fold FOLD] [--profile PROFILE]  Generate folded search key
    sort <FILE> [--profile PROFILE]                      Sort lines of Tamil text from file
    -h, --help                                           Print help information
"#
    );
}

fn handle_collate(args: &[String]) {
    if args.is_empty() {
        print_collate_usage();
        exit(1);
    }
    match args[0].as_str() {
        "compare" => {
            let mut str1: Option<String> = None;
            let mut str2: Option<String> = None;
            let mut profile = tamil_collate::CollationProfile::AgaraV1;
            let mut i = 1;
            while i < args.len() {
                match args[i].as_str() {
                    "--profile" if i + 1 < args.len() => {
                        if let Ok(p) = args[i + 1].parse() {
                            profile = p;
                        }
                        i += 2;
                    }
                    s if !s.starts_with('-') => {
                        if str1.is_none() {
                            str1 = Some(s.to_string());
                        } else if str2.is_none() {
                            str2 = Some(s.to_string());
                        }
                        i += 1;
                    }
                    _ => {
                        i += 1;
                    }
                }
            }
            let (a, b) = match (str1, str2) {
                (Some(a), Some(b)) => (a, b),
                _ => {
                    eprintln!("Error: compare requires two string arguments.");
                    exit(1);
                }
            };
            let cmp = tamil_collate::compare_with_profile(&a, &b, profile);
            let res = match cmp {
                std::cmp::Ordering::Less => -1,
                std::cmp::Ordering::Equal => 0,
                std::cmp::Ordering::Greater => 1,
            };
            println!("{res}");
        }
        "key" => {
            let mut text: Option<String> = None;
            let mut profile = tamil_collate::CollationProfile::AgaraV1;
            let mut i = 1;
            while i < args.len() {
                match args[i].as_str() {
                    "--profile" if i + 1 < args.len() => {
                        if let Ok(p) = args[i + 1].parse() {
                            profile = p;
                        }
                        i += 2;
                    }
                    s if !s.starts_with('-') && text.is_none() => {
                        text = Some(s.to_string());
                        i += 1;
                    }
                    _ => {
                        i += 1;
                    }
                }
            }
            let text = match text {
                Some(t) => t,
                None => {
                    eprintln!("Error: Missing text argument for key.");
                    exit(1);
                }
            };
            let key = tamil_collate::sort_key_with_profile(&text, profile);
            println!(
                "{}",
                key.iter().map(|b| format!("{b:02x}")).collect::<String>()
            );
        }
        "search-key" => {
            let mut text: Option<String> = None;
            let mut fold_profile = tamil_norm::FoldingProfile::Comprehensive;
            let mut collate_profile = tamil_collate::CollationProfile::AgaraV1;
            let mut i = 1;
            while i < args.len() {
                match args[i].as_str() {
                    "--fold" if i + 1 < args.len() => {
                        if let Some(fp) = tamil_norm::FoldingProfile::parse(&args[i + 1]) {
                            fold_profile = fp;
                        }
                        i += 2;
                    }
                    "--profile" if i + 1 < args.len() => {
                        if let Ok(cp) = args[i + 1].parse() {
                            collate_profile = cp;
                        }
                        i += 2;
                    }
                    s if !s.starts_with('-') && text.is_none() => {
                        text = Some(s.to_string());
                        i += 1;
                    }
                    _ => {
                        i += 1;
                    }
                }
            }
            let text = match text {
                Some(t) => t,
                None => {
                    eprintln!("Error: Missing text argument for search-key.");
                    exit(1);
                }
            };
            let key =
                tamil_collate::folded_search_key_with_profile(&text, fold_profile, collate_profile);
            println!(
                "{}",
                key.iter().map(|b| format!("{b:02x}")).collect::<String>()
            );
        }
        "sort" => {
            let mut file_path: Option<String> = None;
            let mut profile = tamil_collate::CollationProfile::AgaraV1;
            let mut i = 1;
            while i < args.len() {
                match args[i].as_str() {
                    "--profile" if i + 1 < args.len() => {
                        if let Ok(p) = args[i + 1].parse() {
                            profile = p;
                        }
                        i += 2;
                    }
                    s if !s.starts_with('-') && file_path.is_none() => {
                        file_path = Some(s.to_string());
                        i += 1;
                    }
                    _ => {
                        i += 1;
                    }
                }
            }
            let file_path = match file_path {
                Some(p) => p,
                None => {
                    eprintln!("Error: Missing file argument for sort.");
                    exit(1);
                }
            };
            let content = match fs::read_to_string(&file_path) {
                Ok(c) => c,
                Err(e) => {
                    eprintln!("Failed to read file '{file_path}': {e}");
                    exit(1);
                }
            };
            let mut lines: Vec<String> = content.lines().map(str::to_string).collect();
            lines.sort_by(|a, b| tamil_collate::compare_with_profile(a, b, profile));
            for line in lines {
                println!("{line}");
            }
        }
        "-h" | "--help" => print_collate_usage(),
        other => {
            eprintln!("Error: Unknown collate subcommand '{other}'.");
            print_collate_usage();
            exit(1);
        }
    }
}

// ==========================================
// Numerals Handlers
// ==========================================

fn print_numerals_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit numerals <SUBCOMMAND> [ARGUMENTS]

SUBCOMMANDS:
    to-words <NUMBER>                       Convert integer to Tamil words
    to-numeral <NUMBER>                     Convert integer to Tamil numeral glyphs
    parse <WORDS_OR_GLYPHS>                 Parse Tamil numeral words or symbols to integer
    -h, --help                              Print help information
"#
    );
}

fn handle_numerals(args: &[String]) {
    if args.is_empty() {
        print_numerals_usage();
        exit(1);
    }
    match args[0].as_str() {
        "to-words" => {
            if args.len() < 2 {
                eprintln!("Error: Missing number argument.");
                exit(1);
            }
            let num: i64 = match args[1].parse() {
                Ok(n) => n,
                Err(_) => {
                    eprintln!("Error: Invalid integer '{}'", args[1]);
                    exit(1);
                }
            };
            match tamil_numerals::to_words(num, tamil_numerals::Locale::TN) {
                Ok(words) => println!("{words}"),
                Err(e) => {
                    eprintln!("Error: {e}");
                    exit(1);
                }
            }
        }
        "to-numeral" => {
            if args.len() < 2 {
                eprintln!("Error: Missing number argument.");
                exit(1);
            }
            let num: i64 = match args[1].parse() {
                Ok(n) => n,
                Err(_) => {
                    eprintln!("Error: Invalid integer '{}'", args[1]);
                    exit(1);
                }
            };
            match tamil_numerals::format_traditional_integer(num) {
                Ok(glyphs) => println!("{glyphs}"),
                Err(e) => {
                    eprintln!("Error: {e}");
                    exit(1);
                }
            }
        }
        "parse" => {
            if args.len() < 2 {
                eprintln!("Error: Missing words or glyphs argument.");
                exit(1);
            }
            let text = &args[1];
            if let Ok(n) = tamil_numerals::parse_traditional_integer(text) {
                println!("{n}");
            } else if let Ok(n) = tamil_numerals::words_to_number(text, tamil_numerals::Locale::TN)
                .or_else(|_| tamil_numerals::words_to_number(text, tamil_numerals::Locale::SL))
            {
                println!("{n}");
            } else {
                eprintln!("Error: Unable to parse Tamil numerals or number words '{text}'");
                exit(1);
            }
        }
        "-h" | "--help" => print_numerals_usage(),
        other => {
            eprintln!("Error: Unknown numerals subcommand '{other}'.");
            print_numerals_usage();
            exit(1);
        }
    }
}

// ==========================================
// Calendar Handlers
// ==========================================

fn print_calendar_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit calendar <SUBCOMMAND> [OPTIONS]

SUBCOMMANDS:
    info [--date YYYY-MM-DD]                Convert date and view Tamil calendar details
    -h, --help                              Print help information
"#
    );
}

fn handle_calendar(args: &[String]) {
    if args.is_empty() {
        print_calendar_usage();
        exit(1);
    }
    match args[0].as_str() {
        "info" => {
            let mut year = 2026i32;
            let mut i = 1;
            while i < args.len() {
                if (args[i] == "-d" || args[i] == "--date") && i + 1 < args.len() {
                    let parts: Vec<&str> = args[i + 1].split('-').collect();
                    if !parts.is_empty() {
                        year = parts[0].parse().unwrap_or(2026);
                    }
                    i += 2;
                } else {
                    i += 1;
                }
            }
            match tamil_calendar::solar_year_cycle_info(year as i64) {
                Ok(info) => println!(
                    "{}",
                    serde_json::to_string_pretty(&json!({
                        "solar_year": info.solar_year,
                        "cycle_index": info.cycle_index,
                        "cycle_name": info.cycle_name,
                    }))
                    .unwrap()
                ),
                Err(e) => {
                    eprintln!("Calendar error: {e}");
                    exit(1);
                }
            }
        }
        "-h" | "--help" => print_calendar_usage(),
        other => {
            eprintln!("Error: Unknown calendar subcommand '{other}'.");
            print_calendar_usage();
            exit(1);
        }
    }
}

// ==========================================
// Lexicon Handlers
// ==========================================

fn print_lexicon_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit lexicon <SUBCOMMAND> [OPTIONS] [ARGUMENTS]

SUBCOMMANDS:
    define <TEXT> [--profile open-lite|open|local|full] [--category CAT] [--pack-dir DIR] [--pack ID]... [--tier open|local|all] [--pos POS] [--domain DOM] [--region ID] [--register ID] [--folded]
                Unified, deduplicated word definition (meanings, domains, regional notes, variants, relations, provenance)
                Auto-discovers packs from TAMIL_LEXICON_DIR, ./dist/lexicon-packs, ./lexicon-packs, or ~/.tamil-toolkit/lexicon-packs
    doctor [--pack-dir DIR]
                Check discovered lexicon packs, profiles, categories, byte sizes, and setup status
    lookup <TEXT> [--pack ID]... [--region ID] [--register ID]
                Exact NFC-normalized lookup over embedded TMLPACK1 packs
    packs       List available embedded TMLPACK1 packs and coverage metadata
    query <TEXT> [--profile open-lite|open|local|full] [--category CAT] [--pack-dir DIR] [--pack ID]... [--tier open|local|all] [--pos POS] [--domain DOM] [--region ID] [--register ID] [--folded]
                Raw entry lookup over external TMLPACK1/TMLPACK2 packs (auto-discovers packs if --pack-dir omitted)
    search <PREFIX> [--profile open-lite|open|local|full] [--category CAT] [--pack-dir DIR] [--pack ID]... [--tier open|local|all] [--pos POS] [--domain DOM] [--region ID] [--register ID] [--folded] [--limit N] [--after KEY]
                FST prefix search / autocomplete over external packs with cursor pagination
    search-en <QUERY> [--profile open-lite|open|local|full] [--category CAT] [--pack-dir DIR] [--pack ID]... [--tier open|local|all] [--pos POS] [--domain DOM] [--region ID] [--register ID] [--limit N] [--json]
                Reverse English-to-Tamil gloss/definition search over external TMLPACK2 packs
    pull [--profile open-lite|open|full|local] [--pack ID]... [--dir DIR] [--manifest-url URL] [--force]
                Download and SHA-256-verify .tlpack v2 bundles using curl
    status [--dir DIR] [--json]
                Show discovered pack directory, installed packs, sizes, counts, and English index status
    verify [--dir DIR]
                Verify SHA-256 and TMLPACK2 integrity of installed packs against MANIFEST.json
    remove <PACK_ID> [--dir DIR]
                Remove an installed .tlpack file from the pack directory
    fuzzy <WORD> [--max-distance 1|2] [--profile ...] [--category CAT] [--limit N]
                Bounded Damerau-Levenshtein spelling suggestion search over external packs
    stems <WORD> [--profile ...] [--category CAT]
                Return exact FST prefix stems of WORD longest-first (for morphological splitting)
    relations <TEXT> [--profile open-lite|open|local|full] [--pack-dir DIR] [--pack ID]... [--tier open|local|all]
                Lookup indexed lexical relations (synonyms, antonyms, related, hypernyms)
    stats [--profile open-lite|open|local|full] [--pack-dir DIR]
                Show loaded external pack metadata, counts, byte sizes, categories, and rights tiers
    inspect <FILE.tlpack>
                Validate and print metadata for a single TMLPACK1/TMLPACK2 file
    compile <INPUT_DIR> --out <FILE.tlpack> [--no-folded]
                Compile an organized pack directory (manifest.json + entries.jsonl + relations.jsonl) into TMLPACK2
    compile-all <ORGANIZED_DIR> --out <OUT_DIR> [--no-folded]
                Compile all open/ and local/ packs under ORGANIZED_DIR into .tlpack v2 files + MANIFEST.json
    source-records <QUERY> --dir <HISTORICAL_DIR> [--offset N] [--limit N]
                Query raw 256-bucket historical source records
    -h, --help  Print help information
"#
    );
}

fn emit_lexicon_result(request: &serde_json::Value) {
    match tamil_toolkit::execute(request) {
        Ok(value) => {
            let encoded = serde_json::to_string(&value).unwrap_or_else(|err| {
                eprintln!("lexicon: serialize error: {err}");
                exit(1);
            });
            println!("{encoded}");
        }
        Err(err) => {
            eprintln!("{err}");
            exit(1);
        }
    }
}

fn mount_external_pack_dir(
    pack_dir: Option<&str>,
    profile: tamil_toolkit::lexicon::LexiconProfile,
) {
    if let Some(dir_str) = pack_dir {
        let p = Path::new(dir_str);
        let res = if p.is_dir() {
            tamil_toolkit::lexicon::init_runtime(profile, Some(p), true).map(|_| ())
        } else {
            tamil_toolkit::lexicon::load_pack_file(p).map(|_| ())
        };
        if let Err(err) = res {
            eprintln!("{err}");
            exit(1);
        }
        return;
    }

    if let Err(err) = tamil_toolkit::lexicon::init_runtime(profile, None, true) {
        eprintln!("{err}");
        exit(1);
    }
}

#[derive(serde::Deserialize)]
struct OrganizedPackManifest {
    pack_id: String,
    pack_tier: tamil_toolkit::lexicon::PackTier,
    rights_status: String,
    license: String,
    dataset_version: String,
    description: String,
    #[serde(default)]
    source_ids: Vec<String>,
    #[serde(default)]
    attribution_notice: String,
}

fn compile_organized_pack_dir(
    input_dir: &Path,
    out_file: &Path,
    build_folded_index: bool,
) -> Result<tamil_toolkit::lexicon::CompactPackSummary, String> {
    let manifest_raw = fs::read_to_string(input_dir.join("manifest.json")).map_err(|err| {
        format!(
            "failed to read manifest.json in '{}': {err}",
            input_dir.display()
        )
    })?;
    let manifest: OrganizedPackManifest = serde_json::from_str(&manifest_raw)
        .map_err(|err| format!("invalid manifest.json in '{}': {err}", input_dir.display()))?;

    let entries_path = input_dir.join("entries.jsonl");
    let mut entries = Vec::new();
    if entries_path.is_file() {
        let raw = fs::read_to_string(&entries_path)
            .map_err(|err| format!("failed to read '{}': {err}", entries_path.display()))?;
        for (line_no, line) in raw.lines().enumerate() {
            if line.trim().is_empty() {
                continue;
            }
            let entry: tamil_toolkit::lexicon::CompactEntry =
                serde_json::from_str(line).map_err(|err| {
                    format!(
                        "invalid entry JSON at {}:{}: {err}",
                        entries_path.display(),
                        line_no + 1
                    )
                })?;
            entries.push(entry);
        }
    }

    let relations_path = input_dir.join("relations.jsonl");
    let mut relations = Vec::new();
    if relations_path.is_file() {
        let raw = fs::read_to_string(&relations_path)
            .map_err(|err| format!("failed to read '{}': {err}", relations_path.display()))?;
        for (line_no, line) in raw.lines().enumerate() {
            if line.trim().is_empty() {
                continue;
            }
            let rel: tamil_toolkit::lexicon::CompactRelation =
                serde_json::from_str(line).map_err(|err| {
                    format!(
                        "invalid relation JSON at {}:{}: {err}",
                        relations_path.display(),
                        line_no + 1
                    )
                })?;
            relations.push(rel);
        }
    }

    let input = tamil_toolkit::lexicon::CompactPackInput {
        pack_id: manifest.pack_id,
        pack_tier: manifest.pack_tier,
        rights_status: manifest.rights_status,
        license: manifest.license,
        dataset_version: manifest.dataset_version,
        description: manifest.description,
        source_ids: manifest.source_ids,
        attribution_notice: manifest.attribution_notice,
        entries,
        relations,
        build_folded_index,
    };
    let bytes = tamil_toolkit::lexicon::build_compact_pack(&input)?;
    let loaded = tamil_toolkit::lexicon::LoadedPack::parse_bytes(bytes.clone())?;
    let summary = loaded.summary();
    if let Some(parent) = out_file.parent() {
        fs::create_dir_all(parent)
            .map_err(|err| format!("failed to create '{}': {err}", parent.display()))?;
    }
    fs::write(out_file, &bytes)
        .map_err(|err| format!("failed to write '{}': {err}", out_file.display()))?;
    Ok(summary)
}

fn handle_lexicon(args: &[String]) {
    if args.is_empty() {
        print_lexicon_usage();
        exit(1);
    }

    match args[0].as_str() {
        "packs" => {
            if args[1..]
                .iter()
                .any(|arg| matches!(arg.as_str(), "-h" | "--help"))
            {
                print_lexicon_usage();
                return;
            }
            if let Some(arg) = args.get(1) {
                eprintln!("Error: Unrecognized option or argument '{arg}'.");
                exit(1);
            }
            emit_lexicon_result(&json!({
                "op": "lexicon_packs",
                "input": serde_json::Value::Null
            }));
        }
        "lookup" => {
            let mut text: Option<String> = None;
            let mut packs: Vec<String> = Vec::new();
            let mut has_packs = false;
            let mut region: Option<String> = None;
            let mut register: Option<String> = None;
            let mut after_double_dash = false;
            let mut i = 1usize;

            while i < args.len() {
                let arg = &args[i];
                if after_double_dash {
                    if text.is_some() {
                        eprintln!("Error: Unexpected positional argument '{arg}'.");
                        exit(1);
                    }
                    text = Some(arg.clone());
                    i += 1;
                    continue;
                }

                match arg.as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--" => {
                        after_double_dash = true;
                        i += 1;
                    }
                    "--pack" => {
                        if i + 1 >= args.len() {
                            eprintln!("Error: --pack requires a pack ID value.");
                            exit(1);
                        }
                        has_packs = true;
                        packs.push(args[i + 1].clone());
                        i += 2;
                    }
                    "--region" => {
                        if i + 1 >= args.len() {
                            eprintln!("Error: --region requires a region code value.");
                            exit(1);
                        }
                        if region.is_some() {
                            eprintln!("lexicon: invalid options");
                            exit(1);
                        }
                        region = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--register" => {
                        if i + 1 >= args.len() {
                            eprintln!("Error: --register requires a register code value.");
                            exit(1);
                        }
                        if register.is_some() {
                            eprintln!("lexicon: invalid options");
                            exit(1);
                        }
                        register = Some(args[i + 1].clone());
                        i += 2;
                    }
                    other if other.starts_with('-') => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                    positional => {
                        if text.is_some() {
                            eprintln!("Error: Unexpected positional argument '{positional}'.");
                            exit(1);
                        }
                        text = Some(positional.to_owned());
                        i += 1;
                    }
                }
            }

            let Some(query_text) = text else {
                eprintln!("Error: Missing <TEXT> argument for lexicon lookup.");
                exit(1);
            };

            let mut req = serde_json::Map::new();
            req.insert("op".to_owned(), json!("lexicon_lookup"));
            req.insert("input".to_owned(), json!(query_text));
            if has_packs {
                req.insert("packs".to_owned(), json!(packs));
            }
            if let Some(reg) = region {
                req.insert("region".to_owned(), json!(reg));
            }
            if let Some(reg) = register {
                req.insert("register".to_owned(), json!(reg));
            }
            emit_lexicon_result(&serde_json::Value::Object(req));
        }
        "define" | "query" | "search" | "relations" | "fuzzy" | "stems" => {
            let sub = args[0].as_str();
            let mut text: Option<String> = None;
            let mut pack_dir: Option<String> = None;
            let mut profile = tamil_toolkit::lexicon::LexiconProfile::Full;
            let mut packs: Vec<String> = Vec::new();
            let mut tier: Option<String> = None;
            let mut category: Option<String> = None;
            let mut pos: Option<String> = None;
            let mut domain: Option<String> = None;
            let mut region: Option<String> = None;
            let mut register: Option<String> = None;
            let mut folded = false;
            let mut limit: Option<u64> = None;
            let mut after_key: Option<String> = None;
            let mut max_distance: Option<u64> = None;
            let mut i = 1usize;
            while i < args.len() {
                match args[i].as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--pack-dir" if i + 1 < args.len() => {
                        pack_dir = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--profile" if i + 1 < args.len() => {
                        profile = tamil_toolkit::lexicon::LexiconProfile::parse(&args[i + 1])
                            .unwrap_or_else(|| {
                                eprintln!(
                                    "Error: Unknown profile '{}'. Expected open-lite, open, local, or full.",
                                    args[i + 1]
                                );
                                exit(1);
                            });
                        i += 2;
                    }
                    "--pack" if i + 1 < args.len() => {
                        packs.push(args[i + 1].clone());
                        i += 2;
                    }
                    "--tier" if i + 1 < args.len() => {
                        tier = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--category" if i + 1 < args.len() => {
                        category = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--pos" if i + 1 < args.len() => {
                        pos = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--domain" if i + 1 < args.len() => {
                        domain = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--region" if i + 1 < args.len() => {
                        region = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--register" if i + 1 < args.len() => {
                        register = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--folded" => {
                        folded = true;
                        i += 1;
                    }
                    "--limit" if i + 1 < args.len() => {
                        limit = Some(args[i + 1].parse::<u64>().unwrap_or_else(|_| {
                            eprintln!("Error: --limit must be an integer.");
                            exit(1);
                        }));
                        i += 2;
                    }
                    "--after" if i + 1 < args.len() => {
                        after_key = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--max-distance" if i + 1 < args.len() => {
                        max_distance = Some(args[i + 1].parse::<u64>().unwrap_or_else(|_| {
                            eprintln!("Error: --max-distance must be an integer (1 or 2).");
                            exit(1);
                        }));
                        i += 2;
                    }
                    other if other.starts_with('-') => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                    positional => {
                        text = Some(positional.to_owned());
                        i += 1;
                    }
                }
            }
            let Some(query_text) = text else {
                eprintln!("Error: Missing <TEXT> argument for lexicon {sub}.");
                exit(1);
            };
            mount_external_pack_dir(pack_dir.as_deref(), profile);
            let op_name = match sub {
                "fuzzy" => "lexicon_fuzzy_search".to_owned(),
                "stems" => "lexicon_longest_prefix".to_owned(),
                other => format!("lexicon_{other}"),
            };
            let mut req = serde_json::Map::new();
            req.insert("op".to_owned(), json!(op_name));
            req.insert("input".to_owned(), json!(query_text));
            if !packs.is_empty() {
                req.insert("packs".to_owned(), json!(packs));
            }
            if let Some(t) = tier {
                req.insert("tier".to_owned(), json!(t));
            }
            if let Some(c) = category {
                req.insert("category".to_owned(), json!(c));
            }
            if let Some(p) = pos {
                req.insert("pos".to_owned(), json!(p));
            }
            if let Some(d) = domain {
                req.insert("domain".to_owned(), json!(d));
            }
            if let Some(r) = region {
                req.insert("region".to_owned(), json!(r));
            }
            if let Some(reg) = register {
                req.insert("register".to_owned(), json!(reg));
            }
            if folded {
                req.insert("folded".to_owned(), json!(true));
            }
            if let Some(l) = limit {
                req.insert("limit".to_owned(), json!(l));
            }
            if let Some(after) = after_key {
                req.insert("after_key".to_owned(), json!(after));
            }
            if let Some(md) = max_distance {
                req.insert("max_distance".to_owned(), json!(md));
            }
            emit_lexicon_result(&serde_json::Value::Object(req));
        }
        "doctor" => {
            let mut pack_dir: Option<String> = None;
            let mut i = 1usize;
            while i < args.len() {
                match args[i].as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--pack-dir" if i + 1 < args.len() => {
                        pack_dir = Some(args[i + 1].clone());
                        i += 2;
                    }
                    other => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                }
            }
            let env_override = env::var("TAMIL_LEXICON_DIR")
                .ok()
                .filter(|v| !v.trim().is_empty());
            let discovered = pack_dir
                .as_deref()
                .map(PathBuf::from)
                .or_else(tamil_toolkit::lexicon::auto_discover_pack_dir);
            let Some(dir) = discovered else {
                let report = json!({
                    "status": "missing_packs",
                    "discovered_dir": serde_json::Value::Null,
                    "env_override": env_override,
                    "pack_count": 0,
                    "setup_hint": "Run `just lexicon-build` to build dist/lexicon-packs or set TAMIL_LEXICON_DIR=/path/to/lexicon-packs"
                });
                println!("{}", serde_json::to_string_pretty(&report).unwrap());
                exit(1);
            };
            let mut reg = tamil_toolkit::lexicon::PackRegistry::new();
            match reg.load_pack_dir(&dir) {
                Ok(packs) => {
                    use std::collections::BTreeMap;
                    let mut by_category: BTreeMap<String, (usize, u64, usize)> = BTreeMap::new();
                    let mut open_packs = 0usize;
                    let mut open_bytes = 0usize;
                    let mut open_lite_packs = 0usize;
                    let mut open_lite_bytes = 0usize;
                    let mut local_packs = 0usize;
                    let mut local_bytes = 0usize;
                    let mut total_entries = 0u64;
                    let mut total_senses = 0u64;
                    let mut total_relations = 0u64;
                    let mut total_bytes = 0usize;
                    for p in &packs {
                        total_entries += u64::from(p.entry_count);
                        total_senses += u64::from(p.sense_count);
                        total_relations += u64::from(p.relation_count);
                        total_bytes += p.byte_len;
                        if p.pack_tier == tamil_toolkit::lexicon::PackTier::VerifiedOpen {
                            open_packs += 1;
                            open_bytes += p.byte_len;
                            if tamil_toolkit::lexicon::LexiconProfile::OpenLite
                                .includes_pack_stem(&p.pack_id, false)
                            {
                                open_lite_packs += 1;
                                open_lite_bytes += p.byte_len;
                            }
                        } else {
                            local_packs += 1;
                            local_bytes += p.byte_len;
                        }
                        let cat_entry = by_category
                            .entry(p.category.as_str().to_owned())
                            .or_insert((0, 0, 0));
                        cat_entry.0 += 1;
                        cat_entry.1 += u64::from(p.entry_count);
                        cat_entry.2 += p.byte_len;
                    }
                    let categories_json: serde_json::Map<String, serde_json::Value> = by_category
                        .into_iter()
                        .map(|(cat, (count, entries, bytes))| {
                            (
                                cat,
                                json!({
                                    "pack_count": count,
                                    "entries": entries,
                                    "bytes": bytes,
                                }),
                            )
                        })
                        .collect();
                    let report = json!({
                        "status": if packs.is_empty() { "missing_packs" } else { "ready" },
                        "discovered_dir": dir.to_string_lossy(),
                        "env_override": env_override,
                        "pack_count": packs.len(),
                        "total_entries": total_entries,
                        "total_senses": total_senses,
                        "total_relations": total_relations,
                        "total_bytes": total_bytes,
                        "profiles": {
                            "open-lite": { "pack_count": open_lite_packs, "bytes": open_lite_bytes },
                            "open": { "pack_count": open_packs, "bytes": open_bytes },
                            "local": { "pack_count": local_packs, "bytes": local_bytes },
                            "full": { "pack_count": packs.len(), "bytes": total_bytes },
                        },
                        "categories": categories_json,
                        "packs": packs,
                    });
                    println!("{}", serde_json::to_string_pretty(&report).unwrap());
                }
                Err(err) => {
                    eprintln!("{err}");
                    exit(1);
                }
            }
        }
        "stats" => {
            let mut pack_dir: Option<String> = None;
            let mut profile = tamil_toolkit::lexicon::LexiconProfile::Full;
            let mut i = 1usize;
            while i < args.len() {
                match args[i].as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--pack-dir" if i + 1 < args.len() => {
                        pack_dir = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--profile" if i + 1 < args.len() => {
                        profile = tamil_toolkit::lexicon::LexiconProfile::parse(&args[i + 1])
                            .unwrap_or_else(|| {
                                eprintln!(
                                    "Error: Unknown profile '{}'. Expected open-lite, open, local, or full.",
                                    args[i + 1]
                                );
                                exit(1);
                            });
                        i += 2;
                    }
                    other => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                }
            }
            mount_external_pack_dir(pack_dir.as_deref(), profile);
            emit_lexicon_result(&json!({
                "op": "lexicon_stats",
                "input": serde_json::Value::Null
            }));
        }
        "inspect" => {
            let Some(path) = args.get(1) else {
                eprintln!("Error: Missing <FILE.tlpack> path.");
                exit(1);
            };
            let bytes = fs::read(path).unwrap_or_else(|err| {
                eprintln!("Error reading '{path}': {err}");
                exit(1);
            });
            match tamil_toolkit::lexicon::LoadedPack::parse_bytes(bytes) {
                Ok(loaded) => {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&loaded.summary()).unwrap()
                    );
                }
                Err(err) => {
                    eprintln!("{err}");
                    exit(1);
                }
            }
        }
        "compile" => {
            let mut input_dir: Option<String> = None;
            let mut out_file: Option<String> = None;
            let mut build_folded = true;
            let mut i = 1usize;
            while i < args.len() {
                match args[i].as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--out" if i + 1 < args.len() => {
                        out_file = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--no-folded" => {
                        build_folded = false;
                        i += 1;
                    }
                    other if other.starts_with('-') => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                    positional => {
                        input_dir = Some(positional.to_owned());
                        i += 1;
                    }
                }
            }
            let (Some(in_dir), Some(out_path)) = (input_dir, out_file) else {
                eprintln!("Error: compile requires <INPUT_DIR> and --out <FILE.tlpack>.");
                exit(1);
            };
            match compile_organized_pack_dir(Path::new(&in_dir), Path::new(&out_path), build_folded)
            {
                Ok(summary) => {
                    println!("{}", serde_json::to_string_pretty(&summary).unwrap());
                }
                Err(err) => {
                    eprintln!("{err}");
                    exit(1);
                }
            }
        }
        "compile-all" => {
            let mut organized_dir: Option<String> = None;
            let mut out_dir: Option<String> = None;
            let mut build_folded = true;
            let mut i = 1usize;
            while i < args.len() {
                match args[i].as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--out" if i + 1 < args.len() => {
                        out_dir = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--no-folded" => {
                        build_folded = false;
                        i += 1;
                    }
                    other if other.starts_with('-') => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                    positional => {
                        organized_dir = Some(positional.to_owned());
                        i += 1;
                    }
                }
            }
            let (Some(org_dir), Some(out_root)) = (organized_dir, out_dir) else {
                eprintln!("Error: compile-all requires <ORGANIZED_DIR> and --out <OUT_DIR>.");
                exit(1);
            };
            let org_path = Path::new(&org_dir);
            let out_path = Path::new(&out_root);
            let mut manifest_packs = Vec::new();
            for track in ["open", "local"] {
                let track_dir = org_path.join(track);
                if !track_dir.is_dir() {
                    continue;
                }
                let mut subdirs: Vec<PathBuf> = fs::read_dir(&track_dir)
                    .unwrap_or_else(|err| {
                        eprintln!("Error reading '{}': {err}", track_dir.display());
                        exit(1);
                    })
                    .filter_map(Result::ok)
                    .map(|e| e.path())
                    .filter(|p| p.is_dir() && p.join("manifest.json").is_file())
                    .collect();
                subdirs.sort();
                for sub in subdirs {
                    let pack_name = sub
                        .file_name()
                        .and_then(|s| s.to_str())
                        .unwrap_or("pack")
                        .to_owned();
                    let rel_file = format!("{track}/{pack_name}.tlpack");
                    let target_file = out_path.join(&rel_file);
                    match compile_organized_pack_dir(&sub, &target_file, build_folded) {
                        Ok(summary) => {
                            manifest_packs.push(json!({
                                "file": rel_file,
                                "summary": summary,
                            }));
                        }
                        Err(err) => {
                            eprintln!("Error compiling '{}': {err}", sub.display());
                            exit(1);
                        }
                    }
                }
            }
            let manifest_json = json!({
                "schema_version": 2,
                "pack_count": manifest_packs.len(),
                "packs": manifest_packs,
            });
            fs::create_dir_all(out_path).unwrap_or_else(|err| {
                eprintln!("Error creating '{}': {err}", out_path.display());
                exit(1);
            });
            fs::write(
                out_path.join("MANIFEST.json"),
                serde_json::to_string_pretty(&manifest_json).unwrap() + "\n",
            )
            .unwrap_or_else(|err| {
                eprintln!("Error writing MANIFEST.json: {err}");
                exit(1);
            });
            println!("{}", serde_json::to_string_pretty(&manifest_json).unwrap());
        }
        "source-records" => {
            let mut query: Option<String> = None;
            let mut hist_dir: Option<String> = None;
            let mut offset: u64 = 0;
            let mut limit: u64 = 25;
            let mut i = 1usize;
            while i < args.len() {
                match args[i].as_str() {
                    "-h" | "--help" => {
                        print_lexicon_usage();
                        return;
                    }
                    "--dir" if i + 1 < args.len() => {
                        hist_dir = Some(args[i + 1].clone());
                        i += 2;
                    }
                    "--offset" if i + 1 < args.len() => {
                        offset = args[i + 1].parse().unwrap_or(0);
                        i += 2;
                    }
                    "--limit" if i + 1 < args.len() => {
                        limit = args[i + 1].parse().unwrap_or(25);
                        i += 2;
                    }
                    other if other.starts_with('-') => {
                        eprintln!("Error: Unrecognized option '{other}'.");
                        exit(1);
                    }
                    positional => {
                        query = Some(positional.to_owned());
                        i += 1;
                    }
                }
            }
            let (Some(q), Some(dir)) = (query, hist_dir) else {
                eprintln!("Error: source-records requires <QUERY> and --dir <HISTORICAL_DIR>.");
                exit(1);
            };
            let bucket_resp = tamil_toolkit::execute(&json!({
                "op": "lexicon_source_bucket",
                "input": q,
            }))
            .unwrap_or_else(|err| {
                eprintln!("{err}");
                exit(1);
            });
            let bucket_id = bucket_resp["bucket"].as_str().unwrap_or("00");
            let bucket_path = Path::new(&dir).join(format!("{bucket_id}.json"));
            let bucket_raw = fs::read_to_string(&bucket_path).unwrap_or_else(|err| {
                eprintln!("Error reading '{}': {err}", bucket_path.display());
                exit(1);
            });
            let bucket_json: serde_json::Value =
                serde_json::from_str(&bucket_raw).unwrap_or_else(|err| {
                    eprintln!("Error parsing '{}': {err}", bucket_path.display());
                    exit(1);
                });
            emit_lexicon_result(&json!({
                "op": "lexicon_source_lookup",
                "input": {
                    "query": q,
                    "bucket": bucket_json,
                    "offset": offset,
                    "limit": limit,
                }
            }));
        }
        "search-en" => handle_lexicon_search_en(&args[1..]),
        "pull" => handle_lexicon_pull(&args[1..]),
        "status" => handle_lexicon_status(&args[1..]),
        "verify" => handle_lexicon_verify(&args[1..]),
        "remove" => handle_lexicon_remove(&args[1..]),
        "-h" | "--help" => print_lexicon_usage(),
        other => {
            eprintln!("Error: Unknown lexicon subcommand '{other}'.");
            print_lexicon_usage();
            exit(1);
        }
    }
}

fn default_lexicon_dir() -> PathBuf {
    if let Ok(env_dir) = env::var("TAMIL_LEXICON_DIR") {
        let trimmed = env_dir.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    for home_var in ["HOME", "USERPROFILE"] {
        if let Ok(home) = env::var(home_var) {
            if !home.trim().is_empty() {
                return PathBuf::from(home)
                    .join(".tamil-toolkit")
                    .join("lexicon-packs");
            }
        }
    }
    PathBuf::from(".tamil-toolkit").join("lexicon-packs")
}

fn resolve_pack_dir(explicit: Option<&str>) -> PathBuf {
    if let Some(dir) = explicit {
        return PathBuf::from(dir);
    }
    if let Ok(env_dir) = env::var("TAMIL_LEXICON_DIR") {
        let trimmed = env_dir.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    tamil_toolkit::lexicon::auto_discover_pack_dir().unwrap_or_else(default_lexicon_dir)
}

fn default_manifest_url() -> String {
    if let Ok(url) = env::var("TAMIL_LEXICON_MANIFEST_URL") {
        let trimmed = url.trim();
        if !trimmed.is_empty() {
            return trimmed.to_owned();
        }
    }
    "https://github.com/abishtakan/tamil-toolkit/releases/latest/download/MANIFEST.json".to_owned()
}

fn sha256_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let digest = Sha256::digest(bytes);
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

fn run_curl_download(url: &str, dest: &Path) -> Result<(), String> {
    if let Some(parent) = dest.parent() {
        fs::create_dir_all(parent)
            .map_err(|err| format!("failed to create '{}': {err}", parent.display()))?;
    }
    let output = std::process::Command::new("curl")
        .args(["-fsSL", "-o"])
        .arg(dest)
        .arg(url)
        .output()
        .map_err(|err| {
            if err.kind() == std::io::ErrorKind::NotFound {
                "curl is required to download lexicon packs; please install curl and retry"
                    .to_owned()
            } else {
                format!("failed to invoke curl for '{url}': {err}")
            }
        })?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let msg = stderr.trim();
        return Err(if msg.is_empty() {
            format!("curl failed for '{url}' with status {}", output.status)
        } else {
            format!("curl failed for '{url}': {msg}")
        });
    }
    Ok(())
}

fn validate_safe_rel_path(rel: &str) -> Result<PathBuf, String> {
    let p = Path::new(rel);
    if p.is_absolute() {
        return Err(format!("unsafe absolute pack path in manifest: '{rel}'"));
    }
    let mut clean = PathBuf::new();
    for comp in p.components() {
        match comp {
            std::path::Component::Normal(part) => clean.push(part),
            _ => return Err(format!("unsafe relative pack path in manifest: '{rel}'")),
        }
    }
    if clean.as_os_str().is_empty() {
        return Err("empty pack path in manifest".to_owned());
    }
    Ok(clean)
}

fn manifest_pack_urls(
    manifest_url: &str,
    rel_file: &str,
    explicit_url: Option<&str>,
) -> Vec<String> {
    let mut urls = Vec::new();
    if let Some(u) = explicit_url.filter(|s| !s.trim().is_empty()) {
        urls.push(u.trim().to_owned());
    }
    let base = match manifest_url.rsplit_once('/') {
        Some((prefix, _)) => prefix,
        None => manifest_url,
    };
    let clean_rel = rel_file.trim_start_matches('/');
    urls.push(format!("{base}/{clean_rel}"));
    if let Some(file_name) = Path::new(clean_rel).file_name().and_then(|s| s.to_str()) {
        let flat = format!("{base}/{file_name}");
        if !urls.contains(&flat) {
            urls.push(flat);
        }
    }
    urls
}

fn verify_pack_bytes_and_checksum(
    bytes: &[u8],
    expected_checksum: &str,
    expected_file_sha256: Option<&str>,
) -> Result<tamil_toolkit::lexicon::CompactPackSummary, String> {
    if let Some(file_sha) = expected_file_sha256.filter(|s| !s.is_empty()) {
        let actual_file_sha = sha256_hex(bytes);
        if !actual_file_sha.eq_ignore_ascii_case(file_sha) {
            return Err(format!(
                "file SHA-256 mismatch: expected {file_sha}, got {actual_file_sha}"
            ));
        }
    }
    let loaded = tamil_toolkit::lexicon::LoadedPack::parse_bytes(bytes.to_vec())?;
    let summary = loaded.summary();
    if !summary
        .checksum_sha256
        .eq_ignore_ascii_case(expected_checksum)
    {
        return Err(format!(
            "pack '{}' TMLPACK2 SHA-256 mismatch: expected {}, got {}",
            summary.pack_id, expected_checksum, summary.checksum_sha256
        ));
    }
    Ok(summary)
}

fn atomic_replace_file(tmp: &Path, dest: &Path) -> Result<(), String> {
    if let Some(parent) = dest.parent() {
        fs::create_dir_all(parent)
            .map_err(|err| format!("failed to create '{}': {err}", parent.display()))?;
    }
    if dest.exists() {
        fs::remove_file(dest)
            .map_err(|err| format!("failed to replace '{}': {err}", dest.display()))?;
    }
    fs::rename(tmp, dest).map_err(|err| {
        format!(
            "failed to move '{}' to '{}': {err}",
            tmp.display(),
            dest.display()
        )
    })
}

fn collect_tlpack_paths(dir: &Path, out: &mut Vec<PathBuf>) -> Result<(), String> {
    let entries = fs::read_dir(dir)
        .map_err(|err| format!("failed to read directory '{}': {err}", dir.display()))?;
    for entry in entries {
        let entry = entry.map_err(|err| format!("directory entry error: {err}"))?;
        let path = entry.path();
        if path.is_dir() {
            collect_tlpack_paths(&path, out)?;
        } else if path.extension().and_then(|s| s.to_str()) == Some("tlpack") {
            out.push(path);
        }
    }
    out.sort();
    Ok(())
}

fn handle_lexicon_pull(args: &[String]) {
    let mut profile_opt: Option<tamil_toolkit::lexicon::LexiconProfile> = None;
    let mut requested_packs: Vec<String> = Vec::new();
    let mut dir_override: Option<String> = None;
    let mut manifest_url_override: Option<String> = None;
    let mut force = false;

    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                print_lexicon_usage();
                return;
            }
            "--profile" if i + 1 < args.len() => {
                profile_opt = Some(
                    tamil_toolkit::lexicon::LexiconProfile::parse(&args[i + 1]).unwrap_or_else(
                        || {
                            eprintln!(
                                "Error: Unknown profile '{}'. Expected open-lite, open, local, or full.",
                                args[i + 1]
                            );
                            exit(1);
                        },
                    ),
                );
                i += 2;
            }
            "--pack" if i + 1 < args.len() => {
                requested_packs.push(args[i + 1].clone());
                i += 2;
            }
            "--dir" if i + 1 < args.len() => {
                dir_override = Some(args[i + 1].clone());
                i += 2;
            }
            "--manifest-url" if i + 1 < args.len() => {
                manifest_url_override = Some(args[i + 1].clone());
                i += 2;
            }
            "--force" => {
                force = true;
                i += 1;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}' for lexicon pull.");
                exit(1);
            }
        }
    }

    let profile = profile_opt.unwrap_or(tamil_toolkit::lexicon::LexiconProfile::Open);
    let target_dir = dir_override
        .map(PathBuf::from)
        .unwrap_or_else(default_lexicon_dir);
    let manifest_url = manifest_url_override.unwrap_or_else(default_manifest_url);

    if let Err(err) = fs::create_dir_all(&target_dir) {
        eprintln!(
            "Error creating pack directory '{}': {err}",
            target_dir.display()
        );
        exit(1);
    }

    let manifest_tmp = target_dir.join("MANIFEST.json.tmp");
    if let Err(err) = run_curl_download(&manifest_url, &manifest_tmp) {
        let _ = fs::remove_file(&manifest_tmp);
        eprintln!("Error fetching manifest: {err}");
        exit(1);
    }
    let manifest_raw = fs::read_to_string(&manifest_tmp).unwrap_or_else(|err| {
        let _ = fs::remove_file(&manifest_tmp);
        eprintln!("Error reading downloaded manifest: {err}");
        exit(1);
    });
    let manifest_json: serde_json::Value =
        serde_json::from_str(&manifest_raw).unwrap_or_else(|err| {
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!("Error parsing MANIFEST.json: {err}");
            exit(1);
        });
    let Some(packs_arr) = manifest_json
        .get("packs")
        .and_then(serde_json::Value::as_array)
    else {
        let _ = fs::remove_file(&manifest_tmp);
        eprintln!("Error: MANIFEST.json missing 'packs' array.");
        exit(1);
    };

    let mut selected: Vec<&serde_json::Value> = Vec::new();
    if !requested_packs.is_empty() {
        for req_id in &requested_packs {
            let found = packs_arr.iter().find(|item| {
                item.get("summary")
                    .and_then(|s| s.get("pack_id"))
                    .and_then(serde_json::Value::as_str)
                    == Some(req_id.as_str())
            });
            let Some(item) = found else {
                let _ = fs::remove_file(&manifest_tmp);
                eprintln!("Error: Pack '{req_id}' not found in MANIFEST.json.");
                exit(1);
            };
            selected.push(item);
        }
    } else {
        for item in packs_arr {
            let summary = &item["summary"];
            let pack_id = summary["pack_id"].as_str().unwrap_or("");
            let tier = summary["pack_tier"].as_str().unwrap_or("");
            let is_local = tier == "local_historical";
            let include = match profile {
                tamil_toolkit::lexicon::LexiconProfile::OpenLite => {
                    !is_local
                        && tamil_toolkit::lexicon::LexiconProfile::OpenLite
                            .includes_pack_stem(pack_id, false)
                }
                tamil_toolkit::lexicon::LexiconProfile::Open => !is_local,
                tamil_toolkit::lexicon::LexiconProfile::Local => is_local,
                tamil_toolkit::lexicon::LexiconProfile::Full => true,
            };
            if include {
                selected.push(item);
            }
        }
    }

    if selected.is_empty() {
        let _ = fs::remove_file(&manifest_tmp);
        eprintln!(
            "Error: No packs matched selection (profile='{}') in MANIFEST.json.",
            profile.as_str()
        );
        exit(1);
    }

    for item in selected {
        let rel_file = item["file"].as_str().unwrap_or_else(|| {
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!("Error: Manifest pack entry missing 'file'.");
            exit(1);
        });
        let summary = &item["summary"];
        let pack_id = summary["pack_id"].as_str().unwrap_or("unknown");
        let expected_sha = summary["checksum_sha256"].as_str().unwrap_or_else(|| {
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!("Error: Manifest entry for '{pack_id}' missing 'checksum_sha256'.");
            exit(1);
        });
        let expected_file_sha = item.get("file_sha256").and_then(serde_json::Value::as_str);
        let rel_path = validate_safe_rel_path(rel_file).unwrap_or_else(|err| {
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!("Error: {err}");
            exit(1);
        });
        let dest = target_dir.join(&rel_path);

        if dest.is_file() && !force {
            if let Ok(existing_bytes) = fs::read(&dest) {
                if verify_pack_bytes_and_checksum(&existing_bytes, expected_sha, expected_file_sha)
                    .is_ok()
                {
                    println!(
                        "Skipping {pack_id} (already up to date at {})",
                        dest.display()
                    );
                    continue;
                }
            }
        }

        let tmp_dest = PathBuf::from(format!("{}.tmp", dest.display()));
        let explicit_url = item.get("url").and_then(serde_json::Value::as_str);
        let candidate_urls = manifest_pack_urls(&manifest_url, rel_file, explicit_url);
        let mut last_err = String::new();
        let mut downloaded = false;
        for url in &candidate_urls {
            match run_curl_download(url, &tmp_dest) {
                Ok(()) => {
                    downloaded = true;
                    break;
                }
                Err(err) => {
                    last_err = err;
                }
            }
        }
        if !downloaded {
            let _ = fs::remove_file(&tmp_dest);
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!("Error downloading pack '{pack_id}': {last_err}");
            exit(1);
        }

        let bytes = fs::read(&tmp_dest).unwrap_or_else(|err| {
            let _ = fs::remove_file(&tmp_dest);
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!(
                "Error reading downloaded pack '{}': {err}",
                tmp_dest.display()
            );
            exit(1);
        });
        let verified_summary =
            match verify_pack_bytes_and_checksum(&bytes, expected_sha, expected_file_sha) {
                Ok(s) => s,
                Err(err) => {
                    let _ = fs::remove_file(&tmp_dest);
                    let _ = fs::remove_file(&manifest_tmp);
                    eprintln!("Error verifying downloaded pack '{pack_id}': {err}");
                    exit(1);
                }
            };
        if let Err(err) = atomic_replace_file(&tmp_dest, &dest) {
            let _ = fs::remove_file(&tmp_dest);
            let _ = fs::remove_file(&manifest_tmp);
            eprintln!("Error installing pack '{pack_id}': {err}");
            exit(1);
        }
        println!(
            "Installed {} ({} entries, {} bytes) -> {}",
            verified_summary.pack_id,
            verified_summary.entry_count,
            verified_summary.byte_len,
            dest.display()
        );
    }

    if let Err(err) = atomic_replace_file(&manifest_tmp, &target_dir.join("MANIFEST.json")) {
        let _ = fs::remove_file(&manifest_tmp);
        eprintln!("Error saving MANIFEST.json: {err}");
        exit(1);
    }
}

fn handle_lexicon_status(args: &[String]) {
    let mut dir_override: Option<String> = None;
    let mut json_mode = false;
    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                print_lexicon_usage();
                return;
            }
            "--dir" | "--pack-dir" if i + 1 < args.len() => {
                dir_override = Some(args[i + 1].clone());
                i += 2;
            }
            "--json" => {
                json_mode = true;
                i += 1;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}' for lexicon status.");
                exit(1);
            }
        }
    }

    let dir = resolve_pack_dir(dir_override.as_deref());
    if !dir.is_dir() {
        if json_mode {
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "directory": dir.to_string_lossy(),
                    "exists": false,
                    "pack_count": 0,
                    "packs": [],
                }))
                .unwrap()
            );
        } else {
            println!("Pack directory does not exist: {}", dir.display());
            println!("Run `tamil-toolkit lexicon pull --profile open` to install packs.");
        }
        return;
    }

    let mut reg = tamil_toolkit::lexicon::PackRegistry::new();
    match reg.load_pack_dir(&dir) {
        Ok(packs) => {
            let stats = tamil_toolkit::lexicon::LexiconStore::stats(&reg);
            if json_mode {
                let payload = json!({
                    "directory": dir.to_string_lossy(),
                    "exists": true,
                    "pack_count": stats.pack_count,
                    "total_entries": stats.total_entries,
                    "total_senses": stats.total_senses,
                    "total_relations": stats.total_relations,
                    "total_bytes": stats.total_bytes,
                    "has_english_index": stats.has_english_index,
                    "category_counts": stats.category_counts,
                    "pos_counts": stats.pos_counts,
                    "domain_counts": stats.domain_counts,
                    "region_counts": stats.region_counts,
                    "register_counts": stats.register_counts,
                    "packs": packs,
                });
                println!("{}", serde_json::to_string_pretty(&payload).unwrap());
            } else {
                println!("Pack directory: {}", dir.display());
                println!(
                    "Installed packs: {} ({} entries, {} senses, {} relations, {} bytes, en_index={})",
                    stats.pack_count,
                    stats.total_entries,
                    stats.total_senses,
                    stats.total_relations,
                    stats.total_bytes,
                    stats.has_english_index
                );
                for p in &packs {
                    println!(
                        "  - {:<18} tier={:<16} entries={:<7} senses={:<7} rels={:<6} bytes={:<9} en_index={}",
                        p.pack_id,
                        p.pack_tier.as_str(),
                        p.entry_count,
                        p.sense_count,
                        p.relation_count,
                        p.byte_len,
                        p.has_english_index
                    );
                }
            }
        }
        Err(err) => {
            eprintln!("Error loading packs from '{}': {err}", dir.display());
            exit(1);
        }
    }
}

fn handle_lexicon_verify(args: &[String]) {
    let mut dir_override: Option<String> = None;
    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                print_lexicon_usage();
                return;
            }
            "--dir" | "--pack-dir" if i + 1 < args.len() => {
                dir_override = Some(args[i + 1].clone());
                i += 2;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}' for lexicon verify.");
                exit(1);
            }
        }
    }

    let dir = resolve_pack_dir(dir_override.as_deref());
    let manifest_path = dir.join("MANIFEST.json");
    if !manifest_path.is_file() {
        eprintln!("Error: MANIFEST.json not found in '{}'.", dir.display());
        exit(1);
    }
    let manifest_raw = fs::read_to_string(&manifest_path).unwrap_or_else(|err| {
        eprintln!("Error reading '{}': {err}", manifest_path.display());
        exit(1);
    });
    let manifest_json: serde_json::Value =
        serde_json::from_str(&manifest_raw).unwrap_or_else(|err| {
            eprintln!("Error parsing '{}': {err}", manifest_path.display());
            exit(1);
        });
    let Some(packs_arr) = manifest_json
        .get("packs")
        .and_then(serde_json::Value::as_array)
    else {
        eprintln!("Error: MANIFEST.json missing 'packs' array.");
        exit(1);
    };

    let mut expected_by_id: std::collections::BTreeMap<String, (String, Option<String>)> =
        std::collections::BTreeMap::new();
    for item in packs_arr {
        if let (Some(pid), Some(sha)) = (
            item.get("summary")
                .and_then(|s| s.get("pack_id"))
                .and_then(serde_json::Value::as_str),
            item.get("summary")
                .and_then(|s| s.get("checksum_sha256"))
                .and_then(serde_json::Value::as_str),
        ) {
            let file_sha = item
                .get("file_sha256")
                .and_then(serde_json::Value::as_str)
                .map(str::to_owned);
            expected_by_id.insert(pid.to_owned(), (sha.to_owned(), file_sha));
        }
    }

    let mut files = Vec::new();
    if let Err(err) = collect_tlpack_paths(&dir, &mut files) {
        eprintln!("Error: {err}");
        exit(1);
    }
    if files.is_empty() {
        eprintln!("Error: No .tlpack files found in '{}'.", dir.display());
        exit(1);
    }

    let mut verified_count = 0usize;
    let mut failed = false;
    for path in &files {
        let bytes = match fs::read(path) {
            Ok(b) => b,
            Err(err) => {
                eprintln!("FAIL {}: {err}", path.display());
                failed = true;
                continue;
            }
        };
        let loaded = match tamil_toolkit::lexicon::LoadedPack::parse_bytes(bytes.clone()) {
            Ok(p) => p,
            Err(err) => {
                eprintln!("FAIL {}: {err}", path.display());
                failed = true;
                continue;
            }
        };
        let summary = loaded.summary();
        let Some((expected_sha, expected_file_sha)) = expected_by_id.get(&summary.pack_id) else {
            eprintln!(
                "FAIL {}: pack_id '{}' not listed in MANIFEST.json",
                path.display(),
                summary.pack_id
            );
            failed = true;
            continue;
        };
        if let Err(err) =
            verify_pack_bytes_and_checksum(&bytes, expected_sha, expected_file_sha.as_deref())
        {
            eprintln!("FAIL {}: {err}", path.display());
            failed = true;
            continue;
        }
        println!("OK {} ({})", summary.pack_id, path.display());
        verified_count += 1;
    }

    if failed {
        exit(1);
    }
    println!(
        "Verified {verified_count} .tlpack pack(s) in {}.",
        dir.display()
    );
}

fn handle_lexicon_remove(args: &[String]) {
    let mut pack_id: Option<String> = None;
    let mut dir_override: Option<String> = None;
    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                print_lexicon_usage();
                return;
            }
            "--dir" | "--pack-dir" if i + 1 < args.len() => {
                dir_override = Some(args[i + 1].clone());
                i += 2;
            }
            other if other.starts_with('-') => {
                eprintln!("Error: Unrecognized option '{other}' for lexicon remove.");
                exit(1);
            }
            positional => {
                if pack_id.is_some() {
                    eprintln!("Error: Unexpected argument '{positional}'.");
                    exit(1);
                }
                pack_id = Some(positional.to_owned());
                i += 1;
            }
        }
    }
    let Some(target_id) = pack_id else {
        eprintln!("Error: Missing <PACK_ID> argument for lexicon remove.");
        exit(1);
    };
    let dir = resolve_pack_dir(dir_override.as_deref());
    if !dir.is_dir() {
        eprintln!("Error: Pack directory not found: '{}'.", dir.display());
        exit(1);
    }
    let mut files = Vec::new();
    if let Err(err) = collect_tlpack_paths(&dir, &mut files) {
        eprintln!("Error: {err}");
        exit(1);
    }
    let target_filename = format!("{target_id}.tlpack");
    let mut removed = 0usize;
    for path in files {
        let matches_stem = path
            .file_name()
            .and_then(|s| s.to_str())
            .is_some_and(|n| n == target_filename);
        let matches_meta = if !matches_stem {
            fs::read(&path)
                .ok()
                .and_then(|b| tamil_toolkit::lexicon::LoadedPack::parse_bytes(b).ok())
                .is_some_and(|p| p.pack_id() == target_id)
        } else {
            false
        };
        if matches_stem || matches_meta {
            if let Err(err) = fs::remove_file(&path) {
                eprintln!("Error removing '{}': {err}", path.display());
                exit(1);
            }
            println!("Removed {}", path.display());
            removed += 1;
        }
    }
    if removed == 0 {
        eprintln!(
            "Error: Pack '{target_id}' not found in '{}'.",
            dir.display()
        );
        exit(1);
    }
}

fn handle_lexicon_search_en(args: &[String]) {
    let mut query: Option<String> = None;
    let mut pack_dir: Option<String> = None;
    let mut profile = tamil_toolkit::lexicon::LexiconProfile::Full;
    let mut packs: Vec<String> = Vec::new();
    let mut tier: Option<String> = None;
    let mut category: Option<String> = None;
    let mut pos: Option<String> = None;
    let mut domain: Option<String> = None;
    let mut region: Option<String> = None;
    let mut register: Option<String> = None;
    let mut limit: Option<u64> = None;
    let mut json_mode = false;

    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                print_lexicon_usage();
                return;
            }
            "--pack-dir" | "--dir" if i + 1 < args.len() => {
                pack_dir = Some(args[i + 1].clone());
                i += 2;
            }
            "--profile" if i + 1 < args.len() => {
                profile = tamil_toolkit::lexicon::LexiconProfile::parse(&args[i + 1])
                    .unwrap_or_else(|| {
                        eprintln!(
                            "Error: Unknown profile '{}'. Expected open-lite, open, local, or full.",
                            args[i + 1]
                        );
                        exit(1);
                    });
                i += 2;
            }
            "--pack" if i + 1 < args.len() => {
                packs.push(args[i + 1].clone());
                i += 2;
            }
            "--tier" if i + 1 < args.len() => {
                tier = Some(args[i + 1].clone());
                i += 2;
            }
            "--category" if i + 1 < args.len() => {
                category = Some(args[i + 1].clone());
                i += 2;
            }
            "--pos" if i + 1 < args.len() => {
                pos = Some(args[i + 1].clone());
                i += 2;
            }
            "--domain" if i + 1 < args.len() => {
                domain = Some(args[i + 1].clone());
                i += 2;
            }
            "--region" if i + 1 < args.len() => {
                region = Some(args[i + 1].clone());
                i += 2;
            }
            "--register" if i + 1 < args.len() => {
                register = Some(args[i + 1].clone());
                i += 2;
            }
            "--limit" if i + 1 < args.len() => {
                limit = Some(args[i + 1].parse::<u64>().unwrap_or_else(|_| {
                    eprintln!("Error: --limit must be an integer.");
                    exit(1);
                }));
                i += 2;
            }
            "--json" => {
                json_mode = true;
                i += 1;
            }
            other if other.starts_with('-') => {
                eprintln!("Error: Unrecognized option '{other}'.");
                exit(1);
            }
            positional => {
                query = Some(match query {
                    Some(prev) => format!("{prev} {positional}"),
                    None => positional.to_owned(),
                });
                i += 1;
            }
        }
    }

    let Some(q) = query else {
        eprintln!("Error: Missing <QUERY> argument for lexicon search-en.");
        exit(1);
    };

    mount_external_pack_dir(pack_dir.as_deref(), profile);
    let mut req = serde_json::Map::new();
    req.insert("op".to_owned(), json!("lexicon_search_english"));
    req.insert("input".to_owned(), json!(q));
    if !packs.is_empty() {
        req.insert("packs".to_owned(), json!(packs));
    }
    if let Some(t) = tier {
        req.insert("tier".to_owned(), json!(t));
    }
    if let Some(c) = category {
        req.insert("category".to_owned(), json!(c));
    }
    if let Some(p) = pos {
        req.insert("pos".to_owned(), json!(p));
    }
    if let Some(d) = domain {
        req.insert("domain".to_owned(), json!(d));
    }
    if let Some(r) = region {
        req.insert("region".to_owned(), json!(r));
    }
    if let Some(reg) = register {
        req.insert("register".to_owned(), json!(reg));
    }
    if let Some(l) = limit {
        req.insert("limit".to_owned(), json!(l));
    }

    if json_mode {
        emit_lexicon_result(&serde_json::Value::Object(req));
        return;
    }

    match tamil_toolkit::execute(&serde_json::Value::Object(req)) {
        Ok(value) => {
            let hits = value["hits"].as_array().map(Vec::as_slice).unwrap_or(&[]);
            if hits.is_empty() {
                println!(
                    "No matches found for '{}'.",
                    value["prefix"].as_str().unwrap_or("")
                );
                return;
            }
            for hit in hits {
                let hw = hit["headword"].as_str().unwrap_or("");
                let pos_str = hit["pos"]
                    .as_array()
                    .map(|arr| {
                        arr.iter()
                            .filter_map(serde_json::Value::as_str)
                            .collect::<Vec<_>>()
                            .join(",")
                    })
                    .unwrap_or_default();
                let gloss = hit["preview_gloss"].as_str().unwrap_or("");
                let packs_str = hit["packs"]
                    .as_array()
                    .map(|arr| {
                        arr.iter()
                            .filter_map(serde_json::Value::as_str)
                            .collect::<Vec<_>>()
                            .join(",")
                    })
                    .unwrap_or_default();
                if pos_str.is_empty() {
                    println!("{hw} — {gloss} [{packs_str}]");
                } else {
                    println!("{hw} ({pos_str}) — {gloss} [{packs_str}]");
                }
            }
        }
        Err(err) => {
            eprintln!("{err}");
            exit(1);
        }
    }
}

// ==========================================
// Main Dispatcher
// ==========================================

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        exit(1);
    }

    match args[1].as_str() {
        "core" => handle_core(&args[2..]),
        "norm" => handle_norm(&args[2..]),
        "codec" => handle_codec(&args[2..]),
        "collate" => handle_collate(&args[2..]),
        "numerals" => handle_numerals(&args[2..]),
        "calendar" => handle_calendar(&args[2..]),
        "hyphen" => handle_hyphen(&args[2..]),
        "lexicon" => handle_lexicon(&args[2..]),
        "help" | "-h" | "--help" => {
            print_usage();
        }
        other => {
            eprintln!("Error: Unrecognized command '{other}'");
            print_usage();
            exit(1);
        }
    }
}
