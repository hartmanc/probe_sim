import { defineConfig } from 'vite';
import { execSync } from 'node:child_process';

// the build's commit for the main menu's version line: Vercel's env on a deploy, git locally, '' when unknown
const gitSha = (() => {
  const v = process.env.VERCEL_GIT_COMMIT_SHA;
  if (v) return v.slice(0, 7);
  try { return execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); } catch { return ''; }
})();

// base './' so the built site works from any path (GitHub Pages project site).
export default defineConfig({
  base: './',
  server: { port: 5173, host: true },
  build: { target: 'es2022', sourcemap: true, chunkSizeWarningLimit: 2000 },
  define: { __GIT_SHA__: JSON.stringify(gitSha) },
});
