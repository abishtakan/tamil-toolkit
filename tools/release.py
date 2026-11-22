"""Build and verify release artifacts. Never uploads to a registry."""

import argparse
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
import zipfile

try:
    from release_files import (
        DICTIONARY_FILES,
        DICTIONARY_PACK_PROFILES,
        DICTIONARY_SCHEMAS,
        PUBLIC,
        ROOT,
        VERSION,
        artifact_license_spdx,
        artifact_notice_paths,
        copy_profile_notices,
        sync,
    )
    from release_policy import archive_paths, check, load
    from tasks import (
        LexiconProfile,
        load_pack_manifest,
        maturin_feature_args,
        profile_env,
        resolve_lexicon_profile,
        wasm_pack_build_command,
    )
except ModuleNotFoundError:
    from tools.release_files import (
        DICTIONARY_FILES,
        DICTIONARY_PACK_PROFILES,
        DICTIONARY_SCHEMAS,
        PUBLIC,
        ROOT,
        VERSION,
        artifact_license_spdx,
        artifact_notice_paths,
        copy_profile_notices,
        sync,
    )
    from tools.release_policy import archive_paths, check, load
    from tools.tasks import (
        LexiconProfile,
        load_pack_manifest,
        maturin_feature_args,
        profile_env,
        resolve_lexicon_profile,
        wasm_pack_build_command,
    )

OUT = ROOT / "target/alpha"
SMOKE = ROOT / "tools/release_smoke"

_FORBIDDEN_EXACT_FILENAMES = frozenset({
    "source_records.csv",
    "dispositions.csv",
    "record_targets.csv",
    "findings.csv",
    "changes.csv",
    "successors.csv",
    "fetch_manifest.json",
    "wikimedia_tou_api.json",
    "cc_by_sa_4_0_legalcode.txt",
})
_FORBIDDEN_PATH_PREFIXES = (
    "data/",
    "docs/reviews/",
    "docs/audits/",
    "target/lexicon/",
    "cldf/",
    "curation/",
)
_FORBIDDEN_PATH_TOKENS = (
    "/data/",
    "/cldf/",
    "/curation/",
    "wiktionary-core-approval",
    "wiktionary-core-decision",
    "wiktionary-candidate",
)
_NOTICE_MD_REF_RE = re.compile(
    r"lexicon/(?:dictionary|packs/(?:names_taxa|regional))/[A-Za-z0-9_./-]+\.md"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def archive_root(profile: str | None = None, *, out: Path | None = None) -> Path:
    """Return the profile-scoped archive root so default and data profiles never collide."""
    spec = resolve_lexicon_profile(profile)
    base = OUT if out is None else out
    if spec.name == "default":
        return base
    return base / "profiles" / spec.name


def run(*args, cwd=ROOT, capture=False, env=None):
    executable = shutil.which(str(args[0]))
    if executable is None:
        home_bin = Path.home() / ".cargo" / "bin" / (f"{args[0]}.exe" if sys.platform == "win32" else str(args[0]))
        if home_bin.exists():
            executable = str(home_bin)
    if executable is None:
        raise RuntimeError(f"Missing executable: {args[0]}")
    env = (env or os.environ).copy()
    cargo_bin = Path.home() / ".cargo" / "bin"
    if cargo_bin.exists() and str(cargo_bin) not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = f"{cargo_bin}{os.pathsep}{env.get('PATH', '')}"
    print("+ " + " ".join(map(str, args)), flush=True)
    result = subprocess.run([executable, *map(str, args[1:])], cwd=cwd, check=True,
                            capture_output=capture, text=True, encoding="utf-8", env=env)
    return result.stdout if capture else None


def fixtures(destination, *, profile: str, extra_planned=()):
    # Export unchanged active rows eligible for the explicit profile and any
    # explicitly selected planned review rows, without importing a binding.
    if not isinstance(profile, str) or not profile.strip():
        raise ValueError("fixtures() requires an explicit profile ('default', 'core', or 'full')")
    spec = resolve_lexicon_profile(profile)
    golden = ROOT / "tests/golden"
    manifest = json.loads((golden / "manifest.json").read_text(encoding="utf-8"))
    selected = {
        name.strip()
        for name in os.environ.get("TAMIL_GOLDEN_INCLUDE_PLANNED", "").split(",")
        if name.strip()
    }
    selected.update(name.strip() for name in extra_planned if name.strip())
    active = []
    planned = []
    excluded = []
    core_profile_suites = 0
    full_profile_suites = 0
    has_declared_full = False
    for suite in manifest["suites"]:
        req_profile = suite.get("required_profile")
        if req_profile is not None and req_profile not in ("default", "core", "full"):
            raise ValueError(f"Invalid required_profile {req_profile!r} in {suite['file']}")
        if req_profile == "full":
            has_declared_full = True
        req_satisfied = req_profile is None or req_profile == spec.name
        if suite["file"] in selected and not req_satisfied:
            raise ValueError(f"{suite['file']} requires profile {req_profile!r}, selected {spec.name!r}")
        if suite["status"] == "active":
            if not req_satisfied:
                row_count = len((golden / suite["file"]).read_text(encoding="utf-8").splitlines())
                excluded.append((suite["file"], req_profile, row_count))
                continue
            active.append(suite)
            if req_profile == "core":
                core_profile_suites += 1
            elif req_profile == "full":
                full_profile_suites += 1
        elif suite["status"] == "planned" and suite["file"] in selected:
            if not req_satisfied:
                raise ValueError(
                    f"Cannot export planned suite {suite['file']} (requires profile {req_profile!r}) under profile {spec.name!r}"
                )
            planned.append(suite)
            if req_profile == "core":
                core_profile_suites += 1
            elif req_profile == "full":
                full_profile_suites += 1
    if spec.name == "core" and core_profile_suites == 0:
        raise ValueError("Core fixture export requires at least one required_profile='core' suite")
    if spec.name == "full" and has_declared_full and full_profile_suites == 0:
        raise ValueError("Full fixture export requires declared required_profile='full' suites to be active or selected")
    for filename, req_profile, row_count in excluded:
        print(
            f"PROFILE_EXCLUDED {filename}: requires profile {req_profile!r} "
            f"(selected {spec.name!r}; {row_count} vectors excluded).",
            flush=True,
        )
    content = "".join((golden / suite["file"]).read_text(encoding="utf-8")
                      for suite in [*active, *planned])
    if planned:
        review_count = sum(len((golden / suite["file"]).read_text(encoding="utf-8").splitlines())
                           for suite in planned)
        print(f"PRE-ACTIVATION ARCHIVE REVIEW: executing {review_count} selected planned vectors; they remain outside active parity and release scope.", flush=True)
    path = destination / "golden.jsonl"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def patches(paths):
    return "[patch.crates-io]\n" + "".join(
        f'{name} = {{ path = "{path.as_posix()}" }}\n' for name, path in paths.items())


def consumer_cargo_toml(version: str, extracted: dict[str, Path], spec: LexiconProfile) -> str:
    if spec.features:
        features_toml = ", ".join(f'"{feat}"' for feat in spec.features)
        dep_line = f'tamil-toolkit = {{ version = "={version}", features = [{features_toml}] }}'
    else:
        dep_line = f'tamil-toolkit = "={version}"'
    return (
        '[package]\nname = "alpha-consumer"\nversion = "0.0.0"\nedition = "2021"\n'
        f'[dependencies]\n{dep_line}\nserde_json = "1"\n'
        + patches(extracted)
    )


def _safe_archive_relpath(raw_name: str) -> PurePosixPath:
    _require("\\" not in raw_name and not raw_name.startswith("/"), f"Unsafe archive path: {raw_name!r}")
    pure = PurePosixPath(raw_name)
    _require(not pure.is_absolute() and ".." not in pure.parts, f"Unsafe archive path traversal: {raw_name!r}")
    return pure


def _safe_tar_members(archive_path: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with tarfile.open(archive_path, "r:gz") as package:
        for member in package.getmembers():
            _safe_archive_relpath(member.name)
            _require(member.isfile() or member.isdir(), f"Archive contains links or special files: {member.name}")
            if member.isfile():
                _require(member.name not in files, f"Duplicate archive member: {member.name}")
                handle = package.extractfile(member)
                _require(handle is not None, f"Unreadable archive member: {member.name}")
                files[member.name] = handle.read()
    return files


def _safe_zip_members(archive_path: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(archive_path, "r") as package:
        for info in package.infolist():
            _safe_archive_relpath(info.filename)
            is_symlink = ((info.external_attr >> 16) & 0o170000) == 0o120000
            _require(not is_symlink, f"Wheel contains symlink entry: {info.filename}")
            if not info.is_dir():
                _require(info.filename not in files, f"Duplicate wheel member: {info.filename}")
                files[info.filename] = package.read(info.filename)
    return files


def _check_no_forbidden_archive_paths(
    rel_paths,
    *,
    allow_canonical_dict: bool,
    artifact_label: str,
) -> None:
    for rel in rel_paths:
        _safe_archive_relpath(rel)
        lower = rel.lower()
        basename = PurePosixPath(rel).name.lower()
        _require(
            not lower.endswith(".fst"),
            f"{artifact_label}: forbidden untrusted FST artifact in archive: {rel}",
        )
        _require(
            basename not in _FORBIDDEN_EXACT_FILENAMES,
            f"{artifact_label}: forbidden private editorial/extraction file in archive: {rel}",
        )
        _require(
            not lower.startswith(_FORBIDDEN_PATH_PREFIXES)
            and not any(token in lower for token in _FORBIDDEN_PATH_TOKENS),
            f"{artifact_label}: forbidden private editorial/extraction path in archive: {rel}",
        )
        if not allow_canonical_dict:
            _require(
                not lower.endswith(".csv"),
                f"{artifact_label}: raw dictionary CSV is forbidden in runtime archive: {rel}",
            )
            _require(
                basename not in {"packs.toml", "schema.toml", "vocabularies.toml"}
                and not lower.startswith("schemas/lexicon/")
                and "/schemas/lexicon/" not in lower,
                f"{artifact_label}: raw canonical manifest/schema file is forbidden in runtime archive: {rel}",
            )


def _verify_notice_contents(
    files_map: dict[str, bytes],
    *,
    expected_notices: list[str],
    spdx: str,
    artifact_label: str,
    allow_repo_notices: bool = False,
) -> None:
    for rel in expected_notices:
        _require(
            rel in files_map and bool(files_map[rel].strip()),
            f"{artifact_label}: missing or empty required notice file {rel}",
        )
    notices_bytes = files_map.get("THIRD_PARTY_NOTICES.md", b"")
    notices_text = notices_bytes.decode("utf-8")
    referenced = set(_NOTICE_MD_REF_RE.findall(notices_text))
    if "CC-BY-SA-4.0" not in spdx:
        if not allow_repo_notices:
            _require(
                not referenced,
                f"{artifact_label}: Apache-2.0-only THIRD_PARTY_NOTICES.md references CC pack notices: {', '.join(sorted(referenced))}",
            )
        return
    _require(
        "CC-BY-SA-4.0" in notices_text and "Wiktionary" in notices_text,
        f"{artifact_label}: THIRD_PARTY_NOTICES.md missing CC-BY-SA-4.0 / Wiktionary notice",
    )
    expected_pack_notices = {
        rel for rel in expected_notices if rel != "THIRD_PARTY_NOTICES.md"
    }
    for ref_path in sorted(referenced):
        _require(
            ref_path in expected_pack_notices,
            f"{artifact_label}: THIRD_PARTY_NOTICES.md references unincluded pack notice file {ref_path}",
        )
        _require(
            ref_path in files_map and bool(files_map[ref_path].strip()),
            f"{artifact_label}: THIRD_PARTY_NOTICES.md references missing notice file {ref_path}",
        )
    missing_refs = sorted(expected_pack_notices - referenced)
    _require(
        not missing_refs,
        f"{artifact_label}: THIRD_PARTY_NOTICES.md omits required pack notice references: {', '.join(missing_refs)}",
    )
    notice_prefixes = sorted({
        rel[: -len("/notices/CC-BY-SA-4.0.md")]
        for rel in expected_notices
        if rel.endswith("/notices/CC-BY-SA-4.0.md")
    })
    for prefix in notice_prefixes:
        cc_rel = f"{prefix}/notices/CC-BY-SA-4.0.md"
        cc_text = files_map[cc_rel].decode("utf-8")
        _require(
            "Attribution-ShareAlike 4.0 International" in cc_text
            and "https://creativecommons.org/licenses/by-sa/4.0/" in cc_text,
            f"{artifact_label}: incomplete CC-BY-SA-4.0 legal text in {cc_rel}",
        )
        attr_terms_rel = f"{prefix}/ATTRIBUTION_AND_TERMS.md"
        attr_terms = files_map[attr_terms_rel].decode("utf-8")
        _require(
            "Wiktionary" in attr_terms and "CC-BY-SA-4.0" in attr_terms,
            f"{artifact_label}: incomplete attribution terms in {attr_terms_rel}",
        )
        attr_license_rel = f"{prefix}/notices/ATTRIBUTION_AND_LICENSE.md"
        attr_license = files_map[attr_license_rel].decode("utf-8")
        _require(
            "CC-BY-SA-4.0" in attr_license,
            f"{artifact_label}: incomplete notice in {attr_license_rel}",
        )


def _iter_manifest_dep_tables(manifest: dict):
    for section in ("dependencies", "build-dependencies", "dev-dependencies"):
        table = manifest.get(section)
        if isinstance(table, dict):
            yield table
    for target_cfg in (manifest.get("target") or {}).values():
        if isinstance(target_cfg, dict):
            for section in ("dependencies", "build-dependencies", "dev-dependencies"):
                table = target_cfg.get(section)
                if isinstance(table, dict):
                    yield table


MAX_CRATES_IO_ARCHIVE_BYTES = 10 * 1024 * 1024


def verify_rust_crate_archive(
    archive_path: Path,
    name: str,
    *,
    expected_manifest_sha256: str | None = None,
    expected_dataset_version: str | None = None,
    expected_pack_manifests: dict[str, dict[str, str]] | None = None,
    policy: dict | None = None,
    root: Path = ROOT,
) -> None:
    """Verify packaged `.crate` size, license metadata, required notices, and canonical scope."""
    pol = policy or load(root)
    version = pol["version"]
    archive_size = archive_path.stat().st_size
    _require(
        archive_size <= MAX_CRATES_IO_ARCHIVE_BYTES,
        f"{name}: crate archive {archive_size} bytes exceeds crates.io 10 MiB limit ({MAX_CRATES_IO_ARCHIVE_BYTES})",
    )
    prefix = f"{name}-{version}/"
    raw_files = _safe_tar_members(archive_path)
    _require(bool(raw_files), f"{name}: empty crate archive {archive_path}")
    _require(all(path.startswith(prefix) for path in raw_files), f"{name}: unexpected crate archive root prefix")
    rel_files = {path[len(prefix):]: content for path, content in raw_files.items()}
    _require("Cargo.toml" in rel_files, f"{name}: crate archive missing Cargo.toml")
    manifest = tomllib.loads(rel_files["Cargo.toml"].decode("utf-8"))

    for dep_table in _iter_manifest_dep_tables(manifest):
        for dep_name, settings in dep_table.items():
            if isinstance(settings, dict):
                _require("path" not in settings, f"Published path dependency in {name}: {dep_name}")

    _check_no_forbidden_archive_paths(
        rel_files,
        allow_canonical_dict=False,
        artifact_label=name,
    )

    if name not in pol["public_crates"]:
        return

    expected_spdx = artifact_license_spdx(name)
    scoped_spdx = pol.get("crate_licenses", {}).get(name)
    if scoped_spdx is not None:
        _require(
            scoped_spdx == expected_spdx,
            f"{name}: release-policy crate_licenses {scoped_spdx!r} != {expected_spdx!r}",
        )
    actual_license = manifest.get("package", {}).get("license")
    _require(
        actual_license == expected_spdx,
        f"{name}: expected crate license {expected_spdx!r}, got {actual_license!r}",
    )

    expected_notices = artifact_notice_paths(name, root=root)
    for req_file in ("LICENSE", "README.md", *expected_notices):
        _require(
            req_file in rel_files and bool(rel_files[req_file].strip()),
            f"{name}: missing or empty required crate file {req_file}",
        )
    _verify_notice_contents(
        rel_files,
        expected_notices=expected_notices,
        spdx=expected_spdx,
        artifact_label=name,
        allow_repo_notices=True,
    )
    _require(
        not any(path.startswith(("lexicon/dictionary/", "lexicon/packs/", "schemas/lexicon/")) for path in rel_files),
        f"{name}: published crate archive must stay slim (< 10 MiB) without bulk dictionary/pack/schema files",
    )


def rust(profile=None):
    spec = resolve_lexicon_profile(profile)
    sync(check=True)
    policy = load()
    destination = archive_root(spec.name) / "rust"
    destination.mkdir(parents=True, exist_ok=True)
    all_crates = {p.name: ROOT / "crates" / p.name for p in (ROOT / "crates").iterdir() if (p / "Cargo.toml").is_file()}
    package_targets = tuple(dict.fromkeys((*PUBLIC, "tamil-calendar")))
    with tempfile.TemporaryDirectory(prefix="tamil-alpha-rust-") as directory:
        temp = Path(directory)
        config = temp / "patches.toml"
        config.write_text(patches(all_crates), encoding="utf-8")
        selections = [item for name in package_targets for item in ("-p", name)]
        # Unpublished siblings cannot resolve from crates.io yet. These patches
        # affect local verification only; normalized archives keep registry versions.
        run("cargo", "package", *selections, "--allow-dirty", "--config", config)
        extracted = {}
        for name in package_targets:
            archive = ROOT / "target/package" / f"{name}-{VERSION}.crate"
            verify_rust_crate_archive(
                archive,
                name,
                expected_manifest_sha256=spec.manifest_sha256,
                expected_dataset_version=spec.dataset_version,
                expected_pack_manifests=spec.pack_manifests_map() or None,
                policy=policy,
            )
            if name in PUBLIC:
                shutil.copy2(archive, destination / archive.name)
            with tarfile.open(archive) as package:
                package.extractall(temp / "crates", filter="data")
            extracted[name] = temp / "crates" / f"{name}-{VERSION}"
        consumer = temp / "consumer"
        (consumer / "src").mkdir(parents=True)
        (consumer / "Cargo.toml").write_text(
            consumer_cargo_toml(VERSION, extracted, spec), encoding="utf-8")
        shutil.copy2(SMOKE / "rust_consumer.rs", consumer / "src/main.rs")
        consumer_env = {**os.environ, **profile_env(spec, include_planned=bool(spec.planned_suites))}
        run(
            "cargo",
            "run",
            "--quiet",
            "--",
            fixtures(consumer, profile=spec.name, extra_planned=spec.planned_suites),
            cwd=consumer,
            env=consumer_env,
        )


def licenses():
    metadata = json.loads(run("cargo", "metadata", "--locked", "--format-version", "1", capture=True))
    nodes = {node["id"]: node for node in metadata["resolve"]["nodes"]}
    pending = [p["id"] for p in metadata["packages"] if p["name"] in ("tamil-python", "tamil-wasm")]
    found = set()
    while pending:
        name = pending.pop()
        if name in found:
            continue
        found.add(name)
        pending.extend(dep["pkg"] for dep in nodes[name]["deps"]
                       if any(kind["kind"] != "dev" for kind in dep["dep_kinds"]))
    parts = ["Locked Rust dependency licenses for tamil-toolkit binary distributions.\n"]
    for package in sorted(metadata["packages"], key=lambda p: (p["name"], p["version"])):
        if package["id"] not in found or package["source"] is None:
            continue
        directory = Path(package["manifest_path"]).parent
        files = sorted(path for path in directory.iterdir() if path.is_file()
                       and path.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")))
        if not files or not package["license"]:
            raise ValueError(f"Missing dependency license evidence: {package['name']}")
        parts.append(f"\n=== {package['name']} {package['version']} ({package['license']}) ===\n")
        parts.extend(f"\n--- {path.name} ---\n{path.read_text(encoding='utf-8')}\n" for path in files)
    for binding in ("python", "js-wasm"):
        (ROOT / "bindings" / binding / "THIRD_PARTY_LICENSES.txt").write_text(
            "".join(parts), encoding="utf-8", newline="\n")


def patch_python_pyproject(pyproject_path: Path, *, spdx: str, license_files) -> None:
    """Update `[project].license` and `[project].license-files` on a staged/extracted pyproject.toml."""
    text = pyproject_path.read_text(encoding="utf-8")
    tomllib.loads(text)
    lf_list = list(dict.fromkeys(license_files))
    header_match = re.search(r"(?m)^\[project\]\s*$", text)
    _require(header_match is not None, f"Missing [project] section in {pyproject_path}")
    body_start = header_match.end()
    next_header = re.search(r"(?m)^\[[^\]]+\]\s*$", text[body_start:])
    body_end = body_start + next_header.start() if next_header else len(text)
    body = text[body_start:body_end]

    new_license_line = f"license = {json.dumps(spdx)}"
    new_lf_line = f"license-files = {json.dumps(lf_list)}"
    if re.search(r"(?m)^license\s*=.*$", body):
        body = re.sub(r"(?m)^license\s*=.*$", new_license_line, body, count=1)
    else:
        body = f"\n{new_license_line}" + body

    if re.search(r"(?ms)^license-files\s*=\s*\[.*?\]", body):
        body = re.sub(r"(?ms)^license-files\s*=\s*\[.*?\]", new_lf_line, body, count=1)
    else:
        body = re.sub(r"(?m)^license\s*=.*$", rf"\g<0>\n{new_lf_line}", body, count=1)

    updated = text[:body_start] + body + text[body_end:]
    parsed = tomllib.loads(updated)
    _require(parsed["project"]["license"] == spdx, f"Failed to patch license in {pyproject_path}")
    _require(parsed["project"]["license-files"] == lf_list, f"Failed to patch license-files in {pyproject_path}")
    pyproject_path.write_text(updated, encoding="utf-8", newline="\n")


def prepare_python_sdist(python_dir: Path, *, root: Path = ROOT) -> None:
    """Copy canonical CC notices and set mixed SPDX on an isolated staged sdist project."""
    spdx = artifact_license_spdx("python-sdist")
    notice_paths = artifact_notice_paths("python-sdist", root=root)
    copy_profile_notices(python_dir, profiles=("core", "names_taxa", "regional"), root=root)
    license_files = list(dict.fromkeys(["LICENSE", "THIRD_PARTY_LICENSES.txt", *notice_paths]))
    patch_python_pyproject(python_dir / "pyproject.toml", spdx=spdx, license_files=license_files)


def prepare_python_wheel(project_dir: Path, *, profile: str | None = None, root: Path = ROOT) -> None:
    """Configure an extracted sdist directory with the wheel profile's exact SPDX and notices."""
    spec = resolve_lexicon_profile(profile, root=root)
    spdx = artifact_license_spdx("python-wheel", profiles=spec.expected_packs)
    notice_paths = artifact_notice_paths("python-wheel", profiles=spec.expected_packs, root=root)
    if not spec.expected_packs and (project_dir / "lexicon").exists():
        shutil.rmtree(project_dir / "lexicon")
    copy_profile_notices(project_dir, profiles=spec.expected_packs, root=root)
    license_files = list(dict.fromkeys(["LICENSE", "THIRD_PARTY_LICENSES.txt", *notice_paths]))
    patch_python_pyproject(project_dir / "pyproject.toml", spdx=spdx, license_files=license_files)


def verify_python_sdist(
    sdist_path: Path,
    *,
    expected_python_version: str | None = None,
    root: Path = ROOT,
) -> None:
    """Verify Python sdist carries Apache-2.0 AND CC-BY-SA-4.0 metadata, canonical notices, and clean vendoring."""
    raw_files = _safe_tar_members(sdist_path)
    pkg_infos = [path for path in raw_files if path.count("/") == 1 and path.endswith("/PKG-INFO")]
    _require(len(pkg_infos) == 1, f"Expected single PKG-INFO in sdist {sdist_path}, found {pkg_infos}")
    prefix = pkg_infos[0].removesuffix("PKG-INFO")
    _require(all(path.startswith(prefix) for path in raw_files), f"Unexpected sdist root prefix in {sdist_path}")
    rel_files = {path[len(prefix):]: content for path, content in raw_files.items()}

    metadata = BytesParser().parsebytes(rel_files["PKG-INFO"])
    _require(metadata.get("Name", "").replace("_", "-") == "tamil-toolkit", "Python sdist name mismatch")
    if expected_python_version is not None:
        _require(metadata.get("Version") == expected_python_version, "Python sdist version mismatch")

    expected_spdx = artifact_license_spdx("python-sdist")
    _require(
        metadata.get("License-Expression") == expected_spdx,
        f"python-sdist: expected License-Expression {expected_spdx!r}, got {metadata.get('License-Expression')!r}",
    )
    expected_notices = artifact_notice_paths("python-sdist", root=root)
    required_license_files = list(dict.fromkeys(["LICENSE", "THIRD_PARTY_LICENSES.txt", *expected_notices]))
    declared_lf = set(metadata.get_all("License-File") or ())
    for req_lf in required_license_files:
        _require(req_lf in declared_lf, f"python-sdist: PKG-INFO missing License-File {req_lf!r}")
        _require(
            req_lf in rel_files and bool(rel_files[req_lf].strip()),
            f"python-sdist: archive missing or empty license/notice file {req_lf}",
        )

    _check_no_forbidden_archive_paths(rel_files, allow_canonical_dict=True, artifact_label="python-sdist")
    _verify_notice_contents(
        rel_files,
        expected_notices=expected_notices,
        spdx=expected_spdx,
        artifact_label="python-sdist",
    )

    vendored_manifest_path = "crates/tamil-toolkit/Cargo.toml"
    _require(vendored_manifest_path in rel_files, "python-sdist missing vendored crates/tamil-toolkit/Cargo.toml")
    vendored_manifest = tomllib.loads(rel_files[vendored_manifest_path].decode("utf-8"))
    vendored_pkg = vendored_manifest.get("package", {})
    vendored_license = vendored_pkg.get("license")
    _require(
        vendored_license == "Apache-2.0" or (isinstance(vendored_license, dict) and vendored_license.get("workspace") is True),
        "python-sdist vendored tamil-toolkit Cargo.toml license mismatch",
    )
    for pack_id, cfg in DICTIONARY_PACK_PROFILES.items():
        vendored_packs_path = f"crates/tamil-toolkit/{cfg['source_dir']}/packs.toml"
        _require(vendored_packs_path in rel_files, f"python-sdist missing vendored {vendored_packs_path}")
        expected_manifest = load_pack_manifest(pack_id, root=root)
        vendored_packs = tomllib.loads(rel_files[vendored_packs_path].decode("utf-8"))
        _require(
            vendored_packs.get("manifest_sha256") == expected_manifest["manifest_sha256"],
            f"python-sdist vendored {vendored_packs_path} manifest_sha256 mismatch",
        )


def verify_python_wheel(
    wheel_path: Path,
    *,
    profile: str | None = None,
    expected_python_version: str | None = None,
    root: Path = ROOT,
) -> None:
    """Verify Python wheel metadata, `.dist-info/licenses/` notices, and zero raw CSV leakage."""
    spec = resolve_lexicon_profile(profile, root=root)
    expected_spdx = artifact_license_spdx("python-wheel", profiles=spec.expected_packs)
    expected_notices = artifact_notice_paths("python-wheel", profiles=spec.expected_packs, root=root)
    required_license_files = list(dict.fromkeys(["LICENSE", "THIRD_PARTY_LICENSES.txt", *expected_notices]))

    raw_files = _safe_zip_members(wheel_path)
    _check_no_forbidden_archive_paths(
        raw_files,
        allow_canonical_dict=False,
        artifact_label=f"python-wheel ({spec.name})",
    )

    metadata_paths = [path for path in raw_files if path.endswith(".dist-info/METADATA")]
    _require(len(metadata_paths) == 1, f"Wheel must contain exactly one METADATA file: {wheel_path}")
    dist_info_dir = metadata_paths[0].removesuffix("/METADATA")
    metadata = BytesParser().parsebytes(raw_files[metadata_paths[0]])
    _require(metadata.get("Name", "").replace("_", "-") == "tamil-toolkit", "Python wheel name mismatch")
    if expected_python_version is not None:
        _require(metadata.get("Version") == expected_python_version, "Python wheel version mismatch")
    _require(
        metadata.get("License-Expression") == expected_spdx,
        f"python-wheel ({spec.name}): expected License-Expression {expected_spdx!r}, got {metadata.get('License-Expression')!r}",
    )

    declared_lf = set(metadata.get_all("License-File") or ())
    licenses_prefix = f"{dist_info_dir}/licenses/"
    wheel_licenses = {
        path[len(licenses_prefix):]: content
        for path, content in raw_files.items()
        if path.startswith(licenses_prefix)
    }
    for req_lf in required_license_files:
        _require(req_lf in declared_lf, f"python-wheel ({spec.name}): METADATA missing License-File {req_lf!r}")
        _require(
            req_lf in wheel_licenses and bool(wheel_licenses[req_lf].strip()),
            f"python-wheel ({spec.name}): missing or empty {licenses_prefix}{req_lf}",
        )

    if not spec.expected_packs:
        _require(
            not any(("lexicon/dictionary" in path or "lexicon/packs" in path) for path in raw_files)
            and not any(("lexicon/dictionary" in lf or "lexicon/packs" in lf) for lf in declared_lf),
            "default python-wheel must not include lexicon/dictionary or lexicon/packs notice or data files",
        )

    _verify_notice_contents(
        wheel_licenses,
        expected_notices=expected_notices,
        spdx=expected_spdx,
        artifact_label=f"python-wheel ({spec.name})",
    )


def stage_python(destination):
    """Minimal workspace; prune omitted members without changing locked releases."""
    destination.mkdir(parents=True)
    stage_crates = tuple(dict.fromkeys((*PUBLIC, "tamil-calendar")))
    for name in stage_crates:
        shutil.copytree(ROOT / "crates" / name, destination / "crates" / name,
                        ignore=shutil.ignore_patterns("tests", "target"))
    shutil.copytree(ROOT / "bindings/python", destination / "bindings/python",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyd", "*.so", "*.pdb", "*.egg-info"))
    manifest = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    members = json.dumps([f"crates/{name}" for name in stage_crates] + ["bindings/python"])
    manifest = manifest.replace(
        'members = ["crates/*", "bindings/python", "bindings/js-wasm", "bindings/dart-flutter/rust"]',
        "members = " + members)
    (destination / "Cargo.toml").write_text(manifest, encoding="utf-8")
    shutil.copy2(ROOT / "Cargo.lock", destination / "Cargo.lock")
    run("cargo", "metadata", "--offline", "--format-version", "1", cwd=destination, capture=True)
    original = tomllib.loads((ROOT / "Cargo.lock").read_text())["package"]
    reduced = tomllib.loads((destination / "Cargo.lock").read_text())["package"]
    locked = {(p["name"], p["version"], p.get("source")): p.get("checksum") for p in original}
    for package in reduced:
        key = (package["name"], package["version"], package.get("source"))
        assert key in locked and locked[key] == package.get("checksum"), "Source staging changed a locked dependency"
    staged_python = destination / "bindings/python"
    prepare_python_sdist(staged_python, root=ROOT)
    return staged_python


def python(profile=None):
    spec = resolve_lexicon_profile(profile)
    sync(check=True)
    licenses()
    py_version = load()["python_version"]
    destination = archive_root(spec.name) / "python"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tamil-alpha-python-") as directory:
        temp = Path(directory)
        project = stage_python(temp / "staged")
        run("maturin", "sdist", "--out", destination, cwd=project)
        sdists = list(destination.glob(f"tamil_toolkit-{py_version}.tar.gz"))
        _require(len(sdists) == 1, "Expected exactly the selected release source distribution")
        verify_python_sdist(sdists[0], expected_python_version=py_version)
        with tarfile.open(sdists[0]) as package:
            package.extractall(temp / "source", filter="data")
        project, = (path.parent for path in (temp / "source").rglob("pyproject.toml"))
        prepare_python_wheel(project, profile=spec.name)
        wheels = temp / "wheels"
        run("maturin", "build", "--release", "--locked", *maturin_feature_args(spec), "--out", wheels, cwd=project)
        wheel, = wheels.glob("*.whl")
        verify_python_wheel(wheel, profile=spec.name, expected_python_version=py_version)
        artifact = destination / wheel.name
        shutil.copy2(wheel, artifact)
        verify_python(artifact, temp, profile=spec.name)


def verify_python(wheel, temp, profile=None):
    spec = resolve_lexicon_profile(profile)
    environment = temp / "venv"
    venv.create(environment, with_pip=True)
    interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(interpreter, "-m", "pip", "install", "--no-deps", wheel)
    shutil.copy2(SMOKE / "python_consumer.py", temp / "consumer.py")
    consumer_env = {**os.environ, **profile_env(spec, include_planned=bool(spec.planned_suites))}
    run(
        interpreter,
        "-I",
        temp / "consumer.py",
        fixtures(temp, profile=spec.name, extra_planned=spec.planned_suites),
        load()["python_version"],
        cwd=temp,
        env=consumer_env,
    )


def stage_npm_package(
    source_dir: Path,
    destination: Path,
    *,
    profile: str | None = None,
    root: Path = ROOT,
) -> Path:
    """Stage built npm assets into an isolated temp dir with profile-accurate package.json & notices."""
    _require(source_dir.resolve() != destination.resolve(), "npm staging destination must be separate from source")
    spec = resolve_lexicon_profile(profile, root=root)
    spdx = artifact_license_spdx("npm", profiles=spec.expected_packs)
    notice_paths = artifact_notice_paths("npm", profiles=spec.expected_packs, root=root)

    destination.mkdir(parents=True, exist_ok=True)
    for subdir in ("dist", "pkg-node", "pkg-web"):
        src_sub = source_dir / subdir
        _require(src_sub.is_dir(), f"Missing built npm output directory: {src_sub}")
        shutil.copytree(src_sub, destination / subdir)
    for rel_file in ("README.md", "LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.txt"):
        src_file = source_dir / rel_file
        if rel_file == "NOTICE" and not src_file.is_file():
            src_file = root / "NOTICE"
        _require(src_file.is_file(), f"Missing required npm package file: {src_file}")
        shutil.copy2(src_file, destination / rel_file)

    copy_profile_notices(destination, profiles=spec.expected_packs, root=root)

    manifest = json.loads((source_dir / "package.json").read_text(encoding="utf-8"))
    manifest["license"] = spdx
    orig_files = list(manifest.get("files", []))
    manifest["files"] = list(dict.fromkeys([*orig_files, *notice_paths]))
    for entry in manifest["files"]:
        _require((destination / entry).exists(), f"Staged npm files entry missing: {entry}")
    (destination / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for sub_pkg in ("pkg-node/package.json", "pkg-web/package.json"):
        sub_path = destination / sub_pkg
        if sub_path.is_file():
            sub_meta = json.loads(sub_path.read_text(encoding="utf-8"))
            sub_meta["license"] = spdx
            sub_path.write_text(json.dumps(sub_meta, indent=2) + "\n", encoding="utf-8")
    return destination


def verify_npm_archive(
    archive_path: Path,
    *,
    profile: str | None = None,
    expected_version: str | None = None,
    source_package_json: Path | None = None,
    root: Path = ROOT,
) -> None:
    """Verify npm tarball metadata, published files/exports, canonical notices, and no raw CSV leakage."""
    spec = resolve_lexicon_profile(profile, root=root)
    expected_spdx = artifact_license_spdx("npm", profiles=spec.expected_packs)
    expected_notices = artifact_notice_paths("npm", profiles=spec.expected_packs, root=root)

    raw_files = _safe_tar_members(archive_path)
    _require(bool(raw_files), f"Empty npm archive: {archive_path}")
    _require(all(path.startswith("package/") for path in raw_files), "Unexpected npm archive root prefix")
    rel_files = {path[len("package/"):]: content for path, content in raw_files.items()}
    _check_no_forbidden_archive_paths(
        rel_files,
        allow_canonical_dict=False,
        artifact_label=f"npm ({spec.name})",
    )

    _require("package.json" in rel_files, "npm archive missing package/package.json")
    metadata = json.loads(rel_files["package.json"].decode("utf-8"))
    _require(metadata.get("name") == "tamil-toolkit", "npm archive package name mismatch")
    _require(not metadata.get("private"), "npm archive must not be private")
    if expected_version is not None:
        _require(metadata.get("version") == expected_version, "npm archive version mismatch")
    _require(
        metadata.get("license") == expected_spdx,
        f"npm ({spec.name}): expected package.json license {expected_spdx!r}, got {metadata.get('license')!r}",
    )

    declared_files = list(metadata.get("files") or [])
    for notice_rel in expected_notices:
        _require(
            notice_rel in declared_files,
            f"npm ({spec.name}): package.json files missing notice path {notice_rel!r}",
        )

    if source_package_json is not None:
        src_meta = json.loads(source_package_json.read_text(encoding="utf-8"))
        _require(metadata.get("version") == src_meta.get("version"), "npm archive version drifted from source")
        _require(metadata.get("exports") == src_meta.get("exports"), "npm archive exports drifted from source")
        _require(
            metadata.get("publishConfig") == src_meta.get("publishConfig"),
            "npm archive publishConfig drifted from source",
        )
        _require(
            set(src_meta.get("files", [])) <= set(declared_files),
            "npm archive package.json files dropped source entries",
        )

    required_paths = (
        "dist/index.d.ts",
        "dist/web.d.ts",
        "dist/api.d.ts",
        "pkg-node/tamil_toolkit_bg.wasm",
        "pkg-web/tamil_toolkit_bg.wasm",
        "LICENSE",
        "THIRD_PARTY_LICENSES.txt",
        *expected_notices,
    )
    for req_path in required_paths:
        _require(
            req_path in rel_files and bool(rel_files[req_path]),
            f"npm ({spec.name}): missing or empty required archive entry {req_path}",
        )

    for sub_pkg in ("pkg-node/package.json", "pkg-web/package.json"):
        if sub_pkg in rel_files:
            sub_meta = json.loads(rel_files[sub_pkg].decode("utf-8"))
            _require(
                sub_meta.get("license") == expected_spdx,
                f"npm ({spec.name}): {sub_pkg} license {sub_meta.get('license')!r} != {expected_spdx!r}",
            )

    if not spec.expected_packs:
        _require(
            not any(path.startswith(("lexicon/dictionary/", "lexicon/packs/")) for path in rel_files),
            "default npm tarball must not include lexicon/dictionary or lexicon/packs notice or data files",
        )

    _verify_notice_contents(
        rel_files,
        expected_notices=expected_notices,
        spdx=expected_spdx,
        artifact_label=f"npm ({spec.name})",
    )


def npm(profile=None):
    spec = resolve_lexicon_profile(profile)
    sync(check=True)
    licenses()
    package = ROOT / "bindings/js-wasm"
    for target, output in (("nodejs", "pkg-node"), ("web", "pkg-web")):
        run(*wasm_pack_build_command(spec, target, output, release=True))
        # wasm-pack writes .gitignore="*" in each output. npm otherwise uses
        # those files and silently omits the actual WASM from the parent tarball.
        (package / output / ".npmignore").write_text("# Include wasm-pack outputs.\n", encoding="utf-8")
    run("pnpm", "--filter", "tamil-toolkit", "build")
    destination = archive_root(spec.name) / "npm"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tamil-alpha-npm-") as directory:
        temp = Path(directory)
        staged = stage_npm_package(package, temp / "npm-stage", profile=spec.name, root=ROOT)
        run("npm", "pack", "--pack-destination", destination, cwd=staged)
        archive = destination / f"tamil-toolkit-{VERSION}.tgz"
        verify_npm_archive(
            archive,
            profile=spec.name,
            expected_version=VERSION,
            source_package_json=package / "package.json",
        )
        consumer = temp / "consumer"
        consumer.mkdir()
        (consumer / "package.json").write_text('{"private":true,"type":"module"}', encoding="utf-8")
        run("npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", archive, cwd=consumer)
        for source in ("node_consumer.mjs", "types_consumer.ts"):
            shutil.copy2(SMOKE / source, consumer / source)
        run("node", package / "node_modules/typescript/bin/tsc", "--noEmit", "--strict", "--target", "ES2022",
            "--module", "NodeNext", "--moduleResolution", "NodeNext", "types_consumer.ts", cwd=consumer)
        consumer_env = {**os.environ, **profile_env(spec, include_planned=bool(spec.planned_suites))}
        run(
            "node",
            "node_consumer.mjs",
            fixtures(consumer, profile=spec.name, extra_planned=spec.planned_suites),
            cwd=consumer,
            env=consumer_env,
        )


def hashes(profile=None):
    target_dir = archive_root(profile)
    records = {path.relative_to(target_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in archive_paths(target_dir)}
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "SHA256SUMS.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Artifact digests recorded for {len(records)} archives in {target_dir}.")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=("rust", "python", "npm", "licenses", "stage-python", "verify-wheel", "all", "hashes"))
    parser.add_argument("--wheel", type=Path, help="Exactly one platform wheel to install and verify")
    parser.add_argument("--lexicon-profile", default=None, help="Optional lexicon compilation profile ('default', 'core', or 'full')")
    args = parser.parse_args()
    task = args.task
    if args.lexicon_profile is not None:
        resolve_lexicon_profile(args.lexicon_profile)
    check()
    if task == "verify-wheel":
        if args.wheel is None:
            parser.error("verify-wheel requires --wheel")
        with tempfile.TemporaryDirectory(prefix="tamil-alpha-wheel-") as directory:
            verify_python(args.wheel.resolve(), Path(directory), profile=args.lexicon_profile)
    elif task == "stage-python":
        sync(check=True)
        licenses()
        print(stage_python(archive_root(args.lexicon_profile) / "python-source"))
    elif task == "all":
        rust(profile=args.lexicon_profile)
        python(profile=args.lexicon_profile)
        npm(profile=args.lexicon_profile)
    elif task in ("rust", "python", "npm", "hashes"):
        globals()[task](profile=args.lexicon_profile)
    else:
        globals()[task]()
    if task not in ("licenses", "stage-python", "verify-wheel", "hashes"):
        hashes(profile=args.lexicon_profile)


if __name__ == "__main__":
    main()
