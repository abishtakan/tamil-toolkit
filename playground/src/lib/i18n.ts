import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

export type Language = "ta" | "en";

export interface Translations {
  siteTitle: string;
  siteSubtitle: string;
  documentTitle: string;
  privacyBadge: string;
  tabs: {
    hub: string;
    publicTools: string;
    devTools: string;
  };
  nav: {
    switchPrompt: string;
    currentLanguageName: string;
    switchLanguageName: string;
    footerNotice: string;
  };
  actions: {
    copy: string;
    copied: string;
    clear: string;
    swap: string;
    loadSample: string;
    autoDetect: string;
    manualSelect: string;
    runNow: string;
    downloadFile: string;
    openTool: string;
    inspect: string;
  };
  hub: {
    heroBadge: string;
    engineStatus: string;
    quickJump: string;
    encodingsSupported: string;
    realtimeHeading: string;
    realtimeDesc: string;
    devToolsHeading: string;
    devToolsDesc: string;
    featuredBadge: string;
    launchTool: string;
    tags: {
      realtime: string;
      financial: string;
      solar: string;
      collation: string;
      unicode: string;
      api: string;
      code: string;
      batch: string;
    };
  };
  tools: {
    codec: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      outputPlaceholder: string;
      detectedEncoding: string;
      confidence: string;
      allProfiles: string;
      directionLegacyToUnicode: string;
      directionUnicodeToLegacy: string;
      inputLegacyLabel: string;
      inputUnicodeLabel: string;
      outputUnicodeLabel: string;
      outputLegacyLabel: string;
    };
    numeral: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      inputLabel: string;
      currencyToggle: string;
      spokenToggle: string;
      formalWordsLabel: string;
      chequeWordsLabel: string;
      spokenWordsLabel: string;
      traditionalSymbolsLabel: string;
      fractionLabel: string;
      spokenVariantBadge: string;
      classicalTamilBadge: string;
      classicalNotationHeading: string;
    };
    calendar: {
      title: string;
      desc: string;
      dateSelectLabel: string;
      tamilDateLabel: string;
      thiruvalluvarYearLabel: string;
      cycleYearLabel: string;
      nakshatraLabel: string;
      tithiLabel: string;
      rahuKalamLabel: string;
      yamagandamLabel: string;
      gulikaiLabel: string;
      holidayLabel: string;
      locationPrompt: string;
      locationFallback: string;
      coordsLabel: string;
      gpsLocationLabel: string;
      chennaiFallbackLabel: string;
      yearFallback: string;
    };
    sorter: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      outputPlaceholder: string;
      sortAsc: string;
      sortDesc: string;
      removeDups: string;
      syllableStats: string;
      inputWordsLabel: string;
      collationOutputLabel: string;
      wordsCountSuffix: string;
    };
    scalar: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      inputLabel: string;
      scalarCountLabel: string;
      clusterCountLabel: string;
      invisibleNotice: string;
      noInvisibleNotice: string;
    };
    dispatcher: {
      title: string;
      desc: string;
      presetLabel: string;
      sendRequest: string;
      latencyLabel: string;
      responseLabel: string;
      payloadLabel: string;
      statusSuccess: string;
      statusError: string;
      responsePlaceholder: string;
    };
    codegen: {
      title: string;
      desc: string;
      selectLang: string;
      installCommand: string;
      snippetHeading: string;
      tabCodec: string;
      tabNumeral: string;
      tabCalendar: string;
    };
    batch: {
      title: string;
      desc: string;
      dropzoneTitle: string;
      dropzoneSubtitle: string;
      progressLabel: string;
      completedNotice: string;
      formatError: string;
    };
  };
}

export const translations: Record<Language, Translations> = {
  ta: {
    siteTitle: "தமிழ் கருவிப் பட்டறை",
    siteSubtitle: "WebAssembly மூலம் இயங்கும் அதிவேகத் தமிழ் பயன்பாட்டுக் கருவிகள்",
    documentTitle: "தமிழ் கருவிப் பட்டறை | Tamil Toolkit Playground",
    privacyBadge: "100% கணினிக்குள் மட்டுமே இயங்குகிறது (தகவல் கசியாது)",
    tabs: {
      hub: "முகப்பு",
      publicTools: "பொதுக் கருவிகள்",
      devTools: "ஆய்வகக் கருவிகள்"
    },
    nav: {
      switchPrompt: "Change language",
      currentLanguageName: "தமிழ்",
      switchLanguageName: "English",
      footerNotice: "100% உங்கள் கணினியிலேயே இயங்குகிறது (Zero server transmission). தரவுகள் எங்கும் அனுப்பப்படுவதில்லை."
    },
    actions: {
      copy: "நகலெடு",
      copied: "நகலெடுக்கப்பட்டது!",
      clear: "அழி",
      swap: "திசை மாற்று",
      loadSample: "உதாரணம்",
      autoDetect: "தானியங்கி கண்டறிதல்",
      manualSelect: "எழுத்துருவைத் தேர்ந்தெடு",
      runNow: "இயக்கு",
      downloadFile: "கோப்பைப் பதிவிறக்கு",
      openTool: "திறக்குக",
      inspect: "ஆய்வு செய்"
    },
    hub: {
      heroBadge: "தமிழ் ஒருங்குறி, எழுத்துரு & பஞ்சாங்கப் பணித்தளம்",
      engineStatus: "WebAssembly இயந்திரம் தயார் (Offline)",
      quickJump: "நேரடிப் பயன்பாடுகள்",
      encodingsSupported: "7 எழுத்துருக்கள் ஆதரிக்கப்படுகின்றன",
      realtimeHeading: "சொல், எழுத்துரு & நாட்காட்டிக் கருவிகள்",
      realtimeDesc: "பழைய எழுத்துருக்களை ஒருங்குறியாக மாற்றுதல், காசோலை எண்களைச் சொற்களாக்குதல், மற்றும் மரபு நாட்காட்டி.",
      devToolsHeading: "பொறியியல் ஆய்வகம் & ஒருங்குறித் தரவுகள்",
      devToolsDesc: "நேரடி Rust WebAssembly இயக்கம், நிரல் உருவாக்கிகள், மற்றும் ஒருங்குறி எழுத்துக் கூட்ட ஆய்வி.",
      featuredBadge: "முதன்மைக் கருவி",
      launchTool: "பயன்படுத்துக",
      tags: {
        realtime: "நிகழ்நேரம்",
        financial: "நிதி",
        solar: "சூரியன்",
        collation: "அகரவரிசை",
        unicode: "ஒருங்குறி",
        api: "வழங்கி",
        code: "நிரல்",
        batch: "தொகுதி"
      }
    },
    tools: {
      codec: {
        title: "பழைய எழுத்துரு மாற்றி",
        desc: "பாமினி, TSCII, TAB, TAM, அஞ்சல், வானவில், LT-TM எழுத்துருக்களை ஒருங்குறியாக (Unicode) நொடியில் மாற்றுக.",
        inputPlaceholder: "மாற்ற வேண்டிய பழைய அல்லது தமிழ் ஒருங்குறி உரையை இங்கே ஒட்டவும் அல்லது தட்டச்சு செய்க...",
        outputPlaceholder: "மாற்றப்பட்ட உரை நிகழ்நேரத்தில் இங்கே தோன்றும்...",
        detectedEncoding: "கண்டறியப்பட்ட எழுத்துரு",
        confidence: "துல்லியம்",
        allProfiles: "ஆதரிக்கப்படும் எழுத்துருக்கள்",
        directionLegacyToUnicode: "  ஒருங்குறி (Unicode)",
        directionUnicodeToLegacy: "  பழைய எழுத்துரு",
        inputLegacyLabel: "உள்ளீடு (பழைய எழுத்துரு):",
        inputUnicodeLabel: "உள்ளீடு (தமிழ் ஒருங்குறி):",
        outputUnicodeLabel: "வெளியீடு (ஒருங்குறி):",
        outputLegacyLabel: "வெளியீடு (பழைய எழுத்துரு):"
      },
      numeral: {
        title: "எண் - சொல் & நாணய வடிவம்",
        desc: "எண்களையும் காசோலைத் தொகைகளையும் அதிகாரப்பூர்வ தமிழ் சொற்களாகவும் பாரம்பரிய தமிழ் எண்களாகவும் மாற்றுக.",
        inputPlaceholder: "எண்ணை அல்லது தொகையை உள்ளிடுக (எ.கா: 125000 அல்லது 1050.75)...",
        inputLabel: "எண் அல்லது நிதித் தொகை:",
        currencyToggle: "ரூபாய் / நாணய வடிவம்",
        spokenToggle: "பேச்சு வழக்கு வடிவம்",
        formalWordsLabel: "அதிகாரப்பூர்வ உரை வடிவம்",
        chequeWordsLabel: "காசோலை (Cheque) வடிவம்",
        spokenWordsLabel: "பேச்சு வழக்கு வடிவம்",
        traditionalSymbolsLabel: "பாரம்பரிய தமிழ் எண்கள்",
        fractionLabel: "பின்னச் சொற்கள்",
        spokenVariantBadge: "பேச்சு வழக்கு",
        classicalTamilBadge: "செவ்வியல் தமிழ் எண்கள்",
        classicalNotationHeading: "செவ்வியல் தமிழ் எண் குறியீடு"
      },
      calendar: {
        title: "தமிழ் நாட்காட்டி & பஞ்சாங்கம்",
        desc: "தமிழ் சூரிய மாதம், திருவள்ளுவர் ஆண்டு, 60-ஆண்டு சுழற்சி பெயர், நட்சத்திரம், திதி மற்றும் ராகு காலம் காண்க.",
        dateSelectLabel: "ஆங்கில தேதியைத் தேர்ந்தெடுக்க:",
        tamilDateLabel: "தமிழ் தேதி",
        thiruvalluvarYearLabel: "திருவள்ளுவர் ஆண்டு",
        cycleYearLabel: "வருடப் பெயர்",
        nakshatraLabel: "நட்சத்திரம்",
        tithiLabel: "திதி",
        rahuKalamLabel: "இராகு காலம்",
        yamagandamLabel: "எமகண்டம்",
        gulikaiLabel: "குளிகை",
        holidayLabel: "அரசு விடுமுறை நாட்கள்",
        locationPrompt: "இருப்பிடத்தைப் பெறுக",
        locationFallback: "சென்னை நேரம் (தானியங்கித் தேர்வு)",
        coordsLabel: "பஞ்சாங்கக் கணக்கீட்டு ஆயத்தொலைவுகள்:",
        gpsLocationLabel: "தற்போதைய இருப்பிடம் (GPS)",
        chennaiFallbackLabel: "சென்னை (தானியங்கி தேர்வு)",
        yearFallback: "தமிழ் ஆண்டு"
      },
      sorter: {
        title: "அகர வரிசைப்படுத்துதல்",
        desc: "தமிழ் இலக்கண மரபுப்படி (உயிர், மெய், உயிர்மெய்) சொற்களை நேர்த்தியாக அகர வரிசைப்படுத்துக.",
        inputPlaceholder: "வரிசைப்படுத்த வேண்டிய தமிழ் சொற்களை ஒவ்வொரு வரியாக உள்ளிடுக...",
        outputPlaceholder: "அகர வரிசைப்படுத்தப்பட்ட பட்டியல்...",
        sortAsc: "அகர வரிசை (அ → ன)",
        sortDesc: "எதிர் வரிசை (ன → அ)",
        removeDups: "மறுமுறை வந்த சொற்களை நீக்கு",
        syllableStats: "சொற்களின் எண்ணிக்கை",
        inputWordsLabel: "உள்ளீடு (ஒரு வரிக்கு ஒரு சொல்):",
        collationOutputLabel: "வரிசைப்படுத்தப்பட்ட முடிவு:",
        wordsCountSuffix: "சொற்கள்"
      },
      scalar: {
        title: "எழுத்துரு & ஒருங்குறி அலகுகள்",
        desc: "தமிழ் எழுத்துக்களின் உட்பிரிவு, பதினாறுமக் குறியீடு (Hex code) மற்றும் கண்ணுக்குத் தெரியாத குறியீடுகளை ஆய்வு செய்க.",
        inputPlaceholder: "ஆய்வு செய்ய வேண்டிய தமிழ் உரையை உள்ளிடுக (எ.கா: தமிழ், ஸ்ரீ)...",
        inputLabel: "ஆய்வு செய்ய வேண்டிய உரை:",
        scalarCountLabel: "ஒருங்குறி அலகுகள் (Scalars)",
        clusterCountLabel: "எழுத்துக் கூட்டங்கள் (Clusters)",
        invisibleNotice: "கண்ணுக்குத் தெரியாத குறியீடுகள் (ZWJ / ZWNJ) கண்டறியப்பட்டன!",
        noInvisibleNotice: "கண்ணுக்குத் தெரியாத கட்டுப்பாட்டுக் குறியீடுகள் இல்லை (தூய உரை)"
      },
      dispatcher: {
        title: "நேரடி ஆய்வகம் (Dispatcher)",
        desc: "டூல்கிட்டின் முழு இயந்திரத்திற்கும் நேரடி JSON கோரிக்கைகளை அனுப்பி உடனடி முடிவுகளைக் காண்க.",
        presetLabel: "மாதிரி கோரிக்கையைத் தேர்ந்தெடு:",
        sendRequest: "கோரிக்கையை அனுப்பு",
        latencyLabel: "இயக்க நேரம்",
        responseLabel: "பெறப்பட்ட முடிவு (JSON)",
        payloadLabel: "JSON கோரிக்கை (Request Payload):",
        statusSuccess: "வெற்றி",
        statusError: "பிழை",
        responsePlaceholder: "கோரிக்கையின் முடிவு இங்கே தோன்றும் ('கோரிக்கையை அனுப்பு' கிளிக் செய்க)"
      },
      codegen: {
        title: "நிரல் குறிமுறை உருவாக்கி",
        desc: "தேர்ந்தெடுக்கப்பட்ட பயன்பாட்டிற்கான Rust, Python, TypeScript, Dart நிரல் குறிமுறைகளை நொடியில் நகலெடுக்க.",
        selectLang: "நிரலாக்க மொழியைத் தேர்ந்தெடு:",
        installCommand: "நிறுவல் கட்டளை",
        snippetHeading: "இணைப்புக் குறியீடு (Code Snippet)",
        tabCodec: "எழுத்துரு மாற்றி",
        tabNumeral: "எண் - சொல்",
        tabCalendar: "நாட்காட்டி"
      },
      batch: {
        title: "கோப்புத் தொகுதி மாற்றி",
        desc: "பெரிய ஆவணங்கள் மற்றும் கோப்புகளை உங்கள் உலாவிக்குள்ளேயே பாதுகாப்பாக மொத்தமாக மாற்றுக.",
        dropzoneTitle: "கோப்புகளை இங்கே இழுத்துப் போடுக",
        dropzoneSubtitle: "அல்லது உங்கள் கணினியிலிருந்து கோப்பைத் தேர்ந்தெடுக்கவும் (.txt, .csv)",
        progressLabel: "மாற்றத்தின் முன்னேற்றம்",
        completedNotice: "மாற்றம் வெற்றிகரமாக முடிந்தது!",
        formatError: "ஆதரிக்கப்படாத கோப்பு வடிவம். .txt அல்லது .csv கோப்புகளை மட்டுமே பதிவேற்றவும்."
      }
    }
  },
  en: {
    siteTitle: "Tamil Toolkit Playground",
    siteSubtitle: "High-performance Tamil language tools & diagnostics powered by WebAssembly",
    documentTitle: "Tamil Toolkit Playground | WebAssembly Diagnostics",
    privacyBadge: "100% Client-Side Execution (Zero Data Leaves Your Device)",
    tabs: {
      hub: "Home",
      publicTools: "Public Tools",
      devTools: "Developer Tools"
    },
    nav: {
      switchPrompt: "மொழியை மாற்ற",
      currentLanguageName: "English",
      switchLanguageName: "தமிழ்",
      footerNotice: "100% client-side WebAssembly execution (Zero server transmission). No data ever leaves your browser."
    },
    actions: {
      copy: "Copy",
      copied: "Copied!",
      clear: "Clear",
      swap: "Swap",
      loadSample: "Sample",
      autoDetect: "Auto-Detect",
      manualSelect: "Select Font",
      runNow: "Run",
      downloadFile: "Download File",
      openTool: "Open Tool",
      inspect: "Inspect"
    },
    hub: {
      heroBadge: "Tamil Script, Numeral & Calendar Workbench",
      engineStatus: "WASM Engine Ready (Offline)",
      quickJump: "Direct Utilities",
      encodingsSupported: "7 Legacy Encodings Supported",
      realtimeHeading: "Script, Numeral & Calendar Utilities",
      realtimeDesc: "Legacy font conversion, legal cheque numeral formatting, and classical solar calendar diagnostics.",
      devToolsHeading: "Diagnostic Console & Unicode Inspector",
      devToolsDesc: "Raw WebAssembly dispatcher execution, polyglot SDK generation, and scalar boundary inspection.",
      featuredBadge: "Featured Tool",
      launchTool: "Open Utility",
      tags: {
        realtime: "Real-time",
        financial: "Financial",
        solar: "Solar / Drik",
        collation: "Collation",
        unicode: "Unicode",
        api: "Dispatcher",
        code: "Code",
        batch: "Batch"
      }
    },
    tools: {
      codec: {
        title: "Legacy Font & Encoding Converter",
        desc: "Bidirectional real-time conversion for Bamini, TSCII, TAB, TAM, Anjal, Vanavil, and LT-TM into modern Unicode.",
        inputPlaceholder: "Paste or type legacy encoded or Unicode text here...",
        outputPlaceholder: "Converted text appears here in real time...",
        detectedEncoding: "Detected Encoding",
        confidence: "Confidence",
        allProfiles: "Supported Encodings",
        directionLegacyToUnicode: "  Unicode",
        directionUnicodeToLegacy: "  Legacy Font",
        inputLegacyLabel: "Input (Legacy Text / Font):",
        inputUnicodeLabel: "Input (Tamil Unicode):",
        outputUnicodeLabel: "Output (Modern Unicode):",
        outputLegacyLabel: "Output (Legacy Encoded Font):"
      },
      numeral: {
        title: "Numerals & Currency Formatter",
        desc: "Format numbers and financial amounts into formal Tamil words, legal cheque phrasing, and traditional numerals.",
        inputPlaceholder: "Enter a number or amount (e.g. 125000 or 1050.75)...",
        inputLabel: "Number or Financial Amount:",
        currencyToggle: "Currency (INR / LKR)",
        spokenToggle: "Spoken Colloquial",
        formalWordsLabel: "Formal Tamil Words",
        chequeWordsLabel: "Legal Cheque Format",
        spokenWordsLabel: "Spoken Variant",
        traditionalSymbolsLabel: "Traditional Tamil Numerals",
        fractionLabel: "Tamil Fractions",
        spokenVariantBadge: "Spoken Colloquial Variant",
        classicalTamilBadge: "Classical Tamil",
        classicalNotationHeading: "Classical Tamil Numeral Notation"
      },
      calendar: {
        title: "Calendar & Panchangam Explorer",
        desc: "Explore Tamil solar months, Thiruvalluvar year, 60-year cycle titles, nakshatra, tithi, and daylight periods.",
        dateSelectLabel: "Select Gregorian Date:",
        tamilDateLabel: "Tamil Solar Date",
        thiruvalluvarYearLabel: "Thiruvalluvar Year",
        cycleYearLabel: "60-Year Cycle Name",
        nakshatraLabel: "Nakshatra",
        tithiLabel: "Tithi",
        rahuKalamLabel: "Rahu Kalam",
        yamagandamLabel: "Yamagandam",
        gulikaiLabel: "Gulikai",
        holidayLabel: "Official Public Holidays",
        locationPrompt: "Use Current Location",
        locationFallback: "Chennai Coordinates (Default)",
        coordsLabel: "Panchangam Calculation Coordinates:",
        gpsLocationLabel: "Current Location (GPS)",
        chennaiFallbackLabel: "Chennai (Fallback)",
        yearFallback: "Tamil Year"
      },
      sorter: {
        title: "Agara Varisai Sorter",
        desc: "Sort Tamil words strictly according to classical Agara varisai grammatical order (உயிர், மெய், உயிர்மெய்).",
        inputPlaceholder: "Enter Tamil words, one per line...",
        outputPlaceholder: "Sorted word list...",
        sortAsc: "Ascending (அ → ன)",
        sortDesc: "Descending (ன → அ)",
        removeDups: "Remove Duplicates",
        syllableStats: "Word Count",
        inputWordsLabel: "Input words (one per line):",
        collationOutputLabel: "Collation Output:",
        wordsCountSuffix: "words"
      },
      scalar: {
        title: "Unicode Scalar Inspector",
        desc: "Inspect Unicode codepoints, hex escapes, grapheme cluster boundaries, and detect invisible joiner codes.",
        inputPlaceholder: "Enter Tamil text to inspect (e.g. தமிழ், ஸ்ரீ)...",
        inputLabel: "Tamil String to Inspect (Input):",
        scalarCountLabel: "Unicode Scalars",
        clusterCountLabel: "Grapheme Clusters",
        invisibleNotice: "Invisible control codes (ZWJ / ZWNJ) detected!",
        noInvisibleNotice: "No invisible control codes detected (Clean text)"
      },
      dispatcher: {
        title: "Dispatcher Sandbox",
        desc: "Execute raw JSON requests directly against the unified Rust WebAssembly dispatcher.",
        presetLabel: "Choose Preset Request:",
        sendRequest: "Send Request",
        latencyLabel: "Execution Latency",
        responseLabel: "JSON Response",
        payloadLabel: "JSON Request Payload:",
        statusSuccess: "Success",
        statusError: "Error",
        responsePlaceholder: "Response will appear here (Click 'Send Request')"
      },
      codegen: {
        title: "Code Snippet Generator",
        desc: "Generate copy-pasteable integration code for Rust, Python, TypeScript, and Dart matching the active parameters.",
        selectLang: "Select Language:",
        installCommand: "Install Command",
        snippetHeading: "Integration Snippet (Example Code)",
        tabCodec: "Font Converter",
        tabNumeral: "Numerals & Words",
        tabCalendar: "Calendar"
      },
      batch: {
        title: "Batch File Processor",
        desc: "Convert large documents and text archives locally in your browser using a background Web Worker.",
        dropzoneTitle: "Drop text files here to convert",
        dropzoneSubtitle: "or click to browse (.txt, .csv files)",
        progressLabel: "Conversion Progress",
        completedNotice: "Batch conversion complete!",
        formatError: "Unsupported file format. Please upload .txt or .csv files."
      }
    }
  }
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType>({
  language: "ta",
  setLanguage: () => {},
  t: translations.ta
});

function resolveInitialLanguage(): Language {
  if (typeof window === "undefined") return "ta";
  try {
    // 1. URL search parameter (?lang=ta or ?lang=en)
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get("lang");
    if (urlLang === "ta" || urlLang === "en") {
      return urlLang;
    }

    // 2. Local storage
    const saved = localStorage.getItem("tt_playground_lang");
    if (saved === "ta" || saved === "en") {
      return saved;
    }

    // 3. Browser language
    if (typeof navigator !== "undefined" && navigator.language && navigator.language.startsWith("ta")) {
      return "ta";
    }
  } catch {
    // ignore security / storage restrictions
  }
  return "en";
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(resolveInitialLanguage);

  const setLanguage = useCallback((newLang: Language) => {
    setLanguageState(newLang);
    try {
      localStorage.setItem("tt_playground_lang", newLang);
      
      // Update URL query parameter seamlessly without full reload
      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        url.searchParams.set("lang", newLang);
        window.history.replaceState(null, "", url.toString());
      }
    } catch {
      // ignore storage/history restriction
    }
  }, []);

  // Sync DOM attributes and title
  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.lang = language;
    document.documentElement.dir = "ltr";
    document.title = translations[language].documentTitle;
  }, [language]);

  // Sync with browser back/forward navigation
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handlePopState = () => {
      const urlLang = new URLSearchParams(window.location.search).get("lang");
      if (urlLang === "ta" || urlLang === "en") {
        setLanguageState(urlLang);
      }
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  return React.createElement(
    LanguageContext.Provider,
    { value: { language, setLanguage, t: translations[language] } },
    children
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
