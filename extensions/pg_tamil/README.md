# pg_tamil (planned integration)

This isolated pgrx scaffold declares tamil-norm and tamil-morph dependencies but
exports no SQL functions or text-search dictionary. It is excluded from the
portable Cargo workspace: a PostgreSQL toolchain should not be required to
build the Rust/Python/WASM/Dart SDKs.

Use Linux/macOS and [pgrx's prerequisites](https://github.com/pgcentralfoundation/pgrx).
Install matching `cargo-pgrx` 0.19.3, initialize a supported PostgreSQL instance,
then work from this directory. Select exactly one of pg17/pg18. This scaffold
has not been built or installed in the Windows bootstrap environment.

Before exposing SQL, define PostgreSQL golden/regression cases and the extension
contract (encoding, normalization, token positions, volatility, and errors).
Full-text search also requires reviewed morphology and search-folding rules.
PGXN packaging and Docker images remain release/integration work. Do not present
an identity stemmer or empty dictionary as implemented Tamil full-text search.
