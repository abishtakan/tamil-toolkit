/* global Office, Word, hyphenateText, removeHyphens */

Office.onReady(() => {
  // Office is ready
});

/**
 * Native Word Ribbon Command: Hyphenate Selection
 * Directly inserts soft-hyphens into the selected text (or active paragraph).
 */
async function hyphenateSelectionCommand(event) {
  try {
    await Word.run(async (context) => {
      const selection = context.document.getSelection();
      selection.load("text");
      await context.sync();

      if (!selection.text || selection.text.trim().length === 0) {
        // Fallback: If cursor is just placed without dragging a selection,
        // target the active paragraph at the cursor position
        const currentParagraph = selection.paragraphs.getFirst();
        currentParagraph.load("text");
        await context.sync();

        if (currentParagraph.text && currentParagraph.text.trim().length > 0) {
          const hyphenated = hyphenateText(currentParagraph.text, 2, 2);
          if (hyphenated !== currentParagraph.text) {
            currentParagraph.insertText(hyphenated, Word.InsertLocation.replace);
            await context.sync();
          }
        }
        return;
      }

      const hyphenated = hyphenateText(selection.text, 2, 2);
      if (hyphenated !== selection.text) {
        selection.insertText(hyphenated, Word.InsertLocation.replace);
        await context.sync();
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
 * Processes all body paragraphs in the active Word document.
 */
async function hyphenateDocumentCommand(event) {
  try {
    await Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load("text");
      await context.sync();

      for (let i = 0; i < paragraphs.items.length; i++) {
        const para = paragraphs.items[i];
        if (para.text && para.text.trim().length > 0) {
          const hyphenated = hyphenateText(para.text, 2, 2);
          if (hyphenated !== para.text) {
            para.insertText(hyphenated, Word.InsertLocation.replace);
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
 * Strips all soft-hyphens from the selection (or entire document if nothing selected).
 */
async function removeHyphensCommand(event) {
  try {
    await Word.run(async (context) => {
      const selection = context.document.getSelection();
      selection.load("text");
      await context.sync();

      if (selection.text && selection.text.trim().length > 0) {
        const cleaned = removeHyphens(selection.text);
        if (cleaned !== selection.text) {
          selection.insertText(cleaned, Word.InsertLocation.replace);
          await context.sync();
        }
      } else {
        // Strip from entire document
        const paragraphs = context.document.body.paragraphs;
        paragraphs.load("text");
        await context.sync();

        for (let i = 0; i < paragraphs.items.length; i++) {
          const para = paragraphs.items[i];
          if (para.text && para.text.includes("\u00AD")) {
            const cleaned = removeHyphens(para.text);
            para.insertText(cleaned, Word.InsertLocation.replace);
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
