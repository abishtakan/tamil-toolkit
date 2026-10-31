"""Build and verify release artifacts. Never uploads to a registry."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
import zipfile
from pathlib import Path

from release_files import PUBLIC, ROOT, VERSION, sync
from release_policy import archive_paths, check, load

OUT = ROOT / "target/alpha"
SMOKE = ROOT / "tools/release_smoke"


def run(*args, cwd=ROOT, capture=False, env=None):
    executable = shutil.which(str(args[0]))
    if executable is None:
        raise RuntimeError(f"Missing executable: {args[0]}")
    print("+ " + " ".join(map(str, args)), flush=True)
    result = subprocess.run([executable, *map(str, args[1:])], cwd=cwd, check=True,
                            capture_output=capture, text=True, encoding="utf-8", env=env)
    return result.stdout if capture else None


def fixtures(destination):
    # Export unchanged active rows, including exact errors, without importing a binding.
    golden = ROOT / "tests/golden"
    manifest = json.loads((golden / "manifest.json").read_text(encoding="utf-8"))
    content = "".join((golden / suite["file"]).read_text(encoding="utf-8")
                      for suite in manifest["suites"] if suite["status"] == "active")
    path = destination / "golden.jsonl"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def patches(paths):
    return "[patch.crates-io]\n" + "".join(
        f'{name} = {{ path = "{path.as_posix()}" }}\n' for name, path in paths.items())


def rust():
    sync(check=True)
    destination = OUT / "rust"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tamil-alpha-rust-") as directory:
        temp = Path(directory)
        config = temp / "patches.toml"
        config.write_text(patches({name: ROOT / "crates" / name for name in PUBLIC}), encoding="utf-8")
        selections = [item for name in PUBLIC for item in ("-p", name)]
        # Unpublished siblings cannot resolve from crates.io yet. These patches
        # affect local verification only; normalized archives keep registry versions.
        run("cargo", "package", *selections, "--allow-dirty", "--config", config)
        extracted = {}
        for name in PUBLIC:
            archive = ROOT / "target/package" / f"{name}-{VERSION}.crate"
            shutil.copy2(archive, destination / archive.name)
            with tarfile.open(archive) as package:
                package.extractall(temp / "crates", filter="data")
            extracted[name] = temp / "crates" / f"{name}-{VERSION}"
            manifest = tomllib.loads((extracted[name] / "Cargo.toml").read_text(encoding="utf-8"))
            assert manifest["package"]["license"] == "MIT"
            for file in ("LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"):
                assert (extracted[name] / file).is_file(), (name, file)
            for dependency in manifest.get("dependencies", {}).values():
                assert "path" not in dependency, f"Published path dependency in {name}"
        consumer = temp / "consumer"
        (consumer / "src").mkdir(parents=True)
        (consumer / "Cargo.toml").write_text(
            '[package]\nname = "alpha-consumer"\nversion = "0.0.0"\nedition = "2021"\n'
            f'[dependencies]\ntamil-toolkit = "={VERSION}"\nserde_json = "1"\n' + patches(extracted), encoding="utf-8")
        shutil.copy2(SMOKE / "rust_consumer.rs", consumer / "src/main.rs")
        run("cargo", "run", "--quiet", "--", fixtures(consumer), cwd=consumer)


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


def stage_python(destination):
    """Minimal workspace; prune omitted members without changing locked releases."""
    destination.mkdir(parents=True)
    for name in PUBLIC:
        shutil.copytree(ROOT / "crates" / name, destination / "crates" / name,
                        ignore=shutil.ignore_patterns("tests", "target"))
    shutil.copytree(ROOT / "bindings/python", destination / "bindings/python",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyd", "*.so", "*.pdb", "*.egg-info"))
    manifest = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    members = json.dumps([f"crates/{name}" for name in PUBLIC] + ["bindings/python"])
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
    return destination / "bindings/python"


def python():
    sync(check=True)
    licenses()
    destination = OUT / "python"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tamil-alpha-python-") as directory:
        temp = Path(directory)
        project = stage_python(temp / "staged")
        run("maturin", "build", "--release", "--locked", "--sdist", "--out", destination, cwd=project)
        sdists = list(destination.glob(f"tamil_toolkit-{load()['python_version']}.tar.gz"))
        assert len(sdists) == 1, "Expected exactly the selected release source distribution"
        with tarfile.open(sdists[0]) as package:
            package.extractall(temp / "source", filter="data")
        project, = (path.parent for path in (temp / "source").rglob("pyproject.toml"))
        wheels = temp / "wheels"
        run("maturin", "build", "--release", "--locked", "--out", wheels, cwd=project)
        wheel, = wheels.glob("*.whl")
        with zipfile.ZipFile(wheel) as package:
            names = package.namelist()
            for suffix in ("LICENSE", "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_LICENSES.txt"):
                assert any(name.endswith("/" + suffix) for name in names), suffix
        artifact = destination / wheel.name
        shutil.copy2(wheel, artifact)
        verify_python(artifact, temp)


def verify_python(wheel, temp):
    environment = temp / "venv"
    venv.create(environment, with_pip=True)
    interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(interpreter, "-m", "pip", "install", "--no-deps", wheel)
    shutil.copy2(SMOKE / "python_consumer.py", temp / "consumer.py")
    run(interpreter, "-I", temp / "consumer.py", fixtures(temp), load()["python_version"], cwd=temp)


def npm():
    sync(check=True)
    licenses()
    package = ROOT / "bindings/js-wasm"
    for target, output in (("nodejs", "pkg-node"), ("web", "pkg-web")):
        run("pnpm", "--filter", "tamil-toolkit", "exec", "wasm-pack", "build", ".", "--release",
            "--target", target, "--out-dir", output, "--out-name", "tamil_toolkit", "--locked")
        # wasm-pack writes .gitignore="*" in each output. npm otherwise uses
        # those files and silently omits the actual WASM from the parent tarball.
        (package / output / ".npmignore").write_text("# Include wasm-pack outputs.\n", encoding="utf-8")
    run("pnpm", "--filter", "tamil-toolkit", "build")
    destination = OUT / "npm"
    destination.mkdir(parents=True, exist_ok=True)
    run("npm", "pack", "--pack-destination", destination, cwd=package)
    archive = destination / f"tamil-toolkit-{VERSION}.tgz"
    with tarfile.open(archive) as packed:
        names = set(packed.getnames())
        for path in ("dist/index.d.ts", "dist/web.d.ts", "dist/api.d.ts", "pkg-node/tamil_toolkit_bg.wasm",
                     "pkg-web/tamil_toolkit_bg.wasm", "LICENSE", "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_LICENSES.txt"):
            assert "package/" + path in names, path
    with tempfile.TemporaryDirectory(prefix="tamil-alpha-npm-") as directory:
        temp = Path(directory)
        (temp / "package.json").write_text('{"private":true,"type":"module"}', encoding="utf-8")
        run("npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", archive, cwd=temp)
        for source in ("node_consumer.mjs", "types_consumer.ts"):
            shutil.copy2(SMOKE / source, temp / source)
        run("node", package / "node_modules/typescript/bin/tsc", "--noEmit", "--strict", "--target", "ES2022",
            "--module", "NodeNext", "--moduleResolution", "NodeNext", "types_consumer.ts", cwd=temp)
        run("node", "node_consumer.mjs", fixtures(temp), cwd=temp)


def hashes():
    records = {path.relative_to(OUT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in archive_paths(OUT)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SHA256SUMS.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Artifact digests recorded for {len(records)} archives in {OUT}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=("rust", "python", "npm", "licenses", "stage-python", "verify-wheel", "all", "hashes"))
    parser.add_argument("--wheel", type=Path, help="Exactly one platform wheel to install and verify")
    args = parser.parse_args()
    task = args.task
    check()
    if task == "verify-wheel":
        if args.wheel is None:
            parser.error("verify-wheel requires --wheel")
        with tempfile.TemporaryDirectory(prefix="tamil-alpha-wheel-") as directory:
            verify_python(args.wheel.resolve(), Path(directory))
    elif task == "stage-python":
        sync(check=True)
        licenses()
        print(stage_python(OUT / "python-source"))
    elif task == "all":
        rust()
        python()
        npm()
    else:
        globals()[task]()
    if task not in ("licenses", "stage-python", "verify-wheel", "hashes"):
        hashes()


if __name__ == "__main__":
    main()
