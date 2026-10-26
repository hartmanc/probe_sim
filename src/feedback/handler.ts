// The in-game "Report a bug / request a feature" button (owner's decision, 26 Oct 2026): POST /api/feedback files a
// GitHub issue on hartmanc/probe_sim with the labels `from-game` and `bug` or `feature`. Pure TS: the store (rate
// limit), the token and fetch are injected (api/feedback.ts reads the token from GITHUB_ISSUES_TOKEN; tests use a fake).
//
// Abuse rules: same origin only, 3 reports per IP per 10 min (the scores store's counter), body <= 4 KB, a description
// of 1..2000 characters, control characters stripped everywhere, user text only inside code fences (no mentions, links
// or markup in the issue), no email field. The issue names the scoreboard name only when this device owns it (its
// device secret matches, src/scoreboard/owner.ts); "anonymous" otherwise.
import { clientIp, originAllowed } from '../scoreboard/http';
import { ownership, sha256Hex } from '../scoreboard/owner';
import type { ScoreStore } from '../scoreboard/store';
import { nameKey, normalizeName } from '../scoreboard/validate';

export const FEEDBACK = {
  repo: 'hartmanc/probe_sim',
  maxBodyBytes: 4096,
  maxDescription: 2000,
  perIp: 3,
  windowS: 600,
  /** GitHub must answer within this, ms */
  upstreamTimeoutMs: 10_000,
  /** the same report (IP + kind + description) within this is not filed twice, s */
  dedupeS: 600,
} as const;

export type FeedbackKind = 'bug' | 'feature';

/** What the game attaches (all optional strings; each capped). */
export interface FeedbackContext { version?: string; sha?: string; track?: string; device?: string; ua?: string; screen?: string; error?: string }
export interface FeedbackRequest { kind: FeedbackKind; description: string; context?: FeedbackContext; name?: string; secret?: string }

type FetchLike = (url: string, init: { method: string; headers: Record<string, string>; body: string; signal?: AbortSignal }) => Promise<{ ok: boolean; status: number; json(): Promise<unknown> }>;

export interface FeedbackDeps {
  store: ScoreStore;
  /** The GitHub token (fine-grained, issues on the repo only); undefined = reports are not set up (503). */
  token: string | undefined;
  fetch?: FetchLike;
  allowedOrigins?: string[];
  log?: (msg: string) => void;
  /** upstream timeout override, ms (tests) */
  timeoutMs?: number;
}

/** The body as text, refusing (null) as soon as it passes `max` bytes, whatever Content-Length said. */
export async function readCapped(req: Request, max: number): Promise<string | null> {
  if (!req.body) return '';
  const reader = req.body.getReader();
  const parts: Uint8Array[] = [];
  let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    n += value.byteLength;
    if (n > max) { try { await reader.cancel(); } catch { /* already closed */ } return null; }
    parts.push(value);
  }
  const all = new Uint8Array(n);
  let o = 0;
  for (const p of parts) { all.set(p, o); o += p.byteLength; }
  return new TextDecoder().decode(all);
}

const CAPS: Record<keyof FeedbackContext, number> = { version: 20, sha: 12, track: 32, device: 16, ua: 300, screen: 32, error: 1500 };

/** Strip control and format characters (keeping newlines when asked), and break code fences. */
export function clean(s: string, keepNewlines = false): string {
  let t = s.normalize('NFC').replace(/\r\n?/g, '\n').replace(/\t/g, ' ');
  t = keepNewlines ? t.replace(/[^\P{C}\n]/gu, '') : t.replace(/\p{C}/gu, ' ');
  return t.replace(/(`{3,}|~{3,})/g, (m) => m.split('').join(' ')).trim();
}

/** Parse and clean a report; reasons when it is not acceptable. */
export function parseFeedback(body: unknown): { ok: true; value: FeedbackRequest } | { ok: false; reasons: string[] } {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return { ok: false, reasons: ['body must be a JSON object'] };
  const b = body as Record<string, unknown>;
  const r: string[] = [];
  const kind = b.kind === 'bug' || b.kind === 'feature' ? b.kind : null;
  if (!kind) r.push('kind must be bug or feature');
  const d = typeof b.description === 'string' ? clean(b.description, true) : '';
  if (!d) r.push('describe the bug or the feature');
  else if ([...d].length > FEEDBACK.maxDescription) r.push(`the description is limited to ${FEEDBACK.maxDescription} characters`);
  const context: FeedbackContext = {};
  if (b.context && typeof b.context === 'object' && !Array.isArray(b.context)) {
    const c = b.context as Record<string, unknown>;
    for (const k of Object.keys(CAPS) as (keyof FeedbackContext)[]) {
      if (typeof c[k] === 'string') { const v = clean(c[k] as string, k === 'error').slice(0, CAPS[k]); if (v) context[k] = v; }
    }
  }
  if (r.length) return { ok: false, reasons: r };
  return { ok: true, value: { kind: kind!, description: d, context, ...(typeof b.name === 'string' ? { name: b.name } : {}), ...(typeof b.secret === 'string' ? { secret: b.secret } : {}) } };
}

const fence = (s: string) => `~~~text\n${s}\n~~~`;

/** The issue: title from the first line, the description and the context in code blocks (nothing user-typed renders). */
export function issueFor(f: FeedbackRequest, who: string): { title: string; body: string; labels: string[] } {
  const first = clean(f.description.split('\n')[0]).replace(/@/g, '(at)').replace(/[<>[\]]/g, '');
  const title = `[${f.kind}] ${[...first].length > 70 ? [...first].slice(0, 69).join('') + '…' : first}`;
  const c = f.context ?? {};
  const ctx = (Object.keys(CAPS) as (keyof FeedbackContext)[]).filter((k) => k !== 'error' && c[k]).map((k) => `${k}: ${c[k]}`).join('\n');
  const body = [
    `Filed from the game (${f.kind === 'bug' ? 'bug report' : 'feature request'}).`,
    '',
    'Scoreboard name:',
    fence(who),
    '',
    'Description:',
    fence(f.description),
    '',
    'Context:',
    fence(ctx || '(none)'),
    ...(c.error ? ['', 'Last error:', fence(c.error)] : []),
  ].join('\n');
  return { title, body, labels: ['from-game', f.kind] };
}

const HEADERS = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
const json = (status: number, body: unknown, extra: Record<string, string> = {}) => new Response(JSON.stringify(body), { status, headers: { ...HEADERS, ...extra } });
const fail = (status: number, error: string, reasons?: string[], extra?: Record<string, string>) => json(status, { ok: false, error, ...(reasons?.length ? { reasons } : {}) }, extra);

export async function handleFeedback(req: Request, deps: FeedbackDeps): Promise<Response> {
  const o = originAllowed(req, deps);
  if (!o.ok) return fail(403, 'cross-origin requests are not allowed');
  if (req.method !== 'POST') return fail(405, 'method not allowed', undefined, { Allow: 'POST' });
  try {
    if (!(req.headers.get('content-type') ?? '').toLowerCase().startsWith('application/json')) return fail(415, 'content-type must be application/json');
    if (Number(req.headers.get('content-length') ?? '0') > FEEDBACK.maxBodyBytes) return fail(413, 'report too large', [`at most ${FEEDBACK.maxBodyBytes} bytes`]);
    const rl = await deps.store.hit(`feedback:${clientIp(req)}`, FEEDBACK.windowS);
    if (rl.count > FEEDBACK.perIp) return fail(429, 'rate limited', [`at most ${FEEDBACK.perIp} reports per ${FEEDBACK.windowS / 60} min`], { 'Retry-After': String(Math.max(1, rl.ttl)) });
    const text = await readCapped(req, FEEDBACK.maxBodyBytes);
    if (text === null) return fail(413, 'report too large', [`at most ${FEEDBACK.maxBodyBytes} bytes`]);
    let body: unknown;
    try { body = JSON.parse(text); } catch { return fail(400, 'body is not valid JSON'); }
    const p = parseFeedback(body);
    if (!p.ok) return fail(422, 'rejected', p.reasons);
    if (!deps.token) return fail(503, 'reports are not set up yet');
    // the same report again (a retry after a timeout, a double tap): answer with the first one, never a second issue
    const dupKey = `sb:fbdup:${await sha256Hex(`${clientIp(req)}|${p.value.kind}|${p.value.description}`)}`;
    if (!(await deps.store.kvSet(dupKey, 'pending', { nx: true, ex: FEEDBACK.dedupeS }))) {
      const prev = await deps.store.kvGet(dupKey);
      let j: { number?: number; url?: string } | null = null;
      try { j = prev && prev !== 'pending' ? JSON.parse(prev) : null; } catch { j = null; }
      if (j) return json(200, { ok: true, number: j.number ?? null, url: j.url ?? null, duplicate: true });
      return fail(409, 'already sent', ['this report is already being filed (or GitHub did not answer in time): check the issues before sending it again']);
    }
    const n = normalizeName(p.value.name);
    const who = n && (await ownership(deps.store, nameKey(n), p.value.secret)) === 'you' ? n : 'anonymous';
    const issue = issueFor(p.value, who);
    let res: Awaited<ReturnType<FetchLike>>;
    try {
      res = await (deps.fetch ?? (fetch as unknown as FetchLike))(`https://api.github.com/repos/${FEEDBACK.repo}/issues`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${deps.token}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'probe-sim-feedback', 'Content-Type': 'application/json',
        },
        body: JSON.stringify(issue),
        signal: AbortSignal.timeout(deps.timeoutMs ?? FEEDBACK.upstreamTimeoutMs),
      });
    } catch (e) {
      // no answer: the issue may or may not exist, so the dedupe key stays (a retry gets 409, not a second issue)
      deps.log?.(`github did not answer: ${(e as Error)?.name ?? e}`);
      return fail(504, 'GitHub did not answer in time; the report may have been filed');
    }
    if (!res.ok) { await deps.store.kvDel(dupKey); deps.log?.(`github answered ${res.status}`); return fail(502, 'could not file the report, try again later'); }
    const j = (await res.json()) as { number?: number; html_url?: string };
    await deps.store.kvSet(dupKey, JSON.stringify({ number: j.number ?? null, url: j.html_url ?? null }), { ex: FEEDBACK.dedupeS });
    deps.log?.(`issue #${j.number} filed (${p.value.kind})`);
    return json(200, { ok: true, number: j.number ?? null, url: j.html_url ?? null });
  } catch (e) {
    deps.log?.(`error: ${(e as Error)?.message ?? e}`);
    return fail(500, 'internal error');
  }
}
