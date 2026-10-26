import { defineConfig, type Plugin } from 'vite';
import { execSync } from 'node:child_process';
import { readFileSync, readdirSync, rmSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

// the build's commit for the main menu's version line: GIT_SHA passed at deploy time
// (`vercel deploy --build-env GIT_SHA=$(git rev-parse --short HEAD)`: a CLI deploy's build has neither git nor
// VERCEL_GIT_COMMIT_SHA), else Vercel's env on a git-connected deploy, else git locally, '' when unknown
const gitSha = (() => {
  const v = process.env.GIT_SHA || process.env.VERCEL_GIT_COMMIT_SHA;
  if (v) return v.slice(0, 7);
  try { return execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); } catch { return ''; }
})();

// `vite preview` serves the headers vercel.json gives every path (CSP report-only, frame / sniff / referrer /
// permissions), so a local preview shows the same CSP violations production would
const vercelHeaders = (() => {
  try {
    const v = JSON.parse(readFileSync('vercel.json', 'utf8')) as { headers?: { source: string; has?: unknown; missing?: unknown; headers: { key: string; value: string }[] }[] };
    // the unconditional rule (production's policy); the preview-only rule (missing host lemons-sim.app) is not mirrored
    const all = v.headers?.find((h) => h.source === '/(.*)' && !h.has && !h.missing);
    return Object.fromEntries((all?.headers ?? []).map((h) => [h.key, h.value]));
  } catch { return {}; }
})();

// public/audio/families/*/preview.mp3 are listening copies for the audio pipeline, never loaded by the game: not shipped
const dropPreviews = (): Plugin => ({
  name: 'drop-audio-previews',
  apply: 'build',
  closeBundle() {
    const fam = resolve('dist/audio/families');
    if (!existsSync(fam)) return;
    for (const d of readdirSync(fam, { withFileTypes: true })) if (d.isDirectory()) rmSync(join(fam, d.name, 'preview.mp3'), { force: true });
  },
});

// base './' so the built site works from any path (GitHub Pages project site).
export default defineConfig({
  base: './',
  server: { port: 5173, host: true },
  preview: { headers: vercelHeaders },
  build: { target: 'es2022', sourcemap: true, chunkSizeWarningLimit: 2000 },
  define: { __GIT_SHA__: JSON.stringify(gitSha) },
  plugins: [dropPreviews()],
});
