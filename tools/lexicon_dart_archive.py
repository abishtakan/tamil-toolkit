"""Build and consume a private host Dart bundle; never creates a Pub release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.harness import ROOT
from tools.release import fixtures
from tools.release_files import artifact_license_spdx, copy_profile_notices
from tools.tasks import cargo_feature_args, profile_env, resolve_lexicon_profile


def build_profile_library(spec) -> Path:
    """Build the requested data profile before copying its host library."""
    cargo = shutil.which("cargo")
    if cargo is None:
        raise ValueError("Cargo is required to build the selected Dart profile")
    subprocess.run(
        [cargo, "build", "--locked", "-p", "tamil-dart", *cargo_feature_args(spec)],
        cwd=ROOT,
        check=True,
    )
    suffix = ".dll" if sys.platform == "win32" else ".dylib" if sys.platform == "darwin" else ".so"
    prefix = "" if sys.platform == "win32" else "lib"
    library = ROOT / "target/debug" / f"{prefix}tamil_toolkit_ffi{suffix}"
    if not library.is_file():
        raise ValueError("Selected Dart profile build did not produce its host library")
    return library


def build_and_verify(profile: str) -> dict:
    spec = resolve_lexicon_profile(profile)
    library = build_profile_library(spec)
    library_name = library.name
    output = (ROOT / "target/lexicon/dart-archives" / spec.name).resolve()
    if not output.is_relative_to((ROOT / "target/lexicon").resolve()):
        raise ValueError("Dart archive output escapes the workspace target")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"tamil_toolkit-private-{spec.name}.zip"
    with tempfile.TemporaryDirectory(dir=output, prefix=".dart-archive-") as temporary:
        temporary = Path(temporary)
        stage = temporary / "stage"
        stage.mkdir()
        source = ROOT / "bindings/dart-flutter"
        for path in sorted((source / "lib").rglob("*.dart")):
            target = stage / "lib" / path.relative_to(source / "lib")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        for name in ("pubspec.yaml", "pubspec.lock", "README.md", "LICENSE", "NOTICE"):
            if (source / name).is_file():
                shutil.copy2(source / name, stage / name)
        copy_profile_notices(stage, profiles=spec.expected_packs)
        (stage / "native").mkdir()
        shutil.copy2(library, stage / "native" / library_name)
        (stage / "bin").mkdir()
        shutil.copy2(ROOT / "tools/release_smoke/dart_consumer.dart", stage / "bin/archive_consumer.dart")
        metadata = {
            "private_verification_only": True,
            "profile": spec.name,
            "expected_packs": list(spec.expected_packs),
            "manifest_sha256": spec.manifest_sha256,
            "pack_manifests": spec.pack_manifests_map(),
            "spdx": artifact_license_spdx("dart", profiles=spec.expected_packs),
            "engine_code_spdx": "Apache-2.0",
            "native_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
        }
        (stage / "ARTIFACT_PROFILE.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as packed:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo("package/" + path.relative_to(stage).as_posix(), (1980, 1, 1, 0, 0, 0))
                    info.external_attr = 0o100644 << 16
                    packed.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        extracted = temporary / "extracted"
        with zipfile.ZipFile(archive) as packed:
            expected = {"package/" + p.relative_to(stage).as_posix(): p.read_bytes()
                        for p in stage.rglob("*") if p.is_file()}
            if set(packed.namelist()) != set(expected):
                raise ValueError("Private Dart archive inventory mismatch")
            for name, content in expected.items():
                if packed.read(name) != content:
                    raise ValueError(f"Private Dart archive content mismatch: {name}")
            packed.extractall(extracted)
        package = extracted / "package"
        if "publish_to: none" not in (package / "pubspec.yaml").read_text():
            raise ValueError("Private Dart bundle must retain publish_to: none")
        fixture_path = fixtures(temporary, profile=spec.name, extra_planned=spec.planned_suites)
        dart = shutil.which("dart")
        if dart is None:
            raise ValueError("Dart runtime is required for archive verification")
        commands = [
            [dart, "pub", "get", "--offline", "--enforce-lockfile"],
            [dart, "analyze", "lib", "bin/archive_consumer.dart"],
            [dart, "run", "bin/archive_consumer.dart", str(package / "native" / library_name),
             str(fixture_path), spec.name, spec.manifest_sha256 or "none"],
        ]
        consumer_env = {**os.environ, **profile_env(spec, include_planned=bool(spec.planned_suites))}
        transcripts = []
        for command in commands:
            result = subprocess.run(command, cwd=package, env=consumer_env, capture_output=True, text=True, encoding="utf-8")
            transcripts.append({"command": command[:4], "exit_code": result.returncode,
                                "stdout": result.stdout, "stderr": result.stderr})
            if result.returncode:
                raise RuntimeError(f"Private Dart archive consumer failed:\n{result.stdout}\n{result.stderr}")
        report = {**metadata, "verified": True, "registry_upload": False,
                  "archive": str(archive.relative_to(ROOT)), "archive_bytes": archive.stat().st_size,
                  "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                  "golden_rows": len(fixture_path.read_text(encoding="utf-8").splitlines()),
                  "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
                  "source_checkout_dependency": False, "transcripts": transcripts}
        (output / "proof.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=("default", "core", "full"))
    args = parser.parse_args()
    result = build_and_verify(args.profile)
    print(json.dumps({key: result[key] for key in ("profile", "verified", "archive_sha256", "golden_rows")}))
