"""Cross-platform task implementations. Use just recipes from the repo root."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT):
    executable = shutil.which(args[0])
    if executable is None:
        raise RuntimeError(f"Missing {args[0]}; see README.md prerequisites and just doctor")
    print("+ " + " ".join(args), flush=True)
    subprocess.run([executable, *args[1:]], cwd=cwd, check=True)


def check_unicode():
    run(sys.executable, "tools/mcp-tamil-oracle/check_source_unicode.py")


def test_rust():
    if shutil.which("cargo-nextest"):
        run("cargo", "nextest", "run", "--locked", "--workspace")
        run("cargo", "test", "--locked", "--workspace", "--exclude", "tamil-python", "--doc")
    else:
        print("cargo-nextest is optional; using cargo test (including the same proptest tests).", flush=True)
        run("cargo", "test", "--locked", "--workspace")


def sync_bindings():
    run("maturin", "develop", "--locked", cwd=ROOT / "bindings/python")
    for target, directory in [("nodejs", "pkg-node"), ("web", "pkg-web")]:
        run("pnpm", "exec", "wasm-pack", "build", "bindings/js-wasm", "--dev", "--target", target,
            "--out-dir", directory, "--out-name", "tamil_toolkit", "--locked")
    run("pnpm", "--filter", "tamil-toolkit", "build")


def parity_runners():
    run("cargo", "test", "--locked", "-p", "tamil-toolkit", "--test", "golden_suite", "--", "--nocapture")
    run(sys.executable, "-m", "pytest", "bindings/python/tests/test_golden.py", "-q")
    run("pnpm", "--filter", "tamil-toolkit", "test")


def test_parity():
    check_unicode()
    sync_bindings()
    parity_runners()


def test_dart():
    run("cargo", "build", "--locked", "-p", "tamil-dart")
    run("dart", "pub", "get", "--enforce-lockfile", cwd=ROOT / "bindings/dart-flutter")
    run("dart", "analyze", cwd=ROOT / "bindings/dart-flutter")
    run("dart", "test", cwd=ROOT / "bindings/dart-flutter")


def post_edit():
    run("cargo", "fmt", "--all", "--", "--check")
    check_unicode()
    run("cargo", "check", "--locked", "--workspace")


def pre_stop():
    post_edit()
    run("cargo", "clippy", "--locked", "--workspace", "--all-targets", "--", "-D", "warnings")
    test_rust()
    run(sys.executable, "-m", "pytest", "tests/harness", "-q")
    sync_bindings()
    parity_runners()


def bootstrap():
    run("uv", "sync", "--locked")
    run("pnpm", "install", "--frozen-lockfile")
    run("rustup", "target", "add", "wasm32-unknown-unknown")
    sync_bindings()


def doctor():
    missing = []
    for tool in ["cargo", "rustup", "uv", "pnpm", "just", "dart", "cargo-nextest"]:
        found = shutil.which(tool)
        print(f"{tool}: {found or 'MISSING'}")
        if not found and tool not in {"dart", "cargo-nextest"}:
            missing.append(tool)
    if missing:
        raise RuntimeError("Install or add to PATH: " + ", ".join(missing))


TASKS = {
    "bootstrap": bootstrap,
    "doctor": doctor,
    "check-unicode": check_unicode,
    "test-rust": test_rust,
    "sync-bindings": sync_bindings,
    "test-parity": test_parity,
    "test-dart": test_dart,
    "test-harness": lambda: run(sys.executable, "-m", "pytest", "tests/harness", "-q"),
    "agent-post-edit": post_edit,
    "agent-pre-stop-gate": pre_stop,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=TASKS)
    args = parser.parse_args()
    try:
        TASKS[args.task]()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
