// Vercel Function: the public scoreboard (docs/scoreboard.md).
//   GET  /api/scores                       -> server's current boards + store kind
//   GET  /api/scores?board=<key>[&name=X]  -> top 10 (+ X's rank)
//   POST /api/scores  (JSON Submission)    -> validate, replay hot laps, store, rank
// Storage: Upstash Redis when UPSTASH_REDIS_REST_URL/_TOKEN or KV_REST_API_URL/_TOKEN are set, else in-memory.
import { installResolveHook } from './_lib/resolve-hook.js';

installResolveHook();

type Handler = (req: Request) => Promise<Response>;
let handler: Promise<Handler> | null = null;

function getHandler(): Promise<Handler> {
  handler ??= (async () => {
    // imported after the hook so the extensionless imports inside src/ resolve under Node ESM
    const [{ handleScores }, { storeFromEnv }, assets] = await Promise.all([
      import('../src/scoreboard/handler.js'),
      import('../src/scoreboard/store.js'),
      import('./_lib/assets.js'),
    ]);
    const store = storeFromEnv(process.env);
    const allowedOrigins = (process.env.SCOREBOARD_ALLOWED_ORIGINS ?? '').split(',').map((s) => s.trim()).filter(Boolean);
    return (req: Request) => handleScores(req, {
      store, allowedOrigins,
      assets: assets.loadSimAssets, physics: assets.serverPhysics,
      log: (m) => console.log(`[scores] ${m}`),
    });
  })();
  return handler;
}

export async function GET(req: Request): Promise<Response> { return (await getHandler())(req); }
export async function POST(req: Request): Promise<Response> { return (await getHandler())(req); }
export async function OPTIONS(req: Request): Promise<Response> { return (await getHandler())(req); }
