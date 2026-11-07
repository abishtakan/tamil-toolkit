"""Release guardrails reject drift and tampering before any registry write."""

import io
import json
import shutil
import tarfile
import zipfile

import pytest

from tools import release_policy as gate

SHA = "a" * 40
POLICY = gate.load()


@pytest.fixture
def repository(tmp_path, monkeypatch):
    monkeypatch.setitem(gate.CRATE_RANKS, "tamil-unfinished", 4)
    root = tmp_path / "repository"
    paths = ["release-policy.toml", "Cargo.toml", "Cargo.lock", "package.json",
             "bindings/js-wasm/package.json",
             "bindings/python/pyproject.toml", "bindings/dart-flutter/pubspec.yaml",
             "extensions/pg_tamil/Cargo.toml", "tests/golden/manifest.json",
             "README.md", "bindings/python/README.md", "bindings/js-wasm/README.md",
             "CHANGELOG.md", "LICENSE"]
    paths += [str(p.relative_to(gate.ROOT)) for p in (gate.ROOT / "crates").glob("*/Cargo.toml")]
    paths += [f"bindings/{p}/Cargo.toml" for p in ("python", "js-wasm", "dart-flutter/rust")]
    paths += [str(p.relative_to(gate.ROOT)) for p in (gate.ROOT / "docs/specs").glob("*.md")]
    for path in paths:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gate.ROOT / path, target)
    planned = root / "crates/tamil-unfinished/Cargo.toml"
    planned.parent.mkdir(parents=True)
    planned.write_text('[package]\nname = "tamil-unfinished"\nversion.workspace = true\npublish.workspace = true\n'
                       'license.workspace = true\nrepository.workspace = true\n')
    return root


def replace(root, path, old, new):
    file = root / path
    text = file.read_text(encoding="utf-8")
    assert old in text
    file.write_text(text.replace(old, new), encoding="utf-8")


def pack(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as archive:
        for name, value in files.items():
            content = value.encode() if isinstance(value, str) else value
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))


def stamp(directory, policy):
    (directory / "release-source.json").write_text(json.dumps(gate.identity(policy, SHA)), encoding="utf-8")
    (directory / "SHA256SUMS.json").write_text(json.dumps(gate.hashes(directory)), encoding="utf-8")


@pytest.fixture
def artifacts(repository, tmp_path, monkeypatch):
    monkeypatch.setattr(gate.subprocess, "check_output", lambda *args, **kwargs: SHA + "\n")
    policy = gate.check(repository)
    root = tmp_path / "artifacts"
    for name in policy["public_crates"]:
        pack(root / "rust/rust" / f"{name}-{policy['version']}.crate", {"payload": "reviewed"})
    stamp(root / "rust", policy)
    metadata = {"name": "tamil-toolkit", "version": policy["version"], "license": "MIT",
                "publishConfig": {"access": "public", "tag": policy["npm_tag"]}}
    archive = root / "npm-node22/npm" / f"tamil-toolkit-{policy['version']}.tgz"
    pack(archive, {"package/package.json": json.dumps(metadata)})
    other = root / "npm-node24/npm" / archive.name
    other.parent.mkdir(parents=True)
    shutil.copy2(archive, other)
    for node in ("22", "24"):
        stamp(root / f"npm-node{node}", policy)
    content = f"Name: tamil-toolkit\nVersion: {policy['python_version']}\n"
    for platform, suffix in (("linux", "manylinux2014_x86_64.manylinux_2_17_x86_64"),
                             ("windows", "win_amd64"), ("macos", "macosx_11_0_arm64")):
        directory = root / f"python-{platform}"
        directory.mkdir()
        with zipfile.ZipFile(directory / f"tamil_toolkit-{policy['python_version']}-cp311-abi3-{suffix}.whl", "w") as wheel:
            wheel.writestr(f"tamil_toolkit-{policy['python_version']}.dist-info/METADATA", content)
        pack(directory / f"tamil_toolkit-{policy['python_version']}.tar.gz",
             {f"tamil_toolkit-{policy['python_version']}/PKG-INFO": content})
        stamp(directory, policy)
    return root, policy


def test_current_repository_meets_policy():
    gate.check()


@pytest.mark.parametrize("path,old,new,message", [
    ("crates/tamil-unfinished/Cargo.toml", "publish.workspace = true", 'publish = ["crates-io"]', "Unapproved crate"),
    ("bindings/python/Cargo.toml", "publish.workspace = true", 'publish = ["crates-io"]', "Unapproved crate"),
    ("bindings/python/pyproject.toml", f'version = "{POLICY["python_version"]}"', 'version = "9.9.9a99"', "Python package"),
    ("bindings/js-wasm/package.json", f'"tag": "{POLICY["npm_tag"]}"', '"tag": "incorrect"', "channel drift"),
    ("Cargo.toml", f'version = "={POLICY["version"]}"', 'version = "=9.9.9-alpha.99"', "Dependency version"),
    ("crates/tamil-toolkit/Cargo.toml", "tamil-core.workspace = true", "tamil-unfinished.workspace = true", "unfinished dependency"),
    ("bindings/dart-flutter/pubspec.yaml", "publish_to: none", "publish_to: https://pub.dev", "Dart publishing"),
    ("bindings/python/pyproject.toml", 'license = "MIT"', 'license = "Proprietary"', "Python license"),
])
def test_policy_rejects_release_drift(repository, path, old, new, message):
    replace(repository, path, old, new)
    with pytest.raises(ValueError, match=message):
        gate.check(repository)


def test_planned_suite_cannot_be_promoted_by_changing_package_flags(repository):
    replace(repository, "release-policy.toml", '"tamil-toolkit"', '"tamil-unfinished", "tamil-toolkit"')
    replace(repository, "crates/tamil-unfinished/Cargo.toml", "publish.workspace = true",
            f'publish = ["crates-io"]\ndocumentation = "https://docs.rs/tamil-unfinished/{POLICY["version"]}"')
    with pytest.raises(ValueError, match="specification and active golden"):
        gate.check(repository)


@pytest.mark.parametrize("version,channel,python_version,tag", [
    ("0.1.0-alpha.2", "alpha", "0.1.0a2", "alpha"),
    ("0.2.0-beta.3", "beta", "0.2.0b3", "beta"),
    ("1.0.0-rc.1", "rc", "1.0.0rc1", "rc"),
    ("1.0.0", "stable", "1.0.0", "latest"),
])
def test_next_release_versions_do_not_require_gate_edits(repository, version, channel, python_version, tag):
    replace(repository, "Cargo.toml", f'version = "{POLICY["version"]}"', f'version = "{version}"')
    replace(repository, "release-policy.toml", f'channel = "{POLICY["channel"]}"', f'channel = "{channel}"')
    policy = gate.load(repository)
    assert (policy["python_version"], policy["npm_tag"]) == (python_version, tag)


def test_synchronized_future_release_passes_without_changing_tools(repository):
    version, python_version = "9.8.7-alpha.42", "9.8.7a42"
    for path in [repository / "Cargo.toml", repository / "Cargo.lock",
                 *(repository / "crates").glob("*/Cargo.toml")]:
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(POLICY["version"], version), encoding="utf-8")
    replace(repository, "bindings/python/pyproject.toml", POLICY["python_version"], python_version)
    replace(repository, "bindings/js-wasm/package.json", POLICY["version"], version)
    replace(repository, "bindings/js-wasm/package.json", f'"tag": "{POLICY["npm_tag"]}"', '"tag": "alpha"')
    replace(repository, "release-policy.toml", f'channel = "{POLICY["channel"]}"', 'channel = "alpha"')
    assert gate.check(repository)["python_version"] == python_version


def test_dependency_order_is_enforced(repository):
    replace(repository, "release-policy.toml", '"tamil-core", "tamil-norm"', '"tamil-norm", "tamil-core"')
    with pytest.raises(ValueError, match="dependency order"):
        gate.check(repository)


def successful_run():
    return {"repository": {"full_name": gate.REPOSITORY}, "workflow_id": 42,
            "name": "Alpha distribution artifacts", "status": "completed", "conclusion": "success",
            "event": "workflow_dispatch", "head_branch": "master"}


@pytest.mark.parametrize("field,value", [("conclusion", "failure"), ("status", "in_progress"),
                                      ("event", "pull_request"), ("head_branch", "feature"),
                                      ("workflow_id", 99), ("repository", {"full_name": "someone/fork"})])
def test_artifact_run_rejects_wrong_origin_or_failed_checks(artifacts, field, value):
    _, policy = artifacts
    run = {**successful_run(), field: value}
    with pytest.raises(ValueError):
        gate.verify_run(run, 42, gate.identity(policy, SHA), SHA, policy)


def test_run_rejects_wrong_or_abbreviated_reviewed_commit(artifacts):
    _, policy = artifacts
    for sha in ("b" * 40, SHA[:7]):
        with pytest.raises(ValueError):
            gate.verify_run(successful_run(), 42, gate.identity(policy, SHA), sha, policy)


def test_reviewed_artifacts_pass_and_pypi_upload_is_exact(repository, artifacts, tmp_path):
    directory, _ = artifacts
    gate.verify_run(successful_run(), 42, gate.read_json(directory / "rust/release-source.json"), SHA, gate.load(repository))
    assert gate.verify("crates.io", directory, SHA, "tamil-core", root=repository)["crate"].endswith(".crate")
    assert gate.verify("npm", directory, SHA, root=repository)["npm_tag"] == POLICY["npm_tag"]
    dist = tmp_path / "dist"
    gate.verify("pypi", directory, SHA, dist=dist, root=repository)
    assert len(list(dist.glob("*.whl"))) == 3
    assert len(list(dist.glob("*.tar.gz"))) == 1


def test_publisher_rejects_unapproved_selected_crate(repository, artifacts):
    directory, _ = artifacts
    with pytest.raises(ValueError, match="outside the public allowlist"):
        gate.verify("crates.io", directory, SHA, "tamil-unfinished", root=repository)


def test_publisher_rejects_modified_archive(repository, artifacts):
    directory, _ = artifacts
    archive = next((directory / "npm-node24/npm").glob("*.tgz"))
    archive.write_bytes(archive.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="digest/inventory mismatch"):
        gate.verify("npm", directory, SHA, root=repository)


def test_publisher_rejects_different_platform_source(repository, artifacts):
    directory, policy = artifacts
    (directory / "python-windows/release-source.json").write_text(json.dumps(gate.identity(policy, "b" * 40)))
    with pytest.raises(ValueError, match="Source/release mismatch"):
        gate.verify("pypi", directory, SHA, dist=directory / "dist", root=repository)


def test_publisher_rejects_different_npm_builds_even_with_valid_hashes(repository, artifacts):
    directory, policy = artifacts
    archive = next((directory / "npm-node24/npm").glob("*.tgz"))
    content = gate.tar_files(archive)
    pack(archive, {**content, "package/extra.txt": "drift"})
    stamp(directory / "npm-node24", policy)
    with pytest.raises(ValueError, match="tarballs differ"):
        gate.verify("npm", directory, SHA, root=repository)


def test_publisher_rejects_wrong_checkout(repository, artifacts, monkeypatch):
    directory, _ = artifacts
    monkeypatch.setattr(gate.subprocess, "check_output", lambda *args, **kwargs: "b" * 40)
    with pytest.raises(ValueError, match="Checkout differs"):
        gate.verify("npm", directory, SHA, root=repository)


def test_hash_inventory_excludes_old_downloads_and_consumers(tmp_path):
    (tmp_path / "consumer").mkdir()
    (tmp_path / "consumer/stale.tgz").write_bytes(b"old")
    (tmp_path / "npm").mkdir()
    (tmp_path / "npm/current.tgz").write_bytes(b"current")
    assert set(gate.hashes(tmp_path)) == {"npm/current.tgz"}


def test_source_record_rejects_dirty_tree(repository, tmp_path, monkeypatch):
    monkeypatch.setattr(gate.subprocess, "check_output", lambda *args, **kwargs: " M Cargo.toml\n")
    with pytest.raises(ValueError, match="dirty source tree"):
        gate.record(tmp_path / "output", root=repository)


def test_source_record_captures_clean_commit_and_archive_digest(repository, tmp_path, monkeypatch):
    monkeypatch.setattr(gate.subprocess, "check_output", lambda args, **kwargs:
                        "" if args[1] == "status" else SHA + "\n")
    directory = tmp_path / "output"
    directory.mkdir()
    (directory / "package.tgz").write_bytes(b"reviewed")
    gate.record(directory, root=repository)
    assert gate.read_json(directory / "release-source.json") == gate.identity(gate.load(repository), SHA)
    assert gate.read_json(directory / "SHA256SUMS.json") == gate.hashes(directory)


def test_repackage_allows_generated_lock_only(tmp_path):
    reviewed = tmp_path / "tamil-core-0.1.0-alpha.1.crate"
    built = tmp_path / "built.crate"
    prefix = reviewed.stem + "/"
    pack(reviewed, {prefix + "src/lib.rs": "reviewed", prefix + "Cargo.lock": "local paths"})
    pack(built, {prefix + "src/lib.rs": "reviewed", prefix + "Cargo.lock": "registry sources"})
    gate.compare_crate(reviewed, built)
    pack(built, {prefix + "src/lib.rs": "changed", prefix + "Cargo.lock": "registry sources"})
    with pytest.raises(ValueError, match="content differs"):
        gate.compare_crate(reviewed, built)


def test_publishing_workflows_require_manual_review_and_serialize():
    for name in ("publish-crate.yml", "publish-npm.yml", "publish-pypi.yml", "publish-release.yml"):
        text = (gate.ROOT / ".github/workflows" / name).read_text()
        assert "workflow_dispatch:" in text and "source_sha:" in text
        assert "  push:" not in text and "  pull_request:" not in text
        assert "default: 'no'" in text and "cancel-in-progress: false" in text
        assert "github.ref == 'refs/heads/master'" in text
        assert "verify-run" in text and "--source-sha" in text
        assert "0.1.0-alpha.1" not in text


def test_parse_version():
    p1 = gate.parse_version("0.1.0-alpha.4")
    assert p1["version"] == "0.1.0-alpha.4"
    assert p1["channel"] == "alpha"
    assert p1["python_version"] == "0.1.0a4"
    assert p1["npm_tag"] == "alpha"
    assert p1["record_name"] == "alpha-4"

    p2 = gate.parse_version("0.2.0-beta.1")
    assert p2["channel"] == "beta"
    assert p2["python_version"] == "0.2.0b1"
    assert p2["npm_tag"] == "beta"
    assert p2["record_name"] == "beta-1"

    p3 = gate.parse_version("1.0.0-rc.3")
    assert p3["channel"] == "rc"
    assert p3["python_version"] == "1.0.0rc3"
    assert p3["npm_tag"] == "rc"
    assert p3["record_name"] == "rc-3"

    p4 = gate.parse_version("1.0.0")
    assert p4["channel"] == "stable"
    assert p4["python_version"] == "1.0.0"
    assert p4["npm_tag"] == "latest"
    assert p4["record_name"] == "v1.0.0"

    with pytest.raises(ValueError, match="Unsupported release version"):
        gate.parse_version("invalid-version")


def test_prepare_bumps_synthetic_repository(repository):
    from tools import release_files

    # Bump to 0.1.0-alpha.4
    gate.prepare("0.1.0-alpha.4", root=repository)
    p1 = gate.check(repository)
    assert p1["version"] == "0.1.0-alpha.4"
    assert p1["python_version"] == "0.1.0a4"
    assert p1["channel"] == "alpha"
    release_files.sync(root=repository, check=True)

    # Bump to 0.2.0-beta.1
    gate.prepare("0.2.0-beta.1", root=repository)
    p2 = gate.check(repository)
    assert p2["version"] == "0.2.0-beta.1"
    assert p2["python_version"] == "0.2.0b1"
    assert p2["channel"] == "beta"
    release_files.sync(root=repository, check=True)


def test_verify_package_all(repository, artifacts):
    directory, policy = artifacts
    output = gate.verify("crates.io", directory, SHA, package="all", root=repository)
    assert output["version"] == policy["version"]
    assert set(output["packages"].split()) == set(policy["public_crates"])
    for name in policy["public_crates"]:
        key = f"crate_{name.replace('-', '_')}"
        assert key in output
        assert output[key].endswith(".crate")


def test_compare_crate_batch(tmp_path):
    policy = gate.load()
    reviewed_dir = tmp_path / "reviewed"
    built_dir = tmp_path / "built"
    reviewed_dir.mkdir()
    built_dir.mkdir()
    for name in policy["public_crates"]:
        prefix = f"{name}-{policy['version']}/"
        rev_path = reviewed_dir / f"{name}-{policy['version']}.crate"
        bld_path = built_dir / f"{name}-{policy['version']}.crate"
        pack(rev_path, {prefix + "src/lib.rs": "code", prefix + "Cargo.lock": "lock a"})
        pack(bld_path, {prefix + "src/lib.rs": "code", prefix + "Cargo.lock": "lock b"})
        gate.compare_crate(reviewed=rev_path, built=bld_path)


def test_is_published_query(monkeypatch):
    class MockResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def mock_urlopen(req, timeout=10):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "404" in url:
            raise gate.urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return MockResponse()

    monkeypatch.setattr(gate.urllib.request, "urlopen", mock_urlopen)
    assert gate.is_published("crates.io", "tamil-core", "0.1.0-alpha.3") is True
    assert gate.is_published("crates.io", "tamil-core", "0.1.0-alpha.404") is False
    assert gate.is_published("npm", "tamil-toolkit", "0.1.0-alpha.3") is True
    assert gate.is_published("npm", "tamil-toolkit", "0.1.0-alpha.404") is False
    assert gate.is_published("pypi", "tamil-toolkit", "0.1.0-alpha.3") is True
    assert gate.is_published("pypi", "tamil-toolkit", "0.1.0-alpha.404") is False


@pytest.mark.parametrize("manifest_rel,section,dep_line,expected_match", [
    (
        "crates/tamil-core/Cargo.toml",
        "[dependencies]",
        "tamil-norm.workspace = true",
        "tamil-core \\(Rank 0\\): dependency tamil-norm \\(Rank 1\\) in \\[dependencies\\] violates acyclic DAG rank order",
    ),
    (
        "crates/tamil-punarchi/Cargo.toml",
        "[dependencies]",
        "tamil-morph.workspace = true",
        "tamil-punarchi \\(Rank 2\\): dependency tamil-morph \\(Rank 3\\) in \\[dependencies\\] violates acyclic DAG rank order",
    ),
    (
        "crates/tamil-collate/Cargo.toml",
        "[build-dependencies]",
        "tamil-hyphen.workspace = true",
        "tamil-collate \\(Rank 2\\): dependency tamil-hyphen \\(Rank 2\\) in \\[build-dependencies\\] violates acyclic DAG rank order",
    ),
    (
        "crates/tamil-norm/Cargo.toml",
        "[dev-dependencies]",
        "tamil-toolkit.workspace = true",
        "tamil-norm \\(Rank 1\\): dependency tamil-toolkit \\(Rank 5\\) in \\[dev-dependencies\\] violates acyclic DAG rank order",
    ),
])
def test_dag_rejects_reverse_and_peer_dependencies(repository, manifest_rel, section, dep_line, expected_match):
    manifest_path = repository / manifest_rel
    text = manifest_path.read_text(encoding="utf-8")
    if section in text:
        text = text.replace(section, f"{section}\n{dep_line}", 1)
    else:
        text = f"{text}\n{section}\n{dep_line}\n"
    manifest_path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=expected_match):
        gate.check(repository)


def test_dag_rejects_premature_empty_scaffold_for_planned_crates(repository):
    translit_dir = repository / "crates/tamil-translit"
    (translit_dir / "src").mkdir(parents=True)
    (translit_dir / "Cargo.toml").write_text(
        '[package]\nname = "tamil-translit"\nversion.workspace = true\npublish.workspace = true\n'
        'license.workspace = true\nrepository.workspace = true\n',
        encoding="utf-8",
    )
    (translit_dir / "src/lib.rs").write_text('pub const STATUS: &str = "planned";\n', encoding="utf-8")
    with pytest.raises(ValueError, match="unscaffolded planned crate cannot be created as an empty placeholder"):
        gate.check(repository)



@pytest.mark.parametrize("section", ["dependencies", "build-dependencies", "dev-dependencies"])
def test_target_dependency_alias_cannot_bypass_rank(repository, section):
    path = repository / "crates/tamil-core/Cargo.toml"
    with path.open("a") as out:
        out.write(f'\n[target.\'cfg(windows)\'.{section}]\nrenamed = {{ package = "tamil-norm", path = "../tamil-norm" }}\n')
    with pytest.raises(ValueError, match="violates acyclic DAG rank order"):
        gate.check_dependency_dag(repository)


def test_workspace_alias_cannot_bypass_rank(repository):
    path = repository / "Cargo.toml"
    text = path.read_text().replace("[workspace.dependencies]", '[workspace.dependencies]\nrenamed = { package = "tamil-norm", path = "crates/tamil-norm" }')
    path.write_text(text)
    path = repository / "crates/tamil-core/Cargo.toml"
    path.write_text(path.read_text().replace("[dev-dependencies]", "[dev-dependencies]\nrenamed.workspace = true"))
    with pytest.raises(ValueError, match="violates acyclic DAG rank order"):
        gate.check_dependency_dag(repository)


@pytest.mark.parametrize("name", sorted(gate.UNSCAFFOLDED_PLANNED_CRATES))
@pytest.mark.parametrize("source", [None, "", '// placeholder\n', 'pub const STATUS : &str= "planned" ;\n', '#![forbid(unsafe_code)]\npub static STATUS: &str = "planned";\n'])
def test_future_crate_placeholder_guard(repository, name, source):
    directory = repository / "crates" / name
    directory.mkdir()
    if source is not None:
        (directory / "src").mkdir()
        (directory / "src/lib.rs").write_text(source, encoding="utf-8")
        (directory / "Cargo.toml").write_text(f'[package]\nname = "{name}"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="empty placeholder"):
        gate.check_dependency_dag(repository)


@pytest.mark.parametrize("name", sorted(gate.UNSCAFFOLDED_PLANNED_CRATES))
def test_future_crate_implementation_allowed(repository, name):
    directory = repository / "crates" / name
    (directory / "src").mkdir(parents=True)
    (directory / "Cargo.toml").write_text(f'[package]\nname = "{name}"\n', encoding="utf-8")
    (directory / "src/lib.rs").write_text('pub const STATUS: &str = "planned";\npub fn operation() -> usize { 1 }\n', encoding="utf-8")
    gate.check_dependency_dag(repository)
