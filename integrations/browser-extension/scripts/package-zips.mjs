import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const extDir = path.resolve(__dirname, "..");
const distDir = path.join(extDir, "dist");
const MAX_ZIP_BYTES = 2 * 1024 * 1024; // 2 MiB strict budget (SC-005)

function createZip(sourceDir, outZip) {
  if (fs.existsSync(outZip)) fs.unlinkSync(outZip);
  const py = [
    "import pathlib, zipfile, sys",
    "src = pathlib.Path(sys.argv[1])",
    "out = pathlib.Path(sys.argv[2])",
    "with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:",
    "    for p in sorted(src.rglob('*')):",
    "        if p.is_file():",
    "            zf.write(p, p.relative_to(src).as_posix())",
  ].join("\n");
  const res = spawnSync("uv", ["run", "--locked", "python", "-", sourceDir, outZip], {
    cwd: path.resolve(extDir, "..", ".."),
    input: py,
    encoding: "utf8",
    stdio: ["pipe", "inherit", "inherit"],
    shell: false,
  });
  if (res.status !== 0) {
    throw new Error(`Failed to create archive ${outZip}`);
  }
  return fs.statSync(outZip).size;
}

const chromeDir = path.join(distDir, "chrome");
const firefoxDir = path.join(distDir, "firefox");
if (!fs.existsSync(chromeDir) || !fs.existsSync(firefoxDir)) {
  console.error("[package-zips] Run `pnpm --filter tamil-browser-extension build` before packaging.");
  process.exit(1);
}

const chromeZip = path.join(distDir, "tamil-toolkit-chrome.zip");
const firefoxZip = path.join(distDir, "tamil-toolkit-firefox.zip");

const chromeBytes = createZip(chromeDir, chromeZip);
const firefoxBytes = createZip(firefoxDir, firefoxZip);

console.log(`[package-zips] Chrome ZIP:  ${(chromeBytes / 1024).toFixed(1)} KiB -> ${chromeZip}`);
console.log(`[package-zips] Firefox ZIP: ${(firefoxBytes / 1024).toFixed(1)} KiB -> ${firefoxZip}`);

if (chromeBytes > MAX_ZIP_BYTES || firefoxBytes > MAX_ZIP_BYTES) {
  console.error("[package-zips] ERROR: Extension package exceeded the 2 MiB size limit!");
  process.exit(1);
}

// Create reproducible AMO source archive with Linux rebuild instructions
const amoStageDir = path.join(distDir, "_amo_source_stage");
fs.rmSync(amoStageDir, { recursive: true, force: true });
fs.mkdirSync(amoStageDir, { recursive: true });
for (const rel of ["package.json", "tsconfig.json", "vite.config.ts", "panel.html", "popup.html", "offscreen.html", "scripts", "src"]) {
  const srcPath = path.join(extDir, rel);
  if (fs.existsSync(srcPath)) {
    fs.cpSync(srcPath, path.join(amoStageDir, rel), {
      recursive: true,
      filter: (p) => !p.includes(`${path.sep}wasm`),
    });
  }
}
fs.writeFileSync(
  path.join(amoStageDir, "BUILD_AMO.sh"),
  `#!/usr/bin/env bash
set -euo pipefail
# Reproducible Firefox AMO build from tamil-toolkit repository root:
#   pnpm install --frozen-lockfile
#   pnpm --filter tamil-browser-extension build
# Output: integrations/browser-extension/dist/firefox/
pnpm --filter tamil-browser-extension build:firefox
`,
  "utf8"
);

const amoZip = path.join(distDir, "tamil-toolkit-firefox-source.zip");
const amoBytes = createZip(amoStageDir, amoZip);
fs.rmSync(amoStageDir, { recursive: true, force: true });
console.log(`[package-zips] AMO source:  ${(amoBytes / 1024).toFixed(1)} KiB -> ${amoZip}`);
