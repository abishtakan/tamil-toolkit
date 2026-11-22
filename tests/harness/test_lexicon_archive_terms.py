"""Tests for archive licensing metadata, canonical notice packaging, and profile separation (Feature 021 T061/T069)."""

from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tomllib
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import release, release_files, release_policy, tasks  # noqa: E402

_CORE_MANIFEST = tasks.load_pack_manifest("core", root=ROOT)
EXPECTED_CORE_MANIFEST_SHA256 = _CORE_MANIFEST["manifest_sha256"]
EXPECTED_CORE_DATASET_VERSION = _CORE_MANIFEST["dataset_version"]
POLICY = release_policy.load(ROOT)
VERSION = POLICY["version"]
PY_VERSION = POLICY["python_version"]


def _profile_packs(profile: str) -> tuple[str, ...]:
    if profile == "default":
        return ()
    if profile == "core":
        return ("core",)
    if profile == "full":
        return ("core", "names_taxa", "regional")
    raise ValueError(f"Unsupported profile {profile!r}")


def _write_targz(path: Path, files: dict[str, bytes | str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as archive:
        for name, value in files.items():
            content = value.encode("utf-8") if isinstance(value, str) else value
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return path


def _write_zip(path: Path, files: dict[str, bytes | str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in files.items():
            content = value.encode("utf-8") if isinstance(value, str) else value
            archive.writestr(name, content)
    return path


def _canonical_dict_entries(prefix: str) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for cfg in release_files.DICTIONARY_PACK_PROFILES.values():
        source_dir = cfg["source_dir"]
        for rel in release_files.DICTIONARY_FILES:
            src = ROOT / source_dir / rel
            out[f"{prefix}{source_dir}/{rel}"] = (
                b"csv-stub\n" if rel.endswith(".csv") else src.read_bytes()
            )
    for name in release_files.DICTIONARY_SCHEMAS:
        out[f"{prefix}schemas/lexicon/{name}"] = (ROOT / "schemas/lexicon" / name).read_bytes()
    return out


def _valid_crate_files(name: str, *, license_override: str | None = None) -> dict[str, bytes | str]:
    prefix = f"{name}-{VERSION}/"
    spdx = license_override or release_files.artifact_license_spdx(name)
    files: dict[str, bytes | str] = {
        f"{prefix}Cargo.toml": (
            f'[package]\nname = "{name}"\nversion = "{VERSION}"\nlicense = "{spdx}"\n'
        ),
        f"{prefix}LICENSE": (ROOT / "LICENSE").read_bytes(),
        f"{prefix}README.md": f"# {name}\n",
        f"{prefix}THIRD_PARTY_NOTICES.md": release_files.notices(ROOT),
        f"{prefix}src/lib.rs": "// lib\n",
    }
    return files


def _valid_sdist_files(
    *,
    license_expr: str = "Apache-2.0 AND CC-BY-SA-4.0",
    license_files: list[str] | None = None,
    omit_paths: set[str] | None = None,
    extra_files: dict[str, bytes | str] | None = None,
) -> dict[str, bytes | str]:
    prefix = f"tamil_toolkit-{PY_VERSION}/"
    all_packs = tuple(release_files.DICTIONARY_PACK_PROFILES)
    req_license_files = (
        license_files
        if license_files is not None
        else [
            "LICENSE",
            "THIRD_PARTY_LICENSES.txt",
            *release_files.artifact_notice_paths("python-sdist", profiles=all_packs, root=ROOT),
        ]
    )
    req_license_files = list(dict.fromkeys(req_license_files))
    pkg_info_lines = [
        "Metadata-Version: 2.4",
        "Name: tamil-toolkit",
        f"Version: {PY_VERSION}",
        f"License-Expression: {license_expr}",
        *[f"License-File: {lf}" for lf in req_license_files],
        "",
        "Description body",
    ]
    files: dict[str, bytes | str] = {
        f"{prefix}PKG-INFO": "\n".join(pkg_info_lines),
        f"{prefix}pyproject.toml": (ROOT / "bindings/python/pyproject.toml").read_bytes(),
        f"{prefix}LICENSE": (ROOT / "LICENSE").read_bytes(),
        f"{prefix}THIRD_PARTY_NOTICES.md": release_files.notices(ROOT, profiles=all_packs),
        f"{prefix}THIRD_PARTY_LICENSES.txt": (ROOT / "bindings/python/THIRD_PARTY_LICENSES.txt").read_bytes(),
        f"{prefix}crates/tamil-toolkit/Cargo.toml": (ROOT / "crates/tamil-toolkit/Cargo.toml").read_bytes(),
        **_canonical_dict_entries(f"{prefix}crates/tamil-toolkit/"),
    }
    for pack_id in all_packs:
        source_dir = release_files.DICTIONARY_PACK_PROFILES[pack_id]["source_dir"]
        for rel in release_files.DICTIONARY_NOTICE_FILES:
            files[f"{prefix}{source_dir}/{rel}"] = (ROOT / source_dir / rel).read_bytes()
    if omit_paths:
        for rel in omit_paths:
            files.pop(f"{prefix}{rel}", None)
    if extra_files:
        for rel, val in extra_files.items():
            files[f"{prefix}{rel}"] = val
    return files


def _valid_wheel_files(
    *,
    profile: str = "default",
    license_expr: str | None = None,
    license_files: list[str] | None = None,
    notices_override: bytes | None = None,
    omit_license_paths: set[str] | None = None,
    extra_files: dict[str, bytes | str] | None = None,
) -> dict[str, bytes | str]:
    dist_info = f"tamil_toolkit-{PY_VERSION}.dist-info"
    packs = _profile_packs(profile)
    spdx = license_expr or release_files.artifact_license_spdx("python-wheel", profiles=packs)
    default_notices = release_files.artifact_notice_paths("python-wheel", profiles=packs, root=ROOT)
    default_lf = list(dict.fromkeys(["LICENSE", "THIRD_PARTY_LICENSES.txt", *default_notices]))
    req_lf = license_files if license_files is not None else default_lf
    metadata_lines = [
        "Metadata-Version: 2.4",
        "Name: tamil-toolkit",
        f"Version: {PY_VERSION}",
        f"License-Expression: {spdx}",
        *[f"License-File: {lf}" for lf in req_lf],
        "",
        "Wheel summary",
    ]
    files: dict[str, bytes | str] = {
        "tamil_toolkit/__init__.py": (ROOT / "bindings/python/python/tamil_toolkit/__init__.py").read_bytes(),
        "tamil_toolkit/__init__.pyi": (ROOT / "bindings/python/python/tamil_toolkit/__init__.pyi").read_bytes(),
        "tamil_toolkit/py.typed": b"",
        "tamil_toolkit/_native.pyd": b"binary-payload",
        f"{dist_info}/METADATA": "\n".join(metadata_lines),
        f"{dist_info}/WHEEL": "Wheel-Version: 1.0\n",
        f"{dist_info}/RECORD": "",
        f"{dist_info}/licenses/LICENSE": (ROOT / "LICENSE").read_bytes(),
        f"{dist_info}/licenses/THIRD_PARTY_NOTICES.md": (
            notices_override if notices_override is not None else release_files.notices(ROOT, profiles=packs)
        ),
        f"{dist_info}/licenses/THIRD_PARTY_LICENSES.txt": (
            ROOT / "bindings/python/THIRD_PARTY_LICENSES.txt"
        ).read_bytes(),
    }
    for pack_id in packs:
        source_dir = release_files.DICTIONARY_PACK_PROFILES[pack_id]["source_dir"]
        for rel in release_files.DICTIONARY_NOTICE_FILES:
            files[f"{dist_info}/licenses/{source_dir}/{rel}"] = (
                ROOT / source_dir / rel
            ).read_bytes()
    if omit_license_paths:
        for rel in omit_license_paths:
            files.pop(f"{dist_info}/licenses/{rel}", None)
    if extra_files:
        files.update(extra_files)
    return files


def _make_fake_js_wasm_dir(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for rel in ("package.json", "README.md", "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_LICENSES.txt"):
        shutil.copy2(ROOT / "bindings/js-wasm" / rel, directory / rel)
    (directory / "dist").mkdir()
    for name in ("index.js", "index.d.ts", "web.js", "web.d.ts", "api.js", "api.d.ts"):
        (directory / "dist" / name).write_text("// built\n", encoding="utf-8")
    for pkg_dir in ("pkg-node", "pkg-web"):
        out = directory / pkg_dir
        out.mkdir()
        (out / "tamil_toolkit.js").write_text("// wasm glue\n", encoding="utf-8")
        (out / "tamil_toolkit.d.ts").write_text("export {};\n", encoding="utf-8")
        (out / "tamil_toolkit_bg.wasm").write_bytes(b"\x00asm\x01\x00\x00\x00")
        (out / ".npmignore").write_text("# Include wasm-pack outputs.\n", encoding="utf-8")
        (out / "package.json").write_text(
            json.dumps({"name": "tamil-wasm", "version": VERSION, "license": "Apache-2.0"}, indent=2),
            encoding="utf-8",
        )
    return directory


def _valid_npm_tar_files(
    *,
    profile: str = "default",
    license_override: str | None = None,
    files_override: list[str] | None = None,
    exports_override: dict | None = None,
    notices_override: bytes | None = None,
    omit_paths: set[str] | None = None,
    extra_files: dict[str, bytes | str] | None = None,
) -> dict[str, bytes | str]:
    pkg_json = json.loads((ROOT / "bindings/js-wasm/package.json").read_text(encoding="utf-8"))
    packs = _profile_packs(profile)
    spdx = license_override or release_files.artifact_license_spdx("npm", profiles=packs)
    pkg_json["license"] = spdx
    if files_override is not None:
        pkg_json["files"] = files_override
    elif packs:
        pack_notice_entries = [
            f"{release_files.DICTIONARY_PACK_PROFILES[pack_id]['source_dir']}/{rel}"
            for pack_id in packs
            for rel in release_files.DICTIONARY_NOTICE_FILES
        ]
        pkg_json["files"] = [*pkg_json["files"], *pack_notice_entries]
    if exports_override is not None:
        pkg_json["exports"] = exports_override

    tar_files: dict[str, bytes | str] = {
        "package/package.json": json.dumps(pkg_json, indent=2),
        "package/README.md": (ROOT / "bindings/js-wasm/README.md").read_bytes(),
        "package/LICENSE": (ROOT / "LICENSE").read_bytes(),
        "package/THIRD_PARTY_NOTICES.md": (
            notices_override if notices_override is not None else release_files.notices(ROOT, profiles=packs)
        ),
        "package/THIRD_PARTY_LICENSES.txt": (ROOT / "bindings/js-wasm/THIRD_PARTY_LICENSES.txt").read_bytes(),
        "package/dist/index.d.ts": "// dts\n",
        "package/dist/web.d.ts": "// dts\n",
        "package/dist/api.d.ts": "// dts\n",
        "package/pkg-node/tamil_toolkit_bg.wasm": b"\x00asm",
        "package/pkg-web/tamil_toolkit_bg.wasm": b"\x00asm",
        "package/pkg-node/package.json": json.dumps({"name": "tamil-wasm", "license": spdx}),
        "package/pkg-web/package.json": json.dumps({"name": "tamil-wasm", "license": spdx}),
    }
    for pack_id in packs:
        source_dir = release_files.DICTIONARY_PACK_PROFILES[pack_id]["source_dir"]
        for rel in release_files.DICTIONARY_NOTICE_FILES:
            tar_files[f"package/{source_dir}/{rel}"] = (
                ROOT / source_dir / rel
            ).read_bytes()
    if omit_paths:
        for rel in omit_paths:
            tar_files.pop(f"package/{rel}", None)
    if extra_files:
        for rel, val in extra_files.items():
            tar_files[f"package/{rel}"] = val
    return tar_files


# ---------------------------------------------------------------------------
# Gap 1: Rust crate archives (lower crates MIT vs tamil-toolkit MIT AND CC-BY-SA-4.0)
# ---------------------------------------------------------------------------


def test_rust_crate_verification_accepts_scoped_facade_and_mit_lower_crates(tmp_path: Path) -> None:
    core_archive = _write_targz(tmp_path / f"tamil-core-{VERSION}.crate", _valid_crate_files("tamil-core"))
    toolkit_archive = _write_targz(
        tmp_path / f"tamil-toolkit-{VERSION}.crate",
        _valid_crate_files("tamil-toolkit"),
    )

    release.verify_rust_crate_archive(core_archive, "tamil-core")
    release.verify_rust_crate_archive(
        toolkit_archive,
        "tamil-toolkit",
        expected_manifest_sha256=EXPECTED_CORE_MANIFEST_SHA256,
        expected_dataset_version=EXPECTED_CORE_DATASET_VERSION,
    )


def test_rust_crate_verification_rejects_wrong_license_missing_notices_or_private_leak(tmp_path: Path, monkeypatch) -> None:
    bad_facade = _write_targz(
        tmp_path / "bad_facade.crate",
        _valid_crate_files("tamil-toolkit", license_override="Apache-2.0 AND CC-BY-SA-4.0"),
    )
    with pytest.raises(ValueError, match="license"):
        release.verify_rust_crate_archive(bad_facade, "tamil-toolkit")

    bad_lower = _write_targz(
        tmp_path / "bad_lower.crate",
        _valid_crate_files("tamil-core", license_override="Apache-2.0 AND CC-BY-SA-4.0"),
    )
    with pytest.raises(ValueError, match="license"):
        release.verify_rust_crate_archive(bad_lower, "tamil-core")

    bulk_dict_files = _valid_crate_files("tamil-toolkit")
    bulk_dict_files[f"tamil-toolkit-{VERSION}/lexicon/dictionary/entries.csv"] = "leak\n"
    bulk_dict = _write_targz(tmp_path / "bulk_dict.crate", bulk_dict_files)
    with pytest.raises(ValueError, match="dictionary|csv"):
        release.verify_rust_crate_archive(bulk_dict, "tamil-toolkit")

    private_leak_files = _valid_crate_files("tamil-toolkit")
    private_leak_files[f"tamil-toolkit-{VERSION}/data/curation/tamil-lexicon/source_records.csv"] = "secret\n"
    private_leak = _write_targz(tmp_path / "private_leak.crate", private_leak_files)
    with pytest.raises(ValueError, match="Forbidden|private"):
        release.verify_rust_crate_archive(private_leak, "tamil-toolkit")

    lower_with_dict_files = _valid_crate_files("tamil-core")
    lower_with_dict_files[f"tamil-core-{VERSION}/lexicon/dictionary/entries.csv"] = "leak\n"
    lower_with_dict = _write_targz(tmp_path / "lower_with_dict.crate", lower_with_dict_files)
    with pytest.raises(ValueError, match="dictionary|csv"):
        release.verify_rust_crate_archive(lower_with_dict, "tamil-core")

    oversized_archive = _write_targz(tmp_path / "oversized.crate", _valid_crate_files("tamil-toolkit"))
    monkeypatch.setattr(release, "MAX_CRATES_IO_ARCHIVE_BYTES", 10)
    with pytest.raises(ValueError, match="10 MiB limit"):
        release.verify_rust_crate_archive(oversized_archive, "tamil-toolkit")


# ---------------------------------------------------------------------------
# Gap 2a: Python sdist (always MIT AND CC-BY-SA-4.0) & wheel (MIT / mixed)
# ---------------------------------------------------------------------------


def test_python_sdist_and_wheel_staging_patches_isolated_copies_only(
    tmp_path: Path,
    small_canonical_repo: Path,
) -> None:
    checked_in_pyproject = (ROOT / "bindings/python/pyproject.toml").read_text(encoding="utf-8")

    # Stage isolated sdist project dir
    sdist_dir = tmp_path / "staged_python"
    shutil.copytree(
        ROOT / "bindings/python",
        sdist_dir,
        ignore=shutil.ignore_patterns(".venv", "tests", "__pycache__", "*.pyd", "*.so", "*.pdb", "*.egg-info"),
    )
    release.prepare_python_sdist(sdist_dir, root=small_canonical_repo)

    sdist_toml = tomllib.loads((sdist_dir / "pyproject.toml").read_text(encoding="utf-8"))
    assert sdist_toml["project"]["license"] == "Apache-2.0 AND CC-BY-SA-4.0"
    for rel in release_files.artifact_notice_paths("python-sdist", root=ROOT):
        assert rel in sdist_toml["project"]["license-files"]
        assert (sdist_dir / rel).is_file()

    # Extracted sdist patched for default wheel -> MIT, no CC notices
    default_wheel_dir = tmp_path / "extracted_default"
    shutil.copytree(sdist_dir, default_wheel_dir)
    release.prepare_python_wheel(default_wheel_dir, profile="default", root=small_canonical_repo)
    default_toml = tomllib.loads((default_wheel_dir / "pyproject.toml").read_text(encoding="utf-8"))
    assert default_toml["project"]["license"] == "Apache-2.0"
    assert default_toml["project"]["license-files"] == [
        "LICENSE",
        "THIRD_PARTY_LICENSES.txt",
        "THIRD_PARTY_NOTICES.md",
    ]
    assert not (default_wheel_dir / "lexicon").exists()

    # Extracted sdist patched for core wheel -> MIT AND CC-BY-SA-4.0 + canonical CC notices
    core_wheel_dir = tmp_path / "extracted_core"
    shutil.copytree(sdist_dir, core_wheel_dir)
    release.prepare_python_wheel(core_wheel_dir, profile="core", root=small_canonical_repo)
    core_toml = tomllib.loads((core_wheel_dir / "pyproject.toml").read_text(encoding="utf-8"))
    assert core_toml["project"]["license"] == "Apache-2.0 AND CC-BY-SA-4.0"
    for rel in release_files.artifact_notice_paths("python-wheel", profiles=("core",), root=ROOT):
        assert rel in core_toml["project"]["license-files"]
        assert (core_wheel_dir / rel).is_file()

    # Checked-in pyproject.toml must remain untouched
    assert (ROOT / "bindings/python/pyproject.toml").read_text(encoding="utf-8") == checked_in_pyproject


def test_python_sdist_verification_enforces_mixed_spdx_notices_and_no_leaks(tmp_path: Path) -> None:
    good_sdist = _write_targz(tmp_path / f"tamil_toolkit-{PY_VERSION}.tar.gz", _valid_sdist_files())
    release.verify_python_sdist(good_sdist, expected_python_version=PY_VERSION)

    wrong_spdx = _write_targz(
        tmp_path / "wrong_spdx.tar.gz",
        _valid_sdist_files(license_expr="Apache-2.0"),
    )
    with pytest.raises(ValueError, match="Apache-2.0 AND CC-BY-SA-4.0"):
        release.verify_python_sdist(wrong_spdx, expected_python_version=PY_VERSION)

    missing_notice = _write_targz(
        tmp_path / "missing_notice.tar.gz",
        _valid_sdist_files(omit_paths={"lexicon/dictionary/notices/CC-BY-SA-4.0.md"}),
    )
    with pytest.raises(ValueError, match="CC-BY-SA-4.0"):
        release.verify_python_sdist(missing_notice, expected_python_version=PY_VERSION)

    private_leak = _write_targz(
        tmp_path / "private_leak.tar.gz",
        _valid_sdist_files(extra_files={"lexicon/dictionary/notices/fetch_manifest.json": "{}"}),
    )
    with pytest.raises(ValueError, match="Forbidden|private"):
        release.verify_python_sdist(private_leak, expected_python_version=PY_VERSION)


def test_python_wheel_verification_enforces_profile_spdx_notices_and_no_raw_csv(tmp_path: Path) -> None:
    good_default = _write_zip(
        tmp_path / f"tamil_toolkit-{PY_VERSION}-cp311-abi3-win_amd64.whl",
        _valid_wheel_files(profile="default"),
    )
    release.verify_python_wheel(good_default, profile="default", expected_python_version=PY_VERSION)

    good_core = _write_zip(
        tmp_path / f"core/tamil_toolkit-{PY_VERSION}-cp311-abi3-win_amd64.whl",
        _valid_wheel_files(profile="core"),
    )
    release.verify_python_wheel(good_core, profile="core", expected_python_version=PY_VERSION)

    good_full = _write_zip(
        tmp_path / f"full/tamil_toolkit-{PY_VERSION}-cp311-abi3-win_amd64.whl",
        _valid_wheel_files(profile="full"),
    )
    release.verify_python_wheel(good_full, profile="full", expected_python_version=PY_VERSION)

    # Core wheel whose THIRD_PARTY_NOTICES.md dangles to unincluded names_taxa fails notice closure.
    core_dangling_notice = _write_zip(
        tmp_path / "core_dangling_notice.whl",
        _valid_wheel_files(
            profile="core",
            notices_override=release_files.notices(ROOT, profiles=("core", "names_taxa", "regional")),
        ),
    )
    with pytest.raises(ValueError, match="unincluded pack notice"):
        release.verify_python_wheel(core_dangling_notice, profile="core", expected_python_version=PY_VERSION)

    # Core wheel claiming MIT fails
    core_mit = _write_zip(
        tmp_path / "core_mit.whl",
        _valid_wheel_files(profile="core", license_expr="Apache-2.0"),
    )
    with pytest.raises(ValueError, match="Apache-2.0 AND CC-BY-SA-4.0"):
        release.verify_python_wheel(core_mit, profile="core", expected_python_version=PY_VERSION)

    # Core wheel missing CC-BY-SA-4.0 notice fails
    core_missing_notice = _write_zip(
        tmp_path / "core_missing_notice.whl",
        _valid_wheel_files(
            profile="core",
            omit_license_paths={"lexicon/dictionary/notices/CC-BY-SA-4.0.md"},
        ),
    )
    with pytest.raises(ValueError, match="CC-BY-SA-4.0"):
        release.verify_python_wheel(core_missing_notice, profile="core", expected_python_version=PY_VERSION)

    # Core wheel leaking raw CSV fails ("no CSV raw into runtime wheel")
    core_raw_csv = _write_zip(
        tmp_path / "core_raw_csv.whl",
        _valid_wheel_files(
            profile="core",
            extra_files={"tamil_toolkit/lexicon/dictionary/entries.csv": "entry_id\n"},
        ),
    )
    with pytest.raises(ValueError, match="csv|Forbidden"):
        release.verify_python_wheel(core_raw_csv, profile="core", expected_python_version=PY_VERSION)

    # Default wheel leaking CC notice or wrong SPDX fails
    default_with_cc = _write_zip(
        tmp_path / "default_with_cc.whl",
        _valid_wheel_files(
            profile="default",
            extra_files={"tamil_toolkit-0.1.0a7.dist-info/licenses/lexicon/dictionary/notices/CC-BY-SA-4.0.md": "x"},
        ),
    )
    with pytest.raises(ValueError, match="lexicon/dictionary|CC-BY-SA-4.0"):
        release.verify_python_wheel(default_with_cc, profile="default", expected_python_version=PY_VERSION)


# ---------------------------------------------------------------------------
# Gap 2b: npm staging (no checked-in package.json mutation) & tarball checks
# ---------------------------------------------------------------------------


def test_npm_staging_preserves_source_package_json_and_stages_profile_terms(
    tmp_path: Path,
    small_canonical_repo: Path,
) -> None:
    checked_in_pkg = (ROOT / "bindings/js-wasm/package.json").read_text(encoding="utf-8")
    fake_src = _make_fake_js_wasm_dir(tmp_path / "js_wasm_src")
    orig_src_pkg = (fake_src / "package.json").read_text(encoding="utf-8")
    orig_parsed = json.loads(orig_src_pkg)

    # Default staging -> MIT, original files, no lexicon/dictionary
    staged_default = release.stage_npm_package(
        fake_src,
        tmp_path / "staged_npm_default",
        profile="default",
        root=small_canonical_repo,
    )
    default_pkg = json.loads((staged_default / "package.json").read_text(encoding="utf-8"))
    assert default_pkg["license"] == "Apache-2.0"
    assert default_pkg["version"] == orig_parsed["version"]
    assert default_pkg["exports"] == orig_parsed["exports"]
    assert default_pkg["files"] == orig_parsed["files"]
    assert not (staged_default / "lexicon").exists()

    # Core staging -> MIT AND CC-BY-SA-4.0, preserves exports/version/files + adds notice MDs, no CSVs
    staged_core = release.stage_npm_package(
        fake_src,
        tmp_path / "staged_npm_core",
        profile="core",
        root=small_canonical_repo,
    )
    core_pkg = json.loads((staged_core / "package.json").read_text(encoding="utf-8"))
    assert core_pkg["license"] == "Apache-2.0 AND CC-BY-SA-4.0"
    assert core_pkg["version"] == orig_parsed["version"]
    assert core_pkg["exports"] == orig_parsed["exports"]
    assert set(orig_parsed["files"]) <= set(core_pkg["files"])
    for rel in release_files.artifact_notice_paths("npm", profiles=("core",), root=ROOT):
        assert rel in core_pkg["files"]
        assert (staged_core / rel).is_file()
    assert json.loads((staged_core / "pkg-node/package.json").read_text(encoding="utf-8"))["license"] == "Apache-2.0 AND CC-BY-SA-4.0"
    assert json.loads((staged_core / "pkg-web/package.json").read_text(encoding="utf-8"))["license"] == "Apache-2.0 AND CC-BY-SA-4.0"
    assert not list(staged_core.rglob("*.csv"))

    # Source package.json was NOT mutated
    assert (fake_src / "package.json").read_text(encoding="utf-8") == orig_src_pkg
    assert (ROOT / "bindings/js-wasm/package.json").read_text(encoding="utf-8") == checked_in_pkg


def test_npm_archive_verification_enforces_notices_spdx_exports_and_no_raw_csv(tmp_path: Path) -> None:
    src_pkg_json = ROOT / "bindings/js-wasm/package.json"
    good_default = _write_targz(tmp_path / f"default/tamil-toolkit-{VERSION}.tgz", _valid_npm_tar_files(profile="default"))
    release.verify_npm_archive(
        good_default,
        profile="default",
        expected_version=VERSION,
        source_package_json=src_pkg_json,
    )

    good_core = _write_targz(tmp_path / f"core/tamil-toolkit-{VERSION}.tgz", _valid_npm_tar_files(profile="core"))
    release.verify_npm_archive(
        good_core,
        profile="core",
        expected_version=VERSION,
        source_package_json=src_pkg_json,
    )

    good_full = _write_targz(tmp_path / f"full/tamil-toolkit-{VERSION}.tgz", _valid_npm_tar_files(profile="full"))
    release.verify_npm_archive(
        good_full,
        profile="full",
        expected_version=VERSION,
        source_package_json=src_pkg_json,
    )

    # Core npm tarball with THIRD_PARTY_NOTICES.md referencing unincluded names_taxa fails notice closure.
    core_dangling_notice = _write_targz(
        tmp_path / "core_dangling_notice.tgz",
        _valid_npm_tar_files(
            profile="core",
            notices_override=release_files.notices(ROOT, profiles=("core", "names_taxa", "regional")),
        ),
    )
    with pytest.raises(ValueError, match="unincluded pack notice"):
        release.verify_npm_archive(core_dangling_notice, profile="core", expected_version=VERSION)

    # Core tarball with license=MIT fails
    core_mit = _write_targz(
        tmp_path / "core_mit.tgz",
        _valid_npm_tar_files(profile="core", license_override="Apache-2.0"),
    )
    with pytest.raises(ValueError, match="Apache-2.0 AND CC-BY-SA-4.0"):
        release.verify_npm_archive(core_mit, profile="core", expected_version=VERSION)

    # Core tarball missing a notice MD referenced in THIRD_PARTY_NOTICES.md fails
    core_missing_md = _write_targz(
        tmp_path / "core_missing_md.tgz",
        _valid_npm_tar_files(profile="core", omit_paths={"lexicon/dictionary/notices/ATTRIBUTION_AND_LICENSE.md"}),
    )
    with pytest.raises(ValueError, match="ATTRIBUTION_AND_LICENSE.md"):
        release.verify_npm_archive(core_missing_md, profile="core", expected_version=VERSION)

    # Core tarball omitting notice MD from package.json "files" fails
    base_files = json.loads(src_pkg_json.read_text(encoding="utf-8"))["files"]
    core_missing_files_entry = _write_targz(
        tmp_path / "core_missing_files_entry.tgz",
        _valid_npm_tar_files(profile="core", files_override=base_files),
    )
    with pytest.raises(ValueError, match="files"):
        release.verify_npm_archive(core_missing_files_entry, profile="core", expected_version=VERSION)

    # Mutated exports fails when compared to source package.json
    mutated_exports = _write_targz(
        tmp_path / "mutated_exports.tgz",
        _valid_npm_tar_files(profile="core", exports_override={".": "./broken.js"}),
    )
    with pytest.raises(ValueError, match="exports"):
        release.verify_npm_archive(
            mutated_exports,
            profile="core",
            expected_version=VERSION,
            source_package_json=src_pkg_json,
        )

    # Raw CSV inside runtime npm tarball fails
    npm_raw_csv = _write_targz(
        tmp_path / "npm_raw_csv.tgz",
        _valid_npm_tar_files(
            profile="core",
            extra_files={"lexicon/dictionary/entries.csv": "entry_id\n"},
        ),
    )
    with pytest.raises(ValueError, match="csv|Forbidden"):
        release.verify_npm_archive(npm_raw_csv, profile="core", expected_version=VERSION)


# ---------------------------------------------------------------------------
# Profile-separated digest outputs (default vs core under target/alpha)
# ---------------------------------------------------------------------------


def test_archive_root_and_hashes_keep_default_and_core_digests_separate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(release, "OUT", tmp_path / "alpha")

    default_root = release.archive_root("default")
    core_root = release.archive_root("core")
    assert default_root == tmp_path / "alpha"
    assert core_root == tmp_path / "alpha/profiles/core"

    (default_root / "npm").mkdir(parents=True)
    (core_root / "npm").mkdir(parents=True)
    (default_root / "npm/tamil-toolkit-default.tgz").write_bytes(b"default-bytes")
    (core_root / "npm/tamil-toolkit-core.tgz").write_bytes(b"core-bytes")

    default_sums = release.hashes(profile="default")
    core_sums = release.hashes(profile="core")

    assert set(default_sums) == {"npm/tamil-toolkit-default.tgz"}
    assert set(core_sums) == {"npm/tamil-toolkit-core.tgz"}
    assert json.loads((default_root / "SHA256SUMS.json").read_text(encoding="utf-8")) == default_sums
    assert json.loads((core_root / "SHA256SUMS.json").read_text(encoding="utf-8")) == core_sums


# ---------------------------------------------------------------------------
# Mocked release.py orchestration tests (no real native builds)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["default", "core", "full"])
def test_python_orchestration_patches_staged_and_extracted_metadata_by_profile(
    tmp_path: Path,
    monkeypatch,
    small_canonical_repo: Path,
    profile: str,
) -> None:
    checked_in_pyproject = (ROOT / "bindings/python/pyproject.toml").read_text(encoding="utf-8")
    out_dir = tmp_path / "alpha"
    monkeypatch.setattr(release, "OUT", out_dir)
    monkeypatch.setattr(release, "sync", lambda check=False: None)
    monkeypatch.setattr(release, "licenses", lambda: None)
    monkeypatch.setattr(release, "verify_python", lambda wheel, temp, profile=None: None)
    orig_prepare_sdist = release.prepare_python_sdist
    orig_prepare_wheel = release.prepare_python_wheel
    monkeypatch.setattr(
        release,
        "prepare_python_sdist",
        lambda python_dir, *, root=ROOT: orig_prepare_sdist(python_dir, root=small_canonical_repo),
    )
    monkeypatch.setattr(
        release,
        "prepare_python_wheel",
        lambda project_dir, *, profile=None, root=ROOT: orig_prepare_wheel(
            project_dir, profile=profile, root=small_canonical_repo
        ),
    )

    recorded_sdist_toml: dict = {}
    recorded_wheel_toml: dict = {}

    def fake_run(*args, cwd=ROOT, capture=False, env=None):
        if args[:2] == ("cargo", "metadata"):
            return "{}"
        if args[:2] == ("maturin", "sdist"):
            out = Path(args[args.index("--out") + 1])
            recorded_sdist_toml.update(tomllib.loads((Path(cwd) / "pyproject.toml").read_text(encoding="utf-8")))
            _write_targz(out / f"tamil_toolkit-{PY_VERSION}.tar.gz", _valid_sdist_files())
            return None
        if args[:2] == ("maturin", "build"):
            out = Path(args[args.index("--out") + 1])
            recorded_wheel_toml.update(tomllib.loads((Path(cwd) / "pyproject.toml").read_text(encoding="utf-8")))
            _write_zip(
                out / f"tamil_toolkit-{PY_VERSION}-cp311-abi3-win_amd64.whl",
                _valid_wheel_files(profile=profile),
            )
            return None
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(release, "run", fake_run)
    release.python(profile=profile)

    expected_dest = out_dir / "python" if profile == "default" else out_dir / "profiles" / profile / "python"
    assert (expected_dest / f"tamil_toolkit-{PY_VERSION}.tar.gz").is_file()
    assert (expected_dest / f"tamil_toolkit-{PY_VERSION}-cp311-abi3-win_amd64.whl").is_file()
    assert recorded_sdist_toml["project"]["license"] == "Apache-2.0 AND CC-BY-SA-4.0"
    expected_wheel_spdx = "Apache-2.0" if profile == "default" else "Apache-2.0 AND CC-BY-SA-4.0"
    assert recorded_wheel_toml["project"]["license"] == expected_wheel_spdx
    assert (ROOT / "bindings/python/pyproject.toml").read_text(encoding="utf-8") == checked_in_pyproject


def _copy_lightweight_lexicon_sources(fake_repo: Path, source_root: Path = ROOT) -> None:
    shutil.copytree(source_root / "tests/golden", fake_repo / "tests/golden")
    shutil.copytree(source_root / "schemas/lexicon", fake_repo / "schemas/lexicon")
    shutil.copy2(source_root / "THIRD_PARTY_NOTICES.md", fake_repo / "THIRD_PARTY_NOTICES.md")
    for cfg in release_files.DICTIONARY_PACK_PROFILES.values():
        source_dir = cfg["source_dir"]
        dest_dir = fake_repo / source_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        for rel in release_files.DICTIONARY_FILES:
            target = dest_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            # Profile notice validation checks the signed file inventory too.
            shutil.copy2(source_root / source_dir / rel, target)


@pytest.mark.parametrize("profile", ["default", "core", "full"])
def test_npm_orchestration_packs_staged_dir_without_mutating_repo_package_json(
    tmp_path: Path,
    monkeypatch,
    small_canonical_repo: Path,
    profile: str,
) -> None:
    fake_repo = tmp_path / "repo"
    fake_js = _make_fake_js_wasm_dir(fake_repo / "bindings/js-wasm")
    _copy_lightweight_lexicon_sources(fake_repo, source_root=small_canonical_repo)
    (fake_repo / "tools/release_smoke").mkdir(parents=True)
    for smoke in ("node_consumer.mjs", "types_consumer.ts"):
        shutil.copy2(ROOT / "tools/release_smoke" / smoke, fake_repo / "tools/release_smoke" / smoke)

    orig_pkg_text = (fake_js / "package.json").read_text(encoding="utf-8")
    out_dir = tmp_path / "alpha"
    monkeypatch.setattr(release, "ROOT", fake_repo)
    monkeypatch.setattr(release, "OUT", out_dir)
    monkeypatch.setattr(release, "SMOKE", fake_repo / "tools/release_smoke")
    monkeypatch.setattr(release, "sync", lambda check=False: None)
    monkeypatch.setattr(release, "licenses", lambda: None)

    pack_cwds: list[Path] = []

    def fake_run(*args, cwd=fake_repo, capture=False, env=None):
        cmd = tuple(str(a) for a in args)
        if "wasm-pack" in cmd or cmd == ("pnpm", "--filter", "tamil-toolkit", "build"):
            return None
        if cmd[:2] == ("npm", "pack"):
            pack_cwds.append(Path(cwd))
            dest = Path(args[args.index("--pack-destination") + 1])
            staged_pkg = json.loads((Path(cwd) / "package.json").read_text(encoding="utf-8"))
            _write_targz(
                dest / f"tamil-toolkit-{VERSION}.tgz",
                _valid_npm_tar_files(
                    profile=profile,
                    license_override=staged_pkg["license"],
                    files_override=staged_pkg["files"],
                ),
            )
            return None
        if cmd[:2] == ("npm", "install") or Path(cmd[0]).name in ("node", "node.exe"):
            return None
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(release, "run", fake_run)
    release.npm(profile=profile)

    assert len(pack_cwds) == 1
    assert pack_cwds[0] != fake_js
    assert (fake_js / "package.json").read_text(encoding="utf-8") == orig_pkg_text
    expected_dest = out_dir / "npm" if profile == "default" else out_dir / "profiles" / profile / "npm"
    assert (expected_dest / f"tamil-toolkit-{VERSION}.tgz").is_file()


def test_rust_orchestration_accepts_scoped_facade_and_separates_profile_outputs(
    tmp_path: Path,
    monkeypatch,
    small_canonical_repo: Path,
) -> None:
    fake_repo = tmp_path / "repo"
    for name in dict.fromkeys((*POLICY["public_crates"], "tamil-calendar")):
        (fake_repo / "crates" / name).mkdir(parents=True)
        (fake_repo / "crates" / name / "Cargo.toml").write_text(f'[package]\nname = "{name}"\n', encoding="utf-8")
    _copy_lightweight_lexicon_sources(fake_repo, source_root=small_canonical_repo)
    (fake_repo / "tools/release_smoke").mkdir(parents=True)
    shutil.copy2(ROOT / "tools/release_smoke/rust_consumer.rs", fake_repo / "tools/release_smoke/rust_consumer.rs")

    out_dir = tmp_path / "alpha"
    monkeypatch.setattr(release, "ROOT", fake_repo)
    monkeypatch.setattr(release, "OUT", out_dir)
    monkeypatch.setattr(release, "SMOKE", fake_repo / "tools/release_smoke")
    monkeypatch.setattr(release, "sync", lambda check=False: None)
    monkeypatch.setattr(release, "load", lambda root=fake_repo: POLICY)

    def fake_run(*args, cwd=fake_repo, capture=False, env=None):
        if args[:2] == ("cargo", "package"):
            for name in (*POLICY["public_crates"], "tamil-calendar"):
                _write_targz(fake_repo / "target/package" / f"{name}-{VERSION}.crate", _valid_crate_files(name))
            return None
        if args[:2] == ("cargo", "run"):
            return None
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(release, "run", fake_run)
    release.rust(profile="core")

    core_rust = out_dir / "profiles/core/rust"
    assert (core_rust / f"tamil-toolkit-{VERSION}.crate").is_file()
    assert (core_rust / f"tamil-core-{VERSION}.crate").is_file()
    assert not (out_dir / "rust").exists()

