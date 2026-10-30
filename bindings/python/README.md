# tamil-toolkit for Python

Build from the repository root with `just sync-bindings`. Import as
`import tamil_toolkit as tamil`. The package delegates all linguistic behavior
to the PyO3 extension. Active functionality and planned modules are documented
in the root README. No package has been published.

Collation APIs: `compare(left, right)`, `sort_words(words)`, `sort_key(text)`,
and `search_key(text)`. Keys are numeric arrays for the versioned `agara-v1`
profile; compare arrays lexicographically and retain the version with indexes.
Sorting preserves original text and canonical ties. See docs/specs/collate-v0.1.md.
