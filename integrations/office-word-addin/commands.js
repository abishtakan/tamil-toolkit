/* global Office, Word, hyphenateOoxml, removeOoxmlHyphens, hyphenateText, removeHyphens, ZERO_WIDTH_SPACE */

Office.onReady(() => {
  // Office is ready
});

/**
 * Helper: Safely applies an OOXML transformation to a Word Range or Paragraph,
 * with a fallback to plain text replacement if OOXML fails on a host build.
 */
async function applyRangeTransform(context, range, useOoxmlTransform, plainTextFallbackFn) {
  try {
    const ooxmlResult = range.getOoxml();
    await context.sync();

    if (ooxmlResult && ooxmlResult.value) {
      const transformedXml = useOoxmlTransform(ooxmlResult.value);
      if (transformedXml !== ooxmlResult.value) {
        range.insertOoxml(transformedXml, Word.InsertLocation.replace);
        await context.sync();
      }
      return;
    }
  } catch (ooxmlError) {
    console.warn("OOXML transform fallback triggered:", ooxmlError);
  }

  // Fallback to direct text replacement
  range.load("text");
  await context.sync();
  if (range.text) {
    const updatedText = plainTextFallbackFn(range.text);
    if (updatedText !== range.text) {
      range.insertText(updatedText, Word.InsertLocation.replace);
      await context.sync();
    }
  }
}

/**
 * Helper: Resolves either the user's current selection (if non-empty)
 * or all paragraphs in the document body.
 */
async function getTargetRanges(context, defaultToAllParagraphs = true) {
  const selection = context.document.getSelection();
  selection.load("text");
  await context.sync();

  if (selection.text && selection.text.trim().length > 0) {
    return [selection];
  }

  if (!defaultToAllParagraphs) {
    const firstPara = selection.paragraphs.getFirst();
    return [firstPara.getRange(Word.RangeLocation.content)];
  }

  const paragraphs = context.document.body.paragraphs;
  paragraphs.load("text");
  await context.sync();

  const ranges = [];
  for (let i = 0; i < paragraphs.items.length; i++) {
    const para = paragraphs.items[i];
    if (para.text && para.text.trim().length > 0) {
      ranges.push(para.getRange(Word.RangeLocation.content));
    }
  }
  return ranges;
}

/**
 * 1. Hyphenate Selection (or Active Paragraph) WITH End-of-Line Hyphen (<w:softHyphen/>)
 */
async function hyphenateSelectionCommand(event) {
  try {
    await Word.run(async (context) => {
      const ranges = await getTargetRanges(context, false);
      for (const range of ranges) {
        await applyRangeTransform(
          context,
          range,
          (xml) => hyphenateOoxml(xml, 3, 3, true),
          (txt) => hyphenateText(txt, 3, 3)
        );
      }
    });
  } catch (error) {
    console.error("Tamil Hyphenation (Selection) Error:", error);
  } finally {
    event.completed();
  }
}

/**
 * 2. Hyphenate Entire Document WITH End-of-Line Hyphen (<w:softHyphen/>)
 */
async function hyphenateDocumentCommand(event) {
  try {
    await Word.run(async (context) => {
      const ranges = await getTargetRanges(context, true);
      for (const range of ranges) {
        await applyRangeTransform(
          context,
          range,
          (xml) => hyphenateOoxml(xml, 3, 3, true),
          (txt) => hyphenateText(txt, 3, 3)
        );
      }
    });
  } catch (error) {
    console.error("Tamil Hyphenation (Document) Error:", error);
  } finally {
    event.completed();
  }
}

/**
 * 3. Wrap Without Visual Hyphen (Zero-Width Space \u200B)
 * Wraps words at syllable boundaries at the end of lines WITHOUT showing any '-' symbol.
 */
async function wrapWithoutHyphenCommand(event) {
  try {
    await Word.run(async (context) => {
      const ranges = await getTargetRanges(context, true);
      for (const range of ranges) {
        await applyRangeTransform(
          context,
          range,
          (xml) => hyphenateOoxml(xml, 3, 3, false),
          (txt) => hyphenateText(txt, 3, 3, ZERO_WIDTH_SPACE)
        );
      }
    });
  } catch (error) {
    console.error("Tamil Wrap Without Hyphen Error:", error);
  } finally {
    event.completed();
  }
}

/**
 * 4. Remove / Disable All Hyphenation
 * Strips all <w:softHyphen/> tags, U+00AD, U+200B, and mid-word hyphens from selection or document.
 */
async function removeHyphensCommand(event) {
  try {
    await Word.run(async (context) => {
      const ranges = await getTargetRanges(context, true);
      for (const range of ranges) {
        await applyRangeTransform(
          context,
          range,
          (xml) => removeOoxmlHyphens(xml),
          (txt) => removeHyphens(txt)
        );
      }
    });
  } catch (error) {
    console.error("Tamil Hyphenation (Remove) Error:", error);
  } finally {
    event.completed();
  }
}

// Associate ribbon commands with their respective implementations
Office.actions.associate("hyphenateSelectionCommand", hyphenateSelectionCommand);
Office.actions.associate("hyphenateDocumentCommand", hyphenateDocumentCommand);
Office.actions.associate("wrapWithoutHyphenCommand", wrapWithoutHyphenCommand);
Office.actions.associate("removeHyphensCommand", removeHyphensCommand);
