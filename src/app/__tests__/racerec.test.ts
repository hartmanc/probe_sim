// Race recordings (docs/races.md): a short race is recorded exactly as the app does it (RaceCapture over the sim the director
// steps), re-run offline (tools/race/replay_core.ts) and must come out identical; a tampered input stream must not.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { HotlapSim, STEP } from '../../scoreboard';
import { autopilot, lagunaAssets } from '../../scoreboard/__tests__/fixtures';
import { lineToWorld } from '../../physics';
import { buildDirector } from '../race-build';
import { neighbourField } from '../field-select';
import { RaceCapture } from '../race-record';
import { RaceSimHost, type HostBuild } from '../race-host';
import type { FieldData } from '../loader';
import { RecAssembler, buildRecording, toWire, type RaceRecording } from '../../scoreboard/racerec';
import { replayRecording } from '../../../tools/race/replay_core';
import { aggregateMd, raceMd } from '../../../tools/race/replay_report';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const readJson = (p: string) => JSON.parse(readFileSync(pub + p, 'utf8'));
const PACE = readJson('cars/field/pace.json'), IDENTITY = readJson('cars/field/identity.json');
const CAP = 10;

/** Record a short Laguna race the way modes/race.ts does: the sim records, the director steps the player's car, a RaceCapture watches. */
async function record(o: { playerAi: boolean; steps: number; laps?: number; events?: boolean; seed?: number }): Promise<{ rec: RaceRecording; sim: HotlapSim }> {
  const sim = new HotlapSim(lagunaAssets(), { record: true, autoShift: true });
  sim.setRef(null); sim.reset();
  const pace = neighbourField(PACE, CAP, '619');
  const field = { pace, identity: IDENTITY, models: [], missing: [] } as unknown as FieldData;
  const seed = o.seed ?? 11, laps = o.laps ?? 1;
  const dir = buildDirector(sim, field, { seed, laps, trackId: 'laguna_seca', playerAi: o.playerAi, realGrid: true });
  sim.stepVehicle = (di) => dir.step(STEP, di as never);
  const cap = new RaceCapture({ dir, sim, trackId: 'laguna_seca', owner: false, worker: null,
    build: { seed, laps, realGrid: true, playerAi: o.playerAi, lod: false, strengthPct: 100, closeRacing: null, planner: null, fieldCap: CAP, ref: sim.refId, autoShift: true, abs: sim.abs } });
  const drive = o.playerAi ? () => ({ steer: 0, throttle: 0, brake: 0 }) : autopilot(sim, 0.8);
  while (sim.stepIndex < o.steps && !(dir.getResults() && !dir.hud().resultsPending)) {
    if (o.events && sim.stepIndex === 60_000) {
      // the app's recovery and a cone report: between steps, logged at this step
      const s = sim.s, L = sim.assets.track.length_m, p = lineToWorld(sim.assets.track, () => 0, ((s % L) + L) % L);
      cap.recover(s); sim.vehicle.reset([p.pos[0], p.pos[1], p.pos[2]], p.heading, 0);
      cap.violation('pit_exit_cones'); dir.reportViolation('pit_exit_cones');
    }
    sim.step(drive);
    cap.after();
  }
  const rec = await cap.finish(false);
  if (!rec) throw new Error('no recording');
  return { rec, sim };
}

const replay = (rec: RaceRecording, extra: Partial<Parameters<typeof replayRecording>[1]> = {}) =>
  replayRecording(rec, { assets: lagunaAssets(), pace: PACE, identity: IDENTITY, analyse: true, ...extra });

describe('race recording and offline re-run', () => {
  it('a playerai race re-runs identically, and the pass table is not empty', async () => {
    const { rec } = await record({ playerAi: true, steps: 400_000, laps: 2 });
    expect(rec.live.lapTimes.length).toBeGreaterThanOrEqual(1);
    expect(rec.live.results?.length).toBe(CAP + 1);
    expect(rec.snapshot?.n).toBeGreaterThan(100);
    const r = replay(rec);
    expect(r.check.problems).toEqual([]);
    expect(r.check.ok).toBe(true);
    expect(r.check).toMatchObject({ config: true, live: true, snapshot: true });
    const a = r.analysis!;
    expect(a.passes.length).toBeGreaterThan(0);
    const p = a.passes[0];
    expect(p.other.length).toBe(101); expect(p.player.length).toBe(101);
    // the reports: a table per race and the aggregate (the owner's and the public's apart)
    const md = raceMd('fixture', r.check, a);
    expect(md).toContain('**Check: passed**'); expect(md).toMatch(/\| made \|/);
    const agg = aggregateMd([{ name: 'fixture', check: r.check, analysis: a }, { name: 'owner', check: r.check, analysis: { ...a, owner: true } }]);
    expect(agg).toMatch(/### Owner: 1 race, \d+ passes made/); expect(agg).toMatch(/### Public: 1 race/); expect(agg).toContain('Yardstick cells');
    if (process.env.RACEREC_OUT) writeFileSync(process.env.RACEREC_OUT, JSON.stringify(toWire(rec)));   // for trying tools/race/replay_race.ts by hand
  }, 300_000);

  it('a driven race with a recovery and a cone report re-runs identically; a tampered input stream fails the check', async () => {
    const { rec } = await record({ playerAi: false, steps: 90_000, events: true });
    expect(rec.events.map((e) => e[1])).toEqual([0, 1]);
    const ok = replay(rec, { analyse: false });
    expect(ok.check.problems).toEqual([]);
    expect(ok.check.ok).toBe(true);
    // lift off for ten seconds in the middle: the player's positions (and so the snapshots) must differ
    const bad: RaceRecording = JSON.parse(JSON.stringify(rec));
    bad.inputs.rows = bad.inputs.rows.map((r) => (r[0] >= 40_000 && r[0] < 50_000 ? [r[0], r[1], 0, 600, r[4]] : r));
    const t = replay(bad, { analyse: false });
    expect(t.check.ok).toBe(false);
    expect(t.check.problems.join(' ')).toMatch(/snapshot differs|live data differs/);
    // a recording from another AI version or build is refused unless forced
    const old: RaceRecording = { ...rec, aiVersion: '0' };
    const refused = replay(old, { analyse: false });
    expect(refused.check.ok).toBe(false); expect(refused.steps).toBe(0); expect(refused.check.problems[0]).toMatch(/refused: AI version/);
    const wrongSha = replay({ ...rec, buildSha: 'abc1234' }, { analyse: false, currentSha: 'def5678' });
    expect(wrongSha.check.problems[0]).toMatch(/refused: build/);
    const forced = replay(old, { analyse: false, force: true });
    expect(forced.steps).toBeGreaterThan(0); expect(forced.check.mismatches.length).toBe(1);
  }, 300_000);

  it('the Worker path (RaceSimHost on a fake clock, frame-by-frame inputs, a recovery and a cone report) is recorded and re-runs identically', () => {
    const host = new RaceSimHost();
    host.init({ assets: lagunaAssets(), field: { pace: neighbourField(PACE, CAP, '619'), identity: IDENTITY }, trackId: 'laguna_seca' });
    const B: HostBuild = { gen: 1, seed: 5, laps: 1, realGrid: true, playerAi: false, lod: false, strengthPct: 100, ref: null, autoShift: true, abs: true, timing: false, record: true };
    host.build(B, 0);
    const sim = host.sim!;
    const drive = autopilot(sim, 0.8);
    let now = 0;
    for (let f = 0; f < 5600; f++) {
      now += 16;
      const r = drive();
      host.input({ steer: r.steer, throttle: r.throttle, brake: r.brake, handbrake: false, up: false, down: false, autoShift: true, abs: true, ref: null });
      host.tick(now);
      if (f === 2500) host.recover(sim.s);
      if (f === 2600) host.violation('pit_exit_cones');
    }
    const fl = host.flush()!;
    expect(fl.chunk.steps).toBeGreaterThan(80_000);
    expect(fl.chunk.events.map((e) => e[1])).toEqual([0, 1]);
    const rec = buildRecording({ trackId: 'laguna_seca', fieldId: 'cars/field/pace.json', seed: B.seed, laps: B.laps, aiVersion: String(host.dir!.config.ai_version), buildSha: '', physics: sim.physics,
      build: { seed: B.seed, laps: B.laps, realGrid: true, playerAi: false, lod: false, strengthPct: 100, closeRacing: null, planner: null, fieldCap: CAP, ref: null, autoShift: true, abs: true },
      config: fl.config, cars: fl.cars, L: fl.L, carId: 'probe_gt', owner: false, started: '2026-10-30T00:00:00.000Z', durationS: fl.chunk.steps * 0.001, aborted: true }, new RecAssembler().add(fl.chunk), fl.live);
    const r = replay(rec, { analyse: false });
    expect(r.check.problems).toEqual([]);
    expect(r.check.ok).toBe(true);
    expect(r.steps).toBe(fl.chunk.steps);
  }, 300_000);
});
