<div align="center">

# tamil_toolkit for Dart & Flutter

### High-Performance Tamil Text Processing, Collation & Legacy Font Conversion for Dart and Flutter

**Native Rust C-ABI adapter · Mei-first Agara collation · Legacy font conversion (Bamini, TSCII, TAB, TAM, Anjal) · Zero-memory-leak memory management**

[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)
[![Flutter / Dart](https://img.shields.io/badge/Dart-3.0+-blue?style=flat-square&logo=dart)](bindings/dart-flutter)

[Overview](#overview) · [Architecture](#architecture) · [Collation & Sorting](#tamil-collation--sorting) · [Legacy Font Transcoding](#legacy-font-transcoding) · [License](#license)

</div>

---

## Overview

`tamil_toolkit` provides high-performance Dart bindings for Flutter mobile, desktop, and backend Dart applications. Built over the shared native Rust core via Dart `dart:ffi` C-ABI bindings.

> **Note on Naming**: Pub requires a snake_case identifier, hence `tamil_toolkit`; the ecosystem repository and Rust crates retain the `tamil-*` convention. See [Pub naming requirements](https://dart.dev/tools/pub/pubspec#name).

---

## Architecture & Safety

- **Zero Memory Leaks**: Native allocations are safely released in `finally` blocks using Dart finalizers and explicit free functions.
- **Structured Error Handling**: Rust errors cross the C-ABI boundary as structured JSON error envelopes rather than unhandled native panics.
- **Cross-Platform**: Designed for Flutter on Android, iOS, macOS, Windows, and Linux. For Flutter Web, use the WebAssembly package [`tamil-toolkit/web`](../js-wasm/README.md).

---

## Capabilities

### 1. Tamil Collation & Sorting (*Agara Varisai*)

Sort Tamil strings in mobile apps according to traditional dictionary ordering (*Mei-first*):

```dart
import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit('/path/to/libtamil_cabi.so');

  // Compare two Tamil strings
  final result = toolkit.compare('அம்மா', 'அப்பா');
  print(result); // -1 (அம்மா precedes அப்பா)

  // Sort word list
  final words = ['ஆடு', 'அம்மா', 'இலை', 'ஈட்டி'];
  final sorted = toolkit.sortWords(words);
  print(sorted); // ['அம்மா', 'ஆடு', 'இலை', 'ஈட்டி']

  // Generate versioned numeric sort keys for SQLite / Hive indexing
  final key = toolkit.sortKey('தமிழ்');
  print('Sort Key: $key');
}
```

### 2. Legacy Font Transcoding

Convert legacy newspaper, magazine, or user-submitted text from legacy encodings into modern Unicode:

```dart
// TSCII Byte Stream to Unicode
final tsciiBytes = [0xba, 0xa2, 0xc5, 0xfd];
final unicodeText = toolkit.tsciiBytesToUnicode(tsciiBytes);
print(unicodeText);

// Unicode to TSCII Bytes
final encodedBytes = toolkit.unicodeToTsciiBytes('தமிழ்');

// TAB and TAM conversion
final tabDecoded = toolkit.tabBytesToUnicode(tabBytes);
final tamDecoded = toolkit.tamBytesToUnicode(tamBytes);

// Anjal legacy byte conversion
final anjalDecoded = toolkit.anjalBytesToUnicode(anjalBytes);
```

---

## Testing

Run the test suite using `just`:

```bash
just test-dart
```

This compiles the Rust C ABI dynamic library and executes tests verifying golden vector parity against the core repository test suite.

---

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).

---

## Keywords

`tamil flutter`, `flutter tamil font converter`, `tamil dart package`, `tscii to unicode dart`, `bamini flutter`, `tamil sort agara varisai dart`, `tamil ffi rust`.
