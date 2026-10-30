# tamil-toolkit for TypeScript / WASM

`just sync-bindings` produces Node and browser WASM builds and TypeScript
declarations. Node: `import * as tamil from 'tamil-toolkit'`. Browser:
`import { init, get_letters } from 'tamil-toolkit/web'; await init();`.
These adapters serialize calls into the shared Rust dispatcher. Planned modules
have no JavaScript fallback. Publishing is disabled during bootstrap.
