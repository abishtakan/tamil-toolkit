import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const extDir = path.resolve(__dirname, "..");

export function createManifest(target, version = "0.1.0") {
  const isFirefox = target === "firefox";
  const basePermissions = [
    "activeTab",
    "scripting",
    "contextMenus",
    "storage",
    "clipboardWrite",
  ];

  const manifest = {
    manifest_version: 3,
    name: "Tamil Toolkit",
    short_name: "Tamil Toolkit",
    version,
    description:
      "Offline live Tamil typing (Phonetic, Tamil99, Anjal, Bamini), Tamil letter & word inspector, legacy font converter, and text repair.",
    icons: {
      "16": "icons/icon-16.png",
      "32": "icons/icon-32.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png",
    },
    action: {
      default_title: "Tamil Toolkit — Live Typing & Side Panel (Alt+Shift+L)",
      default_popup: "popup.html",
      default_icon: {
        "16": "icons/icon-16.png",
        "32": "icons/icon-32.png",
      },
    },
    permissions: isFirefox
      ? basePermissions
      : [...basePermissions, "sidePanel", "offscreen"],
    optional_host_permissions: ["https://*/*", "http://*/*"],
    commands: {
      "toggle-live-typing": {
        suggested_key: {
          default: "Alt+Shift+L",
          mac: "Alt+Shift+L",
        },
        description: "Toggle Live Tamil Typing on the active tab",
      },
    },
    content_security_policy: {
      extension_pages: "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'",
    },
    web_accessible_resources: [
      {
        resources: ["fonts/*.woff2"],
        matches: ["https://*/*", "http://*/*"],
      },
    ],
  };

  if (isFirefox) {
    manifest.background = {
      scripts: ["background.js"],
      type: "module",
    };
    manifest.sidebar_action = {
      default_title: "Tamil Toolkit",
      default_panel: "panel.html",
      default_icon: {
        "16": "icons/icon-16.png",
        "32": "icons/icon-32.png",
      },
      open_at_install: false,
    };
    manifest.browser_specific_settings = {
      gecko: {
        id: "tamil-toolkit@tamil-toolkit.dev",
        strict_min_version: "140.0",
        data_collection_permissions: {
          required: ["none"],
        },
      },
    };
  } else {
    manifest.minimum_chrome_version = "116";
    manifest.background = {
      service_worker: "background.js",
      type: "module",
    };
    manifest.side_panel = {
      default_path: "panel.html",
    };
  }

  return manifest;
}

export function writeManifest(target) {
  const pkg = JSON.parse(fs.readFileSync(path.join(extDir, "package.json"), "utf8"));
  const outDir = path.join(extDir, "dist", target);
  fs.mkdirSync(outDir, { recursive: true });
  const manifest = createManifest(target, pkg.version);
  const manifestPath = path.join(outDir, "manifest.json");
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  return manifestPath;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const target = process.argv[2];
  if (target !== "chrome" && target !== "firefox") {
    console.error("Usage: node scripts/build-manifests.mjs <chrome|firefox>");
    process.exit(1);
  }
  const written = writeManifest(target);
  console.log(`[build-manifests] Wrote ${written}`);
}
