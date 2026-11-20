"""Shared xdist-safe session caches, artifact locks, and small fixtures for tests/harness."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Callable, Iterator, Sequence

import pytest

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import harness, release_files  # noqa: E402
from tools.lexicon_packs import load_canonical_pack, promote, validate_canonical_dir  # noqa: E402
from tools.lexicon_tables import read_rows, write_rows  # noqa: E402
from tools.lexicon_wiktionary_candidate import (  # noqa: E402
    CANDIDATE_DIR,
    HOMOGRAPH_DIR,
    REVIEWED_DIR,
    verify_candidate_workspace,
    verify_reviewed_workspace,
)


def _shared_session_root(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    """Return a run-scoped directory shared across all xdist workers in this invocation."""
    base = tmp_path_factory.getbasetemp()
    if hasattr(request.config, "workerinput"):
        root = base.parent / "xdist-shared"
    else:
        root = base / "xdist-shared"
    root.mkdir(parents=True, exist_ok=True)
    return root


@contextmanager
def cross_worker_lock(lock_path: Path, *, timeout_seconds: float = 600.0) -> Iterator[None]:
    """Acquire a cross-process advisory file lock independent of xdist_group labels."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if sys.platform == "win32":
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            deadline = time.monotonic() + timeout_seconds
            while True:
                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"Timed out waiting for cross-worker lock {lock_path}"
                        ) from exc
                    time.sleep(0.05)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            deadline = time.monotonic() + timeout_seconds
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError as exc:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timed out waiting for cross-worker lock {lock_path}") from exc
                    time.sleep(0.05)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _validate_cache_key(shared_root: Path, subdir: str, key: str) -> tuple[Path, Path]:
    """Validate key and confine cache directory and entry paths inside shared_root."""
    if not key or key in {".", ".."} or any(c in key for c in "/\\:"):
        raise ValueError("Invalid shared fixture key")
    resolved_root = shared_root.resolve()
    cache_dir = (resolved_root / subdir).resolve()
    if not cache_dir.is_relative_to(resolved_root):
        raise ValueError("Shared fixture cache escapes session directory")
    entry_dir = (cache_dir / key).resolve()
    if entry_dir.parent != cache_dir:
        raise ValueError("Shared fixture directory escapes cache")
    return cache_dir, entry_dir


def _fingerprint_paths(paths: Sequence[Path], *, base: Path = ROOT) -> str:
    """Compute a content+path SHA-256 fingerprint over checked-in or read-only trees."""
    hasher = hashlib.sha256()
    seen: set[Path] = set()
    entries: list[tuple[str, Path]] = []
    for raw_path in paths:
        path = Path(raw_path)
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    child_res = child.resolve()
                    try:
                        rel = child_res.relative_to(base.resolve()).as_posix()
                    except ValueError:
                        rel = child_res.as_posix()
                    entries.append((rel, child_res))
        elif path.is_file():
            try:
                rel = resolved.relative_to(base.resolve()).as_posix()
            except ValueError:
                rel = resolved.as_posix()
            entries.append((rel, resolved))
        else:
            hasher.update(b"M")
            hasher.update(resolved.as_posix().encode("utf-8"))
            hasher.update(b"\0")

    entries.sort(key=lambda item: item[0])
    for rel, file_path in entries:
        hasher.update(b"F")
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        file_digest = hashlib.sha256(file_path.read_bytes()).digest()
        hasher.update(file_digest)
    return hasher.hexdigest()


def _run_once_dir(
    shared_root: Path,
    key: str,
    builder: Callable[[Path], Path],
    *,
    fingerprint: str | None = None,
) -> Path:
    """Build a read-only shared directory at most once across all xdist workers."""
    if not key or key in {".", ".."} or any(c in key for c in "/\\:"):
        raise ValueError("Invalid shared fixture key")
    shared_root = shared_root.resolve()
    cache_dir = (shared_root / "dirs").resolve()
    if not cache_dir.is_relative_to(shared_root):
        raise ValueError("Shared fixture cache escapes session directory")
    work_root = (cache_dir / key).resolve()
    if work_root.parent != cache_dir:
        raise ValueError("Shared fixture directory escapes cache")
    ready = cache_dir / f"{key}.ready"
    fp_file = cache_dir / f"{key}.fp"
    with cross_worker_lock(cache_dir / f"{key}.lock"):
        if ready.is_file():
            target = Path(ready.read_text(encoding="utf-8").strip())
            if not target.resolve().is_relative_to(work_root):
                raise ValueError("Shared fixture readiness path escapes its directory")
            fp_matches = fingerprint is None or (
                fp_file.is_file() and fp_file.read_text(encoding="utf-8").strip() == fingerprint
            )
            if fp_matches and target.is_dir():
                return target
            ready.unlink(missing_ok=True)
            fp_file.unlink(missing_ok=True)

        if work_root.exists():
            shutil.rmtree(work_root)
        work_root.mkdir(parents=True, exist_ok=True)
        result_path = builder(work_root)
        if not result_path.resolve().is_relative_to(work_root):
            raise ValueError("Shared fixture builder returned an outside directory")
        if fingerprint is not None:
            tmp_fp = cache_dir / f"{key}.fp.tmp"
            tmp_fp.write_text(fingerprint + "\n", encoding="utf-8")
            tmp_fp.replace(fp_file)
        else:
            fp_file.unlink(missing_ok=True)
        tmp_ready = cache_dir / f"{key}.ready.tmp"
        tmp_ready.write_text(str(result_path) + "\n", encoding="utf-8")
        tmp_ready.replace(ready)
        return result_path


def _run_once_json(
    shared_root: Path,
    key: str,
    builder: Callable[[], Any],
    *,
    fingerprint: str | None = None,
) -> Any:
    """Compute and cache a JSON-serializable result at most once across all xdist workers."""
    cache_dir, _ = _validate_cache_key(shared_root, "json", key)
    data_path = (cache_dir / f"{key}.json").resolve()
    ready = (cache_dir / f"{key}.ready").resolve()
    if data_path.parent != cache_dir or ready.parent != cache_dir:
        raise ValueError("Shared JSON cache path escapes cache directory")
    with cross_worker_lock(cache_dir / f"{key}.lock"):
        if ready.is_file() and data_path.is_file():
            raw = json.loads(data_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "__cached_fingerprint__" in raw:
                if fingerprint is None or raw["__cached_fingerprint__"] == fingerprint:
                    return raw["payload"]
            elif fingerprint is None:
                return raw
            ready.unlink(missing_ok=True)
        payload = builder()
        envelope = (
            payload
            if fingerprint is None
            else {"__cached_fingerprint__": fingerprint, "payload": payload}
        )
        tmp_data = cache_dir / f"{key}.json.tmp"
        tmp_data.write_text(
            json.dumps(envelope, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        tmp_data.replace(data_path)
        tmp_ready = cache_dir / f"{key}.ready.tmp"
        tmp_ready.write_text("ok\n", encoding="utf-8")
        tmp_ready.replace(ready)
        return payload


def _promote_pack_from_reviewed(tmp_root: Path, pack_id: str, output_dir: Path) -> Path:
    """Promote REVIEWED_DIR (or a pack_id-retargeted copy for names_taxa/regional) into output_dir."""
    if pack_id == "core":
        promote(REVIEWED_DIR, pack="core", output=output_dir)
    else:
        ws_copy = tmp_root / f"ws_{pack_id}"
        shutil.copytree(REVIEWED_DIR, ws_copy)
        pm_path = ws_copy / "pack_members.csv"
        rows = list(read_rows(pm_path, "pack_members"))
        for row in rows:
            row["pack_id"] = pack_id
        write_rows(pm_path, "pack_members", rows)
        promote(ws_copy, pack=pack_id, output=output_dir)
    assert validate_canonical_dir(output_dir) == []
    return output_dir


def _build_small_core_canonical(work_root: Path) -> Path:
    return _promote_pack_from_reviewed(work_root, "core", work_root / "core")


def _build_small_golden_dir(work_root: Path) -> Path:
    dest = work_root / "golden"
    dest.mkdir(parents=True, exist_ok=True)
    src_golden = harness.GOLDEN
    manifest = json.loads((src_golden / "manifest.json").read_text(encoding="utf-8"))

    picked_lines: dict[str, str] = {}
    picked_ops: set[str] = set()
    for suite in manifest["suites"]:
        if suite.get("status") != "active" or suite.get("required_profile") is not None:
            continue
        for raw_line in (src_golden / suite["file"]).read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            row = json.loads(raw_line)
            dialect = row.get("dialect")
            if dialect in {"COMMON", "TN", "SL"} and dialect not in picked_lines:
                picked_lines[dialect] = raw_line
                picked_ops.add(row["op"])
            if len(picked_lines) == 3:
                break
        if len(picked_lines) == 3:
            break
    assert set(picked_lines) == {"COMMON", "TN", "SL"}

    (dest / "baseline_min.jsonl").write_text(
        "".join(picked_lines[d] + "\n" for d in ("COMMON", "TN", "SL")),
        encoding="utf-8",
        newline="\n",
    )
    shutil.copy2(src_golden / "lexicon_lookup.jsonl", dest / "lexicon_lookup.jsonl")

    lookup_suite = next(s for s in manifest["suites"] if s["file"] == "lexicon_lookup.jsonl")
    small_manifest = {
        "version": 1,
        "suites": [
            {
                "file": "baseline_min.jsonl",
                "status": "active",
                "operations": sorted(picked_ops),
            },
            dict(lookup_suite),
        ],
    }
    (dest / "manifest.json").write_text(json.dumps(small_manifest, indent=2) + "\n", encoding="utf-8")
    return dest


def _build_small_canonical_repo(
    work_root: Path,
    small_core_canonical: Path,
    small_golden_dir: Path,
) -> Path:
    repo = work_root / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    for rel in (
        "Cargo.toml",
        "Cargo.lock",
        "LICENSE",
        "README.md",
        "THIRD_PARTY_NOTICES.md",
        "release-policy.toml",
    ):
        shutil.copy2(ROOT / rel, repo / rel)

    shutil.copytree(ROOT / "schemas/lexicon", repo / "schemas/lexicon")
    shutil.copytree(small_golden_dir, repo / "tests/golden")

    # Copy notice reference license files needed by release_files.notices().
    notice_ref_files = (
        "tests/reference/unicode-17.0.0/LICENSE.txt",
        "tests/reference/codec-v0.1/LICENSE-ag.txt",
        "tests/reference/codec-v0.1/LICENSE-pakeetharan.txt",
        "tests/reference/codec-tscii/LICENSE.txt",
        "tests/reference/calendar-thirukanitham-v1/astro-LICENSE.md",
    )
    for rel in notice_ref_files:
        src = ROOT / rel
        if src.is_file():
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Copy minimal crate manifests/readmes without cloning 115MB of crates/tamil-toolkit/lexicon CSVs.
    for crate_dir in (ROOT / "crates").iterdir():
        if not crate_dir.is_dir():
            continue
        dst_crate = repo / "crates" / crate_dir.name
        dst_crate.mkdir(parents=True, exist_ok=True)
        for rel in ("Cargo.toml", "LICENSE", "README.md"):
            src = crate_dir / rel
            if src.is_file():
                shutil.copy2(src, dst_crate / rel)

    for binding in ("python", "js-wasm", "dart-flutter"):
        (repo / "bindings" / binding).mkdir(parents=True, exist_ok=True)
        for fname in ("Cargo.toml", "pyproject.toml", "package.json", "pubspec.yaml", "README.md"):
            src = ROOT / "bindings" / binding / fname
            if src.is_file():
                shutil.copy2(src, repo / "bindings" / binding / fname)
    (repo / "bindings/dart-flutter/rust").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "bindings/dart-flutter/rust/Cargo.toml",
        repo / "bindings/dart-flutter/rust/Cargo.toml",
    )

    (repo / "lexicon").mkdir(parents=True, exist_ok=True)
    for item in (ROOT / "lexicon").iterdir():
        if item.is_file():
            shutil.copy2(item, repo / "lexicon" / item.name)

    shutil.copytree(small_core_canonical, repo / "lexicon/dictionary")
    staging_tmp = work_root / "pack-stage"
    _promote_pack_from_reviewed(staging_tmp, "names_taxa", repo / "lexicon/packs/names_taxa")
    _promote_pack_from_reviewed(staging_tmp, "regional", repo / "lexicon/packs/regional")

    release_files.sync(repo, check=False)
    release_files.sync(repo, check=True)
    return repo


@pytest.fixture(scope="session")
def shared_session_root(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    return _shared_session_root(request, tmp_path_factory)


@pytest.fixture(scope="session")
def shared_cargo_lock(shared_session_root: Path) -> Callable[[], Any]:
    """Return a cross-process lock factory protecting shared ROOT/Cargo operations."""
    lock_path = shared_session_root / "locks" / "cargo_root.lock"
    return lambda: cross_worker_lock(lock_path)


@pytest.fixture(scope="session")
def small_core_canonical(shared_session_root: Path) -> Iterator[Path]:
    """Read-only small valid promoted 'core' canonical pack (6 entries, 31 assertions)."""
    inputs = (REVIEWED_DIR,)
    input_fp = _fingerprint_paths(inputs)
    canon_dir = _run_once_dir(
        shared_session_root,
        "small-core-canon",
        _build_small_core_canonical,
        fingerprint=input_fp,
    )
    out_fp = _fingerprint_paths((canon_dir,))
    yield canon_dir
    assert _fingerprint_paths(inputs) == input_fp, "Checked-in reviewed workspace mutated during session"
    assert _fingerprint_paths((canon_dir,)) == out_fp, "Read-only small_core_canonical mutated during session"


@pytest.fixture(scope="session")
def small_golden_dir(shared_session_root: Path) -> Iterator[Path]:
    """Read-only minimal valid tests/golden tree with COMMON/TN/SL baseline + lexicon_lookup."""
    inputs = (harness.GOLDEN / "manifest.json", harness.GOLDEN / "lexicon_lookup.jsonl")
    input_fp = _fingerprint_paths(inputs)
    golden_dir = _run_once_dir(
        shared_session_root,
        "small-golden",
        _build_small_golden_dir,
        fingerprint=input_fp,
    )
    out_fp = _fingerprint_paths((golden_dir,))
    yield golden_dir
    assert _fingerprint_paths(inputs) == input_fp, "Checked-in golden manifest/lookup mutated during session"
    assert _fingerprint_paths((golden_dir,)) == out_fp, "Read-only small_golden_dir mutated during session"


@pytest.fixture(scope="session")
def small_canonical_repo(
    shared_session_root: Path,
    small_core_canonical: Path,
    small_golden_dir: Path,
) -> Iterator[Path]:
    """Read-only minimal valid repo layout with small 3-pack promoted lexicon sources."""
    inputs = (
        small_core_canonical,
        small_golden_dir,
        ROOT / "schemas/lexicon",
        ROOT / "release-policy.toml",
        ROOT / "LICENSE",
    )
    input_fp = _fingerprint_paths(inputs)
    repo_dir = _run_once_dir(
        shared_session_root,
        "small-canon-repo",
        lambda work_root: _build_small_canonical_repo(
            work_root,
            small_core_canonical,
            small_golden_dir,
        ),
        fingerprint=input_fp,
    )
    out_fp = _fingerprint_paths((repo_dir,))
    yield repo_dir
    assert _fingerprint_paths(inputs) == input_fp, "small_canonical_repo inputs mutated during session"
    assert _fingerprint_paths((repo_dir,)) == out_fp, "Read-only small_canonical_repo mutated during session"


# ---------------------------------------------------------------------------
# Cross-worker session-scoped read-only caches for checked-in 11,370-entry full-pack gates
# (scheduled onto single xdist_group AND backed by fingerprint-bound cross-worker disk cache + locks).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_candidate_verification(shared_session_root: Path) -> Iterator[dict[str, Any]]:
    inputs = (CANDIDATE_DIR, ROOT / "lexicon" / "dictionary")
    pre_fp = _fingerprint_paths(inputs)
    result = _run_once_json(
        shared_session_root,
        "real-candidate-verification",
        lambda: verify_candidate_workspace(CANDIDATE_DIR),
        fingerprint=pre_fp,
    )
    yield result
    assert _fingerprint_paths(inputs) == pre_fp, "Checked-in candidate/core pack mutated during session"


@pytest.fixture(scope="session")
def real_homograph_verification(shared_session_root: Path) -> Iterator[dict[str, Any]]:
    inputs = (HOMOGRAPH_DIR, ROOT / "lexicon" / "dictionary")
    pre_fp = _fingerprint_paths(inputs)
    result = _run_once_json(
        shared_session_root,
        "real-homograph-verification",
        lambda: verify_candidate_workspace(HOMOGRAPH_DIR, dataset="homograph"),
        fingerprint=pre_fp,
    )
    yield result
    assert _fingerprint_paths(inputs) == pre_fp, "Checked-in homograph/core pack mutated during session"


@pytest.fixture(scope="session")
def real_reviewed_verification(shared_session_root: Path) -> Iterator[dict[str, Any]]:
    inputs = (REVIEWED_DIR, CANDIDATE_DIR, HOMOGRAPH_DIR, ROOT / "lexicon" / "dictionary")
    pre_fp = _fingerprint_paths(inputs)
    result = _run_once_json(
        shared_session_root,
        "real-reviewed-verification",
        lambda: verify_reviewed_workspace(REVIEWED_DIR),
        fingerprint=pre_fp,
    )
    yield result
    assert _fingerprint_paths(inputs) == pre_fp, "Checked-in reviewed/core pack mutated during session"


@pytest.fixture(scope="session")
def real_core_canonical_validation(shared_session_root: Path) -> Iterator[dict[str, Any]]:
    canon_dir = ROOT / "lexicon" / "dictionary"
    inputs = (canon_dir,)
    pre_fp = _fingerprint_paths(inputs)
    cached = _run_once_json(
        shared_session_root,
        "real-core-canonical-validation",
        lambda: {
            "canon_dir": str(canon_dir),
            "findings": validate_canonical_dir(canon_dir),
        },
        fingerprint=pre_fp,
    )
    resolved_dir = Path(cached["canon_dir"])
    yield {
        "canon_dir": resolved_dir,
        "findings": cached["findings"],
        "loaded": load_canonical_pack(resolved_dir),
        "fingerprint": pre_fp,
    }
    assert _fingerprint_paths(inputs) == pre_fp, "Checked-in lexicon/dictionary mutated during session"


@pytest.fixture(scope="session")
def real_release_files_validation(shared_session_root: Path) -> Iterator[dict[str, Any]]:
    inputs = (
        ROOT / "lexicon" / "dictionary",
        ROOT / "lexicon" / "packs" / "names_taxa",
        ROOT / "lexicon" / "packs" / "regional",
        ROOT / "schemas" / "lexicon",
        ROOT / "crates" / "tamil-toolkit" / "lexicon",
        ROOT / "crates" / "tamil-toolkit" / "schemas" / "lexicon",
        ROOT / "release-policy.toml",
    )
    pre_fp = _fingerprint_paths(inputs)

    def _compute() -> dict[str, Any]:
        expected = release_files.expected_files(ROOT)
        release_files.sync(ROOT, check=True)
        return {
            "expected_files": [str(path) for path in expected],
            "synced": True,
        }

    cached = _run_once_json(
        shared_session_root,
        "real-release-files-validation",
        _compute,
        fingerprint=pre_fp,
    )
    yield {
        "expected_files": [Path(p) for p in cached["expected_files"]],
        "synced": bool(cached["synced"]),
        "fingerprint": pre_fp,
    }
    assert _fingerprint_paths(inputs) == pre_fp, "Checked-in 3-pack lexicon or synced release files mutated during session"


def _selection_to_dict(selection: harness.GoldenSelection) -> dict[str, Any]:
    return {
        "profile": selection.profile,
        "vectors": list(selection.vectors),
        "active_count": selection.active_count,
        "planned_count": selection.planned_count,
        "core_profile_count": selection.core_profile_count,
        "excluded_profile_count": selection.excluded_profile_count,
        "excluded_profile_suites": [list(item) for item in selection.excluded_profile_suites],
        "selected_files": list(selection.selected_files),
        "full_profile_count": selection.full_profile_count,
    }


def _dict_to_selection(raw: dict[str, Any]) -> harness.GoldenSelection:
    return harness.GoldenSelection(
        profile=raw["profile"],
        vectors=tuple(raw["vectors"]),
        active_count=raw["active_count"],
        planned_count=raw["planned_count"],
        core_profile_count=raw["core_profile_count"],
        excluded_profile_count=raw["excluded_profile_count"],
        excluded_profile_suites=tuple(tuple(item) for item in raw["excluded_profile_suites"]),
        selected_files=tuple(raw["selected_files"]),
        full_profile_count=raw["full_profile_count"],
    )


@pytest.fixture(scope="session")
def real_golden_selections(shared_session_root: Path) -> Iterator[dict[str, Any]]:
    inputs = (harness.GOLDEN,)
    pre_fp = _fingerprint_paths(inputs)
    cached = _run_once_json(
        shared_session_root,
        "real-golden-selections",
        lambda: {
            "default": _selection_to_dict(harness.select_vectors(profile="default")),
            "core": _selection_to_dict(harness.select_vectors(profile="core")),
            "full": _selection_to_dict(harness.select_vectors(profile="full")),
            "all": harness.load_vectors(),
        },
        fingerprint=pre_fp,
    )
    yield {
        "default": _dict_to_selection(cached["default"]),
        "core": _dict_to_selection(cached["core"]),
        "full": _dict_to_selection(cached["full"]),
        "all": cached["all"],
        "fingerprint": pre_fp,
    }
    assert _fingerprint_paths(inputs) == pre_fp, "Checked-in tests/golden mutated during session"
