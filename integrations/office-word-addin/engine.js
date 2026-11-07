/**
 * Tamil Soft-Hyphenation Core Engine (Standalone ECMAScript)
 *
 * Implements phonotactically verified syllabic hyphenation using Unicode soft hyphens (\u00AD).
 * Safe for Microsoft Word (Office.js) and Google Docs (Google Apps Script).
 *
 * Rules:
 * 1. Independent vowels (Uyir \u0B85-\u0B94) start syllables.
 * 2. Consonants with vowel markers (Uyirmei) form syllabic nuclei.
 * 3. Pure consonants with pulli/virama (Mei \u0BCD) bind as codas to the preceding nucleus;
 *    a syllable NEVER begins with a pure consonant.
 * 4. Aytham (\u0B83) binds to the preceding nucleus.
 * 5. Minimum margins (leftMin=2, rightMin=2) protect short initial and final syllable runs.
 * 6. Idempotency: Multiple runs will never inject duplicate soft hyphens.
 */

const UYIR = new Set([
  0x0b85, 0x0b86, 0x0b87, 0x0b88, 0x0b89, 0x0b8a,
  0x0b8e, 0x0b8f, 0x0b90, 0x0b92, 0x0b93, 0x0b94
]);

const MEI_BASES = new Set([
  0x0b95, 0x0b99, 0x0b9a, 0x0b9c, 0x0b9e, 0x0b9f,
  0x0ba3, 0x0ba4, 0x0ba8, 0x0ba9, 0x0baa, 0x0bae,
  0x0baf, 0x0bb0, 0x0bb1, 0x0bb2, 0x0bb3, 0x0bb4,
  0x0bb5, 0x0bb6, 0x0bb7, 0x0bb8, 0x0bb9
]);

const VOWEL_SIGNS = new Set([
  0x0bbe, 0x0bbf, 0x0bc0, 0x0bc1, 0x0bc2, 0x0bc6,
  0x0bc7, 0x0bc8, 0x0bca, 0x0bcb, 0x0bcc, 0x0bd7
]);

const VIRAMA = 0x0bcd;
const AYTHAM = 0x0b83;
const SOFT_HYPHEN = '\u00AD';

/**
 * Segment a Tamil word into orthographic graphemes/syllabic units.
 */
function segmentTamilWord(word) {
  // Strip existing soft hyphens to guarantee idempotency
  const cleanWord = word.replace(/\u00AD/g, '');
  const units = [];
  const chars = Array.from(cleanWord);
  let i = 0;

  while (i < chars.length) {
    const code = chars[i].codePointAt(0);

    if (UYIR.has(code) || code === AYTHAM) {
      units.push(chars[i]);
      i++;
    } else if (MEI_BASES.has(code)) {
      let unit = chars[i];
      i++;
      if (i < chars.length) {
        const nextCode = chars[i].codePointAt(0);
        if (nextCode === VIRAMA || VOWEL_SIGNS.has(nextCode)) {
          unit += chars[i];
          i++;
        }
      }
      units.push(unit);
    } else {
      units.push(chars[i]);
      i++;
    }
  }

  return units;
}

/**
 * Group segmented graphemes into legal Tamil phonotactic syllables:
 * Pure consonants (Mei with pulli) and Aytham are bound as codas to the preceding nucleus.
 */
function syllabifyTamil(word) {
  const units = segmentTamilWord(word);
  if (units.length <= 1) return units;

  const syllables = [];

  for (let i = 0; i < units.length; i++) {
    const unit = units[i];
    const isMei = unit.length > 1 && unit.codePointAt(1) === VIRAMA;
    const isAytham = unit.codePointAt(0) === AYTHAM;

    if ((isMei || isAytham) && syllables.length > 0) {
      // Bind coda to the previous nucleus
      syllables[syllables.length - 1] += unit;
    } else {
      syllables.push(unit);
    }
  }

  return syllables;
}

/**
 * Soft-hyphenate a single Tamil word respecting margins.
 */
function hyphenateWord(word, leftMin = 2, rightMin = 2) {
  // Check if word contains any Tamil characters
  const hasTamil = /[\u0B80-\u0BFF]/.test(word);
  if (!hasTamil) return word;

  const syllables = syllabifyTamil(word);
  if (syllables.length < (leftMin + rightMin)) {
    return syllables.join('');
  }

  let result = '';
  for (let i = 0; i < syllables.length; i++) {
    result += syllables[i];
    const leftCount = i + 1;
    const rightCount = syllables.length - (i + 1);
    if (leftCount >= leftMin && rightCount >= rightMin) {
      result += SOFT_HYPHEN;
    }
  }

  return result;
}

/**
 * Soft-hyphenate any text, preserving punctuation, whitespace, and non-Tamil runs.
 */
function hyphenateText(text, leftMin = 2, rightMin = 2) {
  if (!text) return '';
  return text.replace(/[\u0B80-\u0BFF\u00AD]+/g, (match) => {
    return hyphenateWord(match, leftMin, rightMin);
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    segmentTamilWord,
    syllabifyTamil,
    hyphenateWord,
    hyphenateText,
    SOFT_HYPHEN
  };
}
