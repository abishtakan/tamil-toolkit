# Contributing

Contributions are welcome under the MIT license in LICENSE. By submitting a
contribution, you agree to license your original contribution under those terms.
Keep any upstream copyright, license, and attribution notices intact.

Read AGENTS.md and docs/specs/bootstrap.md, then the specification for your module.
Add sourced golden vectors and declarative data before linguistic algorithms.
Rust owns behavior; Python, WASM, and Dart are thin adapters. Label regional
scope accurately and inspect Tamil strings by Unicode scalars.

Run `just bootstrap` and `just agent-pre-stop-gate` before submitting changes.
For changes to canonical lexicon or license files, run `just sync-release-files`
to refresh the checked distribution copies, then run the gates. Use
`just release-check` to verify the first alpha's actual distribution archives.
See docs/releases/alpha-1.md for scope and platform limits.
