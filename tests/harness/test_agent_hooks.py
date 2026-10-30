import json
import subprocess
import sys

import pytest

from tools.agent_hook import ROOT, role_violation


@pytest.mark.parametrize("role,path,allowed", [
    ("rust-core-dev", "crates/tamil-core/src/lib.rs", True),
    ("rust-core-dev", "tests/golden/core_graphemes.jsonl", False),
    ("rust-core-dev", "crates/../../outside.rs", False),
    ("linguist-spec", "lexicon/core.toml", True),
    ("linguist-spec", "crates/tamil-core/src/lib.rs", False),
    ("bindings-sync", "bindings/js-wasm/src/api.ts", True),
    ("bindings-sync", "tests/golden/core_graphemes.jsonl", False),
])
def test_role_write_boundaries(role, path, allowed):
    event = {"agent_type": role, "tool_name": "Edit", "tool_input": {"file_path": path}}
    assert (role_violation(event) is None) == allowed


@pytest.mark.parametrize("command,allowed", [
    ("just test-rust", True),
    ("just test-rust; echo bypass", False),
    ("python -c 'write()'", False),
    ("just test-rust\njust sync-bindings", False),
])
def test_shell_write_bypass_is_rejected(command, allowed):
    event = {"agent_type": "rust-core-dev", "tool_name": "Bash", "tool_input": {"command": command}}
    assert (role_violation(event) is None) == allowed


def test_pre_tool_uses_claude_deny_contract():
    event = {"agent_type": "rust-core-dev", "tool_name": "Write", "tool_input": {"file_path": "tests/golden/x.jsonl"}}
    result = subprocess.run([sys.executable, str(ROOT / "tools/agent_hook.py"), "pre-tool"], input=json.dumps(event), capture_output=True, text=True, check=True)
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"


def test_stop_failure_maps_to_blocking_exit(monkeypatch, capsys):
    import tools.agent_hook as hook
    monkeypatch.setattr(sys, "argv", ["agent_hook.py", "stop"])
    import io
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"stop_hook_active": true}'))
    monkeypatch.setattr(hook.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 1, "failed gate", "reason"))
    assert hook.main() == 2
    assert "failed gate" in capsys.readouterr().err
