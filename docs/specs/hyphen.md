# Canonical Tamil Hyphenation Specification (`tamil-hyphen`)

## 1. Overview & Dialect Scope

This specification defines the canonical prosodic and syllabic hyphenation rules for `tamil-hyphen` across all supported runtimes (Rust, Python, WebAssembly, Playground, and the Microsoft Word Add-in).

- **Pluricentric Dialect Scope**: Orthographically invariant across **Tamil Nadu (`ta-IN`)**, **Sri Lanka (`ta-LK`, including Jaffna, Batticaloa, Vanni, and Up-Country)**, and global diaspora Tamil (`COMMON`).

---

## 2. Default Configuration (`left_min = 3, right_min = 3`)

- **Default Delimiter**: `U+00AD` (Soft Hyphen)
- **Default Leading Margin (`left_min`)**: `3` tailored Tamil letters (*Ezhuthu*)
- **Default Trailing Margin (`right_min`)**: `3` tailored Tamil letters (*Ezhuthu*)
- **Minimum Word Length (`MIN_WORD_LETTERS`)**: `left_min + right_min = 6` tailored Tamil letters. Any Tamil word with fewer than 6 tailored Tamil letters (`உலகம்`, `சமூகம்`, `வணிகம்`, `திட்டம்`, `வரலாறு`, `தலைமுறை`, `அறிவியல்`, `விவசாயம்`, `பாதுகாக்க`) remains **100% unbroken**.

---

## 3. The 5-Step Tamil *Asai* (`நேரசை` / `நிரையசை`) Partitioning Algorithm

For words with $\ge \text{left\_min} + \text{right\_min}$ tailored Tamil letters:

1. **Step 1 — Raw Phonetic Syllable Extraction (*Olippasai*)**:
   - Normalize input to Unicode NFC and strip any pre-existing soft hyphens (`U+00AD`), optional hyphens (`U+001F`), or zero-width spaces (`U+200B`).
   - Partition tailored Tamil letters into raw phonetic syllables: each vowel-bearing letter (`Uyir`, `Uyirmei`, or `AtomicGrantha` `க்ஷ` / `ஸ்ரீ` / `ஶ்ரீ`) absorbs **all** immediately following contiguous pure consonants (`Mei` ending in pulli `\u{0BCD}`) and `Aytham` (`\u{0B83}`).
2. **Step 2 — Word-Initial Participle Stem Binding (`CVC + u/i`)**:
   - If the first raw syllable is a 2-letter closed syllable (`1 Uyir/Uyirmei + 1 Mei/Aytham`, e.g., `கண்`, `இன்`, `கன்`) and the second raw syllable is a 1-letter open syllable ending in `-உ` (`\u{0BC1}`) or `-இ` (`\u{0BBF}`) (e.g., `டு`, `றி`, `னி`), bind them into a single 3-letter stem (`கண்டு-பிடிப்பு`, `இன்றி-யமையாத`, `கன்னி-யாகுமரி`).
3. **Step 3 — Forward *Nirai-asai* Grouping**:
   - Any remaining 1-letter open syllable (having no `Mei` or `Aytham` coda) joins forward with the immediately following syllable (`"குறில் தனித்து அசையாகாது"` $\rightarrow$ `கலைக்`, `கழ`, `திருச்`, `சிராப்`, `ஒருங்`, `கிணைக்`).
4. **Step 4 — Edge & Internal Segment Merging**:
   - **Next-Line Tail Merge (`< right_min`)**: While the final *Asai* has fewer than `right_min` tailored letters (`-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`), merge it into the preceding *Asai* (`கழ` + `கம்` $\rightarrow$ `கழகம்`, `நுட்` + `பம்` $\rightarrow$ `நுட்பம்`).
   - **Current-Line Head Merge (`< left_min`)**: While the first *Asai* has fewer than `left_min` tailored letters (`பல்`, `பள்`, `மட்`, `நாக`), merge it into the second *Asai* (`பல்` + `கலைக்` $\rightarrow$ `பல்கலைக்`, `பள்` + `ளிக்` $\rightarrow$ `பள்ளிக்`).
   - **Internal Segment Merge (`< min(left_min, right_min)`)**: Merge any internal *Asai* shorter than $\min(\text{left\_min}, \text{right\_min})$ with its adjacent neighbor (preferring an open neighbor over a closed *Mei* coda).
5. **Step 5 — Emit Valid Break Points**:
   - Emit break points between adjacent merged *Asai* segments where `left_count >= left_min`, `right_count >= right_min`, the following segment starts with a vowel-bearing onset (`Uyir`, `Uyirmei`, or `AtomicGrantha`), and neither boundary letter contains `ZWJ` (`U+200D`) or `ZWNJ` (`U+200C`).
