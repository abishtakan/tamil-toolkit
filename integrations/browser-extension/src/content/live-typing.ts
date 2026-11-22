import { commitModeForLayout, type CommitMode, type TypingLayout } from "../shared/messages.js";

export type TransliterateFn = (raw: string, layout: TypingLayout) => Promise<string>;
export type SuggestFn = (raw: string, layout: TypingLayout) => Promise<string[]>;

export interface CompositionState {
  layout: TypingLayout;
  commitMode: CommitMode;
  rawBuffer: string;
  committedRenderedLength: number;
  previewText: string;
  candidates: string[];
  selectedIndex: number;
  escapedCurrentWord: boolean;
}

export interface KeyActionResult {
  handled: boolean;
  deleteBeforeCaret?: number;
  insertText?: string;
  previewText: string;
  candidates?: string[];
  selectedIndex?: number;
  rawBuffer: string;
}

const WORD_BOUNDARY_KEYS = new Set([" ", "Enter", "Tab", ".", ",", "!", "?", ";", ":", ")", "]", "}"]);
export const LATIN_WORD_RE = /([A-Za-z][A-Za-z_-]*)$/;

export class HybridTypingEngine {
  private state: CompositionState;
  private readonly transliterate: TransliterateFn;
  private readonly suggest: SuggestFn;

  constructor(layout: TypingLayout, transliterate: TransliterateFn, suggest?: SuggestFn) {
    this.transliterate = transliterate;
    this.suggest =
      suggest ??
      (async (raw, l) => {
        const out = await transliterate(raw, l);
        return out ? [out] : [];
      });
    this.state = {
      layout,
      commitMode: commitModeForLayout(layout),
      rawBuffer: "",
      committedRenderedLength: 0,
      previewText: "",
      candidates: [],
      selectedIndex: 0,
      escapedCurrentWord: false,
    };
  }

  getState(): Readonly<CompositionState> {
    return this.state;
  }

  setLayout(layout: TypingLayout): void {
    this.state.layout = layout;
    this.state.commitMode = commitModeForLayout(layout);
    this.resetWord();
  }

  resetWord(): void {
    this.state.rawBuffer = "";
    this.state.committedRenderedLength = 0;
    this.state.previewText = "";
    this.state.candidates = [];
    this.state.selectedIndex = 0;
    this.state.escapedCurrentWord = false;
  }

  async updateWordPreviewFromTextBeforeCaret(textBeforeCaret: string): Promise<CompositionState> {
    if (this.state.commitMode !== "word-boundary") {
      return this.state;
    }
    if (this.state.escapedCurrentWord) {
      this.state.previewText = "";
      this.state.candidates = [];
      this.state.selectedIndex = 0;
      return this.state;
    }
    const match = textBeforeCaret.match(LATIN_WORD_RE);
    if (!match) {
      this.resetWord();
      return this.state;
    }
    const word = match[1];
    this.state.rawBuffer = word;
    const candidates = await this.suggest(word, this.state.layout);
    if (this.state.escapedCurrentWord) {
      this.state.previewText = "";
      this.state.candidates = [];
      this.state.selectedIndex = 0;
      return this.state;
    }
    if (candidates.length > 0) {
      this.state.candidates = candidates;
      this.state.selectedIndex = 0;
      this.state.previewText = candidates[0];
    } else {
      const primary = await this.transliterate(word, this.state.layout);
      this.state.candidates = primary ? [primary] : [];
      this.state.selectedIndex = 0;
      this.state.previewText = primary;
    }
    return this.state;
  }

  commitCandidateAt(index: number, textBeforeCaret?: string): KeyActionResult {
    if (
      this.state.commitMode !== "word-boundary" ||
      this.state.escapedCurrentWord ||
      index < 0 ||
      index >= this.state.candidates.length
    ) {
      return {
        handled: false,
        previewText: this.state.previewText,
        candidates: [...this.state.candidates],
        selectedIndex: this.state.selectedIndex,
        rawBuffer: this.state.rawBuffer,
      };
    }

    const matchWord = textBeforeCaret?.match(LATIN_WORD_RE)?.[1] ?? "";
    const word = matchWord || this.state.rawBuffer;
    const chosen = this.state.candidates[index];
    this.resetWord();
    if (!word || !chosen || chosen === word) {
      return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
    }
    return {
      handled: true,
      deleteBeforeCaret: word.length,
      insertText: chosen + " ",
      previewText: "",
      candidates: [],
      selectedIndex: 0,
      rawBuffer: "",
    };
  }

  async handleKeyDown(
    key: string,
    modifiers: { ctrlKey?: boolean; metaKey?: boolean; altKey?: boolean; shiftKey?: boolean },
    textBeforeCaret: string
  ): Promise<KeyActionResult> {
    if (modifiers.ctrlKey || modifiers.metaKey || modifiers.altKey) {
      if (key === "z" || key === "Z" || key === "y" || key === "Y") {
        this.resetWord();
      }
      return {
        handled: false,
        previewText: this.state.previewText,
        candidates: [...this.state.candidates],
        selectedIndex: this.state.selectedIndex,
        rawBuffer: this.state.rawBuffer,
      };
    }

    if (key === "Escape") {
      if (this.state.rawBuffer.length > 0) {
        this.state.escapedCurrentWord = true;
        this.state.previewText = "";
        this.state.candidates = [];
        this.state.selectedIndex = 0;
        return {
          handled: true,
          previewText: "",
          candidates: [],
          selectedIndex: 0,
          rawBuffer: this.state.rawBuffer,
        };
      }
      return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
    }

    // Mode 1: Phonetic & Anjal — word-boundary commit with live preview & Mayangoli cycling
    if (this.state.commitMode === "word-boundary") {
      if (!this.state.escapedCurrentWord && this.state.rawBuffer.length > 0) {
        if (
          this.state.candidates.length > 1 &&
          (key === "ArrowDown" || (key === "Tab" && !modifiers.shiftKey))
        ) {
          const nextIdx = (this.state.selectedIndex + 1) % this.state.candidates.length;
          this.state.selectedIndex = nextIdx;
          this.state.previewText = this.state.candidates[nextIdx];
          return {
            handled: true,
            previewText: this.state.previewText,
            candidates: [...this.state.candidates],
            selectedIndex: nextIdx,
            rawBuffer: this.state.rawBuffer,
          };
        }

        if (
          this.state.candidates.length > 1 &&
          (key === "ArrowUp" || (key === "Tab" && modifiers.shiftKey))
        ) {
          const len = this.state.candidates.length;
          const prevIdx = (this.state.selectedIndex - 1 + len) % len;
          this.state.selectedIndex = prevIdx;
          this.state.previewText = this.state.candidates[prevIdx];
          return {
            handled: true,
            previewText: this.state.previewText,
            candidates: [...this.state.candidates],
            selectedIndex: prevIdx,
            rawBuffer: this.state.rawBuffer,
          };
        }

        if (this.state.candidates.length > 0 && /^[1-5]$/.test(key)) {
          const idx = Number(key) - 1;
          if (idx < this.state.candidates.length) {
            return this.commitCandidateAt(idx, textBeforeCaret);
          }
        }
      }

      if (
        key === "ArrowLeft" ||
        key === "ArrowRight" ||
        key === "ArrowUp" ||
        key === "ArrowDown" ||
        key === "Home" ||
        key === "End"
      ) {
        this.resetWord();
        return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
      }

      if (WORD_BOUNDARY_KEYS.has(key)) {
        const match = textBeforeCaret.match(LATIN_WORD_RE);
        const word = match?.[1] ?? "";
        const wasEscaped = this.state.escapedCurrentWord;
        const wasCycled = this.state.selectedIndex > 0;
        const activeCandidate =
          word && this.state.rawBuffer === word
            ? this.state.candidates[this.state.selectedIndex]
            : undefined;
        this.resetWord();
        if (!word || wasEscaped) {
          return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
        }
        const tamil = activeCandidate ?? (await this.transliterate(word, this.state.layout));
        if (!tamil || tamil === word) {
          return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
        }
        const suffix = key === "Enter" ? (wasCycled ? "" : "\n") : key === "Tab" ? "\t" : key;
        return {
          handled: true,
          deleteBeforeCaret: word.length,
          insertText: tamil + suffix,
          previewText: "",
          candidates: [],
          selectedIndex: 0,
          rawBuffer: "",
        };
      }

      return {
        handled: false,
        previewText: this.state.previewText,
        candidates: [...this.state.candidates],
        selectedIndex: this.state.selectedIndex,
        rawBuffer: this.state.rawBuffer,
      };
    }

    if (
      key === "ArrowLeft" ||
      key === "ArrowRight" ||
      key === "ArrowUp" ||
      key === "ArrowDown" ||
      key === "Home" ||
      key === "End"
    ) {
      this.resetWord();
      return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
    }

    // Mode 2: Tamil99 & Bamini — instant per-keystroke conversion
    // Note: punctuation keys like ';', ',', '.', '[', ']', '\'', '/' are active Tamil letter/pulli keys
    // in Bamini and Tamil99, so only whitespace resets the rolling keystroke buffer.
    if (key === "Backspace") {
      if (this.state.rawBuffer.length > 0) {
        const prevLen = this.state.committedRenderedLength;
        this.state.rawBuffer = this.state.rawBuffer.slice(0, -1);
        if (this.state.rawBuffer.length === 0) {
          this.state.committedRenderedLength = 0;
          this.state.previewText = "";
          return {
            handled: true,
            deleteBeforeCaret: prevLen,
            insertText: "",
            previewText: "",
            candidates: [],
            selectedIndex: 0,
            rawBuffer: "",
          };
        }
        const nextTamil = await this.transliterate(this.state.rawBuffer, this.state.layout);
        this.state.committedRenderedLength = nextTamil.length;
        this.state.previewText = nextTamil;
        return {
          handled: true,
          deleteBeforeCaret: prevLen,
          insertText: nextTamil,
          previewText: nextTamil,
          candidates: nextTamil ? [nextTamil] : [],
          selectedIndex: 0,
          rawBuffer: this.state.rawBuffer,
        };
      }
      return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
    }

    if (key === " " || key === "Enter" || key === "Tab") {
      this.resetWord();
      return { handled: false, previewText: "", candidates: [], selectedIndex: 0, rawBuffer: "" };
    }

    if (key.length === 1 && !/\s/.test(key)) {
      const prevLen = this.state.committedRenderedLength;
      const nextRaw = this.state.rawBuffer + key;
      const nextTamil = await this.transliterate(nextRaw, this.state.layout);
      this.state.rawBuffer = nextRaw;
      this.state.committedRenderedLength = nextTamil.length;
      this.state.previewText = nextTamil;
      return {
        handled: true,
        deleteBeforeCaret: prevLen,
        insertText: nextTamil,
        previewText: nextTamil,
        candidates: nextTamil ? [nextTamil] : [],
        selectedIndex: 0,
        rawBuffer: nextRaw,
      };
    }

    return {
      handled: false,
      previewText: this.state.previewText,
      candidates: [...this.state.candidates],
      selectedIndex: this.state.selectedIndex,
      rawBuffer: this.state.rawBuffer,
    };
  }
}
