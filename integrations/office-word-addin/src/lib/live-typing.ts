import { LegacyEncoding, initTamilEngine, isTamilEngineReady } from "./tamil-engine.js";
import { isWordHost, runDirectLiveTypingTick } from "./word-adapter.js";

export interface LiveTypingState {
  active: boolean;
  layout: Exclude<LegacyEncoding, "auto">;
  font: string;
}

type Listener = (state: LiveTypingState, status?: { message: string; kind: "info" | "success" | "error" }) => void;

let active = false;
let layout: Exclude<LegacyEncoding, "auto"> = "bamini";
let font = "Nirmala UI";
let timer: number | null = null;
let inFlight = false;
const listeners = new Set<Listener>();

function emit(status?: { message: string; kind: "info" | "success" | "error" }): void {
  const snapshot: LiveTypingState = { active, layout, font };
  for (const fn of listeners) {
    fn(snapshot, status);
  }
}

export function subscribeLiveTyping(fn: Listener): () => void {
  listeners.add(fn);
  fn({ active, layout, font });
  return () => listeners.delete(fn);
}

export function configureLiveTyping(opts: {
  layout?: Exclude<LegacyEncoding, "auto">;
  font?: string;
}): void {
  if (opts.layout) layout = opts.layout;
  if (opts.font !== undefined) font = opts.font;
  emit();
}

export function isLiveTypingActive(): boolean {
  return active;
}

export function stopLiveTyping(): void {
  if (!active && timer === null) return;
  active = false;
  if (timer !== null) {
    window.clearInterval(timer);
    timer = null;
  }
  emit({ message: "Live Bamini Typing OFF.", kind: "info" });
}

export async function startLiveTyping(): Promise<void> {
  await initTamilEngine();
  if (!isWordHost()) {
    emit({ message: "Open inside Microsoft Word to use Live Typing.", kind: "info" });
    return;
  }
  if (active) return;

  active = true;
  emit({
    message: `Live Typing ON (${layout.toUpperCase()}) — type directly on the Word page.`,
    kind: "success",
  });

  timer = window.setInterval(() => {
    if (!active || inFlight || !isTamilEngineReady()) return;
    inFlight = true;
    void runDirectLiveTypingTick(layout, font, () => active)
      .then((res) => {
        if (res.converted && res.unicode) {
          emit({ message: `Live: ${res.original} → ${res.unicode}`, kind: "success" });
        }
      })
      .catch(() => {
        // Ignore transient Word busy state while typing
      })
      .finally(() => {
        inFlight = false;
      });
  }, 120);
}

export async function toggleLiveTyping(): Promise<boolean> {
  if (active) {
    stopLiveTyping();
    return false;
  }
  await startLiveTyping();
  return active;
}
