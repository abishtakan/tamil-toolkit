import fs from "node:fs";
import https from "node:https";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 3000);
const DIST_DIR = path.join(__dirname, "dist");
const CERT_DIR = path.join(os.homedir(), ".office-addin-dev-certs");

const certFile = path.join(CERT_DIR, "localhost.crt");
const keyFile = path.join(CERT_DIR, "localhost.key");

if (!fs.existsSync(DIST_DIR)) {
  console.error("Build output not found. Run `pnpm --filter tamil-word-addin build` first.");
  process.exit(1);
}

if (!fs.existsSync(certFile) || !fs.existsSync(keyFile)) {
  console.error("SSL Certificates not found in " + CERT_DIR);
  console.error("Run `powershell -File create_cert.ps1` or `npx office-addin-dev-certs install`.");
  process.exit(1);
}

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".wasm": "application/wasm",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

const server = https.createServer(
  {
    key: fs.readFileSync(keyFile),
    cert: fs.readFileSync(certFile),
  },
  (req, res) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    res.setHeader("Cache-Control", "no-store");

    const reqPath = (req.url || "/").split("?")[0];
    const safeRel = path.normalize(reqPath === "/" ? "/index.html" : reqPath).replace(/^(\.\.[/\\])+/, "");
    const filePath = path.join(DIST_DIR, safeRel);

    if (filePath.startsWith(DIST_DIR) && fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath).toLowerCase();
      const stat = fs.statSync(filePath);
      const isStaticAsset = ext === ".png" || ext === ".svg" || ext === ".wasm";
      // Word Desktop's WinInet ribbon icon loader requires cacheable PNGs (no-store causes blue hexagon fallback)
      res.setHeader(
        "Cache-Control",
        isStaticAsset ? "public, max-age=3600" : "no-store"
      );
      res.writeHead(200, {
        "Content-Type": MIME_TYPES[ext] || "application/octet-stream",
        "Content-Length": stat.size,
      });
      fs.createReadStream(filePath).pipe(res);
    } else {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("404 Not Found: " + reqPath);
    }
  }
);

server.listen(PORT, () => {
  console.log(`Tamil Toolkit Word Add-in HTTPS Server running at https://localhost:${PORT}/`);
  console.log(`Taskpane: https://localhost:${PORT}/index.html`);
  console.log(`Commands: https://localhost:${PORT}/commands.html`);
});
