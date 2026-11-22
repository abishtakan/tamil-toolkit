import { commitModeForLayout, type CommitMode, type TypingLayout } from "../shared/messages.js";

export type TransliterateFn = (raw: string, layout: TypingLayout) => Promise<string>;

export interface CompositionState {
  layout: TypingLayout;
  commitMode: CommitMode;
  rawBuffer: string;
  committedRenderedLength: number;
  previewText: string;
  escapedCurrentWord: boolean;
}

export interface KeyActionResult {
  handled: boolean;
  deleteBeforeCaret?: number;
  insertText?: string;
  previewText: string;
  rawBuffer: string;
}

const WORD_BOUNDARY_KEYS = new Set([" ", "Enter", "Tab", ".", ",", "!", "?", ";", ":", ")", "]", "}"]);
export const LATIN_WORD_RE = /([A-Za-z][A-Za-z_-]*)$/;

export class HybridTypingEngine {
  private state: CompositionState;
  private readonly transliterate: TransliterateFn;

  constructor(layout: TypingLayout, transliterate: TransliterateFn) {
    this.transliterate = transliterate;
    this.state = {
      layout,
      commitMode: commitModeForLayout(layout),
      rawBuffer: "",
      committedRenderedLength: 0,
      previewText: "",
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
    this.state.escapedCurrentWord = false;
  }

  async updateWordPreviewFromTextBeforeCaret(textBeforeCaret: string): Promise<CompositionState> {
    if (this.state.commitMode !== "word-boundary") {
      return this.state;
    }
    if (this.state.escapedCurrentWord) {
      this.state.previewText = "";
      return this.state;
    }
    const match = textBeforeCaret.match(LATIN_WORD_RE);
    if (!match) {
      this.resetWord();
      return this.state;
    }
    this.state.rawBuffer = match[1];
    this.state.previewText = await this.transliterate(this.state.rawBuffer, this.state.layout);
    return this.state;
  }

  async handleKeyDown(
    key: string,
    modifiers: { ctrlKey?: boolean; metaKey?: boolean; altKey?: boolean },
    textBeforeCaret: string
  ): Promise<KeyActionResult> {
    if (modifiers.ctrlKey || modifiers.metaKey || modifiers.altKey) {
      if (key === "z" || key === "Z" || key === "y" || key === "Y") {
        this.resetWord();
      }
      return { handled: false, previewText: this.state.previewText, rawBuffer: this.state.rawBuffer };
    }

    if (key === "Escape") {
      if (this.state.rawBuffer.length > 0) {
        this.state.escapedCurrentWord = true;
        this.state.previewText = "";
        return { handled: true, previewText: "", rawBuffer: this.state.rawBuffer };
      }
      return { handled: false, previewText: "", rawBuffer: "" };
    }

    if (key === "ArrowLeft" || key === "ArrowRight" || key === "ArrowUp" || key === "ArrowDown" || key === "Home" || key === "End") {
      this.resetWord();
      return { handled: false, previewText: "", rawBuffer: "" };
    }

    // Mode 1: Phonetic & Anjal — word-boundary commit with live preview
    if (this.state.commitMode === "word-boundary") {
      if (WORD_BOUNDARY_KEYS.has(key)) {
        const match = textBeforeCaret.match(LATIN_WORD_RE);
        const word = match?.[1] ?? "";
        const wasEscaped = this.state.escapedCurrentWord;
        this.resetWord();
        if (!word || wasEscaped) {
          return { handled: false, previewText: "", rawBuffer: "" };
        }
        const tamil = await this.transliterate(word, this.state.layout);
        if (!tamil || tamil === word) {
          return { handled: false, previewText: "", rawBuffer: "" };
        }
        const suffix = key === "Enter" ? "\n" : key === "Tab" ? "\t" : key;
        return {
          handled: true,
          deleteBeforeCaret: word.length,
          insertText: tamil + suffix,
          previewText: "",
          rawBuffer: "",
        };
      }
      return { handled: false, previewText: this.state.previewText, rawBuffer: this.state.rawBuffer };
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
          rawBuffer: this.state.rawBuffer,
        };
      }
      return { handled: false, previewText: "", rawBuffer: "" };
    }

    if (key === " " || key === "Enter" || key === "Tab") {
      this.resetWord();
      return { handled: false, previewText: "", rawBuffer: "" };
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
        rawBuffer: nextRaw,
      };
    }

    return { handled: false, previewText: this.state.previewText, rawBuffer: this.state.rawBuffer };
  }
}
