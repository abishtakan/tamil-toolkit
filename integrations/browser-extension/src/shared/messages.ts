export type TypingLayout = "phonetic-v1" | "tamil99" | "anjal-phonetic" | "suratha-bamini";
export type CommitMode = "word-boundary" | "instant-keystroke";
export type PanelTab = "inspect" | "live" | "fix" | "tools";
export type NumeralLocale = "TN" | "SL";
export type SupportedCurrency = "INR" | "LKR";
export type SortProfile = "agara-v1" | "uyirmei-first-v1";
export type UiLang = "ta" | "en";
export type EditorKind = "native-input" | "contenteditable" | "canvas-fallback" | "none";
export type InspectionSource = "selection" | "active-editor" | "visible-page" | "manual";

export type LegacyEncoding =
  | "auto"
  | "bamini"
  | "tscii"
  | "tab"
  | "tam"
  | "anjal"
  | "vanavil"
  | "lt_tm";

export interface RepairDiagnostics {
  duplicate_pulli_count: number;
  visual_kombu_count: number;
  stripped_control_count: number;
  total_repairs: number;
}

export interface InspectionSnapshot {
  source: InspectionSource;
  editable: boolean;
  letterCount: number;
  wordCount: number;
  syllableCount: number;
  utf16Length: number;
  readingSeconds: number;
  breakdown: {
    uyir: number;
    mei: number;
    uyirmei: number;
    aytham: number;
    grantha: number;
    other: number;
  };
  health: {
    isNfc: boolean;
    duplicatePullis: number;
    visualKombus: number;
    zeroWidthCount: number;
    softHyphenCount: number;
    detectedLegacyEncoding: string | null;
    legacyConfidence: number;
    totalIssues: number;
  };
}

export interface OfficialHolidayItem {
  date: string;
  name: string;
  tamilName?: string;
  category?: string;
}

export interface SelectionHandoffPayload {
  requestId: string;
  tabId: number;
  action: "convert" | "inspect";
  text: string;
  editable: boolean;
  createdAt: number;
}

export type RuntimeRequest =
  | { type: "ENGINE_TRANSLITERATE"; text: string; scheme: TypingLayout }
  | { type: "ENGINE_INSPECT"; text: string; source: InspectionSource; editable: boolean }
  | { type: "ENGINE_REPAIR"; text: string; stripJoiners?: false }
  | { type: "ENGINE_DETECT_AND_CONVERT"; text: string; encoding: LegacyEncoding }
  | { type: "ENGINE_SORT_LINES"; text: string; profile: SortProfile }
  | { type: "ENGINE_NUMERAL_WORDS"; amount: string; locale: NumeralLocale; currency?: SupportedCurrency }
  | { type: "ENGINE_DATE_AND_HOLIDAYS"; year: number; month: number; day: number; jurisdiction: NumeralLocale }
  | { type: "OPEN_SIDE_PANEL"; tab?: PanelTab; handoff?: SelectionHandoffPayload }
  | { type: "TOGGLE_LIVE_TYPING"; tabId?: number; enabled?: boolean; layout?: TypingLayout }
  | { type: "GET_TAB_LIVE_STATE"; tabId?: number }
  | { type: "SET_SITE_ALWAYS_ON"; originPattern: string; enabled: boolean }
  | { type: "SET_SITE_FONT_FIX"; tabId?: number; originPattern: string; enabled: boolean }
  | { type: "REVOKE_SITE_PERMISSIONS"; originPattern: string }
  | { type: "PANEL_GET_TAB_CONTEXT_TEXT"; tabId?: number; mode: "auto" | "visible-page" }
  | { type: "PANEL_REPLACE_TAB_TEXT"; tabId?: number; text: string; scope: "selection" | "active-editor" }
  | { type: "PANEL_INSERT_TAB_TEXT"; tabId?: number; text: string }
  | {
      type: "TAB_SET_LIVE_STATE";
      enabled: boolean;
      layout: TypingLayout;
      uiLang: UiLang;
      showMicroCounter: boolean;
      showConfirmToast?: boolean;
    }
  | { type: "TAB_GET_CONTEXT_TEXT"; mode: "auto" | "visible-page" }
  | { type: "TAB_REPLACE_TEXT"; text: string; scope: "selection" | "active-editor" }
  | { type: "TAB_INSERT_TEXT"; text: string }
  | { type: "LIVE_INSPECT_UPDATE"; text: string; source: InspectionSource; editable: boolean }
  | { type: "OFFSCREEN_COPY_TEXT"; text: string };

export function commitModeForLayout(layout: TypingLayout): CommitMode {
  return layout === "tamil99" || layout === "suratha-bamini"
    ? "instant-keystroke"
    : "word-boundary";
}
