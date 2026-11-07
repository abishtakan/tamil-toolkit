/**
 * Tamil Soft-Hyphenation Core Engine (Standalone ECMAScript)
 *
 * Implements phonotactically verified syllabic hyphenation for Microsoft Word (Office.js).
 * Uses Word's native <w:softHyphen/> OOXML element so hyphens are 100% invisible inside lines
 * and ONLY appear at the end of a line when Word breaks the line.
 *
 * Rules:
 * 1. Independent vowels (Uyir \u0B85-\u0B94) act as syllable nuclei.
 * 2. Consonants with vowel markers (Uyirmei) or inherent-a consonants form syllable nuclei.
 * 3. Pure consonants with pulli/virama (Mei \u0BCD) and Aytham (\u0B83) bind as codas to the preceding nucleus;
 *    a segment NEVER begins with a pure consonant or Aytham.
 * 4. Grantha conjuncts (Ksha \u0B95\u0BCD\u0BB7, Shri \u0BB8\u0BCD\u0BB0\u0BC0 / \u0BB6\u0BCD\u0BB0\u0BC0) are treated atomically.
 * 5. Minimum margins (leftMin=2, rightMin=2) protect short initial and final letter runs.
 * 6. Idempotency: Multiple runs will never inject duplicate soft hyphens.
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

const VIRAMA = 0x0bcd;
const AYTHAM = 0x0b83;
const SOFT_HYPHEN = '\u00AD';

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

/**
 * Hyphenate a single Tamil word respecting left and right letter margins.
 */
function hyphenateWord(word, leftMin = 2, rightMin = 2, delimiter = SOFT_HYPHEN) {
  const cleanWord = word.normalize('NFC').replace(/[\u00AD\u001F]/g, '');
  const letters = getTamilLetters(cleanWord);
  const total = letters.length;
  if (total < (leftMin + rightMin)) return cleanWord;

  const classes = letters.map(classifyLetter);

  const hasNucleusBefore = new Array(total).fill(false);
  let running = false;
  for (let i = 0; i < total; i++) {
    if (isSyllableNucleus(classes[i])) running = true;
    hasNucleusBefore[i] = running;
  }

  const hasNucleusAfter = new Array(total).fill(false);
  running = false;
  for (let i = total - 1; i >= 0; i--) {
    if (isSyllableNucleus(classes[i])) running = true;
    hasNucleusAfter[i] = running;
  }

  let result = '';
  for (let i = 0; i < total; i++) {
    result += letters[i];
    if (i < total - 1) {
      const leftCount = i + 1;
      const rightCount = total - leftCount;
      if (leftCount < leftMin || rightCount < rightMin) continue;
      if (!hasNucleusBefore[i] || !hasNucleusAfter[i + 1]) continue;

      const nextClass = classes[i + 1];
      if (nextClass === 'mei' || nextClass === 'aytham') continue;
      if (!isSyllableNucleus(nextClass)) continue;

      // Joiner check: neither curr nor next letter can be adjacent to ZWJ or ZWNJ
      if (letters[i].includes('\u200C') || letters[i].includes('\u200D') ||
          letters[i + 1].includes('\u200C') || letters[i + 1].includes('\u200D')) {
        continue;
      }

      result += delimiter;
    }
  }
  return result;
}

/**
 * Soft-hyphenate any text, preserving punctuation, whitespace, and non-Tamil runs.
 */
function hyphenateText(text, leftMin = 2, rightMin = 2) {
  if (!text) return '';
  return text.replace(/[\u0B80-\u0BFF\u00AD\u001F]+/g, (match) => {
    return hyphenateWord(match, leftMin, rightMin, SOFT_HYPHEN);
  });
}

/**
 * Remove all soft hyphens from plain text.
 */
function removeHyphens(text) {
  if (!text) return '';
  return text.replace(/[\u00AD\u001F]/g, '');
}

/**
 * Clean existing <w:softHyphen/> elements and U+00AD characters from Word OOXML,
 * merging adjacent <w:t> nodes that were split by <w:softHyphen/>.
 */
function removeOoxmlHyphens(ooxml) {
  if (!ooxml) return '';
  // 1. Merge <w:t>A</w:t><w:softHyphen/><w:t>B</w:t> into <w:t>AB</w:t>
  let cleaned = ooxml.replace(/<\/w:t>\s*<w:softHyphen\s*\/>\s*<w:t(?:\s+[^>]*)?>/g, '');
  // 2. Remove any remaining standalone <w:softHyphen/> tags
  cleaned = cleaned.replace(/<w:softHyphen\s*\/>/g, '');
  // 3. Remove any literal U+00AD or U+001F inside <w:t> tags
  cleaned = cleaned.replace(/[\u00AD\u001F]/g, '');
  return cleaned;
}

/**
 * Process Word OOXML package string:
 * Replaces Tamil words inside <w:t> elements with <w:t>part1</w:t><w:softHyphen/><w:t>part2</w:t>
 * so Microsoft Word uses its native <w:softHyphen/> layout tag (invisible mid-line, breaks only at line end).
 */
function hyphenateOoxml(ooxml, leftMin = 2, rightMin = 2) {
  if (!ooxml) return '';
  // First normalize/clean any pre-existing soft hyphens to guarantee strict idempotency
  const cleanXml = removeOoxmlHyphens(ooxml);

  return cleanXml.replace(/(<w:t(?:\s+[^>]*)?>)([\s\S]*?)(<\/w:t>)/g, (match, openTag, innerText, closeTag) => {
    if (!/[\u0B80-\u0BFF]/.test(innerText)) {
      return match;
    }
    const hyphenated = hyphenateText(innerText, leftMin, rightMin);
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
    classifyLetter,
    hyphenateWord,
    hyphenateText,
    removeHyphens,
    hyphenateOoxml,
    removeOoxmlHyphens,
    SOFT_HYPHEN
  };
}
