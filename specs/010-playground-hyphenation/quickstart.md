# Quickstart: Testing the Tamil Hyphenator Tool in Playground

This guide explains how to start, interact with, and validate the new **Tamil Syllabic Hyphenator & Line Wrapper** tool in the Playground.

---

## 1. Running the Playground Locally

```bash
# Start Vite development server
pnpm --filter tamil-toolkit-playground dev
```

Open `http://localhost:5173` in your browser.

---

## 2. Navigating to the Tool

1. From the **Overview Hub** (*முகப்பு*), click on the **சொல் & பத்தி அசையசைப்பி (Hyphenator & Line Wrapper)** card under Public Utilities (*பொதுக் கருவிகள்*).
2. Alternatively, select the **Public Tools** (*பொதுக் கருவிகள்*) tab in the top navigation bar and click the **அசையசைப்பி** sub-chip.

---

## 3. Interactive Testing Scenarios

### Scenario A: Word Syllabification & Coda Binding
1. Under **Word Syllables** tab, click the preset **பல்கலைக்கழகம்**.
2. Verify that the word is broken into: `பல்` · `க` · `லைக்` · `க` · `ழ` · `கம்`.
3. Note the rule annotation: pure consonants with pulli (`ல்`, `க்`, `ம்`) bind backwards to the vowel nucleus and never begin a line.
4. Try increasing `Left Margin` or `Right Margin` to 3; notice how edge breakpoints are safely constrained.

### Scenario B: Paragraph Soft-Hyphens
1. Switch to the **Paragraph Soft-Hyphens** tab.
2. Paste a Tamil paragraph (or click the sample text button).
3. Toggle "Show invisible soft hyphens" to see where browsers will be allowed to break lines.
4. Click "Copy HTML (`&shy;`)" to copy the pre-hyphenated text for publication in websites or blog posts.

### Scenario C: Line Wrapping Simulator
1. Switch to the **Column Wrap Preview** tab.
2. Drag the **Column Width** slider from 10 to 30 letters.
3. Observe how lines wrap strictly at valid syllable boundaries with trailing hyphens (`-`).
4. Toggle "Compare with Default Wrap" to observe how ordinary browser wrapping produces irregular breaks and stranded consonants.

---

## 4. Running Automated Tests

```bash
pnpm --filter tamil-toolkit-playground test
```
