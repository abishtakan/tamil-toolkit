use std::time::Instant;
use tamil_codec::{detect_encoding, detect_encoding_cids};

fn main() {
    println!("=== Tamil Codec Detection Micro-benchmarks ===");

    // 1KB TSCII buffer
    let tscii_chunk: [u8; 16] = [
        0xdf, 0xa9, 0xb3, 0xd4, 0x20, 0xbf, 0xb4, 0xa9, 0xbb, 0xb8, 0xb3, 0xb8, 0xb3, 0x20, 0xdf,
        0xa9,
    ];
    let mut tscii_1kb = Vec::with_capacity(1024);
    while tscii_1kb.len() + tscii_chunk.len() <= 1024 {
        tscii_1kb.extend_from_slice(&tscii_chunk);
    }

    // 1KB Bamini buffer
    let bamini_chunk = b"jkpo; vOj;Jf;fs; tuyhwwpr; rpwg;G kpf;fit. ";
    let mut bamini_1kb = Vec::with_capacity(1024);
    while bamini_1kb.len() + bamini_chunk.len() <= 1024 {
        bamini_1kb.extend_from_slice(bamini_chunk);
    }

    // 1KB UTF-8 buffer
    let utf8_chunk = "தமிழ் எழுத்துக்கள் வரலாற்றுச் சிறப்பு மிக்கவை. ".as_bytes();
    let mut utf8_1kb = Vec::with_capacity(1024);
    while utf8_1kb.len() + utf8_chunk.len() <= 1024 {
        utf8_1kb.extend_from_slice(utf8_chunk);
    }

    // 512 code units (1KB) LT-TM CID buffer
    let lt_tm_chunk: [u16; 8] = [
        0x00A1, 0x00A2, 0x00C4, 0x00E4, 0x00B5, 0x0020, 0x00A1, 0x00A2,
    ];
    let mut cids_1kb = Vec::with_capacity(512);
    while cids_1kb.len() + lt_tm_chunk.len() <= 512 {
        cids_1kb.extend_from_slice(&lt_tm_chunk);
    }

    // Warmup
    for _ in 0..10_000 {
        let _ = detect_encoding(&tscii_1kb);
        let _ = detect_encoding(&bamini_1kb);
        let _ = detect_encoding(&utf8_1kb);
        let _ = detect_encoding_cids(&cids_1kb);
    }

    // Benchmark TSCII 1KB
    let iterations = 50_000;
    let start = Instant::now();
    for _ in 0..iterations {
        let res = detect_encoding(&tscii_1kb);
        std::hint::black_box(res);
    }
    let elapsed = start.elapsed();
    let per_op_tscii = elapsed / iterations;
    println!(
        "detect_encoding (TSCII 1KB): {:?} per iteration",
        per_op_tscii
    );

    // Benchmark Bamini 1KB
    let start = Instant::now();
    for _ in 0..iterations {
        let res = detect_encoding(&bamini_1kb);
        std::hint::black_box(res);
    }
    let elapsed = start.elapsed();
    let per_op_bamini = elapsed / iterations;
    println!(
        "detect_encoding (Bamini 1KB): {:?} per iteration",
        per_op_bamini
    );

    // Benchmark UTF-8 1KB
    let start = Instant::now();
    for _ in 0..iterations {
        let res = detect_encoding(&utf8_1kb);
        std::hint::black_box(res);
    }
    let elapsed = start.elapsed();
    let per_op_utf8 = elapsed / iterations;
    println!(
        "detect_encoding (UTF-8 1KB): {:?} per iteration",
        per_op_utf8
    );

    // Benchmark CID 1KB
    let start = Instant::now();
    for _ in 0..iterations {
        let res = detect_encoding_cids(&cids_1kb);
        std::hint::black_box(res);
    }
    let elapsed = start.elapsed();
    let per_op_cids = elapsed / iterations;
    println!(
        "detect_encoding_cids (LT-TM 1KB): {:?} per iteration",
        per_op_cids
    );

    println!("All benchmarks completed.");
}
