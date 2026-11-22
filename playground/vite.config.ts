import fs from "node:fs";
import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import wasm from "vite-plugin-wasm";
import { VitePWA } from "vite-plugin-pwa";
import { PLAYGROUND_ORIGIN, SEO_TOOL_PAGES } from "./src/lib/seo-pages";

const isPublicBeta =
  process.env.VITE_PUBLIC_BETA === "1" || process.env.VITE_PUBLIC_BETA === "true";

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function prerenderSeoToolPages(distDir: string): void {
  const indexPath = path.join(distDir, "index.html");
  if (!fs.existsSync(indexPath)) return;
  const baseHtml = fs.readFileSync(indexPath, "utf-8");

  for (const page of SEO_TOOL_PAGES) {
    const pageUrl = `${PLAYGROUND_ORIGIN}/tools/${page.slug}/`;
    const escTitle = escapeHtml(page.title);
    const escDesc = escapeHtml(page.description);

    let html = baseHtml
      .replace(/<title>[\s\S]*?<\/title>/, `<title>${escTitle}</title>`)
      .replace(
        /<meta\s+name="description"\s+content="[^"]*"\s*\/>/,
        `<meta name="description" content="${escDesc}" />`
      )
      .replace(
        /<link\s+rel="canonical"\s+href="[^"]*"\s*\/>/,
        `<link rel="canonical" href="${pageUrl}" />`
      )
      .replace(
        /<meta\s+property="og:url"\s+content="[^"]*"\s*\/>/,
        `<meta property="og:url" content="${pageUrl}" />`
      )
      .replace(
        /<meta\s+property="og:title"\s+content="[^"]*"\s*\/>/,
        `<meta property="og:title" content="${escTitle}" />`
      )
      .replace(
        /<meta\s+property="og:description"\s+content="[^"]*"\s*\/>/,
        `<meta property="og:description" content="${escDesc}" />`
      )
      .replace(
        /<meta\s+name="twitter:title"\s+content="[^"]*"\s*\/>/,
        `<meta name="twitter:title" content="${escTitle}" />`
      )
      .replace(
        /<meta\s+name="twitter:description"\s+content="[^"]*"\s*\/>/,
        `<meta name="twitter:description" content="${escDesc}" />`
      )
      .replace(
        /"url":\s*"https:\/\/tamil-toolkit-playground\.vercel\.app\/"/,
        `"url": "${pageUrl}"`
      );

    const ssrFallback = `<div id="root">
      <main style="max-width: 760px; margin: 2rem auto; padding: 1.5rem; font-family: system-ui, sans-serif; line-height: 1.6;">
        <h1>${escapeHtml(page.h1)}</h1>
        <p>${escapeHtml(page.summary)}</p>
        <p><strong>Example:</strong> <code>${escapeHtml(page.example)}</code></p>
        <p><strong>Scope &amp; limits:</strong> ${escapeHtml(page.limits)}</p>
        <p><a href="/">All Tamil Toolkit Playground Tools</a> · <a href="https://github.com/abishtakan/tamil-toolkit">Rust, Python &amp; JS/WASM Source</a></p>
      </main>
    </div>`;

    html = html.replace(/<div id="root">[\s\S]*?<\/div>/, ssrFallback);

    const outDir = path.join(distDir, "tools", page.slug);
    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(path.join(outDir, "index.html"), html, "utf-8");
  }
}

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
        prerenderSeoToolPages(distDir);
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
