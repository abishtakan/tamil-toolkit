# Research: Additional Interactive Linguistic & Epigraphical Tools

## Research Summary
The Tamil Toolkit playground currently features 4 primary utilities (Legacy Font Converter, Numeral & Legal Cheque Formatter, Calendar Explorer, and Agara Varisai Sorter) alongside 4 developer utilities (Unicode Scalar Inspector, WASM Dispatcher Sandbox, Code Generator, and Batch Processor).

To maximize linguistic utility and cultural value, three additional high-impact tools are designed to expose previously inaccessible core engine capabilities directly to everyday users, scholars, and developers.

---

## Decision 1: Traditional Tamil Fractions & Epigraphical Symbol Explorer (`TamilSymbolsExplorer`)
- **Decision**: Build a dedicated interactive visual explorer for traditional Tamil fractions (முந்திரி $1/320$, காணி $1/80$, அரைக்கால் $1/160$, வீசம்/மாகாணி $1/16$, ஒருமா $1/20$, கால் $1/4$, அரை $1/2$, முக்கால் $3/4$) and historic epigraphical measurement glyphs (வேலி, குழி, கலம், நெல், காசு).
- **Architecture & Engine Integration**:
  - Leverages `tamil-numerals` methods exposed via `execute()`: `symbol_info`, `parse_fraction_symbol`, `format_mixed_fraction`, `parse_mixed_fraction`.
  - Symbol catalog grouped by historical domain:
    1. *விகிதங்கள் & பின்னங்கள்* (Fractions: முந்திரி to முக்கால்).
    2. *நில அளவைகள்* (Land Measures: வேலி, குழி, மா).
    3. *முகத்தல் & தானிய அளவைகள்* (Dry/Liquid Capacity: கலம், பதக்கு, தூணி, நாழி).
    4. *நாணயம் & எடைகள்* (Coinage & Weights: காசு, கழஞ்சு, பொன்).
  - Search/filter by fraction value (e.g. `1/80`, `0.0125`) or Tamil name (e.g. `காணி`).
  - Bi-directional lookup: typing a decimal or fraction displays the exact traditional symbol representation.
- **Rationale**: Tamil epigraphical symbols and fraction glyphs are recognized in Unicode (Tamil Supplement block `U+11FC0`–`U+11FFF` and Tamil block `U+0BF3`–`U+0BFA`), but without an interactive catalog, modern users cannot discover or easily input them.

---

## Decision 2: Real-Time Tamil Letter & Uyirmei Morphological Decomposer (`TamilLetterAnalyzer`)
- **Decision**: Build an interactive orthographic analyzer that decomposes any Tamil word or sentence into its fundamental phonetic syllables (*உயிர்*, *மெய்*, *உயிர்மெய்*, *ஆய்தம்*, *கிரந்தம்*).
- **Architecture & Engine Integration**:
  - Leverages `tamil-core` methods exposed via `execute()`: `get_letters`, `split_uyirmei`, `compose_uyirmei`, `inspect_tamil_string`.
  - For each syllable, provides a breakdown card:
    - Base consonant (`மெய்`, e.g. `ப்`).
    - Vowel (`உயிர்`, e.g. `ஒ`).
    - Combined syllable (`உயிர்மெய்`, e.g. `பொ`).
    - Diacritic marker names (e.g. *இரட்டைக்கொம்பு*, *துணைக்கால்*, *புள்ளி*).
  - Grantha and loan-letter identification (e.g. `ஜ`, `ஷ`, `ஸ`, `ஹ`, `க்ஷ`).
  - Real-time reactivity as user types with zero debounce lag.
- **Rationale**: Tamil learners, teachers, and NLP developers frequently need to understand the exact grapheme-to-phoneme composition of complex Tamil words.

---

## Decision 3: Tamil Unicode Text Normalizer & Anomaly Repair Tool (`TamilNormalizer`)
- **Decision**: Build a real-time text normalizer and anomaly diagnostic tool that fixes common Tamil digital encoding defects.
- **Architecture & Engine Integration**:
  - Leverages `tamil-norm` methods exposed via `execute()`: `normalize_nfc`, `normalize_nfd`.
  - Detects and cleans:
    - Duplicate pulli marks (`க்` + `்`).
    - Split vowel sequences (e.g. decomposed `க` + `ொ` instead of standard composite).
    - Stray zero-width spaces (`U+200B`) and zero-width joiners (`U+200D` / `U+200C`).
    - Non-canonical diacritic placement.
  - Interactive visual diff highlighting what characters were cleaned, removed, or normalized.
- **Rationale**: Web scraping, OCR, and legacy PDF text extraction often introduce subtle diacritic anomalies that break Tamil string matching, sorting, and display. A fast client-side normalizer solves this reliably.

---

## Decision 4: Playground Navigation & Tab Placement
- **Decision**: Organize the tools cleanly within the established tab structure:
  - **Public Tools**:
    1. *எழுத்துரு மாற்றி* (`codec`): Legacy Font Converter.
    2. *எண் & நாணயம்* (`numeral`): Numeral & Legal Cheque Formatter.
    3. *நாட்காட்டி & பஞ்சாங்கம்* (`calendar`): Calendar & Panchangam.
    4. *அகர வரிசை* (`sorter`): Agara Varisai Sorter.
    5. *பழந்தமிழ் பின்னங்கள் & குறியீடுகள்* (`symbols`): Traditional Fractions & Epigraphical Symbols Explorer (**NEW**).
  - **Developer Tools**:
    1. *ஒருங்குறி ஆய்வகம்* (`scalar`): Unicode Scalar Inspector.
    2. *சொல் & எழுத்து பகுப்பாய்வி* (`letter`): Tamil Letter & Uyirmei Decomposer (**NEW**).
    3. *ஒருங்குறி சீரமைப்பி* (`normalizer`): Unicode Normalizer & Cleaner (**NEW**).
    4. *நேரடி ஆய்வகம்* (`dispatcher`): Dispatcher Sandbox.
    5. *நிரல் குறிமுறை உருவாக்கி* (`codegen`): Code Generator.
    6. *கோப்புத் தொகுதி மாற்றி* (`batch`): Batch File Processor.
  - Also update the **Overview Hub** with quick launch cards and live mini-previews for the new tools.
