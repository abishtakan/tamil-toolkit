# Interface Contract: Playground Engine & Web Worker Bridge

**Feature**: `005-playground` | **Date**: 2026-11-05

## Overview

The Playground web application interacts with the compiled `tamil-toolkit` WebAssembly engine through two pathways:
1. **Direct Synchronous Calls (`Main Thread`)**: For instant, interactive keystroke conversions, scalar inspections, and calendar lookups.
2. **Asynchronous Worker Bridge (`Web Worker`)**: For batch file processing and large document conversions.

---

## 1. Main-Thread Engine API Contract

The playground UI imports functions directly from `tamil-toolkit/web`:

```typescript
import init, {
  // Initialization
  init,
  execute,

  // Codec operations
  detect_encoding,
  detect_and_decode,
  bamini_to_unicode,
  unicode_to_bamini,
  tscii_bytes_to_unicode,
  unicode_to_tscii_bytes,
  vanavil_text_to_unicode,
  unicode_to_vanavil_text,
  lt_tm_text_to_unicode,
  unicode_to_lt_tm_text,
  tab_bytes_to_unicode,
  tam_bytes_to_unicode,
  anjal_bytes_to_unicode,

  // Numerals & Currency
  to_words,
  format_currency,
  currency_to_words,
  decimal_to_words,
  format_traditional_integer,
  format_mixed_fraction,

  // Collation & Core
  sort_words,
  inspect_tamil_string,
  get_letters,
  normalize_nfc,

  // Calendar
  gregorian_to_tamil_date,
  tamil_month_info,
  tamil_year_info,
  calendar_official_holidays,
  panchangam_at,
  calendar_daylight_periods
} from "tamil-toolkit/web";
```

### Lifecycle & Initialization Contract

```typescript
export interface WasmInitStatus {
  isReady: boolean;
  isLoading: boolean;
  version: string;
  error?: Error;
}

// Function called on app bootstrap
export async function initializeEngine(): Promise<void>;
```

---

## 2. Web Worker Message Protocol Contract (`playground.worker.ts`)

The worker manages non-blocking execution for batch and heavy tasks.

### Message Request Types

```typescript
export type WorkerRequest =
  | { type: "INIT" }
  | {
      type: "BATCH_CONVERT_FILE";
      jobId: string;
      fileName: string;
      content: ArrayBuffer | string;
      targetCodec?: string; // Optional override; auto-detects if omitted
    }
  | {
      type: "RAW_DISPATCHER_EXECUTE";
      requestId: string;
      payload: string; // JSON string request
    };
```

### Message Response Types

```typescript
export type WorkerResponse =
  | { type: "INIT_SUCCESS"; version: string }
  | { type: "INIT_ERROR"; error: string }
  | {
      type: "BATCH_PROGRESS";
      jobId: string;
      percent: number;
    }
  | {
      type: "BATCH_COMPLETE";
      jobId: string;
      detectedCodec: string;
      convertedText: string;
      durationMs: number;
    }
  | {
      type: "BATCH_ERROR";
      jobId: string;
      error: string;
    }
  | {
      type: "DISPATCHER_RESULT";
      requestId: string;
      success: boolean;
      rawResponse: string;
      durationMs: number;
    };
```

---

## 3. UI Component Actions & Event Contracts

Every tool view implements standard ergonomic control contracts:

```typescript
export interface ToolErgonomicActions {
  /** Copies target text to clipboard and triggers a toast notification */
  onCopy: (text: string) => Promise<boolean>;
  
  /** Resets input and output fields */
  onClear: () => void;
  
  /** Swaps input and output roles for bidirectional converters */
  onSwap?: () => void;
  
  /** Loads predefined high-quality example text */
  onLoadExample?: () => void;
}
```
