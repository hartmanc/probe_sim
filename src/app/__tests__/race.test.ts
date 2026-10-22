// Race mode integration: construction with the real data files, the director stepping the HotlapSim car,
// restart / dispose, the placeholder car, the draw cap, the HUD mapping and the results → scoreboard payload.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { HotlapSim } from '../../scoreboard';
import { lagunaAssets, autopilot } from '../../scoreboard/__tests__/fixtures';
import { HotlapLoop } from '../modes/hotlap';
import { carSound, createRace, modelQueue, silentEngine, newSeed, parseRaceOverrides, raceAiConfig, raceResultFor, RACE_LAPS, type RaceDeps } from '../modes/race';
import type { ModeContext, RaceServices } from '../modes/mode';
import { GLOBAL_IDENTITY, loadIdentityWithFallback, normaliseModelRows, type FieldData } from '../loader';
import { describeAiCar, fieldKey, modelKey, parseIdentity, resolveCarType, type PaceJson } from '../../physics/ai/field';
import { TRACKS } from '../../scoreboard/config';
import { FieldCars, buildPlaceholderCar, identityColor, selectDrawn, triangleCount, PROBE_DIMS, type FieldCarInfo } from '../field-cars';
import { raceHudView, resultRows } from '../race-hud';
import type { RaceHud, ResultRow } from '../../physics/ai/race';
import { ScoreboardClient, setBoardContext, submitRace, type KV } from '../scoreboard-client';
import type { VehicleState } from '../physics-types';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const readJson = (p: string) => JSON.parse(readFileSync(pub + p, 'utf8'));
const fieldData = (): FieldData => ({
  pace: readJson('cars/field/pace.json'), identity: readJson('cars/field/identity.json'),
  models: readJson('cars/field/models.json').cars, missing: [],
});

function harness(search = '?seed=42&laps=2', rand: () => number = () => 0.5, field: () => FieldData = fieldData, loadModel: RaceDeps['loadModel'] = async () => null) {
  const sim = new HotlapSim(lagunaAssets(), { record: true, autoShift: true });
  const pilot = { fn: autopilot(sim, 0.35) };
  const loop = new HotlapLoop(sim, () => ({ ...pilot.fn(), handbrake: false, tag: 'keys' as const }));
  const scene = new THREE.Scene();
  const log: string[] = [];
  const services: RaceServices = {
    sim, scene, search, quality: { maxAiCarsDrawn: 20, shadows: false, aiShadowCasters: 0 },
    menu: { isOpen: false, show: () => log.push('menu:show'), close: () => {}, refresh: () => {} } as unknown as RaceServices['menu'],
    mainMenu: () => log.push('main'), impact: () => {},
  };
  const ctx = {
    track: sim.assets.track, timer: sim.timer,
    ghosts: { group: { visible: true }, fastestReal: () => null },
    hud: { hideCorners: () => {}, setRefName: () => {}, setBanner: () => {}, toast: (m: string) => log.push(`toast:${m}`) },
    simTime: () => sim.simTime, s: () => sim.s,
    rollingStart: () => loop.reset(),
    recoverAt: () => log.push('recover'),
    setScheduleLap: () => {},
    toast: (m: string) => log.push(`toast:${m}`),
    race: services,
  } as unknown as ModeContext;
  const deps: RaceDeps = { loadField: field, loadModel, random: rand, dom: false };
  const race = createRace(ctx, deps);
  loop.onStep = () => race.step(0.001);
  return { sim, loop, scene, race, log, pilot };
}

describe('race mode with the real data files', () => {
  it('builds the director around the HotlapSim car, steps it, restarts with a new seed, disposes', () => {
    const { sim, loop, scene, race, pilot } = harness();
    race.start();
    const d = race.director!;
    expect(d).toBeTruthy();
    expect(race.seed).toBe(42);
    expect(race.laps).toBe(2);
    expect(d.cars.length).toBe(45);
    expect(d.player.vehicle).toBe(sim.vehicle);           // the app's car, not a copy
    expect(d.player.surface).toBe(sim.surface);
    expect(sim.record).toBe(false);
    expect(sim.stepVehicle).toBeTypeOf('function');
    const h0 = d.hud();
    expect(h0.phase).toBe('formation');
    expect(h0.position).toBe(d.player.grid);              // the player starts in its (seeded, shuffled) grid slot
    expect(h0.lapsTotal).toBe(2);
    // AI rigs: one placeholder per AI car, in the scene
    expect(race.fieldCars!.size).toBe(44);
    expect(scene.getObjectByName('field_cars')).toBeTruthy();
    // 1 s of play through the live loop: the director steps every car, the HotlapSim keeps its clock
    const x0 = sim.vehicle.state.pos[0];
    for (let k = 0; k < 20; k++) { loop.advance(0.05); race.frame(0.05, k * 50); }
    expect(sim.stepIndex).toBeGreaterThanOrEqual(999);  // frame dt accumulation (0.05 × 20 in floats)
    expect(d.time).toBeCloseTo(sim.stepIndex * 0.001, 9); // exactly one director step per HotlapSim step
    expect(sim.vehicle.state.pos[0]).not.toBe(x0);
    const ai = d.cars.find((c) => !c.isPlayer)!;
    expect(ai.vehicle.state.speed).toBeGreaterThan(4);
    expect(race.fieldCars!.drawn).toBe(20);               // the draw cap
    // determinism: the same seed and inputs give the same state
    const posA = [...sim.vehicle.state.pos];
    const b = harness();
    b.race.start();
    for (let k = 0; k < 20; k++) b.loop.advance(0.05);
    expect([...b.sim.vehicle.state.pos]).toEqual(posA);
    // restart: new seed, new director, the car back on the grid
    pilot.fn = autopilot(sim, 0.35);
    race.restart();
    expect(race.seed).not.toBe(42);
    expect(race.director).not.toBe(d);
    expect(race.director!.time).toBe(0);
    expect(race.director!.player.vehicle).toBe(sim.vehicle);
    // dispose: the hot lap gets its plain step and recording back
    race.dispose();
    expect(sim.stepVehicle).toBeNull();
    expect(sim.record).toBe(true);
    expect(scene.getObjectByName('field_cars')).toBeUndefined();
  }, 60000);

  it('app-side violations (pit-exit cones) black-flag with the escalation and a 2 s debounce', () => {
    const { race } = harness();
    race.start();
    const d = race.director!;
    expect(d.reportViolation('pit_exit_cones')).toBe(true);
    expect(d.reportViolation('pit_exit_cones')).toBe(false);  // still on the line
    let h = d.hud();
    expect(h.penalties.count).toBe(1);
    expect(h.penalties.lastReason).toBe('crossed the pit-exit cones');
    expect(h.flag).toBe('black');
    for (let k = 0; k < 2100; k++) d.step(0.001);
    expect(d.reportViolation('pit_exit_cones')).toBe(true);
    h = d.hud();
    expect(h.penalties.count).toBe(2);
    expect(h.penalties.pending).toEqual([60]);
    const v = raceHudView(h, { teamOf: () => '', metres: 0, out: null });
    expect(v.flag).toBe('black');
    expect(v.flagTitle).toContain('crossed the pit-exit cones');
    expect(v.flagDetail).toMatch(/60 s stop-and-go in the pit lane/);
    race.dispose();
  }, 60000);
});

describe('overrides and seeds', () => {
  it('parses ?seed= and ?laps=', () => {
    expect(parseRaceOverrides('?seed=123&laps=2')).toEqual({ seed: 123, laps: 2, devSubmit: false });
    expect(parseRaceOverrides('?laps=99&seed=abc')).toEqual({ seed: null, laps: null, devSubmit: false });
    expect(parseRaceOverrides('')).toEqual({ seed: null, laps: null, devSubmit: false });
    expect(parseRaceOverrides('?devsubmit=1').devSubmit).toBe(true);
    expect(RACE_LAPS).toBe(5);
  });
  it('new seeds are positive integers', () => {
    expect(newSeed(() => 0)).toBe(1);
    const s = newSeed(() => 0.999999);
    expect(Number.isInteger(s) && s > 0 && s < 1e9).toBe(true);
  });
});

describe('field cars', () => {
  it('placeholder car: probe.glb node names, about 300 triangles, wheels at the given hubs', () => {
    const dims = { ...PROBE_DIMS, length: 4.0, width: 1.6, wheelbase: 2.3, trackFront: 1.4, trackRear: 1.38, tyreRadius: 0.3 };
    const car = buildPlaceholderCar('711', '#7a5a3a', dims, null);
    for (const n of ['body', 'wheel_fl', 'wheel_fr', 'wheel_rl', 'wheel_rr', 'number_boards']) expect(car.getObjectByName(n)).toBeTruthy();
    const tris = triangleCount(car);
    expect(tris).toBeGreaterThan(150);
    expect(tris).toBeLessThan(1200);
    const fl = car.getObjectByName('wheel_fl')!.position;
    expect([fl.x, fl.y, fl.z]).toEqual([0.7, 0.3, 1.15]);
    const rr = car.getObjectByName('wheel_rr')!.position;
    expect([rr.x, rr.z]).toEqual([-0.69, -1.15]);
  });
  it('identity colours', () => {
    expect(identityColor({ colors: { primary: '#7a5a3a' } })).toBe('#7a5a3a');
    expect(identityColor({ colors: ['#112233'] })).toBe('#112233');
    expect(identityColor({ color: '#abcdef' })).toBe('#abcdef');
    expect(identityColor({ colors: { primary: 'red' } })).toBeNull();
    expect(identityColor(null)).toBeNull();
  });
  it('draw cap: nearest by track distance, wrapped around the lap, player skipped', () => {
    const L = 3600;
    const s = [100, 3550, 200, 1800, 120, 90];
    expect(selectDrawn(s, 100, L, 3, 0)).toEqual([5, 4, 2]);        // 10, 20, 100 m
    expect(selectDrawn(s, 100, L, 99, 0)).toEqual([5, 4, 2, 1, 3]); // #1 at 3550 m is 150 m behind (wrapped)
    expect(selectDrawn(s, 100, L, 0, 0)).toEqual([]);
  });
  it('FieldCars draws at most maxDrawn and lets only the nearest cast shadows', () => {
    const n = 30;
    const infos: FieldCarInfo[] = Array.from({ length: n }, (_, i) => ({ number: String(i + 1), idx: i + 1, color: '#336699', dims: PROBE_DIMS, physicsRadius: 0.316 }));
    const fc = new FieldCars({ maxDrawn: 20, shadowCasters: 6 });
    fc.build(infos);
    const state = (x: number): VehicleState => ({
      pos: [x, 0, 0], quat: [0, 0, 0, 1], vel: [0, 0, 0], angVel: [0, 0, 0], rpm: 0, gear: 1, speed: 0, gLat: 0, gLong: 0, throttleOut: 0,
      wheels: [0, 1, 2, 3].map(() => ({ pos: [x, 0, 0.3], spinAngle: 0, steer: 0, compression: 0, omega: 0, slipRatio: 0, slipAngle: 0, load: 0, onTrack: true })),
    }) as unknown as VehicleState;
    const states = Array.from({ length: n + 1 }, (_, i) => state(i * 10));
    const s = states.map((_, i) => i * 10);
    fc.update(states, s, 0, 3600);
    expect(fc.drawn).toBe(20);
    let visible = 0, casting = 0;
    fc.group.children.forEach((r) => { if (r.visible) visible++; let c = false; r.traverse((o) => { if ((o as THREE.Mesh).isMesh && o.castShadow) c = true; }); if (c) casting++; });
    expect(visible).toBe(20);
    expect(casting).toBe(6);
    expect(fc.group.getObjectByName('ai_1')!.visible).toBe(true);     // 10 m away
    expect(fc.group.getObjectByName('ai_30')!.visible).toBe(false);   // 300 m away
    // a real model replaces a placeholder
    const tpl = buildPlaceholderCar('x', '#ffffff', PROBE_DIMS, null);
    expect(fc.useModel('3', tpl, 0.31)).toBe(true);
    expect(fc.kindOf('3')).toBe('model');
    expect(fc.modelCount).toBe(1);
    fc.dispose();
  });
});

describe('race HUD mapping', () => {
  const base = (): RaceHud => ({
    phase: 'green', flag: 'green', time: 100, lap: 3, lapsTotal: 10, raced: 0, position: 12, carsTotal: 45, classPosition: 4, className: 'B',
    gapAhead: { number: '711', seconds: 1.234, metres: 40 }, gapBehind: { number: '20', seconds: 0.8, metres: 20 },
    lastLap: 128.5, bestLap: 127.25,
    penalties: { count: 0, pending: [], servingRemaining: 0, inBox: false, fastForward: false, lapsToServe: null, lastReason: null, lastAt: -1e9, ejected: false },
    message: null, results: null,
  });
  const info = { teamOf: (n: string) => (n === '711' ? 'Eyesore Racing' : 'NSF Racing'), metres: 7400, out: null };
  it('green running: no banner, position, lap, gaps with team names, metres', () => {
    const v = raceHudView(base(), info);
    expect(v.flag).toBe('none');
    expect(v.position).toBe('P12/45');
    expect(v.lap).toBe('LAP 3/10');
    expect(v.ahead).toBe('▲ #711 Eyesore Racing 1.2 s');
    expect(v.behind).toBe('▼ #20 NSF Racing 0.8 s');
    expect(v.metres).toBe('7,400 m');
    expect(v.lastLap).toBe('2:08.500');
  });
  it('formation, green message, chequered', () => {
    expect(raceHudView({ ...base(), phase: 'formation', flag: 'yellow' }, info).flagTitle).toBe('DOUBLE YELLOW · formation');
    const g = raceHudView({ ...base(), message: 'GREEN GREEN GREEN' }, info);
    expect([g.flag, g.flagTitle]).toEqual(['green', 'GREEN FLAG']);
    expect(raceHudView({ ...base(), phase: 'chequered', flag: 'chequered' }, info).flag).toBe('chequered');
    expect(raceHudView({ ...base(), message: 'BLACK FLAG: contact with #49 — warning' }, info).flag).toBe('black');
  });
  it('black flags: warning, pending stop-and-go, serving, ejected, out', () => {
    const pen = (p: Partial<RaceHud['penalties']>) => ({ ...base(), flag: 'black' as const, penalties: { ...base().penalties, ...p } });
    const w = raceHudView(pen({ count: 1, lastReason: 'contact with #711', lastAt: 99 }), info);
    expect(w.flagTitle).toBe('BLACK FLAG · contact with #711');
    expect(w.flagDetail).toMatch(/Warning/);
    const p = raceHudView(pen({ count: 2, pending: [60], servingRemaining: 60, lapsToServe: 1.75, lastReason: 'four wheels off' }), info);
    expect(p.flagDetail).toBe('Serve a 60 s stop-and-go in the pit lane (penalty box) · 1.8 laps left to serve it');
    expect(p.penalties).toBe('Black flags 2 · 60 s to serve');
    const s = raceHudView(pen({ count: 2, pending: [60], servingRemaining: 41.2, inBox: true, lapsToServe: 1 }), info);
    expect(s.flagDetail).toBe('Serving stop-and-go: 42 s — stay stopped, get ready to go');
    const f = raceHudView(pen({ count: 2, pending: [60], servingRemaining: 41.2, inBox: true, fastForward: true, lapsToServe: 1 }), info);
    expect(f.flagDetail).toBe('Serving stop-and-go: 42 s — car held, time ×10');
    const e = raceHudView(pen({ count: 5, ejected: true, lastReason: 'x' }), info);
    expect(e.flagTitle).toBe('BLACK FLAG · EJECTED');
    const o = raceHudView(base(), { ...info, out: 'Launched into space' });
    expect([o.flag, o.flagTitle]).toEqual(['black', 'OUT OF THE RACE']);
  });
});

describe('results → scoreboard', () => {
  const rows: ResultRow[] = [
    { position: 1, number: '711', team: 'Eyesore Racing', class: 'A', metres: 36_020.4, laps: 10.006, lapsCompleted: 10, bestLap: 108, time: 1130.2, status: 'running', player: false },
    { position: 2, number: '619', team: 'Probe', class: 'B', metres: 35_111.26, laps: 9.75, lapsCompleted: 9, bestLap: 121, time: null, status: 'running', player: true },
  ];
  it('builds the race payload and posts it through submitRace', async () => {
    // classified short of the full distance: distance is the score, not a finished race
    const res = raceResultFor(resultRows(rows, null), { seed: 4242, aiVersion: 2, finished: true })!;
    expect(res).toEqual({ metres: 35111.3, laps: 9, aiVersion: '2', seed: 4242, position: 2, finished: false });
    // the winner: all laps done, the race time is the score
    const win = raceResultFor(resultRows(rows.map((r) => (r.player ? { ...r, position: 1, lapsCompleted: 10, metres: 36_100, time: 1180.5 } : { ...r, position: 2 })), null), { seed: 4242, aiVersion: 2, finished: true })!;
    expect(win).toMatchObject({ laps: 10, position: 1, finished: true, time: 1180.5 });
    // launched: the distance at the launch, not finished
    const out = raceResultFor(resultRows(rows, { metres: 5000 }), { seed: 1, aiVersion: 2, finished: false })!;
    expect([out.metres, out.finished]).toEqual([5000, false]);

    const mem = new Map<string, string>();
    const kv: KV = { getItem: (k) => mem.get(k) ?? null, setItem: (k, v) => { mem.set(k, v); } };
    let posted: any = null;
    const fetchFn = async (_u: string, init?: RequestInit) => {
      posted = JSON.parse(String(init!.body));
      return new Response(JSON.stringify({ ok: true, board: 'b', rank: 1, improved: true }), { status: 200, headers: { 'content-type': 'application/json' } });
    };
    const client = new ScoreboardClient({ base: '/api/scores', fetch: fetchFn as any, storage: kv });
    client.setName('COBY');
    setBoardContext({ client, track: 'laguna_seca', car: 'probe_gt', physics: 'p1', input: () => 'keys', assetsOk: true, raceAiVersion: '2', offer: undefined });
    const o = await submitRace(res);
    expect(o.status).toBe('submitted');
    expect(posted).toMatchObject({ mode: 'race', track: 'laguna_seca', car: 'probe_gt', ai_version: '2', name: 'COBY', metres: 35111.3, laps: 9, position: 2, finished: false, replay: { seed: 4242 } });
  });
});

describe('per-track AI race parameters (TRACKS[id].ai → RaceConfig)', () => {
  it('Sonoma carries its headway, pass-lane margin and grip-capped lane changes; Laguna the defaults', () => {
    expect(raceAiConfig('sonoma')).toEqual({ followScale: 1.4, laneMargin: 0.85, shiftGrip: 1 });
    expect(raceAiConfig('laguna_seca')).toEqual({ followScale: 1, laneMargin: 1, shiftGrip: 0 });
  });
});

describe('per-event fields: identity / model by field key (id, else number)', () => {
  const lagIdent = parseIdentity(readJson('cars/field/identity.json'));
  const bw: PaceJson = readJson('cars/field/buttonwillow/pace.json');

  it('fieldKey and parseIdentity: id first, number as the fallback', () => {
    expect(fieldKey({ number: '711' })).toBe('711');
    expect(fieldKey({ id: '711_bw', number: '711' })).toBe('711_bw');
    expect(fieldKey({ id: '', number: '8' })).toBe('8');
    const m = parseIdentity([{ number: '0', make: 'Laguna zero' }, { id: '0_bw', number: '0', make: 'Buttonwillow zero' }, { number: 38, make: 'Same car' }]);
    expect(m.get('0')!.make).toBe('Laguna zero');
    expect(m.get('0_bw')!.make).toBe('Buttonwillow zero');
    expect(m.get('0_bw')!.number).toBe('0');
    expect(m.get('38')!.make).toBe('Same car');
    // Laguna's identity.json has no ids: every row is keyed by its number, as before
    for (const [k, v] of lagIdent) expect(k).toBe(v.number);
  });

  it('identity.json per track with the global fallback (the per-track file may be missing or 404)', async () => {
    expect(TRACKS.laguna_seca.identity).toBeUndefined();
    expect(TRACKS.buttonwillow.identity).toBe('cars/field/buttonwillow/identity.json');
    expect(GLOBAL_IDENTITY).toBe('cars/field/identity.json');
    const own = { cars: [{ id: '0_bw', number: '0' }] }, global = [{ number: '0' }];
    const asked: string[] = [];
    const get = (have: Record<string, unknown>) => async (u: string) => { asked.push(u); return have[u] ?? null; };
    // own file present: used, the global one not fetched
    expect(await loadIdentityWithFallback(TRACKS.buttonwillow.identity, get({ [TRACKS.buttonwillow.identity!]: own, [GLOBAL_IDENTITY]: global })))
      .toEqual({ identity: own, path: TRACKS.buttonwillow.identity });
    expect(asked).toEqual([TRACKS.buttonwillow.identity]);
    // own file missing / 404 (fetchJson gives null): the global one
    asked.length = 0;
    expect(await loadIdentityWithFallback(TRACKS.buttonwillow.identity, get({ [GLOBAL_IDENTITY]: global }))).toEqual({ identity: global, path: GLOBAL_IDENTITY });
    expect(asked).toEqual([TRACKS.buttonwillow.identity, GLOBAL_IDENTITY]);
    // Laguna (no per-track file): straight to the global one
    asked.length = 0;
    expect(await loadIdentityWithFallback(TRACKS.laguna_seca.identity, get({ [GLOBAL_IDENTITY]: global }))).toEqual({ identity: global, path: GLOBAL_IDENTITY });
    expect(asked).toEqual([GLOBAL_IDENTITY]);
    // neither: null
    expect(await loadIdentityWithFallback(TRACKS.buttonwillow.identity, get({}))).toEqual({ identity: null, path: null });
  });

  it('models.json rows get an id (the number when absent); the queue matches them to cars by field key', () => {
    const rows = normaliseModelRows({ cars: [{ number: 0, file: 'models/0.glb' }, { id: '0_bw', number: '0', file: 'models/0_bw.glb' }, { number: '38', file: 'models/38.glb' }, { number: '5' }] });
    expect(rows.map((r) => [r.number, r.id, r.file])).toEqual([['0', '0', 'models/0.glb'], ['0', '0_bw', 'models/0_bw.glb'], ['38', '38', 'models/38.glb']]);
    const cars = [{ id: '0_bw', number: '0', isPlayer: false }, { id: '38', number: '38', isPlayer: false }, { id: '619', number: '619', isPlayer: true }];
    const kinds: Record<string, 'placeholder' | 'model'> = { '0': 'placeholder', '38': 'placeholder' };
    expect(modelQueue(rows, cars, (n) => kinds[n] ?? null).map((q) => [q.car, q.model.file])).toEqual([['0', 'models/0_bw.glb'], ['38', 'models/38.glb']]);
    // the Laguna #0 model never lands on Buttonwillow's 0_bw; a car without a row keeps its placeholder
    expect(modelQueue(rows.slice(0, 1), cars, (n) => kinds[n] ?? null)).toEqual([]);
    kinds['38'] = 'model';
    expect(modelQueue(rows, cars, (n) => kinds[n] ?? null).map((q) => q.car)).toEqual(['0']);
    // Laguna's raw rows (no id) match by number
    const lag = readJson('cars/field/models.json').cars;
    expect(modelQueue(lag, [{ id: '711', number: '711', isPlayer: false }], () => 'placeholder').map((q) => q.model.file)).toEqual(['models/711.glb']);
  });

  it('the sound index row is found by field key', () => {
    const index = { families: { v8: {}, i4: {} }, aliases: [], fallback: [], default: 'i4', cars: { '0': { family: 'v8' } } } as never;
    const engine = { layout: 'I4', cylinders: 4 };
    expect(carSound(index, { number: '0', identity: null, engine }).family).toBe('v8');
    expect(carSound(index, { number: '0', id: '0', identity: null, engine }).family).toBe('v8');
    expect(carSound(index, { number: '0', id: '0_bw', identity: null, engine }).family).not.toBe('v8');
  });

  it('Buttonwillow pace: ids by number, "<n>_bw" for a different Laguna car', () => {
    const ids = bw.cars.map((c) => c.id);
    expect(ids.every((x) => typeof x === 'string')).toBe(true);
    expect(new Set(ids).size).toBe(bw.cars.length);
    // the 11 "_bw" numbers less #43 and #89 (no lap in the session: left out, named in the notes); #670 is a different
    // car from Laguna's (identity.json), though the team matches
    expect(bw.cars.filter((c) => c.id !== c.number).map((c) => c.id).sort()).toEqual(['0_bw', '16_bw', '1_bw', '40_bw', '670_bw', '711_bw', '801_bw', '8_bw', '9_bw']);
    expect(bw.notes).toMatch(/#89 \(89_bw\), #6, #43 \(43_bw\), #101, #222/);
    // every AI car has an identity row by its id
    const bwIdent = parseIdentity(readJson('cars/field/buttonwillow/identity.json'));
    for (const c of bw.cars) if (!c.player) expect(bwIdent.has(fieldKey(c))).toBe(true);
    for (const n of ['38', '189', '544', '619', '963']) expect(bw.cars.find((c) => c.number === n)!.id).toBe(n);
    expect(bw.cars.filter((c) => c.player).map((c) => c.number)).toEqual(['619']);
    for (const c of bw.cars) { expect(c.targetLap).toBeGreaterThan(100); expect((c.stints ?? []).length).toBeGreaterThan(0); }
  });

  it('the director resolves identity by id; the race loads models by id (Buttonwillow cars on the global fallback)', async () => {
    const pick = ['0', '38', '711', '69', '619'];
    const pace: PaceJson = { ...bw, cars: bw.cars.filter((c) => pick.includes(c.number)) };
    const field = (): FieldData => ({ pace, identity: readJson('cars/field/identity.json'), models: normaliseModelRows(readJson('cars/field/models.json')), missing: [] });
    const asked: string[] = [];
    const { race } = harness('?seed=42&laps=2', () => 0.5, field, async (f) => { asked.push(f); return null; });
    race.start();
    const d = race.director!;
    const car = (n: string) => d.cars.find((c) => c.number === n)!;
    expect(d.cars.length).toBe(5);
    expect(car('0').id).toBe('0_bw');
    expect(car('0').identity).toBeNull();                      // not Laguna's #0
    expect(car('711').identity).toBeNull();                    // not Laguna's #711 Miata
    expect(car('38').identity!.make).toBe(lagIdent.get('38')!.make);   // the same car: its Laguna identity
    expect(car('69').identity).toBeNull();                     // a Buttonwillow-only car: placeholder until its own row
    expect(d.poses().find((p) => p.number === '0')!.id).toBe('0_bw');
    await Promise.resolve(); await new Promise((r) => setTimeout(r, 0));
    expect(asked).toContain('models/38.glb');
    expect(asked).not.toContain('models/0.glb');
    expect(asked).not.toContain('models/711.glb');
    race.dispose();
  }, 60000);

  it('Laguna: every car keyed by its number, identity as before', () => {
    const { race } = harness();
    race.start();
    const d = race.director!;
    for (const c of d.cars) {
      expect(c.id).toBe(c.number);
      if (!c.isPlayer) expect(c.identity?.make).toBe(lagIdent.get(c.number)?.make);
    }
    race.dispose();
  }, 60000);

  it('model key: pace model_id, then identity model_id, then id, then number (a renumbered car reuses its model)', () => {
    expect(modelKey({ number: '6', id: '6', model_id: '8' })).toBe('8');
    expect(modelKey({ number: '6', id: '6' }, { model_id: '8' })).toBe('8');
    expect(modelKey({ number: '6', id: '6', model_id: '8' }, { model_id: '9' })).toBe('8');
    expect(modelKey({ number: '670', id: '670_bw' })).toBe('670_bw');
    expect(modelKey({ number: '711' })).toBe('711');
    const rows = normaliseModelRows(readJson('cars/field/models.json'));
    const cars = [{ id: '6', model: '8', number: '6', isPlayer: false }, { id: '670_bw', model: '670_bw', number: '670', isPlayer: false }, { id: '8_bw', model: '8_bw', number: '8', isPlayer: false }];
    // #6 shows Laguna #8's Opel GT; Buttonwillow's #670 van and #8 never get Laguna's #670 / #8 models
    expect(modelQueue(rows, cars, () => 'placeholder').map((q) => [q.car, q.model.file])).toEqual([['6', 'models/8.glb']]);
  });

  it('a battery-electric car (cylinders 0, layout EV): finite physics, no division by zero, silent in the field audio', () => {
    const bolt = parseIdentity(readJson('cars/field/buttonwillow/identity.json')).get('16_bw')!;
    expect(bolt.engine?.layout).toBe('EV');
    const t = resolveCarType(bolt);
    expect(t.engineLayout).toBe('EV');
    expect(t.cylinders).toBe(0);
    expect(t.turbo).toBe(false);
    const probe = readJson('cars/probe_gt/car.json');
    const r = describeAiCar(probe, bolt, 0.5);
    for (const v of [r.massKg, r.powerKw, r.lateralG, r.topSpeedKph, ...r.gearRatios]) expect(Number.isFinite(v) && v > 0).toBe(true);
    const engine = { layout: t.engineLayout, cylinders: t.cylinders, exhaustNote: t.exhaustNote };
    expect(silentEngine(engine)).toBe(true);
    expect(silentEngine({ layout: 'I4', cylinders: 4 })).toBe(false);
    const index = { families: { v8: {}, i4: {} }, aliases: [['chevrolet', 'v8']], fallback: [{ cylinders: 4, family: 'i4' }], default: 'i4', cars: {} } as never;
    const snd = carSound(index, { number: '16', id: '16_bw', identity: bolt, engine });
    expect(snd.family).toBe('');                       // no borrowed petrol family: the race gives it no voice
    expect(Number.isFinite(snd.trim) && Number.isFinite(snd.muffler) && Number.isFinite(snd.rpmScale)).toBe(true);
    // an explicit index row still wins (an electric family some day)
    expect(carSound({ ...(index as object), cars: { '16_bw': { family: 'i4' } } } as never, { number: '16', id: '16_bw', identity: bolt, engine }).family).toBe('i4');
  });

  it('a Buttonwillow race with its own identity.json: identity and models by id, #670 the van, #16 the Bolt', async () => {
    const pick = ['16', '670', '38', '0', '619'];
    const pace: PaceJson = { ...bw, cars: bw.cars.filter((c) => pick.includes(c.number)) };
    const field = (): FieldData => ({ pace, identity: readJson('cars/field/buttonwillow/identity.json'), models: normaliseModelRows(readJson('cars/field/models.json')), missing: [] });
    const asked: string[] = [];
    const { race } = harness('?seed=42&laps=2', () => 0.5, field, async (f) => { asked.push(f); return null; });
    race.start();
    const d = race.director!;
    const car = (n: string) => d.cars.find((c) => c.number === n)!;
    expect(car('670').identity!.make).toBe('Dodge');
    expect(car('16').identity!.model).toMatch(/Bolt/);
    expect(car('0').id).toBe('0_bw');
    expect(car('0').identity!.make).not.toBe(lagIdent.get('0')!.make);
    const ev = d.poses().find((p) => p.number === '16')!;
    expect(ev.engine.cylinders).toBe(0);
    expect(Number.isFinite(ev.engine.redline)).toBe(true);
    for (let k = 0; k < 500; k++) d.step(0.001);
    expect(Number.isFinite(car('16').vehicle.state.pos[0])).toBe(true);
    await new Promise((r) => setTimeout(r, 0));
    expect(asked).toContain('models/38.glb');
    expect(asked).not.toContain('models/670.glb');
    expect(asked).not.toContain('models/0.glb');
    race.dispose();
  }, 60000);
});
