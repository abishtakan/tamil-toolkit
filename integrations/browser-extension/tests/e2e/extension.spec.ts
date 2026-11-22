import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const root = path.resolve(import.meta.dirname, "..", "..");
const distDir = path.join(root, "dist");

function readManifest(target: "chrome" | "firefox"): Record<string, any> {
  return JSON.parse(fs.readFileSync(path.join(distDir, target, "manifest.json"), "utf8"));
}

describe("Built extension bundles & E2E smoke verification", () => {
  it("Chrome & Firefox dist bundles contain valid MV3 manifests, single slim WASM, fonts, icons, and licenses", () => {
    for (const target of ["chrome", "firefox"] as const) {
      const targetDir = path.join(distDir, target);
      expect(fs.existsSync(path.join(targetDir, "manifest.json"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "background.js"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "content.js"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "panel.html"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "popup.html"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "LICENSE"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "NOTICE"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "fonts", "OFL-NOTO-TAMIL.txt"))).toBe(true);
      expect(fs.existsSync(path.join(targetDir, "icons", "icon-128.png"))).toBe(true);

      const assetsDir = path.join(targetDir, "assets");
      const wasmFiles = fs.readdirSync(assetsDir).filter((f) => f.endsWith(".wasm"));
      expect(wasmFiles).toHaveLength(1);

      const manifest = readManifest(target);
      expect(manifest.manifest_version).toBe(3);
      expect("host_permissions" in manifest).toBe(false);
      expect(manifest.content_security_policy.extension_pages).toContain("'wasm-unsafe-eval'");
    }
  });

  it("Packaged store ZIP archives stay under the 2 MiB budget (SC-005)", () => {
    const maxBytes = 2 * 1024 * 1024;
    for (const zipName of ["tamil-toolkit-chrome.zip", "tamil-toolkit-firefox.zip", "tamil-toolkit-firefox-source.zip"]) {
      const zipPath = path.join(distDir, zipName);
      expect(fs.existsSync(zipPath)).toBe(true);
      expect(fs.statSync(zipPath).size).toBeLessThan(maxBytes);
    }
  });
});
