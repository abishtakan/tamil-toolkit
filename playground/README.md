# Tamil Toolkit Playground (`tamil-toolkit-playground`)

An authentic, zero-latency linguistic workbench and developer playground for Tamil script, numeral conversion, calendar mathematics, legacy encodings, and Unicode analysis.

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
