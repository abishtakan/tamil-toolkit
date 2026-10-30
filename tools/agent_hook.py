"""Claude command hook adapter. Exit 2 makes command failures block completion."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "linguist-spec": ("tests/golden", "lexicon", "docs/specs"),
    "rust-core-dev": ("crates",),
    "bindings-sync": ("bindings/python", "bindings/js-wasm", "bindings/dart-flutter"),
}
VERIFY = {"just " + task for task in (
    "check-unicode", "test-harness", "test-rust", "sync-bindings", "test-parity", "test-dart",
)}
READ_TOOLS = {"Read", "Glob", "Grep", "WebSearch", "WebFetch", "ToolSearch"}


def role_violation(event):
    roots = ROLES.get(event.get("agent_type"))
    if roots is None:
        return None
    tool = event.get("tool_name", "")
    inputs = event.get("tool_input", {})
    if tool in READ_TOOLS or tool.startswith("mcp__tamil-oracle__") or tool.startswith("mcp__tamil_oracle__"):
        return None
    if tool == "Bash":
        if inputs.get("command", "").strip() in VERIFY:
            return None
        return "This role may run only exact approved just verification commands; use scoped Write/Edit tools for changes."
    if tool in {"Write", "Edit"}:
        raw = inputs.get("file_path", "")
        if raw:
            path = Path(raw)
            path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
            if any(path.is_relative_to((ROOT / root).resolve()) for root in roots):
                return None
        return f"{event['agent_type']} may write only: {', '.join(roots)}"
    return f"Tool {tool} is outside this role's approved tool surface."


def main():
    mode = sys.argv[1]
    event = json.load(sys.stdin)
    if mode == "pre-tool":
        violation = role_violation(event)
        if violation:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": violation,
            }}))
        return 0
    task = {"post-edit": "agent-post-edit", "stop": "agent-pre-stop-gate"}[mode]
    result = subprocess.run(
        ["uv", "run", "--locked", "python", "tools/tasks.py", task], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        print(result.stdout + result.stderr, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as error:
        print(f"Agent hook failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
