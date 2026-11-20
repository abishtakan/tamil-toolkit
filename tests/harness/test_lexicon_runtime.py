"""Runtime contract fixtures, schema/feature invariants, and adapter serialization tests for Feature 021 (Lexicon).

IMPORTANT: These tests verify:
1. Escaped runtime contract fixtures (`tests/reference/lexicon/runtime/contract_cases.json`),
2. Closed response schema compliance on planned golden vectors (`tests/golden/lexicon_lookup.jsonl`),
3. Off-default Cargo feature forwarding across Python, TS/WASM, and Dart binding crates, and
4. Pure wrapper request serialization & API signature parity (without Rust execution).

Actual native Rust/PyO3/WASM/Dart runtime parity is NOT mocked or skipped here;
it is deferred to root integration after `cargo` / binding rebuilds (`T061`/`T062`).
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path
from unittest.mock import patch

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON_PKG_DIR = REPO_ROOT / "bindings" / "python" / "python"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(PYTHON_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_PKG_DIR))

import harness  # noqa: E402
import tamil_toolkit  # noqa: E402
import tasks  # noqa: E402
import release  # noqa: E402


CONTRACT_CASES_PATH = REPO_ROOT / "tests" / "reference" / "lexicon" / "runtime" / "contract_cases.json"
GOLDEN_LEXICON_PATH = REPO_ROOT / "tests" / "golden" / "lexicon_lookup.jsonl"
LOOKUP_RESPONSE_SCHEMA_PATH = (
    REPO_ROOT / "specs" / "021-lexicon-curation" / "contracts" / "lookup-response.schema.json"
)
_CORE_MANIFEST = tasks.load_pack_manifest("core")
EXPECTED_CORE_DATASET_VERSION = _CORE_MANIFEST["dataset_version"]
EXPECTED_CORE_MANIFEST_SHA256 = _CORE_MANIFEST["manifest_sha256"]
FORWARDED_LEXICON_FEATURES = (
    "lexicon-core",
    "lexicon-terminology",
    "lexicon-names-taxa",
    "lexicon-regional",
)
CONTRACT_ERROR_PATTERNS = (
    re.compile(r"^lexicon: input must be a string$"),
    re.compile(r"^lexicon: input exceeds 65536 UTF-8 bytes$"),
    re.compile(r"^lexicon: invalid options$"),
    re.compile(r"^lexicon: packs must be a nonempty string array$"),
    re.compile(r"^lexicon: unknown pack '[^']+'$"),
    re.compile(r"^lexicon: pack unavailable '[^']+'$"),
    re.compile(r"^lexicon: unknown region '[^']+'$"),
    re.compile(r"^lexicon: unknown register '[^']+'$"),
    re.compile(r"^lexicon: incompatible pack versions$"),
)


def _materialize_input(case: dict) -> object:
    if "request" in case:
        return case["request"]["input"]
    spec = case["request_template"]["input_spec"]
    return spec["unit"] * spec["repeat"] + spec["suffix"]


def test_runtime_contract_fixtures_are_escaped_and_complete() -> None:
    raw = CONTRACT_CASES_PATH.read_text(encoding="utf-8")
    assert raw.isascii(), "runtime contract fixtures must use escaped ASCII \\uXXXX sequences"

    doc = json.loads(raw)
    assert doc["schema_version"] == 1
    assert doc["max_input_utf8_bytes"] == 65536
    assert doc["default_packs"] == ["core"]
    assert doc["known_pack_ids"] == ["core", "terminology", "names_taxa", "regional"]

    profiles = {p["id"]: p for p in doc["profiles"]}
    assert profiles["default_zero"]["cargo_features"] == []
    assert profiles["default_zero"]["expected_packs"] == []
    assert profiles["lexicon_core"]["cargo_features"] == ["lexicon-core"]
    assert profiles["lexicon_core"]["expected_core_dataset_version"].startswith("0.1.0+")
    assert len(profiles["lexicon_core"]["expected_core_manifest_sha256"]) == 64

    cases = {c["id"]: c for c in doc["cases"]}
    assert len(cases) == 23

    # Verify exact 65,536 vs 65,537 UTF-8 byte boundary inputs.
    boundary_ok = _materialize_input(cases["runtime_lookup_boundary_65536_bytes_006"])
    boundary_err = _materialize_input(cases["runtime_lookup_err_exceeds_65536_bytes_007"])
    assert isinstance(boundary_ok, str) and len(boundary_ok.encode("utf-8")) == 65536
    assert isinstance(boundary_err, str) and len(boundary_err.encode("utf-8")) == 65537

    # Verify every expected error conforms strictly to the documented contract taxonomy.
    errors_seen: list[str] = []
    for case in doc["cases"]:
        err = case.get("expected_error")
        if err is not None:
            errors_seen.append(err)
            assert any(pat.match(err) for pat in CONTRACT_ERROR_PATTERNS), (
                f"{case['id']}: unrecognized contract error {err!r}"
            )

    # Confirm coverage of every required contract category.
    assert any("unknown_option" in cid for cid in cases)
    assert any("packs_empty" in cid for cid in cases)
    assert any("incompatible_pack_versions" in cid for cid in cases)
    assert any("not_found_vs_unavailable" in cid for cid in cases)
    assert any("zwj_preserved" in cid for cid in cases)
    assert any("order_non_string_input_before_options" in cid for cid in cases)
    assert any("order_oversize_input_before_options" in cid for cid in cases)
    assert any("unknown_region" in cid for cid in cases)
    assert any("unknown_register" in cid for cid in cases)
    assert any(e == "lexicon: incompatible pack versions" for e in errors_seen)


def test_planned_golden_vectors_match_closed_lookup_response_schema() -> None:
    raw = GOLDEN_LEXICON_PATH.read_text(encoding="utf-8")
    assert raw.isascii(), "tests/golden/lexicon_lookup.jsonl must remain ASCII-escaped"

    rows = harness.validate_rows(GOLDEN_LEXICON_PATH)
    assert len(rows) == 44

    response_schema = json.loads(LOOKUP_RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(response_schema)

    lookup_positive = [r for r in rows if r["op"] == "lexicon_lookup" and "expected" in r]
    assert lookup_positive, "expected positive lexicon_lookup golden cases"
    for row in lookup_positive:
        validator.validate(row["expected"])

    packs_rows = [r for r in rows if r["id"] == "lexicon_packs_core_043"]
    assert len(packs_rows) == 1
    core_pack = packs_rows[0]["expected"][0]
    assert core_pack["id"] == "core"
    assert core_pack["dataset_version"].startswith("0.1.0+")
    assert core_pack["schema_version"] == 1
    assert len(core_pack["manifest_sha256"]) == 64
    assert core_pack["available"] is True


def test_binding_crates_forward_off_default_lexicon_features() -> None:
    binding_manifests = [
        REPO_ROOT / "bindings" / "python" / "Cargo.toml",
        REPO_ROOT / "bindings" / "js-wasm" / "Cargo.toml",
        REPO_ROOT / "bindings" / "dart-flutter" / "rust" / "Cargo.toml",
    ]
    for manifest_path in binding_manifests:
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["package"]["publish"] == {"workspace": True} or manifest["package"].get("publish") is True
        features = manifest.get("features", {})
        assert features.get("default") == [], f"{manifest_path}: default features must stay empty"
        for feat in FORWARDED_LEXICON_FEATURES:
            assert features.get(feat) == [f"tamil-toolkit/{feat}"], (
                f"{manifest_path}: missing feature forwarder {feat} -> tamil-toolkit/{feat}"
            )

    py_manifest = tomllib.loads(binding_manifests[0].read_text(encoding="utf-8"))
    assert py_manifest["features"].get("extension-module") == ["pyo3/extension-module"]


def test_python_adapter_request_serialization_and_stub_parity() -> None:
    """Serialization-only check of Python thin wrappers (not a Rust runtime pass)."""
    assert "lexicon_lookup" in tamil_toolkit.__all__
    assert "lexicon_packs" in tamil_toolkit.__all__

    # Verify request serialization shapes sent to tamil_toolkit.execute without altering inputs/outputs.
    sent_requests: list[dict] = []

    def capture_execute(payload: dict):
        sent_requests.append(payload)
        return {"sentinel": True, "payload_echo": payload}

    with patch.object(tamil_toolkit, "execute", side_effect=capture_execute):
        # Default call omits packs/region/register so Rust applies default ["core"].
        zwj_word = f"\u0ba8\u0ba9\u0bcd{chr(0x200D)}\u0bb1\u0bbf"
        tamil_toolkit.lexicon_lookup(zwj_word)
        assert sent_requests[-1] == {
            "op": "lexicon_lookup",
            "input": zwj_word,
        }

        # Explicit options are forwarded verbatim without coercion, NFC, or joiner stripping.
        tamil_toolkit.lexicon_lookup(
            "\u0b85\u0b9f\u0b9f\u0bbe",
            packs=["core", "regional"],
            region="IN-TN",
            register="formal",
        )
        assert sent_requests[-1] == {
            "op": "lexicon_lookup",
            "input": "\u0b85\u0b9f\u0b9f\u0bbe",
            "packs": ["core", "regional"],
            "region": "IN-TN",
            "register": "formal",
        }

        # Empty/malformed packs values must pass straight through to Rust validation.
        tamil_toolkit.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=[])
        assert sent_requests[-1] == {
            "op": "lexicon_lookup",
            "input": "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
            "packs": [],
        }

        # lexicon_packs passes null input.
        tamil_toolkit.lexicon_packs()
        assert sent_requests[-1] == {"op": "lexicon_packs", "input": None}

    # Verify .pyi stub exports typed signatures & closed schema TypedDicts.
    pyi_path = PYTHON_PKG_DIR / "tamil_toolkit" / "__init__.pyi"
    pyi_tree = ast.parse(pyi_path.read_text(encoding="utf-8"))
    defined_classes = {node.name for node in pyi_tree.body if isinstance(node, ast.ClassDef)}
    defined_funcs = {node.name: node for node in pyi_tree.body if isinstance(node, ast.FunctionDef)}
    for required_cls in (
        "LexiconAcceptance",
        "LexiconProvenance",
        "LexiconScope",
        "LexiconField",
        "LexiconLabelField",
        "LexiconAnnotation",
        "LexiconForm",
        "LexiconComponentText",
        "LexiconExampleText",
        "LexiconEndpoint",
        "LexiconRelation",
        "LexiconSense",
        "LexiconEntry",
        "LexiconCoverage",
        "LexiconPackInfo",
        "LexiconLookupResponse",
    ):
        assert required_cls in defined_classes
    assert {"lexicon_lookup", "lexicon_packs"}.issubset(defined_funcs.keys())
    kw_args = [arg.arg for arg in defined_funcs["lexicon_lookup"].args.kwonlyargs]
    assert kw_args == ["packs", "region", "register"]


def test_ts_and_dart_adapter_exports_and_shapes() -> None:
    """Static source verification for TS/WASM and Dart thin adapters."""
    api_ts = (REPO_ROOT / "bindings" / "js-wasm" / "src" / "api.ts").read_text(encoding="utf-8")
    index_ts = (REPO_ROOT / "bindings" / "js-wasm" / "src" / "index.ts").read_text(encoding="utf-8")
    web_ts = (REPO_ROOT / "bindings" / "js-wasm" / "src" / "web.ts").read_text(encoding="utf-8")
    dart_lib = (REPO_ROOT / "bindings" / "dart-flutter" / "lib" / "tamil_toolkit.dart").read_text(
        encoding="utf-8"
    )

    for symbol in (
        "LexiconLookupOptions",
        "LexiconPackInfo",
        "LexiconLookupResponse",
        "lexicon_lookup",
        "lexicon_packs",
    ):
        assert symbol in api_ts
        assert symbol in index_ts
        assert symbol in web_ts

    assert 'op: "lexicon_lookup"' in api_ts
    assert 'op: "lexicon_packs", input: null' in api_ts
    assert "Map<String, dynamic> lexiconLookup(" in dart_lib
    assert "List<Map<String, dynamic>> lexiconPacks()" in dart_lib
    assert "'op': 'lexicon_lookup'" in dart_lib
    assert "'op': 'lexicon_packs', 'input': null" in dart_lib


def test_tasks_lexicon_profile_resolution_and_command_forwarding() -> None:
    """T061: verify default vs core profile resolution, manifest check, and CLI flags."""
    import pytest

    default_profile = tasks.resolve_lexicon_profile("default")
    assert default_profile.name == "default"
    assert default_profile.features == ()
    assert default_profile.expected_packs == ()
    assert default_profile.planned_suites == ()
    assert default_profile.manifest_sha256 is None

    core_profile = tasks.resolve_lexicon_profile("core")
    assert core_profile.name == "core"
    assert core_profile.features == ("lexicon-core",)
    assert core_profile.expected_packs == ("core",)
    assert core_profile.planned_suites == ()
    assert tasks.resolve_lexicon_profile().name == "core"
    assert core_profile.dataset_version == EXPECTED_CORE_DATASET_VERSION
    assert core_profile.manifest_sha256 == EXPECTED_CORE_MANIFEST_SHA256

    # Alias resolves identically and unknown profiles fail loudly.
    assert tasks.resolve_lexicon_profile("lexicon-core") == core_profile
    full_profile = tasks.resolve_lexicon_profile("full")
    assert full_profile.name == "full"
    assert full_profile.features == ("lexicon-core", "lexicon-names-taxa", "lexicon-regional")
    assert full_profile.expected_packs == ("core", "names_taxa", "regional")
    assert full_profile.planned_suites == ()
    assert tasks.resolve_lexicon_profile("lexicon-full") == full_profile
    full_manifests = {
        pack_id: tasks.load_pack_manifest(pack_id)
        for pack_id in ("core", "names_taxa", "regional")
    }
    assert full_profile.dataset_version == full_manifests["core"]["dataset_version"]
    assert full_profile.manifest_sha256 == full_manifests["core"]["manifest_sha256"]
    assert dict(full_profile.pack_manifests_map()) == {
        pack_id: {
            "dataset_version": m["dataset_version"],
            "manifest_sha256": m["manifest_sha256"],
        }
        for pack_id, m in full_manifests.items()
    }
    with pytest.raises(ValueError, match="Unsupported or unapproved lexicon profile"):
        tasks.resolve_lexicon_profile("bogus-profile")
    with pytest.raises(ValueError, match="Unsupported or unapproved lexicon profile"):
        tasks.resolve_lexicon_profile("terminology")

    # Feature forwarding commands keep zero payload for default and forward core/full features.
    assert tasks.maturin_feature_args(default_profile) == []
    assert tasks.maturin_feature_args(core_profile) == [
        "--features",
        "extension-module,lexicon-core",
    ]
    assert tasks.maturin_feature_args(full_profile) == [
        "--features",
        "extension-module,lexicon-core,lexicon-names-taxa,lexicon-regional",
    ]
    assert tasks.cargo_feature_args(default_profile) == []
    assert tasks.cargo_feature_args(core_profile) == ["--features", "lexicon-core"]
    assert tasks.cargo_feature_args(full_profile) == [
        "--features",
        "lexicon-core,lexicon-names-taxa,lexicon-regional",
    ]
    assert tasks.wasm_pack_build_command(core_profile, "nodejs", "pkg-node", release=True)[-2:] == [
        "--features",
        "lexicon-core",
    ]
    assert tasks.wasm_pack_build_command(full_profile, "nodejs", "pkg-node", release=True)[-2:] == [
        "--features",
        "lexicon-core,lexicon-names-taxa,lexicon-regional",
    ]
    assert "--features" not in tasks.wasm_pack_build_command(default_profile, "nodejs", "pkg-node")

    # Profile env forbids accidentally mixing default or full profile with core-only lexicon_lookup.jsonl.
    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        tasks.profile_env(
            default_profile,
            base_env={"TAMIL_GOLDEN_INCLUDE_PLANNED": "lexicon_lookup.jsonl"},
        )
    with pytest.raises(ValueError, match="lexicon_lookup.jsonl"):
        tasks.profile_env(
            full_profile,
            base_env={"TAMIL_GOLDEN_INCLUDE_PLANNED": "lexicon_lookup.jsonl"},
        )
    core_env = tasks.profile_env(core_profile, include_planned=True, base_env={})
    assert core_env["TAMIL_LEXICON_PROFILE"] == "core"
    assert core_env["TAMIL_LEXICON_FEATURES"] == "lexicon-core"
    assert core_env["TAMIL_LEXICON_MANIFEST_SHA256"] == EXPECTED_CORE_MANIFEST_SHA256
    assert "TAMIL_GOLDEN_INCLUDE_PLANNED" not in core_env
    full_env = tasks.profile_env(full_profile, include_planned=True, base_env={})
    assert full_env["TAMIL_LEXICON_PROFILE"] == "full"
    assert full_env["TAMIL_LEXICON_FEATURES"] == "lexicon-core,lexicon-names-taxa,lexicon-regional"
    assert full_env["TAMIL_LEXICON_EXPECTED_PACKS"] == "core,names_taxa,regional"
    assert json.loads(full_env["TAMIL_LEXICON_PACK_MANIFESTS"]) == full_profile.pack_manifests_map()
    assert "TAMIL_GOLDEN_INCLUDE_PLANNED" not in full_env


def test_release_consumer_profile_forwarding_and_fixtures(tmp_path: Path, monkeypatch) -> None:
    """T061: verify isolated archive consumer Cargo manifest and planned fixture export."""
    default_profile = tasks.resolve_lexicon_profile("default")
    core_profile = tasks.resolve_lexicon_profile("core")
    full_profile = tasks.resolve_lexicon_profile("full")
    extracted = {"tamil-toolkit": tmp_path / "crates" / "tamil-toolkit-0.1.0"}

    default_cargo = release.consumer_cargo_toml("0.1.0-alpha.7", extracted, default_profile)
    assert 'tamil-toolkit = "=0.1.0-alpha.7"' in default_cargo
    assert "lexicon-core" not in default_cargo

    core_cargo = release.consumer_cargo_toml("0.1.0-alpha.7", extracted, core_profile)
    assert 'tamil-toolkit = { version = "=0.1.0-alpha.7", features = ["lexicon-core"] }' in core_cargo

    full_cargo = release.consumer_cargo_toml("0.1.0-alpha.7", extracted, full_profile)
    assert (
        'tamil-toolkit = { version = "=0.1.0-alpha.7", '
        'features = ["lexicon-core", "lexicon-names-taxa", "lexicon-regional"] }'
    ) in full_cargo

    manifest = json.loads((REPO_ROOT / "tests" / "golden" / "manifest.json").read_text(encoding="utf-8"))
    baseline_expected = sum(
        len((REPO_ROOT / "tests" / "golden" / s["file"]).read_text(encoding="utf-8").splitlines())
        for s in manifest["suites"]
        if s["status"] == "active" and s.get("required_profile") is None
    )
    core_expected = sum(
        len((REPO_ROOT / "tests" / "golden" / s["file"]).read_text(encoding="utf-8").splitlines())
        for s in manifest["suites"]
        if s["status"] == "active" and s.get("required_profile") == "core"
    )
    full_expected = sum(
        len((REPO_ROOT / "tests" / "golden" / s["file"]).read_text(encoding="utf-8").splitlines())
        for s in manifest["suites"]
        if s["status"] == "active" and s.get("required_profile") == "full"
    )

    # Explicit profile selection keeps default baseline, core, and full exports strictly exact.
    monkeypatch.delenv("TAMIL_GOLDEN_INCLUDE_PLANNED", raising=False)
    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "core")
    default_out = tmp_path / "default_fixtures"
    default_out.mkdir()
    default_jsonl = release.fixtures(default_out, profile="default")
    default_ids = {json.loads(line)["id"] for line in default_jsonl.read_text(encoding="utf-8").splitlines()}
    assert len(default_ids) == baseline_expected
    assert "lexicon_lookup_atataa_001" not in default_ids

    monkeypatch.setenv("TAMIL_LEXICON_PROFILE", "default")
    core_out = tmp_path / "core_fixtures"
    core_out.mkdir()
    core_jsonl = release.fixtures(core_out, profile="core", extra_planned=core_profile.planned_suites)
    core_ids = {json.loads(line)["id"] for line in core_jsonl.read_text(encoding="utf-8").splitlines()}
    assert len(core_ids) == baseline_expected + core_expected
    assert "lexicon_lookup_atataa_001" in core_ids
    assert "lexicon_packs_err_invalid_input_044" in core_ids

    full_out = tmp_path / "full_fixtures"
    full_out.mkdir()
    full_jsonl = release.fixtures(full_out, profile="full", extra_planned=full_profile.planned_suites)
    full_ids = {json.loads(line)["id"] for line in full_jsonl.read_text(encoding="utf-8").splitlines()}
    assert len(full_ids) == baseline_expected + full_expected
    assert "lexicon_lookup_atataa_001" not in full_ids
    assert "lexicon_packs_core_043" not in full_ids


def test_harnesses_and_smoke_consumers_verify_lexicon_profile_and_manifest() -> None:
    """T061: static source verification that all parity/smoke runners check profile, full, and absent fixture."""
    rust_absent = "\\u{0b87}\\u{0bb2}\\u{0bcd}\\u{0bb2}\\u{0bbe}\\u{0ba4}\\u{0b9a}\\u{0bca}\\u{0bb2}\\u{0bcd}"
    py_ts_dart_absent = "\\u0b87\\u0bb2\\u0bcd\\u0bb2\\u0bbe\\u0ba4\\u0b9a\\u0bca\\u0bb2\\u0bcd"
    stale_rust = "\\u{0b9a}\\u{0bc6}\\u{0baf}\\u{0bb1}\\u{0bcd}\\u{0b95}\\u{0bc8}"
    stale_escaped = "\\u0b9a\\u0bc6\\u0baf\\u0bb1\\u0bcd\\u0b95\\u0bc8"
    stale_literal = stale_escaped.encode("ascii").decode("unicode_escape")

    expected_checks = {
        REPO_ROOT / "crates" / "tamil-toolkit" / "tests" / "golden_suite.rs": (
            "TAMIL_LEXICON_PROFILE",
            "packs.toml",
            "lexicon_packs",
            "lexicon_lookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            '"full"',
            "absent_golden_input()",
            "lexicon_lookup_not_found_absent_007",
        ),
        REPO_ROOT / "bindings" / "python" / "tests" / "test_golden.py": (
            "TAMIL_LEXICON_PROFILE",
            "packs.toml",
            "lexicon_packs",
            "lexicon_lookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            '"full"',
            "lexicon_lookup_not_found_absent_007",
            "_absent_golden_input()",
        ),
        REPO_ROOT / "bindings" / "js-wasm" / "tests" / "golden.test.ts": (
            "TAMIL_LEXICON_PROFILE",
            "packs.toml",
            "lexicon_packs",
            "lexicon_lookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            '"full"',
            "lexicon_lookup_not_found_absent_007",
            "absentGoldenInput()",
        ),
        REPO_ROOT / "bindings" / "dart-flutter" / "test" / "golden_test.dart": (
            "TAMIL_LEXICON_PROFILE",
            "packs.toml",
            "lexiconPacks",
            "lexiconLookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            "'full'",
            "lexicon_lookup_not_found_absent_007",
            "_absentGoldenInput(",
        ),
        REPO_ROOT / "tools" / "release_smoke" / "rust_consumer.rs": (
            "TAMIL_LEXICON_PROFILE",
            "TAMIL_LEXICON_MANIFEST_SHA256",
            "TAMIL_LEXICON_PACK_MANIFESTS",
            "lexicon_packs",
            "lexicon_lookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            '"full"',
            rust_absent,
        ),
        REPO_ROOT / "tools" / "release_smoke" / "python_consumer.py": (
            "TAMIL_LEXICON_PROFILE",
            "TAMIL_LEXICON_MANIFEST_SHA256",
            "TAMIL_LEXICON_PACK_MANIFESTS",
            "lexicon_packs",
            "lexicon_lookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            '"full"',
            py_ts_dart_absent,
        ),
        REPO_ROOT / "tools" / "release_smoke" / "node_consumer.mjs": (
            "TAMIL_LEXICON_PROFILE",
            "TAMIL_LEXICON_MANIFEST_SHA256",
            "TAMIL_LEXICON_PACK_MANIFESTS",
            "lexicon_packs",
            "lexicon_lookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            '"full"',
            py_ts_dart_absent,
        ),
        REPO_ROOT / "tools" / "release_smoke" / "dart_consumer.dart": (
            "lexiconPacks",
            "lexiconLookup",
            "lexicon: pack unavailable 'core'",
            "terminology",
            "names_taxa",
            "regional",
            "'full'",
            py_ts_dart_absent,
        ),
        REPO_ROOT / "tools" / "release_smoke" / "types_consumer.ts": (
            "lexicon_lookup",
            "lexicon_packs",
            "LexiconLookupResponse",
            "LexiconPackInfo",
            "names_taxa",
            "regional",
        ),
    }
    for path, tokens in expected_checks.items():
        text = path.read_text(encoding="utf-8")
        assert stale_rust not in text, f"{path}: still hardcodes stale seyaRkai absent fixture"
        assert stale_escaped not in text, f"{path}: still hardcodes stale seyaRkai absent fixture"
        assert stale_literal not in text, f"{path}: still hardcodes stale seyaRkai absent fixture"
        for token in tokens:
            assert token in text, f"{path}: missing T061 verification token {token!r}"
