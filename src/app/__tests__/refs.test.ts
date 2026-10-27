import { beforeAll, describe, expect, it } from 'vitest';
import { BOARD_LAP_ID, LapRecorder, REF_KEY, RefController, RefPref, SESSION_LAP_ID, fmtRefTime, type BoardGhost, type KVLike } from '../refs';
import { MenuModel } from '../menu';
import { createHotLap, ghostRefEntry, ghostRefOptions } from '../modes/hotlap';
import { realLapOf } from '../ghosts';
import { LapTimer, type Lap } from '../timing';
import type { GhostLap, GhostsJson } from '../physics-types';
import type { ModeContext } from '../modes/mode';
import { HotlapSim, boardKey, physicsVersion } from '../../scoreboard';
import { handleScores } from '../../scoreboard/handler';
import { MemoryStore } from '../../scoreboard/store';
import { ghostFromTrace } from '../../scoreboard/ghostlap';
import { ScoreboardClient, buildHotlapSubmission } from '../scoreboard-client';
import { autopilot, lagunaAssets } from '../../scoreboard/__tests__/fixtures';

const L = 3000, GRID = 2;
/** A constant-speed lap: 100 s at 30 m/s. */
const flat = (id: string, time: number, driver = 'D'): GhostLap => {
  const v = L / time, m = Math.floor(L / GRID);
  return { id, driver, label: `${driver} ${fmtRefTime(time)}`, kind: 'test', lap_time_s: time, t: Array.from({ length: m }, (_, i) => (i * GRID) / v), v_mps: new Array(m).fill(v) };
};
const memKV = (init: Record<string, string> = {}): KVLike & { m: Map<string, string> } => {
  const m = new Map(Object.entries(init));
  return { m, getItem: (k) => m.get(k) ?? null, setItem: (k, v) => { m.set(k, v); } };
};
const sink = () => {
  const slots = new Map<string, GhostLap>(), vis = new Map<string, boolean>();
  return {
    slots, vis,
    setSlot(slot: string, lap: GhostLap | null, visible = true) { if (lap) { slots.set(slot, lap); vis.set(lap.id, visible); } else slots.delete(slot); return null; },
    setVisible(id: string, on: boolean) { vis.set(id, on); },
  };
};
const mk = (o: { choice?: 'session' | 'board' | 'real'; real?: GhostLap | null; board?: () => Promise<BoardGhost | null> } = {}) => {
  const kv = memKV(o.choice ? { [REF_KEY]: o.choice } : {});
  const pref = new RefPref(kv);
  const cars = sink();
  const c = new RefController({ pref, real: o.real ?? null, length: L, grid: GRID, cars, loadBoard: o.board ?? (async () => null) });
  return { c, pref, cars, kv };
};

describe('RefPref (per device, localStorage)', () => {
  it('defaults to the session best, remembers a choice, ignores junk, survives a missing or throwing storage', () => {
    expect(new RefPref(memKV()).choice).toBe('session');
    const kv = memKV();
    const p = new RefPref(kv);
    let n = 0; p.onChange(() => n++);
    p.set('board'); p.set('board');
    expect(kv.m.get(REF_KEY)).toBe('board');
    expect(n).toBe(1);
    expect(new RefPref(kv).choice).toBe('board');
    expect(new RefPref(memKV({ [REF_KEY]: 'optimal' })).choice).toBe('session');
    expect(new RefPref(null).choice).toBe('session');
    const bad: KVLike = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
    const q = new RefPref(bad);
    expect(q.choice).toBe('session');
    expect(() => q.set('real')).not.toThrow();
    expect(q.choice).toBe('real');
  });
});

describe('RefController: the three references and their fallbacks', () => {
  it('session best: no ghost and no delta before a lap, the lap\'s ghost and delta after', () => {
    const { c, cars } = mk();
    expect(c.active()).toMatchObject({ kind: 'session', lap: null, trace: null, label: 'no reference lap yet' });
    c.setSession(flat(SESSION_LAP_ID, 100));
    const a = c.active();
    expect(a.label).toBe('vs session best 1:40.00');
    expect(a.trace!.tAt(1500)).toBeCloseTo(50, 6);
    expect(cars.slots.get('session')!.id).toBe(SESSION_LAP_ID);
    expect(cars.vis.get(SESSION_LAP_ID)).toBe(true);
    c.setSession(flat(SESSION_LAP_ID, 99));   // a faster one replaces it, still shown
    expect(c.active().label).toBe('vs session best 1:39.00');
    expect(cars.vis.get(SESSION_LAP_ID)).toBe(true);
    c.clearSession();
    expect(c.active().lap).toBeNull();
  });

  it('real lap: the package lap; on a track without one the choice falls back to the session best with a note', () => {
    const real = flat('driver_a_best', 119.32, 'driver A');
    const a = mk({ choice: 'real', real });
    expect(a.c.active()).toMatchObject({ kind: 'real', label: 'vs real lap 1:59.32' });
    expect(a.cars.vis.get('driver_a_best')).toBe(true);
    const b = mk({ choice: 'real', real: null });
    expect(b.c.hasReal).toBe(false);
    expect(b.c.active().label).toBe('no reference lap yet · no real lap on this track');
    b.c.setSession(flat(SESSION_LAP_ID, 100));
    expect(b.c.active().label).toBe('vs session best 1:40.00 · no real lap on this track');
  });

  it('realLapOf: the fastest real lap of the package, never the synthetic stand-ins, none on a track without one', () => {
    const g = (laps: GhostLap[]): GhostsJson => ({ track: 't', s_grid_m: 2, line: { offset_m: [] }, laps });
    const r = (id: string, kind: string, time: number): GhostLap => ({ ...flat(id, time), kind });
    expect(realLapOf(g([r('a', 'real', 130), r('b', 'real', 127), r('o', 'optimal', 118)]))!.id).toBe('b');
    expect(realLapOf(g([r('synthetic_driver', 'real', 100), r('synthetic_optimal', 'optimal', 90)]))).toBeNull();
    expect(realLapOf(g([]))).toBeNull();
  });

  it('all-time best: fetched lazily when chosen (not for the other choices), cached for the session, named in the HUD line', async () => {
    let calls = 0;
    const board = async (): Promise<BoardGhost> => { calls++; return { lap: flat(BOARD_LAP_ID, 113.71, 'Ada'), name: 'Ada', time: 113.71 }; };
    const { c, pref, cars } = mk({ board });
    await c.ensureBoard();
    expect(calls).toBe(0);                                   // session best is chosen: no request
    pref.set('board');
    expect(c.active().label).toBe('no reference lap yet · loading the all-time best…');
    await c.ensureBoard();
    expect(calls).toBe(1);
    expect(c.active()).toMatchObject({ kind: 'board', label: 'vs all-time best 1:53.71 by Ada' });
    expect(cars.vis.get(BOARD_LAP_ID)).toBe(true);
    pref.set('session'); pref.set('board'); await c.ensureBoard();
    expect(calls).toBe(1);                                   // cached
    expect(cars.vis.get(BOARD_LAP_ID)).toBe(true);
    pref.set('session');
    expect(cars.vis.get(BOARD_LAP_ID)).toBe(false);
  });

  it('all-time best with an empty board, a failed fetch or a failed rebuild falls back to the session best with a one-line note', async () => {
    const empty = mk({ choice: 'board', board: async () => null });
    empty.c.setSession(flat(SESSION_LAP_ID, 100));
    await empty.c.ensureBoard();
    expect(empty.c.active().label).toBe('vs session best 1:40.00 · no all-time best on the board yet');
    let tries = 0;
    const failing = mk({ choice: 'board', board: async () => { tries++; throw new Error('offline'); } });
    await failing.c.ensureBoard();
    expect(failing.c.active().label).toBe('no reference lap yet · all-time best unavailable');
    await failing.c.ensureBoard();                           // a failure is retried, an empty board is not
    expect(tries).toBe(2);
    expect(failing.c.active().kind).toBe('session');
  });
});

describe('the Ghost & delta menu row', () => {
  it('lists the three references; Real lap is shown disabled "(Laguna only)" without a real lap and cycling skips it', () => {
    expect(ghostRefOptions(true).map((o) => o.label)).toEqual(['Session best', 'All-time best', 'Real lap']);
    const o = ghostRefOptions(false);
    expect(o[2]).toMatchObject({ label: 'Real lap (Laguna only)', disabled: true });
    const { c, pref } = mk({ real: null });
    const m = new MenuModel({ title: 'T', entries: () => [ghostRefEntry(c)] });
    m.adjust(1); expect(pref.choice).toBe('board');
    m.adjust(1); expect(pref.choice).toBe('session');   // skipped the disabled one
    m.adjust(-1); expect(pref.choice).toBe('board');
    const { c: c2, pref: p2 } = mk({ real: flat('r', 120) });
    const m2 = new MenuModel({ title: 'T', entries: () => [ghostRefEntry(c2)] });
    m2.adjust(1); m2.adjust(1); expect(p2.choice).toBe('real');
  });
});

describe('hot-lap mode: the delta follows the reference in force', () => {
  const setup = (choice: 'session' | 'board' | 'real', real: GhostLap | null) => {
    const { c, pref, cars } = mk({ choice, real });
    let now = 0, s = 0;
    const timer = new LapTimer(L);
    const names: string[] = [];
    const ctx = {
      timer, track: { length_m: L, corners: [] }, refs: c, ghostData: { s_grid_m: GRID },
      ghosts: { group: { visible: false }, ghosts: [], fastestReal: () => null, setVisible() { /* */ } },
      hud: { setRefName: (n: string) => names.push(n), hideCorners() { /* */ }, setBanner() { /* */ }, showCorners() { /* */ } },
      simTime: () => now, s: () => s, vehicle: { state: { speed: 30 } },
      setScheduleLap() { /* */ }, rollingStart() { /* */ }, toast() { /* */ },
    } as unknown as ModeContext;
    const mode = createHotLap(ctx);
    mode.start();
    return { mode, timer, c, pref, cars, names, at: (t: number, pos: number) => { now = t; s = pos; } };
  };
  it('no reference: no delta; with the session best: delta = current - t_ref(s); the panel names the reference', () => {
    const h = setup('session', null);
    h.timer.started = true; h.timer.lapStart = 0;
    h.at(10, 300);
    expect(h.mode.hud().delta).toBeNull();
    expect(h.names.at(-1)).toBe('no reference lap yet');
    h.c.setSession(flat(SESSION_LAP_ID, 100));            // 30 m/s: 300 m is at 10 s
    h.at(10.5, 300);
    expect(h.mode.hud().delta).toBeCloseTo(0.5, 6);
    expect(h.names.at(-1)).toBe('vs session best 1:40.00');
  });
  it('the real lap and the session best give different deltas at the same point', () => {
    const real = flat('driver_a_best', 90);               // 33.3 m/s: 300 m at 9 s
    const h = setup('real', real);
    h.timer.started = true; h.timer.lapStart = 0;
    h.c.setSession(flat(SESSION_LAP_ID, 100));
    h.at(10.5, 300);
    expect(h.mode.hud().delta).toBeCloseTo(1.5, 6);
    expect(h.names.at(-1)).toBe('vs real lap 1:30.00');
    h.pref.set('session');
    expect(h.mode.hud().delta).toBeCloseTo(0.5, 6);
  });
  it('the pause entries carry the choice row', () => {
    const h = setup('session', null);
    expect(h.mode.pauseEntries().some((e) => e.id === 'ghostRef')).toBe(true);
  });
});

describe('the session best from a driven lap, and the all-time best through the API', () => {
  let lap: Lap, rec: LapRecorder, built: GhostLap | null, trace: ReturnType<HotlapSim['trace']>, assets: ReturnType<typeof lagunaAssets>;
  beforeAll(() => {
    assets = lagunaAssets();
    const sim = new HotlapSim(assets, { record: true });
    const drive = autopilot(sim);
    rec = new LapRecorder();
    for (let i = 0; i < 400_000; i++) {
      const ev = sim.step(drive);
      // the mode's step(): after every physics step, before the lap event is handled
      rec.feed(sim.timer.started, sim.timer.lapNumber, sim.timer.current(sim.simTime), sim.s, sim.vehicle.state.speed);
      if (ev && ev !== 'start') {
        lap = ev; trace = sim.trace();
        built = rec.finish(ev.time, assets.track.length_m, assets.ghosts.s_grid_m);
        break;
      }
    }
  }, 120_000);

  it('the recorded lap becomes a ghost that ends at the lap time and runs at the car\'s speeds', () => {
    expect(built).not.toBeNull();
    const g = built!;
    expect(g.lap_time_s).toBe(lap.time);
    expect(g.t[0]).toBe(0);
    for (let i = 1; i < g.t.length; i++) expect(g.t[i]).toBeGreaterThan(g.t[i - 1]);
    expect(g.t.at(-1)!).toBeGreaterThan(lap.time - 1);
    expect(g.t.at(-1)!).toBeLessThanOrEqual(lap.time);
    expect(g.label).toBe(`You ${fmtRefTime(lap.time)}`);
  });

  it('the live recorder and the trace rebuild agree: the same lap gives the same t(s) within a tick', () => {
    const re = ghostFromTrace(assets, trace, lap.n, { id: 'x', driver: 'x', label: () => 'x' })!;
    expect(re.time).toBe(lap.time);
    const a = built!.t, b = re.lap.t;
    expect(b).toHaveLength(a.length);
    let worst = 0;
    for (let i = 0; i < a.length; i++) worst = Math.max(worst, Math.abs(a[i] - b[i]));
    expect(worst).toBeLessThan(0.02);
  }, 120_000);

  it('end to end: post the lap, GET its ghost with the client, rebuild it: the board\'s time to the millisecond', async () => {
    const store = new MemoryStore();
    const physics = physicsVersion(assets.carJson, assets.track.length_m);
    const fetchFn = (url: string, init?: RequestInit) => handleScores(new Request(new URL(url, 'http://local.test').toString(), init), { store, assets: async () => assets, physics: async () => physics });
    const client = new ScoreboardClient({ base: '/api/scores', fetch: fetchFn, storage: memKV() });
    client.setName('Ada');
    const board = boardKey('hotlap', 'laguna_seca', 'probe_gt', physics);
    const none = await client.ghost(board);
    expect(none.ok).toBe(false);
    if (!none.ok) expect(none.status).toBe(404);
    const posted = await client.submit(buildHotlapSubmission({ lap, trace: JSON.parse(JSON.stringify(trace)), name: 'Ada', input: 'pad' }));
    expect(posted.ok).toBe(true);
    const r = await client.ghost(board);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const top = await client.board(board);
    const boardTime = top.ok ? top.value.entries[0].score : NaN;
    expect(r.value.name).toBe('Ada');
    const g = ghostFromTrace(assets, r.value.trace, r.value.lap, { id: BOARD_LAP_ID, driver: r.value.name, label: (t) => `${r.value.name} ${fmtRefTime(t)}` })!;
    expect(Math.abs(g.time - boardTime)).toBeLessThan(0.001);
    expect(g.lap.label).toBe(`Ada ${fmtRefTime(boardTime)}`);
  }, 180_000);
});
