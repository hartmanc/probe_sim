// Transfer codes are single-use under concurrency (Astra review, 26 Oct 2026): two adoptions racing with one code, on
// the memory store and on a store that yields between every operation (as separate Redis round trips would).
import { describe, expect, test } from 'vitest';
import { adopt, claim, issueCode, ownership } from '../owner';
import { MemoryStore, type ScoreStore } from '../store';

const A = 'a'.repeat(32), B = 'b'.repeat(32), C = 'c'.repeat(32);

/** Every store call resolves only after a macrotask: interleaves concurrent multi-step callers. */
function interleaving(s: MemoryStore): ScoreStore {
  return new Proxy(s, {
    get(t, k, r) {
      const v = Reflect.get(t, k, r);
      if (typeof v !== 'function') return v;
      return (...args: unknown[]) => new Promise((res, rej) => setTimeout(() => (v as (...a: unknown[]) => Promise<unknown>).apply(t, args).then(res, rej), 0));
    },
  }) as ScoreStore;
}

for (const [label, wrap] of [['memory store', (s: MemoryStore) => s], ['interleaving store', interleaving]] as const) {
  describe(`transfer code concurrency (${label})`, () => {
    test('two adoptions with one code: exactly one succeeds, and that device is authorised', async () => {
      const s = wrap(new MemoryStore());
      await claim(s, 'coby', A);
      const code = await issueCode(s, 'coby', A);
      const [rb, rc] = await Promise.all([adopt(s, 'coby', code!, B), adopt(s, 'coby', code!, C)]);
      expect([rb, rc].filter((r) => r === 'ok')).toHaveLength(1);
      const winner = rb === 'ok' ? B : C, loser = rb === 'ok' ? C : B;
      expect(await ownership(s, 'coby', winner)).toBe('you');
      expect(await ownership(s, 'coby', loser)).toBe('other');
      expect(await ownership(s, 'coby', A)).toBe('you');
    });
    test('an adoption never consumes a replacement code issued while it runs', async () => {
      const s = wrap(new MemoryStore());
      await claim(s, 'coby', A);
      const c1 = await issueCode(s, 'coby', A);
      const [r1, c2] = await Promise.all([adopt(s, 'coby', c1!, B), issueCode(s, 'coby', A)]);
      // whichever came first: the replacement code is either still valid, or c1 was refused because c2 replaced it
      const r2 = await adopt(s, 'coby', c2!, C);
      expect(r1 === 'ok' || r1 === 'bad-code').toBe(true);
      expect(r2).toBe('ok');
    });
    test('a release (owner key deleted) is not undone by an adoption in flight', async () => {
      const s = wrap(new MemoryStore());
      await claim(s, 'coby', A);
      const code = await issueCode(s, 'coby', A);
      const [r] = await Promise.all([adopt(s, 'coby', code!, B), s.kvDel('sb:own:coby')]);
      // either the adoption ran before the release (then the release wins: free), or after (refused); never resurrected
      expect(['ok', 'not-registered', 'bad-code']).toContain(r);
      expect(await ownership(s, 'coby', B)).toBe('free');
    });
    test('codes are issued only to an owning device', async () => {
      const s = wrap(new MemoryStore());
      expect(await issueCode(s, 'coby', A)).toBeNull();
      await claim(s, 'coby', A);
      expect(await issueCode(s, 'coby', B)).toBeNull();
      expect(await issueCode(s, 'coby', A)).toMatch(/^[A-Z2-9]{6}$/);
    });
  });
}

describe('Upstash: issue and adopt are one EVAL each (one round trip, one atomic script)', () => {
  test('the commands sent', async () => {
    const { UpstashStore, LUA_ADOPT, LUA_ISSUE } = await import('../store');
    const sent: string[][][] = [];
    let answer: unknown = 'ok';
    const store = new UpstashStore('https://redis.example', 'fake', async (_u, init) => {
      sent.push(JSON.parse(init.body));
      return { ok: true, status: 200, json: async () => [{ result: answer }] };
    });
    expect(await store.adoptTransfer('sb:own:coby', 'sb:xfer:coby', 'ch', 'dh', 5)).toBe('ok');
    expect(sent).toEqual([[['EVAL', LUA_ADOPT, '2', 'sb:own:coby', 'sb:xfer:coby', 'ch', 'dh', '5']]]);
    answer = 'bad-code';
    expect(await store.adoptTransfer('sb:own:coby', 'sb:xfer:coby', 'ch', 'dh', 5)).toBe('bad-code');
    answer = 'other';
    expect(await store.issueTransfer('sb:own:coby', 'sb:xfer:coby', 'dh', 'ch', 3600)).toBe('other');
    expect(sent[2]).toEqual([['EVAL', LUA_ISSUE, '2', 'sb:own:coby', 'sb:xfer:coby', 'dh', 'ch', '3600']]);
    // the scripts consume the code before touching the owner record, and never create a missing owner record
    expect(LUA_ADOPT.indexOf("redis.call('DEL', KEYS[2])")).toBeLessThan(LUA_ADOPT.indexOf("redis.call('GET', KEYS[1])"));
    expect(LUA_ADOPT).toMatch(/if not rec then return 'not-registered' end/);
  });
});
