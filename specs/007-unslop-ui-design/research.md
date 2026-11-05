# Research: Unslop UI Design & De-AI-ification

## Research Summary: The "AI Slop" Visual Signature
Modern LLMs and code generators produce visual interfaces with recognizable artifacts due to averaging common web templates in training corpora. In frontend applications, these artifacts include:
1. **The Monoculture Layout**: Repeating 3 or 4 identical rectangular cards with centered icon circles, badge chips, and generic chevron links.
2. **The "Floating SaaS Hero"**: A rounded-3xl container with a subtle radial/conic gradient, a pill tag ("BETA" / "100% Client-Side"), an inflated marketing title, and a hollow subtitle.
3. **Gratuitous Bouncy Micro-Interactions**: Universal application of `group-hover:scale-105`, spring easings, and sliding arrows that add visual instability.
4. **Superlative Buzzword Copy**: Phrasing like "Fast • Secure • Authentic Tamil", "Zero-latency in-browser utilities", "Build the future of...", rather than domain-accurate descriptions.
5. **Lack of Information Density**: Expansive empty space with large padding (p-10) surrounding low-information components.

## Decision 1: Asymmetric Bento Workbench Layout
- **Decision**: Replace the uniform 4-card grids in `OverviewHub.tsx` with a purposeful, high-density **Asymmetric Workbench**.
  - **Hero Feature Zone (2-col span on desktop)**: Legacy Font & Encoding Converter (`CodecConverter`), featuring interactive quick-action chips for instant conversion between Bamini/TSCII and Unicode.
  - **Linguistic Utilities (1-col each)**: Numeral Formatter (with quick currency/cheque toggle preview) and Calendar & Panchangam Explorer (with live solar date indicator).
  - **Collation & Grammar Card**: Agara Varisai sorter with explicit Tamil alphabetical order demonstration (`அ` → `ன`).
  - **Developer Diagnostic Console (Integrated Matrix)**: Group Scalar Inspector, WebAssembly Dispatcher Sandbox, Code Generator, and Batch Processor into a unified, high-density developer toolbar/tray with monospace accents rather than disconnected marketing cards.
- **Rationale**: Real human-designed developer and linguistic tools (e.g. VS Code, Figma, Linear, GitHub, Apple Developer tools) prioritize asymmetric information density and immediate tool readiness over repetitive card rows.

## Decision 2: Elimination of Scale-105 & Bouncy Hover Physics
- **Decision**: Purge all instances of `group-hover:scale-105` and arbitrary transform translations. Replace with:
  - 1px hairline border color transitions (`border-[var(--border-line)]` to `border-[var(--color-semman)]` or `border-[var(--color-sandhanam)]`) over a crisp 120ms duration.
  - Subtle tonal surface shifts (`bg-[var(--bg-raised)]`).
  - Tactile press feedback (`active:scale-[0.99]`).
  - High-visibility keyboard focus rings (`focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] focus-visible:ring-offset-2`).
- **Rationale**: Utility software should feel solid and grounded, not float or bounce when the cursor glides over it.

## Decision 3: Utilitarian Workbench Header & Engine Status
- **Decision**: Replace the floating gradient marketing box with a functional workbench status header:
  - Displays live WebAssembly engine status (`wasm32-unknown-unknown` loaded / offline-ready).
  - Displays active encoding coverage (7 legacy font profiles supported).
  - Provides instant tool search / quick navigation anchor without superfluous slogans.
- **Rationale**: Users opening a language workbench need immediate confidence that the engine is ready and functional, not generic marketing claims.

## Decision 4: Authentic Linguistic Copy Revision
- **Decision**: Audit and refine `i18n.ts` dictionary copy:
  - Replace "Zero-latency in-browser utilities" with "சொல், எழுத்துரு & பஞ்சாங்கக் கருவிகள்" / "Script, Numeral & Calendar Tools".
  - Replace "Diagnostics & low-level sandbox" with "தொழில்நுட்ப ஆய்வகம் & ஒருங்குறித் தரவுகள்" / "Engine Diagnostics & Unicode Inspector".
  - Replace "Fast • Secure • Authentic Tamil" with "100% சாதனத்திற்குள் இயங்கும் தனிப்பட்ட பணித்தளம்" / "Local WebAssembly Engine · Zero Data Leaves Device".
- **Rationale**: Direct, utilitarian copy establishes seriousness and domain respect.

## Decision 5: Basalt Granite & Inscription Slate Dark Mode Palette
- **Decision**: Completely replace muddy, swamp-brown dark mode colors (`#141210`, `#1c1815`, `#26211d`, `#332b25`, `#2d2211`) with a sleek temple basalt granite (`#0c0e11`, `#14171c`, `#1c2026`) and antique brass / vermilion palette:
  - Background: `#0c0e11` (neutral dark granite, zero brown cast).
  - Surface: `#14171c` (slate stone).
  - Raised tiles: `#1c2026` (elevated console).
  - Borders: `#262b33` (crisp cool hairline divider).
  - Primary text: `#f3f4f6` (crisp off-white, 15.8:1 contrast, WCAG AAA).
  - Muted text: `#949ca8` (cool stone silver, 5.7:1 contrast, WCAG AA).
  - Terracotta vermilion: `#e05338` (vibrant readable accent).
  - Sandalwood brass: `#d99f36` (antique inscription gold).
- **Rationale**: The previous dark mode suffered from yellow-brown swamp undertones that caused visual fatigue and appeared dirty. The basalt granite palette evokes ancient Thanjavur granite temple stones and engraved copper inscriptions while maintaining outstanding contrast and accessibility.
