/**
 * Google Docs Workspace Add-on: Tamil Soft-Hyphenator
 *
 * Runs inside Google Docs using Google Apps Script V8 runtime.
 * Only requires `documents.currentonly` scope.
 * 100% private: no document data is sent across the network.
 */

/* global DocumentApp, HtmlService */

/**
 * Creates custom menu on document open.
 */
function onOpen() {
  DocumentApp.getUi()
    .createMenu('தமிழ் (Tamil Toolkit)')
    .addItem('மென்-இணைப்புப் பலகம் (Open Hyphenator Sidebar)', 'showSidebar')
    .addSeparator()
    .addItem('தேர்ந்தெடுத்ததை இணைக்கவும் (Hyphenate Selection)', 'hyphenateSelection')
    .addItem('முழு ஆவணத்தையும் இணைக்கவும் (Hyphenate Document)', 'hyphenateDocument')
    .addToUi();
}

/**
 * Shows the HTML sidebar.
 */
function showSidebar() {
  const ui = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('தமிழ் மென்-இணைப்பு')
    .setWidth(300);
  DocumentApp.getUi().showSidebar(ui);
}

// Linguistic Constants
const UYIR_SET = new Set([
  0x0b85, 0x0b86, 0x0b87, 0x0b88, 0x0b89, 0x0b8a,
  0x0b8e, 0x0b8f, 0x0b90, 0x0b92, 0x0b93, 0x0b94
]);

const MEI_BASE_SET = new Set([
  0x0b95, 0x0b99, 0x0b9a, 0x0b9c, 0x0b9e, 0x0b9f,
  0x0ba3, 0x0ba4, 0x0ba8, 0x0ba9, 0x0baa, 0x0bae,
  0x0baf, 0x0bb0, 0x0bb1, 0x0bb2, 0x0bb3, 0x0bb4,
  0x0bb5, 0x0bb6, 0x0bb7, 0x0bb8, 0x0bb9
]);

const VOWEL_SIGN_SET = new Set([
  0x0bbe, 0x0bbf, 0x0bc0, 0x0bc1, 0x0bc2, 0x0bc6,
  0x0bc7, 0x0bc8, 0x0bca, 0x0bcb, 0x0bcc, 0x0bd7
]);

const VIRAMA_CODE = 0x0bcd;
const AYTHAM_CODE = 0x0b83;
const SOFT_HYPHEN_CHAR = '\u00AD';

/**
 * Syllabifies a Tamil word and soft-hyphenates it respecting margins.
 */
function hyphenateTamilWord(word, leftMin = 2, rightMin = 2) {
  const clean = word.replace(/\u00AD/g, '');
  const chars = Array.from(clean);
  const units = [];
  let i = 0;

  while (i < chars.length) {
    const code = chars[i].codePointAt(0);
    if (UYIR_SET.has(code) || code === AYTHAM_CODE) {
      units.push(chars[i]);
      i++;
    } else if (MEI_BASE_SET.has(code)) {
      let u = chars[i];
      i++;
      if (i < chars.length) {
        const next = chars[i].codePointAt(0);
        if (next === VIRAMA_CODE || VOWEL_SIGN_SET.has(next)) {
          u += chars[i];
          i++;
        }
      }
      units.push(u);
    } else {
      units.push(chars[i]);
      i++;
    }
  }

  if (units.length <= 1) return units.join('');

  const syllables = [];
  for (let j = 0; j < units.length; j++) {
    const u = units[j];
    const isMei = u.length > 1 && u.codePointAt(1) === VIRAMA_CODE;
    const isAytham = u.codePointAt(0) === AYTHAM_CODE;
    if ((isMei || isAytham) && syllables.length > 0) {
      syllables[syllables.length - 1] += u;
    } else {
      syllables.push(u);
    }
  }

  if (syllables.length < (leftMin + rightMin)) {
    return syllables.join('');
  }

  let out = '';
  for (let k = 0; k < syllables.length; k++) {
    out += syllables[k];
    if ((k + 1) >= leftMin && (syllables.length - (k + 1)) >= rightMin) {
      out += SOFT_HYPHEN_CHAR;
    }
  }
  return out;
}

/**
 * Hyphenates text string preserving non-Tamil tokens.
 */
function hyphenateString(str, leftMin = 2, rightMin = 2) {
  if (!str) return '';
  return str.replace(/[\u0B80-\u0BFF\u00AD]+/g, (match) => {
    return hyphenateTamilWord(match, leftMin, rightMin);
  });
}

/**
 * Hyphenates active selection in Google Docs.
 */
function hyphenateSelection(leftMin = 2, rightMin = 2) {
  const doc = DocumentApp.getActiveDocument();
  const selection = doc.getSelection();

  if (!selection) {
    return { success: false, message: 'உரை எதையும் தேர்ந்தெடுக்கவில்லை (No text selected).' };
  }

  const elements = selection.getSelectedElements();
  let count = 0;

  for (let i = 0; i < elements.length; i++) {
    const el = elements[i];
    const textEl = el.getElement().asText();
    if (!textEl) continue;

    if (el.isPartial()) {
      const start = el.getStartOffset();
      const end = el.getEndOffsetInclusive();
      const sub = textEl.getText().substring(start, end + 1);
      const hyphenated = hyphenateString(sub, leftMin, rightMin);
      if (hyphenated !== sub) {
        textEl.deleteText(start, end);
        textEl.insertText(start, hyphenated);
        count++;
      }
    } else {
      const text = textEl.getText();
      const hyphenated = hyphenateString(text, leftMin, rightMin);
      if (hyphenated !== text) {
        textEl.setText(hyphenated);
        count++;
      }
    }
  }

  return {
    success: true,
    message: `${count} பகுதிகள் இணைக்கப்பட்டன (${count} text elements soft-hyphenated).`
  };
}

/**
 * Hyphenates all body paragraphs in Google Docs.
 */
function hyphenateDocument(leftMin = 2, rightMin = 2) {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const paragraphs = body.getParagraphs();
  let count = 0;

  for (let i = 0; i < paragraphs.length; i++) {
    const para = paragraphs[i];
    const text = para.getText();
    if (text && /[\u0B80-\u0BFF]/.test(text)) {
      const hyphenated = hyphenateString(text, leftMin, rightMin);
      if (hyphenated !== text) {
        para.setText(hyphenated);
        count++;
      }
    }
  }

  return {
    success: true,
    message: `முழு ஆவணமும் முடிந்தது: ${count} பத்திகள் இணைக்கப்பட்டன (${count} paragraphs hyphenated).`
  };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    hyphenateTamilWord,
    hyphenateString,
    SOFT_HYPHEN_CHAR
  };
}
