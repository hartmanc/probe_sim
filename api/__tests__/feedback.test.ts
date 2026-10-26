// The deployed entry point api/feedback.ts: loads, refuses GET, and without a token answers 503 (never calls GitHub).
import { afterAll, beforeAll, expect, test, vi } from 'vitest';

beforeAll(() => {
  for (const k of ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'KV_REST_API_URL', 'KV_REST_API_TOKEN', 'GITHUB_ISSUES_TOKEN']) vi.stubEnv(k, '');
});
afterAll(() => { vi.unstubAllEnvs(); });

test('api/feedback.ts: 405 on GET, 422 on an empty report, 503 without a token', async () => {
  const m = await import('../feedback');
  const h = { host: 'probe.example', 'content-type': 'application/json' };
  expect((await m.GET(new Request('https://probe.example/api/feedback', { headers: h }))).status).toBe(405);
  expect((await m.POST(new Request('https://probe.example/api/feedback', { method: 'POST', headers: h, body: JSON.stringify({ kind: 'bug', description: '' }) }))).status).toBe(422);
  expect((await m.POST(new Request('https://probe.example/api/feedback', { method: 'POST', headers: h, body: JSON.stringify({ kind: 'bug', description: 'x' }) }))).status).toBe(503);
});
