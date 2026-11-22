import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { writeManifest } from "./build-manifests.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const extDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(extDir, "..", "..");

const target = process.argv[2];
if (target !== "chrome" && target !== "firefox") {
  console.error("Usage: node scripts/build-extension.mjs <chrome|firefox>");
  process.exit(1);
}

const isWin = process.platform === "win32";
const pnpmCmd = isWin ? "pnpm.cmd" : "pnpm";

function runVite(entryMode) {
  const res = spawnSync(pnpmCmd, ["exec", "vite", "build"], {
    cwd: extDir,
    env: {
      ...process.env,
      BROWSER_TARGET: target,
      BUILD_ENTRY: entryMode,
    },
    stdio: "inherit",
    shell: isWin,
  });
  if (res.status !== 0) {
    process.exit(res.status ?? 1);
  }
}

runVite("pages");
runVite("background");
runVite("content");

const outDir = path.join(extDir, "dist", target);

// Copy static icons, fonts, and license notices into dist/<target>
fs.cpSync(path.join(extDir, "src", "assets", "icons"), path.join(outDir, "icons"), { recursive: true });
fs.cpSync(path.join(extDir, "src", "assets", "fonts"), path.join(outDir, "fonts"), { recursive: true });

for (const noticeFile of ["LICENSE", "NOTICE"]) {
  const srcPath = path.join(repoRoot, noticeFile);
  if (fs.existsSync(srcPath)) {
    fs.copyFileSync(srcPath, path.join(outDir, noticeFile));
  }
}

writeManifest(target);
console.log(`[build-extension] Built ${target} package -> ${outDir}`);
