import path from "node:path";
import { defineConfig } from "vite";
import wasm from "vite-plugin-wasm";

const browserTarget = process.env.BROWSER_TARGET === "firefox" ? "firefox" : "chrome";
const entryMode = process.env.BUILD_ENTRY || "pages";
const outDir = path.resolve(import.meta.dirname, "dist", browserTarget);

export default defineConfig(() => {
  if (entryMode === "content") {
    return {
      define: {
        __BROWSER_TARGET__: JSON.stringify(browserTarget),
      },
      build: {
        target: "es2022",
        outDir,
        emptyOutDir: false,
        lib: {
          entry: path.resolve(import.meta.dirname, "src/content/index.ts"),
          name: "TamilToolkitContent",
          formats: ["iife" as const],
          fileName: () => "content.js",
        },
        rollupOptions: {
          output: {
            inlineDynamicImports: true,
          },
        },
      },
    };
  }

  if (entryMode === "background") {
    return {
      plugins: [wasm()],
      define: {
        __BROWSER_TARGET__: JSON.stringify(browserTarget),
      },
      build: {
        target: "esnext",
        outDir,
        emptyOutDir: false,
        rollupOptions: {
          input: {
            background: path.resolve(import.meta.dirname, "src/background/index.ts"),
          },
          output: {
            format: "es" as const,
            entryFileNames: "[name].js",
            chunkFileNames: "chunks/[name]-[hash].js",
            assetFileNames: "assets/[name]-[hash][extname]",
          },
        },
      },
    };
  }

  const pageInputs: Record<string, string> = {
    panel: path.resolve(import.meta.dirname, "panel.html"),
    popup: path.resolve(import.meta.dirname, "popup.html"),
  };
  if (browserTarget === "chrome") {
    pageInputs.offscreen = path.resolve(import.meta.dirname, "offscreen.html");
  }

  return {
    plugins: [wasm()],
    define: {
      __BROWSER_TARGET__: JSON.stringify(browserTarget),
    },
    build: {
      target: "esnext",
      outDir,
      emptyOutDir: true,
      rollupOptions: {
        input: pageInputs,
        output: {
          entryFileNames: "[name].js",
          chunkFileNames: "chunks/[name]-[hash].js",
          assetFileNames: "assets/[name]-[hash][extname]",
        },
      },
    },
  };
});
