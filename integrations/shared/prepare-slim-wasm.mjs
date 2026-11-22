import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..", "..");
const wasmCrateDir = path.join(repoRoot, "bindings", "js-wasm");

export function prepareSlimWasm({ outDir, label = "integration", force = false }) {
  if (!outDir) {
    throw new Error("prepareSlimWasm requires an outDir path.");
  }

  const resolvedOutDir = path.resolve(outDir);
  const wasmFile = path.join(resolvedOutDir, "tamil_toolkit_bg.wasm");
  const jsFile = path.join(resolvedOutDir, "tamil_toolkit.js");

  if (!force && fs.existsSync(wasmFile) && fs.existsSync(jsFile)) {
    const sizeKb = (fs.statSync(wasmFile).size / 1024).toFixed(1);
    console.log(`[prepare-wasm] Using cached slim WASM (${sizeKb} KiB): ${wasmFile}`);
    return { wasmFile, jsFile, cached: true };
  }

  fs.mkdirSync(resolvedOutDir, { recursive: true });
  console.log(`[prepare-wasm] Building slim Apache-2.0 default-profile WASM for ${label}...`);

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
    resolvedOutDir,
  ];

  const res = spawnSync(wasmPackCmd, args, {
    cwd: repoRoot,
    env,
    stdio: "inherit",
    shell: isWin,
  });

  if (res.error) {
    throw new Error(`Failed to invoke wasm-pack: ${res.error.message}`);
  }
  if (res.status !== 0) {
    process.exit(res.status ?? 1);
  }

  const genGitignore = path.join(resolvedOutDir, ".gitignore");
  if (fs.existsSync(genGitignore)) {
    fs.unlinkSync(genGitignore);
  }

  const sizeKb = (fs.statSync(wasmFile).size / 1024).toFixed(1);
  console.log(`[prepare-wasm] Built slim WASM (${sizeKb} KiB) -> ${resolvedOutDir}`);
  return { wasmFile, jsFile, cached: false };
}

// Allow direct CLI invocation: node integrations/shared/prepare-slim-wasm.mjs --out-dir <path> [--label <name>] [--force]
const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const outIdx = process.argv.indexOf("--out-dir");
  const labelIdx = process.argv.indexOf("--label");
  const outDir = outIdx >= 0 ? process.argv[outIdx + 1] : undefined;
  const label = labelIdx >= 0 ? process.argv[labelIdx + 1] : "integration";
  const force = process.argv.includes("--force");
  if (!outDir) {
    console.error("Usage: node prepare-slim-wasm.mjs --out-dir <path> [--label <name>] [--force]");
    process.exit(1);
  }
  prepareSlimWasm({ outDir, label, force });
}
