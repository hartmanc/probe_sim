// A RESP backend for the scoreboard store in tests (test-only; not shipped).
//
// UpstashStore (src/scoreboard/store.ts) talks to Redis through one injectable function: POST <url>/pipeline with a JSON
// array of commands, answered with [{result}] or [{error}]. respFetch() is that function over a real RESP client
// (ioredis): it parses the very body the store built (so the commands, the EVAL scripts with their keys and args, the
// pipelines and the expiries are byte for byte what the Upstash REST client sends) and runs the pipeline on a real Redis.
// The store itself is unchanged; no Lua is copied here.
import type { UpstashStore } from '../../store';

type FetchLike = NonNullable<ConstructorParameters<typeof UpstashStore>[2]>;

/** The slice of an ioredis client the adapter uses. */
export interface RespClient {
  pipeline(): {
    call(name: string, ...args: string[]): unknown;
    exec(): Promise<[Error | null, unknown][] | null>;
  };
}

/** Upstash's REST replies are the RESP replies as JSON: integers, bulk / status strings, null, nested arrays. */
export function respFetch(redis: RespClient): FetchLike {
  return async (_url, init) => {
    const cmds = JSON.parse(init.body) as (string | number)[][];
    const p = redis.pipeline();
    for (const c of cmds) p.call(String(c[0]), ...c.slice(1).map(String));
    const rows = (await p.exec()) ?? [];
    const out = rows.map(([err, result]) => (err ? { error: err.message } : { result: result ?? null }));
    return { ok: true, status: 200, json: async () => out };
  };
}
