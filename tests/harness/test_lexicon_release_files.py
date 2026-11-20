from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import release_files, release_policy  # noqa: E402


EXPECTED_DICT_RELPATHS = (
    "ATTRIBUTION_AND_TERMS.md",
    "assertions.csv",
    "decisions.csv",
    "entries.csv",
    "evidence.csv",
    "forms.csv",
    "identities.csv",
    "labels.csv",
    "notices/ATTRIBUTION_AND_LICENSE.md",
    "notices/CC-BY-SA-4.0.md",
    "pack_members.csv",
    "packs.toml",
    "relations.csv",
    "schema.toml",
    "scopes.csv",
    "senses.csv",
    "sources.csv",
    "texts.csv",
    "unicode_exceptions.csv",
    "vocabularies.toml",
)

EXPECTED_SCHEMA_FILES = (
    "common.schema.json",
    "intake.schema.json",
    "lexical.schema.json",
    "review.schema.json",
)


def _copy_minimal_repo(tmp_path: Path, *, source_repo: Path | None = None) -> Path:
    repo = tmp_path / "repo"
    if source_repo is not None:
        shutil.copytree(source_repo, repo)
        return repo

    repo.mkdir(parents=True, exist_ok=True)
    for rel in (
        "Cargo.toml",
        "Cargo.lock",
        "LICENSE",
        "release-policy.toml",
    ):
        shutil.copy2(ROOT / rel, repo / rel)

    shutil.copytree(ROOT / "tests/reference", repo / "tests/reference")
    shutil.copytree(ROOT / "tests/golden", repo / "tests/golden")
    shutil.copytree(ROOT / "lexicon", repo / "lexicon")
    shutil.copytree(ROOT / "schemas/lexicon", repo / "schemas/lexicon")
    shutil.copytree(ROOT / "crates", repo / "crates")
    for binding in ("python", "js-wasm", "dart-flutter"):
        (repo / "bindings" / binding).mkdir(parents=True, exist_ok=True)
        for manifest in ("Cargo.toml", "pyproject.toml", "package.json", "pubspec.yaml"):
            src = ROOT / "bindings" / binding / manifest
            if src.is_file():
                shutil.copy2(src, repo / "bindings" / binding / manifest)
    (repo / "bindings/dart-flutter/rust").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "bindings/dart-flutter/rust/Cargo.toml",
        repo / "bindings/dart-flutter/rust/Cargo.toml",
    )
    return repo


def _copy_policy_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "policy-repo"
    repo.mkdir(parents=True, exist_ok=True)
    for rel in ("Cargo.toml", "release-policy.toml", "tests/golden/manifest.json"):
        dest = repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    for source in (ROOT / "docs/specs").glob("*.md"):
        dest = repo / source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    for crate_dir in (ROOT / "crates").iterdir():
        dest = repo / "crates" / crate_dir.name / "Cargo.toml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(crate_dir / "Cargo.toml", dest)
    for binding in ("python", "js-wasm", "dart-flutter"):
        for manifest in ("pyproject.toml", "package.json"):
            src = ROOT / "bindings" / binding / manifest
            if src.is_file():
                dest = repo / "bindings" / binding / manifest
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
    for manifest in (
        ROOT / "bindings/python/Cargo.toml",
        ROOT / "bindings/js-wasm/Cargo.toml",
        ROOT / "bindings/dart-flutter/rust/Cargo.toml",
    ):
        rel = manifest.relative_to(ROOT)
        dest = repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest, dest)
    return repo


@pytest.mark.xdist_group("real_lexicon_packs")
def test_expected_dictionary_mapping_count_and_no_dev_only_assets(
    real_release_files_validation: dict,
) -> None:
    assert release_files.DICTIONARY_FILES == EXPECTED_DICT_RELPATHS
    assert release_files.DICTIONARY_SCHEMAS == EXPECTED_SCHEMA_FILES

    expected = real_release_files_validation["expected_files"]
    dict_targets = sorted(
        str(p.relative_to(ROOT).as_posix())
        for p in expected
        if p.relative_to(ROOT).as_posix().startswith("crates/tamil-toolkit/lexicon/dictionary/")
    )
    names_taxa_targets = sorted(
        str(p.relative_to(ROOT).as_posix())
        for p in expected
        if p.relative_to(ROOT).as_posix().startswith("crates/tamil-toolkit/lexicon/packs/names_taxa/")
    )
    regional_targets = sorted(
        str(p.relative_to(ROOT).as_posix())
        for p in expected
        if p.relative_to(ROOT).as_posix().startswith("crates/tamil-toolkit/lexicon/packs/regional/")
    )
    schema_targets = sorted(
        str(p.relative_to(ROOT).as_posix())
        for p in expected
        if p.relative_to(ROOT).as_posix().startswith("crates/tamil-toolkit/schemas/lexicon/")
    )

    assert dict_targets == [
        f"crates/tamil-toolkit/lexicon/dictionary/{rel}" for rel in EXPECTED_DICT_RELPATHS
    ]
    assert names_taxa_targets == [
        f"crates/tamil-toolkit/lexicon/packs/names_taxa/{rel}" for rel in EXPECTED_DICT_RELPATHS
    ]
    assert regional_targets == [
        f"crates/tamil-toolkit/lexicon/packs/regional/{rel}" for rel in EXPECTED_DICT_RELPATHS
    ]
    assert schema_targets == [
        f"crates/tamil-toolkit/schemas/lexicon/{name}" for name in EXPECTED_SCHEMA_FILES
    ]
    assert len(expected) == 65 + (20 * 3) + 4

    all_rel = [p.relative_to(ROOT).as_posix() for p in expected]
    assert all("cldf" not in rel for rel in all_rel)
    assert all("curation" not in rel for rel in all_rel)
    assert all("wiktionary-core-approval" not in rel for rel in all_rel)
    # Schema JSON files must live outside crates/tamil-toolkit/lexicon/.
    assert all(
        not (rel.startswith("crates/tamil-toolkit/lexicon/") and rel.endswith(".json"))
        for rel in all_rel
    )
    # Lower crates must not receive dictionary files or schemas.
    for lower in (
        "tamil-core",
        "tamil-norm",
        "tamil-collate",
        "tamil-numerals",
        "tamil-calendar",
        "tamil-codec",
        "tamil-hyphen",
    ):
        assert all(not rel.startswith(f"crates/{lower}/lexicon/dictionary") for rel in all_rel)
        assert all(not rel.startswith(f"crates/{lower}/schemas") for rel in all_rel)


@pytest.mark.xdist_group("real_lexicon_packs")
def test_sync_and_check_round_trip_with_stale_missing_and_extra_files(
    tmp_path: Path,
    small_canonical_repo: Path,
    real_release_files_validation: dict,
) -> None:
    assert real_release_files_validation["synced"] is True
    repo = _copy_minimal_repo(tmp_path, source_repo=small_canonical_repo)
    release_files.sync(repo, check=False)
    release_files.sync(repo, check=True)

    # Verify exact SHA-256 parity between canonical sources and synced copies.
    for rel in EXPECTED_DICT_RELPATHS:
        src = (repo / "lexicon/dictionary" / rel).read_bytes()
        dst = (repo / "crates/tamil-toolkit/lexicon/dictionary" / rel).read_bytes()
        assert hashlib.sha256(src).hexdigest() == hashlib.sha256(dst).hexdigest()
    for name in EXPECTED_SCHEMA_FILES:
        src = (repo / "schemas/lexicon" / name).read_bytes()
        dst = (repo / "crates/tamil-toolkit/schemas/lexicon" / name).read_bytes()
        assert src == dst

    # Stale copy fails check.
    target = repo / "crates/tamil-toolkit/lexicon/dictionary/entries.csv"
    target.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Stale release copies"):
        release_files.sync(repo, check=True)
    release_files.sync(repo, check=False)
    release_files.sync(repo, check=True)

    # Missing copy fails check.
    schema_dst = repo / "crates/tamil-toolkit/schemas/lexicon/intake.schema.json"
    schema_dst.unlink()
    with pytest.raises(ValueError, match="Stale release copies"):
        release_files.sync(repo, check=True)
    release_files.sync(repo, check=False)
    release_files.sync(repo, check=True)

    # Extra unapproved file inside target crate directory fails check and is pruned by sync.
    extra_dst = repo / "crates/tamil-toolkit/lexicon/dictionary/private_notes.csv"
    extra_dst.write_text("secret\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unexpected"):
        release_files.sync(repo, check=True)
    release_files.sync(repo, check=False)
    assert not extra_dst.exists()
    release_files.sync(repo, check=True)


def test_canonical_validation_rejects_unapproved_or_tampered_sources(
    tmp_path: Path,
    small_canonical_repo: Path,
) -> None:
    # 1. Extra unapproved file in canonical lexicon/dictionary fails.
    repo = _copy_minimal_repo(tmp_path / "extra_src", source_repo=small_canonical_repo)
    (repo / "lexicon/dictionary/raw_dump.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        release_files.validate_dictionary_sources(repo)

    # 2. l3_pack_eligible = false fails.
    repo = _copy_minimal_repo(tmp_path / "ineligible", source_repo=small_canonical_repo)
    packs_path = repo / "lexicon/dictionary/packs.toml"
    packs_text = packs_path.read_text(encoding="utf-8")
    packs_path.write_text(
        packs_text.replace("l3_pack_eligible = true", "l3_pack_eligible = false"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        release_files.validate_dictionary_sources(repo)

    # 3. Manifest digest tamper fails.
    repo = _copy_minimal_repo(tmp_path / "bad_manifest", source_repo=small_canonical_repo)
    packs_path = repo / "lexicon/dictionary/packs.toml"
    packs_text = packs_path.read_text(encoding="utf-8")
    tampered_packs, sub_count = re.subn(
        r'manifest_sha256 = "[0-9a-f]{64}"',
        'manifest_sha256 = "' + ("0" * 64) + '"',
        packs_text,
        count=1,
    )
    assert sub_count == 1
    packs_path.write_text(tampered_packs, encoding="utf-8")
    with pytest.raises(ValueError):
        release_files.validate_dictionary_sources(repo)

    # 4. Path traversal or unsafe file reference fails.
    repo = _copy_minimal_repo(tmp_path / "traversal", source_repo=small_canonical_repo)
    packs_path = repo / "lexicon/dictionary/packs.toml"
    packs_path.write_text(
        packs_path.read_text(encoding="utf-8").replace(
            'path = "notices/CC-BY-SA-4.0.md"',
            'path = "../CC-BY-SA-4.0.md"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        release_files.validate_dictionary_sources(repo)

    # 5. Missing CC legal notice / unverified source fails.
    repo = _copy_minimal_repo(tmp_path / "unverified_src", source_repo=small_canonical_repo)
    sources_path = repo / "lexicon/dictionary/sources.csv"
    sources_path.write_text(
        sources_path.read_text(encoding="utf-8").replace(",verified,", ",pending,", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        release_files.validate_dictionary_sources(repo)

    repo = _copy_minimal_repo(tmp_path / "bad_cc", source_repo=small_canonical_repo)
    (repo / "lexicon/dictionary/notices/CC-BY-SA-4.0.md").write_text(
        "truncated license", encoding="utf-8"
    )
    with pytest.raises(ValueError):
        release_files.validate_dictionary_sources(repo)


@pytest.mark.xdist_group("real_lexicon_packs")
def test_license_boundary_and_artifact_notice_api(
    tmp_path: Path,
    small_canonical_repo: Path,
) -> None:
    notice_bytes = release_files.notices(ROOT)
    notice_text = notice_bytes.decode("utf-8")
    assert "CC-BY-SA-4.0" in notice_text
    assert "Wiktionary" in notice_text
    assert "lexicon/dictionary/notices/CC-BY-SA-4.0.md" in notice_text
    assert "MIT License" in notice_text or "MIT" in notice_text

    # Slim crates.io archive stays MIT (< 10 MiB); Python sdist carries MIT AND CC-BY-SA-4.0.
    assert release_files.artifact_license_spdx("tamil-toolkit") == "MIT"
    assert release_files.artifact_license_spdx("python-sdist") == "MIT AND CC-BY-SA-4.0"

    # Lower crates and default zero-data profiles stay strictly MIT.
    assert release_files.artifact_license_spdx("tamil-core") == "MIT"
    assert release_files.artifact_license_spdx("python-wheel") == "MIT"
    assert release_files.artifact_license_spdx("npm") == "MIT"
    assert release_files.artifact_license_spdx("dart") == "MIT"

    # Enabling the 'core' profile on binary artifacts upgrades SPDX & notice list.
    assert release_files.artifact_license_spdx("python-wheel", profiles=("core",)) == "MIT AND CC-BY-SA-4.0"
    assert release_files.artifact_license_spdx("npm", profiles=("core",)) == "MIT AND CC-BY-SA-4.0"
    assert release_files.artifact_license_spdx("dart", profiles=("core",)) == "MIT AND CC-BY-SA-4.0"

    assert release_files.artifact_notice_paths("tamil-toolkit", root=ROOT) == ["THIRD_PARTY_NOTICES.md"]
    sdist_notices = release_files.artifact_notice_paths("python-sdist", root=ROOT)
    assert sdist_notices == [
        "THIRD_PARTY_NOTICES.md",
        "lexicon/dictionary/ATTRIBUTION_AND_TERMS.md",
        "lexicon/dictionary/notices/ATTRIBUTION_AND_LICENSE.md",
        "lexicon/dictionary/notices/CC-BY-SA-4.0.md",
        "lexicon/packs/names_taxa/ATTRIBUTION_AND_TERMS.md",
        "lexicon/packs/names_taxa/notices/ATTRIBUTION_AND_LICENSE.md",
        "lexicon/packs/names_taxa/notices/CC-BY-SA-4.0.md",
        "lexicon/packs/regional/ATTRIBUTION_AND_TERMS.md",
        "lexicon/packs/regional/notices/ATTRIBUTION_AND_LICENSE.md",
        "lexicon/packs/regional/notices/CC-BY-SA-4.0.md",
    ]
    assert release_files.artifact_notice_paths("python-wheel", root=ROOT) == ["THIRD_PARTY_NOTICES.md"]
    assert release_files.artifact_notice_paths("python-wheel", profiles=("core",), root=ROOT) == [
        "THIRD_PARTY_NOTICES.md",
        "lexicon/dictionary/ATTRIBUTION_AND_TERMS.md",
        "lexicon/dictionary/notices/ATTRIBUTION_AND_LICENSE.md",
        "lexicon/dictionary/notices/CC-BY-SA-4.0.md",
    ]
    assert (
        release_files.artifact_notice_paths(
            "python-wheel", profiles=("core", "names_taxa", "regional"), root=ROOT
        )
        == sdist_notices
    )

    with pytest.raises(ValueError):
        release_files.artifact_notice_paths("tamil-core", profiles=("core",), root=ROOT)

    dest = tmp_path / "dist-notices"
    copied = release_files.copy_profile_notices(
        dest, profiles=("core",), root=small_canonical_repo
    )
    assert len(copied) == 4
    assert (dest / "THIRD_PARTY_NOTICES.md").is_file()
    assert (dest / "lexicon/dictionary/notices/CC-BY-SA-4.0.md").is_file()

    dest_all = tmp_path / "dist-notices-all"
    copied_all = release_files.copy_profile_notices(
        dest_all, profiles=("core", "names_taxa", "regional"), root=ROOT
    )
    assert len(copied_all) == 10
    assert (dest_all / "lexicon/dictionary/notices/CC-BY-SA-4.0.md").is_file()
    assert (dest_all / "lexicon/packs/names_taxa/notices/CC-BY-SA-4.0.md").is_file()
    assert (dest_all / "lexicon/packs/regional/notices/CC-BY-SA-4.0.md").is_file()


def test_release_policy_scopes_dual_license_only_to_facade_crate(tmp_path: Path) -> None:
    policy = release_policy.check(ROOT)
    assert policy["crate_licenses"] == {}

    # Lower crate cannot override workspace MIT license.
    repo = _copy_policy_repo(tmp_path / "lower_override")
    core_toml = repo / "crates/tamil-core/Cargo.toml"
    core_toml.write_text(
        core_toml.read_text(encoding="utf-8").replace(
            "license.workspace = true", 'license = "MIT AND CC-BY-SA-4.0"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="inherit workspace"):
        release_policy.check(repo)

    # release-policy.toml cannot add lower crates to [crate_licenses].
    repo2 = _copy_policy_repo(tmp_path / "bad_policy_key")
    policy_toml = repo2 / "release-policy.toml"
    policy_toml.write_text(
        policy_toml.read_text(encoding="utf-8") + '\ntamil-core = "MIT AND CC-BY-SA-4.0"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="crate_licenses"):
        release_policy.check(repo2)

    # Facade crate bundling lexicon/dictionary without scoped CC-BY-SA-4.0 license fails policy check.
    repo3 = _copy_policy_repo(tmp_path / "missing_cc_license")
    tk_toml = repo3 / "crates/tamil-toolkit/Cargo.toml"
    tk_toml.write_text(
        tk_toml.read_text(encoding="utf-8").replace(
            '"lexicon/*.toml",', '"lexicon/*.toml",\n  "lexicon/dictionary/*.csv",'
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        release_policy.check(repo3)


@pytest.mark.xdist_group("real_lexicon_packs")
def test_tamil_toolkit_cargo_include_and_package_list(shared_cargo_lock) -> None:
    manifest = tomllib.loads((ROOT / "crates/tamil-toolkit/Cargo.toml").read_text(encoding="utf-8"))
    pkg = manifest["package"]
    assert pkg["license"] == {"workspace": True}
    include = pkg["include"]
    assert "lexicon/dictionary/*.csv" not in include
    assert "lexicon/packs/*/*.csv" not in include
    assert "lexicon/**" not in include

    with shared_cargo_lock():
        result = subprocess.run(
            [shutil.which("cargo") or str(Path.home() / ".cargo/bin/cargo.exe"),
             "package", "-p", "tamil-toolkit", "--list", "--allow-dirty"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    listed = {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}
    for root_file in ("LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"):
        assert root_file in listed
    assert all(not item.startswith(("lexicon/dictionary/", "lexicon/packs/", "schemas/lexicon/")) for item in listed)
    assert all("cldf" not in item for item in listed)
    assert all("curation" not in item for item in listed)
    assert all(
        not (item.startswith("lexicon/") and item.endswith(".json")) for item in listed
    )


def test_xdist_session_cache_and_shared_artifact_locks_isolate_across_workers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify cross-process file locks, fingerprint-bound session caches, and -n loadgroup defaulting."""
    import importlib
    import importlib.util
    from types import SimpleNamespace

    root_spec = importlib.util.spec_from_file_location("_root_conftest_under_test", ROOT / "conftest.py")
    assert root_spec is not None and root_spec.loader is not None
    root_conftest = importlib.util.module_from_spec(root_spec)
    root_spec.loader.exec_module(root_conftest)
    conftest_path = Path(__file__).resolve().with_name("conftest.py")
    spec = importlib.util.spec_from_file_location("_harness_conftest_under_test", conftest_path)
    assert spec is not None and spec.loader is not None
    harness_conftest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness_conftest)

    # 1. Cross-worker session root resolves to shared parent on xdist workers, base locally.
    factory = SimpleNamespace(getbasetemp=lambda: tmp_path / "run" / "popen-gw0")
    req_gw0 = SimpleNamespace(config=SimpleNamespace(workerinput={"workerid": "gw0"}))
    req_gw1 = SimpleNamespace(config=SimpleNamespace(workerinput={"workerid": "gw1"}))
    factory_gw1 = SimpleNamespace(getbasetemp=lambda: tmp_path / "run" / "popen-gw1")

    shared_0 = harness_conftest._shared_session_root(req_gw0, factory)
    shared_1 = harness_conftest._shared_session_root(req_gw1, factory_gw1)
    assert shared_0 == shared_1 == tmp_path / "run" / "xdist-shared"

    # 2. Key/path confinement + fingerprint invalidation prevent stale unconditional cache hits.
    with pytest.raises(ValueError, match="Invalid shared fixture key"):
        harness_conftest._run_once_dir(shared_0, "../escape", lambda root: root)
    with pytest.raises(ValueError, match="Invalid shared fixture key"):
        harness_conftest._run_once_json(shared_0, "../escape", lambda: {})
    with pytest.raises(ValueError, match="outside directory"):
        harness_conftest._run_once_dir(shared_0, "outside-dir", lambda _root: tmp_path)

    src_dir = tmp_path / "inputs"
    src_dir.mkdir()
    input_file = src_dir / "pack.csv"
    input_file.write_text("row,1\n", encoding="utf-8")

    calls = {"json": 0, "dir": 0}

    def build_json() -> dict[str, int]:
        calls["json"] += 1
        return {"count": calls["json"]}

    def build_dir(work_root: Path) -> Path:
        calls["dir"] += 1
        out = work_root / "built"
        out.mkdir(parents=True, exist_ok=True)
        (out / "marker.txt").write_text(f"build-{calls['dir']}\n", encoding="utf-8")
        return out

    fp_v1 = harness_conftest._fingerprint_paths((src_dir,), base=tmp_path)
    assert harness_conftest._run_once_json(shared_0, "sample-json", build_json, fingerprint=fp_v1) == {"count": 1}
    assert harness_conftest._run_once_json(shared_1, "sample-json", build_json, fingerprint=fp_v1) == {"count": 1}
    assert calls["json"] == 1

    dir_0 = harness_conftest._run_once_dir(shared_0, "sample-dir", build_dir, fingerprint=fp_v1)
    dir_1 = harness_conftest._run_once_dir(shared_1, "sample-dir", build_dir, fingerprint=fp_v1)
    assert dir_0 == dir_1
    assert (dir_1 / "marker.txt").read_text(encoding="utf-8") == "build-1\n"
    assert calls["dir"] == 1

    # Changing an input byte invalidates cached JSON and directory entries cleanly.
    input_file.write_text("row,2\n", encoding="utf-8")
    fp_v2 = harness_conftest._fingerprint_paths((src_dir,), base=tmp_path)
    assert fp_v2 != fp_v1
    assert harness_conftest._run_once_json(shared_1, "sample-json", build_json, fingerprint=fp_v2) == {"count": 2}
    assert calls["json"] == 2
    dir_2 = harness_conftest._run_once_dir(shared_1, "sample-dir", build_dir, fingerprint=fp_v2)
    assert (dir_2 / "marker.txt").read_text(encoding="utf-8") == "build-2\n"
    assert calls["dir"] == 2

    # 3. Actual cross-PROCESS advisory lock & once-per-session execution across 4 child OS processes.
    proc_shared = tmp_path / "proc-shared"
    lock_file = tmp_path / "proc-artifact.lock"
    trace_file = tmp_path / "proc-trace.log"
    build_counter = tmp_path / "proc-builds.log"
    worker_script = (
        "import importlib.util, os, sys, time\n"
        "from pathlib import Path\n"
        "conftest_path = Path(sys.argv[1])\n"
        "lock_path = Path(sys.argv[2])\n"
        "trace_path = Path(sys.argv[3])\n"
        "shared_root = Path(sys.argv[4])\n"
        "counter_path = Path(sys.argv[5])\n"
        "fp = sys.argv[6]\n"
        "wid = sys.argv[7]\n"
        "spec = importlib.util.spec_from_file_location('hc', conftest_path)\n"
        "hc = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(hc)\n"
        "with hc.cross_worker_lock(lock_path, timeout_seconds=30.0):\n"
        "    with trace_path.open('a', encoding='utf-8') as f:\n"
        "        f.write(f'{wid}:enter\\n')\n"
        "    time.sleep(0.05)\n"
        "    with trace_path.open('a', encoding='utf-8') as f:\n"
        "        f.write(f'{wid}:exit\\n')\n"
        "def _mk():\n"
        "    with counter_path.open('a', encoding='utf-8') as f:\n"
        "        f.write(f'{wid}\\n')\n"
        "    return {'owner': wid}\n"
        "val = hc._run_once_json(shared_root, 'proc-once', _mk, fingerprint=fp)\n"
        "assert 'owner' in val\n"
    )
    procs = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                worker_script,
                str(conftest_path),
                str(lock_file),
                str(trace_file),
                str(proc_shared),
                str(build_counter),
                fp_v2,
                f"p{idx}",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for idx in range(4)
    ]
    for proc in procs:
        out, err = proc.communicate(timeout=30)
        assert proc.returncode == 0, f"worker failed: stdout={out!r}, stderr={err!r}"

    trace_lines = trace_file.read_text(encoding="utf-8").splitlines()
    assert len(trace_lines) == 8
    for idx in range(0, 8, 2):
        wid_enter, act_enter = trace_lines[idx].split(":", 1)
        wid_exit, act_exit = trace_lines[idx + 1].split(":", 1)
        assert act_enter == "enter" and act_exit == "exit" and wid_enter == wid_exit
    assert len(build_counter.read_text(encoding="utf-8").splitlines()) == 1

    # 4. Root conftest auto-selects loadgroup under -n unless --dist was explicitly provided.
    markers: list[tuple[str, str]] = []
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(tmp_path / "temproot"))

    def make_config(args: tuple[str, ...], dist: str = "load", numprocesses: int | None = 4):
        return SimpleNamespace(
            option=SimpleNamespace(basetemp=None, numprocesses=numprocesses, dist=dist),
            invocation_params=SimpleNamespace(args=args),
            addinivalue_line=lambda kind, line: markers.append((kind, line)),
        )

    cfg_auto = make_config(("-n", "auto", "tests/harness"))
    root_conftest.pytest_configure(cfg_auto)
    assert cfg_auto.option.dist == "loadgroup"

    cfg_explicit = make_config(("-n", "4", "--dist=worksteal", "tests/harness"), dist="worksteal")
    root_conftest.pytest_configure(cfg_explicit)
    assert cfg_explicit.option.dist == "worksteal"
    assert any("xdist_group" in line for _, line in markers)
