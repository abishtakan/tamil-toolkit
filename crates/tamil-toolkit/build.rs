//! Build script for offline compiled lexicon pack artifacts under `OUT_DIR`.
#![forbid(unsafe_code)]

mod build_lexicon;

use std::env;
use std::fs;
use std::path::Path;

fn feature_enabled(var: &str) -> bool {
    env::var_os(var).is_some()
}

fn main() {
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR missing");
    let out_dir = env::var("OUT_DIR").expect("OUT_DIR missing");
    let manifest_path = Path::new(&manifest_dir);
    let out_path = Path::new(&out_dir);

    let lexicon_dir = manifest_path.join("lexicon");
    let dict_dir = lexicon_dir.join("dictionary");
    let packs_dir = lexicon_dir.join("packs");
    let schemas_dir = manifest_path.join("schemas").join("lexicon");

    // Track package-local dictionary, optional pack directories, and schema inputs cleanly.
    if lexicon_dir.exists() {
        println!("cargo:rerun-if-changed={}", lexicon_dir.display());
    }
    emit_rerun_watches(&dict_dir);
    emit_rerun_watches(&packs_dir);
    emit_rerun_watches(&schemas_dir);
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=build_lexicon.rs");

    let pack_specs = [
        ("core", "CARGO_FEATURE_LEXICON_CORE", dict_dir),
        (
            "terminology",
            "CARGO_FEATURE_LEXICON_TERMINOLOGY",
            packs_dir.join("terminology"),
        ),
        (
            "names_taxa",
            "CARGO_FEATURE_LEXICON_NAMES_TAXA",
            packs_dir.join("names_taxa"),
        ),
        (
            "regional",
            "CARGO_FEATURE_LEXICON_REGIONAL",
            packs_dir.join("regional"),
        ),
    ];

    let mut enabled_features: Vec<&'static str> = Vec::new();
    let mut unapproved_enabled: Vec<&'static str> = Vec::new();
    let mut compiled_artifacts: Vec<(&'static str, String, build_lexicon::CompiledPackOutput)> =
        Vec::new();

    for (pack_id, feature_var, pack_dir) in pack_specs {
        if !feature_enabled(feature_var) {
            continue;
        }
        enabled_features.push(pack_id);
        let has_manifest = pack_id == "core" || pack_dir.join("packs.toml").is_file();
        if has_manifest {
            let compiled =
                build_lexicon::compile_pack_dir(&pack_dir, Some(&schemas_dir), Some(pack_id))
                    .unwrap_or_else(|err| {
                        panic!("failed to compile {pack_id} lexicon pack: {err}")
                    });
            let pack_filename = format!("pack_{pack_id}.tlpack");
            let pack_file = out_path.join(&pack_filename);
            fs::write(&pack_file, &compiled.bytes)
                .unwrap_or_else(|err| panic!("failed to write {}: {err}", pack_file.display()));
            compiled_artifacts.push((pack_id, pack_filename, compiled));
        } else {
            unapproved_enabled.push(pack_id);
        }
    }

    let generated_rs =
        render_generated_module(&enabled_features, &unapproved_enabled, &compiled_artifacts);
    fs::write(out_path.join("lexicon_packs.rs"), generated_rs)
        .expect("failed to write OUT_DIR/lexicon_packs.rs");
}

fn emit_rerun_watches(dir: &Path) {
    if !dir.exists() {
        return;
    }
    println!("cargo:rerun-if-changed={}", dir.display());
    if let Ok(entries) = fs::read_dir(dir) {
        let mut paths: Vec<_> = entries.filter_map(Result::ok).map(|e| e.path()).collect();
        paths.sort();
        for path in paths {
            if path.is_dir() {
                emit_rerun_watches(&path);
            } else {
                println!("cargo:rerun-if-changed={}", path.display());
            }
        }
    }
}

fn render_generated_module(
    enabled_features: &[&str],
    unapproved_enabled: &[&str],
    compiled_artifacts: &[(&'static str, String, build_lexicon::CompiledPackOutput)],
) -> String {
    let enabled_list = format_str_slice(enabled_features);
    let unapproved_list = format_str_slice(unapproved_enabled);

    let mut embedded_bytes = 0usize;
    let available_entries = if compiled_artifacts.is_empty() {
        "&[]".to_owned()
    } else {
        let mut body = String::new();
        for (_pack_id, pack_filename, artifact) in compiled_artifacts {
            embedded_bytes += artifact.bytes.len();
            body.push_str(&format!(
                "    EmbeddedPackArtifact {{\n\
                 \x20       id: {:?},\n\
                 \x20       dataset_version: {:?},\n\
                 \x20       schema_version: {},\n\
                 \x20       index_format_version: {},\n\
                 \x20       manifest_sha256: {:?},\n\
                 \x20       artifact_sha256: {:?},\n\
                 \x20       bytes: include_bytes!(concat!(env!(\"OUT_DIR\"), \"/{}\")),\n\
                 \x20   }},\n",
                artifact.pack_id,
                artifact.dataset_version,
                artifact.schema_version,
                artifact.index_format_version,
                artifact.manifest_sha256,
                artifact.artifact_sha256,
                pack_filename,
            ));
        }
        format!("&[\n{body}]")
    };

    format!(
        "// @generated by crates/tamil-toolkit/build.rs\n\
         pub const ENABLED_PACK_FEATURES: &[&str] = {enabled_list};\n\
         pub const UNAPPROVED_ENABLED_PACKS: &[&str] = {unapproved_list};\n\
         pub const EMBEDDED_PAYLOAD_BYTES: usize = {embedded_bytes};\n\
         pub const AVAILABLE_PACKS: &[EmbeddedPackArtifact] = {available_entries};\n"
    )
}

fn format_str_slice(items: &[&str]) -> String {
    if items.is_empty() {
        return "&[]".to_owned();
    }
    let body = items
        .iter()
        .map(|s| format!("{s:?}"))
        .collect::<Vec<_>>()
        .join(", ");
    format!("&[{body}]")
}
