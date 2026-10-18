import { beforeAll, describe, expect, it } from 'vitest';
import { HotlapSim, replayTrace, boardKey, physicsVersion, type InputTrace } from '../../scoreboard';
import { handleScores } from '../../scoreboard/handler';
import { MemoryStore } from '../../scoreboard/store';
import { autopilot, lagunaAssets } from '../../scoreboard/__tests__/fixtures';
import { HotlapLoop, type LiveSample } from '../modes/hotlap';
import type { Lap } from '../timing';
import {
  ScoreboardClient, apiBase, buildHotlapSubmission, checkHotlap, describeFailure, fmtMetres, isBetter, lsPbKey,
  setBoardContext, submitRace, LS_NAME, type KV,
} from '../scoreboard-client';
import { moveGridCursor } from '../scoreboard-ui';

const memKV = (): KV & { m: Map<string, string> } => {
  const m = new Map<string, string>();
  return { m, getItem: (k) => m.get(k) ?? null, setItem: (k, v) => { m.set(k, v); } };
};

/**
 * Drive one lap through the live loop's code path (HotlapLoop, variable frame dt, latched shifts, settings
 * changed between frames through the sim) with the scripted autopilot standing in for the device.
 */
function liveLap(): { lap: Lap; trace: InputTrace; tag: string } {
  const assets = lagunaAssets();
  const sim = new HotlapSim(assets, { record: true, autoShift: true });
  let drive = autopilot(sim);
  let tags = 0;
  const loop = new HotlapLoop(sim, (): LiveSample => {
    const r = drive();
    tags++;
    return { steer: r.steer, throttle: r.throttle, brake: r.brake, handbrake: !!r.handbrake, tag: tags % 3 === 0 ? 'keys' : 'pad' };
  });
  let got: { lap: Lap; trace: InputTrace; tag: string } | null = null;
  loop.onLap = (lap, tag) => { got = { lap, trace: JSON.parse(JSON.stringify(sim.trace())), tag }; };
  loop.halt = () => got !== null;
  // a short false start, then the reset the menu's Restart / R would do: the recording must restart with it
  for (let f = 0; f < 30; f++) loop.advance(0.0167);
  loop.reset();
  drive = autopilot(sim);
  const dts = [0.0167, 0.0333, 0.0071, 0.05, 0.0166, 0.0123];
  for (let f = 0; f < 20000 && !got; f++) {
    // settings flipped between frames (the pause menu / X button), recorded at the next sample
    if (f === 300) sim.abs = !sim.abs;
    if (f === 700) sim.abs = !sim.abs;
    if (f === 900) sim.setRef(null);
    if (f === 1500) sim.setRef(assets.ghosts.laps.find((l) => l.kind === 'real')!.id);
    if (f === 2000) { loop.shiftDown(); }
    if (f === 2003) { loop.shiftUp(); }
    loop.advance(dts[f % dts.length]);
  }
  if (!got) throw new Error('no lap');
  return got;
}

describe('live hot-lap loop → trace → replay', () => {
  let res!: ReturnType<typeof liveLap>;
  beforeAll(() => { res = liveLap(); }, 120_000);
  it('a lap recorded by HotlapLoop replays to the identical lap time', () => {
    const { lap, trace } = res;
    expect(lap.valid).toBe(true);
    expect(trace.rows[0][0]).toBe(0);
    expect(trace.ref.length).toBeGreaterThanOrEqual(3); // default → none → a real lap
    const rep = replayTrace(lagunaAssets(), trace, lap.n);
    expect(rep.lap).not.toBeNull();
    expect(rep.lap!.time).toBe(lap.time);
    expect(rep.lap!.valid).toBe(true);
  }, 120_000);
  it('tags the lap with the most used input type', () => {
    expect(res.tag).toBe('pad');
  });
  it('the submission passes the server handler (replayed, stored, ranked)', async () => {
    const assets = lagunaAssets();
    const store = new MemoryStore();
    const physics = physicsVersion(assets.carJson, assets.track.length_m);
    const fetchFn = (url: string, init?: RequestInit) =>
      handleScores(new Request(new URL(url, 'http://local.test').toString(), init), {
        store, assets: async () => assets, physics: async () => physics,
      });
    const kv = memKV();
    const client = new ScoreboardClient({ base: '/api/scores', fetch: fetchFn, storage: kv });
    expect(client.setName('  Coby   H ')).toBe('Coby H');
    const sub = buildHotlapSubmission({ lap: res.lap, trace: res.trace, name: client.name!, input: 'pad', device: client.device });
    const board = boardKey('hotlap', 'laguna_seca', 'probe_gt', physics);
    const r = await client.submit(sub);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.value.board).toBe(board);
    expect(r.value.rank).toBe(1);
    expect(client.pb(board)).toBeCloseTo(res.lap.time, 2);
    const b = await client.board(board);
    expect(b.ok && b.value.entries[0].name).toBe('Coby H');
    expect(b.ok && b.value.you?.rank).toBe(1);
    expect(client.offline).toBe(false);
  }, 120_000);
});

describe('scoreboard client', () => {
  it('api base: same origin by default, ?api= override', () => {
    expect(apiBase('')).toBe('/api/scores');
    expect(apiBase('?api=http://localhost:3000')).toBe('http://localhost:3000/api/scores');
    expect(apiBase('?api=http://localhost:3000/api/scores/')).toBe('http://localhost:3000/api/scores');
    expect(apiBase('?api=javascript:alert(1)')).toBe('/api/scores');
  });

  it('offline: network errors and non-JSON answers', async () => {
    const c1 = new ScoreboardClient({ base: '/x', fetch: async () => { throw new TypeError('Failed to fetch'); }, storage: null });
    const r1 = await c1.board('hotlap:laguna_seca:probe_gt:abc');
    expect(r1.ok).toBe(false);
    expect(!r1.ok && r1.offline).toBe(true);
    expect(c1.offline).toBe(true);
    const c2 = new ScoreboardClient({ base: '/x', fetch: async () => new Response('<html>', { status: 200, headers: { 'content-type': 'text/html' } }), storage: null });
    const r2 = await c2.info();
    expect(!r2.ok && r2.offline).toBe(true);
    if (!r1.ok) expect(describeFailure(r1)).toBe('Scoreboard offline');
  });

  it('422 reasons and the stale-page case', async () => {
    const c = new ScoreboardClient({
      base: '/x', storage: null,
      fetch: async () => new Response(JSON.stringify({ ok: false, error: 'rejected', reasons: ['physics version mismatch: reload the game'] }), { status: 422, headers: { 'content-type': 'application/json' } }),
    });
    const r = await c.info();
    expect(r.ok).toBe(false);
    if (!r.ok) expect(describeFailure(r)).toMatch(/reload/);
  });

  it('personal bests per board, better only; storage failures are harmless', () => {
    const kv = memKV();
    const c = new ScoreboardClient({ base: '/x', fetch: async () => new Response(), storage: kv });
    c.savePb('b1', 'hotlap', 120.5);
    c.savePb('b1', 'hotlap', 121);
    expect(c.pb('b1')).toBe(120.5);
    c.savePb('r1', 'race', 9000); c.savePb('r1', 'race', 8000);
    expect(kv.m.get(lsPbKey('r1'))).toBe('9000');
    expect(c.name).toBeNull();
    expect(c.setName('x'.repeat(13))).toBeNull();
    const broken = new ScoreboardClient({ base: '/x', storage: { getItem: () => { throw new Error('denied'); }, setItem: () => { throw new Error('denied'); } } });
    expect(broken.name).toBeNull();
    expect(broken.pb('b1')).toBeNull();
    expect(broken.setName('Ok')).toBe('Ok');
    expect(isBetter('hotlap', 1, 2) && isBetter('race', 2, 1)).toBe(true);
  });

  it('which laps can be submitted', () => {
    const lap = (n: number, time: number, valid = true): Lap => ({ n, time, valid, speedTrace: new Float32Array(1) });
    const base = { pb: 130, offered: null, steps: 200_000, rows: 10_000, assetsOk: true };
    expect(checkHotlap(lap(2, 129), base)).toEqual({ best: true, submittable: true, reason: undefined });
    expect(checkHotlap(lap(2, 131), base).best).toBe(false);
    expect(checkHotlap(lap(2, 129), { ...base, offered: 128.5 }).best).toBe(false);
    expect(checkHotlap(lap(7, 129), base).reason).toMatch(/laps 1–6/);
    expect(checkHotlap(lap(2, 129, false), base).submittable).toBe(false);
    expect(checkHotlap(lap(2, 129), { ...base, assetsOk: false }).reason).toMatch(/stand-in/);
    expect(checkHotlap(lap(3, 129), { ...base, steps: 800_000 }).reason).toMatch(/too long/);
  });

  it('submitRace posts a plausibility-checked race entry for the future race mode', async () => {
    const kv = memKV();
    kv.m.set(LS_NAME, 'Racer');
    let body: Record<string, unknown> | null = null;
    const client = new ScoreboardClient({
      base: '/x', storage: kv,
      fetch: async (_u, init) => {
        body = JSON.parse(String(init?.body));
        return new Response(JSON.stringify({ ok: true, board: 'race:laguna_seca:probe_gt:p:ai-1', rank: 4, best: 30000, improved: true }), { headers: { 'content-type': 'application/json' } });
      },
    });
    setBoardContext({ client, track: 'laguna_seca', car: 'probe_gt', physics: 'p', input: () => 'pad', assetsOk: true, offer: undefined });
    expect((await submitRace({ metres: 30000, laps: 8, aiVersion: 'ai-1', seed: 7, position: 3 })).status).toBe('submitted');
    expect(body).toMatchObject({ mode: 'race', ai_version: 'ai-1', metres: 30000, laps: 8, name: 'Racer', input: 'pad', position: 3, replay: { seed: 7 } });
    expect((await submitRace({ metres: 20000, laps: 5, aiVersion: 'ai-1' })).status).toBe('not-best');
    expect(fmtMetres(30000, 8, 3560)).toBe('8L +1,520 m');
  });

  it('name grid cursor', () => {
    const rows = [10, 10, 10, 10, 4];
    expect(moveGridCursor(rows, 0, 0, 'left')).toEqual([0, 9]);
    expect(moveGridCursor(rows, 3, 9, 'down')).toEqual([4, 3]);
    expect(moveGridCursor(rows, 4, 3, 'down')).toEqual([0, 9]);
    expect(moveGridCursor(rows, 0, 0, 'up')).toEqual([4, 0]);
  });
});

describe('new-best prompt: pad → keyboard switch (owner bug: the prompt vanished when typing after a pad lap)', () => {
  // the lap was driven with the pad (input.source 'gamepad'); the owner then types on the keyboard
  const prompt = { promptOpen: true, editorOpen: false, fieldFocused: false };
  it('letters on the prompt open the name editor instead of reaching input.ts (O = close menu, WASD = move)', async () => {
    const { routeScoreboardKey } = await import('../scoreboard-ui');
    for (const key of ['C', 'o', 'b', 'y', 'O', 'w', 'a', 's', 'd', 'm', 'h', 'k', '1', 'é']) {
      expect(routeScoreboardKey(prompt, { key })).toBe('open-editor');
    }
    expect(routeScoreboardKey(prompt, { key: 'Escape' })).toBe('skip');
    expect(routeScoreboardKey(prompt, { key: 'Escape', repeat: true })).toBe('pass');
    for (const key of ['ArrowDown', 'Enter', ' ', 'Shift']) expect(routeScoreboardKey(prompt, { key })).toBe('pass');
    expect(routeScoreboardKey(prompt, { key: 'r', metaKey: true })).toBe('pass');
  });
  it('in the editor, keys type into the name even when the pad grid had the focus', async () => {
    const { routeScoreboardKey } = await import('../scoreboard-ui');
    const grid = { promptOpen: true, editorOpen: true, fieldFocused: false };
    expect(routeScoreboardKey(grid, { key: 'o' })).toBe('type');
    expect(routeScoreboardKey(grid, { key: 'Backspace' })).toBe('delete');
    expect(routeScoreboardKey(grid, { key: 'Escape' })).toBe('cancel');
    expect(routeScoreboardKey(grid, { key: 'Enter' })).toBe('commit');
    expect(routeScoreboardKey({ ...grid, fieldFocused: true }, { key: 'o' })).toBe('pass'); // native typing
  });
  it('pad B cancels only on a deliberate press of an empty name', async () => {
    const { editorBack, EDITOR_SETTLE_MS: W } = await import('../scoreboard-ui');
    expect(editorBack(100, 0, 0, true)).toBe('ignore');            // stale press right after opening
    expect(editorBack(W + 10, 0, 0, false)).toBe('delete');
    expect(editorBack(W + 50, 0, W + 10, true)).toBe('ignore');    // mashing B to clear does not cancel
    expect(editorBack(3 * W, 0, W + 10, true)).toBe('cancel');
  });
  it('the prompt card is not closable by Back / B (only Submit / Skip)', async () => {
    const { MenuModel } = await import('../menu');
    const m = new MenuModel({ title: 'NEW BEST', entries: () => [{ kind: 'action', id: 'sbSkip', label: 'Skip', run: () => {} }] }, false);
    expect(m.nav('back')).toBe('none');
  });
});
