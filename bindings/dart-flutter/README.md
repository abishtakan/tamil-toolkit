# tamil_toolkit for Dart / Flutter

Pub requires a valid Dart identifier, so its package name is `tamil_toolkit`;
the ecosystem, directory, and Rust support crate retain the `tamil-*` convention.
See [Pub naming requirements](https://dart.dev/tools/pub/pubspec#name).

Run `just test-dart` to build the Rust C ABI and consume the same active vectors.
`TamilToolkit(absoluteLibraryPath)` loads the native library. Native allocations
are released in `finally` blocks and errors cross the ABI as JSON envelopes.
Mobile/desktop app bundling and cross-compilation are future packaging work;
this scaffold supports a locally built host shared library. Flutter web uses the
JavaScript/WASM package instead. Publication is disabled.

Collation convenience methods are `compare`, `sortWords`, `sortKey`, and
`searchKey`. They marshal directly to Rust. Keys are versioned numeric arrays;
use lexicographic numeric comparison and the documented `agara-v1` profile.

The host adapter exposes `tsciiBytesToUnicode([0xba, 0xa2, 0xc5, 0xfd])` for the bounded TSCII byte profile.

The host adapter exposes `unicodeToTsciiBytes(text)` returning a byte list.
