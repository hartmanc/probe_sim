// The deployed entry point (api/scores.ts) with the on-disk asset loader and the env-selected store.
import { afterAll, beforeAll, expect, test, vi } from 'vitest';

beforeAll(() => {
  // never talk to a real Redis from tests, whatever the shell has set
  for (const k of ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'KV_REST_API_URL', 'KV_REST_API_TOKEN']) vi.stubEnv(k, '');
});
afterAll(() => { vi.unstubAllEnvs(); });

test('api/scores.ts: discovery GET, empty board, rejected POST, assets read from public/', async () => {
  const m = await import('../scores');
  const r = await m.GET(new Request('https://probe.example/api/scores', { headers: { host: 'probe.example' } }));
  expect(r.status).toBe(200);
  const j = await r.json() as { store: string; boards: Record<string, string> };
  expect(j.store).toBe('memory');
  const key = j.boards['laguna_seca/probe_gt'];
  expect(key).toMatch(/^hotlap:laguna_seca:probe_gt:[0-9a-z]+$/);
  const b = await m.GET(new Request(`https://probe.example/api/scores?board=${key}`, { headers: { host: 'probe.example' } }));
  expect(await b.json()).toMatchObject({ ok: true, entries: [] });
  const p = await m.POST(new Request('https://probe.example/api/scores', { method: 'POST', headers: { host: 'probe.example', 'content-type': 'application/json' }, body: JSON.stringify({ mode: 'hotlap', track: 'laguna_seca', car: 'probe_gt', physics: key.split(':')[3], name: 'x', input: 'pad', time: 80, lap: 1, valid: true }) }));
  expect(p.status).toBe(422);
  const o = await m.OPTIONS(new Request('https://probe.example/api/scores', { method: 'OPTIONS', headers: { host: 'probe.example', origin: 'https://probe.example' } }));
  expect(o.status).toBe(204);
});

test('loadSimAssets decodes the same assets the client uses', async () => {
  const { loadSimAssets, serverPhysics } = await import('../_lib/assets');
  const a = await loadSimAssets('laguna_seca', 'probe_gt');
  expect(a.track.length_m).toBe((await import('../../src/scoreboard/config')).TRACKS.laguna_seca.length_m);
  expect(a.heightfield.length).toBe(a.track.heightfield.nx * a.track.heightfield.ny);
  expect(a.farHeightfield?.length).toBe(501 * 501);
  expect(a.ghosts.laps.length).toBeGreaterThan(0);
  expect(await serverPhysics('laguna_seca', 'probe_gt')).toMatch(/^[0-9a-z]+$/);
  await expect(loadSimAssets('monza', 'probe_gt')).rejects.toThrow();
});
