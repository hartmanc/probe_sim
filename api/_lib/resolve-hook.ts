// Vercel's Node builder transpiles each .ts file to .js but keeps import specifiers as written, and the
// project is "type": "module", so Node's ESM resolver would reject the extensionless relative imports used
// throughout src/ (src/physics, src/scoreboard). This resolve hook retries such specifiers with ".js",
// ".ts" and "/index.js" before giving up. It must be installed before the handler graph is imported.
import * as nodeModule from 'node:module';

type Next = (s: string, c?: unknown) => unknown;
const EXT = ['.js', '.ts', '/index.js', '/index.ts'];
const needsExt = (s: string) => /^\.{1,2}\//.test(s) && !/\.(m|c)?(j|t)s$|\.json$/.test(s);

let installed = false;
export function installResolveHook(): void {
  if (installed) return;
  installed = true;
  const m = nodeModule as unknown as { registerHooks?: (h: { resolve: (s: string, c: unknown, n: Next) => unknown }) => void };
  if (typeof m.registerHooks !== 'function') return; // older Node: nothing to do (bundled or extension-full builds)
  m.registerHooks({
    resolve(specifier, context, next) {
      try { return next(specifier, context); } catch (e) {
        if (!needsExt(specifier)) throw e;
        for (const x of EXT) { try { return next(specifier + x, context); } catch { /* try the next */ } }
        throw e;
      }
    },
  });
}
