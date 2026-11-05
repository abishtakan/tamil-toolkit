import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import wasm from "vite-plugin-wasm";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
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
        globPatterns: ["**/*.{js,css,html,svg,wasm}"],
        maximumFileSizeToCacheInBytes: 10 * 1024 * 1024
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
