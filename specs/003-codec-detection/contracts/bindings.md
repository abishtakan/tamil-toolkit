# Contract: Multi-Runtime High-Level Bindings

**Feature**: `specs/003-codec-detection`  
**Runtimes**: Python (`bindings/python`), WebAssembly/TS (`bindings/js-wasm`), Dart (`bindings/dart`)  

---

## 1. Python (`tamil_toolkit`)

```python
from typing import Union, List, Optional, TypedDict

class EncodingCandidate(TypedDict):
    encoding: str
    confidence: float

class DetectionResult(TypedDict):
    status: str            # "detected" | "uncertain"
    encoding: Optional[str] # e.g. "tscii-1.7-v1", or None
    confidence: float      # 0.0 to 1.0
    reason: Optional[str]   # None or reason string
    candidates: List[EncodingCandidate]

def detect_encoding(data: Union[bytes, str, List[int]]) -> DetectionResult:
    """
    Detect legacy Tamil encoding from raw bytes, text string, or 16-bit CID code units.
    """
    ...

def detect_and_decode(data: Union[bytes, str]) -> str:
    """
    Automatically detects encoding and decodes to standard NFC Unicode.
    Raises ValueError / UncertainEncodingError if detection is uncertain.
    """
    ...
```

---

## 2. WebAssembly / TypeScript (`tamil-toolkit-wasm`)

```typescript
export interface EncodingCandidate {
  encoding: string;
  confidence: number;
}

export interface DetectionResult {
  status: "detected" | "uncertain";
  encoding: string | null;
  confidence: number;
  reason: string | null;
  candidates: EncodingCandidate[];
}

export function detectEncoding(
  data: Uint8Array | string | number[]
): DetectionResult;

export function detectAndDecode(
  data: Uint8Array | string
): string;
```

---

## 3. Dart (`tamil_toolkit`)

```dart
class EncodingCandidate {
  final String encoding;
  final double confidence;
  const EncodingCandidate({required this.encoding, required this.confidence});
}

class DetectionResult {
  final String status; // 'detected' | 'uncertain'
  final String? encoding;
  final double confidence;
  final String? reason;
  final List<EncodingCandidate> candidates;

  const DetectionResult({
    required this.status,
    this.encoding,
    required this.confidence,
    this.reason,
    required this.candidates,
  });
}

DetectionResult detectEncoding(dynamic data); // Uint8List, String, or List<int>
String detectAndDecode(dynamic data); // Uint8List or String
```
