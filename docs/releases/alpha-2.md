# Alpha 2 release preparation

Status: preparing `0.1.0-alpha.2` for Rust/npm and `0.1.0a2` for Python.
This record does not assert publication. Follow [publishing policy](policy.md):
build from one reviewed commit, verify the complete artifact matrix and hashes,
then publish the approved packages in dependency order.

The release includes the existing six public crates and Python/npm umbrellas.
It adds bounded TSCII, TAB, TAM, and Anjal byte conversion. TAM is monolingual:
Latin letter byte positions represent Tamil glyphs. Anjal reports four
ambiguous byte values and rejects a source glyph without an agreed byte mapping.
Inputs outside the declared profiles return errors; these APIs do not claim
complete support for historical font variants or automatic detection. See the
codec specifications and CHANGELOG for exact scope.

The TSCII decoder/encoder and TAB/TAM/Anjal operations are additions relative to
alpha 1; no prior public Bamini behavior was intentionally changed. All active
golden cases, native bindings, and host Dart must pass. Dart/Pub.dev, PostgreSQL,
and unfinished crates remain outside the publication scope.

Record the reviewed source SHA, successful artifact run, artifact digests,
publishing workflow runs and fresh registry-consumer results here as they become
available. Never reuse the alpha 1 artifacts or version.

## Local preparation evidence

On 2026-11-01 the versioned source passed the full agent gate, Dart host
tests, workbench check/build, release-policy and Unicode checks, and
`just release-check`. Extracted Rust crates and isolated Python, Node and
browser-target WASM consumers each passed all 26,957 active vectors. The
workspace lockfile update changed no third-party dependency entries.
Local logs: `target/alpha2-final-gate.log`, `target/alpha2-dart.log`,
`target/alpha2-workbench.log`, and `target/alpha2-release-check.log`.

Local artifacts were built from an uncommitted tree and are not the reviewed
GitHub artifacts required for publication. The local output directory also
contains earlier alpha.1 archives; do not use its combined digest list as the
alpha.2 publication inventory.
