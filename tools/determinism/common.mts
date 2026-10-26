// Shared helpers of the determinism tools (docs/determinism.md): Playwright from a local install, esbuild bundles of
// src modules for a browser page, the strict-V8 browser flags.
import { build, type Plugin } from 'esbuild';
import { homedir } from 'node:os';
import { join } from 'node:path';

/** playwright-core: PW_CORE (a path to the package) or the copy in ~/dev/frame-it (1.61.1, with cached Chromium and
 *  WebKit builds in ~/Library/Caches/ms-playwright). Nothing is downloaded. */
export async function playwright(): Promise<any> {
  const p = process.env.PW_CORE ?? join(homedir(), 'dev/frame-it/node_modules/playwright-core');
  return import(join(p, 'index.mjs'));
}

/** Chromium switches for the strict-V8 oracle: Chrome's V8 is built with V8_USE_LIBM_TRIG_FUNCTIONS (Math.sin / cos
 *  from its glibc port); this flag selects the fdlibm sin / cos that Node's V8 has (Node never defines it). Chromium
 *  compiles V8 without FP contraction, so its fdlibm is the plain IEEE evaluation, as on the linux-x64 server. */
export const STRICT_V8_ARGS = ['--js-flags=--no-use-libm-trig-functions'];

/** Bundle `entry` (a TS module) as an IIFE assigning its exports to globalThis[name]. */
export async function bundleIife(entry: string, name: string, plugins: Plugin[] = []): Promise<string> {
  const r = await build({ entryPoints: [entry], bundle: true, format: 'iife', globalName: name, write: false, platform: 'browser', target: 'es2022', plugins, logLevel: 'error' });
  return r.outputFiles[0].text + `\nglobalThis.${name} = ${name};\n`;
}

export const f64ToB64 = (a: Float64Array): string => Buffer.from(a.buffer, a.byteOffset, a.byteLength).toString('base64');
