# Contract: Unslop Design & Interaction Contract

## 1. Interaction Rules Contract
- **Hover Transitions**:
  - Maximum duration: 150ms.
  - Allowed properties: `border-color`, `background-color`, `color`, `opacity`.
  - Strictly banned: `scale-105`, `scale-110`, `translate-x-1` on hover, spring bouncing.
- **Active / Press Transitions**:
  - Allowed tactile press: `active:scale-[0.99]` (subtle 1% press feedback).
- **Focus Outlines**:
  - `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] focus-visible:ring-offset-2`.

## 2. Visual Materiality & Palette Contract
- **Canvas / Background**: `var(--bg-canvas)` (`#faf7f2` light / `#0c0e11` dark basalt granite).
- **Surface**: `var(--bg-surface)` (`#ffffff` light / `#14171c` dark cool slate).
- **Raised**: `var(--bg-raised)` (`#f3eee6` light / `#1c2026` dark elevated console).
- **Hairline Borders**: `1px solid var(--border-line)` (`#e8e0d4` light / `#262b33` dark stone divider).
- **Primary Brand Accent**: Terracotta `var(--color-semman)` (`#963824` light / `#e05338` dark vermilion).
- **Secondary Accent**: Sandalwood `var(--color-sandhanam)` (`#b88628` light / `#d99f36` dark antique brass).
- **Secondary Accent Light**: `var(--color-sandhanam-light)` (`#fbf5ea` light / `#261d10` dark amber brass).
- **Text Primary**: Carbon Ink `var(--color-mai)` (`#1f1a17` light / `#f3f4f6` dark crisp off-white, 15.8:1 contrast).
- **Text Secondary / Muted**: `var(--color-muted)` (`#574e47` light / `#949ca8` dark cool silver, 5.7:1 contrast) exceeding WCAG AA minimum.

## 3. Copy & Vocabulary Contract
- No marketing buzzwords ("Fast • Secure • Authentic Tamil", "Zero-latency in-browser utilities").
- Utilitarian, descriptive terminology in both Tamil and English dictionaries in `playground/src/lib/i18n.ts`.
