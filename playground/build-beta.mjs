import { spawnSync } from "node:child_process";

const env = { ...process.env, VITE_PUBLIC_BETA: "1" };

function runStep(cmd, args) {
  const result = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
    env,
  });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if ((result.status ?? 1) !== 0) {
    process.exit(result.status ?? 1);
  }
}

runStep("node", ["prepare.mjs", "--public-beta"]);
runStep("pnpm", ["exec", "tsc", "--noEmit"]);
runStep("pnpm", ["exec", "vite", "build"]);
