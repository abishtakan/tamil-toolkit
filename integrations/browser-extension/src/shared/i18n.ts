import type { UiLang } from "./messages.js";

export interface UiStrings {
  brand: string;
  tabInspect: string;
  tabLive: string;
  tabFix: string;
  tabTools: string;
  settingsTitle: string;
  microCounterLabel: string;
  microCounterDesc: string;
  sitePermissionsTitle: string;
  noSitePermissions: string;
  revoke: string;
  // Inspect
  tamilLetters: string;
  words: string;
  utf16Units: string;
  letterBreakdown: string;
  uyir: string;
  mei: string;
  uyirmei: string;
  aytham: string;
  grantha: string;
  healthClean: string;
  healthCleanDetail: string;
  healthIssuesFound: (count: number) => string;
  healthVisualKombu: (count: number) => string;
  healthDuplicatePulli: (count: number) => string;
  healthNonNfc: string;
  healthLegacyDetected: (enc: string) => string;
  healthJoinersPreserved: (count: number) => string;
  repairInPlace: string;
  inspectVisiblePage: string;
  inspectPlaceholder: string;
  refreshInspect: string;
  pillScratchTitle: string;
  pillScratchPlaceholder: string;
  pillInspect: string;
  pillInsert: string;
  pillCopy: string;
  pillLayoutPhonetic: string;
  pillLayoutTamil99: string;
  pillLayoutAnjal: string;
  pillLayoutBamini: string;
  // Live Type
  liveTypingLabel: string;
  liveTypingDesc: string;
  alwaysOnSiteLabel: string;
  alwaysOnSiteDesc: string;
  layoutLabel: string;
  scratchpadLabel: string;
  scratchpadPlaceholder: string;
  insertIntoPage: string;
  copy: string;
  copied: string;
  // Fix Text
  modeConvert: string;
  modeRepair: string;
  modeSort: string;
  encodingAuto: string;
  ambiguousPrompt: string;
  sortAgara: string;
  sortUyirmei: string;
  replaceInPage: string;
  fixPlaceholder: string;
  // Tools
  numbersTitle: string;
  datesTitle: string;
  fontFixTitle: string;
  fontFixDesc: string;
  localeTN: string;
  localeSL: string;
  noCurrency: string;
  unsupportedYear: string;
}

const EN: UiStrings = {
  brand: "Tamil Toolkit",
  tabInspect: "Inspect",
  tabLive: "Live Type",
  tabFix: "Fix Text",
  tabTools: "Tools",
  settingsTitle: "Settings",
  microCounterLabel: "Live letter & word counter",
  microCounterDesc: "Show Tamil letter/word count in the floating pill",
  sitePermissionsTitle: "Site permissions",
  noSitePermissions: "No sites granted persistent access.",
  revoke: "Revoke",
  tamilLetters: "Tamil Letters",
  words: "Words",
  utf16Units: "UTF-16 Units",
  letterBreakdown: "Letter Breakdown",
  uyir: "Uyir",
  mei: "Mei",
  uyirmei: "Uyirmei",
  aytham: "Aytham",
  grantha: "Grantha",
  healthClean: "Clean NFC Unicode",
  healthCleanDetail: "No broken pulli, visual kombu, or legacy encoding detected",
  healthIssuesFound: (count) => `${count} Unicode issue${count === 1 ? "" : "s"} found`,
  healthVisualKombu: (count) => `${count} visual kombu`,
  healthDuplicatePulli: (count) => `${count} duplicate pulli`,
  healthNonNfc: "non-NFC",
  healthLegacyDetected: (enc) => `legacy: ${enc}`,
  healthJoinersPreserved: (count) => `${count} joiner${count === 1 ? "" : "s"} preserved`,
  repairInPlace: "Repair in place",
  inspectVisiblePage: "Inspect visible page",
  inspectPlaceholder: "Select text on the page, or paste/type Tamil here to inspect...",
  refreshInspect: "Refresh from page",
  pillScratchTitle: "Quick Compose (canvas editor fallback)",
  pillScratchPlaceholder: "Type Tamil here...",
  pillInspect: "Inspect",
  pillInsert: "Insert",
  pillCopy: "Copy",
  pillLayoutPhonetic: "Phonetic",
  pillLayoutTamil99: "Tamil99",
  pillLayoutAnjal: "Anjal",
  pillLayoutBamini: "Bamini",
  liveTypingLabel: "Live Inline Typing",
  liveTypingDesc: "Type Tamil directly in web page inputs (Alt+Shift+L)",
  alwaysOnSiteLabel: "Always on for this site",
  alwaysOnSiteDesc: "Opt-in single-site permission only",
  layoutLabel: "Keyboard Layout",
  scratchpadLabel: "Quick Compose (for Google Docs / Canvas)",
  scratchpadPlaceholder: "Type Tanglish, Tamil99, Anjal, or Bamini here...",
  insertIntoPage: "Insert into page",
  copy: "Copy",
  copied: "Copied",
  modeConvert: "Convert",
  modeRepair: "Repair",
  modeSort: "Sort",
  encodingAuto: "Auto-detect",
  ambiguousPrompt: "Encoding is ambiguous — choose an explicit codec above before replacing or copying.",
  sortAgara: "Agara Varisai (Default)",
  sortUyirmei: "Uyirmei-first",
  replaceInPage: "Replace in page",
  fixPlaceholder: "Paste or select legacy/broken Tamil text or lines to sort...",
  numbersTitle: "Numbers & Currency to Tamil Words",
  datesTitle: "Today's Tamil Civil Date & Official Holidays",
  fontFixTitle: "Improve Tamil fonts here",
  fontFixDesc: "Apply bundled Noto Tamil + Tamil Supplement on this site",
  localeTN: "Tamil Nadu (TN)",
  localeSL: "Sri Lanka (SL)",
  noCurrency: "Number only",
  unsupportedYear: "Official holiday data is not available for this year.",
};

const TA: UiStrings = {
  brand: "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0B95\u0BB0\u0BC1\u0BB5\u0BBF",
  tabInspect: "\u0B86\u0BAF\u0BCD\u0BB5\u0BC1",
  tabLive: "\u0BA8\u0BC7\u0BB0\u0B9F\u0BBF",
  tabFix: "\u0B9A\u0BC0\u0BB0\u0BAE\u0BC8",
  tabTools: "\u0B95\u0BB0\u0BC1\u0BB5\u0BBF\u0B95\u0BB3\u0BCD",
  settingsTitle: "\u0B85\u0BAE\u0BC8\u0BAA\u0BCD\u0BAA\u0BC1\u0B95\u0BB3\u0BCD",
  microCounterLabel: "\u0BA8\u0BC7\u0BB0\u0B9F\u0BBF \u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1/\u0B9A\u0BCA\u0BB2\u0BCD \u0B8E\u0BA3\u0BCD\u0BA3\u0BBF\u0B95\u0BCD\u0B95\u0BC8",
  microCounterDesc: "\u0BAE\u0BBF\u0BA4\u0B95\u0BCD\u0B95\u0BC1\u0BAE\u0BCD \u0B95\u0B9F\u0BCD\u0B9F\u0BC1\u0BAA\u0BCD\u0BAA\u0BBE\u0B9F\u0BCD\u0B9F\u0BBF\u0BB2\u0BCD \u0B8E\u0BA3\u0BCD\u0BA3\u0BBF\u0B95\u0BCD\u0B95\u0BC8 \u0B95\u0BBE\u0B9F\u0BCD\u0B9F\u0BC1",
  sitePermissionsTitle: "\u0BA4\u0BB3 \u0B85\u0BA9\u0BC1\u0BAE\u0BA4\u0BBF\u0B95\u0BB3\u0BCD",
  noSitePermissions: "\u0BA8\u0BBF\u0BB0\u0BA8\u0BCD\u0BA4\u0BB0 \u0B85\u0BA9\u0BC1\u0BAE\u0BA4\u0BBF \u0BAA\u0BC6\u0BB1\u0BCD\u0BB1 \u0BA4\u0BB3\u0B99\u0BCD\u0B95\u0BB3\u0BCD \u0B87\u0BB2\u0BCD\u0BB2\u0BC8.",
  revoke: "\u0BA8\u0BC0\u0B95\u0BCD\u0B95\u0BC1",
  tamilLetters: "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1",
  words: "\u0B9A\u0BCA\u0BB1\u0BCD\u0B95\u0BB3\u0BCD",
  utf16Units: "UTF-16 \u0B85\u0BB2\u0B95\u0BC1",
  letterBreakdown: "\u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1\u0BAA\u0BCD \u0BAA\u0BBF\u0BB0\u0BBF\u0BB5\u0BC1",
  uyir: "\u0B89\u0BAF\u0BBF\u0BB0\u0BCD",
  mei: "\u0BAE\u0BC6\u0BAF\u0BCD",
  uyirmei: "\u0B89\u0BAF\u0BBF\u0BB0\u0BCD\u0BAE\u0BC6\u0BAF\u0BCD",
  aytham: "\u0B86\u0BAF\u0BCD\u0BA4\u0BAE\u0BCD",
  grantha: "\u0B95\u0BBF\u0BB0\u0BA8\u0BCD\u0BA4\u0BAE\u0BCD",
  healthClean: "\u0BA4\u0BC2\u0BAF NFC \u0BAF\u0BC2\u0BA9\u0BBF\u0B95\u0BCB\u0B9F\u0BCD",
  healthCleanDetail: "\u0BAA\u0BBF\u0BB4\u0BC8\u0BAF\u0BBE\u0BA9 \u0BAA\u0BC1\u0BB3\u0BCD\u0BB3\u0BBF \u0B85\u0BB2\u0BCD\u0BB2\u0BA4\u0BC1 \u0B95\u0BCA\u0BAE\u0BCD\u0BAA\u0BC1 \u0B87\u0BB2\u0BCD\u0BB2\u0BC8",
  healthIssuesFound: (count) => `${count} \u0BAF\u0BC2\u0BA9\u0BBF\u0B95\u0BCB\u0B9F\u0BCD \u0B9A\u0BBF\u0B95\u0BCD\u0B95\u0BB2\u0BCD`,
  healthVisualKombu: (count) => `${count} \u0BAE\u0BC1\u0BA9\u0BCD-\u0B95\u0BCA\u0BAE\u0BCD\u0BAA\u0BC1`,
  healthDuplicatePulli: (count) => `${count} \u0B87\u0BB0\u0B9F\u0BCD\u0B9F\u0BC8\u0BAA\u0BCD \u0BAA\u0BC1\u0BB3\u0BCD\u0BB3\u0BBF`,
  healthNonNfc: "NFC \u0B85\u0BB2\u0BCD\u0BB2",
  healthLegacyDetected: (enc) => `\u0BAA\u0BB4\u0BC8\u0BAF \u0B95\u0BC1\u0BB1\u0BBF\u0BAF\u0BC0\u0B9F\u0BC1: ${enc}`,
  healthJoinersPreserved: (count) => `${count} \u0B87\u0BA3\u0BC8\u0BAA\u0BCD\u0BAA\u0BC1 \u0BAA\u0BBE\u0BA4\u0BC1\u0B95\u0BBE\u0B95\u0BCD\u0B95\u0BAA\u0BCD\u0BAA\u0B9F\u0BCD\u0B9F\u0BA4\u0BC1`,
  repairInPlace: "\u0B89\u0B9F\u0BA9\u0BC7 \u0B9A\u0BC0\u0BB0\u0BAE\u0BC8",
  inspectVisiblePage: "\u0BAA\u0B95\u0BCD\u0B95\u0BA4\u0BCD\u0BA4\u0BC8 \u0B86\u0BAF\u0BCD\u0BB5\u0BC1 \u0B9A\u0BC6\u0BAF\u0BCD",
  inspectPlaceholder: "\u0B89\u0BB0\u0BC8\u0BAF\u0BC8\u0BA4\u0BCD \u0BA4\u0BC7\u0BB0\u0BCD\u0BB5\u0BC1 \u0B9A\u0BC6\u0BAF\u0BCD\u0B95 \u0B85\u0BB2\u0BCD\u0BB2\u0BA4\u0BC1 \u0B87\u0B99\u0BCD\u0B95\u0BC7 \u0B92\u0B9F\u0BCD\u0B9F\u0BB5\u0BC1\u0BAE\u0BCD...",
  refreshInspect: "\u0BAA\u0B95\u0BCD\u0B95\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BBF\u0BB0\u0BC1\u0BA8\u0BCD\u0BA4\u0BC1 \u0BAA\u0BC1\u0BA4\u0BC1\u0BAA\u0BCD\u0BAA\u0BBF",
  pillScratchTitle: "\u0BB5\u0BBF\u0BB0\u0BC8\u0BB5\u0BC1 \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1 (Canvas \u0BAE\u0BBE\u0BB1\u0BCD\u0BB1\u0BC1)",
  pillScratchPlaceholder: "\u0B87\u0B99\u0BCD\u0B95\u0BC7 \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1 \u0B9A\u0BC6\u0BAF\u0BCD\u0BAF\u0BB5\u0BC1\u0BAE\u0BCD...",
  pillInspect: "\u0B86\u0BAF\u0BCD\u0BB5\u0BC1",
  pillInsert: "\u0B9A\u0BC7\u0BB0\u0BCD",
  pillCopy: "\u0BA8\u0B95\u0BB2\u0BC6\u0B9F\u0BC1",
  pillLayoutPhonetic: "\u0B92\u0BB2\u0BBF\u0BAF\u0BBF\u0BAF\u0BB2\u0BCD",
  pillLayoutTamil99: "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD99",
  pillLayoutAnjal: "\u0B85\u0B9E\u0BCD\u0B9A\u0BB2\u0BCD",
  pillLayoutBamini: "\u0BAA\u0BBE\u0BAE\u0BBF\u0BA9\u0BBF",
  liveTypingLabel: "\u0BA8\u0BC7\u0BB0\u0B9F\u0BBF \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1",
  liveTypingDesc: "\u0B87\u0BA3\u0BC8\u0BAF\u0BAA\u0BCD \u0BAA\u0B95\u0BCD\u0B95\u0B99\u0BCD\u0B95\u0BB3\u0BBF\u0BB2\u0BCD \u0BA8\u0BC7\u0BB0\u0B9F\u0BBF\u0BAF\u0BBE\u0B95 \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1 (Alt+Shift+L)",
  alwaysOnSiteLabel: "\u0B87\u0BA4\u0BCD\u0BA4\u0BB3\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BCD \u0B8E\u0BAA\u0BCD\u0BAA\u0BCB\u0BA4\u0BC1\u0BAE\u0BCD \u0B87\u0BAF\u0B95\u0BCD\u0B95\u0BC1",
  alwaysOnSiteDesc: "\u0B87\u0BA8\u0BCD\u0BA4 \u0B92\u0BB0\u0BC1 \u0BA4\u0BB3\u0BA4\u0BCD\u0BA4\u0BBF\u0BB1\u0BCD\u0B95\u0BC1 \u0BAE\u0B9F\u0BCD\u0B9F\u0BC1\u0BAE\u0BCD \u0B85\u0BA9\u0BC1\u0BAE\u0BA4\u0BBF",
  layoutLabel: "\u0BB5\u0BBF\u0B9A\u0BC8\u0BAA\u0BCD\u0BAA\u0BB2\u0B95\u0BC8",
  scratchpadLabel: "\u0BB5\u0BBF\u0BB0\u0BC8\u0BB5\u0BC1 \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1 (Google Docs / Canvas)",
  scratchpadPlaceholder: "\u0B87\u0B99\u0BCD\u0B95\u0BC7 \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1 \u0B9A\u0BC6\u0BAF\u0BCD\u0BAF\u0BB5\u0BC1\u0BAE\u0BCD...",
  insertIntoPage: "\u0BAA\u0B95\u0BCD\u0B95\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BCD \u0B9A\u0BC7\u0BB0\u0BCD",
  copy: "\u0BA8\u0B95\u0BB2\u0BC6\u0B9F\u0BC1",
  copied: "\u0BA8\u0B95\u0BB2\u0BC6\u0B9F\u0BC1\u0B95\u0BCD\u0B95\u0BAA\u0BCD\u0BAA\u0B9F\u0BCD\u0B9F\u0BA4\u0BC1",
  modeConvert: "\u0BAE\u0BBE\u0BB1\u0BCD\u0BB1\u0BC1",
  modeRepair: "\u0B9A\u0BC0\u0BB0\u0BAE\u0BC8",
  modeSort: "\u0BB5\u0BB0\u0BBF\u0B9A\u0BC8\u0BAA\u0BCD\u0BAA\u0B9F\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1",
  encodingAuto: "\u0BA4\u0BBE\u0BA9\u0BBF\u0BAF\u0B99\u0BCD\u0B95\u0BBF",
  ambiguousPrompt: "\u0B95\u0BC1\u0BB1\u0BBF\u0BAF\u0BC0\u0B9F\u0BC1 \u0BA4\u0BC6\u0BB3\u0BBF\u0BB5\u0BB1\u0BCD\u0BB1\u0BA4\u0BC1 \u2014 \u0BAE\u0BC7\u0BB2\u0BC7 \u0B9A\u0BB0\u0BBF\u0BAF\u0BBE\u0BA9 \u0B95\u0BC1\u0BB1\u0BBF\u0BAF\u0BC0\u0B9F\u0BCD\u0B9F\u0BC8\u0BA4\u0BCD \u0BA4\u0BC7\u0BB0\u0BCD\u0BB5\u0BC1 \u0B9A\u0BC6\u0BAF\u0BCD\u0B95.",
  sortAgara: "\u0B85\u0B95\u0BB0 \u0BB5\u0BB0\u0BBF\u0B9A\u0BC8 (\u0B87\u0BAF\u0BB2\u0BCD\u0BAA\u0BC1)",
  sortUyirmei: "\u0B89\u0BAF\u0BBF\u0BB0\u0BCD\u0BAE\u0BC6\u0BAF\u0BCD \u0BAE\u0BC1\u0BA4\u0BB2\u0BCD",
  replaceInPage: "\u0BAA\u0B95\u0BCD\u0B95\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BCD \u0BAE\u0BBE\u0BB1\u0BCD\u0BB1\u0BC1",
  fixPlaceholder: "\u0BAA\u0BB4\u0BC8\u0BAF \u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1\u0BB0\u0BC1 \u0B85\u0BB2\u0BCD\u0BB2\u0BA4\u0BC1 \u0BB5\u0BB0\u0BBF\u0B95\u0BB3\u0BC8 \u0B87\u0B99\u0BCD\u0B95\u0BC7 \u0B92\u0B9F\u0BCD\u0B9F\u0BB5\u0BC1\u0BAE\u0BCD...",
  numbersTitle: "\u0B8E\u0BA3\u0BCD\u0B95\u0BB3\u0BCD \u0BAE\u0BB1\u0BCD\u0BB1\u0BC1\u0BAE\u0BCD \u0BA8\u0BBE\u0BA3\u0BAF \u0B9A\u0BCA\u0BB1\u0BCD\u0B95\u0BB3\u0BCD",
  datesTitle: "\u0B87\u0BA9\u0BCD\u0BB1\u0BC8\u0BAF \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0BA4\u0BC7\u0BA4\u0BBF \u0BAE\u0BB1\u0BCD\u0BB1\u0BC1\u0BAE\u0BCD \u0BB5\u0BBF\u0B9F\u0BC1\u0BAE\u0BC1\u0BB1\u0BC8\u0B95\u0BB3\u0BCD",
  fontFixTitle: "\u0B87\u0BA4\u0BCD\u0BA4\u0BB3\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BCD \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1\u0BB0\u0BC1\u0BB5\u0BC8 \u0BAE\u0BC7\u0BAE\u0BCD\u0BAA\u0B9F\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1",
  fontFixDesc: "Noto Tamil \u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1\u0BB0\u0BC1\u0BB5\u0BC8 \u0B87\u0BA4\u0BCD\u0BA4\u0BB3\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BCD \u0BAA\u0BAF\u0BA9\u0BCD\u0BAA\u0B9F\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1",
  localeTN: "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD\u0BA8\u0BBE\u0B9F\u0BC1 (TN)",
  localeSL: "\u0B87\u0BB2\u0B99\u0BCD\u0B95\u0BC8 (SL)",
  noCurrency: "\u0B8E\u0BA3\u0BCD \u0BAE\u0B9F\u0BCD\u0B9F\u0BC1\u0BAE\u0BCD",
  unsupportedYear: "\u0B87\u0BA8\u0BCD\u0BA4 \u0B86\u0BA3\u0BCD\u0B9F\u0BBF\u0BB1\u0BCD\u0B95\u0BBE\u0BA9 \u0B85\u0BB0\u0B9A\u0BC1 \u0BB5\u0BBF\u0B9F\u0BC1\u0BAE\u0BC1\u0BB1\u0BC8\u0BA4\u0BCD \u0BA4\u0BB0\u0BB5\u0BC1 \u0B87\u0BB2\u0BCD\u0BB2\u0BC8.",
};

export function stringsFor(lang: UiLang): UiStrings {
  return lang === "ta" ? TA : EN;
}
