/* global Office, Word, hyphenateOoxml, removeOoxmlHyphens */

Office.onReady(() => {
  // Office is ready
});

/**
 * Native Word Ribbon Command: Hyphenate Selection
 * Uses Word's native OOXML <w:softHyphen/> element so hyphens remain 100% invisible
 * inside lines and only display at the right margin when a line breaks.
 */
async function hyphenateSelectionCommand(event) {
  try {
    await Word.run(async (context) => {
      const selection = context.document.getSelection();
      selection.load("text");
      await context.sync();

      // Determine target range: selection if non-empty, otherwise active paragraph
      let targetRange = selection;
      if (!selection.text || selection.text.trim().length === 0) {
        targetRange = selection.paragraphs.getFirst();
      }

      const ooxmlResult = targetRange.getOoxml();
      await context.sync();

      if (ooxmlResult && ooxmlResult.value) {
        const updatedOoxml = hyphenateOoxml(ooxmlResult.value, 2, 2);
        if (updatedOoxml !== ooxmlResult.value) {
          targetRange.insertOoxml(updatedOoxml, Word.InsertLocation.replace);
          await context.sync();
        }
      }
    });
  } catch (error) {
    console.error("Tamil Hyphenation (Selection) Error:", error);
  } finally {
    event.completed();
  }
}

/**
 * Native Word Ribbon Command: Hyphenate Entire Document
 * Processes the document body OOXML using native <w:softHyphen/> elements.
 */
async function hyphenateDocumentCommand(event) {
  try {
    await Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load("text");
      await context.sync();

      const ooxmlResults = [];
      for (let i = 0; i < paragraphs.items.length; i++) {
        const para = paragraphs.items[i];
        if (para.text && /[\u0B80-\u0BFF]/.test(para.text)) {
          ooxmlResults.push({
            para,
            ooxml: para.getOoxml()
          });
        }
      }
      await context.sync();

      for (let i = 0; i < ooxmlResults.length; i++) {
        const { para, ooxml } = ooxmlResults[i];
        if (ooxml && ooxml.value) {
          const updatedOoxml = hyphenateOoxml(ooxml.value, 2, 2);
          if (updatedOoxml !== ooxml.value) {
            para.insertOoxml(updatedOoxml, Word.InsertLocation.replace);
          }
        }
      }
      await context.sync();
    });
  } catch (error) {
    console.error("Tamil Hyphenation (Document) Error:", error);
  } finally {
    event.completed();
  }
}

/**
 * Native Word Ribbon Command: Remove Hyphens
 * Strips all <w:softHyphen/> tags and U+00AD characters from the selection or document.
 */
async function removeHyphensCommand(event) {
  try {
    await Word.run(async (context) => {
      const selection = context.document.getSelection();
      selection.load("text");
      await context.sync();

      if (selection.text && selection.text.trim().length > 0) {
        const ooxmlResult = selection.getOoxml();
        await context.sync();

        if (ooxmlResult && ooxmlResult.value) {
          const cleanedOoxml = removeOoxmlHyphens(ooxmlResult.value);
          if (cleanedOoxml !== ooxmlResult.value) {
            selection.insertOoxml(cleanedOoxml, Word.InsertLocation.replace);
            await context.sync();
          }
        }
      } else {
        const paragraphs = context.document.body.paragraphs;
        paragraphs.load("text");
        await context.sync();

        const ooxmlResults = [];
        for (let i = 0; i < paragraphs.items.length; i++) {
          const para = paragraphs.items[i];
          if (para.text && para.text.trim().length > 0) {
            ooxmlResults.push({
              para,
              ooxml: para.getOoxml()
            });
          }
        }
        await context.sync();

        for (let i = 0; i < ooxmlResults.length; i++) {
          const { para, ooxml } = ooxmlResults[i];
          if (ooxml && ooxml.value) {
            const cleanedOoxml = removeOoxmlHyphens(ooxml.value);
            if (cleanedOoxml !== ooxml.value) {
              para.insertOoxml(cleanedOoxml, Word.InsertLocation.replace);
            }
          }
        }
        await context.sync();
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
Office.actions.associate("removeHyphensCommand", removeHyphensCommand);
