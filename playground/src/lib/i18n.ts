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
  shell: {
    homeLabel: string;
    searchPlaceholder: string;
    noToolsFound: string;
    clearSearch: string;
    openMenu: string;
    closeMenu: string;
    themeDark: string;
    themeLight: string;
    engineReady: string;
    engineLoading: string;
    offlineNote: string;
  };
  navGroups: {
    words: string;
    writing: string;
    reference: string;
    developer: string;
  };
  home: {
    heroSummary: string;
    searchPlaceholder: string;
    searchAction: string;
    quickStartLabel: string;
    quickBamini: string;
    quickCheque: string;
    quickCalendar: string;
    quickClean: string;
    developerSectionTitle: string;
    developerSectionDesc: string;
    dictionaryCountSuffix: string;
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
      targetFontLabel: string;
      errorPolicyLabel: string;
      policyStrict: string;
      policyPreserve: string;
      hexModeToggle: string;
      detectedCandidatesLabel: string;
      sampleTsciiHex: string;
      importPdf: string;
      importingPdf: string;
      pdfNoTextLayer: string;
      pdfExtractedSummary: string;
    };
    translit: {
      title: string;
      desc: string;
      schemeLabel: string;
      bidirectionalBadge: string;
      keyboardOnlyBadge: string;
      dirToTamil: string;
      dirToLatin: string;
      inputLatinLabel: string;
      inputTamilLabel: string;
      outputTamilLabel: string;
      outputLatinLabel: string;
      inputPlaceholder: string;
      outputPlaceholder: string;
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
      modeNumber: string;
      modeInr: string;
      modeLkr: string;
      localeTN: string;
      localeSL: string;
      tabCurrencyWords: string;
      tabTraditionalDigits: string;
      tabFractionsRanges: string;
      tabDatesMath: string;
      currencyLabel: string;
      regionLabel: string;
      inputTypeLabel: string;
      modeCurrency: string;
      modeOrdinal: string;
      modeDigitSeq: string;
      inputDigitsLabel: string;
      outputDigitsLabel: string;
      digitsLatin: string;
      digitsTamil: string;
      groupingToggle: string;
      groupingInternational: string;
      formattedAmountLabel: string;
      resultWordsLabel: string;
      tradFormatHeading: string;
      tradParseHeading: string;
      tradInputLabel: string;
      tradSymbolsInputLabel: string;
      tradParsePlaceholder: string;
      itnHeading: string;
      itnInputLabel: string;
      itnPlaceholder: string;
      digitScriptHeading: string;
      digitScriptInputPlaceholder: string;
      convertToTamil: string;
      convertToLatin: string;
      fractionCalcHeading: string;
      wholeLabel: string;
      numeratorLabel: string;
      denominatorLabel: string;
      fractionSymbolLabel: string;
      fractionWordsLabel: string;
      percentHeading: string;
      percentInputLabel: string;
      percentRatioLabel: string;
      rangeHeading: string;
      rangeStartLabel: string;
      rangeEndLabel: string;
      rangeStartIncl: string;
      rangeEndIncl: string;
      rangeOutputLabel: string;
      dateFormatHeading: string;
      dateStyleLabel: string;
      styleShort: string;
      styleMedium: string;
      styleLong: string;
      styleFull: string;
      weekdayLabel: string;
      dateMathHeading: string;
      startDateLabel: string;
      endDateLabel: string;
      dateDifferenceLabel: string;
      daysSuffix: string;
      addUnitLabel: string;
      addAmountLabel: string;
      unitDays: string;
      unitMonths: string;
      unitYears: string;
      resultingDateLabel: string;
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
      yogaLabel: string;
      karanaLabel: string;
      sunriseLabel: string;
      sunsetLabel: string;
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
      todayButton: string;
      prevDay: string;
      nextDay: string;
      cityLabel: string;
      panchangamHeading: string;
      daylightHeading: string;
      outOfBoundsNotice: string;
      tabDaily: string;
      tabConvertYear: string;
      tabFestivals: string;
      tabCompare: string;
      profileLabel: string;
      profileThirukanitham: string;
      profileVakya: string;
      digitsToggle: string;
      atTimeLabel: string;
      atTimeHeading: string;
      transitionsHeading: string;
      noTransitions: string;
      panchangamError: string;
      reverseConvertHeading: string;
      tamilYearLabel: string;
      tamilMonthLabel: string;
      tamilDayLabel: string;
      gregorianResultLabel: string;
      addTamilDateHeading: string;
      addButtonLabel: string;
      yearMonthsHeading: string;
      monthCol: string;
      startDateCol: string;
      endDateCol: string;
      daysCol: string;
      observancesHeading: string;
      monthFilterAll: string;
      holidaysHeading: string;
      jurisdictionTN: string;
      jurisdictionSL: string;
      lunarPhasesHeading: string;
      noEvents: string;
      compareHeading: string;
      differingFieldsLabel: string;
      thirukanithamCol: string;
      vakyaCol: string;
      solarDateLabel: string;
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
      profileAgara: string;
      profileUyirmei: string;
      compareHeading: string;
      wordALabel: string;
      wordBLabel: string;
      compareResultBefore: string;
      compareResultAfter: string;
      compareResultEqual: string;
      sortKeyLabel: string;
      searchKeyLabel: string;
      foldedKeyLabel: string;
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
      sampleInvisible: string;
      rustInspectHeading: string;
      nfcStatusLabel: string;
      nfdStatusLabel: string;
      ezhuthuCountLabel: string;
      classificationsHeading: string;
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
      shortcutHint: string;
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
      tabLexicon: string;
      tabHyphenator: string;
      tabNormalizer: string;
      tabSorter: string;
    };
    batch: {
      title: string;
      desc: string;
      dropzoneTitle: string;
      dropzoneSubtitle: string;
      progressLabel: string;
      completedNotice: string;
      formatError: string;
      encodingLabel: string;
      convertAnother: string;
    };
    symbols: {
      title: string;
      desc: string;
      searchPlaceholder: string;
      categoryAll: string;
      categoryFractions: string;
      categoryLand: string;
      categoryVolume: string;
      categoryCurrency: string;
      symbolDetailsHeading: string;
      glyphLabel: string;
      codepointLabel: string;
      nameLabel: string;
      rationalLabel: string;
      decimalLabel: string;
      periodLabel: string;
      copySymbolButton: string;
      quickLookupHeading: string;
      quickLookupPlaceholder: string;
      noMatches: string;
      liveCalcHeading: string;
      inspectAnySymbolLabel: string;
      inspectAnyPlaceholder: string;
      fractionBuilderLabel: string;
      buildFractionBtn: string;
    };
    hyphenator: {
      title: string;
      desc: string;
      tabWord: string;
      tabText: string;
      tabWrap: string;
      wordInputLabel: string;
      wordPlaceholder: string;
      textInputLabel: string;
      textPlaceholder: string;
      syllableChipsHeading: string;
      breakpointsHeading: string;
      breakpointsDesc: string;
      codaBindingNotice: string;
      codaBindingRule: string;
      marginHeading: string;
      leftMarginLabel: string;
      rightMarginLabel: string;
      delimiterLabel: string;
      delimiterHyphen: string;
      delimiterBullet: string;
      delimiterSlash: string;
      delimiterSoft: string;
      delimiterNone: string;
      syllablesCount: string;
      breakpointsCount: string;
      noBreakpoints: string;
      shortWordNotice: string;
      showSoftHyphensToggle: string;
      copyWordButton: string;
      copyNoHyphenButton: string;
      copyHtmlButton: string;
      copyTextButton: string;
      columnWidthLabel: string;
      columnWidthLetters: string;
      compareToggle: string;
      defaultWrapHeading: string;
      syllabicWrapHeading: string;
      lineCount: string;
      sampleWordsHeading: string;
      sampleParagraphButton: string;
      errOrphanedPulli: string;
      errOrphanedVisiri: string;
      errOrphanedDiacritic: string;
      errPureConsonant: string;
      errAytham: string;
      integrationsTitle: string;
      integrationsDesc: string;
      downloadOxtButton: string;
      downloadDicButton: string;
      libreofficeGuide: string;
      indesignGuide: string;
      scribusGuide: string;
      formattedSyllablesLabel: string;
      settingsToggle: string;
      visualPreviewHeading: string;
      browserFlowHeading: string;
      setupGuidesLabel: string;
    };
    letter: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      inputLabel: string;
      syllablesCount: string;
      uyirCount: string;
      meiCount: string;
      uyirmeiCount: string;
      granthaCount: string;
      selectedSyllableHeading: string;
      rootConsonantLabel: string;
      vowelLabel: string;
      vowelSignLabel: string;
      codepointsLabel: string;
      classificationLabel: string;
      selectPrompt: string;
      moraLabel: string;
      cognateLabel: string;
      quantityLabel: string;
      tabBreakdown: string;
      tabComposer: string;
      tabOlippasai: string;
      composerMeiLabel: string;
      composerUyirLabel: string;
      composedResultLabel: string;
      allVowelsRowLabel: string;
      olippasaiHeading: string;
      codaYes: string;
      codaNo: string;
      cognateCheckHeading: string;
      cognateYes: string;
      cognateNo: string;
    };
    normalizer: {
      title: string;
      desc: string;
      inputPlaceholder: string;
      inputLabel: string;
      outputLabel: string;
      nfcLabel: string;
      nfdLabel: string;
      repairedLabel: string;
      foldLabel: string;
      statusClean: string;
      statusAnomalies: string;
      anomaliesFixedLabel: string;
      copyNormalizedButton: string;
      diffHeading: string;
      sampleVowelsButton: string;
      sampleDefectiveButton: string;
      codepointInspectorHeading: string;
      nfcBanner: string;
      nfdBanner: string;
      repairedBanner: string;
      foldBanner: string;
      decomposedCountLabel: string;
      profileComprehensive: string;
      profileMayangoli: string;
      profileGrantha: string;
      repairOptionsHeading: string;
      optCollapsePulli: string;
      optReorderKombu: string;
      optStripShy: string;
      optStripJoiners: string;
      diagDuplicatePulli: string;
      diagVisualKombu: string;
      diagStrippedControls: string;
      diagTotalRepairs: string;
    };
    lexicon: {
      title: string;
      desc: string;
      searchLabel: string;
      searchPlaceholder: string;
      searchButton: string;
      exactPreserveNote: string;
      packsLabel: string;
      selectAllAvailable: string;
      clearSelection: string;
      packUnavailableBadge: string;
      packLoadedBadge: string;
      packNotBuiltBadge: string;
      regionFilterLabel: string;
      registerFilterLabel: string;
      allRegionsOption: string;
      allRegistersOption: string;
      unknownScopeNote: string;
      examplesHeading: string;
      corpusInventoryHeading: string;
      fullProfileBadge: string;
      activeBuildLabel: string;
      distinctFormsLabel: string;
      entriesLabel: string;
      sensesLabel: string;
      historicalExclusionHeading: string;
      historicalExclusionBody: string;
      loadingEngine: string;
      noDataBuildHeading: string;
      noDataBuildBody: string;
      statusMatched: string;
      statusNotFound: string;
      statusError: string;
      canonicalQueryLabel: string;
      notFoundHeading: string;
      notFoundBody: string;
      entryIdLabel: string;
      posLabel: string;
      formsHeading: string;
      sensesHeading: string;
      examplesListHeading: string;
      relationsHeading: string;
      annotationsHeading: string;
      regionScopeLabel: string;
      registerScopeLabel: string;
      unrestrictedScope: string;
      unknownScope: string;
      humanAcceptanceBadge: string;
      autoAcceptanceBadge: string;
      mixedAcceptanceBadge: string;
      provenanceToggle: string;
      sourceLinksHeading: string;
      rawInspectorHeading: string;
      rawRequestLabel: string;
      rawResponseLabel: string;
      downloadRequest: string;
      downloadResponse: string;
      contractPresetsToggle: string;
      contractPresetsDesc: string;
      resetToAvailablePacks: string;
      packCoreDesc: string;
      packNamesTaxaDesc: string;
      packRegionalDesc: string;
      packTerminologyDesc: string;
      staleMetadataBadge: string;
      staleMetadataWarning: string;
      verifyingManifests: string;
      unavailableCounts: string;
      partialProfileBadge: string;
      attributionNoticesHeading: string;
      firstLoadSizeNote: string;
      offlineCacheHeading: string;
      offlineCacheNote: string;
      dataDetailsToggle: string;
    };
  };
}

export const translations: Record<Language, Translations> = {
  ta: {
    siteTitle: "தமிழ் கருவிப் பட்டறை",
    siteSubtitle: "அகராதி, எழுத்துரு மாற்றம், தமிழ் நாட்காட்டி மற்றும் எழுத்துப் பகுப்பாய்வு — உங்கள் உலாவியிலேயே தனிப்பட்ட முறையில் இயங்கும் பணித்தளம்.",
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
      footerNotice: "100% உங்கள் உலாவியிலேயே இயங்குகிறது. தரவுகள் எந்தச் சேவையகத்திற்கும் அனுப்பப்படுவதில்லை."
    },
    shell: {
      homeLabel: "முகப்பு",
      searchPlaceholder: "கருவிகளைத் தேடுக…",
      noToolsFound: "பொருந்தும் கருவிகள் இல்லை",
      clearSearch: "தேடலை அழி",
      openMenu: "பட்டியலைத் திற",
      closeMenu: "பட்டியலை மூடு",
      themeDark: "இருண்ட தோற்றம்",
      themeLight: "வெளிச்ச தோற்றம்",
      engineReady: "ஆஃப்லைன் தயார்",
      engineLoading: "இயந்திரம் ஏற்றப்படுகிறது…",
      offlineNote: "உங்கள் சாதனத்தில் மட்டும் இயங்கும்"
    },
    navGroups: {
      words: "அகராதி & சொற்கள்",
      writing: "எழுத்து & மாற்றம்",
      reference: "எண்கள் & நாட்காட்டி",
      developer: "உருவாக்குநர் கருவிகள்"
    },
    home: {
      heroSummary: "சொற்களின் பொருள் காணவும், பழைய எழுத்துருக்களை மாற்றவும், காசோலைத் தொகைகளைத் தமிழில் எழுதவும், தினசரிப் பஞ்சாங்கத்தைப் பார்க்கவுமான எளிய தமிழ் பணித்தளம்.",
      searchPlaceholder: "தமிழ் சொல் அல்லது ஆங்கிலப் பொருளைத் தேடுங்கள் (எ.கா: நன்றி, அறம், கடல்)…",
      searchAction: "அகராதியில் தேடு",
      quickStartLabel: "விரைவுப் பணிகள்:",
      quickBamini: "பாமினி → ஒருங்குறி மாற்றி",
      quickCheque: "காசோலைத் தொகை தமிழில்",
      quickCalendar: "இன்றைய தமிழ் தேதி & ராகு காலம்",
      quickClean: "பிழையான தமிழ் உரை சீரமைப்பு",
      developerSectionTitle: "உருவாக்குநர் & ஒருங்குறி ஆய்வகம்",
      developerSectionDesc: "ஒருங்குறி குறியீடுகள், JSON இயக்கி மற்றும் நிரல் மாதிரிகள்.",
      dictionaryCountSuffix: "சொற்கள்"
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
      encodingsSupported: "12 எழுத்துருக்கள் & பிரெய்லி ஆதரவு",
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
        title: "பழைய எழுத்துரு & பிரெய்லி மாற்றி",
        desc: "பாமினி, TSCII, TAB, TAM, அஞ்சல், வானவில், LT-TM, செந்தமிழ், ஸ்ரீ-தமிழ், அமுதம், தினபூமி மற்றும் பாரதி பிரெய்லியை ஒருங்குறியாக மாற்றுக.",
        inputPlaceholder: "மாற்ற வேண்டிய பழைய அல்லது தமிழ் ஒருங்குறி உரையை இங்கே ஒட்டவும் அல்லது தட்டச்சு செய்க...",
        outputPlaceholder: "மாற்றப்பட்ட உரை இங்கே தோன்றும்...",
        detectedEncoding: "கண்டறியப்பட்ட எழுத்துரு",
        confidence: "துல்லியம்",
        allProfiles: "மூல எழுத்துரு",
        directionLegacyToUnicode: "பழையது → ஒருங்குறி",
        directionUnicodeToLegacy: "ஒருங்குறி → பழையது",
        inputLegacyLabel: "உள்ளீடு (பழைய எழுத்துரு)",
        inputUnicodeLabel: "உள்ளீடு (தமிழ் ஒருங்குறி)",
        outputUnicodeLabel: "வெளியீடு (நவீன ஒருங்குறி)",
        outputLegacyLabel: "வெளியீடு (பழைய எழுத்துரு)",
        targetFontLabel: "இலக்கு எழுத்துரு",
        errorPolicyLabel: "பிழைக் கொள்கை",
        policyStrict: "கண்டிப்பானது (Strict)",
        policyPreserve: "மூலம் காக்க (Preserve)",
        hexModeToggle: "Hex பைட்டுகள் (8-bit)",
        detectedCandidatesLabel: "கண்டறியப்பட்ட வாய்ப்புகள்:",
        sampleTsciiHex: "TSCII (Hex)",
        importPdf: "PDF இறக்குமதி",
        importingPdf: "PDF படிக்கப்படுகிறது...",
        pdfNoTextLayer: "இந்த PDF கோப்பில் தேர்ந்தெடுக்கக்கூடிய உரை அடுக்கு இல்லை (ஸ்கேன் செய்யப்பட்ட பட PDF; OCR இங்கு செய்யப்படுவதில்லை).",
        pdfExtractedSummary: "உலாவியில் PDF உரை பிரித்தெடுக்கப்பட்டது (பதிவேற்றம் இல்லை)"
      },
      translit: {
        title: "ஒலிபெயர்ப்பு & தமிழ்99 தட்டச்சு",
        desc: "ISO 15919, சென்னை அகராதி, ITRANS, Harvard-Kyoto, Tanglish ஒலியியல் மற்றும் தமிழ்99, அஞ்சல், சுரதா பாமினி விசைப்பலகை மாற்றம்.",
        schemeLabel: "ஒலிபெயர்ப்பு / விசைப்பலகை முறை",
        bidirectionalBadge: "இருவழி (லத்தீன் ↔ தமிழ்)",
        keyboardOnlyBadge: "தமிழ் உள்ளீடு மட்டும்",
        dirToTamil: "லத்தீன் → தமிழ்",
        dirToLatin: "தமிழ் → லத்தீன்",
        inputLatinLabel: "உள்ளீடு (லத்தீன் / விசைப்பலகை)",
        inputTamilLabel: "உள்ளீடு (தமிழ் ஒருங்குறி)",
        outputTamilLabel: "வெளியீடு (தமிழ் ஒருங்குறி)",
        outputLatinLabel: "வெளியீடு (லத்தீன் ஒலிபெயர்ப்பு)",
        inputPlaceholder: "ஒலிபெயர்க்க வேண்டிய உரையை இங்கே தட்டச்சு செய்க...",
        outputPlaceholder: "மாற்றப்பட்ட உரை இங்கே தோன்றும்..."
      },
      numeral: {
        title: "எண் - சொல் & காசோலை வடிவம்",
        desc: "எண்களையும் காசோலைத் தொகைகளையும் அதிகாரப்பூர்வ தமிழ் சொற்களாகவும் பாரம்பரிய தமிழ் எண்களாகவும் மாற்றுக.",
        inputPlaceholder: "எண்ணை அல்லது தொகையை உள்ளிடுக (எ.கா: 125000 அல்லது 1050.75)...",
        inputLabel: "எண் அல்லது தொகை",
        currencyToggle: "ரூபாய் / நாணய வடிவம்",
        spokenToggle: "பேச்சு வழக்கு வடிவம்",
        formalWordsLabel: "அதிகாரப்பூர்வ தமிழ் சொற்கள்",
        chequeWordsLabel: "காசோலை (Cheque) வடிவம்",
        spokenWordsLabel: "பேச்சு வழக்கு வடிவம்",
        traditionalSymbolsLabel: "பாரம்பரிய தமிழ் எண்கள்",
        fractionLabel: "பின்னச் சொற்கள்",
        spokenVariantBadge: "பேச்சு வழக்கு",
        classicalTamilBadge: "செவ்வியல் தமிழ் எண்கள்",
        classicalNotationHeading: "செவ்வியல் தமிழ் எண் குறியீடு",
        modeNumber: "சாதாரண எண்",
        modeInr: "இந்திய ரூபாய் (₹ INR)",
        modeLkr: "இலங்கை ரூபாய் (Rs LKR)",
        localeTN: "தமிழ்நாடு (TN)",
        localeSL: "இலங்கை (SL)",
        tabCurrencyWords: "நாணயம் & சொற்கள்",
        tabTraditionalDigits: "தமிழ் எண்கள் & இலக்கங்கள்",
        tabFractionsRanges: "பின்னங்கள், % & வரம்பு",
        tabDatesMath: "தமிழ் தேதி & நாள் கணிதம்",
        currencyLabel: "நாணயம்",
        regionLabel: "வட்டாரம் / மொழி வழக்கு",
        inputTypeLabel: "வடிவம்",
        modeCurrency: "நாணயம்",
        modeOrdinal: "வரிசை எண் (1வது, 2வது…)",
        modeDigitSeq: "இலக்கத் தொடர் (தொலைபேசி/OTP)",
        inputDigitsLabel: "உள்ளீட்டு எண்கள்",
        outputDigitsLabel: "வெளியீட்டு எண்கள்",
        digitsLatin: "லத்தீன் (0–9)",
        digitsTamil: "தமிழ் (௦–௯)",
        groupingToggle: "இந்திய பிரிவு (1,25,000)",
        groupingInternational: "பன்னாட்டு பிரிவு (125,000)",
        formattedAmountLabel: "வடிவமைக்கப்பட்ட எண்",
        resultWordsLabel: "தமிழ் சொற்கள்",
        tradFormatHeading: "அரபு எண் → பழந்தமிழ் எண்",
        tradParseHeading: "பழந்தமிழ் எண் → அரபு எண்",
        tradInputLabel: "முழு எண் (1 – 10,00,000)",
        tradSymbolsInputLabel: "பழந்தமிழ் எண் குறியீடுகள்",
        tradParsePlaceholder: "எ.கா: ௲௨௱௫௰",
        itnHeading: "தமிழ் சொற்கள் → எண் (ITN)",
        itnInputLabel: "அதிகாரப்பூர்வ தமிழ் எண் சொற்கள்",
        itnPlaceholder: "எ.கா: நூற்று இருபத்து மூன்று",
        digitScriptHeading: "உரையில் இலக்க மாற்றம்",
        digitScriptInputPlaceholder: "எண்களைக் கொண்ட தமிழ் அல்லது ஆங்கில உரையை உள்ளிடுக (எ.கா: ஆண்டு 2026)...",
        convertToTamil: "தமிழ் எண்களாக மாற்று (௦–௯)",
        convertToLatin: "லத்தீன் எண்களாக மாற்று (0–9)",
        fractionCalcHeading: "பின்னம் & கலப்பு பின்னக் கணிப்பான்",
        wholeLabel: "முழு எண்",
        numeratorLabel: "தொகுதி (Numerator)",
        denominatorLabel: "பகுதி (Denominator)",
        fractionSymbolLabel: "யூனிகோட் குறியீடு",
        fractionWordsLabel: "தமிழ் பின்னச் சொற்கள்",
        percentHeading: "சதவீதம் & விகிதம் (% ↔ Ratio)",
        percentInputLabel: "சதவீதம் (எ.கா: 12.5%)",
        percentRatioLabel: "விகித மதிப்பு",
        rangeHeading: "எண் வரம்பு வடிவமைப்பு",
        rangeStartLabel: "தொடக்கம்",
        rangeEndLabel: "முடிவு",
        rangeStartIncl: "தொடக்கத்தை உள்ளடக்கு [",
        rangeEndIncl: "முடிவை உள்ளடக்கு ]",
        rangeOutputLabel: "வடிவமைக்கப்பட்ட வரம்பு",
        dateFormatHeading: "ஆங்கில தேதியைத் தமிழ் உரையில் எழுதுக",
        dateStyleLabel: "வடிவமைப்பு நடை",
        styleShort: "குறுகியது",
        styleMedium: "நடுத்தரம்",
        styleLong: "நீண்டது",
        styleFull: "முழுமையானது (கிழமையுடன்)",
        weekdayLabel: "கிழமை",
        dateMathHeading: "தேதி இடைவெளி & கூட்டல்",
        startDateLabel: "தொடக்கத் தேதி",
        endDateLabel: "முடிவுத் தேதி",
        dateDifferenceLabel: "நாட்கள் வித்தியாசம்",
        daysSuffix: "நாட்கள்",
        addUnitLabel: "அலகு",
        addAmountLabel: "எண்ணிக்கை (+/-)",
        unitDays: "நாட்கள்",
        unitMonths: "மாதங்கள்",
        unitYears: "ஆண்டுகள்",
        resultingDateLabel: "புதிய தேதி"
      },
      calendar: {
        title: "தமிழ் நாட்காட்டி & பஞ்சாங்கம்",
        desc: "தமிழ் சூரிய மாதம், திருவள்ளுவர் ஆண்டு, 60-ஆண்டு சுழற்சி பெயர், நட்சத்திரம், திதி, சூரிய உதயம் மற்றும் ராகு காலம் காண்க.",
        dateSelectLabel: "ஆங்கில தேதி",
        tamilDateLabel: "தமிழ் சூரிய தேதி",
        thiruvalluvarYearLabel: "திருவள்ளுவர் ஆண்டு",
        cycleYearLabel: "வருடப் பெயர்",
        nakshatraLabel: "நட்சத்திரம்",
        tithiLabel: "திதி",
        yogaLabel: "யோகம்",
        karanaLabel: "கரணம்",
        sunriseLabel: "சூரிய உதயம்",
        sunsetLabel: "சூரிய அஸ்தமனம்",
        rahuKalamLabel: "இராகு காலம்",
        yamagandamLabel: "எமகண்டம்",
        gulikaiLabel: "குளிகை",
        holidayLabel: "அரசு விடுமுறை நாட்கள்",
        locationPrompt: "தற்போதைய இடம் (GPS)",
        locationFallback: "சென்னை நேரம் (தானியங்கித் தேர்வு)",
        coordsLabel: "நகரம் / இருப்பிடம்",
        gpsLocationLabel: "தற்போதைய இருப்பிடம் (GPS)",
        chennaiFallbackLabel: "சென்னை (தானியங்கி தேர்வு)",
        yearFallback: "தமிழ் ஆண்டு",
        todayButton: "இன்று",
        prevDay: "முந்தைய நாள்",
        nextDay: "அடுத்த நாள்",
        cityLabel: "இடம்",
        panchangamHeading: "பஞ்சாங்கக் கூறுகள் (உதய நேரத்தில்)",
        daylightHeading: "பகல் நேரக் காலங்கள்",
        outOfBoundsNotice: "உங்கள் GPS இருப்பிடம் தமிழ்நாடு/இலங்கை எல்லைக்கு வெளியே உள்ளதால் சென்னை நேரம் பயன்படுத்தப்படுகிறது.",
        tabDaily: "தினசரி நாள்காட்டி",
        tabConvertYear: "தமிழ் ↔ ஆங்கிலம் & ஆண்டு",
        tabFestivals: "விழாக்கள், விடுமுறை & சந்திரன்",
        tabCompare: "திருக்கணிதம் vs வாக்கியம்",
        profileLabel: "கணிப்பு முறை",
        profileThirukanitham: "திருக்கணிதம்",
        profileVakya: "வாக்கியம் (உஜ்ஜைனி)",
        digitsToggle: "தமிழ் எண்கள் (௦–௯)",
        atTimeLabel: "குறிப்பிட்ட நேரத்தில் (HH:MM)",
        atTimeHeading: "தேர்ந்தெடுக்கப்பட்ட நேரப் பஞ்சாங்கம்",
        transitionsHeading: "இன்றைய பஞ்சாங்க மாற்றங்கள்",
        noTransitions: "இந்த நாளில் கூடுதல் மாற்றங்கள் இல்லை",
        panchangamError: "இந்த தேதி/பகுதிக்கு தரவு வரம்புக்கு வெளியே உள்ளது",
        reverseConvertHeading: "தமிழ் சூரிய தேதி → ஆங்கில தேதி",
        tamilYearLabel: "தமிழ் சூரிய ஆண்டு",
        tamilMonthLabel: "தமிழ் மாதம்",
        tamilDayLabel: "தமிழ் நாள்",
        gregorianResultLabel: "ஆங்கில தேதி",
        addTamilDateHeading: "தமிழ் தேதியுடன் நாட்கள்/மாதங்கள்/ஆண்டுகள் கூட்டுக",
        addButtonLabel: "கணக்கிடு",
        yearMonthsHeading: "12 தமிழ் மாத அட்டவணை",
        monthCol: "மாதம்",
        startDateCol: "தொடக்கம்",
        endDateCol: "முடிவு (முன் நாள்)",
        daysCol: "நாட்கள்",
        observancesHeading: "விரதங்கள் & திருவிழாக்கள்",
        monthFilterAll: "அனைத்து மாதங்களும்",
        holidaysHeading: "அரசு விடுமுறைப் பட்டியல்",
        jurisdictionTN: "தமிழ்நாடு (TN)",
        jurisdictionSL: "இலங்கை (SL)",
        lunarPhasesHeading: "சந்திர நிலைகள் (அமாவாசை / பௌர்ணமி)",
        noEvents: "நிகழ்வுகள் எதுவும் இல்லை",
        compareHeading: "திருக்கணிதம் vs வாக்கியம் ஒப்பீடு",
        differingFieldsLabel: "வேறுபடும் புலங்கள்:",
        thirukanithamCol: "திருக்கணிதம்",
        vakyaCol: "வாக்கியம் (Civil)",
        solarDateLabel: "தமிழ் சூரிய தேதி"
      },
      sorter: {
        title: "அகர வரிசைப்படுத்துதல்",
        desc: "தமிழ் இலக்கண மரபுப்படி (உயிர், மெய், உயிர்மெய்) சொற்களை நேர்த்தியாக அகர வரிசைப்படுத்துக.",
        inputPlaceholder: "வரிசைப்படுத்த வேண்டிய தமிழ் சொற்களை ஒவ்வொரு வரியாக உள்ளிடுக...",
        outputPlaceholder: "அகர வரிசைப்படுத்தப்பட்ட பட்டியல்...",
        sortAsc: "அகர வரிசை (அ → ன)",
        sortDesc: "எதிர் வரிசை (ன → அ)",
        removeDups: "நகல்களை நீக்கு",
        syllableStats: "சொற்களின் எண்ணிக்கை",
        inputWordsLabel: "உள்ளீடு (ஒரு வரிக்கு ஒரு சொல்)",
        collationOutputLabel: "வரிசைப்படுத்தப்பட்ட முடிவு",
        wordsCountSuffix: "சொற்கள்",
        profileAgara: "அகரவரிசை (மரபு)",
        profileUyirmei: "உயிர்மெய் முதன்மை",
        compareHeading: "இரு சொற்கள் ஒப்பீடு & வரிசைத் திறவுகோல்கள்",
        wordALabel: "சொல் A",
        wordBLabel: "சொல் B",
        compareResultBefore: "சொல் A முன்னால் வரும் (<)",
        compareResultAfter: "சொல் A பின்னால் வரும் (>)",
        compareResultEqual: "சொற்கள் சமம் (=)",
        sortKeyLabel: "வரிசைத் திறவுகோல் (Sort Key)",
        searchKeyLabel: "தேடல் திறவுகோல் (Search Key)",
        foldedKeyLabel: "மடிப்புத் தேடல் திறவுகோல் (Folded Key)"
      },
      scalar: {
        title: "ஒருங்குறி அலகு ஆய்வி",
        desc: "தமிழ் எழுத்துக்களின் உட்பிரிவு, பதினாறுமக் குறியீடு (Hex code) மற்றும் கண்ணுக்குத் தெரியாத குறியீடுகளை ஆய்வு செய்க.",
        inputPlaceholder: "ஆய்வு செய்ய வேண்டிய தமிழ் உரையை உள்ளிடுக (எ.கா: தமிழ், ஸ்ரீ)...",
        inputLabel: "ஆய்வு செய்ய வேண்டிய உரை",
        scalarCountLabel: "ஒருங்குறி அலகுகள் (Scalars)",
        clusterCountLabel: "எழுத்துக் கூட்டங்கள் (Clusters)",
        invisibleNotice: "கண்ணுக்குத் தெரியாத குறியீடுகள் (ZWJ / ZWNJ / SHY / BOM) கண்டறியப்பட்டன!",
        noInvisibleNotice: "கண்ணுக்குத் தெரியாத கட்டுப்பாட்டுக் குறியீடுகள் இல்லை (தூய உரை)",
        sampleInvisible: "ZWJ / NFD மாதிரி",
        rustInspectHeading: "Rust கட்டமைப்பு ஆய்வு (inspect_tamil_string)",
        nfcStatusLabel: "NFC நிலை",
        nfdStatusLabel: "NFD நிலை",
        ezhuthuCountLabel: "தமிழ் எழுத்து எண்ணிக்கை",
        classificationsHeading: "எழுத்து வகைப்பாடு (வல்லினம் / மெல்லினம் / இடையினம்)"
      },
      dispatcher: {
        title: "நேரடி ஆய்வகம் (Dispatcher)",
        desc: "டூல்கிட்டின் இயந்திரத்திற்கு நேரடி JSON கோரிக்கைகளை அனுப்பி உடனடி முடிவுகளைக் காண்க.",
        presetLabel: "மாதிரி கோரிக்கையைத் தேர்ந்தெடு:",
        sendRequest: "கோரிக்கையை அனுப்பு",
        latencyLabel: "இயக்க நேரம்",
        responseLabel: "பெறப்பட்ட முடிவு (JSON)",
        payloadLabel: "JSON கோரிக்கை",
        statusSuccess: "வெற்றி",
        statusError: "பிழை",
        responsePlaceholder: "கோரிக்கையின் முடிவு இங்கே தோன்றும்",
        shortcutHint: "Ctrl/⌘ + Enter மூலம் இயக்கலாம்"
      },
      codegen: {
        title: "நிரல் குறிமுறை உருவாக்கி",
        desc: "Rust, Python, TypeScript, Dart மொழிகளுக்கான இணைப்பு நிரல் மாதிரிகளை உடனே நகலெடுக்க.",
        selectLang: "நிரலாக்க மொழியைத் தேர்ந்தெடு:",
        installCommand: "நிறுவல் கட்டளை",
        snippetHeading: "மாதிரி நிரல்",
        tabCodec: "எழுத்துரு மாற்றி",
        tabNumeral: "எண் - சொல்",
        tabCalendar: "நாட்காட்டி",
        tabLexicon: "அகராதி",
        tabHyphenator: "அசை பிரிப்பு",
        tabNormalizer: "சீரமைப்பி",
        tabSorter: "அகரவரிசை"
      },
      batch: {
        title: "கோப்புத் தொகுதி மாற்றி",
        desc: "பெரிய ஆவணங்கள் மற்றும் கோப்புகளை உங்கள் உலாவிக்குள்ளேயே பாதுகாப்பாக மொத்தமாக மாற்றுக.",
        dropzoneTitle: "கோப்புகளை இங்கே இழுத்துப் போடுக",
        dropzoneSubtitle: "அல்லது கணினியிலிருந்து தேர்ந்தெடுக்கவும் (.txt, .csv)",
        progressLabel: "மாற்றத்தின் முன்னேற்றம்",
        completedNotice: "மாற்றம் வெற்றிகரமாக முடிந்தது!",
        formatError: "ஆதரிக்கப்படாத கோப்பு வடிவம். .txt அல்லது .csv கோப்புகளை மட்டுமே பதிவேற்றவும்.",
        encodingLabel: "மூல எழுத்துரு:",
        convertAnother: "மற்றொரு கோப்பை மாற்றுக"
      },
      symbols: {
        title: "பழந்தமிழ் பின்னங்கள் & குறியீடுகள்",
        desc: "பழந்தமிழர் பயன்படுத்திய பின்னங்கள் (முந்திரி, காணி, வீசம், கால்), நில அளவை, நாணய மற்றும் தானியக் குறியீடுகளை ஆய்வு செய்க.",
        searchPlaceholder: "குறியீடு, பெயர் அல்லது மதிப்பைத் தேடுக (எ.கா: காணி, 1/80, முக்கால்)...",
        categoryAll: "அனைத்தும்",
        categoryFractions: "பின்னங்கள்",
        categoryLand: "நில அளவை",
        categoryVolume: "முகத்தல் அளவை",
        categoryCurrency: "நாணயம் / எடை",
        symbolDetailsHeading: "குறியீட்டு விவரங்கள்",
        glyphLabel: "வரிவடிவம்",
        codepointLabel: "ஒருங்குறி (Unicode)",
        nameLabel: "பாரம்பரியப் பெயர்",
        rationalLabel: "விகித முறிவெண் (Fraction)",
        decimalLabel: "பதின்ம மதிப்பு (Decimal)",
        periodLabel: "வரலாற்றுப் பயன்பாடு",
        copySymbolButton: "குறியீட்டை நகலெடு",
        quickLookupHeading: "எண் / பின்னத்தைத் தேடுக",
        quickLookupPlaceholder: "எண்ணை உள்ளிடுக (எ.கா: 0.25 அல்லது 1/4)...",
        noMatches: "பொருத்தமான குறியீடுகள் எதுவும் கிடைக்கவில்லை",
        liveCalcHeading: "நேரடி Rust குறியீடு & பின்ன ஆய்வி (72 குறியீடுகள்)",
        inspectAnySymbolLabel: "எந்தவொரு தமிழ் குறியீட்டையும் ஆய்வு செய்க",
        inspectAnyPlaceholder: "குறியீட்டை உள்ளிடுக (எ.கா: 𑿔, ௹, ௳)...",
        fractionBuilderLabel: "விகித பின்னத்தைக் குறியீடாக மாற்றுக",
        buildFractionBtn: "மாற்று"
      },
      hyphenator: {
        title: "சொல் & பத்தி அசையசைப்பி",
        desc: "தமிழ் இலக்கண மரபுப்படி (ஒற்று அடுத்த வரியில் பிரியாத வண்ணம்) சொற்களை அசை பிரித்து, மென்-இணைப்புக் குறி மற்றும் வரி மடிப்பை ஒழுங்கு செய்க.",
        tabWord: "சொல் அசை பிரிப்பு",
        tabText: "பத்தி & மென்-இணைப்பு",
        tabWrap: "நிரல் வரி மடிப்பு",
        wordInputLabel: "ஆராய வேண்டிய சொல்",
        wordPlaceholder: "எ.கா: தமிழ்நாடு, பல்கலைக்கழகம், திருக்குறள்...",
        textInputLabel: "பத்தி உரை",
        textPlaceholder: "மென்-இணைப்புக் குறி சேர்க்க வேண்டிய தமிழ் உரை அல்லது பத்தியை உள்ளிடுக...",
        syllableChipsHeading: "சொல்லின் அசைக்கூறுகள்",
        breakpointsHeading: "அனுமதிக்கப்பட்ட பிரிவிடங்கள்",
        breakpointsDesc: "வரியின் இறுதியில் சொல் நீண்டு செல்லும்போது, அதனைப் பிரித்து (-) அடுத்த வரிக்குக் கொண்டு செல்லக்கூடிய இலக்கணப்படியான இடங்கள்.",
        codaBindingNotice: "மெய் ஒற்று விதி",
        codaBindingRule: "ஒற்று (புள்ளி எழுத்து) முந்தைய உயிருடனோ அல்லது உயிர்மெய்யுடனோ மட்டுமே சேர வேண்டும்; புதிய வரி மெய்யெழுத்தில் தொடங்கக் கூடாது.",
        marginHeading: "விளிம்பு வரம்புகள் & பிரிப்புக் குறி",
        leftMarginLabel: "தொடக்க விளிம்பு (குறைந்தபட்ச எழுத்துக்கள்)",
        rightMarginLabel: "முடிவு விளிம்பு (குறைந்தபட்ச எழுத்துக்கள்)",
        delimiterLabel: "பிரிப்புக் குறியீடு",
        delimiterHyphen: "இணைப்புக் குறி (-)",
        delimiterBullet: "நடுப்புள்ளி (·)",
        delimiterSlash: "சாய்வுக்கோடு (/)",
        delimiterSoft: "மென்-இணைப்பு (&shy;)",
        delimiterNone: "குறியீடு இன்றி (ZWSP)",
        syllablesCount: "அசைகள்",
        breakpointsCount: "பிரிவிடங்கள்",
        noBreakpoints: "இந்தச் சொல்லுக்கு தற்போதைய விளிம்பு அமைப்பில் பிரிவிடங்கள் இல்லை",
        shortWordNotice: "விளிம்பு வரம்புகளுக்குள் அடங்காத குறுகிய சொல்",
        showSoftHyphensToggle: "மென்-இணைப்புக் குறிகளைத் தெளிவாகக் காட்டு ([·])",
        copyWordButton: "Word / Docs-க்கு நகலெடு",
        copyNoHyphenButton: "இணைப்புக் குறியின்றி (ZWSP)",
        copyHtmlButton: "HTML (&shy;) நகலெடு",
        copyTextButton: "மென்-உரை நகலெடு",
        columnWidthLabel: "நிரல் அகலம் (எழுத்துக்கள்):",
        columnWidthLetters: "எழுத்துக்கள் / வரி",
        compareToggle: "வழக்கமான வரி மடிப்போடு ஒப்பிடுக",
        defaultWrapHeading: "வழக்கமான வரி மடிப்பு (ஒற்று பிரிந்து பிழையாகும்)",
        syllabicWrapHeading: "தமிழ் அசைசார் வரி மடிப்பு (இலக்கணப்படி சரியானது)",
        lineCount: "வரிகள்",
        sampleWordsHeading: "மாதிரிச் சொற்கள்:",
        sampleParagraphButton: "மாதிரிப் பத்தி",
        errOrphanedPulli: "(தனிப் புள்ளித் தொடக்கம்!)",
        errOrphanedVisiri: "(விசிறி மட்டும் தொடக்கம்!)",
        errOrphanedDiacritic: "(சிதைந்த குறியீடு தொடக்கம்!)",
        errPureConsonant: "(புள்ளி எழுத்தில் தொடக்கம்!)",
        errAytham: "(ஆய்த எழுத்தில் தொடக்கம்!)",
        integrationsTitle: "டெஸ்க்டாப் மென்பொருள்கள் & பதிப்பக ஒருங்கிணைப்பு",
        integrationsDesc: "LibreOffice, Adobe InDesign மற்றும் Scribus ஆகியவற்றிற்கான சொல் பிரிப்பான் அகராதி (.oxt / .dic).",
        downloadOxtButton: "LibreOffice நீட்டிப்பு (.oxt)",
        downloadDicButton: "Hunspell அகராதி (.dic)",
        libreofficeGuide: "LibreOffice வழிகாட்டி",
        indesignGuide: "InDesign வழிகாட்டி",
        scribusGuide: "Scribus வழிகாட்டி",
        formattedSyllablesLabel: "பிரிக்கப்பட்ட சொல்",
        settingsToggle: "அமைப்புகள்",
        visualPreviewHeading: "மென்-இணைப்புக் காட்சி",
        browserFlowHeading: "உலாவி வரி ஓட்டக் காட்சி",
        setupGuidesLabel: "வழிகாட்டிகள்:"
      },
      letter: {
        title: "சொல் & எழுத்து பகுப்பாய்வி",
        desc: "தமிழ் சொற்களை உயிர், மெய், உயிர்மெய், ஆய்தம் மற்றும் கிரந்த எழுத்துகளாகப் பிரித்து, அவற்றின் இலக்கணக் கட்டமைப்பை ஆராய்க.",
        inputPlaceholder: "பகுப்பாய்வு செய்ய வேண்டிய சொற்களை உள்ளிடுக (எ.கா: தமிழ்நாடு, புரட்சி, ஸ்ரீலங்கா)...",
        inputLabel: "பகுப்பாய்வு செய்ய வேண்டிய உரை",
        syllablesCount: "மொத்த எழுத்துகள்",
        uyirCount: "உயிர்",
        meiCount: "மெய்",
        uyirmeiCount: "உயிர்மெய்",
        granthaCount: "கிரந்தம்",
        selectedSyllableHeading: "எழுத்துக் கட்டமைப்பு",
        rootConsonantLabel: "அடிப்படை மெய்யெழுத்து",
        vowelLabel: "இணைந்த உயிரெழுத்து",
        vowelSignLabel: "உயிர்மெய்க் குறியீடு",
        codepointsLabel: "ஒருங்குறித் தொடர்",
        classificationLabel: "இலக்கண வகை",
        selectPrompt: "விவரங்களைக் காண ஓர் எழுத்தைத் தேர்ந்தெடுக்கவும்",
        moraLabel: "மாத்திரை (கால அளவு)",
        cognateLabel: "இன எழுத்து",
        quantityLabel: "எழுத்துக் கால அளவு",
        tabBreakdown: "எழுத்துப் பகுப்பு",
        tabComposer: "உயிர்மெய் இணைப்பி",
        tabOlippasai: "ஒலிப்பசை & இன எழுத்து",
        composerMeiLabel: "மெய்யெழுத்து",
        composerUyirLabel: "உயிரெழுத்து",
        composedResultLabel: "இணைந்த உயிர்மெய்",
        allVowelsRowLabel: "இந்த மெய்யின் 12 உயிர்மெய் வரிசை",
        olippasaiHeading: "ஒலிப்பசை பிரிப்பு (Olippasai)",
        codaYes: "மெய் ஒற்று உண்டு",
        codaNo: "திறந்த அசை",
        cognateCheckHeading: "இன எழுத்துச் சரிபார்ப்பு (are_cognates)",
        cognateYes: "இன எழுத்துக்கள் ஆகும்",
        cognateNo: "இன எழுத்துக்கள் அல்ல"
      },
      normalizer: {
        title: "ஒருங்குறி சீரமைப்பி",
        desc: "பிழையான புள்ளி, உடைந்த உயிர்மெய்க் குறிகள் மற்றும் தேவையற்ற குறியீடுகளைச் சரிசெய்து, தூய தமிழ் ஒருங்குறியாக மாற்றுக.",
        inputPlaceholder: "சீரமைக்க வேண்டிய தமிழ் உரையை உள்ளிடுக...",
        inputLabel: "மூல உரை",
        outputLabel: "சீரமைக்கப்பட்ட உரை",
        nfcLabel: "இயல்பு வடிவம் (NFC)",
        nfdLabel: "பிரித்த வடிவம் (NFD)",
        repairedLabel: "பிழைதிருத்தம்",
        foldLabel: "தேடல் மடிப்பு",
        statusClean: "தூய ஒருங்குறி (பிழை இல்லை)",
        statusAnomalies: "பிழைகள் சரிசெய்யப்பட்டன",
        anomaliesFixedLabel: "கண்டறியப்பட்ட பிழைகள்",
        copyNormalizedButton: "வெளியீட்டு உரையை நகலெடு",
        diffHeading: "சீரமைப்பு ஒப்பீடு",
        sampleVowelsButton: "இரட்டைக் குறியீடுகள் (கொ, கோ)",
        sampleDefectiveButton: "பிழை உரை மாதிரி",
        codepointInspectorHeading: "ஒருங்குறி பைட் வரிசை ஆய்வு",
        nfcBanner: "NFC (ஒருங்கிணைந்த வடிவம்): பிரிந்த இரட்டைக் குறியீடுகளை (ொ, ோ, ௌ) நிலையான ஒற்றை ஒருங்குறி வடிவமாக இணைக்கிறது.",
        nfdBanner: "NFD (பிரித்த வடிவம்): இரட்டை உயிர்மெய்க் குறிகளை (ொ, ோ, ௌ) கொம்பு (ெ/ே) மற்றும் துணைக்கால்/ளகரக் கூறுகளாகப் (ா/ௗ) பிரிக்கிறது. கீழே உள்ள ஒருங்குறி பைட் ஆய்வில் மாற்றத்தைக் காணலாம்.",
        repairedBanner: "பிழைதிருத்தம்: இரட்டைப் புள்ளிகள் சுருக்கப்பட்டு, சிதைந்த கொம்புகளும் மறைமுகக் குறியீடுகளும் சரிசெய்யப்பட்டு தூய NFC வடிவில் தரப்படுகிறது.",
        foldBanner: "தேடல் மடிப்பு: மயங்கொலி வேறுபாடுகள் (ள/ழ/ல, ண/ந/ன, ற/ர) மற்றும் கிரந்த எழுத்துக்களைச் (ஜ, ஷ, ஸ, ஹ, ஸ்ரீ, க்ஷ) சமப்படுத்தித் தேடலுக்கு உகந்ததாக்குகிறது.",
        decomposedCountLabel: "இரட்டைக் குறியீடுகள் பிரிக்கப்பட்டன",
        profileComprehensive: "முழு மடிப்பு",
        profileMayangoli: "மயங்கொலி மட்டும்",
        profileGrantha: "கிரந்தம் மட்டும்",
        repairOptionsHeading: "சீரமைப்புத் தேர்வுகள் & விவரங்கள்",
        optCollapsePulli: "இரட்டைப் புள்ளி சுருக்குதல்",
        optReorderKombu: "முன்நிற்கும் கொம்பு சீரமைப்பு",
        optStripShy: "மென்-இணைப்புக் குறியீடு (SHY) நீக்கம்",
        optStripJoiners: "மறைமுகக் குறியீடுகள் (ZWJ/ZWNJ) நீக்கம்",
        diagDuplicatePulli: "இரட்டைப் புள்ளிகள்",
        diagVisualKombu: "முன்நிற்கும் கொம்புகள்",
        diagStrippedControls: "நீக்கப்பட்ட மறைமுகக் குறிகள்",
        diagTotalRepairs: "மொத்தத் திருத்தங்கள்"
      },
      lexicon: {
        title: "தமிழ் அகராதி",
        desc: "தமிழ் மற்றும் ஆங்கில விக்சனரி தொகுப்புகளில் சொற்களின் பொருள், வட்டார வழக்குகள், எடுத்துக்காட்டுகள் மற்றும் ஆதாரங்களைத் தேடுக.",
        searchLabel: "சொல் தேடல் (இடைவெளி & இணைப்பிகள் மாற்றமின்றி):",
        searchPlaceholder: "தமிழ் தலைச்சொல்லை உள்ளிடுக (எ.கா: நன்றி, செப்பம், கோளாறு)...",
        searchButton: "தேடு",
        exactPreserveNote: "இடைவெளி, ZWJ/ZWNJ, மென்-இணைப்பி (SHY) நீக்கப்படாது; Rust NFC சமநிலையாக்கம் மட்டுமே.",
        packsLabel: "சொற்களஞ்சியத் தொகுப்புகள்:",
        selectAllAvailable: "கிடைப்பவை அனைத்தையும் தேர்ந்தெடு",
        clearSelection: "தேர்வை நீக்கு",
        packUnavailableBadge: "கிடைக்கவில்லை",
        packLoadedBadge: "ஏற்றப்பட்டது",
        packNotBuiltBadge: "இந்த WASM தொகுப்பில் இல்லை",
        regionFilterLabel: "பகுதி / வட்டார வடிகட்டி:",
        registerFilterLabel: "நடை வடிகட்டி:",
        allRegionsOption: "அனைத்துப் பகுதிகளும் (வடிகட்டியின்றி)",
        allRegistersOption: "அனைத்து நடைகளும் (வடிகட்டியின்றி)",
        unknownScopeNote: "நிரந்தரப் பகுதிப் பட்டியல் (சான்று இல்லாத செல்லுபடியாகும் குறியீடுகள் உட்பட) மற்றும் தேர்ந்தெடுக்கப்பட்ட தொகுப்புகளின் நடைக் குறியீடுகள் காட்டப்படும்; அறியப்படாத (unknown) வரம்புகள் ஊகிக்கப்படாது.",
        examplesHeading: "சரிபார்க்கப்பட்ட தொகுப்பு மாதிரிகள்:",
        corpusInventoryHeading: "தொகுப்பு எண்ணிக்கை & தரவு வரம்புகள்",
        fullProfileBadge: "முழு சுயவிவரத் தொகுப்பு (core + names_taxa + regional)",
        activeBuildLabel: "தற்போதைய WASM சுயவிவரம்:",
        distinctFormsLabel: "தனி வடிவங்கள்",
        entriesLabel: "பதிவுகள்",
        sensesLabel: "பொருள்கள்",
        historicalExclusionHeading: "நீக்கப்பட்ட வரலாற்றுத் தரவுகள் (307,243 பதிவுகள்)",
        historicalExclusionBody: "முந்தைய 307,243 வரலாற்றுப் பதிவுகள் (12 கோப்புகள்) சரிபார்க்கப்படாததால்/உரிம உறுதி இல்லாததால் விலக்கப்பட்டுத் தனிமைப்படுத்தப்பட்டுள்ளன (0 தகுதியான சான்றுகள்). தற்போதைய முழுத் தொகுப்பில் 9,410 தனி வடிவங்கள், 11,377 பதிவுகள், 25,742 பொருள்கள் உள்ளன; terminology தொகுப்பு இன்னும் கிடைக்கவில்லை.",
        loadingEngine: "தமிழ் அகராதி இயந்திரம் ஏற்றப்படுகிறது…",
        noDataBuildHeading: "இந்த உருவாக்கத்தில் சொற்களஞ்சியத் தரவு இல்லை",
        noDataBuildBody: "default உருவாக்கத்தில் தரவுத் தொகுப்புகள் இணைக்கப்படவில்லை.",
        statusMatched: "பொருந்திய பதிவுகள்",
        statusNotFound: "பதிவு கிடைக்கவில்லை",
        statusError: "பிழை",
        canonicalQueryLabel: "NFC வினவல்:",
        notFoundHeading: "துல்லியமான தலைச்சொல் எதுவும் கிடைக்கவில்லை",
        notFoundBody: "தேர்ந்தெடுக்கப்பட்ட தொகுப்புகளில் இந்த வடிவத்திற்குச் சரியான தலைச்சொல் பொருந்தவில்லை.",
        entryIdLabel: "பதிவு ID",
        posLabel: "சொல் வகை",
        formsHeading: "சொல் வடிவங்கள்",
        sensesHeading: "பொருள்கள்",
        examplesListHeading: "எடுத்துக்காட்டுகள்",
        relationsHeading: "தொடர்புகள்",
        annotationsHeading: "குறிப்புகள்",
        regionScopeLabel: "பகுதி வரம்பு",
        registerScopeLabel: "நடை வரம்பு",
        unrestrictedScope: "வரம்பற்றது (அனைத்துப் பகுதிகளும்)",
        unknownScope: "அறியப்படாதது (ஊகிக்கப்படவில்லை)",
        humanAcceptanceBadge: "மனித மதிப்பாய்வு (accepted_human)",
        autoAcceptanceBadge: "தானியங்கி மூலம் (accepted_auto_source)",
        mixedAcceptanceBadge: "மனித + தானியங்கி சான்றுகள்",
        provenanceToggle: "சான்று & ஆதார விவரங்கள்",
        sourceLinksHeading: "பாதுகாப்பான மூல இணைப்புகள்:",
        rawInspectorHeading: "மூல JSON கோரிக்கை & முடிவு",
        rawRequestLabel: "JSON கோரிக்கை",
        rawResponseLabel: "JSON முடிவு / பிழை",
        downloadRequest: "கோரிக்கையைப் பதிவிறக்கு",
        downloadResponse: "முடிவைப் பதிவிறக்கு",
        contractPresetsToggle: "உருவாக்குநர் ஒப்பந்தச் சோதனை மாதிரிகள்",
        contractPresetsDesc: "வெற்றுப் பட்டியல், அறியப்படாத/கிடைக்காத தொகுப்பு, தவறான வடிகட்டி, இடைவெளி/ZWJ மற்றும் NFD→NFC நடத்தைகளைச் சோதிக்க.",
        resetToAvailablePacks: "கிடைக்கும் தொகுப்புகளை மீட்டமை",
        packCoreDesc: "அடிப்படை தமிழ் அகராதித் தொகுப்பு",
        packNamesTaxaDesc: "சிறப்புப் பெயர்கள் & உயிரினப் பெயர்கள்",
        packRegionalDesc: "வட்டாரத் தமிழ் வழக்குத் தொகுப்பு (TN & SL)",
        packTerminologyDesc: "கலைச்சொல் தொகுப்பு (இன்னும் கிடைக்கவில்லை)",
        staleMetadataBadge: "பழைய / பொருந்தாத தரவு",
        staleMetadataWarning: "இயந்திரத்தின் PackInfo.manifest_sha256 மதிப்பு catalog-உடன் பொருந்தவில்லை; நிலையான எண்ணிக்கைகள் நிறுத்தி வைக்கப்பட்டுள்ளன.",
        verifyingManifests: "தொகுப்பு விவரங்கள் சரிபார்க்கப்படுகின்றன…",
        unavailableCounts: "கிடைக்கவில்லை / பொருந்தவில்லை",
        partialProfileBadge: "பகுதி சுயவிவரம்",
        attributionNoticesHeading: "பங்களிப்பு & உரிம அறிவிப்புகள் (CC-BY-SA-4.0):",
        firstLoadSizeNote: "முதல் முறை அகராதி இயந்திரம் (~46 MiB) பதிவிறக்கம் செய்யப்படும்; பின்னர் உலாவியில் ஆஃப்லைன் பயன்பாட்டிற்காகச் சேமிக்கப்படும்.",
        offlineCacheHeading: "முதல் பதிவிறக்க அளவு & ஆஃப்லைன் சேமிப்பு",
        offlineCacheNote: "முழு-தொகுப்பு உலாவி WASM தொகுப்பு ~46 MiB அளவு கொண்டது; ஆஃப்லைன் பயன்பாட்டிற்காகச் சேமிக்கப்படுகிறது.",
        dataDetailsToggle: "தரவு வரம்பு, விலக்கல்கள் & உரிமங்கள்"
      }
    }
  },
  en: {
    siteTitle: "Tamil Toolkit Playground",
    siteSubtitle: "Dictionary, legacy font conversion, Tamil calendar, numerals, and script utilities — running privately in your browser.",
    documentTitle: "Tamil Toolkit Playground | Language Workbench",
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
      footerNotice: "Runs 100% in your browser. Your text never leaves your device."
    },
    shell: {
      homeLabel: "Home",
      searchPlaceholder: "Find a tool…",
      noToolsFound: "No matching tools",
      clearSearch: "Clear search",
      openMenu: "Open navigation menu",
      closeMenu: "Close navigation menu",
      themeDark: "Dark theme",
      themeLight: "Light theme",
      engineReady: "Offline ready",
      engineLoading: "Loading engine…",
      offlineNote: "Runs locally on your device"
    },
    navGroups: {
      words: "Dictionary & Words",
      writing: "Writing & Conversion",
      reference: "Numbers & Calendar",
      developer: "Developer"
    },
    home: {
      heroSummary: "Look up Tamil words, convert legacy fonts like Bamini to Unicode, write cheque amounts in Tamil, and check today's solar calendar and Panchangam.",
      searchPlaceholder: "Look up a Tamil word or English meaning (e.g. நன்றி, அறம், water)…",
      searchAction: "Look up",
      quickStartLabel: "Common tasks:",
      quickBamini: "Convert Bamini → Unicode",
      quickCheque: "Write a Cheque in Tamil",
      quickCalendar: "Today's Tamil Date & Rahu Kalam",
      quickClean: "Clean Broken Unicode",
      developerSectionTitle: "Developer & Unicode Tools",
      developerSectionDesc: "Inspect Unicode scalars, send raw JSON requests, or copy SDK snippets.",
      dictionaryCountSuffix: "words"
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
      encodingsSupported: "12 Legacy Encodings & Braille Supported",
      realtimeHeading: "Script, Numeral & Calendar Utilities",
      realtimeDesc: "Legacy font conversion, legal cheque numeral formatting, and classical solar calendar tools.",
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
        title: "Legacy Font & Braille Converter",
        desc: "Convert between Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM, Senthamil, Shree-Tam, Softview, TBO, Bharathi Braille, and modern Tamil Unicode.",
        inputPlaceholder: "Paste or type text to convert...",
        outputPlaceholder: "Converted text appears here...",
        detectedEncoding: "Detected Font",
        confidence: "Confidence",
        allProfiles: "Source Encoding",
        directionLegacyToUnicode: "Legacy → Unicode",
        directionUnicodeToLegacy: "Unicode → Legacy",
        inputLegacyLabel: "Legacy Text",
        inputUnicodeLabel: "Tamil Unicode",
        outputUnicodeLabel: "Modern Unicode",
        outputLegacyLabel: "Legacy Font Output",
        targetFontLabel: "Target Font",
        errorPolicyLabel: "Error Policy",
        policyStrict: "Strict",
        policyPreserve: "Preserve Unknown",
        hexModeToggle: "Hex Bytes (8-bit)",
        detectedCandidatesLabel: "Detection Candidates:",
        sampleTsciiHex: "TSCII (Hex)",
        importPdf: "Import PDF",
        importingPdf: "Reading PDF...",
        pdfNoTextLayer: "No selectable text layer was found in this PDF (likely a scanned image PDF; client-side extraction does not run OCR).",
        pdfExtractedSummary: "Extracted PDF text layer locally in your browser (zero upload)"
      },
      translit: {
        title: "Transliteration & Tamil99",
        desc: "Convert Tamil using ISO 15919, Madras Lexicon, ITRANS, Harvard-Kyoto, Tanglish Phonetic, Tamil99, Anjal Phonetic, and Suratha Bamini.",
        schemeLabel: "Transliteration / Input Scheme",
        bidirectionalBadge: "Bidirectional (Latin ↔ Tamil)",
        keyboardOnlyBadge: "Input to Tamil only",
        dirToTamil: "Latin → Tamil",
        dirToLatin: "Tamil → Latin",
        inputLatinLabel: "Input (Latin / Keystrokes)",
        inputTamilLabel: "Input (Tamil Unicode)",
        outputTamilLabel: "Output (Tamil Unicode)",
        outputLatinLabel: "Output (Latin Transliteration)",
        inputPlaceholder: "Type or paste text to transliterate...",
        outputPlaceholder: "Transliterated output appears here..."
      },
      numeral: {
        title: "Numbers & Cheques",
        desc: "Write numbers, Indian/Sri Lankan rupee amounts, fractions, percentages, ordinals, and Tamil dates in words and traditional numerals.",
        inputPlaceholder: "Enter a number or amount (e.g. 125000 or 1050.75)...",
        inputLabel: "Number or Amount",
        currencyToggle: "Currency (INR / LKR)",
        spokenToggle: "Spoken Colloquial",
        formalWordsLabel: "Formal Tamil Words",
        chequeWordsLabel: "Cheque Format",
        spokenWordsLabel: "Spoken Variant",
        traditionalSymbolsLabel: "Classical Tamil Numerals",
        fractionLabel: "Tamil Fractions",
        spokenVariantBadge: "Spoken Variant",
        classicalTamilBadge: "Classical Tamil",
        classicalNotationHeading: "Classical Tamil Notation",
        modeNumber: "Plain Number",
        modeInr: "Indian Rupee (₹ INR)",
        modeLkr: "Sri Lankan Rupee (Rs LKR)",
        localeTN: "Tamil Nadu (TN)",
        localeSL: "Sri Lanka (SL)",
        tabCurrencyWords: "Currency & Words",
        tabTraditionalDigits: "Traditional & Digits",
        tabFractionsRanges: "Fractions, % & Ranges",
        tabDatesMath: "Dates & Date Math",
        currencyLabel: "Currency",
        regionLabel: "Region / Dialect",
        inputTypeLabel: "Format",
        modeCurrency: "Currency",
        modeOrdinal: "Ordinal (1st, 2nd…)",
        modeDigitSeq: "Digit Sequence (Phone / OTP)",
        inputDigitsLabel: "Input Digits",
        outputDigitsLabel: "Output Digits",
        digitsLatin: "Latin (0–9)",
        digitsTamil: "Tamil (௦–௯)",
        groupingToggle: "Indian Grouping (1,25,000)",
        groupingInternational: "International Grouping (125,000)",
        formattedAmountLabel: "Formatted Output",
        resultWordsLabel: "Tamil Words",
        tradFormatHeading: "Arabic → Traditional Tamil Integer",
        tradParseHeading: "Traditional Tamil → Arabic Integer",
        tradInputLabel: "Integer (1 – 1,000,000)",
        tradSymbolsInputLabel: "Traditional Tamil Numerals",
        tradParsePlaceholder: "e.g. ௲௨௱௫௰",
        itnHeading: "Tamil Words → Number (ITN)",
        itnInputLabel: "Formal Tamil Number Words",
        itnPlaceholder: "e.g. நூற்று இருபத்து மூன்று",
        digitScriptHeading: "Convert Digits Inside Text",
        digitScriptInputPlaceholder: "Enter text containing digits (e.g. Year 2026 / ௨௦௨௬)...",
        convertToTamil: "Convert to Tamil Digits (௦–௯)",
        convertToLatin: "Convert to Latin Digits (0–9)",
        fractionCalcHeading: "Fraction & Mixed Fraction Calculator",
        wholeLabel: "Whole",
        numeratorLabel: "Numerator",
        denominatorLabel: "Denominator",
        fractionSymbolLabel: "Unicode Symbol",
        fractionWordsLabel: "Fraction in Tamil Words",
        percentHeading: "Percentage ↔ Exact Ratio",
        percentInputLabel: "Percent (e.g. 12.5%)",
        percentRatioLabel: "Exact Ratio / Decimal",
        rangeHeading: "Numeric Range Formatter",
        rangeStartLabel: "Start",
        rangeEndLabel: "End",
        rangeStartIncl: "Start inclusive [",
        rangeEndIncl: "End inclusive ]",
        rangeOutputLabel: "Formatted Range",
        dateFormatHeading: "Format Gregorian Date in Tamil",
        dateStyleLabel: "Display Style",
        styleShort: "Short",
        styleMedium: "Medium",
        styleLong: "Long",
        styleFull: "Full (with Weekday)",
        weekdayLabel: "Weekday",
        dateMathHeading: "Date Difference & Arithmetic",
        startDateLabel: "Start Date",
        endDateLabel: "End Date",
        dateDifferenceLabel: "Day Difference",
        daysSuffix: "days",
        addUnitLabel: "Unit",
        addAmountLabel: "Offset (+/-)",
        unitDays: "Days",
        unitMonths: "Months",
        unitYears: "Years",
        resultingDateLabel: "Resulting Date"
      },
      calendar: {
        title: "Tamil Calendar & Panchangam",
        desc: "Explore Tamil solar dates, 12-month years, Panchangam limbs, festivals, TN/SL holidays, lunar phases, and Thirukanitham vs Vakya comparison.",
        dateSelectLabel: "Gregorian Date",
        tamilDateLabel: "Tamil Solar Date",
        thiruvalluvarYearLabel: "Thiruvalluvar Year",
        cycleYearLabel: "60-Year Cycle",
        nakshatraLabel: "Nakshatra",
        tithiLabel: "Tithi",
        yogaLabel: "Yoga",
        karanaLabel: "Karana",
        sunriseLabel: "Sunrise",
        sunsetLabel: "Sunset",
        rahuKalamLabel: "Rahu Kalam",
        yamagandamLabel: "Yamagandam",
        gulikaiLabel: "Kuligai",
        holidayLabel: "Official Public Holidays",
        locationPrompt: "Use GPS",
        locationFallback: "Chennai (Default)",
        coordsLabel: "City / Location",
        gpsLocationLabel: "Current Location (GPS)",
        chennaiFallbackLabel: "Chennai (Default)",
        yearFallback: "Tamil Year",
        todayButton: "Today",
        prevDay: "Previous day",
        nextDay: "Next day",
        cityLabel: "City",
        panchangamHeading: "Panchangam (at local sunrise)",
        daylightHeading: "Daily Timings",
        outOfBoundsNotice: "GPS coordinates are outside supported Tamil Nadu / Sri Lanka bounds; using Chennai.",
        tabDaily: "Daily Sheet",
        tabConvertYear: "Tamil ↔ Gregorian & Year",
        tabFestivals: "Festivals, Holidays & Moon",
        tabCompare: "Thirukanitham vs Vakya",
        profileLabel: "Calculation Profile",
        profileThirukanitham: "Thirukanitham",
        profileVakya: "Vakya Civil (Ujjain)",
        digitsToggle: "Tamil Digits (௦–௯)",
        atTimeLabel: "Panchangam at Time (HH:MM)",
        atTimeHeading: "Panchangam at Selected Time",
        transitionsHeading: "Limb Transitions Today",
        noTransitions: "No limb transitions during this civil day",
        panchangamError: "Outside supported calendar date/location range",
        reverseConvertHeading: "Tamil Solar Date → Gregorian Date",
        tamilYearLabel: "Solar Year",
        tamilMonthLabel: "Tamil Month",
        tamilDayLabel: "Tamil Day",
        gregorianResultLabel: "Gregorian Date",
        addTamilDateHeading: "Add Days / Months / Years to Tamil Date",
        addButtonLabel: "Calculate",
        yearMonthsHeading: "12-Month Solar Year Schedule",
        monthCol: "Month",
        startDateCol: "Start Date",
        endDateCol: "End (Exclusive)",
        daysCol: "Days",
        observancesHeading: "Named Observances & Festivals",
        monthFilterAll: "All Months",
        holidaysHeading: "Official Public Holidays",
        jurisdictionTN: "Tamil Nadu (TN)",
        jurisdictionSL: "Sri Lanka (SL)",
        lunarPhasesHeading: "Lunar Phases (Month)",
        noEvents: "No events found",
        compareHeading: "Thirukanitham vs Vakya Profile Comparison",
        differingFieldsLabel: "Differing Fields:",
        thirukanithamCol: "Thirukanitham",
        vakyaCol: "Vakya Civil",
        solarDateLabel: "Tamil Solar Date"
      },
      sorter: {
        title: "Agara Varisai Sorter",
        desc: "Sort Tamil words in classical Agara Varisai order (உயிர், மெய், உயிர்மெய்), compare pairs, and inspect sort/search keys.",
        inputPlaceholder: "Enter Tamil words, one per line...",
        outputPlaceholder: "Sorted word list...",
        sortAsc: "A → Z (அ → ன)",
        sortDesc: "Z → A (ன → அ)",
        removeDups: "Remove Duplicates",
        syllableStats: "Word Count",
        inputWordsLabel: "Input words (one per line)",
        collationOutputLabel: "Sorted Result",
        wordsCountSuffix: "words",
        profileAgara: "Agara Varisai",
        profileUyirmei: "Uyirmei First",
        compareHeading: "Compare Words & Inspect Keys",
        wordALabel: "Word A",
        wordBLabel: "Word B",
        compareResultBefore: "Word A comes before Word B (<)",
        compareResultAfter: "Word A comes after Word B (>)",
        compareResultEqual: "Words are collation-equal (=)",
        sortKeyLabel: "Sort Key",
        searchKeyLabel: "Search Key",
        foldedKeyLabel: "Folded Search Key"
      },
      scalar: {
        title: "Unicode Scalar Inspector",
        desc: "Inspect Unicode codepoints, hex escapes, grapheme clusters, Rust structural classification, and invisible joiners.",
        inputPlaceholder: "Enter Tamil text to inspect (e.g. தமிழ், ஸ்ரீ)...",
        inputLabel: "Text to Inspect",
        scalarCountLabel: "Unicode Scalars",
        clusterCountLabel: "Grapheme Clusters",
        invisibleNotice: "Invisible control codes (ZWJ / ZWNJ / SHY / BOM) detected!",
        noInvisibleNotice: "No invisible control codes detected (Clean text)",
        sampleInvisible: "ZWJ / NFD sample",
        rustInspectHeading: "Rust Inspection Summary (inspect_tamil_string)",
        nfcStatusLabel: "NFC",
        nfdStatusLabel: "NFD",
        ezhuthuCountLabel: "Ezhuthu Count",
        classificationsHeading: "Letter Phonetic Classifications"
      },
      dispatcher: {
        title: "Dispatcher Sandbox",
        desc: "Send raw JSON requests directly to the Rust WebAssembly engine and inspect the response.",
        presetLabel: "Choose Preset Request:",
        sendRequest: "Send Request",
        latencyLabel: "Execution Latency",
        responseLabel: "JSON Response",
        payloadLabel: "JSON Request Payload",
        statusSuccess: "Success",
        statusError: "Error",
        responsePlaceholder: "Response will appear here",
        shortcutHint: "Press Ctrl/⌘ + Enter to run"
      },
      codegen: {
        title: "Code Snippets",
        desc: "Copy starter snippets for TypeScript, Python, Rust, and Dart across every module.",
        selectLang: "Select Language:",
        installCommand: "Install Command",
        snippetHeading: "Example Code",
        tabCodec: "Font Converter",
        tabNumeral: "Numerals (INR/LKR)",
        tabCalendar: "Calendar",
        tabLexicon: "Dictionary",
        tabHyphenator: "Hyphenator",
        tabNormalizer: "Normalizer",
        tabSorter: "Sorter"
      },
      batch: {
        title: "Batch File Converter",
        desc: "Convert large .txt and .csv files locally in your browser using a background Web Worker.",
        dropzoneTitle: "Drop text files here to convert",
        dropzoneSubtitle: "or click to browse (.txt, .csv files)",
        progressLabel: "Conversion Progress",
        completedNotice: "Conversion complete!",
        formatError: "Unsupported file format. Please upload .txt or .csv files.",
        encodingLabel: "Source encoding:",
        convertAnother: "Convert another file"
      },
      symbols: {
        title: "Classical Fractions & Symbols",
        desc: "Browse traditional Tamil fractions (Munthiri, Kani, Veesam, Kal), land area, volume, and coin symbols, or inspect any of the 72 Unicode symbols.",
        searchPlaceholder: "Search by symbol, name, or fraction (e.g. Kani, 1/80, 0.75)...",
        categoryAll: "All Glyphs",
        categoryFractions: "Fractions",
        categoryLand: "Land Measures",
        categoryVolume: "Volume Measures",
        categoryCurrency: "Currency / Weight",
        symbolDetailsHeading: "Symbol Details",
        glyphLabel: "Glyph",
        codepointLabel: "Unicode Codepoint",
        nameLabel: "Classical Name",
        rationalLabel: "Rational Fraction",
        decimalLabel: "Decimal Value",
        periodLabel: "Historical Context",
        copySymbolButton: "Copy Symbol",
        quickLookupHeading: "Number to Fraction Lookup",
        quickLookupPlaceholder: "Enter number or fraction (e.g. 0.25 or 1/4)...",
        noMatches: "No matching traditional symbols found",
        liveCalcHeading: "Live Rust Symbol & Fraction Lookup",
        inspectAnySymbolLabel: "Inspect Any Tamil Symbol (72 Unicode Symbols)",
        inspectAnyPlaceholder: "Paste symbol (e.g. 𑿔, ௹, ௳)...",
        fractionBuilderLabel: "Fraction to Symbol & Words",
        buildFractionBtn: "Convert"
      },
      hyphenator: {
        title: "Syllabic Hyphenator & Line Wrapper",
        desc: "Split Tamil words into syllables, insert soft hyphens without breaking pure consonants (ஒற்று), and test narrow column wrapping.",
        tabWord: "Word Syllables",
        tabText: "Paragraph Soft-Hyphens",
        tabWrap: "Column Wrap",
        wordInputLabel: "Tamil Word",
        wordPlaceholder: "e.g. தமிழ்நாடு, பல்கலைக்கழகம், திருக்குறள்...",
        textInputLabel: "Paragraph Text",
        textPlaceholder: "Enter Tamil text to add soft hyphens or test line wrapping...",
        syllableChipsHeading: "Syllable Units",
        breakpointsHeading: "Allowed Breakpoints",
        breakpointsDesc: "Valid points where a hyphen (-) can wrap to the next line without splitting a pure consonant from its vowel.",
        codaBindingNotice: "Coda Binding Rule",
        codaBindingRule: "Pure consonants (ஒற்று / pulli letters) stay attached to the preceding syllable and never begin a new line.",
        marginHeading: "Margins & Delimiter",
        leftMarginLabel: "Start Margin (min letters)",
        rightMarginLabel: "End Margin (min letters)",
        delimiterLabel: "Delimiter",
        delimiterHyphen: "Hyphen (-)",
        delimiterBullet: "Middle Dot (·)",
        delimiterSlash: "Slash (/)",
        delimiterSoft: "Soft Hyphen (&shy;)",
        delimiterNone: "None / ZWSP",
        syllablesCount: "Syllables",
        breakpointsCount: "Breakpoints",
        noBreakpoints: "No valid breakpoints within current margins",
        shortWordNotice: "Word is too short for current margin settings",
        showSoftHyphensToggle: "Highlight Soft Hyphens ([·])",
        copyWordButton: "Copy for Word / Docs",
        copyNoHyphenButton: "Copy without Hyphen (ZWSP)",
        copyHtmlButton: "Copy HTML (&shy;)",
        copyTextButton: "Copy Soft-Hyphen Text",
        columnWidthLabel: "Column Width:",
        columnWidthLetters: "letters / line",
        compareToggle: "Compare with Naive Character Wrap",
        defaultWrapHeading: "Naive Character Wrap (Breaks pulli)",
        syllabicWrapHeading: "Tamil Syllabic Wrap (Compliant)",
        lineCount: "Lines",
        sampleWordsHeading: "Try a word:",
        sampleParagraphButton: "Load sample",
        errOrphanedPulli: "(Orphaned Pulli / Virama!)",
        errOrphanedVisiri: "(Orphaned Visiri ி/ீ!)",
        errOrphanedDiacritic: "(Orphaned Diacritic!)",
        errPureConsonant: "(Starts with Pure Consonant / Mei!)",
        errAytham: "(Starts with Aytham ஃ!)",
        integrationsTitle: "Desktop Publishing & Office Integrations",
        integrationsDesc: "Hyphenation dictionaries for LibreOffice Writer, Adobe InDesign, and Scribus.",
        downloadOxtButton: "LibreOffice Extension (.oxt)",
        downloadDicButton: "Hunspell Dictionary (.dic)",
        libreofficeGuide: "LibreOffice Guide",
        indesignGuide: "InDesign Guide",
        scribusGuide: "Scribus Guide",
        formattedSyllablesLabel: "Hyphenated Word",
        settingsToggle: "Settings",
        visualPreviewHeading: "Soft-Hyphen Visual Preview",
        browserFlowHeading: "Browser Flow Preview (Resize Window)",
        setupGuidesLabel: "Setup Guides:"
      },
      letter: {
        title: "Word & Syllable Breakdown",
        desc: "Break Tamil words into vowels (உயிர்), consonants (மெய்), composite letters (உயிர்மெய்), and Grantha letters.",
        inputPlaceholder: "Type or paste Tamil words to analyze (e.g. தமிழ்நாடு, புரட்சி, ஸ்ரீலங்கா)...",
        inputLabel: "Text to Analyze",
        syllablesCount: "Total Letters",
        uyirCount: "Vowels (உயிர்)",
        meiCount: "Consonants (மெய்)",
        uyirmeiCount: "Composite (உயிர்மெய்)",
        granthaCount: "Grantha (கிரந்தம்)",
        selectedSyllableHeading: "Letter Breakdown",
        rootConsonantLabel: "Root Consonant (மெய்)",
        vowelLabel: "Vowel (உயிர்)",
        vowelSignLabel: "Vowel Sign",
        codepointsLabel: "Unicode Sequence",
        classificationLabel: "Category",
        selectPrompt: "Select any letter above to see how it is formed",
        moraLabel: "Duration (Māthirai)",
        cognateLabel: "Cognate Consonant",
        quantityLabel: "Quantity",
        tabBreakdown: "Letter Breakdown",
        tabComposer: "Uyirmei Composer",
        tabOlippasai: "Syllables & Cognates",
        composerMeiLabel: "Consonant (மெய்)",
        composerUyirLabel: "Vowel (உயிர்)",
        composedResultLabel: "Composed Uyirmei",
        allVowelsRowLabel: "All 12 Vowel Forms for This Consonant",
        olippasaiHeading: "Spoken Syllables (Olippasai)",
        codaYes: "Coda consonant",
        codaNo: "Open syllable",
        cognateCheckHeading: "Cognate Pair Check (are_cognates)",
        cognateYes: "Cognate pair (இன எழுத்து)",
        cognateNo: "Not cognates"
      },
      normalizer: {
        title: "Unicode Cleanup & Repair",
        desc: "Fix broken vowel signs, duplicate pulli marks, and stray invisible characters into clean Tamil Unicode.",
        inputPlaceholder: "Paste Tamil text to clean or normalize...",
        inputLabel: "Original Text",
        outputLabel: "Cleaned Output",
        nfcLabel: "Standard NFC",
        nfdLabel: "Decomposed NFD",
        repairedLabel: "Repair Broken Text",
        foldLabel: "Search Fold",
        statusClean: "Clean Unicode (0 issues)",
        statusAnomalies: "issues fixed",
        anomaliesFixedLabel: "Issues Detected",
        copyNormalizedButton: "Copy Clean Text",
        diffHeading: "Normalization Diff",
        sampleVowelsButton: "Two-part vowels (கொ, கோ)",
        sampleDefectiveButton: "Broken text sample",
        codepointInspectorHeading: "Codepoint Inspector",
        nfcBanner: "Standard NFC: Combines split two-part vowel signs (ொ, ோ, ௌ) into canonical single Unicode codepoints.",
        nfdBanner: "Decomposed NFD: Splits composite vowel signs (ொ, ோ, ௌ) into kombu (ெ/ே) plus trailing sign (ா/ௗ). Although visually identical in fonts, the Codepoint Inspector below reveals the underlying sequence.",
        repairedBanner: "Repair Broken Text: Collapses duplicate pulli marks, reorders misplaced visual kombu signs, strips stray invisible controls, and outputs clean NFC.",
        foldBanner: "Search Fold: Maps similar-sounding Mayangoli letters (ள/ழ/ல, ண/ந/ன, ற/ர) and Grantha letters (ஜ, ஷ, ஸ, ஹ, ஸ்ரீ, க்ஷ) into canonical search keys.",
        decomposedCountLabel: "Two-part vowel signs decomposed",
        profileComprehensive: "All (Mayangoli + Grantha)",
        profileMayangoli: "Mayangoli Only",
        profileGrantha: "Grantha Only",
        repairOptionsHeading: "Repair Options & Counts",
        optCollapsePulli: "Collapse Duplicate Pulli",
        optReorderKombu: "Reorder Visual Kombu",
        optStripShy: "Strip Soft Hyphens (SHY)",
        optStripJoiners: "Strip Joiners (ZWJ/ZWNJ)",
        diagDuplicatePulli: "Duplicate Pulli",
        diagVisualKombu: "Visual Kombu",
        diagStrippedControls: "Stripped Controls",
        diagTotalRepairs: "Total Repairs"
      },
      lexicon: {
        title: "Tamil Dictionary",
        desc: "Look up verified Tamil and English Wiktionary entries with definitions, regional dialects, examples, and sources.",
        searchLabel: "Headword Search (preserves whitespace & joiners):",
        searchPlaceholder: "Enter Tamil word or English meaning (e.g. நன்றி, செப்பம், water)...",
        searchButton: "Search",
        exactPreserveNote: "Whitespace, ZWJ/ZWNJ, and soft hyphens are preserved verbatim; only Rust NFC canonicalization runs.",
        packsLabel: "Lexicon Packs:",
        selectAllAvailable: "Select All Available",
        clearSelection: "Clear All",
        packUnavailableBadge: "Unavailable",
        packLoadedBadge: "Loaded",
        packNotBuiltBadge: "Not in this build",
        regionFilterLabel: "Dialect / Region:",
        registerFilterLabel: "Register:",
        allRegionsOption: "All Regions",
        allRegistersOption: "All Registers (unfiltered)",
        unknownScopeNote: "Finite registry region options and selected-pack register codes are shown; unknown entry scopes are never inferred.",
        examplesHeading: "Try these words:",
        corpusInventoryHeading: "Pack Totals & Provenance Scope",
        fullProfileBadge: "Full Profile (core + names_taxa + regional)",
        activeBuildLabel: "Current Build:",
        distinctFormsLabel: "Distinct Forms",
        entriesLabel: "Entries",
        sensesLabel: "Senses",
        historicalExclusionHeading: "Excluded Historical Intake (307,243 records)",
        historicalExclusionBody: "The original 307,243 historical intake records (12 frozen files) remain excluded from the verified dictionary (0 eligible assertions) and are searchable separately under Historical Archive.",
        loadingEngine: "Loading dictionary engine…",
        noDataBuildHeading: "No dictionary data embedded in this build",
        noDataBuildBody: "This zero-payload build contains no compiled dictionary packs.",
        statusMatched: "Matched",
        statusNotFound: "Not Found",
        statusError: "Error",
        canonicalQueryLabel: "Canonical Query (NFC):",
        notFoundHeading: "No exact headword match",
        notFoundBody: "No entry matched this exact headword in the selected packs and filters.",
        entryIdLabel: "Entry ID",
        posLabel: "Part of Speech",
        formsHeading: "Forms",
        sensesHeading: "Senses",
        examplesListHeading: "Examples",
        relationsHeading: "Relations",
        annotationsHeading: "Annotations",
        regionScopeLabel: "Region Scope",
        registerScopeLabel: "Register",
        unrestrictedScope: "Unrestricted (all regions)",
        unknownScope: "Unknown (not inferred)",
        humanAcceptanceBadge: "Human-reviewed (accepted_human)",
        autoAcceptanceBadge: "Automated source (accepted_auto_source)",
        mixedAcceptanceBadge: "Mixed: Human + Automated",
        provenanceToggle: "Provenance & Acceptance",
        sourceLinksHeading: "Safe Source Links:",
        rawInspectorHeading: "Raw JSON Request & Response",
        rawRequestLabel: "Raw Request JSON",
        rawResponseLabel: "Raw Response / Error JSON",
        downloadRequest: "Download Request",
        downloadResponse: "Download Response",
        contractPresetsToggle: "Developer Contract-Test Presets",
        contractPresetsDesc: "Presets to test empty/unknown/unavailable packs, invalid filters, whitespace/joiner preservation, and NFD→NFC behavior.",
        resetToAvailablePacks: "Reset to Available Packs",
        packCoreDesc: "Approved core Tamil lexicon pack",
        packNamesTaxaDesc: "Proper names & biological/cultural taxa",
        packRegionalDesc: "Pluricentric regional varieties (TN & SL)",
        packTerminologyDesc: "Technical terminology pack (unavailable)",
        staleMetadataBadge: "Stale / Mismatched Metadata",
        staleMetadataWarning: "Engine PackInfo.manifest_sha256 does not match catalog; static catalog counts are withheld as stale/unavailable.",
        verifyingManifests: "Verifying dictionary metadata…",
        unavailableCounts: "Unavailable / stale",
        partialProfileBadge: "Partial Profile (Verified Loaded Packs Only)",
        attributionNoticesHeading: "Public Attribution & License Notices (CC-BY-SA-4.0):",
        firstLoadSizeNote: "First load downloads the dictionary (~46 MiB), then caches it locally for offline lookup.",
        offlineCacheHeading: "First-Load Size & Offline Cache",
        offlineCacheNote: "The browser WASM bundle (~46 MiB) is cached locally alongside attribution notices for offline lookup.",
        dataDetailsToggle: "Data coverage, exclusions & attribution"
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
