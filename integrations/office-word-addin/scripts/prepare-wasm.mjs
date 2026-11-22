import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const addinDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(addinDir, "..", "..");
const wasmCrateDir = path.join(repoRoot, "bindings", "js-wasm");
const outDir = path.join(addinDir, "src", "wasm");
const wasmFile = path.join(outDir, "tamil_toolkit_bg.wasm");
const jsFile = path.join(outDir, "tamil_toolkit.js");

const force = process.argv.includes("--force");

if (!force && fs.existsSync(wasmFile) && fs.existsSync(jsFile)) {
  const sizeKb = (fs.statSync(wasmFile).size / 1024).toFixed(1);
  console.log(`[prepare-wasm] Using cached slim WASM (${sizeKb} KiB): ${wasmFile}`);
  process.exit(0);
}

console.log("[prepare-wasm] Building slim Apache-2.0 default-profile WASM for Word Add-in...");

const cargoBin = path.join(process.env.USERPROFILE || process.env.HOME || "", ".cargo", "bin");
const env = {
  ...process.env,
  PATH: cargoBin ? `${cargoBin}${path.delimiter}${process.env.PATH || ""}` : process.env.PATH,
};

const isWin = process.platform === "win32";
const wasmPackCmd = isWin ? "pnpm.cmd" : "pnpm";
const args = [
  "--filter",
  "tamil-toolkit",
  "exec",
  "wasm-pack",
  "build",
  wasmCrateDir,
  "--target",
  "web",
  "--release",
  "--out-name",
  "tamil_toolkit",
  "--out-dir",
  outDir,
];

const res = spawnSync(wasmPackCmd, args, {
  cwd: repoRoot,
  env,
  stdio: "inherit",
  shell: isWin,
});

if (res.error) {
  console.error("[prepare-wasm] Failed to invoke wasm-pack:", res.error.message);
  process.exit(1);
}
if (res.status !== 0) {
  process.exit(res.status ?? 1);
}

// Clean up wasm-pack's generated .gitignore so git/vite handles it cleanly
const genGitignore = path.join(outDir, ".gitignore");
if (fs.existsSync(genGitignore)) {
  fs.unlinkSync(genGitignore);
}

const sizeKb = (fs.statSync(wasmFile).size / 1024).toFixed(1);
console.log(`[prepare-wasm] Built slim WASM (${sizeKb} KiB) -> ${outDir}`);
