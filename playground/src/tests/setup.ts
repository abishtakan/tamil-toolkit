import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { init } from "tamil-toolkit/web";

let initialized = false;

export async function ensureToolkitInitialized() {
  if (initialized) return;
  const wasmUrl = new URL("../../../bindings/js-wasm/pkg-web/tamil_toolkit_bg.wasm", import.meta.url);
  const bytes = readFileSync(fileURLToPath(wasmUrl));
  await init({ module_or_path: bytes });
  initialized = true;
}
