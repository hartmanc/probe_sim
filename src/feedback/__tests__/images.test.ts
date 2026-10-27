// Pictures on a report: validation, the upload to the feedback-images branch, the fallback (fake token, fake GitHub).
import { describe, expect, test } from 'vitest';
import { FEEDBACK, handleFeedback, issueFor, parseImages, type FeedbackDeps } from '../handler';
import { MemoryStore } from '../../scoreboard/store';

const ORIGIN = 'https://probe.example';
const b64 = (bytes: number[], pad = 0) => Buffer.from([...bytes, ...new Array(pad).fill(7)]).toString('base64');
const JPG = b64([0xff, 0xd8, 0xff, 0xe0], 100);
const PNG = b64([0x89, 0x50, 0x4e, 0x47], 100);
const jpg = (data = JPG) => ({ name: 'a.jpg', type: 'image/jpeg', data });
let ipn = 0;
const post = (body: unknown, headers: Record<string, string> = {}) => new Request(`${ORIGIN}/api/feedback`, {
  method: 'POST', headers: { 'content-type': 'application/json', host: 'probe.example', origin: ORIGIN, 'x-forwarded-for': `8.8.8.${++ipn}`, [FEEDBACK.imagesHeader]: '1', ...headers },
  body: JSON.stringify(body),
});
type Call = { method: string; url: string; body?: any };
type Script = { branch?: 'exists' | 'missing'; putStatus?: (n: number) => number; failRefs?: number };
function gh(sc: Script = {}) {
  const calls: Call[] = [];
  let puts = 0;
  const d: FeedbackDeps = {
    store: new MemoryStore(), token: 'fake-token',
    fetch: async (url, init) => {
      const path = url.replace('https://api.github.com/repos/hartmanc/probe_sim', '');
      calls.push({ method: init.method, url: path, ...(init.body ? { body: JSON.parse(init.body) } : {}) });
      const r = (status: number, j: unknown = {}) => ({ ok: status < 300, status, json: async () => j });
      if (init.method === 'GET' && path === '/git/ref/heads/feedback-images') return sc.branch === 'missing' ? r(404) : r(200, { object: { sha: 'x' } });
      if (init.method === 'GET' && path === '') return r(200, { default_branch: 'main' });
      if (init.method === 'GET' && path === '/git/ref/heads/main') return r(200, { object: { sha: 'abc123' } });
      if (init.method === 'POST' && path === '/git/refs') return r(sc.failRefs ?? 201);
      if (init.method === 'PUT') return r(sc.putStatus ? sc.putStatus(++puts) : 201);
      if (init.method === 'POST' && path === '/issues') return r(201, { number: 42, html_url: 'https://github.com/hartmanc/probe_sim/issues/42' });
      return r(500);
    },
  };
  return { d, calls };
}
const rep = (images: unknown) => ({ kind: 'bug', description: 'Crash at T3', images });

describe('picture validation', () => {
  test('every branch is a 400 with a reason and files nothing', async () => {
    const bad: [unknown, RegExp][] = [
      [[jpg(), jpg(), jpg(), jpg()], /at most 3/],
      [[{ type: 'image/gif', data: JPG }], /type must be/],
      [[{ type: 'image/jpeg', data: '!!!!' }], /base64/],
      [[{ type: 'image/jpeg', data: 'abc' }], /base64/],
      [[{ type: 'image/jpeg', data: PNG }], /not really a JPEG/],
      [[{ type: 'image/png', data: JPG }], /not really a PNG/],
      [[{ type: 'image/jpeg', data: b64([0xff, 0xd8, 0xff], FEEDBACK.maxImageBytes) }], /over 900 KB/],
      [[{ type: 'image/jpeg', data: b64([0xff, 0xd8, 0xff], FEEDBACK.maxImageBytes - 10) }, { type: 'image/jpeg', data: b64([0xff, 0xd8, 0xff], FEEDBACK.maxImageBytes - 10) }, { type: 'image/jpeg', data: b64([0xff, 0xd8, 0xff], FEEDBACK.maxImageBytes - 10) }], /together/],
      ['nope', /list/],
      [[null], /not an object/],
    ];
    for (const [images, re] of bad) {
      const { d, calls } = gh();
      const r = await handleFeedback(post(rep(images)), d);
      expect(r.status, JSON.stringify(images).slice(0, 60)).toBe(400);
      expect(((await r.json()) as { reasons: string[] }).reasons.join()).toMatch(re);
      expect(calls).toHaveLength(0);
    }
  });
  test('accepts jpeg and png, none, and counts decoded bytes', () => {
    expect(parseImages(undefined)).toEqual({ ok: true, images: [] });
    const p = parseImages([jpg(), { type: 'image/png', data: PNG }]);
    expect(p.ok && p.images.map((i) => i.bytes)).toEqual([104, 104]);
  });
  test('without the images header the 4 KB cap stays', async () => {
    const { d } = gh();
    const big = rep([jpg(b64([0xff, 0xd8, 0xff], 6000))]);
    const req = new Request(`${ORIGIN}/api/feedback`, { method: 'POST', headers: { 'content-type': 'application/json', host: 'probe.example', origin: ORIGIN, 'x-forwarded-for': '7.7.7.7' }, body: JSON.stringify(big) });
    expect((await handleFeedback(req, d)).status).toBe(413);
  });
});

describe('picture upload', () => {
  test('branch exists: parallel PUTs, markdown with raw URLs, response counts', async () => {
    const { d, calls } = gh({ branch: 'exists' });
    const r = await handleFeedback(post(rep([jpg(), jpg(JPG)])), d);
    expect(await r.json()).toEqual({ ok: true, number: 42, url: 'https://github.com/hartmanc/probe_sim/issues/42', images: { uploaded: 2, failed: 0 } });
    expect(calls.some((c) => c.url === '/git/refs')).toBe(false);
    const puts = calls.filter((c) => c.method === 'PUT');
    expect(puts).toHaveLength(2);
    expect(puts[0].url).toMatch(/^\/contents\/feedback-images\/\d{4}\/\d{2}\/\d+-1\.jpg$/);
    expect(puts[0].body).toMatchObject({ message: 'feedback image for a report', branch: 'feedback-images', content: JPG, committer: { name: expect.any(String), email: expect.any(String) } });
    const issue = calls.find((c) => c.url === '/issues')!.body;
    expect(issue.body).toContain('## Pictures');
    expect(issue.body).toMatch(/!\[picture 1\]\(https:\/\/raw\.githubusercontent\.com\/hartmanc\/probe_sim\/feedback-images\/feedback-images\/\d{4}\/\d{2}\/\d+-1\.jpg\)/);
    expect(issue.body).toContain('![picture 2](');
    expect(issue.body).not.toContain('could not be uploaded');
    expect(calls.at(-1)!.url).toBe('/issues');
  });
  test('branch missing: created from the default branch HEAD first', async () => {
    const { d, calls } = gh({ branch: 'missing' });
    const r = await handleFeedback(post(rep([jpg()])), d);
    expect((await r.json() as any).images).toEqual({ uploaded: 1, failed: 0 });
    const mk = calls.find((c) => c.url === '/git/refs')!;
    expect(mk.body).toEqual({ ref: 'refs/heads/feedback-images', sha: 'abc123' });
    expect(calls.findIndex((c) => c.url === '/git/refs')).toBeLessThan(calls.findIndex((c) => c.method === 'PUT'));
  });
  test('403 (token without contents: write): the text-only issue is still filed with the note', async () => {
    const { d, calls } = gh({ branch: 'exists', putStatus: () => 403 });
    const r = await handleFeedback(post(rep([jpg(), jpg()])), d);
    expect(r.status).toBe(200);
    expect(await r.json()).toMatchObject({ ok: true, number: 42, images: { uploaded: 0, failed: 2 } });
    const body = calls.find((c) => c.url === '/issues')!.body.body as string;
    expect(body).toContain('_2 picture(s) could not be uploaded (HTTP 403)_');
    expect(body).not.toContain('## Pictures');
  });
  test('422 on one of two: the other is embedded, one is reported failed', async () => {
    const { d, calls } = gh({ branch: 'exists', putStatus: (n) => (n === 1 ? 422 : 201) });
    const r = await handleFeedback(post(rep([jpg(), jpg()])), d);
    expect((await r.json() as any).images).toEqual({ uploaded: 1, failed: 1 });
    const body = calls.find((c) => c.url === '/issues')!.body.body as string;
    expect(body).toContain('![picture 1](');
    expect(body).not.toContain('![picture 2](');
    expect(body).toContain('_1 picture(s) could not be uploaded (HTTP 422)_');
  });
  test('a 409 race is retried once; a network error and a failed branch step fall back too', async () => {
    const a = gh({ branch: 'exists', putStatus: (n) => (n === 1 ? 409 : 201) });
    expect((await (await handleFeedback(post(rep([jpg()])), a.d)).json() as any).images).toEqual({ uploaded: 1, failed: 0 });
    const net = gh();
    const inner = net.d.fetch!;
    net.d.fetch = async (u, i) => { if (i.method === 'PUT') throw new Error('socket'); return inner(u, i); };
    const rn = await handleFeedback(post(rep([jpg()])), net.d);
    expect(rn.status).toBe(200);
    expect(net.calls.find((c) => c.url === '/issues')!.body.body).toContain('(HTTP no answer)');
    const f = gh({ branch: 'missing', failRefs: 403 });
    expect((await (await handleFeedback(post(rep([jpg()])), f.d)).json() as any).images).toEqual({ uploaded: 0, failed: 1 });
  });
  test('text-only reports are unchanged: no images key in the answer, no GitHub calls but the issue', async () => {
    const { d, calls } = gh();
    const r = await handleFeedback(post({ kind: 'bug', description: 'plain' }, {}), d);
    expect(await r.json()).toEqual({ ok: true, number: 42, url: 'https://github.com/hartmanc/probe_sim/issues/42' });
    expect(calls.map((c) => c.method + c.url)).toEqual(['POST/issues']);
  });
  test('uploads count under the existing rate limiter', async () => {
    const { d } = gh();
    const h = { 'x-forwarded-for': '6.6.6.6' };
    const codes: number[] = [];
    for (let i = 0; i < FEEDBACK.perIp + 1; i++) codes.push((await handleFeedback(post({ ...rep([jpg()]), description: `r${i}` }, h), d)).status);
    expect(codes).toEqual([200, 200, 200, 429]);
  });
  test('issueFor keeps user text fenced next to the pictures', () => {
    const i = issueFor({ kind: 'bug', description: 'x' }, 'anonymous', { urls: ['https://raw.githubusercontent.com/a/b'], failed: 0 });
    expect(i.body).toContain('## Pictures\n\n![picture 1](https://raw.githubusercontent.com/a/b)');
  });
});
