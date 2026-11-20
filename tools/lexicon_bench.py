"""Independent Feature 021 lexicon benchmark runner (`T063`).

Measures:
1. ``structural``: fresh end-to-end ``inventory`` -> ``stage`` -> full-scope
   structural validation (CLDF/CSV schema, ``claim_revision_sha256``, projection
   invariants, disposition accounting, and source payload SHA-256 verification)
   across the full 12-file / 307,243-CSV-record Tamil Lexicon bundle using
   isolated scratch directories and existing host tools.
2. ``lookup``: warm 10,000-query throughput/latency, JSON serialization & full
   untruncated response byte sizes, default vs selected pack sizes, and
   separate fresh-process cold-start latency/RSS against the actual native
   Rust ``tamil_toolkit`` dispatcher after verifying ``PackInfo`` parity with
   ``lexicon/dictionary/packs.toml``.

Completed measurement vs performance budget pass/fail are strictly separated.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import csv
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import threading
import time
import tomllib
from typing import Any
import unicodedata
import uuid

import jsonschema
import psutil

from tools.lexicon import (
    MANIFEST,
    ROOT,
    SOURCE,
    LexiconError,
    atomic_json,
    digest,
    inventory as run_inventory_tool,
    json_text,
    safe_output,
    stage as run_stage_tool,
)
from tools.lexicon_proof import prove as run_prove_tool, verify_source_payloads
from tools.lexicon_validate import check_curated_csv

BENCH_SCHEMA_VERSION = 1
DEFAULT_OUTPUT = ROOT / "target" / "lexicon" / "benchmarks.json"
DEFAULT_SCRATCH_BASE = ROOT / "target" / "lexicon" / "bench-scratch"
CANONICAL_PACKS_TOML = ROOT / "lexicon" / "dictionary" / "packs.toml"
LOOKUP_RESPONSE_SCHEMA_PATH = (
    ROOT / "specs" / "021-lexicon-curation" / "contracts" / "lookup-response.schema.json"
)
L3_ACCEPTANCE_PATH = ROOT / "target" / "lexicon" / "l3-acceptance.json"

STRUCTURAL_WALL_BUDGET_S = 60.0
STRUCTURAL_RSS_BUDGET_BYTES = 512 * 1024 * 1024  # 512 MiB
LOOKUP_WARM_P95_BUDGET_MS = 10.0

CANONICAL_CSV_RECORDS = 307243
CANONICAL_SOURCE_FILES = 12
CANONICAL_CORE_PACK_ID = "core"
CANONICAL_PACK_MANIFEST_SHA256 = (
    "a211334e3659647deb4fc30a1c5c6778f4fa9ef98815ed44674a7d5d7dc05bdf"
)

DEFAULT_SAMPLING_INTERVAL_MS = 10.0
DEFAULT_WARM_QUERIES = 10000
DEFAULT_WARMUP_QUERIES = 500
DEFAULT_SEED = 20261114
MAX_LOOKUP_QUERY_UTF8_BYTES = 65536

PROTECTED_REPO_DIRS = (
    ROOT / "data",
    ROOT / "lexicon",
    ROOT / "crates",
    ROOT / "bindings",
    ROOT / "schemas",
    ROOT / "tests",
    ROOT / "tools",
    ROOT / "docs",
    ROOT / "specs",
)

STAGE_INVENTORY = "inventory"
STAGE_STAGE = "stage"
STAGE_VALIDATION = "structural_validation"


def _resolve_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _paths_overlap(a: Path, b: Path) -> bool:
    ra = _resolve_path(a)
    rb = _resolve_path(b)
    return ra == rb or ra.is_relative_to(rb) or rb.is_relative_to(ra)


def check_safe_bench_path(path: Path, *, label: str) -> Path:
    """Reject empty or repo-protected paths for benchmark scratch/output writes."""
    if not str(path).strip():
        raise LexiconError(f"{label} path must be non-empty", code=2)
    resolved = _resolve_path(path)
    if resolved == _resolve_path(ROOT):
        raise LexiconError(f"{label} cannot be the repository root: {resolved}", code=2)
    for protected in PROTECTED_REPO_DIRS:
        if _paths_overlap(resolved, protected):
            raise LexiconError(
                f"{label} cannot overlap protected repository directory {protected}: {resolved}",
                code=2,
            )
    return resolved


def check_safe_output_path(path: Path) -> Path:
    """Validate an output JSON path against repo-protected paths."""
    resolved = check_safe_bench_path(path, label="output")
    return safe_output(resolved, source_root=SOURCE)


def check_safe_scratch_dir(path: Path, *, source_root: Path) -> Path:
    """Validate a disposable scratch workspace path."""
    resolved = check_safe_bench_path(path, label="scratch_dir")
    if _paths_overlap(resolved, source_root):
        raise LexiconError(
            f"scratch_dir cannot overlap source_root ({source_root}): {resolved}",
            code=2,
        )
    return resolved


def read_process_tree_rss_bytes(root_pid: int) -> int:
    """Sum resident set size in bytes for ``root_pid`` and all live descendants."""
    try:
        root = psutil.Process(root_pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return 0

    total = 0
    processes: list[psutil.Process] = [root]
    try:
        processes.extend(root.children(recursive=True))
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

    seen_pids: set[int] = set()
    for proc in processes:
        if proc.pid in seen_pids:
            continue
        seen_pids.add(proc.pid)
        try:
            total += int(proc.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return total


class ProcessTreeMemorySampler:
    """Polls process-tree RSS bytes at a fixed interval on a background thread."""

    def __init__(
        self,
        root_pid: int,
        *,
        interval_ms: float = DEFAULT_SAMPLING_INTERVAL_MS,
        rss_reader: Callable[[int], int] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if interval_ms <= 0:
            raise LexiconError(f"sampling_interval_ms must be > 0, got {interval_ms}", code=2)
        self.root_pid = int(root_pid)
        self.interval_ms = float(interval_ms)
        self._interval_s = self.interval_ms / 1000.0
        self._rss_reader = rss_reader or read_process_tree_rss_bytes
        self._clock = clock or time.perf_counter
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._start_t: float | None = None
        self._end_t: float | None = None
        self.peak_rss_bytes = 0
        self.last_rss_bytes = 0
        self.sample_count = 0

    def sample_once(self) -> int:
        rss = int(self._rss_reader(self.root_pid))
        with self._lock:
            self.last_rss_bytes = rss
            if rss > self.peak_rss_bytes:
                self.peak_rss_bytes = rss
            self.sample_count += 1
        return rss

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval_s):
            self.sample_once()

    def start(self) -> None:
        self._start_t = self._clock()
        self.sample_once()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self._interval_s * 10))
        self.sample_once()
        self._end_t = self._clock()
        elapsed_s = 0.0 if self._start_t is None else max(0.0, self._end_t - self._start_t)
        return {
            "elapsed_s": elapsed_s,
            "peak_rss_bytes": self.peak_rss_bytes,
            "sample_count": self.sample_count,
            "sampling_interval_ms": self.interval_ms,
        }

    def __enter__(self) -> ProcessTreeMemorySampler:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.stop()


def _probe_command_version(argv: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    first = (completed.stdout or completed.stderr).strip().splitlines()
    return first[0].strip() if first else None


def collect_environment_metadata(*, sampling_interval_ms: float) -> dict[str, Any]:
    """Capture machine, OS, toolchain, and memory sampling metadata."""
    vm = psutil.virtual_memory()
    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "total_ram_bytes": int(vm.total),
        },
        "toolchain": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "python_executable": sys.executable,
            "psutil_version": psutil.__version__,
            "rustc_version": _probe_command_version(["rustc", "--version"]),
            "cargo_version": _probe_command_version(["cargo", "--version"]),
        },
        "measurement_method": {
            "clock": "time.perf_counter / time.perf_counter_ns (monotonic)",
            "memory": "psutil_process_tree_rss",
            "sampling_interval_ms": float(sampling_interval_ms),
            "includes_child_processes": True,
            "includes_native_allocations": True,
            "quantile_method": "nearest_rank",
        },
    }


def _nearest_rank(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    idx = min(n - 1, max(0, math.ceil(q * n) - 1))
    return float(sorted_values[idx])


def compute_latency_stats_ms(samples_ns: Sequence[int]) -> dict[str, Any]:
    """Summarize monotonic nanosecond latency samples in milliseconds."""
    if not samples_ns:
        raise LexiconError("cannot compute latency stats for empty sample list", code=2)
    sorted_ms = sorted(ns / 1_000_000.0 for ns in samples_ns)
    total_ms = sum(sorted_ms)
    count = len(sorted_ms)
    return {
        "count": count,
        "total_ms": round(total_ms, 6),
        "min_ms": round(sorted_ms[0], 6),
        "mean_ms": round(total_ms / count, 6),
        "p50_ms": round(_nearest_rank(sorted_ms, 0.50), 6),
        "p95_ms": round(_nearest_rank(sorted_ms, 0.95), 6),
        "p99_ms": round(_nearest_rank(sorted_ms, 0.99), 6),
        "max_ms": round(sorted_ms[-1], 6),
    }


def compute_byte_stats(sizes: Sequence[int]) -> dict[str, Any]:
    """Summarize serialized payload byte sizes."""
    if not sizes:
        raise LexiconError("cannot compute byte stats for empty sample list", code=2)
    ordered = sorted(int(s) for s in sizes)
    total = sum(ordered)
    count = len(ordered)
    return {
        "count": count,
        "total_bytes": total,
        "min_bytes": ordered[0],
        "mean_bytes": round(total / count, 2),
        "p50_bytes": int(_nearest_rank(ordered, 0.50)),
        "p95_bytes": int(_nearest_rank(ordered, 0.95)),
        "max_bytes": ordered[-1],
    }


def _inspect_source_identity(
    source_root: Path,
    manifest_path: Path | None,
) -> dict[str, Any]:
    resolved_source = _resolve_path(source_root)
    if not resolved_source.is_dir():
        raise LexiconError(f"source_root directory not found: {resolved_source}", code=2)
    resolved_manifest: Path | None = None
    manifest_sha256: str | None = None
    if manifest_path is not None:
        resolved_manifest = _resolve_path(manifest_path)
        if not resolved_manifest.is_file():
            raise LexiconError(f"manifest not found: {resolved_manifest}", code=2)
        manifest_sha256 = digest(resolved_manifest)
    files = sorted(p for p in resolved_source.rglob("*") if p.is_file())
    file_hashes = {
        p.relative_to(resolved_source).as_posix(): digest(p) for p in files
    }
    return {
        "source_root": str(resolved_source),
        "manifest_path": str(resolved_manifest) if resolved_manifest is not None else None,
        "manifest_sha256": manifest_sha256,
        "file_count": len(file_hashes),
        "files_sha256": file_hashes,
    }


def _verify_staged_full_scope_generic(
    *,
    source_root: Path,
    manifest_path: Path | None,
    inventory_path: Path,
    workspace: Path,
    proof_out: Path,
) -> dict[str, Any]:
    """Full-scope validation without pilot substitution, supporting non-canonical fixtures."""
    empty_canonical = workspace / "_empty_canonical_for_bench"
    empty_canonical.mkdir(parents=True, exist_ok=True)
    csv_report = check_curated_csv(workspace=workspace, canonical=empty_canonical)
    payload_report = verify_source_payloads(
        workspace=workspace,
        source=source_root,
        manifest_path=manifest_path,
    )
    inv_doc = json.loads((inventory_path / "manifest.json").read_text(encoding="utf-8"))
    stage_report = json.loads((workspace / "stage-report.json").read_text(encoding="utf-8"))
    source_csv_records = int(inv_doc.get("csv_records", -1))
    staged_counts = stage_report.get("counts", {})
    staged_source_records = int(staged_counts.get("source_records", -1))
    staged_dispositions = int(staged_counts.get("dispositions", -1))
    if source_csv_records != staged_source_records or staged_dispositions != source_csv_records:
        raise LexiconError(
            f"staged counts mismatch: source_records={staged_source_records}, "
            f"dispositions={staged_dispositions}, inventory csv_records={source_csv_records}",
            code=2,
        )
    non_csv_snaps = {
        item["snapshot_id"]
        for item in inv_doc.get("files", [])
        if not str(item.get("file", "")).endswith(".csv")
    }
    disp_snaps = {item["snapshot_id"] for item in stage_report.get("file_dispositions", [])}
    if non_csv_snaps != disp_snaps:
        raise LexiconError(
            "stage file_dispositions do not cover every non-CSV inventoried snapshot",
            code=2,
        )
    if csv_report.get("findings"):
        raise LexiconError(
            f"full-scope check_curated_csv reported findings: {csv_report['findings'][:3]}",
            code=1,
        )
    if not (
        payload_report.get("exact_decoded_source_fields_and_scalars") is True
        and payload_report.get("subject_ids_match_immutable_allocations") is True
        and int(payload_report.get("missing_or_duplicate_assertions", -1)) == 0
        and int(payload_report.get("source_records", -1)) == source_csv_records
        and int(payload_report.get("matching_raw_assertions", -1)) == source_csv_records
        and int(payload_report.get("source_hashes_verified", -1)) == len(inv_doc.get("files", []))
    ):
        raise LexiconError(f"verify_source_payloads failed accounting checks: {payload_report}", code=1)
    summary = {
        "schema_version": 1,
        "command": "generic-structural-proof",
        "csv_records_verified": source_csv_records,
        "source_files_verified": len(inv_doc.get("files", [])),
        "csv_check": csv_report,
        "source_payloads": payload_report,
        "staged_counts": staged_counts,
    }
    atomic_json(proof_out, summary, source_root=source_root)
    return summary


def _benchmark_csv_validation(workspace: Path, canonical: Path) -> dict:
    return check_curated_csv(workspace=workspace, canonical=canonical)


def _benchmark_intake_proof(workspace: Path, inventory: Path, output: Path) -> dict:
    return run_prove_tool(workspace, inventory, output, replay=False, verify_payloads=True)


def execute_structural_stage_worker(
    *,
    stage_name: str,
    source_root: Path,
    manifest_path: Path | None,
    inventory_path: Path,
    workspace: Path,
    proof_out: Path,
    allow_noncanonical_counts: bool,
) -> dict[str, Any]:
    """Execute one structural stage cleanly inside the current Python process."""
    if stage_name == STAGE_INVENTORY:
        doc = run_inventory_tool(
            source_root,
            inventory_path,
            manifest_path=manifest_path,
        )
        return {
            "stage": STAGE_INVENTORY,
            "file_count": len(doc.get("files", [])),
            "csv_records": int(doc.get("csv_records", 0)),
        }

    if stage_name == STAGE_STAGE:
        doc = run_stage_tool(inventory_path, workspace)
        return {
            "stage": STAGE_STAGE,
            "counts": doc.get("counts", {}),
            "file_dispositions_count": len(doc.get("file_dispositions", [])),
        }

    if stage_name == STAGE_VALIDATION:
        inv_doc = json.loads((inventory_path / "manifest.json").read_text(encoding="utf-8"))
        csv_records = int(inv_doc.get("csv_records", 0))
        source_files = len(inv_doc.get("files", []))
        is_canonical = (
            _resolve_path(source_root) == _resolve_path(SOURCE)
            and (manifest_path is None or _resolve_path(manifest_path) == _resolve_path(MANIFEST))
            and csv_records == CANONICAL_CSV_RECORDS
            and source_files == CANONICAL_SOURCE_FILES
        )
        if not allow_noncanonical_counts:
            if csv_records != CANONICAL_CSV_RECORDS or source_files != CANONICAL_SOURCE_FILES:
                raise LexiconError(
                    "full-scope structural benchmark requires canonical counts "
                    f"({CANONICAL_CSV_RECORDS} CSV records, {CANONICAL_SOURCE_FILES} source files), "
                    f"got {csv_records} CSV records and {source_files} source files; "
                    "pilot subsets are not permitted as full structural substitutes",
                    code=2,
                )
        if is_canonical:
            empty_canonical = workspace / "_empty_canonical_for_bench"
            empty_canonical.mkdir(parents=True, exist_ok=True)
            # Both passes read the completed immutable scratch workspace.
            # Spawn avoids forking native validators or the RSS sampler thread.
            with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn")) as pool:
                csv_future = pool.submit(_benchmark_csv_validation, workspace, empty_canonical)
                proof_future = pool.submit(_benchmark_intake_proof, workspace, inventory_path, proof_out)
                csv_report = csv_future.result()
                proof = proof_future.result()
            if csv_report.get("findings"):
                raise LexiconError(
                    f"full-scope check_curated_csv reported findings: {csv_report['findings'][:3]}",
                    code=1,
                )
            return {
                "stage": STAGE_VALIDATION,
                "canonical_proof_used": True,
                "csv_records_verified": csv_records,
                "source_files_verified": source_files,
                "csv_check_counts": csv_report.get("counts", {}),
                "proof_schema_version": proof.get("schema_version"),
            }

        generic = _verify_staged_full_scope_generic(
            source_root=source_root,
            manifest_path=manifest_path,
            inventory_path=inventory_path,
            workspace=workspace,
            proof_out=proof_out,
        )
        return {
            "stage": STAGE_VALIDATION,
            "canonical_proof_used": False,
            "csv_records_verified": generic["csv_records_verified"],
            "source_files_verified": generic["source_files_verified"],
            "csv_check_counts": generic["csv_check"].get("counts", {}),
            "staged_counts": generic["staged_counts"],
        }

    raise LexiconError(f"unknown internal structural stage: {stage_name}", code=2)


def _default_subprocess_stage_runner(
    *,
    stage_name: str,
    source_root: Path,
    manifest_path: Path | None,
    inventory_path: Path,
    workspace: Path,
    proof_out: Path,
    allow_noncanonical_counts: bool,
    sampling_interval_ms: float,
    stage_result_path: Path,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "tools.lexicon_bench",
        "--_internal-stage",
        stage_name,
        "--source-root",
        str(source_root),
        "--inventory-path",
        str(inventory_path),
        "--workspace",
        str(workspace),
        "--proof-out",
        str(proof_out),
        "--stage-result-out",
        str(stage_result_path),
    ]
    if manifest_path is not None:
        cmd.extend(["--manifest", str(manifest_path)])
    else:
        cmd.append("--no-manifest")
    if allow_noncanonical_counts:
        cmd.append("--allow-noncanonical-counts")

    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    sampler = ProcessTreeMemorySampler(proc.pid, interval_ms=sampling_interval_ms)
    sampler.start()
    try:
        stdout, stderr = proc.communicate()
    finally:
        metrics = sampler.stop()

    if proc.returncode != 0:
        detail = (stderr or stdout).strip()
        raise LexiconError(
            f"structural stage {stage_name!r} failed with exit {proc.returncode}: {detail}",
            code=2 if proc.returncode != 1 else 1,
        )
    if not stage_result_path.is_file():
        raise LexiconError(
            f"structural stage {stage_name!r} did not produce {stage_result_path}",
            code=2,
        )
    stage_doc = json.loads(stage_result_path.read_text(encoding="utf-8"))
    self_peak = int(stage_doc.pop("self_rss_bytes", 0))
    metrics["peak_rss_bytes"] = max(int(metrics["peak_rss_bytes"]), self_peak)
    return {**metrics, "details": stage_doc}


def run_structural_benchmark(
    *,
    source_root: Path = SOURCE,
    manifest_path: Path | None = MANIFEST,
    scratch_base: Path = DEFAULT_SCRATCH_BASE,
    sampling_interval_ms: float = DEFAULT_SAMPLING_INTERVAL_MS,
    allow_noncanonical_counts: bool = False,
    keep_scratch: bool = False,
    stage_runner: Callable[..., dict[str, Any]] | None = None,
    wall_budget_s: float | None = None,
    rss_budget_bytes: int | None = None,
) -> dict[str, Any]:
    """Run fresh inventory -> stage -> full-scope validation and measure wall + RSS."""
    eff_wall_budget_s = STRUCTURAL_WALL_BUDGET_S if wall_budget_s is None else float(wall_budget_s)
    eff_rss_budget_bytes = (
        STRUCTURAL_RSS_BUDGET_BYTES if rss_budget_bytes is None else int(rss_budget_bytes)
    )
    safe_scratch_base = check_safe_scratch_dir(scratch_base, source_root=source_root)
    input_identity = _inspect_source_identity(source_root, manifest_path)

    run_dir = safe_scratch_base / f"run-{uuid.uuid4().hex[:12]}"
    inventory_path = run_dir / "inventory"
    workspace = run_dir / "curation"
    proof_out = run_dir / "l2-proof.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    runner = stage_runner or _default_subprocess_stage_runner
    stages: dict[str, dict[str, Any]] = {}
    t_total_start = time.perf_counter()
    try:
        for stage_name in (STAGE_INVENTORY, STAGE_STAGE, STAGE_VALIDATION):
            stage_result_path = run_dir / f"stage-{stage_name}.json"
            stage_metrics = runner(
                stage_name=stage_name,
                source_root=_resolve_path(source_root),
                manifest_path=_resolve_path(manifest_path) if manifest_path is not None else None,
                inventory_path=inventory_path,
                workspace=workspace,
                proof_out=proof_out,
                allow_noncanonical_counts=allow_noncanonical_counts,
                sampling_interval_ms=sampling_interval_ms,
                stage_result_path=stage_result_path,
            )
            stages[stage_name] = stage_metrics
        total_wall_s = max(0.0, time.perf_counter() - t_total_start)
    finally:
        if not keep_scratch:
            shutil.rmtree(run_dir, ignore_errors=True)

    inv_details = stages[STAGE_INVENTORY]["details"]
    csv_records = int(inv_details["csv_records"])
    source_file_count = int(inv_details["file_count"])
    full_corpus_verified = (
        csv_records == CANONICAL_CSV_RECORDS
        and source_file_count == CANONICAL_SOURCE_FILES
        and _resolve_path(source_root) == _resolve_path(SOURCE)
    )
    peak_rss_bytes = max(int(s["peak_rss_bytes"]) for s in stages.values())
    total_samples = sum(int(s["sample_count"]) for s in stages.values())
    sum_stage_wall_s = sum(float(s["elapsed_s"]) for s in stages.values())

    wall_budget_met = total_wall_s < eff_wall_budget_s
    rss_budget_met = peak_rss_bytes <= eff_rss_budget_bytes
    budget_met = wall_budget_met and rss_budget_met

    return {
        "workload": "structural",
        "measurement_completed": True,
        "full_corpus_verified": full_corpus_verified,
        "canonical_counts_enforced": not allow_noncanonical_counts,
        "pilot_substituted": False,
        "budgets": {
            "max_wall_seconds": eff_wall_budget_s,
            "max_rss_bytes": eff_rss_budget_bytes,
            "max_rss_mib": round(eff_rss_budget_bytes / (1024 * 1024), 2),
        },
        "wall_budget_met": wall_budget_met,
        "rss_budget_met": rss_budget_met,
        "budget_met": budget_met,
        "input_identity": {
            **input_identity,
            "csv_records": csv_records,
        },
        "stages": {
            name: {
                "elapsed_s": round(float(data["elapsed_s"]), 6),
                "peak_rss_bytes": int(data["peak_rss_bytes"]),
                "peak_rss_mib": round(int(data["peak_rss_bytes"]) / (1024 * 1024), 2),
                "sample_count": int(data["sample_count"]),
                "sampling_interval_ms": float(data["sampling_interval_ms"]),
                "details": data["details"],
            }
            for name, data in stages.items()
        },
        "end_to_end": {
            "elapsed_s": round(total_wall_s, 6),
            "sum_of_stage_wall_s": round(sum_stage_wall_s, 6),
            "peak_rss_bytes": peak_rss_bytes,
            "peak_rss_mib": round(peak_rss_bytes / (1024 * 1024), 2),
            "sample_count": total_samples,
            "sampling_interval_ms": float(sampling_interval_ms),
        },
    }


def load_canonical_core_pack_spec(
    packs_toml_path: Path = CANONICAL_PACKS_TOML,
) -> dict[str, Any]:
    """Load canonical core pack metadata and CSV entries/senses from ``lexicon/dictionary``."""
    resolved_toml = _resolve_path(packs_toml_path)
    if not resolved_toml.is_file():
        raise LexiconError(f"canonical packs.toml not found: {resolved_toml}", code=2)
    doc = tomllib.loads(resolved_toml.read_text(encoding="utf-8"))
    pack_dir = resolved_toml.parent
    files = doc.get("files", [])
    canonical_csv_bytes = sum(int(item["bytes"]) for item in files)

    entries_path = pack_dir / "entries.csv"
    forms_path = pack_dir / "forms.csv"
    assertions_path = pack_dir / "assertions.csv"
    senses_path = pack_dir / "senses.csv"

    headwords_by_assertion: dict[str, str] = {}
    with assertions_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["subject_kind"] == "form" and row["property_code"] == "headword":
                headwords_by_assertion[row["assertion_id"]] = json.loads(row["value_json"])

    form_headword_by_id: dict[str, str] = {}
    with forms_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["representation"] == "written" and row["role"] == "canonical":
                hw = headwords_by_assertion.get(row["text_assertion_id"])
                if hw is not None:
                    form_headword_by_id[row["form_id"]] = hw

    senses_per_entry: dict[str, int] = {}
    with senses_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            eid = row["entry_id"]
            senses_per_entry[eid] = senses_per_entry.get(eid, 0) + 1

    headword_specs: dict[str, dict[str, Any]] = {}
    with entries_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            eid = row["entry_id"]
            cfid = row["canonical_form_id"]
            hw = form_headword_by_id.get(cfid)
            if hw is None:
                raise LexiconError(f"missing canonical headword for entry {eid}", code=2)
            spec = headword_specs.setdefault(
                hw,
                {
                    "headword": hw,
                    "entry_ids": [],
                    "sense_count": 0,
                },
            )
            spec["entry_ids"].append(eid)
            spec["sense_count"] += senses_per_entry.get(eid, 0)

    specs_list = sorted(headword_specs.values(), key=lambda item: item["headword"])
    total_entries = sum(len(item["entry_ids"]) for item in specs_list)
    total_senses = sum(int(item["sense_count"]) for item in specs_list)
    if total_entries != int(doc["entry_count"]) or total_senses != int(doc["sense_count"]):
        raise LexiconError(
            "canonical CSV counts disagree with packs.toml: "
            f"entries {total_entries} != {doc['entry_count']}, "
            f"senses {total_senses} != {doc['sense_count']}",
            code=2,
        )

    return {
        "packs_toml_path": str(resolved_toml),
        "packs_toml_sha256": digest(resolved_toml),
        "pack_id": doc["pack_id"],
        "dataset_version": doc["dataset_version"],
        "schema_version": int(doc["schema_version"]),
        "index_format_version": int(doc["index_format_version"]),
        "manifest_sha256": doc["manifest_sha256"],
        "entry_count": int(doc["entry_count"]),
        "sense_count": int(doc["sense_count"]),
        "coverage": doc["coverage"],
        "canonical_csv_bytes": canonical_csv_bytes,
        "headword_specs": specs_list,
    }


def _discover_pack_byte_measurements(canonical_spec: dict[str, Any]) -> dict[str, Any]:
    """Report actual default (0 B), canonical CSV, and built compiled `.tlpack` sizes."""
    compiled_artifacts = sorted(
        (ROOT / "target").glob("*/build/tamil-toolkit-*/out/pack_core.tlpack"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    compiled_core: dict[str, Any] | None = None
    if compiled_artifacts:
        latest = compiled_artifacts[0]
        compiled_core = {
            "path": str(latest),
            "bytes": int(latest.stat().st_size),
            "sha256": digest(latest),
        }

    acceptance_proof: dict[str, Any] | None = None
    if L3_ACCEPTANCE_PATH.is_file():
        acc = json.loads(L3_ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        cp = acc.get("compiler_proof")
        if isinstance(cp, dict):
            acceptance_proof = {
                "path": str(L3_ACCEPTANCE_PATH),
                "core_artifact_bytes": cp.get("core_artifact_bytes"),
                "core_artifact_sha256": cp.get("core_artifact_sha256"),
                "default_payload_bytes": cp.get("default_payload_bytes"),
                "canonical_manifest_sha256": cp.get("canonical_manifest_sha256"),
            }

    return {
        "default_build_payload_bytes": 0,
        "canonical_csv_bytes": int(canonical_spec["canonical_csv_bytes"]),
        "compiled_core_pack": compiled_core,
        "l3_acceptance_compiler_proof": acceptance_proof,
    }


def load_native_dispatcher() -> tuple[Callable[[str], str], Callable[[dict[str, Any]], Any]]:
    """Import the real PyO3 native adapter and fail closed if missing."""
    try:
        import tamil_toolkit  # type: ignore[import-not-found]
        from tamil_toolkit import _native  # type: ignore[import-not-found]
    except Exception as exc:
        raise LexiconError(
            f"failed to import tamil_toolkit native runtime adapter: {exc}",
            code=2,
        ) from exc
    if not hasattr(_native, "execute") or not hasattr(tamil_toolkit, "execute"):
        raise LexiconError(
            "tamil_toolkit native adapter is missing execute/_native.execute",
            code=2,
        )
    return _native.execute, tamil_toolkit.execute


def _inspect_native_module_artifact() -> dict[str, Any] | None:
    """Record path, byte size, and sha256 of the loaded PyO3 `_native` extension."""
    mod = sys.modules.get("tamil_toolkit._native")
    raw_file = getattr(mod, "__file__", None) if mod is not None else None
    if not raw_file:
        return None
    path = Path(raw_file).resolve(strict=False)
    if not path.is_file():
        return {"path": str(path), "exists": False}
    return {
        "path": str(path),
        "bytes": int(path.stat().st_size),
        "sha256": digest(path),
    }


def verify_runtime_core_pack(
    execute_dict_fn: Callable[[dict[str, Any]], Any],
    canonical_spec: dict[str, Any],
) -> dict[str, Any]:
    """Fail closed if native runtime lacks lexicon_packs, pack data, or manifest parity."""
    try:
        response = execute_dict_fn({"op": "lexicon_packs", "input": None})
    except Exception as exc:
        raise LexiconError(
            f"native runtime rejected lexicon_packs (old binding or runtime error): {exc}",
            code=2,
        ) from exc

    if not isinstance(response, list):
        raise LexiconError(
            f"lexicon_packs returned non-array response: {type(response).__name__}",
            code=2,
        )
    packs = response
    if not packs:
        raise LexiconError(
            "native runtime has no compiled lexicon packs (no-data build cannot benchmark lookup)",
            code=2,
        )
    core_pack = next((p for p in packs if isinstance(p, dict) and p.get("id") == CANONICAL_CORE_PACK_ID), None)
    if core_pack is None:
        raise LexiconError(
            f"native runtime lexicon_packs missing required {CANONICAL_CORE_PACK_ID!r} pack",
            code=2,
        )
    if core_pack.get("available") is not True:
        raise LexiconError(
            f"native runtime {CANONICAL_CORE_PACK_ID!r} pack is not available: {core_pack}",
            code=2,
        )

    mismatches: list[str] = []
    for field in ("dataset_version", "schema_version", "index_format_version", "manifest_sha256", "coverage"):
        if core_pack.get(field) != canonical_spec.get(field):
            mismatches.append(
                f"{field}: runtime={core_pack.get(field)!r} != canonical={canonical_spec.get(field)!r}"
            )
    if mismatches:
        raise LexiconError(
            "native runtime core PackInfo mismatch vs lexicon/dictionary/packs.toml: "
            + "; ".join(mismatches),
            code=2,
        )
    return core_pack


def build_lookup_queries(
    headword_specs: Sequence[dict[str, Any]],
    *,
    count: int = DEFAULT_WARM_QUERIES,
    seed: int = DEFAULT_SEED,
) -> tuple[list[dict[str, Any]], str]:
    """Generate a reproducible seeded query mix honoring the 65,536-byte input cap."""
    if count <= 0:
        raise LexiconError(f"query count must be > 0, got {count}", code=2)
    if not headword_specs:
        raise LexiconError("headword_specs cannot be empty", code=2)

    rng = random.Random(seed)
    spec_by_hw = {item["headword"]: item for item in headword_specs}
    approved = [item["headword"] for item in headword_specs]
    multi_sense = max(headword_specs, key=lambda item: int(item["sense_count"]))["headword"]
    homograph = max(headword_specs, key=lambda item: len(item["entry_ids"]))["headword"]

    nonexistent_tam = [
        "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0b87\u0bb2\u0bcd\u0bb2\u0bc8",  # தமிழ்இல்லை
        "\u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd\u0bb2\u0bbe\u0b95\u0bcd\u0b95\u0bae\u0bcd",
        "\u0b85\u0bb1\u0bbf\u0bb5\u0bbf\u0baf\u0bb2\u0bcd",
        "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd",
        "   \u0ba8\u0ba9\u0bcd\u0bb1\u0bbf" + chr(0x200C) + "   ",  # preserved ZWNJ miss
        "",
        "   ",
    ]
    nonexistent_tam.extend(f"  {headword}  " for headword in approved)
    # A word absent from the bootstrap pack may exist after expansion. Never
    # label an actual canonical key as a negative benchmark expectation.
    nonexistent_tam = [q for q in nonexistent_tam if unicodedata.normalize("NFC", q) not in spec_by_hw]
    # Exact 65,536-byte UTF-8 boundary query (single ASCII repeats padded with Tamil miss prefix)
    prefix = "\u0b85\u0bb1\u0bbf\u0bb5\u0bc1"  # அறிவு (15 bytes UTF-8)
    boundary_65536 = prefix + ("a" * (MAX_LOOKUP_QUERY_UTF8_BYTES - len(prefix.encode("utf-8"))))
    assert len(boundary_65536.encode("utf-8")) == MAX_LOOKUP_QUERY_UTF8_BYTES

    anchor_cases: list[dict[str, Any]] = []
    # Bound anchor coverage so large packs still exercise a seeded mix of hits,
    # misses and boundary requests. Always include the largest sense/homograph
    # cases; the rest are sampled from the entire pack without truncating data.
    anchor_limit = min(len(approved), max(2, count // 8), 128)
    anchor_words = list(dict.fromkeys([multi_sense, homograph]))
    remaining_words = [hw for hw in approved if hw not in anchor_words]
    anchor_words.extend(rng.sample(remaining_words, max(0, anchor_limit - len(anchor_words))))
    for hw in anchor_words:
        spec = spec_by_hw[hw]
        anchor_cases.append(
            {
                "kind": "matched_canonical",
                "input": hw,
                "packs": ["core"],
                "expected_status": "matched",
                "expected_canonical": unicodedata.normalize("NFC", hw),
                "expected_entries": len(spec["entry_ids"]),
                "expected_senses": int(spec["sense_count"]),
            }
        )
        nfd = unicodedata.normalize("NFD", hw)
        anchor_cases.append(
            {
                "kind": "matched_nfd",
                "input": nfd,
                "packs": None,  # default packs resolution
                "expected_status": "matched",
                "expected_canonical": unicodedata.normalize("NFC", hw),
                "expected_entries": len(spec["entry_ids"]),
                "expected_senses": int(spec["sense_count"]),
            }
        )
    anchor_cases.append(
        {
            "kind": "not_found_max_65536_bytes",
            "input": boundary_65536,
            "packs": ["core"],
            "expected_status": "not_found",
            "expected_canonical": boundary_65536,
            "expected_entries": 0,
            "expected_senses": 0,
        }
    )

    # Reserve negative anchors before the matched anchors, so bounded runs do
    # not accidentally claim negative-input coverage from random chance.
    anchor_cases.insert(0, anchor_cases.pop())
    for q in (nonexistent_tam[0], f"  {multi_sense}  "):
        if unicodedata.normalize("NFC", q) not in spec_by_hw:
            anchor_cases.insert(1, {"kind": "not_found", "input": q, "packs": ["core"],
                                    "expected_status": "not_found", "expected_canonical": unicodedata.normalize("NFC", q),
                                    "expected_entries": 0, "expected_senses": 0})
    queries: list[dict[str, Any]] = list(anchor_cases[:count])
    while len(queries) < count:
        roll = rng.random()
        if roll < 0.55:
            if rng.random() < 0.45:
                hw = multi_sense if rng.random() < 0.5 else homograph
            else:
                hw = rng.choice(approved)
            spec = spec_by_hw[hw]
            queries.append(
                {
                    "kind": "matched_canonical",
                    "input": hw,
                    "packs": ["core"] if rng.random() < 0.5 else None,
                    "expected_status": "matched",
                    "expected_canonical": hw,
                    "expected_entries": len(spec["entry_ids"]),
                    "expected_senses": int(spec["sense_count"]),
                }
            )
        elif roll < 0.75:
            hw = rng.choice(approved)
            spec = spec_by_hw[hw]
            nfd = unicodedata.normalize("NFD", hw)
            queries.append(
                {
                    "kind": "matched_nfd",
                    "input": nfd,
                    "packs": ["core"],
                    "expected_status": "matched",
                    "expected_canonical": hw,
                    "expected_entries": len(spec["entry_ids"]),
                    "expected_senses": int(spec["sense_count"]),
                }
            )
        else:
            q = rng.choice(nonexistent_tam)
            queries.append(
                {
                    "kind": "not_found",
                    "input": q,
                    "packs": ["core"],
                    "expected_status": "not_found",
                    "expected_canonical": unicodedata.normalize("NFC", q),
                    "expected_entries": 0,
                    "expected_senses": 0,
                }
            )

    rng.shuffle(queries)
    hasher = hashlib.sha256()
    for item in queries:
        hasher.update(
            json_text(
                {
                    "input": item["input"],
                    "packs": item["packs"],
                    "kind": item["kind"],
                }
            ).encode("utf-8")
        )
        hasher.update(b"\n")
    return queries, hasher.hexdigest()


def _make_lookup_request(query_spec: dict[str, Any]) -> dict[str, Any]:
    req: dict[str, Any] = {"op": "lexicon_lookup", "input": query_spec["input"]}
    if query_spec["packs"] is not None:
        req["packs"] = query_spec["packs"]
    return req


def _verify_untruncated_lookup_response(
    response: Any,
    *,
    query_spec: dict[str, Any],
    expected_manifest_sha256: str,
) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise LexiconError(
            f"lookup returned non-object payload: {type(response).__name__}",
            code=2,
        )
    if response.get("schema_version") != 1:
        raise LexiconError(
            f"unexpected lookup schema_version: {response.get('schema_version')!r}",
            code=2,
        )
    status = response.get("status")
    if status != query_spec["expected_status"]:
        raise LexiconError(
            f"lookup status mismatch for kind={query_spec['kind']}: "
            f"got {status!r}, expected {query_spec['expected_status']!r}",
            code=2,
        )
    if response.get("canonical_query") != query_spec["expected_canonical"]:
        raise LexiconError(
            f"canonical_query mismatch for kind={query_spec['kind']}",
            code=2,
        )
    packs = response.get("packs")
    if not isinstance(packs, list) or not packs:
        raise LexiconError("lookup response missing packs metadata", code=2)
    core_pack = next(
        (p for p in packs if isinstance(p, dict) and p.get("id") == CANONICAL_CORE_PACK_ID),
        None,
    )
    if core_pack is None or core_pack.get("manifest_sha256") != expected_manifest_sha256:
        got_manifest = core_pack.get("manifest_sha256") if core_pack else None
        raise LexiconError(
            f"lookup response manifest mismatch: {got_manifest!r} != {expected_manifest_sha256!r}",
            code=2,
        )
    entries = response.get("entries")
    if not isinstance(entries, list):
        raise LexiconError("lookup response entries must be a list", code=2)
    if len(entries) != int(query_spec["expected_entries"]):
        raise LexiconError(
            f"entry count mismatch for kind={query_spec['kind']}: "
            f"got {len(entries)}, expected {query_spec['expected_entries']}",
            code=2,
        )
    sense_count = sum(len(entry.get("senses", [])) for entry in entries)
    if sense_count != int(query_spec["expected_senses"]):
        raise LexiconError(
            f"sense count mismatch for kind={query_spec['kind']}: "
            f"got {sense_count}, expected {query_spec['expected_senses']}",
            code=2,
        )
    for entry in entries:
        if not entry.get("forms") or not entry.get("senses"):
            raise LexiconError(
                f"lookup entry {entry.get('entry_id')!r} appears truncated (missing forms/senses)",
                code=2,
            )
    return {
        "status": status,
        "entry_count": len(entries),
        "sense_count": sense_count,
    }


def _default_cold_start_runner(
    *,
    query: str,
    expected_manifest_sha256: str,
    sampling_interval_ms: float,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "tools.lexicon_bench",
        "--_internal-cold-start",
        "--query",
        query,
        "--expected-manifest",
        expected_manifest_sha256,
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    sampler = ProcessTreeMemorySampler(proc.pid, interval_ms=sampling_interval_ms)
    sampler.start()
    try:
        stdout, stderr = proc.communicate(timeout=30.0)
    finally:
        metrics = sampler.stop()

    if proc.returncode != 0:
        detail = (stderr or stdout).strip()
        raise LexiconError(
            f"cold-start lookup subprocess failed with exit {proc.returncode}: {detail}",
            code=2,
        )
    child = json.loads(stdout)
    child_self_rss = int(child.get("self_rss_bytes", 0))
    peak_rss_bytes = max(int(metrics["peak_rss_bytes"]), child_self_rss)
    return {
        "total_process_wall_ms": round(float(metrics["elapsed_s"]) * 1000.0, 6),
        "import_ms": float(child["import_ms"]),
        "first_lookup_ms": float(child["first_lookup_ms"]),
        "child_total_ms": float(child["child_total_ms"]),
        "peak_rss_bytes": peak_rss_bytes,
        "peak_rss_mib": round(peak_rss_bytes / (1024 * 1024), 2),
        "sample_count": int(metrics["sample_count"]),
        "sampling_interval_ms": float(metrics["sampling_interval_ms"]),
        "response_utf8_bytes": int(child["response_utf8_bytes"]),
        "status": child["status"],
        "entry_count": int(child["entry_count"]),
        "sense_count": int(child["sense_count"]),
    }


def _execute_cold_start_worker(*, query: str, expected_manifest: str) -> dict[str, Any]:
    t0 = time.perf_counter_ns()
    execute_native, _ = load_native_dispatcher()
    t_import = time.perf_counter_ns()
    req_json = json.dumps({"op": "lexicon_lookup", "input": query, "packs": ["core"]}, ensure_ascii=True)
    res_json = execute_native(req_json)
    t_lookup = time.perf_counter_ns()
    response = json.loads(res_json)
    packs = response.get("packs") or []
    core_pack = next(
        (p for p in packs if isinstance(p, dict) and p.get("id") == CANONICAL_CORE_PACK_ID),
        None,
    )
    if core_pack is None or core_pack.get("manifest_sha256") != expected_manifest:
        got_manifest = core_pack.get("manifest_sha256") if core_pack else None
        raise LexiconError(
            f"cold-start lookup manifest mismatch: {got_manifest!r} != {expected_manifest!r}",
            code=2,
        )
    if response.get("status") != "matched" or not response.get("entries"):
        raise LexiconError(
            f"cold-start lookup expected matched entry for {query!r}, got {response.get('status')!r}",
            code=2,
        )
    entries = response["entries"]
    sense_count = sum(len(entry.get("senses", [])) for entry in entries)
    self_rss = int(psutil.Process().memory_info().rss)
    return {
        "import_ms": round((t_import - t0) / 1_000_000.0, 6),
        "first_lookup_ms": round((t_lookup - t_import) / 1_000_000.0, 6),
        "child_total_ms": round((t_lookup - t0) / 1_000_000.0, 6),
        "self_rss_bytes": self_rss,
        "response_utf8_bytes": len(res_json.encode("utf-8")),
        "status": response["status"],
        "entry_count": len(entries),
        "sense_count": sense_count,
    }


def _validate_responses_against_schema(
    sample_responses: dict[str, dict[str, Any]],
    *,
    schema_path: Path = LOOKUP_RESPONSE_SCHEMA_PATH,
) -> int:
    resolved = _resolve_path(schema_path)
    schema = json.loads(resolved.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for key, doc in sample_responses.items():
        errors = sorted(validator.iter_errors(doc), key=lambda err: list(err.path))
        if errors:
            raise LexiconError(
                f"lookup response failed schema validation ({key}): {errors[0].message}",
                code=2,
            )
    return len(sample_responses)


def run_lookup_benchmark(
    *,
    queries: int = DEFAULT_WARM_QUERIES,
    warmup: int = DEFAULT_WARMUP_QUERIES,
    seed: int = DEFAULT_SEED,
    sampling_interval_ms: float = DEFAULT_SAMPLING_INTERVAL_MS,
    packs_toml_path: Path = CANONICAL_PACKS_TOML,
    dispatcher_loader: Callable[
        [], tuple[Callable[[str], str], Callable[[dict[str, Any]], Any]]
    ]
    | None = None,
    cold_start_runner: Callable[..., dict[str, Any]] | None = None,
    warm_p95_budget_ms: float | None = None,
    runtime_mode_label: str = "native_rust",
) -> dict[str, Any]:
    """Verify native runtime + PackInfo, benchmark warm 10k queries & cold start."""
    eff_warm_p95_budget_ms = (
        LOOKUP_WARM_P95_BUDGET_MS if warm_p95_budget_ms is None else float(warm_p95_budget_ms)
    )
    canonical_spec = load_canonical_core_pack_spec(packs_toml_path)
    pack_bytes = _discover_pack_byte_measurements(canonical_spec)

    loader = dispatcher_loader or load_native_dispatcher
    execute_native_json, execute_dict = loader()
    native_binary = _inspect_native_module_artifact() if dispatcher_loader is None else None
    verified_pack = verify_runtime_core_pack(execute_dict, canonical_spec)

    query_plan, corpus_sha256 = build_lookup_queries(
        canonical_spec["headword_specs"],
        count=queries,
        seed=seed,
    )
    requests_dict = [_make_lookup_request(item) for item in query_plan]
    requests_json = [json.dumps(req, ensure_ascii=True) for req in requests_dict]
    request_byte_sizes = [len(raw.encode("utf-8")) for raw in requests_json]

    warmup_count = min(max(0, warmup), len(requests_json))
    for i in range(warmup_count):
        _ = execute_native_json(requests_json[i])

    # Pass A: native JSON dispatch (caller holds JSON string; isolates Rust dispatch + JSON parse/emit)
    native_samples_ns: list[int] = []
    native_response_bytes: list[int] = []
    native_sampler = ProcessTreeMemorySampler(os.getpid(), interval_ms=sampling_interval_ms)
    native_sampler.start()
    try:
        for req_str in requests_json:
            t0 = time.perf_counter_ns()
            res_str = execute_native_json(req_str)
            t1 = time.perf_counter_ns()
            native_samples_ns.append(t1 - t0)
            native_response_bytes.append(len(res_str.encode("utf-8")))
    finally:
        native_mem = native_sampler.stop()

    # Pass B: end-to-end Python->JSON->Rust->JSON->Python serialization + untruncated verification
    serialized_samples_ns: list[int] = []
    serialized_response_bytes: list[int] = []
    unique_responses_to_validate: dict[str, dict[str, Any]] = {}
    matched_queries = 0
    not_found_queries = 0
    largest_response_info = {"bytes": 0, "kind": "", "input_preview": "", "entry_count": 0, "sense_count": 0}

    ser_sampler = ProcessTreeMemorySampler(os.getpid(), interval_ms=sampling_interval_ms)
    ser_sampler.start()
    try:
        for spec, req_dict in zip(query_plan, requests_dict, strict=True):
            t0 = time.perf_counter_ns()
            res_obj = execute_dict(req_dict)
            t1 = time.perf_counter_ns()
            serialized_samples_ns.append(t1 - t0)
            res_bytes = len(json.dumps(res_obj, ensure_ascii=False).encode("utf-8"))
            serialized_response_bytes.append(res_bytes)

            check = _verify_untruncated_lookup_response(
                res_obj,
                query_spec=spec,
                expected_manifest_sha256=canonical_spec["manifest_sha256"],
            )
            if check["status"] == "matched":
                matched_queries += 1
            else:
                not_found_queries += 1
            if res_bytes > largest_response_info["bytes"]:
                largest_response_info = {
                    "bytes": res_bytes,
                    "kind": spec["kind"],
                    "input_preview": spec["input"][:64],
                    "entry_count": check["entry_count"],
                    "sense_count": check["sense_count"],
                }
            sig = f"{spec['kind']}::{spec['expected_canonical'][:32]}"
            if sig not in unique_responses_to_validate:
                unique_responses_to_validate[sig] = res_obj
    finally:
        ser_mem = ser_sampler.stop()

    schema_validated_count = _validate_responses_against_schema(unique_responses_to_validate)

    # Cold start: pick the richest multi-sense headword so first lookup returns full entry payload
    cold_headword = max(
        canonical_spec["headword_specs"],
        key=lambda item: int(item["sense_count"]),
    )["headword"]
    cs_runner = cold_start_runner or _default_cold_start_runner
    cold_start_metrics = cs_runner(
        query=cold_headword,
        expected_manifest_sha256=canonical_spec["manifest_sha256"],
        sampling_interval_ms=sampling_interval_ms,
    )

    native_latency = compute_latency_stats_ms(native_samples_ns)
    serialized_latency = compute_latency_stats_ms(serialized_samples_ns)

    native_total_s = max(1e-9, sum(native_samples_ns) / 1_000_000_000.0)
    serialized_total_s = max(1e-9, sum(serialized_samples_ns) / 1_000_000_000.0)

    warm_p95_budget_met = (
        native_latency["p95_ms"] < eff_warm_p95_budget_ms
        and serialized_latency["p95_ms"] < eff_warm_p95_budget_ms
    )

    return {
        "workload": "lookup",
        "measurement_completed": True,
        "runtime_mode": runtime_mode_label,
        "native_binary": native_binary,
        "corpus_coverage_note": (
            f"Benchmarked against the reviewed core pack ({canonical_spec['entry_count']} entries, "
            f"{canonical_spec['sense_count']} senses, manifest {canonical_spec['manifest_sha256']}). "
            "Reproducible seeded warm queries measure runtime dispatch and serialization on core; "
            "they do not claim ~263k/307k large-corpus lookup coverage or scale."
        ),
        "budgets": {
            "warm_p95_max_ms": eff_warm_p95_budget_ms,
        },
        "warm_p95_budget_met": warm_p95_budget_met,
        "budget_met": warm_p95_budget_met,
        "pack_info": {
            "canonical_spec": {
                "packs_toml_path": canonical_spec["packs_toml_path"],
                "packs_toml_sha256": canonical_spec["packs_toml_sha256"],
                "pack_id": canonical_spec["pack_id"],
                "dataset_version": canonical_spec["dataset_version"],
                "schema_version": canonical_spec["schema_version"],
                "index_format_version": canonical_spec["index_format_version"],
                "manifest_sha256": canonical_spec["manifest_sha256"],
                "entry_count": canonical_spec["entry_count"],
                "sense_count": canonical_spec["sense_count"],
                "coverage": canonical_spec["coverage"],
            },
            "runtime_pack": verified_pack,
            "pack_bytes": pack_bytes,
        },
        "cold_start": cold_start_metrics,
        "warm": {
            "query_count": len(requests_json),
            "warmup_count": warmup_count,
            "seed": seed,
            "corpus_sha256": corpus_sha256,
            "native_dispatch": {
                "latency_ms": native_latency,
                "throughput_qps": round(len(requests_json) / native_total_s, 2),
                "response_bytes": compute_byte_stats(native_response_bytes),
                "peak_rss_bytes": int(native_mem["peak_rss_bytes"]),
                "sample_count": int(native_mem["sample_count"]),
                "sampling_interval_ms": float(native_mem["sampling_interval_ms"]),
            },
            "serialized_end_to_end": {
                "latency_ms": serialized_latency,
                "throughput_qps": round(len(requests_json) / serialized_total_s, 2),
                "request_bytes": compute_byte_stats(request_byte_sizes),
                "response_bytes": compute_byte_stats(serialized_response_bytes),
                "peak_rss_bytes": int(ser_mem["peak_rss_bytes"]),
                "sample_count": int(ser_mem["sample_count"]),
                "sampling_interval_ms": float(ser_mem["sampling_interval_ms"]),
            },
            "verification": {
                "verified_queries": len(requests_json),
                "matched_queries": matched_queries,
                "not_found_queries": not_found_queries,
                "truncated_responses": 0,
                "schema_validated_unique_responses": schema_validated_count,
                "largest_response": largest_response_info,
            },
        },
    }


def assemble_benchmark_report(
    *,
    workloads: dict[str, dict[str, Any]],
    sampling_interval_ms: float = DEFAULT_SAMPLING_INTERVAL_MS,
) -> dict[str, Any]:
    """Assemble the complete Feature 021 benchmark report."""
    measurement_completed = bool(workloads) and all(
        bool(item.get("measurement_completed")) for item in workloads.values()
    )
    budget_met = bool(workloads) and all(
        bool(item.get("budget_met")) for item in workloads.values()
    )
    return {
        "schema_version": BENCH_SCHEMA_VERSION,
        "feature": "021-lexicon-curation",
        "task": "T063",
        "measurement_completed": measurement_completed,
        "budget_met": budget_met,
        "environment": collect_environment_metadata(
            sampling_interval_ms=sampling_interval_ms,
        ),
        "workloads": workloads,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tools.lexicon_bench",
        description="Feature 021 T063 lexicon structural and native lookup benchmark runner",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["structural", "lookup", "all"],
        help="Benchmark workload to execute",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-root", type=Path, default=SOURCE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--no-manifest", action="store_true")
    parser.add_argument("--scratch-dir", type=Path, default=DEFAULT_SCRATCH_BASE)
    parser.add_argument("--keep-scratch", action="store_true")
    parser.add_argument("--allow-noncanonical-counts", action="store_true")
    parser.add_argument("--sampling-interval-ms", type=float, default=DEFAULT_SAMPLING_INTERVAL_MS)
    parser.add_argument("--queries", type=int, default=DEFAULT_WARM_QUERIES)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP_QUERIES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--enforce-budgets",
        action="store_true",
        help="Return exit code 1 if measurement succeeds but any performance budget target is missed",
    )

    # Hidden internal subprocess entrypoints for clean stage/cold-start memory isolation
    parser.add_argument("--_internal-stage", choices=[STAGE_INVENTORY, STAGE_STAGE, STAGE_VALIDATION], help=argparse.SUPPRESS)
    parser.add_argument("--inventory-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--workspace", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--proof-out", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--stage-result-out", type=Path, help=argparse.SUPPRESS)

    parser.add_argument("--_internal-cold-start", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--query", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--expected-manifest", type=str, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        manifest_arg = None if args.no_manifest else args.manifest
        if args._internal_stage:
            if not all([args.inventory_path, args.workspace, args.proof_out, args.stage_result_out]):
                raise LexiconError("missing internal stage paths", code=2)
            details = execute_structural_stage_worker(
                stage_name=args._internal_stage,
                source_root=args.source_root,
                manifest_path=manifest_arg,
                inventory_path=args.inventory_path,
                workspace=args.workspace,
                proof_out=args.proof_out,
                allow_noncanonical_counts=args.allow_noncanonical_counts,
            )
            details["self_rss_bytes"] = int(psutil.Process().memory_info().rss)
            atomic_json(args.stage_result_out, details, source_root=args.source_root)
            return 0

        if args._internal_cold_start:
            if not args.query or not args.expected_manifest:
                raise LexiconError("missing internal cold-start arguments", code=2)
            doc = _execute_cold_start_worker(
                query=args.query,
                expected_manifest=args.expected_manifest,
            )
            sys.stdout.write(json_text(doc))
            return 0

        if not args.mode:
            parser.print_help()
            return 2

        safe_out = check_safe_output_path(args.output)
        workloads: dict[str, dict[str, Any]] = {}
        if args.mode in ("structural", "all"):
            workloads["structural"] = run_structural_benchmark(
                source_root=args.source_root,
                manifest_path=manifest_arg,
                scratch_base=args.scratch_dir,
                sampling_interval_ms=args.sampling_interval_ms,
                allow_noncanonical_counts=args.allow_noncanonical_counts,
                keep_scratch=args.keep_scratch,
            )
        if args.mode in ("lookup", "all"):
            workloads["lookup"] = run_lookup_benchmark(
                queries=args.queries,
                warmup=args.warmup,
                seed=args.seed,
                sampling_interval_ms=args.sampling_interval_ms,
            )

        report = assemble_benchmark_report(
            workloads=workloads,
            sampling_interval_ms=args.sampling_interval_ms,
        )
        atomic_json(safe_out, report, source_root=args.source_root)
        sys.stdout.write(
            json_text(
                {
                    "output": str(safe_out),
                    "measurement_completed": report["measurement_completed"],
                    "budget_met": report["budget_met"],
                    "workloads": {
                        k: {
                            "measurement_completed": v["measurement_completed"],
                            "budget_met": v["budget_met"],
                        }
                        for k, v in report["workloads"].items()
                    },
                }
            )
        )
        if args.enforce_budgets and not report["budget_met"]:
            return 1
        return 0
    except LexiconError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return exc.code


if __name__ == "__main__":
    raise SystemExit(main())
