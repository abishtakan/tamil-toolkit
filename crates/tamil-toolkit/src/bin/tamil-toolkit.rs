#![forbid(unsafe_code)]

use std::env;
use std::fs;
use std::path::PathBuf;
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
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for fold.");
                exit(1);
            }
            let text = &args[1];
            let profile = if args.len() >= 4 && args[2] == "--profile" {
                tamil_norm::FoldingProfile::parse(&args[3])
                    .unwrap_or(tamil_norm::FoldingProfile::Comprehensive)
            } else {
                tamil_norm::FoldingProfile::Comprehensive
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
    compare <STR1> <STR2>                   Compare two Tamil strings (-1, 0, 1)
    key <TEXT> [--profile PROFILE]          Generate collation sort key
    sort <FILE>                             Sort lines of Tamil text from file
    -h, --help                              Print help information
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
            if args.len() < 3 {
                eprintln!("Error: compare requires two string arguments.");
                exit(1);
            }
            let a = &args[1];
            let b = &args[2];
            let cmp = tamil_collate::compare(a, b);
            let res = match cmp {
                std::cmp::Ordering::Less => -1,
                std::cmp::Ordering::Equal => 0,
                std::cmp::Ordering::Greater => 1,
            };
            println!("{res}");
        }
        "key" => {
            if args.len() < 2 {
                eprintln!("Error: Missing text argument for key.");
                exit(1);
            }
            let text = &args[1];
            let key = tamil_collate::sort_key(text);
            println!(
                "{}",
                key.iter().map(|b| format!("{b:02x}")).collect::<String>()
            );
        }
        "sort" => {
            if args.len() < 2 {
                eprintln!("Error: Missing file argument for sort.");
                exit(1);
            }
            let file_path = &args[1];
            let content = match fs::read_to_string(file_path) {
                Ok(c) => c,
                Err(e) => {
                    eprintln!("Failed to read file '{file_path}': {e}");
                    exit(1);
                }
            };
            let mut lines: Vec<String> = content.lines().map(str::to_string).collect();
            lines.sort_by(|a, b| tamil_collate::compare(a, b));
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
            } else {
                eprintln!("Error: Unable to parse traditional numerals '{text}'");
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
