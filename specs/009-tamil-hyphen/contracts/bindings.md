# Multi-Runtime Bindings Contract: `tamil-hyphen`

## 1. Python (`bindings/python`)

```python
# Function signatures exposed via tamil_toolkit
from typing import TypedDict, List, Optional

class HyphenationConfig(TypedDict, total=False):
    delimiter: str
    left_min: int
    right_min: int

class HyphenationPoint(TypedDict):
    letter_index: int
    scalar_offset: int
    byte_offset: int

class HyphenationResult(TypedDict):
    original: str
    hyphenated: str
    segments: List[str]
    points: List[HyphenationPoint]

class WrapResult(TypedDict):
    lines: List[str]
    broken_words_count: int

def hyphenate_word(word: str, config: Optional[HyphenationConfig] = None) -> HyphenationResult: ...
def hyphenation_points(word: str, config: Optional[HyphenationConfig] = None) -> List[HyphenationPoint]: ...
def hyphenate_text(text: str, config: Optional[HyphenationConfig] = None) -> str: ...
def wrap_text(text: str, max_width: int, config: Optional[HyphenationConfig] = None) -> WrapResult: ...
```

---

## 2. JavaScript / TypeScript & WASM (`bindings/js-wasm`)

```typescript
export interface HyphenationConfig {
  delimiter?: string;
  left_min?: number;
  right_min?: number;
}

export interface HyphenationPoint {
  letter_index: number;
  scalar_offset: number;
  byte_offset: number;
}

export interface HyphenationResult {
  original: string;
  hyphenated: string;
  segments: string[];
  points: HyphenationPoint[];
}

export interface WrapResult {
  lines: string[];
  broken_words_count: number;
}

export function hyphenateWord(word: string, config?: HyphenationConfig): HyphenationResult;
export function hyphenationPoints(word: string, config?: HyphenationConfig): HyphenationPoint[];
export function hyphenateText(text: string, config?: HyphenationConfig): string;
export function wrapText(text: string, maxWidth: number, config?: HyphenationConfig): WrapResult;
```

---

## 3. Dart (`bindings/dart-flutter`)

```dart
class HyphenationConfig {
  final String delimiter;
  final int leftMin;
  final int rightMin;

  const HyphenationConfig({
    this.delimiter = '\u00AD',
    this.leftMin = 2,
    this.rightMin = 2,
  });
}

class HyphenationPoint {
  final int letterIndex;
  final int scalarOffset;
  final int byteOffset;

  HyphenationPoint({required this.letterIndex, required this.scalarOffset, required this.byteOffset});
}

class HyphenationResult {
  final String original;
  final String hyphenated;
  final List<String> segments;
  final List<HyphenationPoint> points;

  HyphenationResult({required this.original, required this.hyphenated, required this.segments, required this.points});
}

class WrapResult {
  final List<String> lines;
  final int brokenWordsCount;

  WrapResult({required this.lines, required this.brokenWordsCount});
}

// Method signatures on TamilToolkit
HyphenationResult hyphenateWord(String word, [HyphenationConfig? config]);
List<HyphenationPoint> hyphenationPoints(String word, [HyphenationConfig? config]);
String hyphenateText(String text, [HyphenationConfig? config]);
WrapResult wrapText(String text, int maxWidth, [HyphenationConfig? config]);
```
