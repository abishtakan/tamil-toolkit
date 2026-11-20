import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import wasm from "vite-plugin-wasm";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
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
        // Keep the 46 MiB WASM and lexicon shards out of eager SW precache; cache app shell only.
        globPatterns: ["**/*.{js,css,html,svg,md}"],
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
