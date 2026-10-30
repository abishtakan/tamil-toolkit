# mcp-tamil-oracle

Run from the repo root: `uv run --locked python tools/mcp-tamil-oracle/server.py`.
`.mcp.json` registers this stdio server with compatible clients. Ensure Cargo is
on PATH; `just bootstrap` builds the Rust code and installs Python dependencies.
Other clients may need the same command added in their own MCP configuration.

Tools: `inspect_tamil_string`, `inspect_codepoints` (alias),
`diff_tamil_outputs`, and `validate_golden_schema`.

Inspection calls the current Rust dispatcher through `cargo run --locked`, so
there is no separately implemented Python Tamil segmenter or stale binary.
Original scalar data remains distinct from normalized letter output. Diff
indices count Unicode scalars, not bytes or UTF-16 code units. Schema validation
is confined to this repository's golden directory and checks IDs across files.

The small server uses the [official MCP Python SDK](https://py.sdk.modelcontextprotocol.io/).
Protocol framing, initialization, and tool schemas are provided by the SDK.
