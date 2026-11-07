use std::env;
use std::path::PathBuf;
use std::process::exit;
use tamil_hyphen::docx::process_docx_file;
use tamil_hyphen::types::HyphenationConfig;
use tamil_hyphen::{
    export_dic_file, generate_patterns, package_oxt, DicExportOptions, LiangEvaluator,
};

fn print_usage() {
    eprintln!(
        r#"tamil-toolkit CLI

USAGE:
    tamil-toolkit <COMMAND>

COMMANDS:
    hyphen export-dic [OPTIONS]     Export Frank Liang hyphenation dictionary (.dic)
    hyphen package-oxt [OPTIONS]    Package LibreOffice extension (.oxt)
    hyphen process-docx [OPTIONS]   Batch-hyphenate OpenXML Word (.docx) document
    help                            Print this message

Run 'tamil-toolkit <COMMAND> --help' for command-specific options.
"#
    );
}

fn print_export_dic_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit hyphen export-dic [OPTIONS]

OPTIONS:
    -o, --output <PATH>         Destination filepath [default: hyph_ta_IN.dic]
    -l, --lefthyphenmin <N>     Minimum characters before hyphen [default: 2]
    -r, --righthyphenmin <N>    Minimum characters after hyphen [default: 2]
    --verify                    Run verification after export
    -h, --help                  Print help information
"#
    );
}

fn print_package_oxt_usage() {
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
}

fn print_process_docx_usage() {
    eprintln!(
        r#"USAGE:
    tamil-toolkit hyphen process-docx [OPTIONS] --input <PATH>

OPTIONS:
    -i, --input <PATH>          Source .docx file to process
    -o, --output <PATH>         Destination .docx path (required unless --inplace is set)
    --inplace                   Overwrite input file atomically
    -l, --left-min <N>          Minimum characters before hyphen [default: 2]
    -r, --right-min <N>         Minimum characters after hyphen [default: 2]
    -v, --verbose               Print detailed processing statistics
    -h, --help                  Print help information
"#
    );
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        exit(1);
    }

    match args[1].as_str() {
        "hyphen" => {
            if args.len() < 3 {
                eprintln!("Error: Missing hyphen subcommand.");
                print_usage();
                exit(1);
            }
            match args[2].as_str() {
                "export-dic" => handle_export_dic(&args[3..]),
                "package-oxt" => handle_package_oxt(&args[3..]),
                "process-docx" => handle_process_docx(&args[3..]),
                "-h" | "--help" => {
                    print_usage();
                }
                other => {
                    eprintln!("Error: Unknown hyphen subcommand '{other}'.");
                    print_usage();
                    exit(1);
                }
            }
        }
        "-h" | "--help" | "help" => {
            print_usage();
        }
        other => {
            eprintln!("Error: Unknown command '{other}'.");
            print_usage();
            exit(1);
        }
    }
}

fn handle_export_dic(args: &[String]) {
    let mut output = PathBuf::from("hyph_ta_IN.dic");
    let mut left_min = 2usize;
    let mut right_min = 2usize;
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
                print_export_dic_usage();
                return;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}'");
                print_export_dic_usage();
                exit(1);
            }
        }
    }

    if let Some(parent) = output.parent() {
        if !parent.as_os_str().is_empty() {
            let _ = std::fs::create_dir_all(parent);
        }
    }

    let options = DicExportOptions {
        left_hyphen_min: left_min,
        right_hyphen_min: right_min,
    };

    let dict = generate_patterns(&options);
    let pattern_count = dict.patterns.len();

    if let Err(e) = export_dic_file(&dict, &output) {
        eprintln!("Error writing dictionary file {}: {e}", output.display());
        exit(1);
    }

    println!(
        "Successfully exported {} Frank Liang hyphenation patterns to {}",
        pattern_count,
        output.display()
    );
    println!(
        "LEFTHYPHENMIN: {}, RIGHTHYPHENMIN: {}, Enforced locales: ta-IN, ta-LK, ta-SG, ta-MY, ta",
        left_min, right_min
    );

    if verify {
        let evaluator = LiangEvaluator::new(&dict);
        let sample_words = [
            "தமிழ்நாடு",
            "பல்கலைக்கழகம்",
            "வணக்கம்",
            "தக்ஷிணம்",
            "ஸ்ரீரங்கம்",
            "அஃது",
        ];
        let mut passed = 0;
        for word in &sample_words {
            let (hyphenated, segs) = evaluator.hyphenate_word(word, "-");
            let mut valid = true;
            for seg in &segs {
                if seg.starts_with('\u{0BCD}') {
                    valid = false;
                }
                // Check if starts with pure consonant (consonant + virama not followed by another consonant onset like ஸ்ரீ or க்ஷ)
                let chars: Vec<char> = seg.chars().collect();
                if chars.len() >= 2 && chars[1] == '\u{0BCD}' {
                    // Check if it's a valid Grantha onset cluster (e.g. ஸ்ரீ or க்ஷ)
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
        println!("Verified {passed}/{} sample words with zero orthographic violations.", sample_words.len());
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
                print_package_oxt_usage();
                return;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}'");
                print_package_oxt_usage();
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
    let mut left_min = 2usize;
    let mut right_min = 2usize;
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
                print_process_docx_usage();
                return;
            }
            other => {
                eprintln!("Error: Unrecognized option '{other}'");
                print_process_docx_usage();
                exit(1);
            }
        }
    }

    let input_path = match input {
        Some(p) => p,
        None => {
            eprintln!("Error: Missing required option --input <PATH>.");
            print_process_docx_usage();
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
                print_process_docx_usage();
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
