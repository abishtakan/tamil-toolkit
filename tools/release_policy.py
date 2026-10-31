"""Read-only release gates and artifact preparation. Never publishes packages."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "abishtakan/tamil-toolkit"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_toml(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load(root=ROOT):
    policy = read_toml(root / "release-policy.toml")
    require(policy["schema"] == 1, "Unknown release policy schema")
    require(policy["branch"] == "master", "Release branch requires workflow review")
    require(policy["registries"] == ["crates.io", "pypi", "npm"], "Registry scope requires workflow review")
    version = read_toml(root / "Cargo.toml")["workspace"]["package"]["version"]
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:-(alpha|beta|rc)\.([1-9]\d*))?", version)
    require(match is not None, "Unsupported release version; use X.Y.Z[-alpha.N|-beta.N|-rc.N]")
    base, stage, number = match.groups()
    require(policy["channel"] == (stage or "stable"), "Release channel disagrees with workspace version")
    python_version = base + ({"alpha": "a", "beta": "b", "rc": "rc"}[stage] + number if stage else "")
    public = policy["public_crates"]
    require(public and len(public) == len(set(public)) and public[-1] == "tamil-toolkit",
            "Public crate list must be unique and end with the umbrella")
    require(all(re.fullmatch(r"tamil-[a-z]+", name) for name in public), "Invalid public crate name")
    return {**policy, "version": version, "python_version": python_version,
            "npm_tag": stage or "latest"}


def check(root=ROOT):
    policy = load(root)
    workspace = read_toml(root / "Cargo.toml")["workspace"]
    public = policy["public_crates"]
    require(workspace["package"]["publish"] is False, "Workspace default must remain unpublished")
    require(workspace["package"]["license"] == "MIT", "Workspace license must be MIT")
    require(workspace["package"]["repository"] == "https://github.com/" + REPOSITORY,
            "Workspace repository identity drift")
    manifests = list((root / "crates").glob("*/Cargo.toml"))
    manifests += [root / "bindings" / path / "Cargo.toml" for path in
                  ("python", "js-wasm", "dart-flutter/rust")]
    suites = read_json(root / "tests/golden/manifest.json")["suites"]
    found = set()
    for path in manifests:
        manifest = read_toml(path)
        package = manifest["package"]
        name = package["name"]
        if name not in public:
            require(package.get("publish") in (False, {"workspace": True}),
                    f"Unapproved crate is publishable: {name}")
            continue
        require(path.parent.parent == root / "crates", f"FFI support crates cannot be public: {name}")
        found.add(name)
        require(package.get("version") == {"workspace": True}, f"{name}: version must inherit workspace")
        require(package.get("license") == {"workspace": True}
                and package.get("repository") == {"workspace": True},
                f"{name}: license/repository must inherit workspace")
        require(package.get("publish") == ["crates-io"], f"{name}: expected crates.io only")
        require(package.get("documentation") == f"https://docs.rs/{name}/{policy['version']}",
                f"{name}: documentation version drift")
        module = "core" if name == "tamil-norm" else name.removeprefix("tamil-")
        if name != "tamil-toolkit":
            require(any(s["status"] == "active" and s["file"].startswith(module + "_") for s in suites)
                    and any((root / "docs/specs").glob(module + "-*.md")),
                    f"{name}: a specification and active golden suite are required before publication")
        for dependency, settings in manifest.get("dependencies", {}).items():
            if not dependency.startswith("tamil-"):
                continue
            require(dependency in public, f"{name}: unfinished dependency {dependency}")
            require(public.index(dependency) < public.index(name), f"{name}: public dependency order is wrong")
            require(settings == {"workspace": True}, f"{name}: dependency must inherit workspace: {dependency}")
    require(found == set(public), "Public scope contains missing or private support crates")
    umbrella = read_toml(root / "crates/tamil-toolkit/Cargo.toml")["dependencies"]
    require({name for name in umbrella if name.startswith("tamil-")} == set(public) - {"tamil-toolkit"},
            "Umbrella must expose exactly the approved modules")
    for name, settings in workspace["dependencies"].items():
        if name.startswith("tamil-"):
            require(settings.get("version") == "=" + policy["version"], f"Dependency version drift: {name}")
    locked = read_toml(root / "Cargo.lock")["package"]
    require(all(p["version"] == policy["version"] for p in locked
                if "source" not in p and p["name"].startswith("tamil-")), "Cargo.lock workspace version drift")
    python = read_toml(root / "bindings/python/pyproject.toml")["project"]
    require(python["name"] == "tamil-toolkit" and python["version"] == policy["python_version"],
            "Python package identity/version drift")
    require(python.get("license") == "MIT", "Python license must be MIT")
    npm = read_json(root / "bindings/js-wasm/package.json")
    require(npm["name"] == "tamil-toolkit" and npm["version"] == policy["version"] and not npm.get("private"),
            "npm package identity/version/private drift")
    require(npm["publishConfig"] == {"access": "public", "tag": policy["npm_tag"]}, "npm release channel drift")
    require(npm.get("license") == "MIT", "npm license must be MIT")
    for path in ("package.json", "workbench/package.json"):
        require(read_json(root / path).get("private") is True, f"{path} must remain private")
    require(re.search(r"(?m)^publish_to:\s*none\s*$", (root / "bindings/dart-flutter/pubspec.yaml").read_text()),
            "Dart publishing is deferred")
    require(read_toml(root / "extensions/pg_tamil/Cargo.toml")["package"].get("publish") is False,
            "PostgreSQL publishing is deferred")
    return policy


def identity(policy, source_sha):
    require(re.fullmatch(r"[0-9a-f]{40}", source_sha) is not None, "Supply the full reviewed 40-character source SHA")
    return {"schema": 1, "source_sha": source_sha, **{key: policy[key] for key in
            ("version", "python_version", "npm_tag", "public_crates")}}


def archive_paths(directory):
    # Do not include old review downloads, consumers, or staged source trees.
    return sorted(path for folder in (directory, *(directory / name for name in ("rust", "python", "npm")))
                  if folder.is_dir() for path in folder.iterdir() if path.is_file()
                  and path.name.endswith((".crate", ".whl", ".tar.gz", ".tgz")))


def hashes(directory):
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in archive_paths(directory)}


def record(directory, root=ROOT):
    policy = check(root)
    changes = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"],
                                      cwd=root, text=True).strip()
    require(not changes, "Refuse to record release artifacts from a dirty source tree")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    directory.mkdir(parents=True, exist_ok=True)
    records = hashes(directory)
    require(records, "No release archives to record")
    for name, value in (("release-source.json", identity(policy, sha)), ("SHA256SUMS.json", records)):
        (directory / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def verify_run(run, workflow_id, manifest, source_sha, policy):
    identity(policy, source_sha)
    require(run.get("repository", {}).get("full_name") == REPOSITORY, "Wrong artifact repository")
    require(run.get("workflow_id") == workflow_id and run.get("name") == "Alpha distribution artifacts",
            "Wrong artifact workflow")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "Artifact run did not succeed")
    require(run.get("event") == "workflow_dispatch" and run.get("head_branch") == policy["branch"],
            "Artifact run must be an explicit master dispatch")
    require(manifest.get("schema") == 1 and manifest.get("source_sha") == source_sha,
            "Artifact source differs from the reviewed commit; rebuild using the new release harness")


def verified_archives(directory, expected):
    require(read_json(directory / "release-source.json") == expected, f"Source/release mismatch: {directory.name}")
    actual = hashes(directory)
    require(actual and actual == read_json(directory / "SHA256SUMS.json"), f"Artifact digest/inventory mismatch: {directory.name}")
    return archive_paths(directory)


def tar_files(archive):
    files = {}
    with tarfile.open(archive, "r:gz") as package:
        for member in package.getmembers():
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in member.name,
                    "Unsafe archive path")
            require(member.isfile() or member.isdir(), "Archive contains links or special files")
            if member.isfile():
                require(member.name not in files, "Duplicate archive member")
                files[member.name] = package.extractfile(member).read()
    return files


def metadata_matches(content, version):
    metadata = BytesParser().parsebytes(content)
    require(metadata.get("Name", "").replace("_", "-") == "tamil-toolkit" and metadata["Version"] == version,
            "Python archive metadata/version mismatch")


def verify(registry, directory, source_sha, package=None, dist=None, root=ROOT):
    policy = check(root)
    expected = identity(policy, source_sha)
    checkout_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    require(checkout_sha == source_sha, "Checkout differs from the reviewed source commit")
    output = {}
    # All publishers consume the same Rust source manifest, even when uploading bindings.
    rust = verified_archives(directory / "rust", expected)
    require({p.name for p in rust} == {f"{name}-{policy['version']}.crate" for name in policy["public_crates"]},
            "Rust artifact scope/version mismatch")
    if registry == "crates.io":
        require(package in policy["public_crates"], "Selected crate is outside the public allowlist")
        output["crate"] = str(next(p for p in rust if p.name == f"{package}-{policy['version']}.crate"))
        output["version"] = policy["version"]
    elif registry == "npm":
        archives = []
        for node in ("22", "24"):
            paths = verified_archives(directory / f"npm-node{node}", expected)
            require(len(paths) == 1 and paths[0].name == f"tamil-toolkit-{policy['version']}.tgz", "npm artifact scope/version mismatch")
            metadata = json.loads(tar_files(paths[0])["package/package.json"])
            require(metadata.get("name") == "tamil-toolkit" and metadata.get("version") == policy["version"]
                    and not metadata.get("private") and metadata.get("license") == "MIT"
                    and metadata.get("publishConfig") == {"access": "public", "tag": policy["npm_tag"]},
                    "npm archive metadata/channel mismatch")
            archives.append(paths[0])
        require(archives[0].read_bytes() == archives[1].read_bytes(), "Node 22/24 tarballs differ")
        output.update(tarball=str(archives[1]), npm_tag=policy["npm_tag"])
    elif registry == "pypi":
        selected = []
        for platform, suffix in (("linux", "manylinux2014_x86_64.manylinux_2_17_x86_64"),
                                 ("windows", "win_amd64"), ("macos", "macosx_11_0_arm64")):
            paths = verified_archives(directory / f"python-{platform}", expected)
            wheel = f"tamil_toolkit-{policy['python_version']}-cp311-abi3-{suffix}.whl"
            sdist = f"tamil_toolkit-{policy['python_version']}.tar.gz"
            require({p.name for p in paths} == {wheel, sdist}, f"Python {platform} artifact scope/version mismatch")
            wheel_path = next(p for p in paths if p.name == wheel)
            with zipfile.ZipFile(wheel_path) as packed:
                names = [name for name in packed.namelist() if name.endswith(".dist-info/METADATA")]
                require(len(names) == 1, "Wheel must have exactly one package metadata file")
                metadata_matches(packed.read(names[0]), policy["python_version"])
            source_path = next(p for p in paths if p.name == sdist)
            metadata_matches(tar_files(source_path)[f"tamil_toolkit-{policy['python_version']}/PKG-INFO"], policy["python_version"])
            selected.append(wheel_path)
            if platform == "linux":
                selected.append(source_path)
        require(dist is not None and not dist.exists(), "PyPI dist directory must be a fresh path")
        dist.mkdir(parents=True)
        for path in selected:
            shutil.copy2(path, dist / path.name)
    else:
        raise ValueError("Registry is outside release policy")
    return output


def compare_crate(reviewed, built):
    expected, actual = tar_files(reviewed), tar_files(built)
    require(set(expected) == set(actual), "Repackaged crate file inventory differs from review")
    prefix = reviewed.stem + "/"
    require(all(name.startswith(prefix) for name in expected), "Unexpected crate archive root")
    changed = [name for name in expected if expected[name] != actual[name]
               and name != prefix + "Cargo.lock"]
    require(not changed, "Repackaged crate content differs from review: " + ", ".join(changed))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=("check", "status", "record", "verify-run", "verify", "compare-crate"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--run-info", type=Path)
    parser.add_argument("--workflow-id", type=int)
    parser.add_argument("--registry", choices=("crates.io", "pypi", "npm"))
    parser.add_argument("--package")
    parser.add_argument("--dist", type=Path)
    parser.add_argument("--reviewed", type=Path)
    parser.add_argument("--built", type=Path)
    args = parser.parse_args()
    if args.task in ("check", "status"):
        policy = check()
        print(json.dumps(policy, indent=2) if args.task == "status" else "Release policy verified.")
    elif args.task == "record":
        record(args.directory)
    elif args.task == "verify-run":
        verify_run(read_json(args.run_info), args.workflow_id,
                   read_json(args.directory / "rust/release-source.json"), args.source_sha, load())
    elif args.task == "verify":
        output = verify(args.registry, args.directory, args.source_sha, args.package, args.dist)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
                stream.writelines(f"{key}={value}\n" for key, value in output.items())
        print(json.dumps(output))
    else:
        compare_crate(args.reviewed, args.built)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"Release gate failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
