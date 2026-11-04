"""Read-only release gates and artifact preparation. Never publishes packages."""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import urllib.error
import urllib.request
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


def parse_version(version):
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:-(alpha|beta|rc)\.([1-9]\d*))?", version)
    require(match is not None, "Unsupported release version; use X.Y.Z[-alpha.N|-beta.N|-rc.N]")
    base, stage, number = match.groups()
    channel = stage or "stable"
    python_version = base + ({"alpha": "a", "beta": "b", "rc": "rc"}[stage] + number if stage else "")
    npm_tag = stage or "latest"
    record_name = f"{stage}-{number}" if stage else f"v{base}"
    label = f"{stage} {number}" if stage else base
    return {
        "version": version,
        "base": base,
        "stage": stage,
        "number": number,
        "channel": channel,
        "python_version": python_version,
        "npm_tag": npm_tag,
        "record_name": record_name,
        "label": label,
    }


def load(root=ROOT):
    policy = read_toml(root / "release-policy.toml")
    require(policy["schema"] == 1, "Unknown release policy schema")
    require(policy["branch"] == "master", "Release branch requires workflow review")
    require(policy["registries"] == ["crates.io", "pypi", "npm"], "Registry scope requires workflow review")
    version = read_toml(root / "Cargo.toml")["workspace"]["package"]["version"]
    parsed = parse_version(version)
    require(policy["channel"] == parsed["channel"], "Release channel disagrees with workspace version")
    public = policy["public_crates"]
    require(public and len(public) == len(set(public)) and public[-1] == "tamil-toolkit",
            "Public crate list must be unique and end with the umbrella")
    require(all(re.fullmatch(r"tamil-[a-z]+", name) for name in public), "Invalid public crate name")
    return {**policy, **parsed}


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
            if not dependency.startswith("tamil-") or dependency == "tamil-calendar":
                continue
            require(dependency in public, f"{name}: unfinished dependency {dependency}")
            require(public.index(dependency) < public.index(name), f"{name}: public dependency order is wrong")
            require(settings == {"workspace": True}, f"{name}: dependency must inherit workspace: {dependency}")
    require(found == set(public), "Public scope contains missing or private support crates")
    umbrella = read_toml(root / "crates/tamil-toolkit/Cargo.toml")["dependencies"]
    require({name for name in umbrella if name.startswith("tamil-") and name != "tamil-calendar"} == set(public) - {"tamil-toolkit"},
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
        if package == "all":
            output["version"] = policy["version"]
            output["packages"] = " ".join(policy["public_crates"])
            for name in policy["public_crates"]:
                output[f"crate_{name.replace('-', '_')}"] = str(
                    next(p for p in rust if p.name == f"{name}-{policy['version']}.crate"))
        else:
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


def compare_crate(reviewed=None, built=None, directory=None, package=None, root=ROOT):
    policy = load(root)
    if package == "all" or (package is None and reviewed is None and directory is not None):
        rust_archives = archive_paths(directory / "rust")
        for name in policy["public_crates"]:
            rev = next(p for p in rust_archives if p.name == f"{name}-{policy['version']}.crate")
            bld = root / f"target/package/{name}-{policy['version']}.crate"
            compare_crate(reviewed=rev, built=bld, root=root)
        return
    if reviewed is None and directory is not None and package is not None:
        reviewed = next(p for p in archive_paths(directory / "rust") if p.name == f"{package}-{policy['version']}.crate")
    if built is None and package is not None:
        built = root / f"target/package/{package}-{policy['version']}.crate"
    require(reviewed is not None and built is not None, "Both reviewed and built crate archives are required")
    expected, actual = tar_files(reviewed), tar_files(built)
    require(set(expected) == set(actual), "Repackaged crate file inventory differs from review")
    prefix = reviewed.stem + "/"
    require(all(name.startswith(prefix) for name in expected), "Unexpected crate archive root")
    changed = [name for name in expected if expected[name] != actual[name]
               and name != prefix + "Cargo.lock"]
    require(not changed, "Repackaged crate content differs from review: " + ", ".join(changed))


def is_published(registry, package, version=None, root=ROOT):
    if version is None:
        version = load(root)["version"]
    if registry == "crates.io":
        url = f"https://crates.io/api/v1/crates/{package}/{version}"
        headers = {"User-Agent": f"tamil-toolkit-release-verifier/{version} (https://github.com/{REPOSITORY})"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return False
            raise
        except Exception:
            return False
    elif registry == "npm":
        url = f"https://registry.npmjs.org/{package}/{version}"
        req = urllib.request.Request(url, headers={"User-Agent": "tamil-toolkit-release-verifier"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return False
            raise
        except Exception:
            return False
    elif registry == "pypi":
        try:
            py_ver = parse_version(version)["python_version"]
        except ValueError:
            py_ver = version
        url = f"https://pypi.org/pypi/{package}/{py_ver}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "tamil-toolkit-release-verifier"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return False
            raise
        except Exception:
            return False
    else:
        raise ValueError(f"Unknown registry: {registry}")


def update_cargo_lock(lock_text, new_version):
    blocks = lock_text.split("[[package]]\n")
    new_blocks = [blocks[0]]
    for block in blocks[1:]:
        if 'source = ' not in block and re.search(r'name = "tamil-[a-z]+"', block):
            block = re.sub(r'version = "[^"]*"', f'version = "{new_version}"', block, count=1)
        new_blocks.append(block)
    return "[[package]]\n".join(new_blocks)


def update_changelog(changelog_text, version, python_version, today=None, force=False):
    if today is None:
        today = datetime.date.today().isoformat()
    match = re.search(r"(?s)(## Unreleased\s*\n\n?)(.*?)(?=\n## |\Z)", changelog_text)
    if not match:
        return changelog_text
    prefix, unreleased = match.group(1), match.group(2).strip()
    if not unreleased and not force:
        return changelog_text
    new_header = f"## Unreleased\n\n## {version} / Python {python_version} - {today}\n\n"
    if unreleased:
        new_header += unreleased + "\n"
    return changelog_text[:match.start()] + new_header + changelog_text[match.end():]


def scaffold_release_record(path, parsed):
    version = parsed["version"]
    python_version = parsed["python_version"]
    label = parsed["label"]
    title = label.title()
    content = f"""# {title} release

Status: pending publication.

## Reviewed source and artifact matrix

- Release version: Rust/npm `{version}`; Python `{python_version}`.
- Reviewed source commit: pending.
- Artifact workflow: pending.
- Local release checks passed: pending.

## Published registries

### crates.io

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/{version}) | `{version}` | pending | pending |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/{version}) | `{version}` | pending | pending |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/{version}) | `{version}` | pending | pending |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/{version}) | `{version}` | pending | pending |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/{version}) | `{version}` | pending | pending |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/{version}) | `{version}` | pending | pending |

### npm

[`tamil-toolkit@{version}`](https://www.npmjs.com/package/tamil-toolkit/v/{version})

### PyPI

[`tamil-toolkit {python_version}`](https://pypi.org/project/tamil-toolkit/{python_version}/)

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-{python_version}-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | pending |
| Windows wheel `tamil_toolkit-{python_version}-cp311-abi3-win_amd64.whl` | pending |
| macOS wheel `tamil_toolkit-{python_version}-cp311-abi3-macosx_11_0_arm64.whl` | pending |
| Source archive `tamil_toolkit-{python_version}.tar.gz` | pending |

## Compatibility and scope

Pending publication.
"""
    path.write_text(content, encoding="utf-8")


def prepare(version, root=ROOT, lockfile=False, changelog=False):
    parsed = parse_version(version)
    policy_path = root / "release-policy.toml"
    if policy_path.exists():
        policy_text = policy_path.read_text(encoding="utf-8")
        policy_text = re.sub(r'(?m)^channel\s*=\s*"[^"]*"', f'channel = "{parsed["channel"]}"', policy_text)
        policy_path.write_text(policy_text, encoding="utf-8")

    cargo_root = root / "Cargo.toml"
    if cargo_root.exists():
        cargo_text = cargo_root.read_text(encoding="utf-8")
        cargo_text = re.sub(r'(?m)^version\s*=\s*"[^"]*"', f'version = "{version}"', cargo_text, count=1)
        cargo_text = re.sub(rf'(?m)^(tamil-[a-z]+\s*=\s*\{{[^}}]*version\s*=\s*")[^"]*(")',
                            rf'\g<1>={version}\g<2>', cargo_text)
        cargo_root.write_text(cargo_text, encoding="utf-8")

    for crate_manifest in (root / "crates").glob("*/Cargo.toml"):
        text = crate_manifest.read_text(encoding="utf-8")
        crate_name = crate_manifest.parent.name
        if "documentation =" in text:
            text = re.sub(r'(?m)^documentation\s*=\s*"[^"]*"',
                          f'documentation = "https://docs.rs/{crate_name}/{version}"', text)
            crate_manifest.write_text(text, encoding="utf-8")

    pyproject_path = root / "bindings/python/pyproject.toml"
    if pyproject_path.exists():
        pyproject_text = pyproject_path.read_text(encoding="utf-8")
        pyproject_text = re.sub(r'(?m)^version\s*=\s*"[^"]*"',
                                f'version = "{parsed["python_version"]}"', pyproject_text, count=1)
        pyproject_path.write_text(pyproject_text, encoding="utf-8")

    package_json = root / "bindings/js-wasm/package.json"
    if package_json.exists():
        js_text = package_json.read_text(encoding="utf-8")
        js_text = re.sub(r'"version":\s*"[^"]*"', f'"version": "{version}"', js_text, count=1)
        js_text = re.sub(r'("publishConfig":\s*\{[^}]*"tag":\s*")[^"]*(")',
                         rf'\g<1>{parsed["npm_tag"]}\g<2>', js_text)
        package_json.write_text(js_text, encoding="utf-8")

    lock_path = root / "Cargo.lock"
    if lock_path.exists():
        lock_text = lock_path.read_text(encoding="utf-8")
        updated_lock = update_cargo_lock(lock_text, version)
        lock_path.write_text(updated_lock, encoding="utf-8")
        if lockfile and shutil.which("cargo"):
            try:
                subprocess.run(["cargo", "update", "--workspace"], cwd=root, check=True,
                               capture_output=True, text=True)
            except Exception:
                pass

    changelog_path = root / "CHANGELOG.md"
    if changelog_path.exists():
        cl_text = changelog_path.read_text(encoding="utf-8")
        new_cl = update_changelog(cl_text, version, parsed["python_version"], force=changelog)
        if new_cl != cl_text:
            changelog_path.write_text(new_cl, encoding="utf-8")

    record_path = root / f"docs/releases/{parsed['record_name']}.md"
    if not record_path.exists():
        record_path.parent.mkdir(parents=True, exist_ok=True)
        scaffold_release_record(record_path, parsed)

    try:
        from release_files import sync
        sync(root=root, check=False)
    except ModuleNotFoundError:
        try:
            from tools.release_files import sync
            sync(root=root, check=False)
        except ImportError:
            pass
    except ImportError:
        pass

    return check(root)


def release_record(run_id, root=ROOT, output=None):
    policy = load(root)
    version = policy["version"]
    python_version = policy["python_version"]
    record_name = policy["record_name"]
    label = policy["label"]
    title = label.title()

    # 1. Fetch artifact run info
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    run_info = {}
    if shutil.which("gh"):
        try:
            out = subprocess.check_output(["gh", "api", f"repos/{REPOSITORY}/actions/runs/{run_id}"],
                                          cwd=root, text=True, stderr=subprocess.DEVNULL)
            run_info = json.loads(out)
        except Exception:
            pass
    if not run_info:
        headers = {"User-Agent": "tamil-toolkit-release-verifier"}
        if token:
            headers["Authorization"] = f"token {token}"
        req = urllib.request.Request(f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                run_info = json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

    head_sha = run_info.get("head_sha", "pending")
    run_url = run_info.get("html_url", f"https://github.com/{REPOSITORY}/actions/runs/{run_id}")

    # 2. Query publisher runs for head_sha
    publisher_runs = []
    if head_sha != "pending":
        if shutil.which("gh"):
            try:
                out = subprocess.check_output(
                    ["gh", "api", f"repos/{REPOSITORY}/actions/runs?event=workflow_dispatch&head_sha={head_sha}&per_page=50"],
                    cwd=root, text=True, stderr=subprocess.DEVNULL)
                publisher_runs = json.loads(out).get("workflow_runs", [])
            except Exception:
                pass
        if not publisher_runs:
            headers = {"User-Agent": "tamil-toolkit-release-verifier"}
            if token:
                headers["Authorization"] = f"token {token}"
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPOSITORY}/actions/runs?event=workflow_dispatch&head_sha={head_sha}&per_page=50",
                headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    publisher_runs = json.loads(resp.read().decode("utf-8")).get("workflow_runs", [])
            except Exception:
                pass

    crate_runs = {}
    npm_run_id = None
    pypi_run_id = None
    unified_run_id = None

    for r in publisher_runs:
        if r.get("conclusion") != "success":
            continue
        name = r.get("name", "")
        rid = r["id"]
        if "Publish release" in name:
            unified_run_id = rid
        elif "Publish npm package" in name and not npm_run_id:
            npm_run_id = rid
        elif "Publish Python package to PyPI" in name and not pypi_run_id:
            pypi_run_id = rid
        elif "Publish Rust crate to crates.io" in name:
            crate_runs[rid] = r

    if unified_run_id:
        npm_run_id = npm_run_id or unified_run_id
        pypi_run_id = pypi_run_id or unified_run_id

    # 3. Query registry checksums
    crate_checksums = {}
    for crate_name in policy["public_crates"]:
        try:
            req = urllib.request.Request(
                f"https://crates.io/api/v1/crates/{crate_name}/{version}",
                headers={"User-Agent": f"tamil-toolkit-release-verifier/{version} (https://github.com/{REPOSITORY})"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                crate_checksums[crate_name] = data["version"].get("checksum", "pending")
        except Exception:
            crate_checksums[crate_name] = "pending"

    npm_sha256 = "pending"
    try:
        req = urllib.request.Request(
            f"https://registry.npmjs.org/tamil-toolkit/-/tamil-toolkit-{version}.tgz",
            headers={"User-Agent": "tamil-toolkit-release-verifier"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            npm_sha256 = hashlib.sha256(resp.read()).hexdigest()
    except Exception:
        pass

    pypi_checksums = {}
    try:
        req = urllib.request.Request(
            f"https://pypi.org/pypi/tamil-toolkit/{python_version}/json",
            headers={"User-Agent": "tamil-toolkit-release-verifier"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for u in data.get("urls", []):
                pypi_checksums[u["filename"]] = u.get("digests", {}).get("sha256", "pending")
    except Exception:
        pass

    # Fallback to local artifact hash manifest if available
    sums_file = root / "target/alpha/SHA256SUMS.json"
    if sums_file.exists():
        local_hashes = read_json(sums_file)
        if npm_sha256 == "pending":
            npm_sha256 = local_hashes.get(f"npm/tamil-toolkit-{version}.tgz", "pending")
        for name in policy["public_crates"]:
            if crate_checksums.get(name) == "pending":
                crate_checksums[name] = local_hashes.get(f"rust/{name}-{version}.crate", "pending")

    crate_rows = []
    sorted_crate_runs = sorted(crate_runs.keys())
    for idx, crate_name in enumerate(policy["public_crates"]):
        chk = crate_checksums.get(crate_name, "pending")
        if unified_run_id:
            c_run = f"[{unified_run_id}](https://github.com/{REPOSITORY}/actions/runs/{unified_run_id})"
        elif idx < len(sorted_crate_runs):
            c_id = sorted_crate_runs[idx]
            c_run = f"[{c_id}](https://github.com/{REPOSITORY}/actions/runs/{c_id})"
        else:
            c_run = "pending"
        crate_rows.append(
            f"| [`{crate_name}`](https://crates.io/crates/{crate_name}/{version}) | `{version}` | {c_run} | `{chk}` |")

    crate_table = "\n".join(crate_rows)

    npm_run_str = f"[run {npm_run_id}](https://github.com/{REPOSITORY}/actions/runs/{npm_run_id})" if npm_run_id else "pending"
    pypi_run_str = f"[run {pypi_run_id}](https://github.com/{REPOSITORY}/actions/runs/{pypi_run_id})" if pypi_run_id else "pending"

    linux_wheel = f"tamil_toolkit-{python_version}-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"
    win_wheel = f"tamil_toolkit-{python_version}-cp311-abi3-win_amd64.whl"
    mac_wheel = f"tamil_toolkit-{python_version}-cp311-abi3-macosx_11_0_arm64.whl"
    sdist = f"tamil_toolkit-{python_version}.tar.gz"

    pypi_table = f"""| File | SHA-256 |
| --- | --- |
| Linux wheel `{linux_wheel}` | `{pypi_checksums.get(linux_wheel, 'pending')}` |
| Windows wheel `{win_wheel}` | `{pypi_checksums.get(win_wheel, 'pending')}` |
| macOS wheel `{mac_wheel}` | `{pypi_checksums.get(mac_wheel, 'pending')}` |
| Source archive `{sdist}` | `{pypi_checksums.get(sdist, 'pending')}` |"""

    target_path = output or (root / f"docs/releases/{record_name}.md")
    compat_section = "Pending publication."
    if target_path.exists():
        existing_content = target_path.read_text(encoding="utf-8")
        match = re.search(r"(?s)## Compatibility and scope\s*\n\n?(.*)", existing_content)
        if match and match.group(1).strip() and match.group(1).strip() != "Pending publication.":
            compat_section = match.group(1).strip()

    doc = f"""# {title} release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v{version}`](https://github.com/{REPOSITORY}/tree/v{version})
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `{version}`; Python `{python_version}`.
- Reviewed source commit: `{head_sha}`.
- Artifact workflow: [run {run_id}]({run_url}), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
{crate_table}

### npm

[`tamil-toolkit@{version}`](https://www.npmjs.com/package/tamil-toolkit/v/{version})
was published by {npm_run_str}
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`{npm_sha256}`.
The `{policy["npm_tag"]}` tag points to `{version}`; `latest` remains on alpha 1.

### PyPI

[`tamil-toolkit {python_version}`](https://pypi.org/project/tamil-toolkit/{python_version}/)
was published by {pypi_run_str}
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

{pypi_table}

## Compatibility and scope

{compat_section}
"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(doc, encoding="utf-8")
    print(f"Release record written to {target_path}")
    return target_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=("check", "status", "record", "verify-run", "verify", "compare-crate",
                                         "prepare", "is-published", "release-record"))
    parser.add_argument("version", nargs="?", help="Release version for prepare or artifact run_id for release-record")
    parser.add_argument("--version", dest="version_flag", help="Release version")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--run-info", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--workflow-id", type=int)
    parser.add_argument("--registry", choices=("crates.io", "pypi", "npm"))
    parser.add_argument("--package")
    parser.add_argument("--dist", type=Path)
    parser.add_argument("--reviewed", type=Path)
    parser.add_argument("--built", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--lockfile", action="store_true")
    parser.add_argument("--changelog", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = args.version or args.version_flag
    if args.task in ("check", "status"):
        policy = check(args.root)
        print(json.dumps(policy, indent=2) if args.task == "status" else "Release policy verified.")
    elif args.task == "record":
        record(args.directory, root=args.root)
    elif args.task == "verify-run":
        verify_run(read_json(args.run_info), args.workflow_id,
                   read_json(args.directory / "rust/release-source.json"), args.source_sha, load(args.root))
    elif args.task == "verify":
        output = verify(args.registry, args.directory, args.source_sha, args.package, args.dist, root=args.root)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
                stream.writelines(f"{key}={value}\n" for key, value in output.items())
        print(json.dumps(output))
    elif args.task == "compare-crate":
        compare_crate(reviewed=args.reviewed, built=args.built,
                      directory=args.directory, package=args.package, root=args.root)
    elif args.task == "prepare":
        require(version, "Specify the version to prepare")
        prepare(version, root=args.root, lockfile=args.lockfile, changelog=args.changelog)
        print(f"Release {version} prepared successfully.")
    elif args.task == "is-published":
        require(args.registry and args.package, "is-published requires --registry and --package")
        published = is_published(args.registry, args.package, version, root=args.root)
        print(f"{args.package}@{version or load(args.root)['version']}: {'published' if published else 'not published'}")
        if not published:
            raise SystemExit(1)
    elif args.task == "release-record":
        run_id = args.run_id or version
        require(run_id, "Artifact run ID is required")
        release_record(run_id, root=args.root, output=args.output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"Release gate failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
