// Small request helpers shared by api/scores (handler.ts) and api/feedback (src/feedback/handler.ts). Pure TS.

/** Same-origin check: no Origin header (curl, same-origin GET) passes; otherwise its host must be ours or allowed. */
export function originAllowed(req: Request, deps: { allowedOrigins?: string[] }): { ok: boolean; origin: string | null } {
  const origin = req.headers.get('origin');
  if (!origin) return { ok: true, origin: null };
  if (deps.allowedOrigins?.includes(origin)) return { ok: true, origin };
  const host = req.headers.get('x-forwarded-host') ?? req.headers.get('host') ?? new URL(req.url).host;
  try { return { ok: new URL(origin).host === host, origin }; } catch { return { ok: false, origin }; }
}

export function clientIp(req: Request): string {
  const xff = req.headers.get('x-forwarded-for');
  const ip = (xff ? xff.split(',')[0] : req.headers.get('x-real-ip')) ?? 'unknown';
  return ip.trim().slice(0, 64) || 'unknown';
}
