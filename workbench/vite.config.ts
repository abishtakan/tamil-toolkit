import { spawn } from "node:child_process";
import { isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";

const workbenchRoot = fileURLToPath(new URL(".", import.meta.url));
const root = fileURLToPath(new URL("../", import.meta.url));
const wasmBuildArgs = [
  "--dir", "workbench", "run", "build:wasm:web",
];

type TestStep = { label: string; command: string; args: string[]; cwd?: string };
const rustPackages = ["tamil-core", "tamil-collate", "tamil-numerals", "tamil-codec", "tamil-toolkit"];
const nativeTestPlans: Record<string, TestStep[]> = Object.fromEntries([
  ...rustPackages.map((packageId): [string, TestStep[]] => [packageId, [{
    label: `Rust package tests: ${packageId}`,
    command: "cargo",
    args: ["test", "--locked", "-p", packageId],
  }]]),
  ["tamil-wasm", [
    {
      label: "Build Node WASM binding",
      command: "pnpm",
      args: ["--dir", "workbench", "exec", "wasm-pack", "build", "../bindings/js-wasm", "--dev", "--target", "nodejs", "--out-dir", "pkg-node", "--out-name", "tamil_toolkit", "--locked"],
    },
    {
      label: "Run Node and browser WASM package tests",
      command: "pnpm",
      args: ["--filter", "tamil-toolkit", "exec", "vitest", "run", "--reporter=dot"],
    },
  ]],
  ["tamil-python", [
    {
      label: "Prepare dependency license notices",
      command: "uv",
      args: ["run", "--locked", "python", "tools/release.py", "licenses"],
    },
    {
      label: "Build the PyO3 extension",
      command: "uv",
      args: ["run", "--locked", "maturin", "develop", "--locked", "--manifest-path", "bindings/python/Cargo.toml"],
    },
    {
      label: "Run Python package golden tests",
      command: "uv",
      args: ["run", "--locked", "python", "-m", "pytest", "bindings/python/tests/test_golden.py", "-q"],
    },
  ]],
  ["tamil-dart", [{ label: "Run Dart FFI build, analysis, and golden tests", command: "just", args: ["test-dart"] }]],
]);

function rustWasmHotReload(): Plugin {
  return {
    name: "tamil-toolkit-rust-wasm-hmr",
    configureServer(server) {
      server.watcher.add(["crates", "lexicon", "bindings/js-wasm/Cargo.toml", "Cargo.toml", "Cargo.lock"].map((path) => resolve(root, path)));

      let timer: ReturnType<typeof setTimeout> | undefined;
      let building = false;
      let buildAgain = false;
      const nativeBuilds = new Map<string, Promise<string | undefined>>();

      const isRustInput = (filename: string) => {
        const absolute = isAbsolute(filename) ? filename : resolve(root, filename);
        const pathFromRoot = relative(root, absolute).replaceAll("\\", "/");
        return /^(?:crates\/.*\.(?:rs|toml)|lexicon\/.*\.(?:toml|csv)|bindings\/js-wasm\/Cargo\.toml|Cargo\.(?:toml|lock))$/i.test(pathFromRoot);
      };

      const startBuild = () => {
        if (building) {
          buildAgain = true;
          return;
        }
        building = true;
        server.ws.send("workbench:wasm-build", { state: "building" });
        server.config.logger.info("Rust/lexicon changed; rebuilding browser WASM…");

        const command = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
        const child = spawn(command, wasmBuildArgs, { cwd: root, shell: process.platform === "win32" });
        child.stdout.on("data", (chunk: Buffer) => server.config.logger.info(chunk.toString().trimEnd()));
        child.stderr.on("data", (chunk: Buffer) => server.config.logger.info(chunk.toString().trimEnd()));
        child.on("error", (error) => {
          server.config.logger.error(`Browser WASM rebuild could not start: ${error.message}`);
          server.ws.send("workbench:wasm-build", { state: "failed", message: error.message });
        });
        child.on("close", (code) => {
          building = false;
          if (code === 0) {
            server.config.logger.info("Browser WASM rebuilt; refreshing the workbench.");
            server.ws.send("workbench:wasm-build", { state: "ready" });
            server.ws.send({ type: "full-reload", path: "*" });
          } else {
            const message = `wasm-pack exited with code ${code ?? "unknown"}`;
            server.config.logger.error(message);
            server.ws.send("workbench:wasm-build", { state: "failed", message });
          }
          if (buildAgain) {
            buildAgain = false;
            startBuild();
          }
        });
      };

      const scheduleBuild = (filename: string) => {
        if (!isRustInput(filename)) return;
        nativeBuilds.clear();
        if (timer) clearTimeout(timer);
        timer = setTimeout(startBuild, 350);
      };

      server.watcher.on("change", scheduleBuild);
      server.watcher.on("add", scheduleBuild);
      server.watcher.on("unlink", scheduleBuild);

      let nativeWorkRunning = false;
      const runCommand = (command: string, args: string[], cwd: string, input = "", extraEnv: Record<string, string> = {}) =>
        new Promise<{ code: number | null; stdout: string; stderr: string; spawnError: string }>((resolveRun) => {
          const child = spawn(command, args, {
            cwd,
            shell: process.platform === "win32" && command === "dart",
            windowsHide: true,
            env: { ...process.env, ...extraEnv },
          });
          let stdout = "";
          let stderr = "";
          let spawnError = "";
          child.stdout.on("data", (chunk: Buffer) => { stdout = (stdout + chunk.toString()).slice(-512_000); });
          child.stderr.on("data", (chunk: Buffer) => { stderr = (stderr + chunk.toString()).slice(-512_000); });
          child.on("error", (error) => { spawnError = error.message; });
          child.on("close", (code) => resolveRun({ code, stdout, stderr, spawnError }));
          child.stdin.end(input);
        });

      const commandFailure = (label: string, result: { code: number | null; stdout: string; stderr: string; spawnError: string }) =>
        result.spawnError || result.stderr.trim() || result.stdout.trim() || `${label} exited with code ${result.code ?? "unknown"}`;

      const prepareNativeRuntime = (packageId: string): Promise<string | undefined> => {
        const cached = nativeBuilds.get(packageId);
        if (cached) return cached;
        const preparation = (async () => {
          if (packageId === "tamil-python") {
            const notices = await runCommand("uv", ["run", "--locked", "python", "tools/release.py", "licenses"], root);
            if (notices.code !== 0) return commandFailure("Dependency license notices", notices);
            const result = await runCommand("uv", ["run", "--locked", "maturin", "develop", "--locked", "--manifest-path", "bindings/python/Cargo.toml"], root);
            return result.code === 0 ? undefined : commandFailure("PyO3 build", result);
          }
          const build = await runCommand("cargo", ["build", "--locked", "-p", "tamil-dart"], root);
          if (build.code !== 0) return commandFailure("Dart FFI library build", build);
          const dependencies = await runCommand("dart", ["pub", "get", "--enforce-lockfile"], resolve(root, "bindings/dart-flutter"));
          return dependencies.code === 0 ? undefined : commandFailure("Dart dependency check", dependencies);
        })();
        nativeBuilds.set(packageId, preparation);
        void preparation.then((error) => {
          if (error && nativeBuilds.get(packageId) === preparation) nativeBuilds.delete(packageId);
        }, () => nativeBuilds.delete(packageId));
        return preparation;
      };

      server.middlewares.use("/__workbench/manual-run", (request, response) => {
        const reply = (status: number, value: Record<string, unknown>) => {
          response.writeHead(status, {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
          });
          response.end(JSON.stringify(value));
        };
        const host = request.headers.host;
        if (request.method !== "POST") return reply(405, { error: "POST required" });
        if (!host || request.headers.origin !== `http://${host}`) return reply(403, { error: "Local workbench origin required" });
        if (nativeWorkRunning) return reply(409, { error: "A native package task is already running" });

        let body = "";
        let bodySize = 0;
        let tooLarge = false;
        request.on("data", (chunk: Buffer) => {
          bodySize += chunk.length;
          if (bodySize > 64 * 1024) {
            tooLarge = true;
            return;
          }
          body += chunk.toString("utf8");
        });
        request.on("end", () => {
          if (tooLarge) return reply(413, { error: "Manual request must be smaller than 64 KB" });
          if (nativeWorkRunning) return reply(409, { error: "A native package task is already running" });
          let payload: { packageId?: string; request?: unknown };
          try {
            payload = JSON.parse(body) as { packageId?: string; request?: unknown };
          } catch {
            return reply(400, { error: "Invalid JSON body" });
          }
          const { packageId, request: operationRequest } = payload;
          if (packageId !== "tamil-python" && packageId !== "tamil-dart") {
            return reply(404, { error: "Only the Python and Dart native adapters use this runner" });
          }
          if (!operationRequest || typeof operationRequest !== "object" || typeof (operationRequest as { op?: unknown }).op !== "string") {
            return reply(400, { error: "A dispatcher request with an operation name is required" });
          }
          nativeWorkRunning = true;
          const input = JSON.stringify(operationRequest);

          const execute = async () => {
            try {
              const preparationError = await prepareNativeRuntime(packageId);
              if (preparationError) return reply(500, { error: preparationError });
              if (packageId === "tamil-python") {
                const code = "import json,sys,tamil_toolkit\ntry:\n request=json.load(sys.stdin)\n print(json.dumps({'ok':tamil_toolkit.execute(request)},ensure_ascii=True))\nexcept Exception as error:\n print(json.dumps({'error':str(error)},ensure_ascii=True))";
                const result = await runCommand("uv", ["run", "--locked", "python", "-c", code], root, input, { PYTHONIOENCODING: "utf-8" });
                if (result.code !== 0) return reply(500, { error: commandFailure("Python request", result) });
                const answer = JSON.parse(result.stdout.trim().split(/\r?\n/).at(-1) ?? "") as Record<string, unknown>;
                return reply(200, answer);
              }

              const dartRoot = resolve(root, "bindings/dart-flutter");
              const libraryName = process.platform === "win32"
                ? "tamil_toolkit_ffi.dll"
                : process.platform === "darwin"
                  ? "libtamil_toolkit_ffi.dylib"
                  : "libtamil_toolkit_ffi.so";
              const libraryPath = resolve(root, "target/debug", libraryName);
              const result = await runCommand("dart", ["run", "bin/manual_request.dart", libraryPath], dartRoot, input);
              if (result.code !== 0) return reply(500, { error: commandFailure("Dart FFI request", result) });
              const answer = JSON.parse(result.stdout.trim().split(/\r?\n/).at(-1) ?? "") as Record<string, unknown>;
              return reply(200, answer);
            } catch (error) {
              return reply(500, { error: error instanceof Error ? error.message : String(error) });
            } finally {
              nativeWorkRunning = false;
            }
          };
          void execute();
        });
      });

      server.middlewares.use("/__workbench/native-test", (request, response) => {
        const host = request.headers.host;
        if (request.method !== "POST") {
          response.writeHead(405, { "content-type": "application/json" });
          response.end(JSON.stringify({ error: "POST required" }));
          return;
        }
        if (!host || request.headers.origin !== `http://${host}`) {
          response.writeHead(403, { "content-type": "application/json" });
          response.end(JSON.stringify({ error: "Local workbench origin required" }));
          return;
        }
        if (nativeWorkRunning) {
          response.writeHead(409, { "content-type": "application/json" });
          response.end(JSON.stringify({ error: "A native package test is already running" }));
          return;
        }

        let body = "";
        let tooLarge = false;
        request.on("data", (chunk: Buffer) => {
          if (tooLarge) return;
          body += chunk.toString();
          if (body.length > 256) {
            tooLarge = true;
            body = "";
          }
        });
        request.on("end", () => {
          if (tooLarge) {
            response.writeHead(413, { "content-type": "application/json" });
            response.end(JSON.stringify({ error: "Request body too large" }));
            return;
          }
          let packageId = "";
          try {
            packageId = (JSON.parse(body) as { packageId?: string }).packageId ?? "";
          } catch {
            response.writeHead(400, { "content-type": "application/json" });
            response.end(JSON.stringify({ error: "Invalid JSON body" }));
            return;
          }
          const steps = nativeTestPlans[packageId];
          if (!steps) {
            response.writeHead(404, { "content-type": "application/json" });
            response.end(JSON.stringify({ error: "No native test is registered for that package" }));
            return;
          }

          nativeWorkRunning = true;
          response.writeHead(200, {
            "content-type": "application/x-ndjson; charset=utf-8",
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
          });
          const send = (event: Record<string, unknown>) => {
            if (!response.writableEnded && !response.destroyed) response.write(`${JSON.stringify(event)}\n`);
          };
          const finish = (success: boolean, message?: string) => {
            send({ type: "complete", success, message });
            nativeWorkRunning = false;
            if (!response.destroyed) response.end();
          };

          const runStep = (index: number) => {
            const step = steps[index];
            if (!step) {
              finish(true, "Native package tests passed.");
              return;
            }
            send({ type: "step", label: step.label });
            const command = process.platform === "win32" && step.command === "pnpm" ? "pnpm.cmd" : step.command;
            const child = spawn(command, step.args, {
              cwd: step.cwd ? resolve(root, step.cwd) : root,
              shell: process.platform === "win32" && command.endsWith(".cmd"),
            });
            child.stdout.on("data", (chunk: Buffer) => send({ type: "output", text: chunk.toString() }));
            child.stderr.on("data", (chunk: Buffer) => send({ type: "output", text: chunk.toString() }));
            let spawnError = "";
            child.on("error", (error) => { spawnError = error.message; });
            child.on("close", (code) => {
              if (code !== 0) {
                finish(false, spawnError || `${step.command} exited with code ${code ?? "unknown"}`);
                return;
              }
              runStep(index + 1);
            });
          };
          runStep(0);
        });
      });
    },
  };
}

export default defineConfig({
  root: workbenchRoot,
  plugins: [rustWasmHotReload()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    watch: { ignored: ["**/dist/**"] },
  },
  build: { chunkSizeWarningLimit: 3000 },
});
