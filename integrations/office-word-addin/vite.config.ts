import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { defineConfig } from "vite";
import wasm from "vite-plugin-wasm";

const certDir = path.join(os.homedir(), ".office-addin-dev-certs");
const certFile = path.join(certDir, "localhost.crt");
const keyFile = path.join(certDir, "localhost.key");
const hasDevCerts = fs.existsSync(certFile) && fs.existsSync(keyFile);

export default defineConfig({
  plugins: [wasm()],
  publicDir: "public",
  server: {
    port: 3000,
    strictPort: true,
    https: hasDevCerts
      ? {
          cert: fs.readFileSync(certFile),
          key: fs.readFileSync(keyFile),
        }
      : undefined,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "no-store",
    },
  },
  build: {
    target: "esnext",
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: path.resolve(import.meta.dirname, "index.html"),
        commands: path.resolve(import.meta.dirname, "commands.html"),
        privacy: path.resolve(import.meta.dirname, "privacy.html"),
        support: path.resolve(import.meta.dirname, "support.html"),
      },
    },
  },
});
