import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const extraArgs = process.argv.slice(2);
const isPublicBeta = process.env.VITE_PUBLIC_BETA === '1' || process.env.VITE_PUBLIC_BETA === 'true';
if (isPublicBeta && !extraArgs.includes('--public-beta')) {
  extraArgs.push('--public-beta');
}
const result = spawnSync('uv', ['run', '--locked', 'python', 'tools/prepare_playground.py', ...extraArgs], { cwd: root, stdio: 'inherit' });
if (result.error) { console.error(result.error.message); process.exit(1); }
process.exit(result.status ?? 1);

