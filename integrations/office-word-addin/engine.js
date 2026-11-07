/**
 * Tamil Soft-Hyphenation Core Engine (Standalone ECMAScript)
 *
 * Implements phonotactically verified syllabic hyphenation for Microsoft Word (Office.js).
 * Supports two modes:
 * 1. Native <w:softHyphen/> mode: Invisible inside lines, shows '-' only at end-of-line wrap.
 * 2. Invisible Wrap (No Visual Hyphen) mode (\u200B): Wraps syllables cleanly at margins with ZERO visible hyphen.
 *
 * Rules:
 * 1. Independent vowels (Uyir \u0B85-\u0B94) act as syllable nuclei.
 * 2. Consonants with vowel markers (Uyirmei) or inherent-a consonants form syllable nuclei.
 * 3. Pure consonants with pulli/virama (Mei \u0BCD) and Aytham (\u0B83) bind as codas to the preceding nucleus;
 *    a segment NEVER begins with a pure consonant or Aytham.
 * 4. Grantha conjuncts (Ksha \u0B95\u0BCD\u0BB7, Shri \u0BB8\u0BCD\u0BB0\u0BC0 / \u0BB6\u0BCD\u0BB0\u0BC0) are treated atomically.
 * 5. Canonical Tamil Asai + 3-Letter Minimum Segment Rule (leftMin=3, rightMin=3):
 *    - Short words (< 6 Tamil letters, e.g., உலகம், சமூகம், வணிகம், திட்டம், வரலாறு, அறிவியல்) never break.
 *    - Bigger words (>= 6 Tamil letters) are partitioned into Tamil Asai (நேரசை / நிரையசை) syllables and
 *      merged so that NO segment (before a break, between breaks, or on the next line) ever has fewer than
 *      3 tailored Tamil letters (eliminating 2-letter next-line orphans like -கம், -பம், -றல், -யம், -கள்).
 * 6. Idempotency: Multiple runs will never inject duplicate soft hyphens or zero-width spaces.
 */

const UYIR = new Set([
  0x0b85, 0x0b86, 0x0b87, 0x0b88, 0x0b89, 0x0b8a,
  0x0b8e, 0x0b8f, 0x0b90, 0x0b92, 0x0b93, 0x0b94
]);

const CONSONANTS = new Set([
  0x0b95, 0x0b99, 0x0b9a, 0x0b9c, 0x0b9e, 0x0b9f,
  0x0ba3, 0x0ba4, 0x0ba8, 0x0ba9, 0x0baa, 0x0bae,
  0x0baf, 0x0bb0, 0x0bb1, 0x0bb2, 0x0bb3, 0x0bb4,
  0x0bb5, 0x0bb6, 0x0bb7, 0x0bb8, 0x0bb9
]);

const VOWEL_SIGNS = new Set([
  0x0bbe, 0x0bbf, 0x0bc0, 0x0bc1, 0x0bc2, 0x0bc6,
  0x0bc7, 0x0bc8, 0x0bca, 0x0bcb, 0x0bcc, 0x0bd7
]);

const U_OR_I_SIGNS = new Set([0x0bbf, 0x0bc1]); // -i (ி) or -u (ு) participle endings
const VIRAMA = 0x0bcd;
const AYTHAM = 0x0b83;
const SOFT_HYPHEN = '\u00AD';
const ZERO_WIDTH_SPACE = '\u200B';
const MIN_WORD_LETTERS = 6;

/**
 * Split text into tailored Tamil letters (Ezhuthukkal).
 */
function getTamilLetters(text) {
  const normalized = text.normalize('NFC');
  const letters = [];
  const chars = Array.from(normalized);
  let i = 0;

  while (i < chars.length) {
    const s = chars.slice(i).join('');
    // Handle atomic Grantha sequences (ksha, shri)
    if (s.startsWith('\u0B95\u0BCD\u0BB7')) {
      let len = 3;
      if (i + 3 < chars.length && (VOWEL_SIGNS.has(chars[i + 3].codePointAt(0)) || chars[i + 3].codePointAt(0) === VIRAMA)) {
        len = 4;
      }
      letters.push(chars.slice(i, i + len).join(''));
      i += len;
      continue;
    }
    if (s.startsWith('\u0BB8\u0BCD\u0BB0\u0BC0') || s.startsWith('\u0BB6\u0BCD\u0BB0\u0BC0')) {
      letters.push(chars.slice(i, i + 4).join(''));
      i += 4;
      continue;
    }

    const code = chars[i].codePointAt(0);
    if (UYIR.has(code) || code === AYTHAM) {
      letters.push(chars[i]);
      i++;
    } else if (CONSONANTS.has(code)) {
      let letter = chars[i];
      i++;
      if (i < chars.length) {
        const nextCode = chars[i].codePointAt(0);
        if (nextCode === VIRAMA || VOWEL_SIGNS.has(nextCode)) {
          letter += chars[i];
          i++;
        }
      }
      letters.push(letter);
    } else {
      letters.push(chars[i]);
      i++;
    }
  }
  return letters;
}

/**
 * Classify a tailored letter into its phonotactic role.
 */
function classifyLetter(letter) {
  if (letter === '\u0B83') return 'aytham';
  if (letter.endsWith('\u0BCD')) return 'mei';
  if (letter.startsWith('\u0B95\u0BCD\u0BB7') || letter.startsWith('\u0BB8\u0BCD\u0BB0\u0BC0') || letter.startsWith('\u0BB6\u0BCD\u0BB0\u0BC0')) {
    return 'atomic_grantha';
  }
  const firstCode = letter.codePointAt(0);
  if (UYIR.has(firstCode)) return 'uyir';
  if (CONSONANTS.has(firstCode)) return 'uyirmei';
  return 'other';
}

function isSyllableNucleus(cls) {
  return cls === 'uyir' || cls === 'uyirmei' || cls === 'atomic_grantha';
}

function isKurriyalUorI(syl) {
  if (syl.length !== 1) return false;
  const l = syl[0];
  return l.length === 2 && U_OR_I_SIGNS.has(l.codePointAt(1));
}

/**
 * Partition tailored Tamil letters into raw phonetic nuclei (1 vowel nucleus + trailing Mei/Aytham codas).
 */
function getRawSyllables(word) {
  const letters = getTamilLetters(word);
  if (letters.length === 0) return [];

  const rawSyllables = [];
  let current = [];

  for (let i = 0; i < letters.length; i++) {
    const letter = letters[i];
    const cls = classifyLetter(letter);
    if (isSyllableNucleus(cls)) {
      if (current.length > 0) {
        rawSyllables.push(current);
        current = [];
      }
      current.push(letter);
    } else {
      current.push(letter);
    }
  }
  if (current.length > 0) {
    rawSyllables.push(current);
  }
  return rawSyllables;
}

/**
 * Partition a Tamil word into canonical Tamil Asai (நேரசை / நிரையசை) segments where:
 * - Final segment has >= rightMin (default 3) tailored letters
 * - First segment has >= leftMin (default 3) tailored letters
 * - Internal segments have >= Math.min(leftMin, rightMin) tailored letters
 */
function getTamilSyllables(word, leftMin = 3, rightMin = 3) {
  const raw = getRawSyllables(word);
  const totalLetters = raw.reduce((acc, s) => acc + s.length, 0);
  const minSegLetters = Math.min(leftMin, rightMin);
  if (totalLetters < leftMin + rightMin || raw.length < 2) {
    return raw.length > 0 ? [raw.reduce((a, b) => a.concat(b), [])] : [];
  }
  if (minSegLetters <= 1) {
    return raw;
  }

  const asais = [];
  let i = 0;

  // Step 1: Word-initial CVC + -u/-i participle stem (e.g. கண்டு, இன்றி, சுதந், கன்னி)
  if (raw.length >= 3 && raw[0].length === 2 && isKurriyalUorI(raw[1])) {
    asais.push(raw[0].concat(raw[1]));
    i = 2;
  }

  // Step 2: Classical forward Nirai-asai grouping (any 1-letter open syllable joins with next syllable)
  while (i < raw.length) {
    if (raw[i].length === 1 && i + 1 < raw.length) {
      asais.push(raw[i].concat(raw[i + 1]));
      i += 2;
    } else if (raw[i].length === 1 && i === raw.length - 1 && asais.length > 0) {
      asais[asais.length - 1] = asais[asais.length - 1].concat(raw[i]);
      i += 1;
    } else {
      asais.push(raw[i]);
      i += 1;
    }
  }

  // Step 3: Never leave < rightMin (default 3) on the next line (Tail merge: prevents -கம், -பம், -றல், -யம், -கள்)
  while (asais.length >= 2 && asais[asais.length - 1].length < rightMin) {
    const last = asais.pop();
    asais[asais.length - 1] = asais[asais.length - 1].concat(last);
  }

  // Step 4: Never leave < leftMin (default 3) before the first break (Head merge: prevents 2-letter stubs)
  while (asais.length >= 2 && asais[0].length < leftMin) {
    const first = asais.shift();
    asais[0] = first.concat(asais[0]);
  }

  // Step 5: Merge any internal < minSegLetters segment into its neighbor (preferring open neighbor over closed Mei coda)
  let k = 1;
  while (k < asais.length - 1) {
    if (asais[k].length < minSegLetters) {
      const prevEndsMei = classifyLetter(asais[k - 1][asais[k - 1].length - 1]) === 'mei';
      if (!prevEndsMei) {
        asais[k - 1] = asais[k - 1].concat(asais[k]);
        asais.splice(k, 1);
      } else {
        asais[k + 1] = asais[k].concat(asais[k + 1]);
        asais.splice(k, 1);
      }
    } else {
      k++;
    }
  }

  return asais;
}

/**
 * Strip existing hyphenation / break characters from a Tamil word or string.
 */
function removeHyphens(text) {
  if (!text) return '';
  // 1. Remove soft hyphens, optional hyphens, and zero-width spaces
  let cleaned = text.replace(/[\u00AD\u001F\u200B]/g, '');
  // 2. Also remove ASCII hyphens '-' that sit strictly between two Tamil characters
  // (in case a user had visible hyphens inserted inside Tamil words)
  cleaned = cleaned.replace(/([\u0B80-\u0BFF])-+([\u0B80-\u0BFF])/g, '$1$2');
  // Run twice for adjacent 1-letter syllables like க-ழ-க
  cleaned = cleaned.replace(/([\u0B80-\u0BFF])-+([\u0B80-\u0BFF])/g, '$1$2');
  return cleaned;
}

/**
 * Hyphenate a single Tamil word:
 * - Short words (< leftMin + rightMin tailored Tamil letters, default 6: உலகம், சமூகம், திட்டம், அறிவியல்) are never broken.
 * - Bigger words (>= 6 tailored Tamil letters) break strictly at canonical Tamil Asai boundaries where
 *   every segment (left, internal, and next-line right) has at least 3 tailored Tamil letters by default.
 */
function hyphenateWord(word, leftMin = 3, rightMin = 3, delimiter = SOFT_HYPHEN, minWordLetters = null) {
  const cleanWord = removeHyphens(word.normalize('NFC'));
  const letters = getTamilLetters(cleanWord);
  const totalLetters = letters.length;
  const effectiveMinWord = minWordLetters !== null ? Math.max(minWordLetters, leftMin + rightMin) : Math.max(2, leftMin + rightMin);
  if (totalLetters < effectiveMinWord) return cleanWord;

  // Reject words containing ZWJ or ZWNJ to protect forced conjuncts
  if (cleanWord.includes('\u200C') || cleanWord.includes('\u200D')) {
    return cleanWord;
  }

  const segments = getTamilSyllables(cleanWord, leftMin, rightMin);
  if (segments.length < 2) return cleanWord;

  return segments.map(s => s.join('')).join(delimiter);
}

/**
 * Soft-hyphenate any text, preserving punctuation, whitespace, and non-Tamil runs.
 */
function hyphenateText(text, leftMin = 3, rightMin = 3, delimiter = SOFT_HYPHEN) {
  if (!text) return '';
  const cleaned = removeHyphens(text);
  return cleaned.replace(/[\u0B80-\u0BFF]+/g, (match) => {
    return hyphenateWord(match, leftMin, rightMin, delimiter);
  });
}

/**
 * Clean existing <w:softHyphen/> elements, U+00AD, and U+200B characters from Word OOXML,
 * merging adjacent <w:t> nodes that were split by <w:softHyphen/>.
 */
function removeOoxmlHyphens(ooxml) {
  if (!ooxml) return '';
  // 1. Repeatedly merge <w:t>A</w:t><w:softHyphen/><w:t>B</w:t> into <w:t>AB</w:t>
  let cleaned = ooxml;
  let prev;
  do {
    prev = cleaned;
    cleaned = cleaned.replace(/<\/w:t>\s*<w:softHyphen\s*\/>\s*<w:t(?:\s+[^>]*)?>/g, '');
  } while (cleaned !== prev);

  // 2. Remove any remaining standalone <w:softHyphen/> tags
  cleaned = cleaned.replace(/<w:softHyphen\s*\/>/g, '');

  // 3. Clean inside <w:t> tags (removes U+00AD, U+001F, U+200B, and mid-word Tamil '-')
  cleaned = cleaned.replace(/(<w:t(?:\s+[^>]*)?>)([\s\S]*?)(<\/w:t>)/g, (match, openTag, innerText, closeTag) => {
    return openTag + removeHyphens(innerText) + closeTag;
  });

  return cleaned;
}

/**
 * Process Word OOXML package string:
 * - If useVisualHyphen = true (default): splits <w:t> nodes with Word's native <w:softHyphen/> tag
 *   so hyphens are invisible mid-line and appear as '-' ONLY at the right margin when wrapping.
 * - If useVisualHyphen = false: inserts Unicode Zero-Width Space (\u200B) at syllable boundaries
 *   so long words wrap cleanly at margins WITHOUT showing any '-' glyph at all.
 */
function hyphenateOoxml(ooxml, leftMin = 3, rightMin = 3, useVisualHyphen = true) {
  if (!ooxml) return '';
  const cleanXml = removeOoxmlHyphens(ooxml);

  return cleanXml.replace(/(<w:t(?:\s+[^>]*)?>)([\s\S]*?)(<\/w:t>)/g, (match, openTag, innerText, closeTag) => {
    if (!/[\u0B80-\u0BFF]/.test(innerText)) {
      return match;
    }

    if (!useVisualHyphen) {
      // No visual hyphen mode: use Zero-Width Space (\u200B)
      const wrapped = hyphenateText(innerText, leftMin, rightMin, ZERO_WIDTH_SPACE);
      return `<w:t xml:space="preserve">${wrapped}</w:t>`;
    }

    // Visual hyphen at line-end mode: use native <w:softHyphen/>
    const hyphenated = hyphenateText(innerText, leftMin, rightMin, SOFT_HYPHEN);
    if (!hyphenated.includes(SOFT_HYPHEN)) {
      return openTag + hyphenated + closeTag;
    }
    const parts = hyphenated.split(SOFT_HYPHEN);
    return parts.map(part => `<w:t xml:space="preserve">${part}</w:t>`).join('<w:softHyphen/>');
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getTamilLetters,
    getRawSyllables,
    getTamilSyllables,
    classifyLetter,
    hyphenateWord,
    hyphenateText,
    removeHyphens,
    hyphenateOoxml,
    removeOoxmlHyphens,
    SOFT_HYPHEN,
    ZERO_WIDTH_SPACE,
    MIN_WORD_LETTERS
  };
}
