"""Local stdio oracle. Rust owns segmentation; stdout belongs to MCP."""

import difflib
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mcp.server import MCPServer  # noqa: E402
from tools.harness import JOINERS, ROOT, validate_golden_schema as validate_file  # noqa: E402

mcp = MCPServer("mcp-tamil-oracle")


def scalar(char):
    return {"char": char, "hex": f"U+{ord(char):04X}", "name": unicodedata.name(char, "UNNAMED")}


@mcp.tool()
def inspect_tamil_string(text: str) -> dict:
    """Inspect original Unicode scalars, normalization, Rust Ezhuthu count/classes."""
    completed = subprocess.run(
        ["cargo", "run", "--quiet", "--locked", "-p", "tamil-toolkit", "--bin", "tamil-oracle"],
        input=json.dumps({"op": "inspect_tamil_string", "input": text}, ensure_ascii=True) + "\n",
        text=True, encoding="utf-8", capture_output=True, cwd=ROOT, check=True,
    )
    result = json.loads(completed.stdout)
    result["scalars"] = [{"index": index, **scalar(char)} for index, char in enumerate(text)]
    result["joiners"] = [index for index, char in enumerate(text) if char in JOINERS]
    return result


@mcp.tool()
def inspect_codepoints(text: str) -> dict:
    """Alias for inspect_tamil_string, retained for agent-constitution compatibility."""
    return inspect_tamil_string(text)


@mcp.tool()
def diff_tamil_outputs(expected: str, actual: str) -> dict:
    """Align by Unicode scalar, exposing invisible changes and canonical equivalence."""
    differences = []
    for kind, left, left_end, right, right_end in difflib.SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes():
        if kind != "equal":
            differences.append({
                "kind": kind, "expected_range": [left, left_end], "actual_range": [right, right_end],
                "expected": [scalar(c) for c in expected[left:left_end]],
                "actual": [scalar(c) for c in actual[right:right_end]],
            })
    return {"equal": expected == actual, "canonically_equivalent": unicodedata.normalize("NFC", expected) == unicodedata.normalize("NFC", actual), "differences": differences}


@mcp.tool()
def validate_golden_schema(file_path: str) -> dict:
    """Validate metadata, scalars, scoped Unicode exceptions, and globally unique IDs."""
    return validate_file(file_path)


if __name__ == "__main__":
    mcp.run()
