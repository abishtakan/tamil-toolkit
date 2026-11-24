import { KeyboardLayout, initTamilEngine, isTamilEngineReady } from "./tamil-engine.js";
import { isWordHost, resetLiveTypingCache, runDirectLiveTypingTick } from "./word-adapter.js";

export interface LiveTypingState {
  active: boolean;
  layout: KeyboardLayout;
  font: string;
}

export interface LiveTypingStatus {
  message?: string;
  kind?: "info" | "success" | "error";
  converted?: boolean;
  pendingWord?: string;
  activeTamilWord?: string;
}

type Listener = (state: LiveTypingState, status?: LiveTypingStatus) => void;

let active = false;
let layout: KeyboardLayout = "phonetic-v1";
let font = "";
let timer: number | null = null;
let inFlight = false;
let suspended = false;
let lastActivityAt = 0;
const ACTIVE_POLL_MS = 100;
const IDLE_POLL_MS = 280;
const IDLE_THRESHOLD_MS = 2000;
const listeners = new Set<Listener>();

function emit(status?: LiveTypingStatus): void {
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
  layout?: KeyboardLayout;
  font?: string;
}): void {
  if (opts.layout) {
    layout = opts.layout;
    resetLiveTypingCache();
    lastActivityAt = Date.now();
  }
  if (opts.font !== undefined) font = opts.font;
  emit();
}

export function isLiveTypingActive(): boolean {
  return active;
}

export function setLiveTypingSuspended(value: boolean): void {
  suspended = value;
  if (!value && active) {
    lastActivityAt = Date.now();
  }
}

export function stopLiveTyping(): void {
  resetLiveTypingCache();
  if (!active && timer === null) return;
  active = false;
  if (timer !== null) {
    window.clearTimeout(timer);
    timer = null;
  }
  emit({ message: "Live Word Typing OFF.", kind: "info", pendingWord: "" });
}

function scheduleNextTick(): void {
  if (!active) return;
  const isRecentlyActive = Date.now() - lastActivityAt < IDLE_THRESHOLD_MS;
  const delay = isRecentlyActive ? ACTIVE_POLL_MS : IDLE_POLL_MS;
  timer = window.setTimeout(() => {
    timer = null;
    if (!active) return;
    if (inFlight || suspended || !isTamilEngineReady()) {
      scheduleNextTick();
      return;
    }
    inFlight = true;
    void runDirectLiveTypingTick(layout, font, () => active)
      .then((res) => {
        if (res.activeInput || res.converted) {
          lastActivityAt = Date.now();
        }
        if (res.unchanged) return;
        if (res.converted && res.unicode) {
          emit({
            message: `Live: ${res.original} → ${res.unicode}`,
            kind: "success",
            converted: true,
            pendingWord: "",
            activeTamilWord: res.activeTamilWord ?? "",
          });
        } else if (res.pendingWord !== undefined || res.activeTamilWord !== undefined) {
          emit({
            pendingWord: res.pendingWord ?? "",
            activeTamilWord: res.activeTamilWord ?? "",
          });
        }
      })
      .catch(() => {
        // Ignore transient Word busy state while typing
      })
      .finally(() => {
        inFlight = false;
        scheduleNextTick();
      });
  }, delay);
}

export async function startLiveTyping(): Promise<void> {
  await initTamilEngine();
  if (!isWordHost()) {
    emit({ message: "Open inside Microsoft Word to use Live Typing.", kind: "info" });
    return;
  }
  if (active) return;

  resetLiveTypingCache();
  active = true;
  lastActivityAt = Date.now();
  emit({
    message: `Live Typing ON (${layout}) — type directly on the Word page.`,
    kind: "success",
  });
  scheduleNextTick();
}

export async function toggleLiveTyping(): Promise<boolean> {
  if (active) {
    stopLiveTyping();
    return false;
  }
  await startLiveTyping();
  return active;
}
