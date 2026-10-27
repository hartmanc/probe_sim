// The RESP adapter (support/respAdapter.ts) against the fake REST pipeline of store.test.ts, on the same command
// sequences: UpstashStore must send the identical commands through either, and read the replies the same way.
// No Redis here (the real one is src/scoreboard/__tests__/e2e.scoreboard.test.ts).
import { describe, expect, test } from 'vitest';
import { UpstashStore } from '../store';
import { respFetch, type RespClient } from './support/respAdapter';

type Cmd = string[];
/** reply per command name, as the real server would answer these sequences */
const replies: Record<string, unknown> = {
  ZADD: 1, ZSCORE: '118.5', ZRANGE: [], HSET: 1, EVAL: 'ok', GET: null, SET: 'OK', INCR: 3, TTL: -1, EXPIRE: 1, SCAN: ['0', ['sb:z:a', 'sb:z:b']], DEL: 1,
};

function run(drive: (s: UpstashStore) => Promise<unknown[]>) {
  const viaRest: Cmd[][] = [], viaResp: Cmd[][] = [];
  const fake = async (_u: string, init: { body: string }) => {
    const cmds = JSON.parse(init.body) as Cmd[];
    viaRest.push(cmds);
    return { ok: true, status: 200, json: async () => cmds.map((c) => ({ result: replies[c[0]] ?? null })) };
  };
  const client: RespClient = {
    pipeline() {
      const q: Cmd[] = [];
      return {
        call(name, ...args) { q.push([name, ...args]); return this; },
        async exec() { viaResp.push(q); return q.map((c) => [null, replies[c[0]] ?? null] as [Error | null, unknown]); },
      };
    },
  };
  return (async () => {
    const a = await drive(new UpstashStore('https://r.example', 't', fake as never));
    const b = await drive(new UpstashStore('https://r.example', 't', respFetch(client)));
    return { a, b, viaRest, viaResp };
  })();
}

describe('respFetch', () => {
  test('the same commands reach the RESP client as the REST pipeline, and the replies read the same', async () => {
    const { a, b, viaRest, viaResp } = await run(async (s) => [
      await s.submit('hotlap:x', 'coby', 118.5, true, '{"name":"coby"}'),
      await s.issueTransfer('sb:own:coby', 'sb:xfer:coby', 'h1', 'c1', 3600),
      await s.adoptTransfer('sb:own:coby', 'sb:xfer:coby', 'c1', 'h2', 5),
      await s.kvSet('sb:own:n', 'v1|x|h', { nx: true }),
      await s.kvGet('sb:own:n'),
      await s.hit('post:1.2.3.4', 600),
      await s.boards(),
      await s.kvDel('sb:own:n'),
    ]);
    expect(viaResp).toEqual(viaRest);
    expect(viaResp.flat().map((c) => c[0])).toContain('EVAL');
    const ev = viaResp.flat().filter((c) => c[0] === 'EVAL');
    expect(ev[0].slice(2, 4)).toEqual(['2', 'sb:own:coby']);   // numkeys, then KEYS[1]; args follow the keys
    expect(b).toEqual(a);
  });
  test('an error reply becomes {error} and the store throws it', async () => {
    const client: RespClient = {
      pipeline() { return { call() { return this; }, async exec() { return [[new Error('ERR boom'), undefined]] as [Error | null, unknown][]; } }; },
    };
    await expect(new UpstashStore('https://r.example', 't', respFetch(client)).kvGet('k')).rejects.toThrow('redis: ERR boom');
  });
  test('a null reply stays null', async () => {
    const client: RespClient = { pipeline() { return { call() { return this; }, async exec() { return [[null, null]] as [Error | null, unknown][]; } }; } };
    expect(await new UpstashStore('https://r.example', 't', respFetch(client)).kvGet('k')).toBeNull();
  });
});
