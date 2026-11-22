export type UiLang = "ta" | "en";

const STORAGE_KEY = "tamil-toolkit-word-lang";

export function getSavedLang(): UiLang {
  try {
    const saved = window.localStorage?.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "ta") return saved;
  } catch {
    // Ignore storage restriction in sandboxed iframes
  }
  return "en";
}

export function saveLang(lang: UiLang): void {
  try {
    window.localStorage?.setItem(STORAGE_KEY, lang);
  } catch {
    // Ignore storage restriction
  }
}

export const STRINGS: Record<UiLang, Record<string, string>> = {
  en: {
    tabType: "Type",
    tabPrepare: "Prepare",
    tabInsert: "Insert",
    quickConvertTitle: "Direct Live Typing (Bamini → Unicode)",
    quickConvertDesc: "Turn ON, click directly on your Word page, and type in Bamini (e.g. jkpo;). Characters convert live to Unicode Tamil as you type.",
    btnStartLive: "Start Live Word Typing (Bamini → Unicode)",
    btnConvertPara: "Convert Paragraph",
    btnConvertSel: "Convert Selection",
    composerTitle: "Optional Scratchpad Composer",
    composerHint: "Ctrl+Enter to insert",
    btnInsertWord: "Insert into Word",
    btnCopy: "Copy",
    prepareTitle: "1-Click Prepare Document",
    prepareDesc: "Convert legacy fonts, repair NFC, and hyphenate in a single batched pass.",
    btnPrepareRun: "Prepare Now",
    scopeSel: "Selection",
    scopePara: "Current Paragraph",
    scopeDoc: "Body & Tables",
    optHeadersFooters: "Include headers & footers",
    optConvert: "Convert legacy font → Unicode",
    optRepair: "Normalize NFC & repair pulli/kombu (keeps ZWJ/ZWNJ)",
    optHyphen: "Add canonical syllabic soft-hyphens",
    findReplaceTitle: "Tamil-Aware Find & Replace",
    sortTitle: "Akara Varisai Sorting",
    hyphenTitle: "Syllabic Hyphenation",
    inspectTitle: "Document Inspector",
    dateTitle: "Tamil Date & Panchangam Stamp",
    numTitle: "Numbers & Currency to Words",
    symTitle: "Traditional Fractions & Symbols",
  },
  ta: {
    tabType: "தட்டச்சு",
    tabPrepare: "தயார் செய்",
    tabInsert: "சேர்",
    quickConvertTitle: "நேரடி Word தட்டச்சு (பாமினி → Unicode)",
    quickConvertDesc: "இதை இயக்கி Word பக்கத்தில் நேரடியாக பாமினியில் தட்டச்சு செய்யவும் (எ.கா: jkpo;). எழுத்துகள் உடனுக்குடன் Unicode தமிழாக மாறும்.",
    btnStartLive: "நேரடி Word தட்டச்சைத் தொடங்கு (பாமினி → Unicode)",
    btnConvertPara: "பத்தியை மாற்று",
    btnConvertSel: "தேர்ந்தெடுத்ததை மாற்று",
    composerTitle: "விருப்ப சோதனைப் பலகை",
    composerHint: "Ctrl+Enter சேர்க்க",
    btnInsertWord: "Word-இல் சேர்",
    btnCopy: "நகலெடு",
    prepareTitle: "ஒரே கிளிக்கில் ஆவணம் தயார்",
    prepareDesc: "எழுத்துரு மாற்றம், NFC சீரமைப்பு, சொல் பிரிப்பு ஆகியவற்றை ஒரே சுற்றில் செய்யவும்.",
    btnPrepareRun: "இப்போது தயார் செய்",
    scopeSel: "தேர்வு",
    scopePara: "தற்போதைய பத்தி",
    scopeDoc: "உடல் & அட்டவணை",
    optHeadersFooters: "தலைப்பு & அடிக்குறிப்பு சேர்",
    optConvert: "பழைய எழுத்துரு → Unicode மாற்று",
    optRepair: "NFC & புள்ளி/கொம்பு சீரமைப்பு (ZWJ/ZWNJ காக்கும்)",
    optHyphen: "தமிழ் அசை மென்-இணைப்பு சேர்",
    findReplaceTitle: "தமிழ் தேடல் & மாற்றம்",
    sortTitle: "அகரவரிசை வரிசைப்படுத்தல்",
    hyphenTitle: "சொல் பிரிப்பு (Hyphenation)",
    inspectTitle: "ஆவண ஆய்வு",
    dateTitle: "தமிழ் நாள்காட்டி & பஞ்சாங்கம்",
    numTitle: "எண் & பண எழுத்துக்கள்",
    symTitle: "பண்டைய பின்னங்கள் & குறியீடுகள்",
  },
};
