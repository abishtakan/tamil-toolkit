"""Exercise real initialization, tool listing, and calls over MCP stdio."""

import asyncio
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tools.harness import ROOT, load_vectors


def test_mcp_stdio_tools():
    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "tools/mcp-tamil-oracle/server.py")], cwd=str(ROOT))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                listing = await client.list_tools()
                assert {tool.name for tool in listing.tools} == {
                    "inspect_tamil_string", "inspect_codepoints", "diff_tamil_outputs", "validate_golden_schema",
                }
                case = load_vectors()[0]
                result = await client.call_tool("inspect_tamil_string", {"text": case["input"]})
                assert not result.is_error
                result = await client.call_tool("diff_tamil_outputs", {"expected": "a", "actual": "a"})
                assert not result.is_error
                result = await client.call_tool("validate_golden_schema", {"file_path": "tests/golden/core_graphemes.jsonl"})
                assert not result.is_error
                result = await client.call_tool("validate_golden_schema", {"file_path": "../outside.jsonl"})
                assert result.is_error
    asyncio.run(exercise())
