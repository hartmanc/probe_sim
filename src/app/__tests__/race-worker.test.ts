// The race Worker's simulation (race-host.ts), its snapshot codec and the main-thread mirror: the host stepped on a fake clock
// must be the main-thread race bit for bit, and a snapshot must land in the main thread's objects.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { HotlapSim, STEP } from '../../scoreboard';
import { lagunaAssets } from '../../scoreboard/__tests__/fixtures';
import { buildDirector } from '../race-build';
import { RaceSimHost, type HostBuild } from '../race-host';
import { CAR_STRIDE, packCar, unpackCar } from '../race-snapshot';
import { RaceWorkerClient, applySnapshot, installMirror, newMirrorState, type WorkerLike } from '../race-worker-client';
import type { FieldData } from '../loader';
import type { VehicleState } from '../physics-types';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const readJson = (p: string) => JSON.parse(readFileSync(pub + p, 'utf8'));
const field = { pace: readJson('cars/field/pace.json'), identity: readJson('cars/field/identity.json') };
const B: HostBuild = { gen: 1, seed: 3, laps: 2, realGrid: false, playerAi: true, lod: false, strengthPct: 100, ref: null, autoShift: true, abs: true, timing: false };

function mainThreadRace(steps: number, o: Partial<HostBuild> = {}) {
  const strengthPct = o.strengthPct ?? 100;
  const sim = new HotlapSim(lagunaAssets(), { record: false, autoShift: true });
  sim.setRef(null); sim.reset();
  const dir = buildDirector(sim, { ...field, models: [], missing: [] } as unknown as FieldData, { seed: B.seed, laps: B.laps, trackId: 'laguna_seca', playerAi: true, strengthPct, ...(o.lod ? { lod: true } : {}), ...(o.planner ? { planner: o.planner } : {}) });
  sim.stepVehicle = (di) => dir.step(STEP, di as never);
  for (let i = 0; i < steps; i++) sim.step(() => ({ steer: 0, throttle: 0, brake: 0 }));
  return { sim, dir };
}

describe('state codec', () => {
  it('round-trips a vehicle state in place (float32)', () => {
    const { dir } = mainThreadRace(1500);
    const f = new Float32Array(CAR_STRIDE);
    const src = dir.cars[3].vehicle.state;
    packCar(src, 0.25, f, 0);
    const dst = JSON.parse(JSON.stringify(dir.cars[0].vehicle.state)) as VehicleState;
    expect(unpackCar(f, 0, dst)).toBe(0.25);
    for (let i = 0; i < 3; i++) { expect(dst.pos[i]).toBeCloseTo(src.pos[i], 2); expect(dst.vel[i]).toBeCloseTo(src.vel[i], 3); }
    for (let w = 0; w < 4; w++) {
      expect(dst.wheels[w].steer).toBeCloseTo(src.wheels[w].steer, 5); expect(dst.wheels[w].onTrack).toBe(src.wheels[w].onTrack);
      expect(dst.wheels[w].slipUse).toBeCloseTo(src.wheels[w].slipUse, 3);
    }
    expect(dst.gear).toBe(src.gear); expect(dst.rpm).toBeCloseTo(src.rpm, 0);
  }, 60000);
});

describe('race host', () => {
  it.each([[100, 'lanes'], [105, 'lanes'], [100, 'offset']] as const)('on a fake clock it steps exactly the main-thread race (same bits, same contacts) and caps a stall at 50 ms, AI strength %i %%, planner %s', (strengthPct, planner) => {
    const host = new RaceSimHost();
    host.init({ assets: lagunaAssets(), field, trackId: 'laguna_seca' });
    host.build({ ...B, strengthPct, planner }, 0);
    // the switch reaches the worker's director and every AI driver (C1: ?planner=offset)
    expect(host.dir!.config.planner).toBe(planner);
    for (const c of host.dir!.cars) if (c.driver) expect(c.driver.planner).toBe(planner);
    let t = 0;
    for (let k = 0; k < 120; k++) { t += 25; host.tick(t); }       // 3 s in 25 ms frames: 3000 steps
    expect(Math.abs(host.sim!.stepIndex - 3000)).toBeLessThanOrEqual(2);   // the float accumulator, as in the main loop
    const n = host.tick(t + 400); t += 400;
    expect(Math.abs(n - 50)).toBeLessThanOrEqual(1);               // a 400 ms stall: the main loop's 50 ms cap
    const a = mainThreadRace(host.sim!.stepIndex, { strengthPct, planner });
    expect(host.dir!.contactTotal).toBe(a.dir.contactTotal);
    for (let i = 0; i < a.dir.cars.length; i++) {
      expect(Array.from(host.dir!.cars[i].vehicle.state.pos)).toEqual(Array.from(a.dir.cars[i].vehicle.state.pos));
      expect(host.dir!.cars[i].U).toBe(a.dir.cars[i].U);
    }
    expect(host.dir!.time).toBe(a.dir.time);
  }, 120000);

  it('strength 105 really changes the race (the worker is not silently running 100 %)', () => {
    const a = mainThreadRace(4000), b = mainThreadRace(4000, { strengthPct: 105 });
    const diff = a.dir.cars.some((c, i) => c.vehicle.state.pos[0] !== b.dir.cars[i].vehicle.state.pos[0]);
    expect(diff).toBe(true);
  }, 120000);

  it('a snapshot lands in the main thread director and HotlapSim; paused it does not step; recover moves the car', () => {
    const host = new RaceSimHost();
    host.init({ assets: lagunaAssets(), field, trackId: 'laguna_seca' });
    host.build(B, 0);
    for (let t = 25; t <= 2500; t += 25) host.tick(t);
    const snap = host.snapshot(2500)!;
    const main = mainThreadRace(0);
    const ms = newMirrorState(1);
    let reported = '';
    installMirror(main.dir, main.sim, ms, (k) => { reported = k; });
    applySnapshot(snap, main.dir, main.sim, ms);
    for (let i = 0; i < main.dir.cars.length; i++) {
      const w = host.dir!.cars[i], m = main.dir.cars[i];
      expect(m.vehicle.state.pos[0]).toBeCloseTo(w.vehicle.state.pos[0], 2);
      expect(m.U).toBe(w.U);
    }
    expect(main.dir.hud().phase).toBe(host.dir!.hud().phase);
    expect(main.dir.hud().position).toBe(host.dir!.hud().position);
    expect(main.dir.getResults()).toBeNull();
    expect(main.dir.poses()[2].brake).toBeCloseTo(host.dir!.poses()[2].brake, 5);
    expect(main.dir.time).toBe(host.dir!.time);
    expect(main.sim.simTime).toBe(host.sim!.simTime);
    main.dir.reportViolation('pit_exit_cones');
    expect(reported).toBe('pit_exit_cones');
    // paused: no steps; resumed: the clock restarts (no catch-up for the pause)
    const n0 = host.sim!.stepIndex;
    host.setRunning(false, 2600); expect(host.tick(5000)).toBe(0);
    host.setRunning(true, 6000); host.tick(6020);
    expect(host.sim!.stepIndex - n0).toBeGreaterThanOrEqual(19);
    expect(host.sim!.stepIndex - n0).toBeLessThanOrEqual(20);
    const p0 = host.sim!.vehicle.state.pos.slice();
    host.recover(100);
    expect(host.sim!.vehicle.state.pos[0]).not.toBe(p0[0]);
  }, 120000);
});

describe('worker client', () => {
  it('drops a snapshot of an earlier race, hands each snapshot out once, and posts the protocol', () => {
    const sent: { type: string }[] = [];
    const fake: WorkerLike = { postMessage: (m) => sent.push(m as { type: string }), terminate: () => {}, onmessage: null, onerror: null };
    const c = new RaceWorkerClient(() => fake);
    const g1 = c.build({ seed: 1, laps: 1, realGrid: false, playerAi: true, lod: false, strengthPct: 100, ref: null, autoShift: true, abs: true, timing: false });
    const snap = (gen: number, seq: number) => ({ data: { type: 'snap', gen, seq } }) as MessageEvent;
    fake.onmessage!(snap(g1, 1));
    expect(c.take(0)?.seq).toBe(1);
    expect(c.take(1)).toBeNull();
    const g2 = c.build({ seed: 2, laps: 1, realGrid: false, playerAi: true, lod: false, strengthPct: 100, ref: null, autoShift: true, abs: true, timing: false });
    fake.onmessage!(snap(g1, 2));            // a late snapshot of race 1
    expect(c.take(0)).toBeNull();
    fake.onmessage!(snap(g2, 1));
    expect(c.take(0)?.seq).toBe(1);
    c.setRunning(false); c.setRunning(false); c.recover(10); c.violation('pit_exit_cones');
    expect(sent.map((m) => m.type)).toEqual(['build', 'build', 'run', 'recover', 'violation']);
    c.dispose();
  });
});
