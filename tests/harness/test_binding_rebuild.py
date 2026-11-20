"""Prevent stale interpreter-specific extensions from shadowing rebuilds."""

from tools import tasks


def test_sync_bindings_removes_only_old_native_extensions(tmp_path, monkeypatch):
    from types import SimpleNamespace

    package = tmp_path / "bindings/python/python/tamil_toolkit"
    package.mkdir(parents=True)
    stale = [package / "_native.cp314-win_amd64.pyd", package / "_native.cpython-314-x86_64.so"]
    for artifact in stale:
        artifact.write_bytes(b"old")
    keep = package / "__init__.py"
    keep.write_text("", encoding="utf-8")
    monkeypatch.setattr(tasks, "ROOT", tmp_path)
    monkeypatch.setattr(tasks.shutil, "disk_usage", lambda _path: SimpleNamespace(free=100 * 1024**3))
    calls = []
    monkeypatch.setattr(tasks, "run", lambda *args, **kwargs: calls.append(args))
    tasks.sync_bindings()
    assert all(not artifact.exists() for artifact in stale)
    assert keep.exists()
    assert any(call[0] == "maturin" for call in calls)


def test_workspace_rust_profile_matches_selected_planned_suite(monkeypatch):
    calls = []
    monkeypatch.setattr(tasks, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(tasks.shutil, "which", lambda _name: "cargo-nextest")
    tasks.test_rust(profile="core")
    workspace = [(args, kwargs) for args, kwargs in calls if "--workspace" in args]
    assert workspace
    for args, kwargs in workspace:
        assert "--features" in args and "lexicon-core" in args
        assert "TAMIL_GOLDEN_INCLUDE_PLANNED" not in kwargs["extra_env"]
        assert kwargs["extra_env"]["TAMIL_LEXICON_PROFILE"] == "core"


def test_workspace_rust_default_profile_keeps_zero_payload(monkeypatch):
    calls = []
    monkeypatch.setattr(tasks, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(tasks.shutil, "which", lambda _name: "cargo-nextest")
    tasks.test_rust(profile="default")
    workspace = [(args, kwargs) for args, kwargs in calls if "--workspace" in args]
    assert workspace
    for args, kwargs in workspace:
        assert "--features" not in args
        assert kwargs["extra_env"]["TAMIL_LEXICON_PROFILE"] == "default"
        assert kwargs["extra_env"]["TAMIL_LEXICON_FEATURES"] == ""
        assert kwargs["extra_env"]["TAMIL_LEXICON_EXPECTED_PACKS"] == ""


def test_workspace_rust_implicit_canonical_profile_is_core(monkeypatch):
    monkeypatch.delenv("TAMIL_LEXICON_PROFILE", raising=False)
    calls = []
    monkeypatch.setattr(tasks, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(tasks.shutil, "which", lambda _name: "cargo-nextest")
    tasks.test_rust()
    workspace = [(args, kwargs) for args, kwargs in calls if "--workspace" in args]
    assert workspace
    for args, kwargs in workspace:
        assert "--features" in args and "lexicon-core" in args
        assert kwargs["extra_env"]["TAMIL_LEXICON_PROFILE"] == "core"


def test_workspace_rust_full_profile_forwards_all_three_packs(monkeypatch):
    import json

    calls = []
    monkeypatch.setattr(tasks, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(tasks.shutil, "which", lambda _name: "cargo-nextest")
    tasks.test_rust(profile="full")
    workspace = [(args, kwargs) for args, kwargs in calls if "--workspace" in args]
    assert workspace
    for args, kwargs in workspace:
        assert "--features" in args and "lexicon-core,lexicon-names-taxa,lexicon-regional" in args
        assert "TAMIL_GOLDEN_INCLUDE_PLANNED" not in kwargs["extra_env"]
        assert kwargs["extra_env"]["TAMIL_LEXICON_PROFILE"] == "full"
        assert kwargs["extra_env"]["TAMIL_LEXICON_EXPECTED_PACKS"] == "core,names_taxa,regional"
        pack_manifests = json.loads(kwargs["extra_env"]["TAMIL_LEXICON_PACK_MANIFESTS"])
        assert sorted(pack_manifests) == ["core", "names_taxa", "regional"]


def test_strict_vector_projection_preserves_request_options():
    from tools.harness import vector_request
    case = {"id": "fixture", "op": "lexicon_lookup", "input": "x", "packs": ["core"],
            "region": None, "register": None, "dialect": "COMMON", "tags": [],
            "source": {}, "expected": {}, "unicode_exceptions": [], "unknown_option": 1}
    request = vector_request(case)
    assert request == {"op": "lexicon_lookup", "input": "x", "packs": ["core"],
                       "region": None, "register": None, "unknown_option": 1}
    assert "id" in case  # projection cannot alter the fixture or its expected outcome
