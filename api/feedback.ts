// Vercel Function: the in-game bug / feature report (src/feedback/handler.ts; docs/feedback.md: limits, token, labels).
//   POST /api/feedback  { kind: 'bug'|'feature', description, context?, name?, secret? } -> { ok, number, url }
// Files a GitHub issue on hartmanc/probe_sim with the token in GITHUB_ISSUES_TOKEN (a fine-grained token limited to
// issues on that repo, set by the owner in Vercel). The rate limiter shares the scoreboard's store.
import { installResolveHook } from './_lib/resolve-hook.js';

installResolveHook();

type Handler = (req: Request) => Promise<Response>;
let handler: Promise<Handler> | null = null;

function getHandler(): Promise<Handler> {
  handler ??= (async () => {
    const [{ handleFeedback }, { storeFromEnv }] = await Promise.all([
      import('../src/feedback/handler.js'),
      import('../src/scoreboard/store.js'),
    ]);
    const store = storeFromEnv(process.env);
    const allowedOrigins = (process.env.SCOREBOARD_ALLOWED_ORIGINS ?? '').split(',').map((s) => s.trim()).filter(Boolean);
    return (req: Request) => handleFeedback(req, {
      store, allowedOrigins, token: process.env.GITHUB_ISSUES_TOKEN || undefined,
      log: (m) => console.log(`[feedback] ${m}`),
    });
  })();
  return handler;
}

export async function POST(req: Request): Promise<Response> { return (await getHandler())(req); }
export async function GET(req: Request): Promise<Response> { return (await getHandler())(req); }
