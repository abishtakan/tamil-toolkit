"""Release invariants: public scope and standalone build inputs, not Tamil rules."""

import json
import tomllib
from tools.harness import ROOT


PUBLIC = {"tamil-core", "tamil-norm", "tamil-collate", "tamil-numerals", "tamil-codec", "tamil-toolkit"}
VERSION = "0.1.0-alpha.1"
REPOSITORY = "https://github.com/abishtakan/tamil-toolkit"


def read_toml(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_alpha_scope_and_versions():
    workspace = read_toml(ROOT / "Cargo.toml")
    assert workspace["workspace"]["package"]["version"] == VERSION
    assert workspace["workspace"]["package"]["license"] == "MIT"
    assert workspace["workspace"]["package"]["repository"] == REPOSITORY
    umbrella = read_toml(ROOT / "crates/tamil-toolkit/Cargo.toml")
    assert {name for name in umbrella["dependencies"] if name.startswith("tamil-")} == PUBLIC - {"tamil-toolkit"}
    for path in (ROOT / "crates").glob("*/Cargo.toml"):
        manifest = read_toml(path)
        if manifest["package"]["name"] not in PUBLIC:
            assert manifest["package"].get("publish") in (False, {"workspace": True})
    assert workspace["workspace"]["package"]["publish"] is False
    assert read_toml(ROOT / "bindings/python/pyproject.toml")["project"]["version"] == "0.1.0a1"
    assert json.loads((ROOT / "bindings/js-wasm/package.json").read_text())["version"] == VERSION


def test_public_build_inputs_are_self_contained_and_canonical():
    inputs = {
        "tamil-core": ["core.toml"], "tamil-collate": ["collate.toml"],
        "tamil-numerals": ["numerals.toml", "numerals-formats.toml"],
        "tamil-codec": ["bamini.toml"],
    }
    for name, files in inputs.items():
        for filename in files:
            assert (ROOT / "crates" / name / "lexicon" / filename).read_bytes() == (ROOT / "lexicon" / filename).read_bytes()
    for name in PUBLIC:
        package = ROOT / "crates" / name
        assert (package / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
        assert (package / "THIRD_PARTY_NOTICES.md").read_bytes() == (ROOT / "THIRD_PARTY_NOTICES.md").read_bytes()
        assert (package / "README.md").is_file()
        for script in package.glob("build*.rs"):
            assert "../../lexicon/" not in script.read_text(encoding="utf-8")


def test_npm_archive_contract_includes_binary_and_type_outputs():
    package = json.loads((ROOT / "bindings/js-wasm/package.json").read_text())
    assert package["license"] == "MIT"
    assert package["repository"]["url"] == REPOSITORY + ".git"
    assert package["publishConfig"]["tag"] == "alpha"
    assert {"dist", "pkg-node", "pkg-web", "LICENSE", "THIRD_PARTY_NOTICES.md"} <= set(package["files"])
