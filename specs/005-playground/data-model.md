# Data Model: Interactive Public & Developer Playground (`playground`)

**Feature**: `005-playground` | **Date**: 2026-11-05

## Entity Relationships & Domain Types

This document specifies the reactive client state, data structures, and entity definitions governing the playground application.

---

### 1. Navigation & Tool Registry

```typescript
export type ToolCategory = "public" | "developer";

export type ToolId =
  // Public tools
  | "codec-converter"
  | "numeral-formatter"
  | "calendar-explorer"
  | "text-sorter"
  // Developer tools
  | "scalar-inspector"
  | "dispatcher-sandbox"
  | "code-generator"
  | "batch-processor";

export interface ToolDefinition {
  id: ToolId;
  title: string;
  shortDescription: string;
  category: ToolCategory;
  iconName: string;
  badge?: string;
  searchKeywords: string[];
}
```

---

### 2. Public Tools Domain Models

#### A. Legacy Font & Encoding Converter State (`CodecConversionState`)

```typescript
export type SupportedCodec =
  | "bamini-v1"
  | "tscii-1.7-v1"
  | "tab-v1"
  | "tam-v1"
  | "anjal-v1"
  | "vanavil-avvaiyar-cid-v1"
  | "lt-tm-cid-v1";

export type ConversionDirection = "to_unicode" | "from_unicode";

export interface EncodingCandidate {
  encoding: SupportedCodec;
  confidence: number; // 0.0 to 1.0
  sampleText?: string;
}

export interface CodecConversionState {
  inputText: string;
  direction: ConversionDirection;
  autoDetect: boolean;
  detectedEncoding: SupportedCodec | null;
  confidence: number;
  selectedEncoding: SupportedCodec;
  outputText: string;
  executionDurationMs: number;
  status: "idle" | "detecting" | "converted" | "uncertain" | "error";
  errorMessage?: string;
}
```

#### B. Numeral & Currency Formatter State (`NumeralState`)

```typescript
export interface NumeralState {
  inputAmount: string; // e.g. "125000" or "1050.75"
  isCurrency: boolean;
  currencyUnit: "INR" | "LKR";
  includeSpokenVariant: boolean;
  includeTraditionalDigits: boolean;
  
  // Results
  formalWords: string; // e.g. "ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய்"
  spokenWords: string;
  chequeFormat: string; // "ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய் மட்டும்"
  traditionalSymbols: string; // "௱௨௰௫௲"
  fractionWords?: string;
  executionDurationMs: number;
}
```

#### C. Tamil Calendar & Panchangam Explorer State (`CalendarState`)

```typescript
export interface CalendarState {
  selectedGregorianDate: string; // ISO date "YYYY-MM-DD"
  region: "tamil-nadu" | "sri-lanka";
  profile: "thirukanitham" | "vakya";

  // Solar Date
  tamilYear: number;
  thiruvalluvarYear: number;
  cycleYearName: string; // e.g. "குரோதி"
  tamilMonthName: string; // e.g. "ஐப்பசி"
  tamilDay: number;
  
  // Astronomical details
  tithi: string;
  nakshatra: string;
  yoga: string;
  karana: string;
  
  // Daylight periods (Rahu, Yamagandam, Gulikai)
  daylightPeriods: {
    rahuKalam: { start: string; end: string };
    yamagandam: { start: string; end: string };
    gulikai: { start: string; end: string };
  };
  
  // Official Holidays
  holidayObservances: string[];
}
```

#### D. Agara Varisai Sorter State (`CollationState`)

```typescript
export interface CollationState {
  rawInputText: string;
  delimiter: "newline" | "comma" | "space";
  ascending: boolean;
  removeDuplicates: boolean;
  
  sortedItems: string[];
  totalItemCount: number;
  uniqueItemCount: number;
  executionDurationMs: number;
}
```

---

### 3. Developer Tools Domain Models

#### A. Unicode Scalar & Grapheme Inspector State (`ScalarInspectionState`)

```typescript
export interface UnicodeScalarItem {
  scalar: string;        // e.g. "அ" or "்"
  codePoint: number;     // e.g. 0x0B85
  hex: string;           // e.g. "U+0B85"
  category: string;      // "Lo", "Mn", "Cf", etc.
  script: string;        // "Tamil", "Common", etc.
  isInvisibleControl: boolean; // ZWJ (\u200D), ZWNJ (\u200C)
  clusterIndex: number;  // grapheme cluster grouping ID
}

export interface GraphemeCluster {
  cluster: string;
  type: "uyir" | "mei" | "uyirmei" | "aytham" | "other";
  baseChar: string;
  vowelSign?: string;
  pulliAttached: boolean;
  scalars: UnicodeScalarItem[];
}

export interface ScalarInspectionState {
  inputString: string;
  totalScalars: number;
  totalGraphemeClusters: number;
  invisibleControlsDetected: boolean;
  clusters: GraphemeCluster[];
  rawScalarList: UnicodeScalarItem[];
}
```

#### B. Dispatcher Sandbox State (`DispatcherSandboxState`)

```typescript
export interface DispatcherSandboxState {
  rawJsonRequest: string;
  formattedJsonRequest: string;
  selectedTemplatePreset: string;
  status: "idle" | "executing" | "success" | "error";
  responsePayload: Record<string, unknown> | null;
  rawJsonResponse: string;
  latencyMs: number;
  errorMessage?: string;
}
```

#### C. Multi-Language Code Snippet Model (`CodeSnippetExport`)

```typescript
export type TargetLanguage = "rust" | "python" | "typescript" | "dart";

export interface CodeSnippet {
  language: TargetLanguage;
  displayName: string;
  code: string;
  installCommand: string;
}

export interface CodeSnippetExport {
  operationName: string;
  snippets: Record<TargetLanguage, CodeSnippet>;
}
```

#### D. Batch Processing Job (`BatchFileJob`)

```typescript
export interface BatchFileJob {
  id: string;
  fileName: string;
  fileSizeBytes: number;
  detectedCodec: SupportedCodec;
  status: "queued" | "processing" | "completed" | "failed";
  progressPercent: number;
  outputDownloadBlobUrl?: string;
  error?: string;
}
```
