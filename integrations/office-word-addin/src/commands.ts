import { toggleLiveTyping } from "./lib/live-typing.js";
import {
  buildTamilDateStamp,
  initTamilEngine,
  numberToTamilWords,
} from "./lib/tamil-engine.js";
import {
  insertAtCursor,
  readTargetText,
  runHyphenation,
  runLegacyToUnicode,
  runRemoveHyphens,
  runRepairTamil,
  runSortSelectionParagraphs,
} from "./lib/word-adapter.js";

export type RibbonStatusSink = (message: string, kind: "info" | "success" | "error") => void;

let registered = false;

export function registerRibbonCommands(onStatus?: RibbonStatusSink): void {
  if (registered) return;
  if (typeof Office === "undefined" || !Office.actions?.associate) return;
  registered = true;

  const notify: RibbonStatusSink = (msg, kind) => {
    if (onStatus) {
      onStatus(msg, kind);
    } else if (kind === "error") {
      console.error("[Tamil Toolkit Ribbon]", msg);
    }
  };

  async function withEngine(
    event: Office.AddinCommands.Event,
    fn: () => Promise<void>
  ): Promise<void> {
    try {
      await initTamilEngine();
      await fn();
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      notify(`Ribbon error: ${msg}`, "error");
    } finally {
      event.completed();
    }
  }

  Office.actions.associate("toggleLiveTypingCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const isOn = await toggleLiveTyping();
      notify(
        isOn
          ? "Live Bamini Typing ON — click on your Word page and type."
          : "Live Bamini Typing OFF.",
        isOn ? "success" : "info"
      );
    });
  });

  Office.actions.associate("autoConvertUnicodeCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = await readTargetText("selection");
      const scope = sel.trim().length > 0 ? "selection" : "paragraph";
      const summary = await runLegacyToUnicode(scope, "auto", "Nirmala UI");
      notify(
        `Converted ${summary.rangesModified} ${scope} [${summary.detectedEncoding}] → Unicode.`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  Office.actions.associate("convertBaminiParagraphCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = await readTargetText("selection");
      const scope = sel.trim().length > 0 ? "selection" : "paragraph";
      const summary = await runLegacyToUnicode(scope, "bamini", "Nirmala UI");
      notify(
        `Converted Bamini ${scope} → Unicode (${summary.rangesModified} updated).`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  Office.actions.associate("repairTamilCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = await readTargetText("selection");
      const scope = sel.trim().length > 0 ? "selection" : "paragraph";
      const summary = await runRepairTamil(scope, {
        fixDuplicatePulli: true,
        reorderVisualVowels: true,
        stripZeroWidth: false,
        stripSoftHyphens: false,
      });
      notify(
        `Repaired ${summary.rangesModified} ${scope} (${summary.details || "NFC clean"}).`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  Office.actions.associate("sortAkaraVarisaiCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const res = await runSortSelectionParagraphs({
        descending: false,
        profile: "agara-v1",
        ignoreLeadingNumbers: false,
      });
      notify(
        res.sortedCount >= 2
          ? `Sorted ${res.sortedCount} paragraphs (Akara Varisai).`
          : "Select at least 2 paragraphs to sort.",
        res.sortedCount >= 2 ? "success" : "info"
      );
    });
  });

  Office.actions.associate("insertTamilDateCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const now = new Date();
      const stamp = buildTamilDateStamp(now.getFullYear(), now.getMonth() + 1, now.getDate(), {
        profile: "thirukanitham",
        region: "TN",
        includePanchangam: false,
      });
      await insertAtCursor(stamp.formatted_formal, true, "Nirmala UI");
      notify("Inserted formal Tamil date header.", "success");
    });
  });

  Office.actions.associate("numberToWordsCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = (await readTargetText("selection")).trim();
      if (!sel) {
        notify("Select a number first to convert to Tamil words.", "info");
        return;
      }
      const mode = sel.includes(".") ? "decimal" : "cardinal";
      const words = numberToTamilWords(sel, mode, { locale: "TN" });
      await insertAtCursor(words, true, "Nirmala UI");
      notify(`Converted ${sel} to Tamil words.`, "success");
    });
  });

  Office.actions.associate("hyphenateSelectionCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = await readTargetText("selection");
      const scope = sel.trim().length > 0 ? "selection" : "paragraph";
      const summary = await runHyphenation(scope, {
        leftMin: 3,
        rightMin: 3,
        useNativeSoftHyphen: true,
        toggle: false,
      });
      notify(`Soft-hyphenated ${summary.rangesModified}/${summary.rangesProcessed} range(s).`, "success");
    });
  });

  Office.actions.associate("hyphenateDocumentCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const summary = await runHyphenation("document", {
        leftMin: 3,
        rightMin: 3,
        useNativeSoftHyphen: true,
        toggle: false,
      });
      notify(
        `Soft-hyphenated ${summary.rangesModified}/${summary.rangesProcessed} paragraph(s).`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  Office.actions.associate("wrapWithoutHyphenCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = await readTargetText("selection");
      const scope = sel.trim().length > 0 ? "selection" : "document";
      const summary = await runHyphenation(scope, {
        leftMin: 3,
        rightMin: 3,
        useNativeSoftHyphen: false,
        toggle: false,
      });
      notify(`Applied invisible syllable wrap to ${summary.rangesModified} range(s) (no '-' shown).`, "success");
    });
  });

  Office.actions.associate("removeHyphensCommand", (event: Office.AddinCommands.Event) => {
    void withEngine(event, async () => {
      const sel = await readTargetText("selection");
      const scope = sel.trim().length > 0 ? "selection" : "document";
      const summary = await runRemoveHyphens(scope);
      notify(
        `Removed Tamil hyphenation from ${summary.rangesModified} ${scope === "selection" ? "selection" : "paragraph(s)"} (manual '-' preserved).`,
        "success"
      );
    });
  });
}

// Auto-register when loaded standalone via commands.html
if (typeof Office !== "undefined" && typeof Office.onReady === "function") {
  Office.onReady(() => {
    registerRibbonCommands();
    void initTamilEngine().catch((err) => console.error("WASM init failed:", err));
  });
}
