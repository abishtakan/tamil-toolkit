import { init } from "tamil-toolkit/web";
import * as tt from "tamil-toolkit/web";

export interface EngineStatus {
  isReady: boolean;
  isLoading: boolean;
  error: Error | null;
}

let initPromise: Promise<void> | null = null;
let isInitialized = false;

export async function initializeEngine(): Promise<void> {
  if (isInitialized) return;
  if (!initPromise) {
    initPromise = (async () => {
      try {
        await init();
        isInitialized = true;
      } catch (err) {
        initPromise = null;
        throw err;
      }
    })();
  }
  return initPromise;
}

export function isEngineReady(): boolean {
  return isInitialized;
}

export { tt };
