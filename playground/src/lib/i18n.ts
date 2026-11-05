import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "ta" | "en";

export interface Translations {
  siteTitle: string;
  siteSubtitle: string;
  privacyBadge: string;
  tabs: {
    hub: string;
    publicTools: string;
    devTools: string;
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
    };
    numeral: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      currencyToggle: string;
      spokenToggle: string;
      formalWordsLabel: string;
      chequeWordsLabel: string;
      spokenWordsLabel: string;
      traditionalSymbolsLabel: string;
      fractionLabel: string;
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
    };
    scalar: {
      title: string;
      desc: string;
      inputPlaceholder: string;
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
    };
    codegen: {
      title: string;
      desc: string;
      selectLang: string;
      installCommand: string;
    };
    batch: {
      title: string;
      desc: string;
      dropzoneTitle: string;
      dropzoneSubtitle: string;
      progressLabel: string;
      completedNotice: string;
    };
  };
}

export const translations: Record<Language, Translations> = {
  ta: {
    siteTitle: "தமிழ் கருவிப் பட்டறை",
    siteSubtitle: "WebAssembly மூலம் இயங்கும் அதிவேகத் தமிழ் பயன்பாட்டுக் கருவிகள்",
    privacyBadge: "100% கணினிக்குள் மட்டுமே இயங்குகிறது (தகவல் கசியாது)",
    tabs: {
      hub: "முகப்பு",
      publicTools: "பொதுக் கருவிகள்",
      devTools: "ஆய்வகக் கருவிகள்"
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
      downloadFile: "கோப்பைப் பதிவிறக்கு"
    },
    tools: {
      codec: {
        title: "பழைய எழுத்துரு மாற்றி",
        desc: "பாமினி, TSCII, TAB, TAM, அஞ்சல், வானவில், LT-TM எழுத்துருக்களை ஒருங்குறியாக (Unicode) நொடியில் மாற்றுக.",
        inputPlaceholder: "மாற்ற வேண்டிய பழைய அல்லது தமிழ் ஒருங்குறி உரையை இங்கே ஒட்டவும் அல்லது தட்டச்சு செய்க...",
        outputPlaceholder: "மாற்றப்பட்ட உரை நிகழ்நேரத்தில் இங்கே தோன்றும்...",
        detectedEncoding: "கண்டறியப்பட்ட எழுத்துரு",
        confidence: "துல்லியம்",
        allProfiles: "ஆதரிக்கப்படும் எழுத்துருக்கள்"
      },
      numeral: {
        title: "எண் - சொல் & நாணய வடிவம்",
        desc: "எண்களையும் காசோலைத் தொகைகளையும் அதிகாரப்பூர்வ தமிழ் சொற்களாகவும் பாரம்பரிய தமிழ் எண்களாகவும் மாற்றுக.",
        inputPlaceholder: "எண்ணை அல்லது தொகையை உள்ளிடுக (எ.கா: 125000 அல்லது 1050.75)...",
        currencyToggle: "ரூபாய் / நாணய வடிவம்",
        spokenToggle: "பேச்சு வழக்கு வடிவம்",
        formalWordsLabel: "அதிகாரப்பூர்வ உரை வடிவம்",
        chequeWordsLabel: "காசோலை (Cheque) வடிவம்",
        spokenWordsLabel: "பேச்சு வழக்கு வடிவம்",
        traditionalSymbolsLabel: "பாரம்பரிய தமிழ் எண்கள்",
        fractionLabel: "பின்னச் சொற்கள்"
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
        locationFallback: "சென்னை நேரம் (தானியங்கித் தேர்வு)"
      },
      sorter: {
        title: "அகர வரிசைப்படுத்துதல்",
        desc: "தமிழ் இலக்கண மரபுப்படி (உயிர், மெய், உயிர்மெய்) சொற்களை நேர்த்தியாக அகர வரிசைப்படுத்துக.",
        inputPlaceholder: "வரிசைப்படுத்த வேண்டிய தமிழ் சொற்களை ஒவ்வொரு வரியாக உள்ளிடுக...",
        outputPlaceholder: "அகர வரிசைப்படுத்தப்பட்ட பட்டியல்...",
        sortAsc: "அகர வரிசை (அ → ன)",
        sortDesc: "எதிர் வரிசை (ன → அ)",
        removeDups: "மறுமுறை வந்த சொற்களை நீக்கு",
        syllableStats: "சொற்களின் எண்ணிக்கை"
      },
      scalar: {
        title: "எழுத்துரு & ஒருங்குறி அலகுகள்",
        desc: "தமிழ் எழுத்துக்களின் உட்பிரிவு, பதினறுமக் குறியீடு (Hex code) மற்றும் கண்ணுக்குத் தெரியாத குறியீடுகளை ஆய்வு செய்க.",
        inputPlaceholder: "ஆய்வு செய்ய வேண்டிய தமிழ் உரையை உள்ளிடுக (எ.கா: தமிழ், ஸ்ரீ)...",
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
        responseLabel: "பெறப்பட்ட முடிவு (JSON)"
      },
      codegen: {
        title: "நிரல் குறிமுறை உருவாக்கி",
        desc: "தேர்ந்தெடுக்கப்பட்ட பயன்பாட்டிற்கான Rust, Python, TypeScript, Dart நிரல் குறிமுறைகளை நொடியில் நகலெடுக்க.",
        selectLang: "நிரலாக்க மொழியைத் தேர்ந்தெடு:",
        installCommand: "நிறுவல் கட்டளை"
      },
      batch: {
        title: "கோப்புத் தொகுதி மாற்றி",
        desc: "பெரிய ஆவணங்கள் மற்றும் கோப்புகளை உங்கள் உலாவிக்குள்ளேயே பாதுகாப்பாக மொத்தமாக மாற்றுக.",
        dropzoneTitle: "கோப்புகளை இங்கே இழுத்துப் போடுக",
        dropzoneSubtitle: "அல்லது உங்கள் கணினியிலிருந்து கோப்பைத் தேர்ந்தெடுக்கவும் (txt, csv)",
        progressLabel: "மாற்றத்தின் முன்னேற்றம்",
        completedNotice: "மாற்றம் வெற்றிகரமாக முடிந்தது!"
      }
    }
  },
  en: {
    siteTitle: "Tamil Toolkit Playground",
    siteSubtitle: "High-performance Tamil language tools & diagnostics powered by WebAssembly",
    privacyBadge: "100% Client-Side Execution (Zero Data Leaves Your Device)",
    tabs: {
      hub: "Home",
      publicTools: "Public Tools",
      devTools: "Developer Tools"
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
      downloadFile: "Download File"
    },
    tools: {
      codec: {
        title: "Legacy Font & Encoding Converter",
        desc: "Bidirectional real-time conversion for Bamini, TSCII, TAB, TAM, Anjal, Vanavil, and LT-TM into modern Unicode.",
        inputPlaceholder: "Paste or type legacy encoded or Unicode text here...",
        outputPlaceholder: "Converted text appears here in real time...",
        detectedEncoding: "Detected Encoding",
        confidence: "Confidence",
        allProfiles: "Supported Encodings"
      },
      numeral: {
        title: "Numerals & Currency Formatter",
        desc: "Format numbers and financial amounts into formal Tamil words, legal cheque phrasing, and traditional numerals.",
        inputPlaceholder: "Enter a number or amount (e.g. 125000 or 1050.75)...",
        currencyToggle: "Currency (INR / LKR)",
        spokenToggle: "Spoken Colloquial",
        formalWordsLabel: "Formal Tamil Words",
        chequeWordsLabel: "Legal Cheque Format",
        spokenWordsLabel: "Spoken Variant",
        traditionalSymbolsLabel: "Traditional Tamil Numerals",
        fractionLabel: "Tamil Fractions"
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
        locationFallback: "Chennai Coordinates (Default)"
      },
      sorter: {
        title: "Agara Varisai Sorter",
        desc: "Sort Tamil words strictly according to classical Agara varisai grammatical order (உயிர், மெய், உயிர்மெய்).",
        inputPlaceholder: "Enter Tamil words, one per line...",
        outputPlaceholder: "Sorted word list...",
        sortAsc: "Ascending (அ → ன)",
        sortDesc: "Descending (ன → அ)",
        removeDups: "Remove Duplicates",
        syllableStats: "Word Count"
      },
      scalar: {
        title: "Unicode Scalar Inspector",
        desc: "Inspect Unicode codepoints, hex escapes, grapheme cluster boundaries, and detect invisible joiner codes.",
        inputPlaceholder: "Enter Tamil text to inspect (e.g. தமிழ், ஸ்ரீ)...",
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
        responseLabel: "JSON Response"
      },
      codegen: {
        title: "Code Snippet Generator",
        desc: "Generate copy-pasteable integration code for Rust, Python, TypeScript, and Dart matching the active parameters.",
        selectLang: "Select Language:",
        installCommand: "Install Command"
      },
      batch: {
        title: "Batch File Processor",
        desc: "Convert large documents and text archives locally in your browser using a background Web Worker.",
        dropzoneTitle: "Drop text files here to convert",
        dropzoneSubtitle: "or click to browse (.txt, .csv files)",
        progressLabel: "Conversion Progress",
        completedNotice: "Batch conversion complete!"
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

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem("tt_playground_lang");
      if (saved === "ta" || saved === "en") return saved;
      if (typeof navigator !== "undefined" && navigator.language && navigator.language.startsWith("ta")) {
        return "ta";
      }
    } catch {
      // ignore
    }
    return "en";
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem("tt_playground_lang", lang);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return React.createElement(
    LanguageContext.Provider,
    { value: { language, setLanguage, t: translations[language] } },
    children
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
