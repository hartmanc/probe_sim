import { describe, expect, test } from 'vitest';
import { MemoryStore, UpstashStore, storeFromEnv } from '../store';

describe('MemoryStore', () => {
  test('ascending board keeps the best (lowest) per member and ranks', async () => {
    const s = new MemoryStore();
    expect(await s.submit('b', 'coby', 120, true, '{"name":"Coby"}')).toEqual({ improved: true, best: 120 });
    expect(await s.submit('b', 'coby', 125, true, '{"name":"worse"}')).toEqual({ improved: false, best: 120 });
    expect(await s.meta('b', 'coby')).toBe('{"name":"Coby"}');
    await s.submit('b', 'driver_a', 119, true, '{}');
    expect(await s.rank('b', 'driver_a', true)).toBe(0);
    expect(await s.rank('b', 'coby', true)).toBe(1);
    expect(await s.submit('b', 'coby', 118, true, '{"name":"Coby2"}')).toEqual({ improved: true, best: 118 });
    expect((await s.top('b', 10, true)).map((e) => e.member)).toEqual(['coby', 'driver_a']);
    expect(await s.rank('b', 'nobody', true)).toBeNull();
  });
  test('descending board keeps the highest; trims to keep', async () => {
    const s = new MemoryStore();
    for (let i = 0; i < 12; i++) await s.submit('r', `p${i}`, 1000 + i, false, '{}', 10);
    const top = await s.top('r', 10, false);
    expect(top.length).toBe(10);
    expect(top[0]).toMatchObject({ member: 'p11', score: 1011 });
    expect(await s.score('r', 'p0')).toBeNull(); // trimmed
    expect(await s.meta('r', 'p0')).toBeNull();
    expect(await s.submit('r', 'p11', 900, false, '{}', 10)).toEqual({ improved: false, best: 1011 });
  });
  test('fixed-window rate counter', async () => {
    let t = 0;
    const s = new MemoryStore(() => t);
    for (let i = 1; i <= 3; i++) expect((await s.hit('ip', 600)).count).toBe(i);
    t = 599_000;
    expect(await s.hit('ip', 600)).toEqual({ count: 4, ttl: 1 });
    t = 600_000;
    expect((await s.hit('ip', 600)).count).toBe(1);
  });
});

describe('storeFromEnv', () => {
  test('detects the store by presence of either env pair', () => {
    expect(storeFromEnv({}).kind).toBe('memory');
    expect(storeFromEnv({ UPSTASH_REDIS_REST_URL: 'https://x' }).kind).toBe('memory');
    expect(storeFromEnv({ UPSTASH_REDIS_REST_URL: 'https://x', UPSTASH_REDIS_REST_TOKEN: 't' }).kind).toBe('upstash');
    expect(storeFromEnv({ KV_REST_API_URL: 'https://x', KV_REST_API_TOKEN: 't' }).kind).toBe('upstash');
  });
  test('UpstashStore speaks the REST pipeline protocol', async () => {
    const calls: unknown[] = [];
    const fake = async (url: string, init: { body: string; headers: Record<string, string> }) => {
      const cmds = JSON.parse(init.body) as string[][];
      calls.push({ url, auth: init.headers.Authorization, cmds });
      const res = cmds.map((c) => ({ result: c[0] === 'ZADD' ? 1 : c[0] === 'ZSCORE' ? '118.5' : c[0] === 'ZRANGE' ? [] : 'OK' }));
      return { ok: true, status: 200, json: async () => res };
    };
    const s = new UpstashStore('https://redis.example/', 'tok', fake as never);
    expect(await s.submit('hotlap:x', 'coby', 118.5, true, '{}')).toEqual({ improved: true, best: 118.5 });
    expect(calls[0]).toEqual({ url: 'https://redis.example/pipeline', auth: 'Bearer tok', cmds: [['ZADD', 'sb:z:hotlap:x', 'LT', 'CH', '118.5', 'coby'], ['ZSCORE', 'sb:z:hotlap:x', 'coby']] });
    expect((calls[1] as { cmds: string[][] }).cmds).toEqual([['HSET', 'sb:h:hotlap:x', 'coby', '{}'], ['ZRANGE', 'sb:z:hotlap:x', '100', '-1']]);
  });
});
