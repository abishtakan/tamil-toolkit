# Feature Specification: Unslop UI Design & De-AI-ification

**Feature Branch**: `007-unslop-ui-design`

**Created**: 2026-11-05

**Status**: Complete — listed implementation tasks and verification are complete (2026-11-08)

**Input**: User description: "fix AI-ish elements in the UI. fully research online and find out ai-ish things. there are already some methods for unslop ai designs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Elimination of AI-Slop Layouts & Asymmetric Functional Hierarchy (Priority: P1) 🎯 MVP

As a user and developer visiting the Tamil Toolkit Playground, I want the interface to present a purposeful, high-density linguistic workbench with clear functional hierarchy instead of generic AI-generated marketing tropes (such as repetitive 4-card uniform grids, floating oversized hero banners, and generic pill tags), so that the tool immediately feels like an authentic, professional utility crafted with human intent.

**Why this priority**: Repetitive symmetrical cards and generic hero sections are the primary tell of AI-slop design. Replacing them with an asymmetric, content-driven layout (e.g., prominent workbench zones, contextual previews, and compact diagnostic trays) immediately establishes visual credibility and tool utility.

**Independent Test**: Can be tested by opening the playground home view and verifying that the uniform 4-card grids and oversized gradient hero banner are replaced by a purposeful, asymmetric workbench layout where primary tools (e.g., Codec Converter) have distinct functional prominence over secondary diagnostics.

**Acceptance Scenarios**:

1. **Given** the user lands on the Home/Hub view, **When** viewing the layout, **Then** the interface displays an authentic workbench structure with distinct visual weight for primary versus secondary utilities, with zero repetitive identical 4-card rows.
2. **Given** the primary tools section, **When** examining tool entry points, **Then** tools feature informative, contextual micro-previews (e.g., font badge previews, live calendar badge, numeral conversion indicator) rather than generic identical icon boxes with placeholder tags.
3. **Given** the developer diagnostics area, **When** viewing technical utilities, **Then** tools are organized as an integrated, high-density diagnostic panel rather than decorative marketing cards.

---

### User Story 2 - Purging AI-Slop Micro-Interactions, Hover Gimmicks & Shadows (Priority: P2)

As a user interacting with buttons, cards, and inputs, I want interactions to feel crisp, instant, and tactile (subtle 100-150ms state shifts, 1px hairline borders, and clear keyboard focus rings) rather than bouncy AI hover scaling (`scale-105`), floating glassmorphism, or soft ambient neon glows, so that the interface feels fast, responsive, and distraction-free.

**Why this priority**: AI design prompts universally over-index on bouncy hover transforms (`group-hover:scale-105`, animated sliding arrows, heavy drop shadows) that introduce visual jitter and make the interface feel like a disposable demo rather than production software.

**Independent Test**: Can be tested by hovering, clicking, and tabbing across all interactive elements (cards, buttons, tabs, inputs) and verifying that all `scale-105` transforms and bouncy translations are removed in favor of crisp 1px hairline color transitions and high-visibility `:focus-visible` outlines.

**Acceptance Scenarios**:

1. **Given** any card or interactive container, **When** the user hovers over it, **Then** there is zero scale distortion (`scale-105`), and state feedback is provided via crisp hairline border color shifts (`border-[var(--color-semman)]` or tonal surface tint) within 120ms.
2. **Given** interactive buttons and chips, **When** pressed or focused, **Then** tactile active states (`active:scale-[0.99]`) and high-contrast focus rings appear without layout shifts.
3. **Given** the global stylesheet, **When** evaluating transition rules, **Then** blanket `transition: all` rules are replaced with explicitly targeted properties (e.g. `transition: background-color 150ms ease, border-color 150ms ease`).

---

### User Story 3 - Authentic Linguistic Copy & Cultural Materiality (Priority: P3)

As a native Tamil speaker or linguistic researcher, I want the copy, typography, and visual materiality of the toolkit to convey authentic Tamil craft (classical Terracotta, palm leaf parchment, sandalwood brass, and carbon ink) and precise utilitarian copy, completely free of generic AI SaaS microcopy ("Zero-latency in-browser utilities", "Fast • Secure • Authentic Tamil", "Build the future"), so that the interface reflects genuine cultural and technical craftsmanship.

**Why this priority**: AI templates fill interfaces with hollow superlatives and buzzwords. Replacing generic marketing claims with clear, domain-accurate descriptions reinforces trust and cultural authenticity.

**Independent Test**: Can be tested by reviewing copy across both Tamil and English locales and verifying that all buzzword tags and generic marketing banners are replaced with precise, descriptive language explaining exactly what linguistic task each tool performs.

**Acceptance Scenarios**:

1. **Given** the application header and hero section, **When** reading interface text, **Then** generic buzzword badges are replaced with utilitarian domain information (e.g. active WASM engine status, offline verification badge, exact supported legacy font count).
2. **Given** tool descriptions in both locales, **When** reading tool cards, **Then** copy directly describes the linguistic operation (e.g., "Unicode decomposition & grapheme cluster boundaries" instead of "Diagnostics & low-level sandbox").
3. **Given** the color and typography design system, **When** inspecting contrast ratios, **Then** all text elements satisfy WCAG AA (minimum 4.5:1) and AAA where applicable against parchment/terracotta backgrounds.

---

### Edge Cases

- **Mobile Viewport Densities**: When the asymmetric desktop workbench folds into mobile screens (<640px), the hierarchy must preserve clear primary tool access without collapsing into an endless vertical stack of uniform cards.
- **Dark Mode Materiality**: In dark mode, parchment surfaces must transition to deep carbon ink stone (`#141210`, `#1c1815`) without re-introducing neon glows or saturated indigo tints.
- **Dynamic Content Heights**: Asymmetric cards with contextual previews must handle localized text length variations gracefully without clipped text or uneven layout misalignment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the uniform 4-card grid layout with an asymmetric, content-driven workbench architecture prioritizing primary tools (Font Converter & Numeral Formatter) with contextual previews.
- **FR-002**: System MUST eliminate the floating gradient hero marketing container in favor of an integrated, functional workbench header displaying live engine telemetry (WASM status, offline client-side indicator, tool shortcut switcher).
- **FR-003**: System MUST ban all decorative hover-scale animations (`scale-105`, `group-hover:scale-105`) and floating transform gimmicks across all UI components.
- **FR-004**: System MUST enforce crisp 1px hairline borders (`var(--border-line)`) and subtle surface tonal shifts in place of heavy drop shadows or glassmorphism.
- **FR-005**: System MUST eliminate generic AI microcopy and buzzword badge strings ("Fast • Secure • Authentic Tamil", "Zero-latency in-browser utilities") in favor of concrete, domain-specific linguistic descriptions in both Tamil and English dictionaries.
- **FR-006**: System MUST ensure every interactive element has explicit `:focus-visible` styling conforming to WCAG AA accessibility standards.
- **FR-007**: System MUST replace blanket `transition: all` declarations with targeted CSS transitions (`border-color`, `background-color`, `color`) capped at 150ms duration.
- **FR-008**: System MUST organize developer diagnostic tools (Scalar Inspector, Dispatcher, Code Generator, Batch Processor) into an integrated utility console rather than consumer marketing cards.
- **FR-009**: System MUST maintain the authentic classical Tamil materiality palette (Terracotta `#963824`, Palm Leaf `#faf7f2`, Sandalwood `#b88628`, Carbon Ink `#1f1a17`) without artificial neon accents.

### Key Entities

- **WorkbenchLayout**: The primary layout system providing asymmetric hierarchy between high-frequency linguistic converters and secondary technical diagnostics.
- **ToolCardVariant**: Structural presentation modes (Hero, Compact, Console) replacing one-size-fits-all card templates.
- **DesignTokens**: The consolidated color, border, and typography scales defining the tactile, hairline-separated aesthetic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero occurrences of `scale-105` or spring-based hover scale animations in the playground codebase.
- **SC-002**: Primary tool discovery speed: Users can identify and launch the primary Font Converter or Numeral tool within 1 click directly from the home view.
- **SC-003**: 100% of text and interactive controls maintain a contrast ratio of at least 4.5:1 against their active background in both light and dark themes.
- **SC-004**: Elimination of 100% of identified generic AI marketing copy from both Tamil and English dictionaries.
- **SC-005**: Full compilation and test suite passing (`tsc -b`, Vitest 30+ tests, `just agent-post-edit`).

## Assumptions

- The primary audience seeks a serious, reliable linguistic utility for Tamil publishing, translation, banking, and software engineering—not a flashy SaaS demo.
- Clean typography and functional density with clear visual anchors reflect professional craftsmanship far better than decorative card embellishments.
