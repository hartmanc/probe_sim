// The app side of race recordings (docs/races.md): what a race keeps, when it is finished, and the upload. The format and the
// tap are src/scoreboard/racerec.ts; the Worker's half is race-host.ts (flush). Nothing here is personal: no name, no device
// id, no secret, no user agent (the request carries what every request carries).
import type { RaceDirector } from '../physics/ai/race';
import { race as R } from '../physics';
import type { HotlapSim } from '../scoreboard';
import { TRACKS } from '../scoreboard/config';
import { REC_MIN_ABORT_S, RecAssembler, buildRecording, packRecording, toWire, type RaceRecording, type RecBuild, type RecChunk, type RecLive } from '../scoreboard/racerec';
import { RaceTap, configOf, liveOf } from '../scoreboard/racetap';
import { apiBase } from './scoreboard-client';
import type { RaceWorkerClient } from './race-worker-client';

export type RecordMode = 'on' | 'off' | 'download';
/** `?record=0` switches the recording off, `?record=download` also offers the file from the results card. */
export function parseRecordMode(search: string): RecordMode {
  const v = new URLSearchParams(search).get('record');
  return v === '0' || v === 'off' || v === 'false' ? 'off' : v === 'download' ? 'download' : 'on';
}

/** `/api/races` beside wherever the scoreboard API is (same `?api=` rule as the scoreboard). */
export function racesUrl(base: string = apiBase()): string { return base.replace(/\/scores$/, '/races'); }

/** The build's short git sha ('' when unknown). */
export const buildSha = (): string => (typeof __GIT_SHA__ !== 'undefined' ? __GIT_SHA__ : '');

export interface CaptureOptions {
  dir: RaceDirector; sim: HotlapSim; trackId: string; build: RecBuild;
  /** the Worker that steps this race (race generation `gen`), or null on the main-thread path */
  worker?: { client: Pick<RaceWorkerClient, 'flushRec'>; gen: number } | null;
}

/**
 * One race's recording. On the main-thread path a RaceTap watches the sim this thread steps; on the Worker path the Worker's own
 * tap does (the inputs the director consumed live there) and `finish` asks it for the data. `finish` is idempotent.
 */
export class RaceCapture {
  readonly tap: RaceTap | null;
  private readonly started = new Date().toISOString();
  private result: Promise<RaceRecording | null> | null = null;
  private readonly config: Record<string, unknown>;
  constructor(private readonly o: CaptureOptions) {
    this.tap = o.worker ? null : new RaceTap(o.sim, o.dir);
    this.config = configOf(o.dir);
  }
  /** The player was put back on the track (main-thread path; the Worker logs its own). */
  recover(s: number): void { this.tap?.recover(s); }
  violation(kind: string, detail?: string): void { this.tap?.violation(kind, detail); }
  /** After each physics step (main-thread path). */
  after(): void { this.tap?.after(); }
  get done(): boolean { return this.result !== null; }

  /** The recording, built now: the flag, the player's ejection or the menu (`aborted`). null when it is not worth keeping (an aborted race under REC_MIN_ABORT_S) or the Worker could not give it. */
  finish(aborted: boolean): Promise<RaceRecording | null> {
    if (this.result) return this.result;
    const { dir, sim, worker } = this.o;
    let src: Promise<{ chunk: RecChunk; live: RecLive; cars: string[]; L: number; config: Record<string, unknown> } | null>;
    if (worker) src = worker.client.flushRec(worker.gen).then((r) => (r ? { chunk: r.chunk, live: r.live, cars: r.cars, L: r.L, config: r.config } : null));
    else src = Promise.resolve(this.tap ? { chunk: this.tap.drain(), live: liveOf(dir), cars: dir.cars.map((c) => c.number), L: dir.line.L, config: this.config } : null);
    this.result = src.then((d) => {
      if (!d) return null;
      const durationS = d.chunk.steps * 0.001;
      if (aborted && durationS < REC_MIN_ABORT_S) return null;
      const o = this.o;
      return buildRecording({
        trackId: o.trackId, fieldId: TRACKS[o.trackId]?.pace ?? '', seed: o.build.seed, laps: o.build.laps, aiVersion: String(R.AI_VERSION), buildSha: buildSha(),
        physics: sim.physics, build: o.build, config: d.config, cars: d.cars, L: d.L, carId: sim.assets.carId, started: this.started, durationS, aborted,
      }, new RecAssembler().add(d.chunk), d.live);
    });
    return this.result;
  }
}

type FetchFn = (input: string, init?: RequestInit) => Promise<Response>;
/** Pack (gzip, within REC_MAX_BYTES, cut if need be) and POST once. Silent to the player: a console line on failure. */
export async function uploadRecording(rec: RaceRecording, o: { url?: string; fetchFn?: FetchFn } = {}): Promise<boolean> {
  try {
    const packed = await packRecording(rec);
    if (!packed) { console.info('race recording: too large to send, dropped'); return false; }
    const headers: Record<string, string> = { 'Content-Type': packed.gzip ? 'application/gzip' : 'application/json' };
    const res = await (o.fetchFn ?? ((u, i) => fetch(u, i)))(o.url ?? racesUrl(), { method: 'POST', headers, body: packed.body as BodyInit });
    if (!res.ok && res.status !== 204) { console.info(`race recording: not accepted (HTTP ${res.status})`); return false; }
    return true;
  } catch (e) {
    console.info('race recording: not sent', (e as Error)?.message ?? e);
    return false;
  }
}

/** `?record=download`: the recording as a file (an <a download> on a Blob URL). */
export function downloadRecording(rec: RaceRecording): void {
  const url = URL.createObjectURL(new Blob([JSON.stringify(toWire(rec))], { type: 'application/json' }));
  const a = document.createElement('a');
  a.href = url; a.download = `race_${rec.trackId}_${rec.seed}${rec.aborted ? '_aborted' : ''}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
