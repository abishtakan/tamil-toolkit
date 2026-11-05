# Feature Specification: Interactive Public & Developer Playground (`playground`)

**Feature Branch**: `005-playground`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "the playground is UI for these packages. It will have public tools using these packages. and developer tools. The UI/UX should be better easier to use in mobile aswell. Not confusing. No multiple clicks for simple things. real-time conversion, etc. Also use modern tech stack that not consume lot of resources to build or use. nextjs, tailwindcss, shadcn - these are just suggestion but if it is wrong suggestion let me know."

## Clarifications

### Session 2026-11-05
- Q: What are the primary user groups and use cases?
  → A:
    1. **Public / End Users**: Everyday practical tools (legacy font converter, numeral/currency to Tamil words, calendar/panchangam explorer, Tamil text sorter) requiring zero technical knowledge.
    2. **Developers & Integrators**: Interactive diagnostics, Unicode scalar breakdown, raw dispatcher sandbox, and multi-language code snippet generation (Rust, Python, WebAssembly, Dart).
- Q: What are the mobile and interaction UX principles?
  → A:
    - **Zero-Friction Real-Time Conversion**: Outputs update live as the user types or pastes without requiring a manual "Submit" or "Convert" button click.
    - **No Multiple Clicks for Common Actions**: Pasting auto-detects encoding; one tap copies the result to clipboard with visual feedback; one tap swaps directions.
    - **Mobile-First Touch Ergonomics**: Minimum 44x44px touch targets, sticky bottom action bar on mobile viewports for primary actions (Copy, Clear, Swap), and clean tab navigation without cluttered or nested modal menus.
- Q: Where does computation occur and what are the privacy guarantees?
  → A: 100% client-side computation in the browser via compiled WebAssembly (`tamil-toolkit`). No user text, documents, or queries are transmitted to or stored on remote servers.
- Q: What is the recommended technology stack for low resource consumption and optimal WASM support?
  → A:
    - **Recommended Stack**: **Vite + React + Tailwind CSS + shadcn/ui (Radix UI) + Lucide Icons**.
    - **Why not Next.js**: Next.js is designed for server-side rendering (SSR/RSC) with a Node.js server runtime. For a pure client-side, zero-backend, offline-capable WASM application, Next.js adds unnecessary build complexity, larger bundle sizes, hydration mismatches with WASM, and heavy build times. Vite provides sub-second builds, native ES module HMR, effortless WebAssembly support, and outputs a pure static Single Page Application (SPA) deployable anywhere (e.g. GitHub Pages) with near-zero resource consumption.
- Q: When a first-time user opens the playground, how should the initial interface language be determined?
  → A: Auto-detect from browser locale (defaults to `தமிழ்` if `navigator.language` starts with "ta", otherwise `English`); user selection is persisted in local storage.
- Q: Which view should be displayed by default when a user first lands on the playground?
  → A: Overview Hub / Dashboard, presenting categorized cards for all public and developer tools with quick one-tap entry into any tool.
- Q: How should geographic location be set for calculating local daylight periods (Rahu Kalam, Yamagandam, Gulikai) and panchangam in the calendar tool?
  → A: Browser Geolocation API prompt with automatic fallback to Chennai (13.0827° N, 80.2707° E) if denied, unavailable, or dismissed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Public Tools with Zero-Friction Mobile & Real-Time UX (Priority: P1) 🎯 MVP

As an everyday user or mobile phone user (content writer, translator, legal professional, or student), I want an uncluttered web app where I can paste or type text and immediately see converted results in real time with a single tap to copy, without having to navigate multiple dropdowns or press "Submit" buttons.

**Why this priority**: Delivers immediate, frustration-free utility for the most common end-user tasks on both mobile devices and desktops.

**Independent Test**: Open the application on a mobile browser viewport (390px width), paste Bamini text into the converter input; verify that the encoding is detected automatically, the Unicode result appears live in under 50ms without pressing any convert button, and tapping the floating copy button copies the result to clipboard with immediate visual confirmation.

**Acceptance Scenarios**:
1. **Given** an empty converter on desktop or mobile, **When** the user pastes legacy Tamil text (e.g. Bamini or TSCII), **Then** the engine automatically detects the encoding and renders the converted Unicode Tamil output in real time without requiring a button press.
2. **Given** live output displayed in any tool, **When** the user taps the primary Copy button, **Then** the result is copied to the system clipboard and a brief toast notification confirms the action.
3. **Given** a user entering numbers in the Numeral Formatter, **When** each digit is typed, **Then** the formal Tamil words (cheque/legal format) and spoken equivalents update instantaneously.
4. **Given** mobile viewport usage, **When** viewing any tool, **Then** key actions (Copy, Clear, Swap) remain easily reachable in the bottom thumb zone without zooming or horizontal scrolling.

---

### User Story 2 - Developer Diagnostics & Interactive API Sandbox (Priority: P2)

As a software engineer, data scientist, or system integrator building applications with Tamil text, I want an interactive developer sandbox where I can inspect Unicode scalar compositions, test edge-case inputs against all toolkit packages, inspect raw JSON requests and responses, and copy reproducible code snippets for my preferred programming language.

**Why this priority**: Accelerates developer onboarding and debugging. Developers can immediately diagnose encoding bugs, verify linguistic behavior, and obtain ready-to-run code snippets in Rust, Python, TypeScript, and Dart.

**Independent Test**: Navigate to the Developer tab, input a Tamil string containing complex grapheme clusters or invisible characters, verify the scalar breakdown displays exact hex codepoints and cluster boundaries, and verify that the generated code snippet executes identically in external environments.

**Acceptance Scenarios**:
1. **Given** a Tamil string with complex ligatures or potential invisible characters (e.g., ZWJ or ZWNJ), **When** inspected in the developer inspector, **Then** every Unicode scalar is individually visualized with its hexadecimal value (`\u{0B85}`), category classification, and grapheme cluster boundaries.
2. **Given** any operation configured in the sandbox UI, **When** the user switches to the Code Snippet tab, **Then** valid, runnable code samples are generated in Rust, Python, TypeScript/JavaScript, and Dart matching the exact inputs and options selected.
3. **Given** custom JSON dispatcher input, **When** the developer submits the payload, **Then** the raw JSON response is displayed alongside execution latency and diagnostic metadata.

---

### User Story 3 - Client-Side Privacy, Low Resource Footprint & Offline Operation (Priority: P3)

As a privacy-conscious user or developer handling sensitive, confidential documents (such as personal letters, legal contracts, or banking records) on constrained mobile networks or hardware, I want the playground to load rapidly, consume minimal memory/CPU, execute entirely within my local browser sandbox without transmitting data to any remote server, and remain fully functional when offline.

**Why this priority**: Guarantees zero data leakage for confidential records and ensures smooth performance on low-end mobile devices and spotty network connections.

**Independent Test**: Load the playground on a throttled mobile network, verify initial asset bundle loads under 250 KB (excluding WASM binary), turn on airplane mode, perform legacy conversions and calendar calculations, and verify through network activity monitoring that zero network requests are dispatched during operation.

**Acceptance Scenarios**:
1. **Given** an active playground session, **When** network connectivity is severed, **Then** all core public and developer tools remain fully operational without error or degradation.
2. **Given** sensitive text pasted into any tool, **When** processing and converting data, **Then** 100% of data transformations occur locally in the client runtime without sending HTTP requests.
3. **Given** a low-power mobile device, **When** typing into the real-time converter, **Then** execution is debounced so UI rendering remains smooth at 60 fps without battery drain.

---

### Edge Cases

- **Ambiguous or Short Input**: When a user inputs text that could match multiple legacy encodings or is too short for high-confidence detection (< 4 characters), the converter displays candidate encodings with confidence percentages and provides one-tap chips to manually select the intended source encoding without opening nested menus.
- **Malformed Input & Corrupt Codepoints**: When inputs contain invalid byte sequences or unsupported control characters, the tools isolate invalid sections, display inline non-blocking visual badges, and preserve surrounding valid text.
- **Large Document Processing**: When processing text or files exceeding standard single-view capacity (e.g. files > 2 MB), processing is delegated to a background Web Worker so the main UI thread remains completely responsive.
- **Mixed-Language Content**: When text contains mixed English, numerals, and Tamil, conversions preserve English text and punctuation unaltered while transforming legacy Tamil sequences correctly.
- **Mobile Keyboard Obstruction**: When the virtual keyboard is open on mobile devices, input and live output areas adjust dynamically to prevent controls from being pushed offscreen.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The playground MUST provide a clean, modern web interface starting with an uncluttered Overview Hub / Dashboard that presents categorized cards for all public and developer tools, with intuitive top/bottom navigation requiring at most one tap to launch or switch between tools.
- **FR-002**: All text-based conversion tools (Legacy Converter, Numeral Formatter, Text Sorter) MUST execute in real time as the user types or pastes, debounced smoothly (e.g. 50–100ms) without requiring the user to press a "Convert" or "Submit" button.
- **FR-003**: The Legacy Font & Encoding Converter MUST automatically detect the input encoding upon text entry and display the converted Unicode output immediately, with a single-tap override chip row for manual selection.
- **FR-004**: Every tool MUST provide a prominent, single-tap "Copy to Clipboard" action with instant visual confirmation (toast / icon swap) and a single-tap "Clear" action.
- **FR-005**: Bidirectional tools (Unicode ↔ Legacy encodings) MUST provide a single-tap "Swap" button that flips input and output roles seamlessly.
- **FR-006**: The Public Tools section MUST include a Numeral & Currency Formatter providing formal Tamil words, spoken variants, legal cheque wording format, traditional Tamil numerals, and Tamil fractions.
- **FR-007**: The Public Tools section MUST include a Tamil Calendar & Panchangam Explorer displaying Tamil solar dates, Thiruvalluvar year, 60-year cycle names, nakshatram, tithi, daylight periods (Rahu kalam, Yamagandam, Gulikai calculated using browser Geolocation API with automatic fallback to Chennai coordinates 13.0827° N, 80.2707° E), and official holiday observances within supported bounded ranges.
- **FR-008**: The Public Tools section MUST include an Agara Varisai Sorter supporting alphabetical sorting of Tamil words, word frequency extraction, and syllable breakdown.
- **FR-009**: The Developer Tools section MUST include a Unicode Scalar & Grapheme Inspector that visualizes individual scalar values (`\u{0B85}`), hex codepoint badges, cluster composition, and alerts for invisible format controls (ZWJ `\u{200D}`, ZWNJ `\u{200C}`).
- **FR-010**: The Developer Tools section MUST include an Interactive Dispatcher Sandbox allowing manual execution of raw JSON payloads against all active toolkit capabilities with live response and latency display.
- **FR-011**: The Developer Tools section MUST provide dynamic, copy-ready Code Snippets for every configured operation across four runtimes: Rust, Python, TypeScript/JavaScript, and Dart.
- **FR-012**: The playground MUST execute all linguistic and computational logic entirely client-side in the browser using the compiled toolkit WebAssembly engine, requiring zero server-side processing for any tool operation.
- **FR-013**: The playground MUST function completely offline once initial static web assets have loaded (Progressive Web App / service worker caching).
- **FR-014**: The mobile layout MUST follow touch ergonomics: minimum 44x44px interactive touch targets, thumb-accessible primary action bar on viewports < 768px, and zero horizontal scrolling.
- **FR-015**: Heavy operations (such as batch text file conversion) MUST run inside a dedicated Web Worker to prevent blocking the UI rendering thread.
- **FR-016**: The interface MUST be fully bilingual, auto-detecting the initial language from browser locale (`navigator.language` matching `ta*` → `தமிழ்`, otherwise `English`) while persisting user toggle selections across sessions in local storage, and offering a single-tap language switcher (`தமிழ்` / `English`) that localizes all tool titles, descriptions, action buttons, placeholders, status chips, and copy toast confirmations into natural, idiomatic Tamil.
- **FR-017**: The visual design MUST embody an authentic Tamil aesthetic rooted in classical palm-leaf manuscripts (*ஓலைச்சுவடி*), natural terracotta earth (*செம்மண்* `#963824`), warm rice-ivory parchment, and carbon ink (*மையெழுத்து*), strictly avoiding generic synthetic SaaS palettes (no electric blues, purples, pinks, or artificial greens) while maintaining a clean, uncluttered, high-contrast interface.

### Key Entities

- **ToolDefinition**: Represents an individual public or developer utility with name, category, icon, description, and execution handler.
- **ConversionState**: Encapsulates active input, detected/selected encoding, converted output, confidence rating, and processing status.
- **ScalarBreakdown**: Represents an analyzed Tamil string with codepoint sequences, hex strings, Unicode category names, and cluster boundary tags.
- **CalendarView**: Encapsulates solar date, civil date, panchangam attributes, daylight period bounds, and festival/holiday markers for a designated date.
- **CodeSnippetExport**: Contains generated syntax-highlighted code samples for Rust, Python, TypeScript, and Dart matching the user's active configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Common conversions (e.g. converting a paragraph of legacy text or formatting a number into Tamil words) complete in under 30 milliseconds once loaded.
- **SC-002**: 100% of user data remains on the client device; zero outbound network requests containing user input are transmitted during tool usage.
- **SC-003**: Users can complete a conversion (paste -> see result -> copy) in under 3 seconds with at most 1 click/tap.
- **SC-004**: The web application achieves a Lighthouse Performance and Accessibility score of ≥ 95 on mobile devices.
- **SC-005**: All public and developer tools remain 100% functional when the device is completely disconnected from the internet.
- **SC-006**: Initial static bundle size (JavaScript + CSS, excluding WebAssembly binary) remains under 250 KB gzipped for lightning-fast mobile loading.
- **SC-007**: Interface maintains full responsive usability across viewports ranging from 360px (mobile) to 4K desktop screens without layout breaking or clipped text.
- **SC-008**: 100% of user interface strings, buttons, tooltips, and toasts have complete parity in both Tamil and English, switchable in real-time with zero page reload.

## Assumptions & Technology Decisions

### Technology Stack Decisions
- **Architecture**: Static Single Page Application (SPA) deployed to static hosting (e.g. GitHub Pages).
- **Bundler & Build Tool**: **Vite** (chosen over Next.js for instant builds, lightweight footprint, native ES modules, and seamless WebAssembly integration without SSR/Node server overhead).
- **UI Framework & Components**: **React with TypeScript**, styled with **Tailwind CSS** and **shadcn/ui** (Radix UI accessible primitives) with **Lucide Icons** for a crisp, modern, accessible design system.
- **Linguistic Engine**: Official `tamil-toolkit` WebAssembly export (`wasm-bindgen`), with zero duplicate JavaScript linguistic algorithms.
- **Concurrency**: Web Workers used for non-blocking file processing and heavy operations.
