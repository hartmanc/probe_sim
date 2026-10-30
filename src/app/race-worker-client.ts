// Main-thread side of the race Worker (?worker=1, docs/performance.md). The main thread still builds the race's RaceDirector
// (the field's specs, identities, the line, the penalty box) but never steps it: `installMirror` takes over its dynamic
// methods and `applySnapshot` copies each snapshot of the worker's simulation into the VehicleState objects, the director's
// car book-keeping and the HotlapSim fields that the renderer, camera, HUD and audio already read.
import type { RaceDirector, RaceHud } from '../physics/ai/race';
import type { HotlapSim, SimAssets } from '../scoreboard';
import type { CarContactEvent } from '../physics/cars';
import { CAR64_STRIDE, CAR_STRIDE, unpackCar, unpackRace, type CarRace } from './race-snapshot';
import type { HostBuild, HostInit, HostInput, HostRec, HostSnapshot } from './race-host';

/** What the mirror remembers between snapshots. */
export interface MirrorState {
  gen: number;
  hud: RaceHud | null;
  brakes: Float32Array | null;
  launchedOffTrack: boolean;
  snapshots: number;
  lastSeq: number;
  busyMs: number; spanMs: number;
}
export const newMirrorState = (gen: number): MirrorState => ({ gen, hud: null, brakes: null, launchedOffTrack: false, snapshots: 0, lastSeq: 0, busyMs: 0, spanMs: 0 });

/**
 * Take over the director's dynamic API on the main thread: the HUD, the results, the poses' brake flags, rule reports and
 * the step itself come from / go to the worker. `report` forwards `reportViolation`.
 */
export function installMirror(dir: RaceDirector, sim: HotlapSim, ms: MirrorState, report: (kind: string, detail?: string) => void): void {
  const d = dir as unknown as Record<string, unknown>;
  const origHud = dir.hud.bind(dir), origPoses = dir.poses.bind(dir);
  d.hud = () => ms.hud ?? origHud();
  d.getResults = () => ms.hud?.results ?? null;
  d.reportViolation = (kind: string, detail?: string) => { report(kind, detail); return true; };
  d.step = () => { /* the worker steps */ };
  d.poses = () => {
    const p = origPoses();
    if (ms.brakes) for (let i = 0; i < p.length; i++) p[i].brake = ms.brakes[i];
    return p;
  };
  Object.defineProperty(sim, 'launchedOffTrack', { get: () => ms.launchedOffTrack, configurable: true });
}

const scratch: CarRace = { U: 0, s: 0, lastLap: NaN, bestLap: NaN, finishAt: NaN, finished: false, lapIdx: 0, lapsDone: 0 };

/** Copy a snapshot into the main thread's director and HotlapSim (same car order: both build the field the same way). */
export function applySnapshot(snap: HostSnapshot, dir: RaceDirector, sim: HotlapSim, ms: MirrorState): void {
  const n = dir.cars.length;
  if (snap.f32.length !== n * CAR_STRIDE) return;   // another field: ignore
  if (!ms.brakes || ms.brakes.length !== n) ms.brakes = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const c = dir.cars[i];
    ms.brakes[i] = unpackCar(snap.f32, i * CAR_STRIDE, c.vehicle.state);
    const r = unpackRace(snap.f64, i * CAR64_STRIDE, scratch);
    c.U = r.U; c.lastLap = r.lastLap; c.bestLap = r.bestLap; c.finishAt = r.finishAt; c.finished = r.finished; c.lapIdx = r.lapIdx; c.lapsDone = r.lapsDone;
    dir.traffic.s[i] = r.s; dir.traffic.U[i] = r.U;
  }
  dir.time = snap.time; dir.phase = snap.phase as RaceDirector['phase']; dir.timeScale = snap.timeScale;
  dir.contactTotal = snap.contactTotal; dir.lodFar = snap.lodFar;
  dir.contacts = snap.contacts as unknown as readonly CarContactEvent[]; dir.contactCount = snap.contacts.length;
  ms.hud = snap.hud; ms.launchedOffTrack = snap.launchedOffTrack;
  sim.simTime = snap.simTime; sim.s = snap.s;
  const inp = sim.input as { throttle: number; brake: number };
  inp.throttle = snap.throttle; inp.brake = snap.brake;
  ms.snapshots++; ms.lastSeq = snap.seq; ms.busyMs += snap.busyMs; ms.spanMs += snap.spanMs;
  if (snap.timing && dir.timing) {
    const t = dir.timing, a = snap.timing;
    t.steps += a.steps; t.control += a.control; t.player += a.player; t.aiPhysics += a.aiPhysics; t.contacts += a.contacts; t.other += a.other;
  }
}

export interface WorkerLike { postMessage(m: unknown, t?: Transferable[]): void; terminate(): void; onmessage: ((e: MessageEvent) => void) | null; onerror: ((e: ErrorEvent) => void) | null }

/** The worker handle: init once, build per race, an input message per frame, snapshots stored as they arrive. */
export class RaceWorkerClient {
  private w: WorkerLike;
  latest: HostSnapshot | null = null;
  private gen = 0;
  private running = false;
  ready = false;
  failed: string | null = null;
  private recWaiters = new Map<number, (r: HostRec | null) => void>();

  constructor(make: () => WorkerLike = () => new Worker(new URL('./race-worker.ts', import.meta.url), { type: 'module' }) as unknown as WorkerLike) {
    this.w = make();
    this.w.onmessage = (e) => {
      const m = e.data as { type: string; gen?: number };
      if (m.type === 'ready') this.ready = true;
      else if (m.type === 'snap' && m.gen === this.gen) this.latest = e.data as HostSnapshot;   // a snapshot of an earlier race is dropped
      else if (m.type === 'rec') {
        const w = this.recWaiters.get(m.gen ?? -1);
        if (w) { this.recWaiters.delete(m.gen ?? -1); w((e.data as { none?: boolean }).none ? null : (e.data as HostRec)); }
      }
    };
    this.w.onerror = (e) => { this.failed = e.message || 'worker error'; };
  }

  init(assets: SimAssets, field: HostInit['field'], trackId: string): void {
    this.w.postMessage({ type: 'init', assets, field, trackId } satisfies { type: 'init' } & HostInit);
  }
  /** A new race; returns its generation number. */
  build(m: Omit<HostBuild, 'gen'>): number {
    this.gen++; this.latest = null; this.running = true;
    this.w.postMessage({ type: 'build', ...m, gen: this.gen });
    return this.gen;
  }
  get generation(): number { return this.gen; }
  input(m: HostInput): void { if (!this.running) this.setRunning(true); this.w.postMessage({ type: 'input', ...m }); }
  setRunning(on: boolean): void { if (on === this.running) return; this.running = on; this.w.postMessage({ type: 'run', on }); }
  recover(s: number): void { this.w.postMessage({ type: 'recover', s }); }
  violation(kind: string, detail?: string): void { this.w.postMessage({ type: 'violation', kind, detail }); }
  /** Ask the worker for the race recording so far (race generation `gen`, the current one by default); null when it is not recorded, answers late or never. Messages are handled in order, so a flush sent before the next 'build' sees the race it was asked about. */
  flushRec(gen: number = this.gen, timeoutMs = 4000): Promise<HostRec | null> {
    return new Promise((resolve) => {
      const t = setTimeout(() => { if (this.recWaiters.delete(gen)) resolve(null); }, timeoutMs);
      this.recWaiters.set(gen, (r) => { clearTimeout(t); resolve(r); });
      this.w.postMessage({ type: 'flush' });
    });
  }
  /** The newest snapshot not yet applied (null when none new). */
  take(lastSeq: number): HostSnapshot | null { const s = this.latest; return s && s.seq !== lastSeq ? s : null; }
  dispose(): void { this.w.onmessage = null; this.w.terminate(); }
}
