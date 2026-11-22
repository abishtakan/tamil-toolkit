import { getBrowserApi } from "../shared/browser-api.js";

const api = getBrowserApi();

if (api?.runtime?.onMessage) {
  api.runtime.onMessage.addListener((msg: any, _sender: any, sendResponse: (res: unknown) => void) => {
    if (msg?.type !== "OFFSCREEN_COPY_TEXT") return false;
    const text = typeof msg.text === "string" ? msg.text : "";
    void (async () => {
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
          sendResponse({ ok: true });
          return;
        }
      } catch {
        // Fall through to execCommand fallback inside offscreen document
      }
      try {
        const ta = document.getElementById("clipboard-buffer") as HTMLTextAreaElement | null;
        if (!ta) {
          sendResponse({ ok: false, error: "Clipboard buffer missing." });
          return;
        }
        ta.value = text;
        ta.select();
        const ok = document.execCommand("copy");
        ta.value = "";
        sendResponse({ ok });
      } catch (err) {
        sendResponse({ ok: false, error: err instanceof Error ? err.message : String(err) });
      }
    })();
    return true;
  });
}
