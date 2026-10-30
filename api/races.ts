// Vercel Function: race recordings (docs/races.md).
//   POST /api/races  (a RaceRecording as JSON or gzip)  -> 204
//   GET  /api/races?day=YYYY-MM-DD | ?id=<id>            -> the replay tool's listing / one recording (header X-Fetch-Token)
// Storage: the scoreboard's store (Upstash Redis when its env is set, else in-memory). The fetch token is RACES_FETCH_TOKEN (env;
// unset: the GET side answers 403).
import { installResolveHook } from './_lib/resolve-hook.js';

installResolveHook();

type Handler = (req: Request) => Promise<Response>;
let handler: Promise<Handler> | null = null;

function getHandler(): Promise<Handler> {
  handler ??= (async () => {
    const [{ handleRaces }, { storeFromEnv }] = await Promise.all([
      import('../src/scoreboard/racehandler.js'),
      import('../src/scoreboard/store.js'),
    ]);
    const store = storeFromEnv(process.env);
    const allowedOrigins = (process.env.SCOREBOARD_ALLOWED_ORIGINS ?? '').split(',').map((s) => s.trim()).filter(Boolean);
    return (req: Request) => handleRaces(req, {
      store, allowedOrigins, fetchToken: process.env.RACES_FETCH_TOKEN || undefined,
      log: (m) => console.log(`[races] ${m}`),
    });
  })();
  return handler;
}

export async function GET(req: Request): Promise<Response> { return (await getHandler())(req); }
export async function POST(req: Request): Promise<Response> { return (await getHandler())(req); }
export async function OPTIONS(req: Request): Promise<Response> { return (await getHandler())(req); }
