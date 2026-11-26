"""Cross-platform task implementations. Use just recipes from the repo root."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import threading
import time
import tomllib
import uuid
from pathlib import Path
from typing import Iterable, Mapping

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

ROOT = Path(__file__).resolve().parents[1]
KNOWN_LEXICON_FEATURES = (
    "lexicon-core",
    "lexicon-terminology",
    "lexicon-names-taxa",
    "lexicon-regional",
)

BINDING_CACHE_DIR_REL = Path("target/bindings-cache")
BINDING_CACHE_SCHEMA_VERSION = 1
ALL_BINDING_TARGETS = ("python", "wasm-node", "wasm-web", "dart")
DEFAULT_BINDING_TARGETS = ("python", "wasm-node", "wasm-web")
_BUILD_ENV_KEYS = (
    "RUSTC",
    "RUSTDOC",
    "RUSTFLAGS",
    "CARGO_ENCODED_RUSTFLAGS",
    "RUSTC_WRAPPER",
    "CARGO_BUILD_TARGET",
    "PYO3_PYTHON",
)
_EXCLUDED_CRATE_DIRS = frozenset({"target", "tests", "benches", "examples", "__pycache__", ".git"})
_EXCLUDED_PYTHON_DIRS = frozenset(
    {".venv", "__pycache__", "tests", ".pytest_cache", "target", "build", "dist", ".mypy_cache", ".ruff_cache", ".git"}
)
_REQUIRED_WASM_OUTPUTS = (
    "tamil_toolkit_bg.wasm",
    "tamil_toolkit.js",
    "tamil_toolkit.d.ts",
    "tamil_toolkit_bg.wasm.d.ts",
    "package.json",
)
_REQUIRED_TSC_OUTPUTS = (
    "index.js",
    "index.d.ts",
    "web.js",
    "web.d.ts",
    "api.js",
    "api.d.ts",
)
_DEFAULT_CANONICAL_LEASE_TIMEOUT_SECONDS = 120.0
_GIB = 1024 ** 3
_COLD_TARGET_DISK_GIB = {
    "python": 2.0,
    "wasm-node": 1.5,
    "wasm-web": 1.5,
    "dart": 2.0,
}
_WARM_TARGET_DISK_GIB = 0.25
_DISK_SAFETY_HEADROOM_GIB = 2.0

_PRINT_LOCK = threading.Lock()
_CANONICAL_LEASE_MUTEX = threading.Lock()


@dataclass
class _CanonicalLeaseState:
    root: Path | None = None
    depth: int = 0
    profile: str | None = None
    nonce: str | None = None
    lock_handle: "_CrossProcessFileLock | None" = None


_CANONICAL_LEASE_STATE = _CanonicalLeaseState()


@dataclass(frozen=True)
class LexiconProfile:
    name: str
    features: tuple[str, ...]
    expected_packs: tuple[str, ...]
    planned_suites: tuple[str, ...]
    dataset_version: str | None
    manifest_sha256: str | None
    pack_manifests: tuple[tuple[str, str, str], ...] = ()

    def pack_manifests_map(self) -> dict[str, dict[str, str]]:
        """Return `{pack_id: {dataset_version, manifest_sha256}}` for all embedded packs."""
        return {
            pack_id: {"dataset_version": dataset_version, "manifest_sha256": manifest_sha256}
            for pack_id, dataset_version, manifest_sha256 in self.pack_manifests
        }


_PACK_MANIFEST_PATHS = {
    "core": "lexicon/dictionary/packs.toml",
    "names_taxa": "lexicon/packs/names_taxa/packs.toml",
    "regional": "lexicon/packs/regional/packs.toml",
}


def load_pack_manifest(pack_id: str = "core", root: Path | None = None) -> dict:
    if pack_id not in _PACK_MANIFEST_PATHS:
        raise ValueError(f"Unsupported or unapproved lexicon profile: {pack_id!r}")
    manifest_path = (root or ROOT) / _PACK_MANIFEST_PATHS[pack_id]
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("pack_id") != pack_id or manifest.get("schema_version") != 1:
        raise ValueError(f"Invalid pack manifest metadata in {manifest_path}")
    if manifest.get("l3_pack_eligible") is not True:
        raise ValueError(f"Pack {pack_id!r} in {manifest_path} is not L3-eligible")
    dataset_version = manifest.get("dataset_version")
    manifest_sha256 = manifest.get("manifest_sha256")
    if not isinstance(dataset_version, str) or not dataset_version:
        raise ValueError(f"Missing dataset_version in {manifest_path}")
    if not isinstance(manifest_sha256, str) or len(manifest_sha256) != 64:
        raise ValueError(f"Missing or invalid manifest_sha256 in {manifest_path}")
    return manifest


def resolve_lexicon_profile(profile: str | None = None, *, root: Path | None = None) -> LexiconProfile:
    manifest_path = (root or ROOT) / "tests/golden/manifest.json"
    suites = json.loads(manifest_path.read_text(encoding="utf-8"))["suites"] if manifest_path.is_file() else []
    core_active = any(s["file"] == "lexicon_lookup.jsonl" and s["status"] == "active" for s in suites)
    full_planned_suites = tuple(
        s["file"] for s in suites if s.get("required_profile") == "full" and s.get("status") == "planned"
    )
    # Verification/release consumers must execute every active vector with its
    # declared data profile; Cargo's own default features remain empty.
    raw = os.environ.get("TAMIL_LEXICON_PROFILE", "core" if core_active else "default") if profile is None else profile
    normalized = raw.strip().lower()
    if normalized in ("", "default", "none"):
        return LexiconProfile(
            name="default",
            features=(),
            expected_packs=(),
            planned_suites=(),
            dataset_version=None,
            manifest_sha256=None,
            pack_manifests=(),
        )
    if normalized in ("core", "lexicon-core"):
        manifest = load_pack_manifest("core", root=root)
        return LexiconProfile(
            name="core",
            features=("lexicon-core",),
            expected_packs=("core",),
            planned_suites=() if core_active else ("lexicon_lookup.jsonl",),
            dataset_version=manifest["dataset_version"],
            manifest_sha256=manifest["manifest_sha256"],
            pack_manifests=(("core", manifest["dataset_version"], manifest["manifest_sha256"]),),
        )
    if normalized in ("full", "lexicon-full"):
        manifests = {pack_id: load_pack_manifest(pack_id, root=root) for pack_id in ("core", "names_taxa", "regional")}
        return LexiconProfile(
            name="full",
            features=("lexicon-core", "lexicon-names-taxa", "lexicon-regional"),
            expected_packs=("core", "names_taxa", "regional"),
            planned_suites=full_planned_suites,
            dataset_version=manifests["core"]["dataset_version"],
            manifest_sha256=manifests["core"]["manifest_sha256"],
            pack_manifests=tuple(
                (pack_id, manifests[pack_id]["dataset_version"], manifests[pack_id]["manifest_sha256"])
                for pack_id in ("core", "names_taxa", "regional")
            ),
        )
    raise ValueError(
        f"Unsupported or unapproved lexicon profile: {raw!r} (expected 'default', 'core', or 'full')"
    )


def profile_env(
    spec: LexiconProfile,
    *,
    include_planned: bool = False,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    source_env = os.environ if base_env is None else base_env
    existing_planned = [
        item.strip()
        for item in source_env.get("TAMIL_GOLDEN_INCLUDE_PLANNED", "").split(",")
        if item.strip()
    ]
    manifest_path = ROOT / "tests/golden/manifest.json"
    suite_profiles = {}
    if manifest_path.is_file():
        for suite in json.loads(manifest_path.read_text(encoding="utf-8")).get("suites", []):
            if suite.get("required_profile"):
                suite_profiles[suite["file"]] = suite["required_profile"]
    for planned_file in existing_planned:
        req_profile = suite_profiles.get(planned_file)
        if req_profile is not None and req_profile != spec.name:
            raise ValueError(
                f"Cannot run {planned_file} (requires profile {req_profile!r}) under {spec.name} profile"
            )
    if spec.name != "core" and "lexicon_lookup.jsonl" in existing_planned:
        raise ValueError(
            f"Cannot run core-only lexicon_lookup.jsonl under {spec.name} profile; pass --lexicon-profile core"
        )
    overrides = {
        "TAMIL_LEXICON_PROFILE": spec.name,
        "TAMIL_LEXICON_FEATURES": ",".join(spec.features),
        "TAMIL_LEXICON_EXPECTED_PACKS": ",".join(spec.expected_packs),
    }
    if spec.manifest_sha256 is not None:
        overrides["TAMIL_LEXICON_MANIFEST_SHA256"] = spec.manifest_sha256
    if spec.dataset_version is not None:
        overrides["TAMIL_LEXICON_DATASET_VERSION"] = spec.dataset_version
    if spec.pack_manifests:
        overrides["TAMIL_LEXICON_PACK_MANIFESTS"] = json.dumps(spec.pack_manifests_map(), sort_keys=True)
    if include_planned and spec.planned_suites:
        merged = list(dict.fromkeys([*existing_planned, *spec.planned_suites]))
        overrides["TAMIL_GOLDEN_INCLUDE_PLANNED"] = ",".join(merged)
    return overrides


def cargo_feature_args(spec: LexiconProfile) -> list[str]:
    return ["--features", ",".join(spec.features)] if spec.features else []


def maturin_feature_args(spec: LexiconProfile) -> list[str]:
    if not spec.features:
        return []
    return ["--features", ",".join(("extension-module", *spec.features))]


def wasm_pack_build_command(
    spec: LexiconProfile,
    target: str,
    directory: str,
    *,
    release: bool = False,
) -> list[str]:
    mode = "--release" if release else "--dev"
    return [
        "pnpm",
        "--filter",
        "tamil-toolkit",
        "exec",
        "wasm-pack",
        "build",
        ".",
        mode,
        "--target",
        target,
        "--out-dir",
        directory,
        "--out-name",
        "tamil_toolkit",
        "--locked",
        *cargo_feature_args(spec),
    ]


def _resolve_executable(command: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        home_bin = Path.home() / ".cargo" / "bin" / (f"{command}.exe" if sys.platform == "win32" else command)
        if home_bin.exists():
            executable = str(home_bin)
    return executable


def run(*args, cwd=None, extra_env=None):
    work_dir = ROOT if cwd is None else cwd
    executable = _resolve_executable(args[0])
    if executable is None:
        raise RuntimeError(f"Missing {args[0]}; see README.md prerequisites and just doctor")
    with _PRINT_LOCK:
        print("+ " + " ".join(args), flush=True)
    cargo_bin = Path.home() / ".cargo" / "bin"
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    if cargo_bin.exists() and str(cargo_bin) not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = f"{cargo_bin}{os.pathsep}{env.get('PATH', '')}"
    subprocess.run([executable, *args[1:]], cwd=work_dir, check=True, env=env)


def detect_total_ram_gib() -> float:
    """Return physical host RAM in GiB without requiring third-party packages."""
    if sys.platform == "win32":
        class _MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) and status.ullTotalPhys > 0:
            return status.ullTotalPhys / float(1024 ** 3)
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return (int(parts[1]) * 1024) / float(1024 ** 3)
    if hasattr(os, "sysconf"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            if isinstance(pages, int) and isinstance(page_size, int) and pages > 0 and page_size > 0:
                return (pages * page_size) / float(1024 ** 3)
        except (ValueError, OSError):
            pass
    return 16.0


def _parse_positive_int_override(env: Mapping[str, str], key: str) -> int | None:
    raw = env.get(key)
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw.strip())
    except ValueError as error:
        raise ValueError(f"{key} must be a positive integer, got {raw!r}") from error
    if value <= 0:
        raise ValueError(f"{key} must be a positive integer, got {raw!r}")
    return value


def compute_build_budget(
    pending_builds: int,
    *,
    cpu_count: int | None = None,
    ram_gib: float | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[int, int]:
    """Return `(max_workers, cargo_jobs_per_worker)` bounded by CPU and RAM."""
    if pending_builds <= 0:
        return (1, 1)
    source_env = os.environ if env is None else env
    cpus = max(1, cpu_count if cpu_count is not None else (os.cpu_count() or 4))
    ram = max(1.0, ram_gib if ram_gib is not None else detect_total_ram_gib())

    ram_worker_cap = 1 if ram < 6.0 else 2 if ram < 12.0 else 3 if ram <= 20.0 else 4
    worker_override = _parse_positive_int_override(source_env, "TAMIL_BINDING_CONCURRENCY")
    if worker_override is not None:
        max_workers = max(1, min(pending_builds, worker_override))
    else:
        max_workers = max(1, min(pending_builds, cpus, ram_worker_cap))

    # Reserve host headroom when running multiple rustc/LLVM toolchains concurrently.
    single_build_cap = min(cpus, 8 if ram <= 20.0 else 12)
    cpu_per_worker = single_build_cap if max_workers == 1 else max(1, cpus // max_workers)
    ram_per_worker = max(1, int((ram + 1.0) // (1.8 * max_workers)))
    cargo_jobs = max(1, min(cpu_per_worker, ram_per_worker))

    user_cargo_jobs = _parse_positive_int_override(source_env, "CARGO_BUILD_JOBS")
    if user_cargo_jobs is not None:
        cargo_jobs = min(cargo_jobs, user_cargo_jobs)
    custom_jobs = _parse_positive_int_override(source_env, "TAMIL_CARGO_BUILD_JOBS")
    if custom_jobs is not None:
        cargo_jobs = custom_jobs
    return (max_workers, cargo_jobs)


def _is_cargo_target_dir_populated(target_dir: Path) -> bool:
    if not target_dir.is_dir():
        return False
    return any(
        (target_dir / subdir).is_dir()
        for subdir in ("debug", "release", "wasm32-unknown-unknown")
    )


def check_binding_disk_budget(
    root: Path,
    *,
    profile: str,
    targets: Iterable[str],
    release: bool = False,
) -> dict[str, object]:
    """Ensure adequate free disk space for pending isolated `CARGO_TARGET_DIR` builds."""
    pending_targets = list(targets)
    if not pending_targets:
        return {"required_gib": 0.0, "free_gib": 0.0, "cold_targets": [], "warm_targets": []}

    cold_targets: list[str] = []
    warm_targets: list[str] = []
    required_gib = _DISK_SAFETY_HEADROOM_GIB
    for target in pending_targets:
        target_dir = binding_cargo_target_dir(root, profile, target, release=release)
        if _is_cargo_target_dir_populated(target_dir):
            warm_targets.append(target)
            required_gib += _WARM_TARGET_DISK_GIB
        else:
            cold_targets.append(target)
            required_gib += _COLD_TARGET_DISK_GIB.get(target, 1.5)

    probe_path = root / BINDING_CACHE_DIR_REL
    while not probe_path.exists() and probe_path.parent != probe_path:
        probe_path = probe_path.parent
    free_gib = shutil.disk_usage(probe_path).free / float(_GIB)
    if free_gib < required_gib:
        cold_desc = ", ".join(cold_targets) if cold_targets else "none"
        warm_desc = ", ".join(warm_targets) if warm_targets else "none"
        cache_root = root / BINDING_CACHE_DIR_REL / "cargo"
        raise RuntimeError(
            f"Insufficient free disk space for isolated binding Cargo builds ({profile}): "
            f"{free_gib:.2f} GiB free < {required_gib:.2f} GiB required "
            f"(cold targets: {cold_desc}; warm targets: {warm_desc}; headroom: {_DISK_SAFETY_HEADROOM_GIB:.1f} GiB). "
            f"Free disk space or remove stale profile caches under {cache_root}."
        )
    return {
        "required_gib": required_gib,
        "free_gib": free_gib,
        "cold_targets": cold_targets,
        "warm_targets": warm_targets,
    }


def _sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _iter_tree_files(
    directory: Path,
    *,
    exclude_dirs: frozenset[str] = frozenset(),
    exclude_dir_suffixes: tuple[str, ...] = (),
    exclude_names: frozenset[str] = frozenset(),
    predicate=None,
) -> list[Path]:
    if not directory.is_dir():
        return []
    collected: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in exclude_dirs and not (exclude_dir_suffixes and name.endswith(exclude_dir_suffixes))
        )
        for name in sorted(filenames):
            if name in exclude_names:
                continue
            path = Path(dirpath) / name
            if predicate is None or predicate(path):
                collected.append(path)
    return collected


def _hash_file_map(
    paths: Iterable[Path],
    *,
    root: Path,
    digest_cache: dict[Path, str] | None = None,
) -> dict[str, str]:
    entries: dict[str, str] = {}
    unique_paths = sorted({path for path in paths if path.is_file()}, key=lambda p: p.relative_to(root).as_posix())
    for path in unique_paths:
        digest = digest_cache.get(path) if digest_cache is not None else None
        if digest is None:
            digest = _sha256_file(path)
            if digest_cache is not None:
                digest_cache[path] = digest
        entries[path.relative_to(root).as_posix()] = digest
    return entries


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _probe_command_output(args: list[str], *, cwd: Path) -> str:
    executable = _resolve_executable(args[0])
    if executable is None:
        return "missing"
    try:
        result = subprocess.run(
            [executable, *args[1:]],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return "missing"
    if result.returncode != 0:
        return f"error:{result.returncode}"
    return result.stdout.strip()


def _read_npm_tool_version(root: Path, package_name: str) -> str:
    pkg_json = root / "bindings/js-wasm/node_modules" / package_name / "package.json"
    if not pkg_json.is_file():
        return "missing"
    try:
        return str(json.loads(pkg_json.read_text(encoding="utf-8")).get("version", "unknown"))
    except (OSError, json.JSONDecodeError):
        return "unreadable"


def collect_toolchain_fingerprint(root: Path) -> dict[str, object]:
    """Capture compiler, binding-tool, Python ABI, and build-flag state."""
    try:
        maturin_dist_version = importlib.metadata.version("maturin")
    except importlib.metadata.PackageNotFoundError:
        maturin_dist_version = "missing"
    return {
        "rustc": _probe_command_output(["rustc", "-vV"], cwd=root),
        "cargo": _probe_command_output(["cargo", "--version"], cwd=root),
        "maturin_cli": _probe_command_output(["maturin", "--version"], cwd=root),
        "maturin_dist": maturin_dist_version,
        "node": _probe_command_output(["node", "--version"], cwd=root),
        "pnpm": _probe_command_output(["pnpm", "--version"], cwd=root),
        "wasm_pack_npm": _read_npm_tool_version(root, "wasm-pack"),
        "typescript_npm": _read_npm_tool_version(root, "typescript"),
        "python_version": list(sys.version_info[:2]),
        "python_impl": sys.implementation.name,
        "python_ext_suffix": sysconfig.get_config_var("EXT_SUFFIX") or "",
        "python_prefix": sys.prefix,
        "platform": sys.platform,
        "machine": platform.machine(),
        "env": {key: os.environ.get(key) for key in _BUILD_ENV_KEYS},
    }


def _shared_workspace_files(root: Path) -> list[Path]:
    files = [
        root / "Cargo.toml",
        root / "Cargo.lock",
        root / "rust-toolchain.toml",
        root / ".cargo/config.toml",
    ]
    files.extend(_iter_tree_files(root / "crates", exclude_dirs=_EXCLUDED_CRATE_DIRS))
    return [path for path in files if path.is_file()]


def _dart_library_filename() -> str:
    prefix = "" if sys.platform == "win32" else "lib"
    suffix = ".dll" if sys.platform == "win32" else ".dylib" if sys.platform == "darwin" else ".so"
    return f"{prefix}tamil_toolkit_ffi{suffix}"


def binding_cargo_target_dir(root: Path, profile: str, target: str, *, release: bool = False) -> Path:
    """Return an isolated `CARGO_TARGET_DIR` per `(profile, target[, mode])`."""
    suffix = f"{target}-{'release' if release else 'dev'}" if target in ("wasm-node", "wasm-web") else target
    return (root / BINDING_CACHE_DIR_REL / "cargo" / profile / suffix).resolve()


def binding_stamp_path(root: Path, target: str) -> Path:
    return root / BINDING_CACHE_DIR_REL / "stamps" / f"{target}.json"


def _invalidate_stamp(root: Path, target: str) -> None:
    binding_stamp_path(root, target).unlink(missing_ok=True)


def _stale_python_native_artifacts(package_dir: Path) -> list[Path]:
    if not package_dir.is_dir():
        return []
    candidates = [*package_dir.glob("_native.*.pyd"), *package_dir.glob("_native.*.so")]
    if sys.platform == "win32":
        return sorted(candidates)
    return sorted(path for path in candidates if path.name != "_native.abi3.so")


def _cleanup_stale_python_extensions(package_dir: Path) -> None:
    # Old interpreter-tagged builds take import precedence over maturin's new
    # abi3 extension. Remove only generated native-extension artifacts.
    if not package_dir.is_dir():
        return
    for pattern in ("_native.*.pyd", "_native.*.so"):
        for artifact in package_dir.glob(pattern):
            artifact.unlink()


def _collect_target_outputs(root: Path, target: str) -> dict[str, Path] | None:
    """Return `{relative_name: Path}` if all required outputs exist and are non-empty, else `None`."""
    if target == "licenses":
        paths = [
            root / "bindings/python/THIRD_PARTY_LICENSES.txt",
            root / "bindings/js-wasm/THIRD_PARTY_LICENSES.txt",
        ]
        if not all(path.is_file() and path.stat().st_size > 0 for path in paths):
            return None
        return {path.relative_to(root).as_posix(): path for path in paths}

    if target == "python":
        package_dir = root / "bindings/python/python/tamil_toolkit"
        if not package_dir.is_dir() or _stale_python_native_artifacts(package_dir):
            return None
        extensions = sorted(
            path
            for path in (*package_dir.glob("_native*.pyd"), *package_dir.glob("_native*.so"))
            if path.is_file()
        )
        if not extensions or any(path.stat().st_size <= 0 for path in extensions):
            return None
        return {path.relative_to(package_dir).as_posix(): path for path in extensions}

    if target in ("wasm-node", "wasm-web"):
        out_dir = root / "bindings/js-wasm" / ("pkg-node" if target == "wasm-node" else "pkg-web")
        if not out_dir.is_dir():
            return None
        for req_name in _REQUIRED_WASM_OUTPUTS:
            req_path = out_dir / req_name
            if not req_path.is_file() or req_path.stat().st_size <= 0:
                return None
        artifacts = sorted(
            path
            for path in out_dir.iterdir()
            if path.is_file() and (path.suffix in {".wasm", ".js", ".ts"} or path.name == "package.json")
        )
        return {path.relative_to(out_dir).as_posix(): path for path in artifacts}

    if target == "js-tsc":
        dist_dir = root / "bindings/js-wasm/dist"
        if not dist_dir.is_dir():
            return None
        for req_name in _REQUIRED_TSC_OUTPUTS:
            req_path = dist_dir / req_name
            if not req_path.is_file() or req_path.stat().st_size <= 0:
                return None
        files = _iter_tree_files(dist_dir)
        if not files or any(path.stat().st_size <= 0 for path in files):
            return None
        return {path.relative_to(dist_dir).as_posix(): path for path in files}

    if target == "dart":
        lib_name = _dart_library_filename()
        canonical_lib = root / "target/debug" / lib_name
        if not canonical_lib.is_file() or canonical_lib.stat().st_size <= 0:
            return None
        return {lib_name: canonical_lib}

    raise ValueError(f"Unknown binding target: {target!r}")


def _compute_target_input_hash(
    root: Path,
    target: str,
    spec: LexiconProfile,
    toolchain: dict[str, object],
    *,
    release: bool = False,
    digest_cache: dict[Path, str] | None = None,
) -> str:
    if target == "licenses":
        cargo_manifests = [
            root / "Cargo.toml",
            root / "Cargo.lock",
            root / "rust-toolchain.toml",
            root / "tools/release.py",
            root / "bindings/python/Cargo.toml",
            root / "bindings/js-wasm/Cargo.toml",
            *(root / "crates").glob("*/Cargo.toml"),
        ]
        payload = {
            "target": target,
            "cargo": toolchain["cargo"],
            "files": _hash_file_map(cargo_manifests, root=root, digest_cache=digest_cache),
        }
        return _canonical_sha256(payload)

    if target == "js-tsc":
        js_root = root / "bindings/js-wasm"
        files = [
            root / "pnpm-lock.yaml",
            js_root / "package.json",
            js_root / "tsconfig.json",
            *_iter_tree_files(js_root / "src", predicate=lambda p: p.suffix == ".ts"),
            *(js_root / "pkg-node").glob("*.js"),
            *(js_root / "pkg-node").glob("*.d.ts"),
            *(js_root / "pkg-web").glob("*.js"),
            *(js_root / "pkg-web").glob("*.d.ts"),
        ]
        payload = {
            "target": target,
            "profile": spec.name,
            "node": toolchain["node"],
            "pnpm": toolchain["pnpm"],
            "typescript_npm": toolchain["typescript_npm"],
            "files": _hash_file_map(files, root=root, digest_cache=digest_cache),
        }
        return _canonical_sha256(payload)

    files = _shared_workspace_files(root)
    target_toolchain: dict[str, object] = {
        "rustc": toolchain["rustc"],
        "cargo": toolchain["cargo"],
        "platform": toolchain["platform"],
        "machine": toolchain["machine"],
        "env": toolchain["env"],
    }
    if target == "python":
        package_dir = (root / "bindings/python/python/tamil_toolkit").resolve()
        files.extend(
            _iter_tree_files(
                root / "bindings/python",
                exclude_dirs=_EXCLUDED_PYTHON_DIRS,
                exclude_dir_suffixes=(".egg-info", ".dist-info"),
                predicate=lambda p: not (
                    p.parent.resolve() == package_dir and p.name.startswith("_native")
                ),
            )
        )
        target_toolchain.update(
            {
                "maturin_cli": toolchain["maturin_cli"],
                "maturin_dist": toolchain["maturin_dist"],
                "python_version": toolchain["python_version"],
                "python_impl": toolchain["python_impl"],
                "python_ext_suffix": toolchain["python_ext_suffix"],
                "python_prefix": toolchain["python_prefix"],
            }
        )
        feature_args = maturin_feature_args(spec)
        build_command = ["maturin", "develop", "--locked", *feature_args]
    elif target in ("wasm-node", "wasm-web"):
        js_root = root / "bindings/js-wasm"
        files.extend(
            [
                js_root / "Cargo.toml",
                js_root / ".cargo/config.toml",
                js_root / "package.json",
                js_root / "LICENSE",
                js_root / "THIRD_PARTY_NOTICES.md",
                js_root / "THIRD_PARTY_LICENSES.txt",
                *_iter_tree_files(js_root / "src", predicate=lambda p: p.suffix == ".rs"),
            ]
        )
        target_toolchain.update(
            {
                "node": toolchain["node"],
                "pnpm": toolchain["pnpm"],
                "wasm_pack_npm": toolchain["wasm_pack_npm"],
            }
        )
        feature_args = cargo_feature_args(spec)
        wasm_dir = "pkg-node" if target == "wasm-node" else "pkg-web"
        wasm_target = "nodejs" if target == "wasm-node" else "web"
        build_command = wasm_pack_build_command(spec, wasm_target, wasm_dir, release=release)
    elif target == "dart":
        files.extend(
            _iter_tree_files(
                root / "bindings/dart-flutter/rust",
                exclude_dirs=frozenset({"target", ".git"}),
            )
        )
        feature_args = cargo_feature_args(spec)
        build_command = ["cargo", "build", "--locked", "-p", "tamil-dart", *feature_args]
    else:
        raise ValueError(f"Unknown binding target: {target!r}")

    payload = {
        "schema_version": BINDING_CACHE_SCHEMA_VERSION,
        "target": target,
        "profile": spec.name,
        "release": bool(release) if target in ("wasm-node", "wasm-web") else False,
        "features": list(spec.features),
        "feature_args": feature_args,
        "build_command": build_command,
        "pack_manifests": spec.pack_manifests_map(),
        "toolchain": target_toolchain,
        "files": _hash_file_map(files, root=root, digest_cache=digest_cache),
    }
    return _canonical_sha256(payload)


def is_binding_cache_valid(
    root: Path,
    target: str,
    *,
    expected_profile: str,
    expected_input_hash: str,
    digest_cache: dict[Path, str] | None = None,
) -> bool:
    """Return `True` only when stamp metadata, input hashes, and output hashes all match."""
    stamp_file = binding_stamp_path(root, target)
    if not stamp_file.is_file():
        return False
    try:
        stamp = json.loads(stamp_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(stamp, dict):
        return False
    if stamp.get("schema_version") != BINDING_CACHE_SCHEMA_VERSION:
        return False
    if stamp.get("target") != target or stamp.get("profile") != expected_profile:
        return False
    if stamp.get("input_hash") != expected_input_hash:
        return False
    recorded_outputs = stamp.get("outputs")
    if not isinstance(recorded_outputs, dict) or not recorded_outputs:
        return False

    actual_paths = _collect_target_outputs(root, target)
    if actual_paths is None or set(actual_paths) != set(recorded_outputs):
        return False
    for rel_name, path in actual_paths.items():
        expected_digest = recorded_outputs.get(rel_name)
        if not isinstance(expected_digest, str) or len(expected_digest) != 64:
            return False
        actual_digest = digest_cache.get(path) if digest_cache is not None else None
        if actual_digest is None:
            try:
                actual_digest = _sha256_file(path)
            except OSError:
                return False
            if digest_cache is not None:
                digest_cache[path] = actual_digest
        if actual_digest != expected_digest:
            return False
    return True


def _write_binding_stamp(root: Path, target: str, *, profile: str, input_hash: str) -> None:
    outputs = _collect_target_outputs(root, target)
    if outputs is None:
        return
    output_hashes = {
        rel_name: _sha256_file(path)
        for rel_name, path in sorted(outputs.items())
    }
    stamp_file = binding_stamp_path(root, target)
    stamp_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": BINDING_CACHE_SCHEMA_VERSION,
        "target": target,
        "profile": profile,
        "input_hash": input_hash,
        "outputs": output_hashes,
    }
    tmp_file = stamp_file.with_name(f".{stamp_file.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp_file.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_file, stamp_file)


class _CrossProcessFileLock:
    """Advisory cross-process file lock using OS file locking primitives."""

    def __init__(self, lock_path: Path, *, timeout_seconds: float = _DEFAULT_CANONICAL_LEASE_TIMEOUT_SECONDS) -> None:
        self.lock_path = lock_path
        self.timeout_seconds = timeout_seconds
        self._handle = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout_seconds
        handle = self.lock_path.open("a+b")
        try:
            if sys.platform == "win32":
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\n")
                    handle.flush()
            while True:
                try:
                    if sys.platform == "win32":
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._handle = handle
                    return
                except OSError as error:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timed out waiting for lock {self.lock_path}") from error
                    time.sleep(0.05)
        except BaseException:
            handle.close()
            raise

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            if sys.platform == "win32":
                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()


def canonical_lease_paths(root: Path) -> tuple[Path, Path]:
    locks_dir = root / BINDING_CACHE_DIR_REL / "locks"
    return (locks_dir / "canonical-outputs.lock", locks_dir / "canonical-outputs.lease.json")


def _lease_timeout_seconds() -> float:
    raw = os.environ.get("TAMIL_CANONICAL_LEASE_TIMEOUT_SECONDS")
    if raw is None or not raw.strip():
        return _DEFAULT_CANONICAL_LEASE_TIMEOUT_SECONDS
    try:
        value = float(raw.strip())
    except ValueError as error:
        raise ValueError(f"TAMIL_CANONICAL_LEASE_TIMEOUT_SECONDS must be positive, got {raw!r}") from error
    if value <= 0:
        raise ValueError(f"TAMIL_CANONICAL_LEASE_TIMEOUT_SECONDS must be positive, got {raw!r}")
    return value


def _read_and_validate_lease_state(
    state_path: Path,
    *,
    expected_pid: int | None = None,
    expected_nonce: str | None = None,
    expected_profile: str | None = None,
) -> dict:
    if not state_path.is_file():
        raise RuntimeError(f"Missing canonical binding lease state: {state_path}")
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Malformed canonical binding lease state in {state_path}: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Malformed canonical binding lease state in {state_path}: expected JSON object")
    if payload.get("schema_version") != BINDING_CACHE_SCHEMA_VERSION:
        raise RuntimeError(
            f"Unsupported canonical binding lease schema_version in {state_path}: {payload.get('schema_version')!r}"
        )
    pid = payload.get("pid")
    nonce = payload.get("nonce")
    profile = payload.get("profile")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise RuntimeError(f"Malformed canonical binding lease pid in {state_path}: {pid!r}")
    if not isinstance(nonce, str) or not nonce:
        raise RuntimeError(f"Malformed canonical binding lease nonce in {state_path}")
    if not isinstance(profile, str) or not profile:
        raise RuntimeError(f"Malformed canonical binding lease profile in {state_path}: {profile!r}")
    if expected_pid is not None and pid != expected_pid:
        raise RuntimeError(
            f"Canonical binding lease pid mismatch in {state_path}: expected {expected_pid}, found {pid}"
        )
    if expected_nonce is not None and nonce != expected_nonce:
        raise RuntimeError(f"Canonical binding lease nonce mismatch in {state_path}")
    if expected_profile is not None and profile != expected_profile:
        raise RuntimeError(
            f"Canonical binding lease profile mismatch in {state_path}: "
            f"expected {expected_profile!r}, active lease is {profile!r}"
        )
    return payload


def verify_canonical_lease(root: Path, *, expected_profile: str | None = None) -> dict:
    """Verify this process holds an active, well-formed canonical binding output lease."""
    resolved_root = root.resolve()
    with _CANONICAL_LEASE_MUTEX:
        depth = _CANONICAL_LEASE_STATE.depth
        lease_root = _CANONICAL_LEASE_STATE.root
        nonce = _CANONICAL_LEASE_STATE.nonce
        active_profile = _CANONICAL_LEASE_STATE.profile
    if depth <= 0 or lease_root != resolved_root or not nonce:
        raise RuntimeError(f"No active canonical binding output lease held for {resolved_root}")
    if expected_profile is not None and active_profile != expected_profile:
        raise RuntimeError(
            f"Active canonical binding lease profile {active_profile!r} does not match {expected_profile!r}"
        )
    _, state_path = canonical_lease_paths(resolved_root)
    return _read_and_validate_lease_state(
        state_path,
        expected_pid=os.getpid(),
        expected_nonce=nonce,
        expected_profile=expected_profile,
    )


@contextmanager
def canonical_output_lease(
    root: Path,
    *,
    profile: str,
    targets: Iterable[str] | None = None,
):
    """Acquire or re-enter the cross-process lease protecting canonical binding outputs."""
    resolved_root = root.resolve()
    lock_path, state_path = canonical_lease_paths(resolved_root)

    with _CANONICAL_LEASE_MUTEX:
        if _CANONICAL_LEASE_STATE.depth > 0:
            if _CANONICAL_LEASE_STATE.root != resolved_root:
                raise RuntimeError(
                    f"Canonical binding lease root mismatch: held for {_CANONICAL_LEASE_STATE.root}, "
                    f"requested {resolved_root}"
                )
            _read_and_validate_lease_state(
                state_path,
                expected_pid=os.getpid(),
                expected_nonce=_CANONICAL_LEASE_STATE.nonce,
                expected_profile=profile,
            )
            _CANONICAL_LEASE_STATE.depth += 1
        else:
            timeout = _lease_timeout_seconds()
            lock = _CrossProcessFileLock(lock_path, timeout_seconds=timeout)
            try:
                lock.acquire()
            except TimeoutError as error:
                detail = "lease state missing or malformed"
                try:
                    holder = _read_and_validate_lease_state(state_path)
                    detail = f"held by pid={holder['pid']} profile={holder['profile']!r}"
                except RuntimeError as state_err:
                    detail = str(state_err)
                raise RuntimeError(
                    f"Timed out after {timeout:.1f}s waiting for canonical binding output lease ({detail})"
                ) from error

            try:
                if state_path.exists():
                    # Reject corrupted/malformed lease state files rather than silently overwriting them.
                    _read_and_validate_lease_state(state_path)
                nonce = uuid.uuid4().hex
                payload = {
                    "schema_version": BINDING_CACHE_SCHEMA_VERSION,
                    "pid": os.getpid(),
                    "nonce": nonce,
                    "profile": profile,
                    "targets": list(targets or ()),
                    "acquired_at": time.time(),
                }
                tmp_state = state_path.with_name(f".{state_path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
                tmp_state.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                os.replace(tmp_state, state_path)
            except BaseException:
                lock.release()
                raise

            _CANONICAL_LEASE_STATE.root = resolved_root
            _CANONICAL_LEASE_STATE.depth = 1
            _CANONICAL_LEASE_STATE.profile = profile
            _CANONICAL_LEASE_STATE.nonce = nonce
            _CANONICAL_LEASE_STATE.lock_handle = lock

    try:
        yield
    finally:
        with _CANONICAL_LEASE_MUTEX:
            _CANONICAL_LEASE_STATE.depth -= 1
            if _CANONICAL_LEASE_STATE.depth == 0:
                lock = _CANONICAL_LEASE_STATE.lock_handle
                try:
                    state_path.unlink(missing_ok=True)
                finally:
                    _CANONICAL_LEASE_STATE.root = None
                    _CANONICAL_LEASE_STATE.profile = None
                    _CANONICAL_LEASE_STATE.nonce = None
                    _CANONICAL_LEASE_STATE.lock_handle = None
                    if lock is not None:
                        lock.release()


def _locked_wasm_bindgen_version(root: Path) -> str | None:
    lock_path = root / "Cargo.lock"
    if not lock_path.is_file():
        return None
    try:
        packages = tomllib.loads(lock_path.read_text(encoding="utf-8")).get("package", ())
    except (OSError, tomllib.TOMLDecodeError):
        return None
    for pkg in packages:
        if isinstance(pkg, dict) and pkg.get("name") == "wasm-bindgen":
            version = pkg.get("version")
            if isinstance(version, str) and version:
                return version
    return None


def _wasm_pack_cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData/Local"))
        return base / ".wasm-pack"
    if sys.platform == "darwin":
        return Path.home() / "Library/Caches/.wasm-pack"
    base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return base / ".wasm-pack"


def is_wasm_bindgen_bootstrapped(root: Path) -> bool:
    """Return `True` only when a verified `wasm-bindgen` binary matching `Cargo.lock` is cached."""
    expected_version = _locked_wasm_bindgen_version(root)
    exe_name = "wasm-bindgen.exe" if sys.platform == "win32" else "wasm-bindgen"
    candidates: list[Path] = []
    on_path = _resolve_executable("wasm-bindgen")
    if on_path is not None:
        candidates.append(Path(on_path))
    cache_dir = _wasm_pack_cache_dir()
    if cache_dir.is_dir():
        candidates.extend(sorted(cache_dir.glob(f"wasm-bindgen-*/{exe_name}")))
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            if candidate.stat().st_size <= 0:
                continue
        except OSError:
            continue
        if expected_version is None:
            return True
        version_out = _probe_command_output([str(candidate), "--version"], cwd=root)
        if expected_version in version_out:
            return True
    return False


def _stage_dart_canonical_library(root: Path, dart_target_dir: Path, *, profile: str) -> None:
    lib_name = _dart_library_filename()
    built_lib = dart_target_dir / "debug" / lib_name
    if not built_lib.is_file():
        return
    verify_canonical_lease(root, expected_profile=profile)
    canonical_lib = root / "target/debug" / lib_name
    canonical_lib.parent.mkdir(parents=True, exist_ok=True)
    tmp_lib = canonical_lib.with_name(f".{lib_name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        shutil.copy2(built_lib, tmp_lib)
        os.replace(tmp_lib, canonical_lib)
    except PermissionError as error:
        tmp_lib.unlink(missing_ok=True)
        raise RuntimeError(
            f"Cannot overwrite canonical Dart FFI library {canonical_lib}; "
            "close any running Dart/FFI consumer holding the DLL lock."
        ) from error
    except BaseException:
        tmp_lib.unlink(missing_ok=True)
        raise


def _should_force_rebuild(force: bool) -> bool:
    if force:
        return True
    return os.environ.get("TAMIL_FORCE_BINDING_REBUILD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _normalize_binding_targets(
    targets: Iterable[str] | None,
    *,
    include_dart: bool,
) -> tuple[str, ...]:
    if targets is None:
        base = list(DEFAULT_BINDING_TARGETS)
        if include_dart:
            base.append("dart")
        return tuple(base)
    normalized = tuple(dict.fromkeys(item.strip().lower() for item in targets if item.strip()))
    if not normalized:
        raise ValueError("At least one binding target must be specified")
    unknown = [item for item in normalized if item not in ALL_BINDING_TARGETS]
    if unknown:
        raise ValueError(
            f"Unsupported binding targets: {', '.join(unknown)} "
            f"(expected subset of {', '.join(ALL_BINDING_TARGETS)})"
        )
    if include_dart and "dart" not in normalized:
        normalized = (*normalized, "dart")
    return normalized


def _build_single_target(
    root: Path,
    spec: LexiconProfile,
    target: str,
    *,
    cargo_jobs: int,
    release: bool,
) -> None:
    target_dir = binding_cargo_target_dir(root, spec.name, target, release=release)
    target_dir.mkdir(parents=True, exist_ok=True)
    build_env = {
        "CARGO_TARGET_DIR": str(target_dir),
        "CARGO_BUILD_JOBS": str(cargo_jobs),
    }
    if target == "python":
        verify_canonical_lease(root, expected_profile=spec.name)
        _cleanup_stale_python_extensions(root / "bindings/python/python/tamil_toolkit")
        run(
            "maturin",
            "develop",
            "--locked",
            *maturin_feature_args(spec),
            cwd=root / "bindings/python",
            extra_env=build_env,
        )
    elif target in {"wasm-node", "wasm-web"}:
        out_dir = "pkg-node" if target == "wasm-node" else "pkg-web"
        pack_target = "nodejs" if target == "wasm-node" else "web"
        cmd = wasm_pack_build_command(spec, pack_target, out_dir, release=release)
        if not is_wasm_bindgen_bootstrapped(root):
            bootstrap_lock_path = root / BINDING_CACHE_DIR_REL / "locks/wasm-bindgen-bootstrap.lock"
            bootstrap_lock = _CrossProcessFileLock(bootstrap_lock_path, timeout_seconds=300.0)
            bootstrap_lock.acquire()
            try:
                verify_canonical_lease(root, expected_profile=spec.name)
                run(*cmd, cwd=root, extra_env=build_env)
            finally:
                bootstrap_lock.release()
        else:
            verify_canonical_lease(root, expected_profile=spec.name)
            run(*cmd, cwd=root, extra_env=build_env)
    elif target == "dart":
        run(
            "cargo",
            "build",
            "--locked",
            "-p",
            "tamil-dart",
            *cargo_feature_args(spec),
            cwd=root,
            extra_env=build_env,
        )
        _stage_dart_canonical_library(root, target_dir, profile=spec.name)
    else:
        raise ValueError(f"Unknown binding target: {target!r}")


def _ensure_licenses(root: Path, spec: LexiconProfile, toolchain: dict[str, object], *, force: bool) -> bool:
    digest_cache: dict[Path, str] = {}
    input_hash = _compute_target_input_hash(root, "licenses", spec, toolchain, digest_cache=digest_cache)
    if not force and is_binding_cache_valid(
        root,
        "licenses",
        expected_profile="shared",
        expected_input_hash=input_hash,
        digest_cache=digest_cache,
    ):
        return False
    _invalidate_stamp(root, "licenses")
    run(sys.executable, "tools/release.py", "licenses", cwd=root)
    _write_binding_stamp(root, "licenses", profile="shared", input_hash=input_hash)
    return True


def check_unicode():
    run(sys.executable, "tools/release_policy.py", "check")
    run(sys.executable, "tools/mcp-tamil-oracle/check_source_unicode.py")
    for projection in (
        "tools/extract_numeral_ordinal_data.py",
        "tools/extract_numeral_symbol_data.py",
        "tools/extract_numeral_traditional_data.py",
        "tools/generate_tokenize_unicode.py",
    ):
        run(sys.executable, projection, "--check")
    run(sys.executable, "tools/release_files.py", "--check")


def test_rust(profile=None):
    spec = resolve_lexicon_profile(profile)
    env = profile_env(spec, include_planned=bool(spec.planned_suites))
    cargo_bin = Path.home() / ".cargo" / "bin"
    nextest_bin = cargo_bin / ("cargo-nextest.exe" if sys.platform == "win32" else "cargo-nextest")
    if shutil.which("cargo-nextest") or nextest_bin.exists():
        run("cargo", "nextest", "run", "--locked", "--workspace", *cargo_feature_args(spec), extra_env=env)
        run("cargo", "test", "--locked", "--workspace", "--exclude", "tamil-python", "--doc", *cargo_feature_args(spec), extra_env=env)
    else:
        print("cargo-nextest is optional; using cargo test (including the same proptest tests).", flush=True)
        run("cargo", "test", "--locked", "--workspace", *cargo_feature_args(spec), extra_env=env)


def sync_bindings(
    profile=None,
    *,
    force: bool = False,
    include_dart: bool = False,
    targets: Iterable[str] | None = None,
    release: bool = False,
):
    root = ROOT
    spec = resolve_lexicon_profile(profile, root=root)
    selected_targets = _normalize_binding_targets(targets, include_dart=include_dart)
    force_rebuild = _should_force_rebuild(force)
    toolchain = collect_toolchain_fingerprint(root)

    with canonical_output_lease(root, profile=spec.name, targets=selected_targets):
        verify_canonical_lease(root, expected_profile=spec.name)
        digest_cache: dict[Path, str] = {}
        input_hashes: dict[str, str] = {}
        pending: list[str] = []
        cached: list[str] = []

        for target in selected_targets:
            input_hash = _compute_target_input_hash(
                root,
                target,
                spec,
                toolchain,
                release=release,
                digest_cache=digest_cache,
            )
            input_hashes[target] = input_hash
            if not force_rebuild and is_binding_cache_valid(
                root,
                target,
                expected_profile=spec.name,
                expected_input_hash=input_hash,
                digest_cache=digest_cache,
            ):
                cached.append(target)
            else:
                pending.append(target)

        if pending:
            check_binding_disk_budget(root, profile=spec.name, targets=pending, release=release)

        if any(target in selected_targets for target in ("python", "wasm-node", "wasm-web")):
            if _ensure_licenses(root, spec, toolchain, force=force_rebuild):
                # Generated notices are build inputs. Recheck after generation,
                # without trusting hashes computed against the previous bytes.
                digest_cache.clear()
                pending.clear()
                cached.clear()
                for target in selected_targets:
                    input_hash = _compute_target_input_hash(
                        root, target, spec, toolchain, release=release, digest_cache=digest_cache,
                    )
                    input_hashes[target] = input_hash
                    if not force_rebuild and is_binding_cache_valid(
                        root, target, expected_profile=spec.name,
                        expected_input_hash=input_hash, digest_cache=digest_cache,
                    ):
                        cached.append(target)
                    else:
                        pending.append(target)

        if cached:
            with _PRINT_LOCK:
                print(
                    f"sync-bindings ({spec.name}): reusing verified cached {', '.join(cached)}",
                    flush=True,
                )

        if pending:
            check_binding_disk_budget(root, profile=spec.name, targets=pending, release=release)
            for target in pending:
                _invalidate_stamp(root, target)
                if target == "python":
                    _cleanup_stale_python_extensions(root / "bindings/python/python/tamil_toolkit")

            max_workers, cargo_jobs = compute_build_budget(len(pending))
            with _PRINT_LOCK:
                print(
                    f"sync-bindings ({spec.name}): building {', '.join(pending)} "
                    f"(workers={max_workers}, cargo_jobs={cargo_jobs})",
                    flush=True,
                )

            failures: list[tuple[str, BaseException]] = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(
                        _build_single_target,
                        root,
                        spec,
                        target,
                        cargo_jobs=cargo_jobs,
                        release=release,
                    ): target
                    for target in pending
                }
                for future in as_completed(future_map):
                    target = future_map[future]
                    try:
                        future.result()
                    except BaseException as error:
                        failures.append((target, error))
                    else:
                        _write_binding_stamp(
                            root,
                            target,
                            profile=spec.name,
                            input_hash=input_hashes[target],
                        )
            if failures:
                failed_names = ", ".join(name for name, _ in sorted(failures))
                first_error = failures[0][1]
                if len(failures) == 1 and isinstance(first_error, (RuntimeError, ValueError, subprocess.CalledProcessError)):
                    raise first_error
                raise RuntimeError(f"Binding build failed for [{failed_names}]: {first_error}") from first_error

        if "wasm-node" in selected_targets or "wasm-web" in selected_targets:
            verify_canonical_lease(root, expected_profile=spec.name)
            both_wasm_selected = "wasm-node" in selected_targets and "wasm-web" in selected_targets
            has_node_outputs = _collect_target_outputs(root, "wasm-node") is not None
            has_web_outputs = _collect_target_outputs(root, "wasm-web") is not None
            if not both_wasm_selected and not (has_node_outputs and has_web_outputs):
                _invalidate_stamp(root, "js-tsc")
                with _PRINT_LOCK:
                    print(
                        f"sync-bindings ({spec.name}): deferring js-tsc until both wasm-node and wasm-web outputs exist",
                        flush=True,
                    )
            else:
                tsc_digest_cache: dict[Path, str] = {}
                tsc_input_hash = _compute_target_input_hash(
                    root,
                    "js-tsc",
                    spec,
                    toolchain,
                    digest_cache=tsc_digest_cache,
                )
                if not force_rebuild and is_binding_cache_valid(
                    root,
                    "js-tsc",
                    expected_profile=spec.name,
                    expected_input_hash=tsc_input_hash,
                    digest_cache=tsc_digest_cache,
                ):
                    with _PRINT_LOCK:
                        print(f"sync-bindings ({spec.name}): reusing verified cached js-tsc", flush=True)
                else:
                    _invalidate_stamp(root, "js-tsc")
                    dist_dir = root / "bindings/js-wasm/dist"
                    if dist_dir.is_dir():
                        shutil.rmtree(dist_dir)
                    run("pnpm", "--filter", "tamil-toolkit", "build", cwd=root)
                    _write_binding_stamp(root, "js-tsc", profile=spec.name, input_hash=tsc_input_hash)


def parity_runners(profile=None):
    spec = resolve_lexicon_profile(profile)
    with canonical_output_lease(ROOT, profile=spec.name, targets=("parity",)):
        verify_canonical_lease(ROOT, expected_profile=spec.name)
        env = profile_env(spec, include_planned=bool(spec.planned_suites))
        if spec.planned_suites:
            print(
                f"PRE-ACTIVATION LEXICON PARITY ({spec.name}): executing planned suites "
                f"{','.join(spec.planned_suites)} against manifest {spec.manifest_sha256}; "
                "they are not active release coverage.",
                flush=True,
            )
        run(
            "cargo",
            "test",
            "--locked",
            "-p",
            "tamil-toolkit",
            *cargo_feature_args(spec),
            "--test",
            "golden_suite",
            "--",
            "--nocapture",
            extra_env=env,
        )
        run(sys.executable, "-m", "pytest", "bindings/python/tests/test_golden.py", "-q", extra_env=env)
        run("pnpm", "--filter", "tamil-toolkit", "test", extra_env=env)


def test_parity(profile=None, *, force_bindings: bool = False):
    spec = resolve_lexicon_profile(profile)
    check_unicode()
    with canonical_output_lease(ROOT, profile=spec.name, targets=("python", "wasm-node", "wasm-web", "parity")):
        sync_bindings(profile=spec.name, force=force_bindings)
        parity_runners(profile=spec.name)


def test_lexicon_parity(*, force_bindings: bool = False):
    check_unicode()
    with canonical_output_lease(ROOT, profile="core", targets=("python", "wasm-node", "wasm-web", "dart", "parity")):
        sync_bindings(profile="core", force=force_bindings, include_dart=True)
        parity_runners(profile="core")
        test_dart(profile="core", force=False)


def test_dart(profile=None, *, force: bool = False):
    spec = resolve_lexicon_profile(profile)
    env = profile_env(spec, include_planned=bool(spec.planned_suites))
    with canonical_output_lease(ROOT, profile=spec.name, targets=("dart",)):
        sync_bindings(profile=spec.name, force=force, targets=("dart",))
        verify_canonical_lease(ROOT, expected_profile=spec.name)
        run("dart", "pub", "get", "--enforce-lockfile", cwd=ROOT / "bindings/dart-flutter")
        run("dart", "analyze", cwd=ROOT / "bindings/dart-flutter")
        run("dart", "test", cwd=ROOT / "bindings/dart-flutter", extra_env=env)


def _resolve_harness_workers(workers: str | int | None = None) -> str | None:
    raw = os.environ.get("TAMIL_HARNESS_WORKERS") if workers is None else str(workers)
    if raw is None or not raw.strip():
        return "auto"
    token = raw.strip().lower()
    if token in {"auto", "logical"}:
        return token
    if token.isdigit():
        value = int(token)
        if value == 0:
            return None
        return str(value)
    raise ValueError(
        f"Harness workers must be 'auto', 'logical', '0', or a positive integer, got {raw!r}"
    )


def test_harness(*, workers: str | int | None = None):
    worker_spec = _resolve_harness_workers(workers)
    args = [sys.executable, "-m", "pytest", "tests/harness"]
    if worker_spec is not None:
        args.extend(["-n", worker_spec, "--dist=loadgroup"])
    args.append("-q")
    run(*args)


def post_edit(profile=None):
    spec = resolve_lexicon_profile(profile)
    run("cargo", "fmt", "--all", "--", "--check")
    check_unicode()
    run("cargo", "check", "--locked", "--workspace")
    if spec.features:
        run("cargo", "check", "--locked", "-p", "tamil-toolkit", *cargo_feature_args(spec))


def pre_stop(profile=None, *, force_bindings: bool = False, harness_workers: str | int | None = None):
    spec = resolve_lexicon_profile(profile)
    post_edit(profile=profile)
    run("cargo", "clippy", "--locked", "--workspace", "--all-targets", "--", "-D", "warnings")
    if spec.features:
        run(
            "cargo",
            "clippy",
            "--locked",
            "-p",
            "tamil-toolkit",
            *cargo_feature_args(spec),
            "--all-targets",
            "--",
            "-D",
            "warnings",
        )
    test_rust(profile=profile)
    test_harness(workers=harness_workers)
    with canonical_output_lease(ROOT, profile=spec.name, targets=("python", "wasm-node", "wasm-web", "parity")):
        sync_bindings(profile=spec.name, force=force_bindings)
        parity_runners(profile=spec.name)


def bootstrap():
    run("uv", "sync", "--locked")
    run("pnpm", "install", "--frozen-lockfile")
    run("rustup", "target", "add", "wasm32-unknown-unknown")
    sync_bindings()


def doctor():
    missing = []
    cargo_bin = Path.home() / ".cargo" / "bin"
    for tool in ["cargo", "rustup", "uv", "pnpm", "just", "dart", "cargo-nextest"]:
        found = shutil.which(tool)
        if not found and cargo_bin.exists():
            candidate = cargo_bin / (f"{tool}.exe" if sys.platform == "win32" else tool)
            if candidate.exists():
                found = str(candidate)
        print(f"{tool}: {found or 'MISSING'}")
        if not found and tool not in {"dart", "cargo-nextest"}:
            missing.append(tool)
    if missing:
        raise RuntimeError("Install or add to PATH: " + ", ".join(missing))


def release_test(profile=None, *, force: bool = True):
    spec = resolve_lexicon_profile(profile)
    with canonical_output_lease(
        ROOT,
        profile=spec.name,
        targets=("python", "wasm-node", "wasm-web", "dart", "parity", "release"),
    ):
        pre_stop(profile=spec.name, force_bindings=force)
        if shutil.which("dart"):
            test_dart(profile=spec.name, force=force)
        verify_canonical_lease(ROOT, expected_profile=spec.name)
        args = [sys.executable, "tools/release.py", "all"]
        if profile is not None:
            args.extend(["--lexicon-profile", profile])
        run(*args)


PROFILE_TASKS = {
    "test-rust",
    "sync-bindings",
    "test-parity",
    "test-dart",
    "agent-post-edit",
    "agent-pre-stop-gate",
    "release-test",
}


TASKS = {
    "bootstrap": bootstrap,
    "doctor": doctor,
    "check-unicode": check_unicode,
    "test-rust": test_rust,
    "sync-bindings": sync_bindings,
    "test-parity": test_parity,
    "test-lexicon-parity": test_lexicon_parity,
    "test-dart": test_dart,
    "test-harness": test_harness,
    "agent-post-edit": post_edit,
    "agent-pre-stop-gate": pre_stop,
    "release-test": release_test,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=TASKS)
    parser.add_argument(
        "--lexicon-profile",
        default=None,
        help="Optional lexicon compilation profile ('default', 'core', or 'full')",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild of selected bindings instead of reusing verified cached artifacts",
    )
    parser.add_argument(
        "--include-dart",
        action="store_true",
        help="Include optional Dart FFI library build during sync-bindings",
    )
    parser.add_argument(
        "--targets",
        default=None,
        help="Optional comma-separated sync-bindings targets (python,wasm-node,wasm-web,dart)",
    )
    parser.add_argument(
        "--workers",
        default=None,
        help="Optional pytest-xdist worker count for test-harness / agent-pre-stop-gate ('auto', '0', or N)",
    )
    args = parser.parse_args()
    try:
        if args.lexicon_profile is not None:
            resolve_lexicon_profile(args.lexicon_profile)
        parsed_targets = (
            [item.strip() for item in args.targets.split(",") if item.strip()]
            if args.targets is not None
            else None
        )
        if args.task == "sync-bindings":
            sync_bindings(
                profile=args.lexicon_profile,
                force=args.force,
                include_dart=args.include_dart,
                targets=parsed_targets,
            )
        elif args.task == "test-parity":
            test_parity(profile=args.lexicon_profile, force_bindings=args.force)
        elif args.task == "agent-pre-stop-gate":
            pre_stop(
                profile=args.lexicon_profile,
                force_bindings=args.force,
                harness_workers=args.workers,
            )
        elif args.task == "test-harness":
            test_harness(workers=args.workers)
        elif args.task == "test-dart":
            test_dart(profile=args.lexicon_profile, force=args.force)
        elif args.task == "test-lexicon-parity":
            test_lexicon_parity(force_bindings=args.force)
        elif args.task == "release-test":
            release_test(profile=args.lexicon_profile, force=True)
        elif args.task in PROFILE_TASKS and args.lexicon_profile is not None:
            TASKS[args.task](profile=args.lexicon_profile)
        else:
            TASKS[args.task]()
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
