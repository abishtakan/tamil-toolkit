use std::time::Instant;
use tamil_hyphen::{hyphenate_text, hyphenate_word, wrap_text};

fn main() {
    println!("=== Tamil Hyphenation Benchmarks ===");

    let word = "பல்கலைக்கழகம்";
    let text = "தமிழ்நாடு மற்றும் பல்கலைக்கழகம் ஆகிய இரண்டும் செழித்து வளர்கின்றன. சென்னை, மதுரை, கோயம்புத்தூர் ஆகிய நகரங்கள் சிறந்த மையங்கள்.";

    // Warmup
    for _ in 0..10_000 {
        let _ = hyphenate_word(word, None).unwrap();
        let _ = hyphenate_text(text, None).unwrap();
        let _ = wrap_text(text, 20, None).unwrap();
    }

    // Benchmark word hyphenation
    let iterations = 100_000;
    let start = Instant::now();
    for _ in 0..iterations {
        let _ = hyphenate_word(word, None).unwrap();
    }
    let duration = start.elapsed();
    let per_word_us = duration.as_micros() as f64 / iterations as f64;
    println!(
        "Word hyphenation ({}): {:.3} µs / op (target < 5.0 µs)",
        word, per_word_us
    );
    assert!(
        per_word_us < 5.0,
        "Word hyphenation exceeds 5µs limit: {:.3} µs",
        per_word_us
    );

    // Benchmark text soft-hyphenation
    let text_iterations = 20_000;
    let start = Instant::now();
    for _ in 0..text_iterations {
        let _ = hyphenate_text(text, None).unwrap();
    }
    let duration = start.elapsed();
    let per_text_us = duration.as_micros() as f64 / text_iterations as f64;
    println!(
        "Paragraph hyphenation: {:.3} µs / op (target < 100.0 µs)",
        per_text_us
    );
    assert!(
        per_text_us < 100.0,
        "Paragraph hyphenation exceeds 100µs limit: {:.3} µs",
        per_text_us
    );

    // Benchmark line wrapping
    let wrap_iterations = 20_000;
    let start = Instant::now();
    for _ in 0..wrap_iterations {
        let _ = wrap_text(text, 20, None).unwrap();
    }
    let duration = start.elapsed();
    let per_wrap_us = duration.as_micros() as f64 / wrap_iterations as f64;
    println!("Line wrapping: {:.3} µs / op", per_wrap_us);

    println!("All hyphenation performance targets met!");
}
