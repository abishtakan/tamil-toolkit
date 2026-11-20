"""Tests for concurrent, isolated, content-verified binding rebuilds in tools/tasks.py."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from tools import tasks


def _write_pack_manifest(directory: Path, pack_id: str, manifest_sha256: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "packs.toml").write_text(
        f'pack_id = "{pack_id}"\n'
        "schema_version = 1\n"
        "l3_pack_eligible = true\n"
        f'dataset_version = "0.1.0+{pack_id}"\n'
        f'manifest_sha256 = "{manifest_sha256}"\n',
        encoding="utf-8",
    )
    (directory / "entries.csv").write_text("entry_id\nent_1\n", encoding="utf-8")


def _make_fake_workspace(root: Path) -> None:
    (root / "Cargo.toml").write_text('[workspace]\nmembers = ["crates/*"]\n', encoding="utf-8")
    (root / "Cargo.lock").write_text('version = 3\n[[package]]\nname = "tamil-core"\n', encoding="utf-8")
    (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.95.0"\n', encoding="utf-8")
    (root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "tools/release.py").write_text("# release stub\n", encoding="utf-8")

    (root / "crates/tamil-core/src").mkdir(parents=True, exist_ok=True)
    (root / "crates/tamil-core/Cargo.toml").write_text('[package]\nname = "tamil-core"\n', encoding="utf-8")
    (root / "crates/tamil-core/src/lib.rs").write_text("pub fn ok() -> u8 { 1 }\n", encoding="utf-8")

    (root / "crates/tamil-toolkit/src").mkdir(parents=True, exist_ok=True)
    (root / "crates/tamil-toolkit/Cargo.toml").write_text('[package]\nname = "tamil-toolkit"\n', encoding="utf-8")
    (root / "crates/tamil-toolkit/src/lib.rs").write_text("pub fn dispatch() -> u8 { 1 }\n", encoding="utf-8")
    (root / "crates/tamil-toolkit/build.rs").write_text("fn main() {}\n", encoding="utf-8")

    _write_pack_manifest(root / "lexicon/dictionary", "core", "a" * 64)
    _write_pack_manifest(root / "lexicon/packs/names_taxa", "names_taxa", "b" * 64)
    _write_pack_manifest(root / "lexicon/packs/regional", "regional", "c" * 64)
    _write_pack_manifest(root / "crates/tamil-toolkit/lexicon/dictionary", "core", "a" * 64)
    _write_pack_manifest(root / "crates/tamil-toolkit/lexicon/packs/names_taxa", "names_taxa", "b" * 64)
    _write_pack_manifest(root / "crates/tamil-toolkit/lexicon/packs/regional", "regional", "c" * 64)

    (root / "tests/golden").mkdir(parents=True, exist_ok=True)
    (root / "tests/golden/manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "suites": [
                    {
                        "file": "lexicon_lookup.jsonl",
                        "status": "active",
                        "required_profile": "core",
                        "operations": ["lexicon_lookup"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    py_pkg = root / "bindings/python/python/tamil_toolkit"
    py_pkg.mkdir(parents=True, exist_ok=True)
    (py_pkg / "__init__.py").write_text("def version(): return '1'\n", encoding="utf-8")
    (root / "bindings/python/src").mkdir(parents=True, exist_ok=True)
    (root / "bindings/python/src/lib.rs").write_text("// pyo3\n", encoding="utf-8")
    (root / "bindings/python/Cargo.toml").write_text('[package]\nname = "tamil-python"\n', encoding="utf-8")
    (root / "bindings/python/pyproject.toml").write_text('[project]\nname = "tamil-toolkit"\n', encoding="utf-8")

    js_src = root / "bindings/js-wasm/src"
    js_src.mkdir(parents=True, exist_ok=True)
    (js_src / "lib.rs").write_text("// wasm\n", encoding="utf-8")
    (js_src / "api.ts").write_text("export const apiVersion = 1;\n", encoding="utf-8")
    (js_src / "index.ts").write_text("export * from './api.js';\n", encoding="utf-8")
    (js_src / "web.ts").write_text("export * from './api.js';\n", encoding="utf-8")
    (root / "bindings/js-wasm/Cargo.toml").write_text('[package]\nname = "tamil-wasm"\n', encoding="utf-8")
    (root / "bindings/js-wasm/package.json").write_text('{"name":"tamil-toolkit"}\n', encoding="utf-8")
    (root / "bindings/js-wasm/tsconfig.json").write_text('{"compilerOptions":{}}\n', encoding="utf-8")

    dart_rust = root / "bindings/dart-flutter/rust/src"
    dart_rust.mkdir(parents=True, exist_ok=True)
    (dart_rust / "lib.rs").write_text("// dart ffi\n", encoding="utf-8")
    (root / "bindings/dart-flutter/rust/Cargo.toml").write_text(
        '[package]\nname = "tamil-dart"\n', encoding="utf-8"
    )


def _python_ext_filename() -> str:
    return "_native.pyd" if sys.platform == "win32" else "_native.abi3.so"


def _feature_tag(args: tuple[str, ...]) -> str:
    if "--features" in args:
        idx = args.index("--features")
        return args[idx + 1]
    return "default"


class _FakeRunner:
    """Thread-safe fake `tasks.run` that records commands and emits deterministic artifacts."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.lock = threading.Lock()
        self.calls: list[dict] = []
        self.hook = None

    def __call__(self, *args, cwd=None, extra_env=None):
        entry = {
            "args": tuple(str(a) for a in args),
            "cwd": Path(cwd) if cwd is not None else self.root,
            "extra_env": dict(extra_env or {}),
        }
        with self.lock:
            self.calls.append(entry)
        if self.hook is not None:
            self.hook(entry)

        cmd = entry["args"]
        if len(cmd) >= 3 and cmd[1] == "tools/release.py" and cmd[2] == "licenses":
            text = (self.root / "Cargo.lock").read_text(encoding="utf-8")
            for rel in (
                "bindings/python/THIRD_PARTY_LICENSES.txt",
                "bindings/js-wasm/THIRD_PARTY_LICENSES.txt",
            ):
                out = self.root / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(f"licenses:{hashlib.sha256(text.encode()).hexdigest()}\n", encoding="utf-8")
            return

        if cmd[0] == "maturin":
            src = (self.root / "bindings/python/src/lib.rs").read_text(encoding="utf-8")
            core = (self.root / "crates/tamil-core/src/lib.rs").read_text(encoding="utf-8")
            ext = self.root / "bindings/python/python/tamil_toolkit" / _python_ext_filename()
            ext.write_bytes(f"pyd:{_feature_tag(cmd)}:{src}:{core}".encode("utf-8"))
            return

        if len(cmd) >= 5 and cmd[0] == "pnpm" and cmd[4] == "wasm-pack":
            out_idx = cmd.index("--out-dir")
            out_name = cmd[out_idx + 1]
            out_dir = self.root / "bindings/js-wasm" / out_name
            out_dir.mkdir(parents=True, exist_ok=True)
            rs = (self.root / "bindings/js-wasm/src/lib.rs").read_text(encoding="utf-8")
            core = (self.root / "crates/tamil-core/src/lib.rs").read_text(encoding="utf-8")
            feat = _feature_tag(cmd)
            (out_dir / "tamil_toolkit_bg.wasm").write_bytes(f"wasm:{out_name}:{feat}:{rs}:{core}".encode("utf-8"))
            (out_dir / "tamil_toolkit.js").write_text(f"// js:{out_name}:{feat}\n", encoding="utf-8")
            (out_dir / "tamil_toolkit.d.ts").write_text(f"// dts:{out_name}:{feat}\n", encoding="utf-8")
            (out_dir / "tamil_toolkit_bg.wasm.d.ts").write_text("// wasm dts\n", encoding="utf-8")
            (out_dir / "package.json").write_text('{"name":"tamil-toolkit-wasm"}\n', encoding="utf-8")
            return

        if cmd[:4] == ("pnpm", "--filter", "tamil-toolkit", "build"):
            dist = self.root / "bindings/js-wasm/dist"
            dist.mkdir(parents=True, exist_ok=True)
            api_ts = (self.root / "bindings/js-wasm/src/api.ts").read_text(encoding="utf-8")
            for name in ("index.js", "index.d.ts", "web.js", "web.d.ts", "api.js", "api.d.ts"):
                (dist / name).write_text(f"// {name}:{api_ts}\n", encoding="utf-8")
            return

        if cmd[:4] == ("cargo", "build", "--locked", "-p") and len(cmd) >= 5 and cmd[4] == "tamil-dart":
            cargo_target = Path(entry["extra_env"]["CARGO_TARGET_DIR"])
            debug_dir = cargo_target / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            dart_rs = (self.root / "bindings/dart-flutter/rust/src/lib.rs").read_text(encoding="utf-8")
            core = (self.root / "crates/tamil-core/src/lib.rs").read_text(encoding="utf-8")
            lib_name = tasks._dart_library_filename()
            (debug_dir / lib_name).write_bytes(f"dll:{_feature_tag(cmd)}:{dart_rs}:{core}".encode("utf-8"))
            return


def _setup_workspace(tmp_path: Path, monkeypatch) -> _FakeRunner:
    from types import SimpleNamespace

    _make_fake_workspace(tmp_path)
    # This runner writes byte-sized stand-ins, not real Cargo builds. Keep
    # unrelated cache tests independent of the host drive; the disk-budget
    # regression below overrides this value and exercises the real guard.
    monkeypatch.setattr(tasks.shutil, "disk_usage", lambda _path: SimpleNamespace(free=100 * 1024**3))
    monkeypatch.setattr(tasks, "ROOT", tmp_path)
    monkeypatch.delenv("TAMIL_LEXICON_PROFILE", raising=False)
    monkeypatch.delenv("TAMIL_FORCE_BINDING_REBUILD", raising=False)
    monkeypatch.delenv("CARGO_BUILD_JOBS", raising=False)
    monkeypatch.delenv("TAMIL_CARGO_BUILD_JOBS", raising=False)
    monkeypatch.delenv("TAMIL_BINDING_CONCURRENCY", raising=False)
    monkeypatch.delenv("TAMIL_BINDING_LEASE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TAMIL_CANONICAL_LEASE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TAMIL_HARNESS_WORKERS", raising=False)
    monkeypatch.setattr(tasks, "is_wasm_bindgen_bootstrapped", lambda _root: True)
    monkeypatch.setattr(
        tasks,
        "collect_toolchain_fingerprint",
        lambda _root: {
            "schema_version": tasks.BINDING_CACHE_SCHEMA_VERSION,
            "rustc": "rustc 1.95.0",
            "rustc_binary": "rustc-hash",
            "rustdoc": "rustdoc 1.95.0",
            "cargo": "cargo 1.95.0",
            "cargo_binary": "cargo-hash",
            "maturin_cli": "maturin 1.8.0",
            "maturin_dist": "1.8.0",
            "node": "v22.0.0",
            "pnpm": "10.0.0",
            "wasm_pack_npm": "0.15.1",
            "typescript_npm": "7.0.2",
            "python_version": [3, 12],
            "python_impl": "cpython",
            "python_ext_suffix": ".pyd" if sys.platform == "win32" else ".abi3.so",
            "python_prefix": "/venv",
            "platform": sys.platform,
            "machine": "AMD64",
            "env": {},
        },
    )
    runner = _FakeRunner(tmp_path)
    monkeypatch.setattr(tasks, "run", runner)
    return runner


def _build_labels(calls: list[dict]) -> list[str]:
    labels: list[str] = []
    for call in calls:
        cmd = call["args"]
        if len(cmd) >= 3 and cmd[1] == "tools/release.py" and cmd[2] == "licenses":
            labels.append("licenses")
        elif cmd[0] == "maturin":
            labels.append("python")
        elif len(cmd) >= 5 and cmd[0] == "pnpm" and cmd[4] == "wasm-pack":
            labels.append("wasm-node" if "pkg-node" in cmd else "wasm-web")
        elif cmd[:4] == ("pnpm", "--filter", "tamil-toolkit", "build"):
            labels.append("js-tsc")
        elif len(cmd) >= 5 and cmd[:4] == ("cargo", "build", "--locked", "-p") and cmd[4] == "tamil-dart":
            labels.append("dart")
    return labels


def test_cold_build_and_unchanged_cache_reuse(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)

    tasks.sync_bindings(include_dart=True)
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "dart", "js-tsc"}
    assert (tmp_path / "target/debug" / tasks._dart_library_filename()).is_file()

    runner.calls.clear()
    tasks.sync_bindings(include_dart=True)
    assert runner.calls == []


def test_changed_shared_rust_and_lexicon_inputs_invalidate_compiled_targets(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(include_dart=True)

    # Editing shared Rust crate invalidates all Rust-compiled targets (not licenses).
    runner.calls.clear()
    (tmp_path / "crates/tamil-core/src/lib.rs").write_text("pub fn ok() -> u8 { 2 }\n", encoding="utf-8")
    tasks.sync_bindings(include_dart=True)
    assert set(_build_labels(runner.calls)) == {"python", "wasm-node", "wasm-web", "dart"}

    # Editing embedded pack CSV data also invalidates all compiled targets.
    runner.calls.clear()
    (tmp_path / "crates/tamil-toolkit/lexicon/dictionary/entries.csv").write_text(
        "entry_id\nent_1\nent_2\n", encoding="utf-8"
    )
    tasks.sync_bindings(include_dart=True)
    assert set(_build_labels(runner.calls)) == {"python", "wasm-node", "wasm-web", "dart"}


def test_changed_target_specific_source_rebuilds_only_affected_target(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(include_dart=True)

    runner.calls.clear()
    (tmp_path / "bindings/python/src/lib.rs").write_text("// pyo3 v2\n", encoding="utf-8")
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["python"]

    runner.calls.clear()
    (tmp_path / "bindings/js-wasm/src/api.ts").write_text("export const apiVersion = 2;\n", encoding="utf-8")
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["js-tsc"]

    runner.calls.clear()
    (tmp_path / "bindings/dart-flutter/rust/src/lib.rs").write_text("// dart v2\n", encoding="utf-8")
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["dart"]


def test_cache_never_relies_on_mtime_only(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(include_dart=True)
    core_rs = tmp_path / "crates/tamil-core/src/lib.rs"
    orig_stat = core_rs.stat()

    # Touching mtime without changing content keeps cache valid.
    runner.calls.clear()
    os.utime(core_rs, (orig_stat.st_atime + 100, orig_stat.st_mtime + 100))
    tasks.sync_bindings(include_dart=True)
    assert runner.calls == []

    # Same-byte-length edit WITH original mtime restored still invalidates cache.
    runner.calls.clear()
    core_rs.write_text("pub fn ok() -> u8 { 9 }\n", encoding="utf-8")
    os.utime(core_rs, (orig_stat.st_atime, orig_stat.st_mtime))
    tasks.sync_bindings(include_dart=True)
    assert set(_build_labels(runner.calls)) == {"python", "wasm-node", "wasm-web", "dart"}


def test_missing_corrupted_or_stale_outputs_invalidate_only_broken_target(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(include_dart=True)

    # Missing pkg-web wasm -> rebuilds only wasm-web.
    runner.calls.clear()
    (tmp_path / "bindings/js-wasm/pkg-web/tamil_toolkit_bg.wasm").unlink()
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["wasm-web"]

    # Corrupted Python extension -> rebuilds only python.
    runner.calls.clear()
    py_ext = tmp_path / "bindings/python/python/tamil_toolkit" / _python_ext_filename()
    py_ext.write_bytes(b"corrupted-bytes")
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["python"]

    # Truncated (0-byte) Dart DLL -> rebuilds only dart.
    runner.calls.clear()
    dart_dll = tmp_path / "target/debug" / tasks._dart_library_filename()
    dart_dll.write_bytes(b"")
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["dart"]

    # Corrupted stamp JSON -> rebuilds only that target.
    runner.calls.clear()
    tasks.binding_stamp_path(tmp_path, "wasm-node").write_text("{bad json", encoding="utf-8")
    tasks.sync_bindings(include_dart=True)
    assert _build_labels(runner.calls) == ["wasm-node"]

    # Stale interpreter-tagged extension alongside valid abi3 extension -> cleaned & rebuilt.
    runner.calls.clear()
    stale_pyd = tmp_path / "bindings/python/python/tamil_toolkit/_native.cp314-win_amd64.pyd"
    stale_pyd.write_bytes(b"stale")
    tasks.sync_bindings(include_dart=True)
    assert not stale_pyd.exists()
    assert _build_labels(runner.calls) == ["python"]


def test_profile_switch_and_wrong_profile_artifact_invalidate_cache(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)

    tasks.sync_bindings(profile="core", include_dart=True)
    core_dart_bytes = (tmp_path / "target/debug" / tasks._dart_library_filename()).read_bytes()

    # Switching to default must rebuild with no --features and separate CARGO_TARGET_DIR.
    runner.calls.clear()
    tasks.sync_bindings(profile="default", include_dart=True)
    assert set(_build_labels(runner.calls)) == {"python", "wasm-node", "wasm-web", "dart", "js-tsc"}
    for call in runner.calls:
        if "CARGO_TARGET_DIR" in call["extra_env"]:
            assert f"{os.sep}default{os.sep}" in call["extra_env"]["CARGO_TARGET_DIR"]
        if call["args"][0] in ("maturin", "cargo"):
            assert "--features" not in call["args"]
    default_dart_bytes = (tmp_path / "target/debug" / tasks._dart_library_filename()).read_bytes()
    assert default_dart_bytes != core_dart_bytes

    # Switching back to core must rebuild rather than accepting default outputs.
    runner.calls.clear()
    tasks.sync_bindings(profile="core", include_dart=True)
    assert set(_build_labels(runner.calls)) == {"python", "wasm-node", "wasm-web", "dart", "js-tsc"}
    assert (tmp_path / "target/debug" / tasks._dart_library_filename()).read_bytes() == core_dart_bytes

    # Swapping canonical DLL with wrong-profile bytes invalidates cache on same profile.
    runner.calls.clear()
    (tmp_path / "target/debug" / tasks._dart_library_filename()).write_bytes(default_dart_bytes)
    tasks.sync_bindings(profile="core", targets=("dart",))
    assert _build_labels(runner.calls) == ["dart"]
    assert (tmp_path / "target/debug" / tasks._dart_library_filename()).read_bytes() == core_dart_bytes


def test_force_rebuild_paths_bypass_verified_cache(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(profile="core", include_dart=True)

    runner.calls.clear()
    tasks.sync_bindings(profile="core", include_dart=True, force=True)
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "dart", "js-tsc"}

    runner.calls.clear()
    monkeypatch.setenv("TAMIL_FORCE_BINDING_REBUILD", "1")
    tasks.sync_bindings(profile="core", include_dart=True)
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "dart", "js-tsc"}


def test_bounded_budget_isolated_target_dirs_and_concurrent_execution(tmp_path: Path, monkeypatch) -> None:
    # Verify CPU and RAM budget math for 12 logical CPUs / 16 GiB Windows host.
    assert tasks.compute_build_budget(1, cpu_count=12, ram_gib=16.0, env={}) == (1, 8)
    assert tasks.compute_build_budget(2, cpu_count=12, ram_gib=16.0, env={}) == (2, 4)
    assert tasks.compute_build_budget(3, cpu_count=12, ram_gib=16.0, env={}) == (3, 3)
    assert tasks.compute_build_budget(4, cpu_count=12, ram_gib=16.0, env={}) == (3, 3)
    assert tasks.compute_build_budget(4, cpu_count=12, ram_gib=8.0, env={}) == (2, 2)

    runner = _setup_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(tasks, "compute_build_budget", lambda pending, **_: (min(pending, 3), 3))
    barrier = threading.Barrier(3, timeout=5.0)
    tsc_saw_active = {"count": 0}
    active = {"count": 0}
    active_lock = threading.Lock()

    def hook(entry: dict) -> None:
        cmd = entry["args"]
        is_concurrent = (
            cmd[0] == "maturin"
            or (len(cmd) >= 5 and cmd[0] == "pnpm" and cmd[4] == "wasm-pack")
        )
        if is_concurrent:
            with active_lock:
                active["count"] += 1
            try:
                barrier.wait()
            finally:
                with active_lock:
                    active["count"] -= 1
        elif cmd[:4] == ("pnpm", "--filter", "tamil-toolkit", "build"):
            with active_lock:
                tsc_saw_active["count"] = active["count"]

    runner.hook = hook
    tasks.sync_bindings(profile="core")

    assert tsc_saw_active["count"] == 0
    target_dirs = {
        call["extra_env"]["CARGO_TARGET_DIR"]
        for call in runner.calls
        if "CARGO_TARGET_DIR" in call["extra_env"]
    }
    assert len(target_dirs) == 3
    for call in runner.calls:
        if "CARGO_BUILD_JOBS" in call["extra_env"]:
            assert call["extra_env"]["CARGO_BUILD_JOBS"] == "3"


def test_dart_stages_canonical_dll_before_consumer_and_reuses_cache(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    canonical_dll = tmp_path / "target/debug" / tasks._dart_library_filename()
    saw_dll_before_dart_test = {"present": False}

    def hook(entry: dict) -> None:
        if entry["args"][:2] == ("dart", "test"):
            saw_dll_before_dart_test["present"] = canonical_dll.is_file() and canonical_dll.stat().st_size > 0

    runner.hook = hook
    tasks.test_dart(profile="core")
    assert saw_dll_before_dart_test["present"] is True
    assert _build_labels(runner.calls) == ["dart"]
    dart_cmds = [c["args"][:2] for c in runner.calls if c["args"][0] == "dart"]
    assert dart_cmds == [("dart", "pub"), ("dart", "analyze"), ("dart", "test")]

    # Second run reuses cached DLL without cargo build, yet still runs pub get/analyze/test.
    runner.calls.clear()
    tasks.test_dart(profile="core")
    assert _build_labels(runner.calls) == []
    dart_cmds = [c["args"][:2] for c in runner.calls if c["args"][0] == "dart"]
    assert dart_cmds == [("dart", "pub"), ("dart", "analyze"), ("dart", "test")]


def test_concurrency_failure_invalidates_stamp_and_skips_js_tsc(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(profile="core")
    assert tasks.binding_stamp_path(tmp_path, "wasm-node").is_file()

    # Force source + TS API changes so compiled targets and js-tsc must rebuild, and fail wasm-node.
    runner.calls.clear()
    (tmp_path / "crates/tamil-core/src/lib.rs").write_text("pub fn ok() -> u8 { 7 }\n", encoding="utf-8")
    (tmp_path / "bindings/js-wasm/src/api.ts").write_text("export const apiVersion = 2;\n", encoding="utf-8")

    def fail_wasm_node(entry: dict) -> None:
        cmd = entry["args"]
        if len(cmd) >= 5 and cmd[0] == "pnpm" and cmd[4] == "wasm-pack" and "pkg-node" in cmd:
            raise subprocess.CalledProcessError(1, cmd)

    runner.hook = fail_wasm_node
    with pytest.raises(subprocess.CalledProcessError):
        tasks.sync_bindings(profile="core")

    assert "js-tsc" not in _build_labels(runner.calls)
    assert not tasks.binding_stamp_path(tmp_path, "wasm-node").exists()

    # Recover: next sync_bindings rebuilds failed wasm-node and js-tsc, reusing clean targets.
    runner.hook = None
    runner.calls.clear()
    tasks.sync_bindings(profile="core")
    assert set(_build_labels(runner.calls)) == {"wasm-node", "js-tsc"}
    assert tasks.binding_stamp_path(tmp_path, "wasm-node").is_file()


def test_parity_and_pre_stop_never_skip_checks_when_bindings_reused(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(tasks.shutil, "which", lambda name: name)
    tasks.sync_bindings(profile="core")

    runner.calls.clear()
    tasks.test_parity(profile="core")
    assert _build_labels(runner.calls) == []
    cmds = [call["args"] for call in runner.calls]
    assert any("tools/release_policy.py" in args for args in cmds)
    assert any("golden_suite" in args for args in cmds)
    assert any("bindings/python/tests/test_golden.py" in args for args in cmds)
    assert any(args[:4] == ("pnpm", "--filter", "tamil-toolkit", "test") for args in cmds)

    runner.calls.clear()
    tasks.pre_stop(profile="core")
    assert _build_labels(runner.calls) == []
    cmds = [call["args"] for call in runner.calls]
    assert any(args[:2] == ("cargo", "fmt") for args in cmds)
    assert any(args[:2] == ("cargo", "check") for args in cmds)
    assert any(args[:2] == ("cargo", "clippy") for args in cmds)
    assert any(args[:2] == ("cargo", "nextest") for args in cmds)
    assert any(args[1:] == ("-m", "pytest", "tests/harness", "-n", "auto", "--dist=loadgroup", "-q") for args in cmds)
    assert any("golden_suite" in args for args in cmds)
    assert any("bindings/python/tests/test_golden.py" in args for args in cmds)
    assert any(args[:4] == ("pnpm", "--filter", "tamil-toolkit", "test") for args in cmds)


def test_release_test_forces_rebuild_and_keeps_isolated_release_all(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(tasks.shutil, "which", lambda name: name)
    tasks.sync_bindings(profile="core", include_dart=True)

    runner.calls.clear()
    tasks.release_test(profile="core")
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "dart", "js-tsc"}
    assert any(
        call["args"][1:4] == ("tools/release.py", "all", "--lexicon-profile")
        and call["args"][4] == "core"
        for call in runner.calls
    )


def test_implicit_profile_remains_core_and_rejects_unknown_targets(tmp_path: Path, monkeypatch) -> None:
    _setup_workspace(tmp_path, monkeypatch)
    assert tasks.resolve_lexicon_profile().name == "core"
    with pytest.raises(ValueError, match="Unsupported binding targets"):
        tasks.sync_bindings(targets=("unknown",))


def test_is_wasm_bindgen_bootstrapped_checks_lockfile_version(tmp_path: Path, monkeypatch) -> None:
    _make_fake_workspace(tmp_path)
    (tmp_path / "Cargo.lock").write_text(
        'version = 3\n[[package]]\nname = "wasm-bindgen"\nversion = "0.2.100"\n',
        encoding="utf-8",
    )
    cache_home = tmp_path / "cache-home"
    monkeypatch.setenv("LOCALAPPDATA", str(cache_home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    monkeypatch.setattr(tasks, "_resolve_executable", lambda _name: None)

    assert tasks.is_wasm_bindgen_bootstrapped(tmp_path) is False

    exe_name = "wasm-bindgen.exe" if sys.platform == "win32" else "wasm-bindgen"
    cached_bin = cache_home / ".wasm-pack/wasm-bindgen-deadbeef" / exe_name
    cached_bin.parent.mkdir(parents=True, exist_ok=True)
    cached_bin.write_bytes(b"binary")

    monkeypatch.setattr(tasks, "_probe_command_output", lambda _cmd, cwd=None: "wasm-bindgen 0.2.99")
    assert tasks.is_wasm_bindgen_bootstrapped(tmp_path) is False

    monkeypatch.setattr(tasks, "_probe_command_output", lambda _cmd, cwd=None: "wasm-bindgen 0.2.100")
    assert tasks.is_wasm_bindgen_bootstrapped(tmp_path) is True


def test_cold_wasm_bootstrap_serializes_wasm_while_python_runs_parallel(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(tasks, "is_wasm_bindgen_bootstrapped", lambda _root: False)
    monkeypatch.setattr(tasks, "compute_build_budget", lambda pending_count: (min(3, pending_count), 3))

    py_and_first_wasm = threading.Barrier(2, timeout=5.0)
    state_lock = threading.Lock()
    active_wasm = {"count": 0, "max": 0}
    wasm_entered = {"count": 0}

    def hook(entry: dict) -> None:
        cmd = entry["args"]
        if cmd[0] == "maturin":
            py_and_first_wasm.wait()
        elif len(cmd) >= 5 and cmd[0] == "pnpm" and cmd[4] == "wasm-pack":
            with state_lock:
                wasm_entered["count"] += 1
                is_first_wasm = wasm_entered["count"] == 1
                active_wasm["count"] += 1
                active_wasm["max"] = max(active_wasm["max"], active_wasm["count"])
            try:
                if is_first_wasm:
                    py_and_first_wasm.wait()
            finally:
                with state_lock:
                    active_wasm["count"] -= 1

    runner.hook = hook
    tasks.sync_bindings(profile="core")
    assert active_wasm["max"] == 1
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "js-tsc"}


def test_canonical_lease_reentrant_fail_loud_and_cross_process_contention(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    lock_path, state_path = tasks.canonical_lease_paths(tmp_path)

    with pytest.raises(RuntimeError, match="No active canonical binding output lease held"):
        tasks.verify_canonical_lease(tmp_path, expected_profile="core")

    with tasks.canonical_output_lease(tmp_path, profile="core", targets=("parity",)):
        assert state_path.is_file()
        holder = tasks.verify_canonical_lease(tmp_path, expected_profile="core")
        assert holder["pid"] == os.getpid()

        with pytest.raises(RuntimeError, match="does not match"):
            tasks.verify_canonical_lease(tmp_path, expected_profile="full")

        with tasks.canonical_output_lease(tmp_path, profile="core", targets=("python",)):
            assert state_path.is_file()
            tasks.verify_canonical_lease(tmp_path, expected_profile="core")

        assert state_path.is_file()
        state_path.write_text("{corrupt", encoding="utf-8")
        with pytest.raises(RuntimeError, match="Malformed canonical binding lease"):
            tasks.verify_canonical_lease(tmp_path, expected_profile="core")

    assert not state_path.exists()

    # Cross-process contention: hold canonical lock from another process and assert fail-loud timeout.
    repo_root = str(Path(tasks.__file__).resolve().parents[1])
    ready_file = tmp_path / "holder.ready"
    holder_script = (
        "import json, os, pathlib, sys, time; "
        f"sys.path.insert(0, {repo_root!r}); "
        "from tools import tasks; "
        f"lock_path = pathlib.Path({str(lock_path)!r}); "
        f"state_path = pathlib.Path({str(state_path)!r}); "
        f"ready = pathlib.Path({str(ready_file)!r}); "
        "lock = tasks._CrossProcessFileLock(lock_path, timeout_seconds=5.0); "
        "lock.acquire(); "
        "state_path.parent.mkdir(parents=True, exist_ok=True); "
        "state_path.write_text("
        "json.dumps({'schema_version': tasks.BINDING_CACHE_SCHEMA_VERSION, 'pid': os.getpid(), 'nonce': 'ext', 'profile': 'regional'}), "
        "encoding='utf-8'); "
        "ready.write_text(str(os.getpid()), encoding='utf-8'); "
        "time.sleep(10)"
    )
    proc = subprocess.Popen([sys.executable, "-c", holder_script])
    try:
        deadline = threading.Event()
        while not ready_file.is_file() and proc.poll() is None:
            deadline.wait(0.02)
        assert ready_file.is_file()
        holder_pid = ready_file.read_text(encoding="utf-8").strip()

        monkeypatch.setenv("TAMIL_CANONICAL_LEASE_TIMEOUT_SECONDS", "0.25")
        with pytest.raises(RuntimeError, match=f"pid={holder_pid}.*profile='regional'"):
            tasks.sync_bindings(profile="core")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        state_path.unlink(missing_ok=True)

    monkeypatch.setenv("TAMIL_CANONICAL_LEASE_TIMEOUT_SECONDS", "5")
    runner.calls.clear()
    tasks.sync_bindings(profile="core")
    assert "python" in _build_labels(runner.calls)


def test_partial_wasm_target_defers_js_tsc_until_both_pkg_dirs_exist(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)

    # Seed valid fake TS outputs + a stale js-tsc stamp so partial wasm sync proves it invalidates stale metadata.
    dist_dir = tmp_path / "bindings/js-wasm/dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    for name in tasks._REQUIRED_TSC_OUTPUTS:
        (dist_dir / name).write_text(f"// stale {name}\n", encoding="utf-8")
    tasks._write_binding_stamp(tmp_path, "js-tsc", profile="core", input_hash="stale")
    assert tasks.binding_stamp_path(tmp_path, "js-tsc").is_file()

    tasks.sync_bindings(profile="core", targets=("wasm-node",))
    assert _build_labels(runner.calls) == ["licenses", "wasm-node"]
    assert not tasks.binding_stamp_path(tmp_path, "js-tsc").exists()

    runner.calls.clear()
    tasks.sync_bindings(profile="core", targets=("wasm-web",))
    assert _build_labels(runner.calls) == ["wasm-web", "js-tsc"]
    assert (tmp_path / "bindings/js-wasm/dist/index.d.ts").is_file()
    assert tasks.binding_stamp_path(tmp_path, "js-tsc").is_file()


def test_rust_change_with_identical_js_glue_reuses_js_tsc_cache(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(profile="core")
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "js-tsc"}

    runner.calls.clear()
    (tmp_path / "crates/tamil-core/src/lib.rs").write_text("pub fn ok() -> u8 { 9 }\n", encoding="utf-8")
    tasks.sync_bindings(profile="core")
    # Compiled targets rebuild, while js-tsc reuses its content-addressed cache when pkg-*.js/.d.ts bytes stay identical.
    assert set(_build_labels(runner.calls)) == {"python", "wasm-node", "wasm-web"}


def test_test_rust_runs_workspace_and_doctests_once_without_redundant_package_pass(
    tmp_path: Path, monkeypatch
) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(tasks.Path, "home", classmethod(lambda cls: empty_home))

    # Nextest path: single workspace nextest pass + workspace doctest pass, no redundant -p tamil-toolkit rerun.
    monkeypatch.setattr(tasks.shutil, "which", lambda name: name if name == "cargo-nextest" else None)
    tasks.test_rust(profile="core")
    assert [call["args"] for call in runner.calls] == [
        ("cargo", "nextest", "run", "--locked", "--workspace", "--features", "lexicon-core"),
        ("cargo", "test", "--locked", "--workspace", "--exclude", "tamil-python", "--doc", "--features", "lexicon-core"),
    ]
    assert all(call["extra_env"]["TAMIL_LEXICON_PROFILE"] == "core" for call in runner.calls)

    # Cargo fallback path: single workspace test pass (includes unit, integration, doctests, proptests).
    runner.calls.clear()
    monkeypatch.setattr(tasks.shutil, "which", lambda _name: None)
    tasks.test_rust(profile="core")
    assert [call["args"] for call in runner.calls] == [
        ("cargo", "test", "--locked", "--workspace", "--features", "lexicon-core"),
    ]
    assert runner.calls[0]["extra_env"]["TAMIL_LEXICON_PROFILE"] == "core"

    # Default empty-feature profile preserves both nextest + doctest commands cleanly.
    runner.calls.clear()
    monkeypatch.setattr(tasks.shutil, "which", lambda name: name if name == "cargo-nextest" else None)
    tasks.test_rust(profile="default")
    assert [call["args"] for call in runner.calls] == [
        ("cargo", "nextest", "run", "--locked", "--workspace"),
        ("cargo", "test", "--locked", "--workspace", "--exclude", "tamil-python", "--doc"),
    ]


def test_generated_metadata_and_wasm_cache_do_not_self_invalidate(tmp_path: Path, monkeypatch) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    tasks.sync_bindings(profile="core")

    # Simulate build-time metadata/sidecar outputs that must not invalidate Python fingerprints.
    egg_info = tmp_path / "bindings/python/tamil_toolkit.egg-info"
    egg_info.mkdir(parents=True, exist_ok=True)
    (egg_info / "PKG-INFO").write_text("Name: tamil-toolkit\n", encoding="utf-8")
    (tmp_path / "bindings/python/python/tamil_toolkit/_native.pdb").write_bytes(b"pdb")
    (tmp_path / "bindings/python/python/tamil_toolkit/_native.lib").write_bytes(b"lib")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "wasm-cache-after-build"))

    runner.calls.clear()
    tasks.sync_bindings(profile="core")
    assert _build_labels(runner.calls) == []


def test_harness_and_pre_stop_use_xdist_loadgroup_and_support_worker_overrides(
    tmp_path: Path, monkeypatch
) -> None:
    runner = _setup_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(tasks.shutil, "which", lambda name: name)
    tasks.sync_bindings(profile="core")

    runner.calls.clear()
    tasks.test_harness()
    assert runner.calls[0]["args"][1:] == ("-m", "pytest", "tests/harness", "-n", "auto", "--dist=loadgroup", "-q")

    runner.calls.clear()
    monkeypatch.setenv("TAMIL_HARNESS_WORKERS", "4")
    tasks.pre_stop(profile="core")
    cmds = [call["args"][1:] for call in runner.calls]
    assert ("-m", "pytest", "tests/harness", "-n", "4", "--dist=loadgroup", "-q") in cmds

    runner.calls.clear()
    tasks.test_harness(workers=0)
    assert runner.calls[0]["args"][1:] == ("-m", "pytest", "tests/harness", "-q")

    with pytest.raises(ValueError, match="Harness workers must be"):
        tasks.test_harness(workers="-1")


def test_binding_disk_budget_accounts_for_cold_vs_warm_targets_and_fails_clearly(
    tmp_path: Path, monkeypatch
) -> None:
    from collections import namedtuple

    runner = _setup_workspace(tmp_path, monkeypatch)
    usage_cls = namedtuple("usage", ["total", "used", "free"])
    gib = 1024 ** 3

    # 3 cold targets = python (2.0) + wasm-node (1.5) + wasm-web (1.5) + headroom (2.0) = 7.0 GiB required.
    monkeypatch.setattr(tasks.shutil, "disk_usage", lambda _path: usage_cls(100 * gib, 94 * gib, int(6.0 * gib)))
    with pytest.raises(RuntimeError, match=r"Insufficient free disk space.*6\.00 GiB free < 7\.00 GiB required"):
        tasks.sync_bindings(profile="core")
    assert _build_labels(runner.calls) == []

    # Populating target subdirs reduces estimate to incremental delta: 3 * 0.25 + 2.0 = 2.75 GiB required.
    for target, subdir in (("python", "debug"), ("wasm-node", "wasm32-unknown-unknown"), ("wasm-web", "wasm32-unknown-unknown")):
        (tasks.binding_cargo_target_dir(tmp_path, "core", target) / subdir).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tasks.shutil, "disk_usage", lambda _path: usage_cls(100 * gib, 97 * gib, int(2.5 * gib)))
    with pytest.raises(RuntimeError, match=r"2\.50 GiB free < 2\.75 GiB required"):
        tasks.sync_bindings(profile="core")

    monkeypatch.setattr(tasks.shutil, "disk_usage", lambda _path: usage_cls(100 * gib, 94 * gib, int(6.0 * gib)))
    tasks.sync_bindings(profile="core")
    assert set(_build_labels(runner.calls)) == {"licenses", "python", "wasm-node", "wasm-web", "js-tsc"}


