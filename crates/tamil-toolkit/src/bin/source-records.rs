#![forbid(unsafe_code)]

//! Deterministic exporter for owner-supplied historical source CSV records.
//!
//! Verifies all 12 frozen input files (length and SHA-256) before creating output,
//! indexes all 11 CSV files across 256 SHA-256 bucket JSON files with bounded memory,
//! writes `NOTICE.md`, and writes `manifest.json` last upon complete success.

use std::collections::{BTreeMap, HashSet};
use std::env;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::process::exit;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tamil_toolkit::source_records::{
    bucket_for_normalized, bucket_index_for_normalized, is_plain_csv_filename, DATA_STATUS,
    RIGHTS_STATUS, SCHEMA_VERSION,
};

const OWNER_DIRECTION: &str =
    "Explicit user request 2026-11-16; no third-party rights grant asserted";

const FROZEN_NON_CSV_FILE: &str = "primary_lexicon.fst";

const CSV_KEY_COLUMNS: [(&str, &str); 11] = [
    ("primary_lemmas.csv", "headword_ta"),
    ("primary_meanings.csv", "headword_ta"),
    ("primary_relationships.csv", "source_headword_ta"),
    ("secondary_archaic_literary_terms.csv", "term_ta"),
    ("secondary_dialect_colloquialisms.csv", "term_ta"),
    ("secondary_phrases_mwes.csv", "phrase_ta"),
    ("secondary_proper_names_toponyms.csv", "name_ta"),
    ("secondary_scientific_taxa.csv", "tamil_name"),
    ("secondary_specialized_technical_terms.csv", "term_ta"),
    (
        "secondary_transliterations_loanwords.csv",
        "transliterated_ta",
    ),
    ("unified_master_30col.csv", "headword_ta"),
];

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct FrozenManifestEntry {
    file: String,
    bytes: u64,
    sha256: String,
}

#[derive(Debug, Serialize)]
struct ExportRecord<'a> {
    source_file: &'a str,
    source_row: u64,
    lookup_key: &'a str,
    fields: &'a BTreeMap<String, String>,
}

#[derive(Debug, Serialize)]
struct ManifestFileEntry {
    file: String,
    rows: u64,
    sha256: String,
    bytes: u64,
}

#[derive(Debug, Serialize)]
struct ManifestBucketEntry {
    file: String,
    sha256: String,
    bytes: u64,
    records: u64,
}

#[derive(Debug, Serialize)]
struct OutputManifest {
    schema_version: u64,
    data_status: &'static str,
    rights_status: &'static str,
    total_records: u64,
    distinct_keys: u64,
    files: Vec<ManifestFileEntry>,
    buckets: BTreeMap<String, ManifestBucketEntry>,
    owner_direction: &'static str,
}

struct HashingWriter<W: Write> {
    inner: W,
    hasher: Sha256,
    bytes: u64,
}

impl<W: Write> HashingWriter<W> {
    fn new(inner: W) -> Self {
        Self {
            inner,
            hasher: Sha256::new(),
            bytes: 0,
        }
    }

    fn write_all_hashed(&mut self, buf: &[u8]) -> io::Result<()> {
        self.inner.write_all(buf)?;
        self.hasher.update(buf);
        self.bytes += buf.len() as u64;
        Ok(())
    }

    fn finish(mut self) -> io::Result<(u64, String)> {
        self.inner.flush()?;
        let digest = self.hasher.finalize();
        Ok((self.bytes, hex_lower(&digest)))
    }
}

fn hex_lower(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        out.push(HEX_CHARS[(b >> 4) as usize]);
        out.push(HEX_CHARS[(b & 0x0f) as usize]);
    }
    out
}

const HEX_CHARS: [char; 16] = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f',
];

fn is_valid_sha256_hex(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

fn is_safe_manifest_filename(name: &str) -> bool {
    !name.is_empty()
        && !name.starts_with('.')
        && !name.contains("..")
        && !name.contains(['/', '\\', ':', '\0'])
        && !name.chars().any(char::is_control)
}

fn lookup_column_for_csv(filename: &str) -> Option<&'static str> {
    CSV_KEY_COLUMNS
        .iter()
        .find(|(name, _)| *name == filename)
        .map(|(_, col)| *col)
}

fn is_expected_frozen_file(filename: &str) -> bool {
    filename == FROZEN_NON_CSV_FILE || lookup_column_for_csv(filename).is_some()
}

fn sha256_and_len(path: &Path) -> Result<(u64, String), String> {
    let meta = fs::symlink_metadata(path)
        .map_err(|e| format!("failed to stat {}: {e}", path.display()))?;
    if !meta.is_file() {
        return Err(format!(
            "frozen input is not a regular file: {}",
            path.display()
        ));
    }
    let mut file =
        File::open(path).map_err(|e| format!("failed to open {}: {e}", path.display()))?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 64 * 1024];
    let mut total_bytes: u64 = 0;
    loop {
        let read = file
            .read(&mut buf)
            .map_err(|e| format!("failed to read {}: {e}", path.display()))?;
        if read == 0 {
            break;
        }
        hasher.update(&buf[..read]);
        total_bytes += read as u64;
    }
    let digest = hasher.finalize();
    Ok((total_bytes, hex_lower(&digest)))
}

fn verify_frozen_inputs(
    source_dir: &Path,
    manifest_path: &Path,
) -> Result<Vec<FrozenManifestEntry>, String> {
    let src_meta = fs::metadata(source_dir)
        .map_err(|e| format!("invalid source directory {}: {e}", source_dir.display()))?;
    if !src_meta.is_dir() {
        return Err(format!(
            "source path is not a directory: {}",
            source_dir.display()
        ));
    }

    let manifest_text = fs::read_to_string(manifest_path)
        .map_err(|e| format!("failed to read manifest {}: {e}", manifest_path.display()))?;
    let entries: Vec<FrozenManifestEntry> = serde_json::from_str(&manifest_text)
        .map_err(|e| format!("invalid frozen manifest JSON: {e}"))?;

    if entries.len() != 12 {
        return Err(format!(
            "frozen manifest must contain exactly 12 entries, found {}",
            entries.len()
        ));
    }

    let mut seen = HashSet::with_capacity(12);
    for entry in &entries {
        if !is_safe_manifest_filename(&entry.file) {
            return Err(format!(
                "unsafe filename in frozen manifest: {:?}",
                entry.file
            ));
        }
        if !is_expected_frozen_file(&entry.file) {
            return Err(format!(
                "unexpected file in frozen manifest: {}",
                entry.file
            ));
        }
        if entry.file != FROZEN_NON_CSV_FILE && !is_plain_csv_filename(&entry.file) {
            return Err(format!(
                "unsafe CSV filename in frozen manifest: {}",
                entry.file
            ));
        }
        if !is_valid_sha256_hex(&entry.sha256) {
            return Err(format!(
                "invalid sha256 in frozen manifest for {}",
                entry.file
            ));
        }
        if !seen.insert(entry.file.as_str()) {
            return Err(format!(
                "duplicate entry in frozen manifest: {}",
                entry.file
            ));
        }
    }

    // Reject any extra .csv files in source_dir.
    let dir_entries = fs::read_dir(source_dir).map_err(|e| {
        format!(
            "failed to list source directory {}: {e}",
            source_dir.display()
        )
    })?;
    for dir_entry in dir_entries {
        let dir_entry = dir_entry.map_err(|e| format!("failed to read directory entry: {e}"))?;
        let name = dir_entry
            .file_name()
            .into_string()
            .map_err(|_| "non-UTF-8 filename in source directory".to_owned())?;
        if name.to_ascii_lowercase().ends_with(".csv") && lookup_column_for_csv(&name).is_none() {
            return Err(format!("extra CSV file in source directory: {name}"));
        }
    }

    // Verify all 12 frozen file lengths and SHA-256 hashes before writing output.
    for entry in &entries {
        let path = source_dir.join(&entry.file);
        let (actual_bytes, actual_sha256) = sha256_and_len(&path)?;
        if actual_bytes != entry.bytes || actual_sha256 != entry.sha256 {
            return Err(format!(
                "frozen checksum/length mismatch for {}: expected ({} bytes, {}), got ({} bytes, {})",
                entry.file, entry.bytes, entry.sha256, actual_bytes, actual_sha256
            ));
        }
    }

    Ok(entries)
}

fn create_new_file(path: &Path) -> Result<File, String> {
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|e| format!("failed to create {}: {e}", path.display()))
}

fn remove_temp_shards(shard_paths: &[PathBuf]) {
    for path in shard_paths {
        let _ = fs::remove_file(path);
    }
}

fn export_bundle(source_dir: &Path, manifest_path: &Path, output_dir: &Path) -> Result<(), String> {
    if fs::symlink_metadata(output_dir).is_ok() {
        return Err(format!(
            "output directory already exists (refusing to overwrite): {}",
            output_dir.display()
        ));
    }

    let mut frozen_entries = verify_frozen_inputs(source_dir, manifest_path)?;
    frozen_entries.sort_by(|a, b| a.file.cmp(&b.file));

    // Create output directory only after all 12 inputs pass verification.
    if let Some(parent) = output_dir.parent() {
        if !parent.as_os_str().is_empty() && !parent.exists() {
            return Err(format!(
                "parent directory of output does not exist: {}",
                parent.display()
            ));
        }
    }
    fs::create_dir(output_dir).map_err(|e| {
        format!(
            "failed to create output directory {}: {e}",
            output_dir.display()
        )
    })?;

    let mut shard_paths = Vec::with_capacity(16);
    for shard_idx in 0..16u8 {
        shard_paths.push(output_dir.join(format!("._shard_{shard_idx:x}.tmp")));
    }

    let result = export_inner(source_dir, output_dir, &frozen_entries, &shard_paths);
    remove_temp_shards(&shard_paths);
    result
}

fn export_inner(
    source_dir: &Path,
    output_dir: &Path,
    frozen_entries: &[FrozenManifestEntry],
    shard_paths: &[PathBuf],
) -> Result<(), String> {
    let mut shard_writers: Vec<BufWriter<File>> = Vec::with_capacity(16);
    for path in shard_paths {
        let file = create_new_file(path)?;
        shard_writers.push(BufWriter::with_capacity(64 * 1024, file));
    }

    let mut file_entries: Vec<ManifestFileEntry> = Vec::with_capacity(11);
    let mut total_records: u64 = 0;

    for entry in frozen_entries {
        if entry.file == FROZEN_NON_CSV_FILE {
            continue;
        }
        let key_col = lookup_column_for_csv(&entry.file)
            .ok_or_else(|| format!("missing lookup column mapping for {}", entry.file))?;
        let csv_path = source_dir.join(&entry.file);
        let rows = stream_csv_into_shards(&csv_path, &entry.file, key_col, &mut shard_writers)?;
        total_records += rows;
        file_entries.push(ManifestFileEntry {
            file: entry.file.clone(),
            rows,
            sha256: entry.sha256.clone(),
            bytes: entry.bytes,
        });
    }

    for writer in &mut shard_writers {
        writer
            .flush()
            .map_err(|e| format!("failed to flush shard buffer: {e}"))?;
    }
    drop(shard_writers);

    let mut buckets_manifest: BTreeMap<String, ManifestBucketEntry> = BTreeMap::new();
    let mut distinct_keys: u64 = 0;

    for (shard_idx, shard_path) in shard_paths.iter().enumerate() {
        let (shard_distinct, shard_buckets) =
            finalize_shard(output_dir, shard_idx as u8, shard_path)?;
        distinct_keys += shard_distinct;
        buckets_manifest.extend(shard_buckets);
        let _ = fs::remove_file(shard_path);
    }

    write_notice(output_dir)?;

    let manifest = OutputManifest {
        schema_version: SCHEMA_VERSION,
        data_status: DATA_STATUS,
        rights_status: RIGHTS_STATUS,
        total_records,
        distinct_keys,
        files: file_entries,
        buckets: buckets_manifest,
        owner_direction: OWNER_DIRECTION,
    };

    // Write manifest last so any failure leaves no usable manifest.
    let manifest_file = create_new_file(&output_dir.join("manifest.json"))?;
    let mut manifest_writer = BufWriter::new(manifest_file);
    serde_json::to_writer_pretty(&mut manifest_writer, &manifest)
        .map_err(|e| format!("failed to serialize manifest.json: {e}"))?;
    manifest_writer
        .write_all(b"\n")
        .and_then(|()| manifest_writer.flush())
        .map_err(|e| format!("failed to write manifest.json: {e}"))?;

    Ok(())
}

fn stream_csv_into_shards(
    csv_path: &Path,
    filename: &str,
    key_col: &str,
    shard_writers: &mut [BufWriter<File>],
) -> Result<u64, String> {
    let file =
        File::open(csv_path).map_err(|e| format!("failed to open {}: {e}", csv_path.display()))?;
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .flexible(false)
        .trim(csv::Trim::None)
        .from_reader(BufReader::with_capacity(64 * 1024, file));

    let headers: Vec<String> = reader
        .headers()
        .map_err(|e| format!("failed to read CSV headers in {filename}: {e}"))?
        .iter()
        .map(str::to_owned)
        .collect();

    if headers.is_empty() {
        return Err(format!("empty CSV header in {filename}"));
    }

    let mut header_set = HashSet::with_capacity(headers.len());
    for header in &headers {
        if !header_set.insert(header.as_str()) {
            return Err(format!(
                "duplicate CSV header column '{header}' in {filename}"
            ));
        }
    }

    let key_idx = headers
        .iter()
        .position(|h| h == key_col)
        .ok_or_else(|| format!("missing primary lookup column '{key_col}' in {filename}"))?;
    let sci_idx = headers.iter().position(|h| h == "scientific_name");

    let mut row_num: u64 = 0;
    let mut raw_record = csv::StringRecord::new();
    let mut fields: BTreeMap<String, String> = BTreeMap::new();

    while reader
        .read_record(&mut raw_record)
        .map_err(|e| format!("CSV parse error in {filename} after row {row_num}: {e}"))?
    {
        row_num += 1;
        if raw_record.len() != headers.len() {
            return Err(format!(
                "wrong CSV row width in {filename}:{row_num}: expected {}, got {}",
                headers.len(),
                raw_record.len()
            ));
        }

        let primary_val = &raw_record[key_idx];
        let fallback_owned: String;
        let selected_key = if !primary_val.is_empty() {
            primary_val
        } else if let Some(idx) = sci_idx.filter(|&i| !raw_record[i].is_empty()) {
            &raw_record[idx]
        } else {
            fallback_owned = format!("{filename}:{row_num}");
            &fallback_owned
        };

        let lookup_key = tamil_norm::normalize_nfc(selected_key);
        if lookup_key.is_empty() {
            return Err(format!(
                "empty normalized lookup_key at {filename}:{row_num}"
            ));
        }

        let bucket_idx = bucket_index_for_normalized(&lookup_key);
        let bucket_hex = bucket_for_normalized(&lookup_key);
        let shard_idx = (bucket_idx >> 4) as usize;

        fields.clear();
        for (idx, header) in headers.iter().enumerate() {
            fields.insert(header.clone(), raw_record[idx].to_owned());
        }

        let rec = ExportRecord {
            source_file: filename,
            source_row: row_num,
            lookup_key: &lookup_key,
            fields: &fields,
        };
        let key_json = serde_json::to_string(&lookup_key)
            .map_err(|e| format!("JSON serialize error for key in {filename}:{row_num}: {e}"))?;
        let rec_json = serde_json::to_string(&rec)
            .map_err(|e| format!("JSON serialize error in {filename}:{row_num}: {e}"))?;

        let writer = &mut shard_writers[shard_idx];
        writer
            .write_all(bucket_hex.as_bytes())
            .and_then(|()| writer.write_all(b"\t"))
            .and_then(|()| writer.write_all(key_json.as_bytes()))
            .and_then(|()| writer.write_all(b"\t"))
            .and_then(|()| writer.write_all(rec_json.as_bytes()))
            .and_then(|()| writer.write_all(b"\n"))
            .map_err(|e| format!("failed to write shard for {filename}:{row_num}: {e}"))?;
    }

    Ok(row_num)
}

fn finalize_shard(
    output_dir: &Path,
    shard_idx: u8,
    shard_path: &Path,
) -> Result<(u64, BTreeMap<String, ManifestBucketEntry>), String> {
    let mut bucket_writers: Vec<HashingWriter<BufWriter<File>>> = Vec::with_capacity(16);
    let mut bucket_names: Vec<String> = Vec::with_capacity(16);
    let mut bucket_counts = [0u64; 16];
    let mut bucket_keys: Vec<HashSet<String>> = (0..16).map(|_| HashSet::new()).collect();

    for low in 0..16u8 {
        let bucket_id = format!("{:02x}", (shard_idx << 4) | low);
        let file_name = format!("{bucket_id}.json");
        let file = create_new_file(&output_dir.join(&file_name))?;
        let mut hw = HashingWriter::new(BufWriter::with_capacity(64 * 1024, file));
        let header = format!(
            "{{\"schema_version\":{SCHEMA_VERSION},\"bucket\":\"{bucket_id}\",\"records\":["
        );
        hw.write_all_hashed(header.as_bytes())
            .map_err(|e| format!("failed to write bucket header {file_name}: {e}"))?;
        bucket_writers.push(hw);
        bucket_names.push(bucket_id);
    }

    let shard_file = File::open(shard_path)
        .map_err(|e| format!("failed to reopen shard {}: {e}", shard_path.display()))?;
    let mut reader = BufReader::with_capacity(64 * 1024, shard_file);
    let mut line = String::new();

    loop {
        line.clear();
        let read = reader
            .read_line(&mut line)
            .map_err(|e| format!("failed to read shard {}: {e}", shard_path.display()))?;
        if read == 0 {
            break;
        }
        let trimmed = line.trim_end_matches(&['\r', '\n'][..]);
        let mut parts = trimmed.splitn(3, '\t');
        let bucket_hex = parts
            .next()
            .ok_or_else(|| "corrupt shard record: missing bucket".to_owned())?;
        let key_json = parts
            .next()
            .ok_or_else(|| "corrupt shard record: missing key".to_owned())?;
        let rec_json = parts
            .next()
            .ok_or_else(|| "corrupt shard record: missing payload".to_owned())?;

        let bucket_byte = u8::from_str_radix(bucket_hex, 16)
            .map_err(|_| format!("corrupt bucket id in shard: {bucket_hex}"))?;
        if (bucket_byte >> 4) != shard_idx {
            return Err(format!("shard mismatch for bucket {bucket_hex}"));
        }
        let low = (bucket_byte & 0x0f) as usize;
        let key: String = serde_json::from_str(key_json)
            .map_err(|e| format!("corrupt key JSON in shard: {e}"))?;
        bucket_keys[low].insert(key);

        let hw = &mut bucket_writers[low];
        if bucket_counts[low] > 0 {
            hw.write_all_hashed(b",")
                .map_err(|e| format!("failed to write bucket {bucket_hex}: {e}"))?;
        }
        hw.write_all_hashed(rec_json.as_bytes())
            .map_err(|e| format!("failed to write bucket {bucket_hex}: {e}"))?;
        bucket_counts[low] += 1;
    }

    let mut entries = BTreeMap::new();
    let mut distinct_sum = 0u64;

    for (low, (mut hw, bucket_id)) in bucket_writers.into_iter().zip(bucket_names).enumerate() {
        hw.write_all_hashed(b"]}")
            .map_err(|e| format!("failed to close bucket {bucket_id}: {e}"))?;
        let (bytes, sha256) = hw
            .finish()
            .map_err(|e| format!("failed to flush bucket {bucket_id}: {e}"))?;
        let file = format!("{bucket_id}.json");
        distinct_sum += bucket_keys[low].len() as u64;
        entries.insert(
            bucket_id,
            ManifestBucketEntry {
                file,
                sha256,
                bytes,
                records: bucket_counts[low],
            },
        );
    }

    Ok((distinct_sum, entries))
}

fn write_notice(output_dir: &Path) -> Result<(), String> {
    let notice = format!(
        "# Owner-Supplied Historical Source Records Notice\n\n\
         - `data_status`: `{DATA_STATUS}`\n\
         - `rights_status`: `{RIGHTS_STATUS}`\n\
         - `owner_direction`: `{OWNER_DIRECTION}`\n\n\
         This artifact is a deterministic, cell-preserving export of the 12 frozen\n\
         owner-supplied historical lexicon files (11 CSV tables indexed across 256\n\
         SHA-256 bucket files, plus `primary_lexicon.fst` verified by byte length\n\
         and SHA-256 and not used for queries).\n\n\
         No linguistic verification, accepted dictionary claims, regional scope\n\
         inferences, or newly asserted content licenses are made by this export.\n\
         Verified MIT/CC-BY-SA-4.0 package metadata does not relicense these\n\
         historical records.\n"
    );
    let mut file = create_new_file(&output_dir.join("NOTICE.md"))?;
    file.write_all(notice.as_bytes())
        .and_then(|()| file.flush())
        .map_err(|e| format!("failed to write NOTICE.md: {e}"))
}

fn print_usage() {
    eprintln!("USAGE:\n    source-records <source-dir> <frozen-manifest> <new-output-dir>\n");
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() == 1 && matches!(args[0].as_str(), "-h" | "--help") {
        print_usage();
        return;
    }
    if args.len() != 3 {
        print_usage();
        exit(2);
    }

    let source_dir = Path::new(&args[0]);
    let manifest_path = Path::new(&args[1]);
    let output_dir = Path::new(&args[2]);

    if let Err(err) = export_bundle(source_dir, manifest_path, output_dir) {
        eprintln!("source-records error: {err}");
        exit(1);
    }
}
