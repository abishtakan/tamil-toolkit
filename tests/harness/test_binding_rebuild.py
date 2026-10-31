"""Prevent stale interpreter-specific extensions from shadowing rebuilds."""

from tools import tasks


def test_sync_bindings_removes_only_old_native_extensions(tmp_path, monkeypatch):
    package = tmp_path / "bindings/python/python/tamil_toolkit"
    package.mkdir(parents=True)
    stale = [package / "_native.cp314-win_amd64.pyd", package / "_native.cpython-314-x86_64.so"]
    for artifact in stale:
        artifact.write_bytes(b"old")
    keep = package / "__init__.py"
    keep.write_text("", encoding="utf-8")
    monkeypatch.setattr(tasks, "ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(tasks, "run", lambda *args, **kwargs: calls.append(args))
    tasks.sync_bindings()
    assert all(not artifact.exists() for artifact in stale)
    assert keep.exists()
    assert any(call[0] == "maturin" for call in calls)
