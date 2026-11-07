# Quickstart Validation Guide: Canonical Prosodic & Syllabic Tamil Hyphenation (`015-canonical-tamil-hyphenation`)

## Prerequisites

- Rust stable toolchain (`cargo`, `rustup`)
- Node.js $\ge 20$
- Python $\ge 3.11$ (for `just test-parity`)

---

## 1. Validate Core Rust Engine & Golden Vectors

Run the `tamil-hyphen` unit and golden vector test suites:

```powershell
cargo test -p tamil-hyphen
```

**Expected Outcome**:
- Short words ($< 6$ tailored Tamil letters: `உலகம்`, `சமூகம்`, `வணிகம்`, `திட்டம்`, `வரலாறு`, `அறிவியல்`, `பாதுகாக்க`) return `0` break points under default `HyphenationConfig::default()` (`left_min = 3, right_min = 3`).
- Bigger words ($\ge 6$ tailored Tamil letters) break cleanly at Tamil *Asai* boundaries with zero 1-letter or 2-letter segments:
  - `பல்கலைக்கழகம்` $\rightarrow$ `பல்கலைக்-கழகம்`
  - `பல்கலைக்கழகங்களில்` $\rightarrow$ `பல்கலைக்-கழகங்-களில்`
  - `தொழில்நுட்பம்` $\rightarrow$ `தொழில்-நுட்பம்`
  - `படைப்பாற்றல்` $\rightarrow$ `படைப்-பாற்றல்`
  - `கண்டுபிடிப்பு` $\rightarrow$ `கண்டு-பிடிப்பு`
  - `இன்றியமையாத` $\rightarrow$ `இன்றி-யமையாத`
  - `திருச்சிராப்பள்ளி` $\rightarrow$ `திருச்-சிராப்-பள்ளி`
  - `ஒருங்கிணைக்கப்பட்ட` $\rightarrow$ `ஒருங்-கிணைக்-கப்பட்ட`

---

## 2. Validate Microsoft Word Add-in & Playground Engines

Verify the standalone JS engine in `integrations/office-word-addin/engine.js`:

```powershell
node -e "const E = require('./integrations/office-word-addin/engine.js'); console.log(E.hyphenateWord('உலகம்', 3, 3, '-')); console.log(E.hyphenateWord('பல்கலைக்கழகங்களில்', 3, 3, '-')); console.log(E.hyphenateWord('தொழில்நுட்பம்', 3, 3, '-'));"
```

**Expected Output**:
```text
உலகம்
பல்கலைக்-கழகங்-களில்
தொழில்-நுட்பம்
```

---

## 3. Validate Multi-Runtime Parity & Quality Gates

```powershell
just test-rust
just test-parity
```
