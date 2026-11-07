/* global Office, Word, hyphenateText */

Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    document.getElementById("btn-hyphenate-selection").onclick = hyphenateSelection;
    document.getElementById("btn-hyphenate-document").onclick = hyphenateDocument;
  }
});

function getMargins() {
  const leftMin = parseInt(document.getElementById("left-min").value, 10) || 3;
  const rightMin = parseInt(document.getElementById("right-min").value, 10) || 3;
  return { leftMin, rightMin };
}

function showStatus(message, isError = false) {
  const statusEl = document.getElementById("status-message");
  statusEl.className = "status-box " + (isError ? "error" : "success");
  statusEl.textContent = message;
  statusEl.style.display = "block";
}

/**
 * Hyphenates the current selection in Word.
 */
async function hyphenateSelection() {
  const { leftMin, rightMin } = getMargins();
  const btn = document.getElementById("btn-hyphenate-selection");
  btn.disabled = true;

  try {
    await Word.run(async (context) => {
      const selection = context.document.getSelection();
      selection.load("text");
      await context.sync();

      if (!selection.text || selection.text.trim().length === 0) {
        showStatus("தயவுசெய்து உரையைத் தேர்ந்தெடுக்கவும் (Please select some text).", true);
        return;
      }

      const originalText = selection.text;
      const hyphenated = hyphenateText(originalText, leftMin, rightMin);

      // Insert soft-hyphenated text replacing the selection
      selection.insertText(hyphenated, Word.InsertLocation.replace);
      await context.sync();

      showStatus("தேர்ந்தெடுத்த உரை வெற்றிகரமாக இணைக்கப்பட்டது (Selection successfully soft-hyphenated)!");
    });
  } catch (error) {
    console.error("Word Add-in Error:", error);
    showStatus("பிழை ஏற்பட்டது (An error occurred): " + error.message, true);
  } finally {
    btn.disabled = false;
  }
}

/**
 * Hyphenates all body paragraphs in the active Word document.
 */
async function hyphenateDocument() {
  const { leftMin, rightMin } = getMargins();
  const btn = document.getElementById("btn-hyphenate-document");
  btn.disabled = true;

  try {
    await Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load("items");
      await context.sync();

      let modifiedCount = 0;

      for (let i = 0; i < paragraphs.items.length; i++) {
        const para = paragraphs.items[i];
        para.load("text");
      }
      await context.sync();

      for (let i = 0; i < paragraphs.items.length; i++) {
        const para = paragraphs.items[i];
        if (para.text && /[\u0B80-\u0BFF]/.test(para.text)) {
          const hyphenated = hyphenateText(para.text, leftMin, rightMin);
          if (hyphenated !== para.text) {
            para.insertText(hyphenated, Word.InsertLocation.replace);
            modifiedCount++;
          }
        }
      }

      await context.sync();
      showStatus(`முழு ஆவணம் முடிந்தது: ${modifiedCount} பத்திகள் இணைக்கப்பட்டன (${modifiedCount} paragraphs hyphenated).`);
    });
  } catch (error) {
    console.error("Word Add-in Error:", error);
    showStatus("பிழை ஏற்பட்டது (An error occurred): " + error.message, true);
  } finally {
    btn.disabled = false;
  }
}
