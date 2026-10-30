# tamil-toolkit for TypeScript / WASM

`just sync-bindings` produces Node and browser WASM builds and TypeScript
declarations. Node: `import * as tamil from 'tamil-toolkit'`. Browser:
`import { init, get_letters } from 'tamil-toolkit/web'; await init();`.
These adapters serialize calls into the shared Rust dispatcher. Planned modules
have no JavaScript fallback. Publishing is disabled during bootstrap.

Both entry points expose `compare`, `sort_words`, `sort_key`, and `search_key`.
Use the comparison result or numeric-array keys for ordering; comparing their
JSON string representation is incorrect. The versioned `agara-v1` profile and
its mixed-script fallback are specified in docs/specs/collate-v0.1.md.
