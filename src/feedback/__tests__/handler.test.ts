// The report button's function with a fake GitHub token and a fake fetch (never the real API).
import { describe, expect, test } from 'vitest';
import { FEEDBACK, clean, handleFeedback, issueFor, parseFeedback, type FeedbackDeps } from '../handler';
import { MemoryStore } from '../../scoreboard/store';
import { claim } from '../../scoreboard/owner';

const FAKE = 'fake-token-for-tests';
const ORIGIN = 'https://probe.example';
type Sent = { url: string; headers: Record<string, string>; body: { title: string; body: string; labels: string[] } };
function deps(over: Partial<FeedbackDeps> = {}) {
  const sent: Sent[] = [];
  const d: FeedbackDeps = {
    store: new MemoryStore(), token: FAKE,
    fetch: async (url, init) => { sent.push({ url, headers: init.headers, body: JSON.parse(init.body) }); return { ok: true, status: 201, json: async () => ({ number: 42, html_url: 'https://github.com/hartmanc/probe_sim/issues/42' }) }; },
    ...over,
  };
  return { d, sent };
}
const post = (body: unknown, headers: Record<string, string> = {}) => new Request(`${ORIGIN}/api/feedback`, {
  method: 'POST', headers: { 'content-type': 'application/json', host: 'probe.example', origin: ORIGIN, 'x-forwarded-for': '9.9.9.9', ...headers },
  body: typeof body === 'string' ? body : JSON.stringify(body),
});
const ctx = { version: '0.4.0', sha: 'abc1234', track: 'sonoma', device: 'phone', ua: 'Mozilla/5.0 (iPhone)', screen: '844x390@3', error: 'TypeError: x is undefined\n  at foo' };

describe('feedback function', () => {
  test('files an issue with the labels, the context and "anonymous" without a registered name', async () => {
    const { d, sent } = deps();
    const r = await handleFeedback(post({ kind: 'bug', description: 'The car falls through T11.\nEvery time.', context: ctx }), d);
    expect(r.status).toBe(200);
    expect(await r.json()).toEqual({ ok: true, number: 42, url: 'https://github.com/hartmanc/probe_sim/issues/42' });
    expect(sent).toHaveLength(1);
    expect(sent[0].url).toBe(`https://api.github.com/repos/${FEEDBACK.repo}/issues`);
    expect(sent[0].headers.Authorization).toBe(`Bearer ${FAKE}`);
    expect(sent[0].body.labels).toEqual(['from-game', 'bug']);
    expect(sent[0].body.title).toBe('[bug] The car falls through T11.');
    for (const s of ['anonymous', 'version: 0.4.0', 'sha: abc1234', 'track: sonoma', 'device: phone', 'ua: Mozilla/5.0 (iPhone)', 'screen: 844x390@3', 'TypeError: x is undefined']) expect(sent[0].body.body).toContain(s);
  });

  test('the scoreboard name only when this device owns it', async () => {
    const { d, sent } = deps();
    const S = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
    await claim(d.store, 'coby', S);
    await handleFeedback(post({ kind: 'feature', description: 'Rain', name: 'Coby', secret: S }), d);
    await handleFeedback(post({ kind: 'feature', description: 'Rain', name: 'Coby', secret: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' }), d);
    expect(sent[0].body.body).toContain('~~~text\nCoby\n~~~');
    expect(sent[0].body.labels).toEqual(['from-game', 'feature']);
    expect(sent[1].body.body).toContain('~~~text\nanonymous\n~~~');
  });

  test('user text cannot break out of its code block or mention anyone in the title', () => {
    const p = parseFeedback({ kind: 'bug', description: '@owner hi ~~~\n```js\nalert(1)\u0007‮' });
    expect(p.ok).toBe(true);
    if (!p.ok) return;
    expect(p.value.description).not.toMatch(/~~~|```|\u0007|‮/);
    const i = issueFor(p.value, 'anonymous');
    expect(i.title).not.toContain('@');
    expect(i.body.match(/~~~/g)!.length % 2).toBe(0);
    expect(clean('a\u0000b\nc')).toBe('a b c');
    expect(clean('a\u0000b\nc', true)).toBe('ab\nc');
  });

  test('rejects empty, over-long, wrong kind, oversize and non-JSON reports', async () => {
    const { d, sent } = deps();
    const ip = (n: number) => ({ 'x-forwarded-for': `10.0.0.${n}` });
    expect((await handleFeedback(post({ kind: 'bug', description: '   \u0000 ' }, ip(1)), d)).status).toBe(422);
    expect((await handleFeedback(post({ kind: 'bug', description: 'x'.repeat(FEEDBACK.maxDescription + 1) }, ip(2)), d)).status).toBe(422);
    expect((await handleFeedback(post({ kind: 'praise', description: 'nice' }, ip(3)), d)).status).toBe(422);
    expect((await handleFeedback(post({ kind: 'bug', description: 'é'.repeat(1999), context: ctx }, ip(4)), d)).status).toBe(413);
    expect((await handleFeedback(post('{nope', ip(5)), d)).status).toBe(400);
    expect((await handleFeedback(post('{}', { ...ip(6), 'content-type': 'text/plain' }), d)).status).toBe(415);
    expect((await handleFeedback(post({}, { ...ip(7), 'content-length': '5000' }), d)).status).toBe(413);
    expect(sent).toHaveLength(0);
  });

  test('3 reports per IP per 10 minutes', async () => {
    const { d } = deps();
    for (let i = 0; i < 3; i++) expect((await handleFeedback(post({ kind: 'bug', description: `n${i}` }), d)).status).toBe(200);
    const r = await handleFeedback(post({ kind: 'bug', description: 'four' }), d);
    expect(r.status).toBe(429);
    expect(Number(r.headers.get('retry-after'))).toBeGreaterThan(0);
    expect((await handleFeedback(post({ kind: 'bug', description: 'other ip' }, { 'x-forwarded-for': '8.8.8.8' }), d)).status).toBe(200);
  });

  test('no token: 503 and nothing sent; GitHub failure: 502; foreign origin: 403; GET: 405', async () => {
    const a = deps({ token: undefined });
    expect((await handleFeedback(post({ kind: 'bug', description: 'x' }), a.d)).status).toBe(503);
    expect(a.sent).toHaveLength(0);
    const b = deps({ fetch: async () => ({ ok: false, status: 401, json: async () => ({}) }) });
    expect((await handleFeedback(post({ kind: 'bug', description: 'x' }), b.d)).status).toBe(502);
    expect((await handleFeedback(post({ kind: 'bug', description: 'x' }, { origin: 'https://evil.example' }), deps().d)).status).toBe(403);
    expect((await handleFeedback(new Request(`${ORIGIN}/api/feedback`, { headers: { host: 'probe.example' } }), deps().d)).status).toBe(405);
  });
});
