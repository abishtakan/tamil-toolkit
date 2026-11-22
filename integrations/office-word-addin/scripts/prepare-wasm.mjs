import path from "node:path";
import { fileURLToPath } from "node:url";
import { prepareSlimWasm } from "../../shared/prepare-slim-wasm.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const addinDir = path.resolve(__dirname, "..");
const outDir = path.join(addinDir, "src", "wasm");
const force = process.argv.includes("--force");

prepareSlimWasm({
  outDir,
  label: "Word Add-in",
  force,
});
