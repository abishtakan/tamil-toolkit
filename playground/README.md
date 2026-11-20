# Tamil Toolkit Playground (`tamil-toolkit-playground`)

A local linguistic workbench and developer playground for Tamil script, numeral conversion, calendar mathematics, legacy encodings, and Unicode analysis.


## Full lexicon testing

Run `just playground-dev`, then open http://localhost:5173/?tool=lexicon (or select **Lexicon** from the home page).
The start/build scripts prepare the optimized browser WASM with core, names/taxa
and regional packs. The first build can take several minutes; later starts reuse
verified build outputs. The complete browser bundle is about 46 MiB, including
source provenance, and is precached for offline use in production. Rust's default
Cargo data features remain off.

The explorer provides exact lookup, pack selection, region/register filters,
sourced examples, homographs, senses, provenance and raw request/response views.
It preserves whitespace and joiners. It does not provide fuzzy/prefix search or
search inside English definitions; those operations are outside the current engine.

Current verified-pack data: 9,410 distinct headwords, 11,377 entries and 25,742 senses.
Only six entries have human approval; bulk entries retain automated source
acceptance. The separate **Historical source records** view searches all 307,243
owner-supplied CSV records, including technical terms, source meanings, phrases,
names and outgoing relations. Results retain original fields and file/row
locators; inherited status labels do not establish verified linguistic acceptance.
Source rights remain unresolved. Each search downloads one hash-checked data
bucket; these historical buckets are not part of the fully precached verified
dictionary. Pack-specific attribution and CC-BY-SA
terms are available under `/lexicon-notices/<pack>/ATTRIBUTION_AND_TERMS.md`.

`uv run --locked python tools/prepare_playground.py --check` verifies generated
catalog metadata against the canonical packs.
`uv run --locked python tools/prepare_historical_lexicon.py --check` proves every
exported historical cell equals the frozen original. Start/build preparation
generates the data when missing. No remote lookup service is used.

To create a separate owner-directed data artifact without changing engine package
licenses or publishing it:

```powershell
uv run --locked python tools/prepare_historical_lexicon.py --archive target/lexicon/historical-source-records.zip
```

---

## 1. UI Design Language & Philosophy: "செம்புலப் பெயல் நீர்"

The playground UI rejects generic SaaS templates, neon gradients, and AI-generated design slop. Instead, it embodies **human-crafted, authentic Tamil linguistic materiality** and high-density utilitarian engineering:

- **Asymmetric Workbench Hierarchy**: Primary tools (such as Legacy Font & Encoding Converter) receive visual prominence, while secondary diagnostics are arranged into an integrated developer console.
- **Tools Suite**:
  - **Public Utilities**:
    1. *எழுத்துரு மாற்றி* (`codec`): Legacy Font & Encoding Converter (Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM).
    2. *எண் - சொல் & நாணயம்* (`numeral`): Tamil Numeral, Cheque Legal Words & Financial Notation Formatter.
    3. *நாட்காட்டி & பஞ்சாங்கம்* (`calendar`): Classical Thirukanitham & Vakya Solar Calendar Explorer.
    4. *அகர வரிசை* (`sorter`): Classical Tamil Agara Varisai Word Sorter.
    5. *பழந்தமிழ் பின்னங்கள் & குறியீடுகள்* (`symbols`): Traditional Fractions (முந்திரி to முக்கால்) and Epigraphical Measurement Glyph Explorer.
    6. *சொல் & பத்தி அசையசைப்பி* (`hyphenator`): Syllabic Hyphenation, Coda Binding Inspector & Responsive Line Wrapper.
  - **Developer Diagnostics**:
    1. *ஒருங்குறி ஆய்வகம்* (`scalar`): Unicode Scalar & Invisible Joiner Code Inspector.
    2. *சொல் & எழுத்து பகுப்பாய்வி* (`letter`): Grapheme Cluster & Morphological Syllable (உயிர், மெய், உயிர்மெய், கிரந்தம்) Decomposer.
    3. *ஒருங்குறி சீரமைப்பி* (`normalizer`): Unicode NFC/NFD Canonical Normalizer & Digital Diacritic Anomaly Repair.
    4. *நேரடி ஆய்வகம்* (`dispatcher`): Raw JSON WebAssembly Dispatcher Console.
    5. *நிரல் குறிமுறை உருவாக்கி* (`codegen`): Polyglot SDK Generator (Rust, Python, TypeScript, Dart).
    6. *கோப்புத் தொகுதி மாற்றி* (`batch`): Background Web Worker Document Batch Processor.
- **De-AI-ified Interactions (Un-slop)**: 
  - Strictly **no** `scale-105` or bouncy hover physics.
  - State changes use crisp **1px hairline border color transitions** (`border-[var(--color-semman)]`, `border-[var(--color-sandhanam)]`) over a responsive 120–150ms duration.
  - Tactile press feedback (`active:scale-[0.99]`) and high-visibility keyboard focus rings (`focus-visible:ring-2 focus-visible:ring-[var(--color-semman)]`).
- **Domain-Accurate Copy**: Zero marketing buzzwords or superlative claims. All labels in both Tamil and English describe exact linguistic functions and engine states.

---

## 2. Color Palette & Token System

The design system employs CSS custom properties defined in `src/index.css`.

### Light Mode: *ஏட்டுச்சுவடி & செம்மண்* (Palm Leaf & Terracotta)
Inspired by ancient palm-leaf manuscripts (*ஓலைச்சுவடி*), natural terracotta pigments (*செம்மண்*), and carbon manuscript ink (*மை*).

| Token | CSS Variable | Hex | Role | Contrast Ratio |
|---|---|---|---|---|
| Canvas Background | `--bg-canvas` | `#faf7f2` | Warm palm leaf / ivory background | — |
| Surface Panel | `--bg-surface` | `#ffffff` | Clean white panel container | — |
| Raised Tile | `--bg-raised` | `#f3eee6` | Sandstone accent & nested cards | — |
| Border Line | `--border-line` | `#e8e0d4` | 1px earthen hairline divider | — |
| Terracotta Brand | `--color-semman` | `#963824` | Primary brand accent & active states | 6.4:1 |
| Terracotta Hover | `--color-semman-hover` | `#7d2e1c` | Darker terracotta on hover | 8.8:1 |
| Terracotta Tint | `--color-semman-light` | `#fbeee9` | Soft terracotta badge background | — |
| Sandalwood Accent | `--color-sandhanam` | `#b88628` | Sandalwood gold / calendar badges | 4.8:1 |
| Sandalwood Tint | `--color-sandhanam-light` | `#fbf5ea` | Subtle warm gold badge background | — |
| Primary Text (Mai) | `--color-mai` | `#1f1a17` | Deep carbon ink typography | 15.2:1 (AAA) |
| Muted Text | `--color-muted` | `#574e47` | Secondary labels & metadata | 6.2:1 (AA) |

### Dark Mode: *கருங்கல் & செப்புப் பட்டயம்* (Basalt Granite & Inscription Slate)
Inspired by Thanjavur / Chola temple granite carvings (**கருங்கல்**) and engraved copper-plate charters (**செப்புப் பட்டயம்**). Replaces muddy, swamp-brown tones with clean, high-contrast basalt stone.

| Token | CSS Variable | Hex | Role | Contrast Ratio |
|---|---|---|---|---|
| Canvas Background | `--bg-canvas` | `#0c0e11` | Deep neutral basalt granite (zero brown cast) | — |
| Surface Panel | `--bg-surface` | `#14171c` | Cool engraved stone slate container | — |
| Raised Tile | `--bg-raised` | `#1c2026` | Elevated tool console tile | — |
| Border Line | `--border-line` | `#262b33` | 1px cool stone hairline divider | — |
| Terracotta Brand | `--color-semman` | `#e05338` | Radiant vermilion terracotta | 5.2:1 (AA) |
| Terracotta Hover | `--color-semman-hover` | `#eb674e` | Bright vermilion hover highlight | 6.5:1 |
| Terracotta Tint | `--color-semman-light` | `#2a1512` | Dark vermilion badge background | — |
| Sandalwood Accent | `--color-sandhanam` | `#d99f36` | Antique temple brass / gold | 6.8:1 (AA) |
| Sandalwood Tint | `--color-sandhanam-light` | `#261d10` | Dark warm brass badge background | — |
| Primary Text (Mai) | `--color-mai` | `#f3f4f6` | High-contrast crisp off-white | **15.8:1 (AAA)** |
| Muted Text | `--color-muted` | `#949ca8` | Cool stone silver for secondary text | **5.7:1 (AA)** |

---

## 3. Typography Hierarchy

Tamil script features unique fluid curves and diacritics (pulli `்`, kombu `ெ`, `ே`, `ை`, sub-base loops `ு`, `ூ`). The typographic cascade provides generous line heights (`leading-loose` or `leading-relaxed`) to prevent vowel signs from clipping or crowding:

- **Literary Titles & Headlines**: `font-tamil` (`"Noto Serif Tamil", "Mukta Malar", "Nirmala UI", serif`).
- **UI & Navigation**: `font-tamil-sans` (`"Inter", "Noto Sans Tamil", "Nirmala UI", sans-serif`).
- **Code & Unicode Scalars**: `font-mono-tamil` (`"JetBrains Mono", "Cascadia Code", monospace`).

---

## 4. Bilingual First Architecture

- **Single Toggle Switcher**: Seamless 1-tap switching between Tamil (`தமிழ்`) and English (`English`) in the navigation bar.
- **Unified Dictionary**: All interface strings are strictly typed and managed in `src/lib/i18n.ts`. No hardcoded strings are allowed in components.
- **Cultural Accuracy**: Technical terms use established Tamil computing vocabulary (e.g. `குறியாக்கம்` for encoding, `ஒருங்குறி` for Unicode, `எழுத்துரு` for font).

---

## 5. Development & Testing

```bash
# Run playground tests (including design token & ergonomics tests)
pnpm --filter tamil-toolkit-playground test

# Run build verification
pnpm --filter tamil-toolkit-playground build

# Start local dev server
pnpm --filter tamil-toolkit-playground dev
```
