# Design Standard: Tamil Cultural Essence & Minimalist UI Guidelines

**Feature**: `005-playground` | **Date**: 2026-11-05

This document establishes the authentic Tamil visual design system, cultural color palette, classical typography hierarchy, bilingual UI architecture (தமிழ் / English), and clutter-free mobile ergonomics for the `tamil-toolkit` Playground.

---

## 1. Cultural Design Philosophy: "செம்புலப் பெயல் நீர்" (Authentic & Minimal)

The design rejects generic SaaS neon palettes (no electric blues, purples, pinks, or artificial greens). Instead, it draws inspiration from classical Tamil antiquity, palm-leaf manuscripts (*ஓலைச்சுவடி*), natural pigments (*செம்மண்*, *சந்தனம்*), and carbon manuscript ink (*மை*):

1. **செம்மண் (Semman - Terracotta & Burnt Ochre)**: The warmth of Sangam literature (*"செம்புலப் பெயல் நீர் போல"* — like pouring rain absorbed by red earth). Serves as the primary active brand and interactive highlight color.
2. **ஏடு / ஓலைச்சுவடி (Olai Chuvadi - Warm Palm Leaf & Rice Ivory)**: Soft warm parchment cream backgrounds (`#faf7f2` light / `#181513` dark) that eliminate harsh screen glare and create a natural paper-like reading feel.
3. **மையெழுத்து (Mai - Traditional Carbon & Charcoal Ink)**: Deep warm charcoal for typography and structural borders rather than cold synthetic black.
4. **பொன் / மஞ்சள் (Sandalwood Gold & Brass)**: Subtle warm metallic ochre used sparingly for badges, status chips, and astronomical/calendar markers.
5. **முற்றிலும் தமிழ் (Bilingual Tamil-First Experience)**: Complete 1-tap bilingual UI toggle (`தமிழ்` ↔ `English`) covering all navigation, labels, tooltips, and copy confirmations.

---

## 2. Cultural Color Palette & Theme Tokens

### Light Theme: *ஏட்டுச்சுவடி* (Palm Leaf & Red Clay)
- **Background (`--bg-canvas`)**: `#faf7f2` (Warm palm leaf cream / rice ivory)
- **Surface Panels (`--bg-surface`)**: `#ffffff` (Clean warm white)
- **Surface Raised (`--bg-raised`)**: `#f3eee6` (Subtle sandstone accent)
- **Primary Brand (`--color-semman`)**: `#963824` / `#a83f2a` (Rich Terracotta / Burnt Ochre)
- **Primary Hover (`--color-semman-hover`)**: `#7d2e1c`
- **Secondary Accent (`--color-sandhanam`)**: `#b88628` / `#8c6218` (Sandalwood Brass / Warm Ochre)
- **Borders & Dividers (`--border-line`)**: `#e8e0d4` (Warm earthen stroke)
- **Primary Text (`--text-mai`)**: `#1f1a17` (Deep carbon ink)
- **Muted Text (`--text-muted`)**: `#6e645c` (Weathered stone)
- **Notice / Badge Accent (`--badge-accent`)**: `#f5ede2` (Parchment badge with terracotta border)

### Dark Theme: *இரவுச் சுவடி* (Night Scribe / Smoked Slate)
- **Background (`--bg-canvas`)**: `#141210` (Deep warm soot)
- **Surface Panels (`--bg-surface`)**: `#1c1815` (Smoked terracotta stone)
- **Surface Raised (`--bg-raised`)**: `#26211d` (Warm obsidian)
- **Primary Brand (`--color-semman`)**: `#d95c43` (Vibrant terracotta flame)
- **Primary Hover (`--color-semman-hover`)**: `#e6725b`
- **Secondary Accent (`--color-sandhanam`)**: `#e0a638` (Polished temple brass)
- **Borders & Dividers (`--border-line`)**: `#332b25` (Subtle charcoal border)
- **Primary Text (`--text-mai`)**: `#f4efe8` (Clean parchment white)
- **Muted Text (`--text-muted`)**: `#a69a8f` (Muted ash)
- **Notice / Badge Accent (`--badge-accent`)**: `#2a211b` (Smoked amber badge)

---

## 3. Typography: Literary Dignity & Digital Precision

Tamil letterforms possess distinct rhythm, fluid curves, and sensitive vowel marks (pulli `்`, kombu `ெ`, `ே`, `ை`, sub-base signs `ு`, `ூ`). The typography must never look cramped or visually distorted.

```css
/* Typography Cascade */
--font-tamil: "Noto Serif Tamil", "Mukta Malar", "Nirmala UI", "Latha", serif;
--font-tamil-sans: "Inter", "Noto Sans Tamil", "Nirmala UI", sans-serif;
--font-mono: "JetBrains Mono", "Cascadia Code", monospace;
```

### Hierarchy & Metrics
- **Main Tool Title**: `text-2xl` (`1.5rem`), font weight `600`, leading `1.3`, serif elegance.
- **Input & Output Textarea**: `text-lg` (`1.125rem`), leading `1.7` (`leading-loose`). Extra vertical clearance prevents upper pulli and lower u/oo loops from touching adjacent lines.
- **Microcopy & Chips**: `text-sm` (`0.875rem`), font weight `500`, tracking slightly loosened (`tracking-wide`).
- **Unicode Scalars & Hex Code**: `--font-mono`, `text-xs` (`0.75rem`), with warm terracotta borders.

---

## 4. Bilingual Tamil-First UI Architecture (`i18n`)

A prominent, single-tap bilingual language switcher sits at the top right of the navigation header:

```text
[ 🌐 தமிழ் / English ]
```

### Dictionary Sample Mapping

| Interface Element | English (EN) | தமிழ் (TA) |
|:---|:---|:---|
| **Site Branding** | Tamil Toolkit Playground | தமிழ் கருவிப் பட்டறை |
| **Tool 1 Title** | Legacy Font & Encoding Converter | பழைய எழுத்துரு மாற்றி |
| **Tool 2 Title** | Tamil Numerals & Currency Words | எண் - சொல் & நாணய வடிவம் |
| **Tool 3 Title** | Calendar & Panchangam Explorer | தமிழ் நாட்காட்டி & பஞ்சாங்கம் |
| **Tool 4 Title** | Agara Varisai Sorter | அகர வரிசைப்படுத்துதல் |
| **Dev Tool 1** | Unicode Scalar Inspector | எழுத்துரு & ஒருங்குறி அலகுகள் |
| **Dev Tool 2** | Dispatcher Sandbox | நேரடி ஆய்வகம் (Dispatcher) |
| **Dev Tool 3** | Code Generator | நிரல் குறிமுறை உருவாக்கி |
| **Dev Tool 4** | Batch File Processor | கோப்புத் தொகுதி மாற்றி |
| **Action: Copy** | Copy | நகலெடு |
| **Action: Copied**| Copied to clipboard! | நகலெடுக்கப்பட்டது! |
| **Action: Clear**| Clear | அழி |
| **Action: Swap** | Swap Direction | திசை மாற்று |
| **Action: Sample**| Load Sample | உதாரணம் |
| **Auto-Detect** | Auto-Detect | தானியங்கி கண்டறிதல் |
| **Privacy Tag** | 100% Client-Side (Zero Server Upload) | கணினிக்குள் மட்டும் (முழுத் தனிநபர் பாதுகாப்பு) |

---

## 5. Uncluttered Mobile Ergonomics

### A. Strict Anti-Clutter Rules
1. **No Jarring Banner Graphics**: Clean textual framing; beauty comes from Tamil typography and balanced white space.
2. **Single-Tap Pill Chips**: Encoding selection is a swipeable horizontal row of warm earthen chips:
   `[தானியங்கி ✓] [பாமினி] [TSCII] [TAB] [TAM] [அஞ்சல்] [வானவில்] [LT-TM]`
3. **Floating / Sticky Bottom Action Bar**:
   On mobile phones (`< 768px`), the three vital actions dock to the thumb zone:
   - **`[ நகலெடு ]` (Copy)**: Terracotta accent with high contrast.
   - **`[ திசை மாற்று ]` (Swap)**: Reverses conversion with 1 tap.
   - **`[ அழி ]` (Clear)**: Subtle muted reset button.

### B. Live Conversion Flow (Zero Clicks)
```text
[ பயனர் உரையை ஒட்டுகிறார் / தட்டச்சு செய்கிறார் ]
                      │
                      ▼ (50ms அமைதி நேரம்)
[ தானியங்கி எழுத்துரு கண்டறிதல் (எ.கா: பாமினி) ]
                      │
                      ▼
[ நிகழ்நேர ஒருங்குறி தமிழ் உரை பார்வைக்கு வருகிறது ]
                      │
                      ▼ (ஒற்றைத் தட்டு)
[ "நகலெடு" பொத்தான் ] ──► [ "நகலெடுக்கப்பட்டது!" அறிவிப்பு ]
```

---

## 6. CSS Design Tokens (`playground/src/index.css`)

```css
@theme {
  --color-canvas-light: #faf7f2;
  --color-surface-light: #ffffff;
  --color-semman-light: #963824;
  --color-semman-hover-light: #7d2e1c;
  --color-sandhanam-light: #b88628;
  --color-mai-light: #1f1a17;
  --color-border-light: #e8e0d4;

  --color-canvas-dark: #141210;
  --color-surface-dark: #1c1815;
  --color-semman-dark: #d95c43;
  --color-semman-hover-dark: #e6725b;
  --color-sandhanam-dark: #e0a638;
  --color-mai-dark: #f4efe8;
  --color-border-dark: #332b25;
}
```
