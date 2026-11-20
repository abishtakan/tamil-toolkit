"""Tests-first verification of profile-aware golden selection and binding/release alignment."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tools import harness, release, tasks


def _manifest_active_counts() -> tuple[int, int]:
    manifest = json.loads((harness.GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    baseline = 0
    core_only = 0
    for suite in manifest["suites"]:
        if suite.get("status") != "active":
            continue
        rows = len((harness.GOLDEN / suite["file"]).read_text(encoding="utf-8").splitlines())
        if suite.get("required_profile") is None:
            baseline += rows
        elif suite.get("required_profile") == "core":
            core_only += rows
    return baseline, core_only


@pytest.mark.xdist_group("real_golden_vectors")
def test_harness_select_vectors_honors_required_profile_and_reports_exclusions(
    real_golden_selections: dict,
) -> None:
    baseline_count, core_only_count = _manifest_active_counts()
    assert core_only_count == 44

    default_sel = real_golden_selections["default"]
    assert default_sel.profile == "default"
    assert default_sel.active_count == baseline_count
    assert default_sel.excluded_profile_count == core_only_count
    assert default_sel.excluded_profile_suites == (("lexicon_lookup.jsonl", "core", core_only_count),)
    assert default_sel.core_profile_count == 0
    assert default_sel.full_profile_count == 0
    assert default_sel.planned_count == 0
    assert len(default_sel.vectors) == baseline_count
    assert all(row["op"] not in {"lexicon_lookup", "lexicon_packs"} for row in default_sel.vectors)

    core_sel = real_golden_selections["core"]
    assert core_sel.profile == "core"
    assert core_sel.active_count == baseline_count + core_only_count
    assert core_sel.excluded_profile_count == 0
    assert core_sel.excluded_profile_suites == ()
    assert core_sel.core_profile_count == core_only_count
    assert core_sel.full_profile_count == 0
    assert core_sel.planned_count == 0
    assert len(core_sel.vectors) == baseline_count + core_only_count
    assert sum(1 for row in core_sel.vectors if row["op"] in {"lexicon_lookup", "lexicon_packs"}) == core_only_count

    full_sel = real_golden_selections["full"]
    assert full_sel.profile == "full"
    assert full_sel.active_count == baseline_count + full_sel.full_profile_count
    assert full_sel.core_profile_count == 0
    assert ("lexicon_lookup.jsonl", "core", core_only_count) in full_sel.excluded_profile_suites
    assert full_sel.excluded_profile_count >= core_only_count
    assert len(full_sel.vectors) == full_sel.active_count
    assert all(row["id"] != "lexicon_packs_core_043" for row in full_sel.vectors)

    # Unfiltered load_vectors() preserves full-corpus active count for schema/Unicode gates.
    assert len(real_golden_selections["all"]) == baseline_count + core_only_count + full_sel.full_profile_count
    assert len(harness.load_vectors(profile="default")) == baseline_count
    assert len(harness.load_vectors(profile="core")) == baseline_count + core_only_count
    assert len(harness.load_vectors(profile="full")) == full_sel.active_count


def test_harness_rejects_unknown_profile_or_profile_incompatible_planned_suite(
    tmp_path: Path,
    small_golden_dir: Path,
) -> None:
    with pytest.raises(ValueError, match="Unsupported or unapproved lexicon profile"):
        harness.select_vectors(profile="terminology")

    # Copy minimal valid golden dir into tmp_path and convert lexicon_lookup.jsonl back to planned
    # to verify incompatible planned selection fails loudly rather than silently skipping.
    golden_copy = tmp_path / "golden"
    shutil.copytree(small_golden_dir, golden_copy)
    manifest_path = golden_copy / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for suite in manifest["suites"]:
        if suite["file"] == "lexicon_lookup.jsonl":
            suite["status"] = "planned"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        harness.select_vectors(root=golden_copy, include_planned=("lexicon_lookup.jsonl",), profile="default")

    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        harness.select_vectors(root=golden_copy, include_planned=("lexicon_lookup.jsonl",), profile="full")

    # Dedicated required_profile='full' suite runs only under full and is excluded under core/default.
    full_suite = golden_copy / "lexicon_full_test.jsonl"
    full_suite.write_text(
        json.dumps(
            {
                "id": "lexicon_full_test_001",
                "op": "lexicon_packs",
                "input": None,
                "expected": [],
                "dialect": "COMMON",
                "tags": ["lexicon", "full"],
                "source": "synthetic full profile test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest["suites"].append(
        {
            "file": "lexicon_full_test.jsonl",
            "status": "active",
            "required_profile": "full",
            "operations": ["lexicon_packs"],
        }
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert harness.select_vectors(root=golden_copy, profile="full").full_profile_count == 1
    assert ("lexicon_full_test.jsonl", "full", 1) in harness.select_vectors(
        root=golden_copy, profile="core", include_planned=("lexicon_lookup.jsonl",)
    ).excluded_profile_suites

    # Missing core suite under core profile must also fail loudly (no silent skips).
    manifest["suites"] = [s for s in manifest["suites"] if s["file"] != "lexicon_lookup.jsonl"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (golden_copy / "lexicon_lookup.jsonl").unlink()
    with pytest.raises(ValueError, match="core"):
        harness.select_vectors(root=golden_copy, profile="core")


def test_harness_rejects_unknown_required_profile_in_manifest(
    tmp_path: Path,
    small_golden_dir: Path,
) -> None:
    golden_copy = tmp_path / "golden"
    shutil.copytree(small_golden_dir, golden_copy)
    manifest_path = golden_copy / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["suites"][0]["required_profile"] = "regional"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="required_profile"):
        harness.select_vectors(root=golden_copy, profile="default")


def test_release_fixtures_requires_explicit_profile_and_never_guesses(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "core")
    with pytest.raises(TypeError):
        release.fixtures(tmp_path)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="explicit profile"):
        release.fixtures(tmp_path, profile="")

    with pytest.raises(ValueError, match="Unsupported or unapproved lexicon profile"):
        release.fixtures(tmp_path, profile="bogus")

    monkeypatch.setenv("TAMIL_GOLDEN_INCLUDE_PLANNED", "lexicon_lookup.jsonl")
    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        release.fixtures(tmp_path, profile="default")
    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        release.fixtures(tmp_path, profile="full")


def test_tasks_profile_env_rejects_incompatible_planned_suite(monkeypatch) -> None:
    default_profile = tasks.resolve_lexicon_profile("default")
    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        tasks.profile_env(
            default_profile,
            base_env={"TAMIL_GOLDEN_INCLUDE_PLANNED": "lexicon_lookup.jsonl"},
        )
    full_profile = tasks.resolve_lexicon_profile("full")
    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        tasks.profile_env(
            full_profile,
            base_env={"TAMIL_GOLDEN_INCLUDE_PLANNED": "lexicon_lookup.jsonl"},
        )
    assert full_profile.planned_suites == ()
    # Implicit default of tasks remains canonical core after activation.
    monkeypatch.delenv("TAMIL_LEXICON_PROFILE", raising=False)
    assert tasks.resolve_lexicon_profile().name == "core"


def test_python_golden_harness_aligns_compiled_profile_and_rejects_mismatch(monkeypatch) -> None:
    import importlib
    import bindings.python.tests.test_golden as py_golden

    importlib.reload(py_golden)

    # Isolate profile resolution from whichever real binding the prior build installed.
    monkeypatch.setattr(py_golden.tamil, "lexicon_packs", lambda: [{"id": "core", "available": True}])

    # Compiled core binding without TAMIL_LEXICON_PROFILE infers 'core', not 'default'.
    monkeypatch.delenv("TAMIL_LEXICON_PROFILE", raising=False)
    monkeypatch.delenv("TAMIL_GOLDEN_INCLUDE_PLANNED", raising=False)
    assert py_golden.resolve_python_profile() == "core"

    # Explicit matching env succeeds.
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "core")
    assert py_golden.resolve_python_profile() == "core"

    # Mismatched env fails loudly.
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "default")
    with pytest.raises((AssertionError, ValueError, Exception), match="does not match compiled"):
        py_golden.resolve_python_profile()

    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "full")
    with pytest.raises((AssertionError, ValueError, Exception), match="does not match compiled"):
        py_golden.resolve_python_profile()

    # Unknown env fails loudly.
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "bogus")
    with pytest.raises((AssertionError, ValueError, Exception), match="Unsupported"):
        py_golden.resolve_python_profile()

    # Three compiled packs resolve cleanly as 'full'; partial packs fail loudly.
    full_packs = [
        {"id": pid, "available": True}
        for pid in ("core", "names_taxa", "regional")
    ]
    monkeypatch.setattr(py_golden.tamil, "lexicon_packs", lambda: full_packs)
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "full")
    assert py_golden.resolve_python_profile() == "full"
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "core")
    with pytest.raises((AssertionError, ValueError, Exception), match="does not match compiled"):
        py_golden.resolve_python_profile()
    monkeypatch.setattr(
        py_golden.tamil,
        "lexicon_packs",
        lambda: [{"id": "core", "available": True}, {"id": "regional", "available": True}],
    )
    with pytest.raises(AssertionError, match="Unsupported compiled Python lexicon packs"):
        py_golden.infer_compiled_python_profile()


def test_lexicon_dart_archive_cli_supports_full_profile(monkeypatch) -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "tools/lexicon_dart_archive.py", "--help"],
        cwd=harness.ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "full" in proc.stdout


@pytest.mark.parametrize("features", [(), ("lexicon-core",),
    ("lexicon-core", "lexicon-names-taxa", "lexicon-regional")])
def test_dart_archive_builds_selected_profile_before_using_library(tmp_path, monkeypatch, features):
    from types import SimpleNamespace
    import sys
    from tools import lexicon_dart_archive as archive

    monkeypatch.setattr(archive, "ROOT", tmp_path)
    monkeypatch.setattr(archive.shutil, "which", lambda name: "cargo-test" if name == "cargo" else None)
    suffix = ".dll" if sys.platform == "win32" else ".dylib" if sys.platform == "darwin" else ".so"
    prefix = "" if sys.platform == "win32" else "lib"
    library = tmp_path / "target/debug" / f"{prefix}tamil_toolkit_ffi{suffix}"
    calls = []

    def build(command, *, cwd, check):
        calls.append((command, cwd, check))
        library.parent.mkdir(parents=True)
        library.write_bytes(b"synthetic selected-profile library")

    monkeypatch.setattr(archive.subprocess, "run", build)
    assert archive.build_profile_library(SimpleNamespace(features=features)) == library
    expected = ["cargo-test", "build", "--locked", "-p", "tamil-dart"]
    if features:
        expected += ["--features", ",".join(features)]
    assert calls == [(expected, tmp_path, True)]


def test_xdist_group_marks_single_and_cover_real_pack_fixtures(
    small_golden_dir: Path,
) -> None:
    """Guard against loadgroup composite-group splits and ungrouped real-pack fixtures."""
    import ast

    real_fixtures = {
        "real_candidate_verification",
        "real_homograph_verification",
        "real_reviewed_verification",
        "real_core_canonical_validation",
        "real_release_files_validation",
        "real_golden_selections",
    }

    def _xdist_groups_on_func(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        groups: list[str] = []
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            is_xdist = (
                isinstance(func, ast.Attribute) and func.attr == "xdist_group"
            ) or (isinstance(func, ast.Name) and func.id == "xdist_group")
            if not is_xdist:
                continue
            name_val: str | None = None
            if (
                dec.args
                and isinstance(dec.args[0], ast.Constant)
                and isinstance(dec.args[0].value, str)
            ):
                name_val = dec.args[0].value
            else:
                for kw in dec.keywords:
                    if (
                        kw.arg == "name"
                        and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)
                    ):
                        name_val = kw.value.value
                        break
            groups.append(name_val or "<dynamic>")
        return groups

    harness_dir = Path(__file__).resolve().parent
    for test_file in sorted(harness_dir.glob("test_*.py")):
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                continue
            groups = _xdist_groups_on_func(node)
            assert len(groups) <= 1, (
                f"{test_file.name}::{node.name} has multiple xdist_group marks {groups!r}; "
                "loadgroup merges multiple marks into a separate composite group."
            )
            params = {arg.arg for arg in node.args.args}
            used_real = params & real_fixtures
            if used_real:
                assert len(groups) == 1, (
                    f"{test_file.name}::{node.name} consumes {sorted(used_real)} without a single xdist_group mark"
                )

    # Minimal small_golden_dir retains COMMON/TN/SL baseline + lexicon_lookup without cloning full baseline.
    sel_core = harness.select_vectors(root=small_golden_dir, profile="core")
    assert {row["dialect"] for row in sel_core.vectors} == {"COMMON", "TN", "SL"}
    assert sel_core.core_profile_count == 44
