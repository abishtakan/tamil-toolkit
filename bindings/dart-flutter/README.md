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
