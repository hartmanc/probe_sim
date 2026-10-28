// The race simulation as the Worker runs it (?worker=1, docs/performance.md): the player's HotlapSim plus the RaceDirector,
// stepped on the worker's own clock with the main thread's accumulator (1 ms steps, 50 ms cap, the director's time scale),
// so a slow render frame no longer stalls the physics. Pure TS with no `self`: race-worker.ts is the thin message shell, and
// the unit tests drive this class directly with a fake clock.
import { HotlapSim, STEP, type RawInput, type SimAssets } from '../scoreboard';
import { lineToWorld } from '../physics';
import type { RaceDirector, RaceHud, DirectorTiming } from '../physics/ai/race';
import { buildDirector } from './race-build';
import type { FieldData } from './loader';
import { CAR64_STRIDE, CAR_STRIDE, packCar, packRace } from './race-snapshot';

export const HOST_MAX_FRAME = 0.05;      // the main loop's cap per rendered frame (index.ts MAX_FRAME)

export interface HostInit { assets: SimAssets; field: { pace: unknown; identity: unknown }; trackId: string }
export interface HostBuild { gen: number; seed: number; laps: number; realGrid: boolean; playerAi: boolean; lod: boolean; strengthPct: number; closeRacing?: boolean | null; ref: string | null; autoShift: boolean; abs: boolean; timing: boolean }
export interface HostInput { steer: number; throttle: number; brake: number; handbrake: boolean; up: boolean; down: boolean; autoShift: boolean; abs: boolean; ref: string | null }

/** One snapshot message. `f32` / `f64` are transferred; the rest is a small structured clone. */
export interface HostSnapshot {
  type: 'snap';
  gen: number; seq: number;
  f32: Float32Array; f64: Float64Array;
  hud: RaceHud;
  time: number; phase: string; timeScale: number; contactTotal: number; lodFar: number;
  simTime: number; s: number; launchedOffTrack: boolean; throttle: number; brake: number;
  /** other cars' contacts since the last snapshot (closing >= 2 m/s): what the app turns into distant thumps */
  contacts: { a: number; b: number; x: number; y: number; closing: number }[];
  /** the director's per-group step timings since the last snapshot (ms), when asked for */
  timing: DirectorTiming | null;
  /** wall time the worker spent stepping since the last snapshot, ms, and the wall time it covers */
  busyMs: number; spanMs: number;
}

export class RaceSimHost {
  sim: HotlapSim | null = null;
  dir: RaceDirector | null = null;
  running = false;
  gen = 0;
  private seq = 0;
  private init_: HostInit | null = null;
  private acc = 0;
  private last = 0;
  private inp: HostInput = { steer: 0, throttle: 0, brake: 0, handbrake: false, up: false, down: false, autoShift: true, abs: true, ref: null };
  private up = false;
  private down = false;
  private contacts: HostSnapshot['contacts'] = [];
  private busy = 0;
  private spanStart = 0;
  private timing: DirectorTiming | null = null;

  init(m: HostInit): void {
    this.init_ = m;
    this.sim = new HotlapSim(m.assets, { record: false, autoShift: true });
  }

  /** A fresh race: the rolling start + a new director, exactly as modes/race.ts build() does on the main thread. */
  build(m: HostBuild, now: number): void {
    const sim = this.sim, init = this.init_;
    if (!sim || !init) throw new Error('race host: not initialised');
    this.gen = m.gen;
    sim.autoShift = m.autoShift; sim.abs = m.abs; sim.setRef(m.ref);
    sim.launchUntil = 0;
    sim.reset();                       // ctx.rollingStart(): fresh Vehicle + Surface, step counter 0
    sim.record = false;
    const field = { pace: init.field.pace, identity: init.field.identity, models: [], missing: [] } as unknown as FieldData;
    const dir = buildDirector(sim, field, { seed: m.seed, laps: m.laps, trackId: init.trackId, realGrid: m.realGrid, playerAi: m.playerAi, lod: m.lod, strengthPct: m.strengthPct, closeRacing: m.closeRacing ?? null });
    this.timing = m.timing ? { steps: 0, control: 0, player: 0, aiPhysics: 0, contacts: 0, other: 0 } : null;
    dir.timing = this.timing;
    sim.stepVehicle = (di) => dir.step(STEP, di as Parameters<RaceDirector['step']>[1]);
    this.dir = dir;
    this.acc = 0; this.last = now; this.contacts = []; this.up = false; this.down = false;
    this.busy = 0; this.spanStart = now;
    this.running = true;
  }

  input(m: HostInput): void {
    this.inp = m;
    if (m.up) this.up = true;
    if (m.down) this.down = true;
    const sim = this.sim;
    if (sim) { sim.autoShift = m.autoShift; sim.abs = m.abs; if (sim.refId !== m.ref) sim.setRef(m.ref); }
  }

  setRunning(on: boolean, now: number): void {
    if (on && !this.running) { this.last = now; this.acc = 0; }
    this.running = on && !!this.dir;
  }

  /** Put the player's car back on the centreline at s (race recovery; modes/race.ts reset()). */
  recover(s: number): void {
    const sim = this.sim;
    if (!sim) return;
    const L = sim.assets.track.length_m;
    const p = lineToWorld(sim.assets.track, () => 0, ((s % L) + L) % L);
    sim.vehicle.reset([p.pos[0], p.pos[1], p.pos[2]], p.heading, 0);
  }

  violation(kind: string, detail?: string): void { this.dir?.reportViolation(kind, detail); }

  private readonly sample = (): RawInput => {
    const r = this.inp;
    const raw: RawInput = { steer: r.steer, throttle: r.throttle, brake: r.brake, handbrake: r.handbrake, shiftUp: this.up, shiftDown: this.down };
    this.up = false; this.down = false;   // latched until the next sample
    return raw;
  };

  /** Advance to wall time `now` (ms); returns the number of physics steps run. */
  tick(now: number): number {
    const sim = this.sim, dir = this.dir;
    if (!sim || !dir || !this.running) return 0;
    const t0 = performance.now();
    const dt = Math.min(Math.max(0, now - this.last) / 1000, HOST_MAX_FRAME);
    this.last = now;
    this.acc += dt * dir.timeScale;
    let n = 0;
    while (this.acc >= STEP) {
      sim.step(this.sample);
      this.acc -= STEP; n++;
      for (let k = 0; k < dir.contactCount; k++) {
        const ev = dir.contacts[k];
        if (ev.closing < 2 || ev.a === dir.player.idx || ev.b === dir.player.idx) continue;
        if (this.contacts.length < 256) this.contacts.push({ a: ev.a, b: ev.b, x: ev.x, y: ev.y, closing: ev.closing });
      }
    }
    this.busy += performance.now() - t0;
    return n;
  }

  /** The state for the main thread (transfer `f32` and `f64`). */
  snapshot(now: number): HostSnapshot | null {
    const sim = this.sim, dir = this.dir;
    if (!sim || !dir) return null;
    const n = dir.cars.length;
    const f32 = new Float32Array(n * CAR_STRIDE), f64 = new Float64Array(n * CAR64_STRIDE);
    const poses = dir.poses();
    for (let i = 0; i < n; i++) {
      const c = dir.cars[i];
      packCar(c.vehicle.state, poses[i].brake, f32, i * CAR_STRIDE);
      packRace({ U: c.U, s: dir.traffic.s[i], lastLap: c.lastLap, bestLap: c.bestLap, finishAt: c.finishAt, finished: c.finished, lapIdx: c.lapIdx, lapsDone: c.lapsDone }, f64, i * CAR64_STRIDE);
    }
    const hud = JSON.parse(JSON.stringify(dir.hud())) as RaceHud;   // a detached copy: the director reuses its object
    const snap: HostSnapshot = {
      type: 'snap', gen: this.gen, seq: ++this.seq, f32, f64, hud,
      time: dir.time, phase: dir.phase, timeScale: dir.timeScale, contactTotal: dir.contactTotal, lodFar: dir.lodFar,
      simTime: sim.simTime, s: sim.s, launchedOffTrack: sim.launchedOffTrack, throttle: sim.input.throttle, brake: sim.input.brake,
      contacts: this.contacts, timing: this.timing ? { ...this.timing } : null, busyMs: this.busy, spanMs: now - this.spanStart,
    };
    this.contacts = []; this.busy = 0; this.spanStart = now;
    if (this.timing) { const t = this.timing; t.steps = 0; t.control = 0; t.player = 0; t.aiPhysics = 0; t.contacts = 0; t.other = 0; }
    return snap;
  }
}
