import fs from "node:fs";
import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import wasm from "vite-plugin-wasm";
import { VitePWA } from "vite-plugin-pwa";

const isPublicBeta =
  process.env.VITE_PUBLIC_BETA === "1" || process.env.VITE_PUBLIC_BETA === "true";

export default defineConfig({
  plugins: [
    {
      name: "public-beta-exclude-historical",
      closeBundle() {
        const distDir = path.resolve(__dirname, "dist");
        const vercelCfg = path.resolve(__dirname, "vercel.json");
        if (fs.existsSync(distDir) && fs.existsSync(vercelCfg)) {
          fs.copyFileSync(vercelCfg, path.join(distDir, "vercel.json"));
        }
        if (!isPublicBeta) return;
        const historicalDist = path.join(distDir, "historical-lexicon");
        if (fs.existsSync(historicalDist)) {
          fs.rmSync(historicalDist, { recursive: true, force: true });
        }
      },
    },
    {
      name: "cache-large-dev-assets",
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          const url = req.url ?? "";
          if (
            url.includes(".wasm") ||
            url.startsWith("/lexicon-extended/") ||
            url.startsWith("/historical-lexicon/") ||
            url === "/lexicon-browse-index.json"
          ) {
            res.setHeader("Cache-Control", "public, max-age=600");
          }
          next();
        });
      },
    },
    wasm(),
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "robots.txt"],
      manifest: {
        name: "Tamil Toolkit Playground | தமிழ் கருவிப் பட்டறை",
        short_name: "தமிழ் கருவி",
        description: "Practical Tamil language tools and developer diagnostics powered by WebAssembly",
        theme_color: "#963824",
        background_color: "#faf7f2",
        display: "standalone",
        icons: [
          {
            src: "/favicon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any maskable"
          }
        ]
      },
      workbox: {
        // Keep the 46 MiB WASM and lexicon shards out of eager SW precache; cache app shell and bundled Tamil fonts.
        globPatterns: ["**/*.{js,css,html,svg,md,woff2}"],
      }
    })
  ],
  server: {
    port: 5173
  },
  build: {
    target: "esnext"
  }
});
