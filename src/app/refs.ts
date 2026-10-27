// "Ghost & delta" (owner, 26 Oct 2026): ONE reference lap for the ghost car and the HUD delta, chosen per device:
//   session  your fastest valid lap of this session, a ghost from the lap that sets it
//   board    the leaderboard's all-time best on this track and car, rebuilt here from its input trace (GET ?ghost=)
//   real     the team's fastest real logger lap from the package's ghosts.json (Laguna only)
// RefController holds the three laps and answers "which one is in force and what do we call it"; the fallbacks are
// here (board empty / hidden / failed -> session best with a one-line note; real on a track without one -> session).
import type { GhostLap } from './physics-types';
import { GhostTrace, type GhostSlot } from './ghosts';
import { buildGhostLap, type LapSample } from '../scoreboard/ghostlap';

export type RefChoice = 'session' | 'board' | 'real';
export const REF_CHOICES: readonly RefChoice[] = ['session', 'board', 'real'];
export const REF_KEY = 'probeSim.ghostRef.v1';
export const SESSION_LAP_ID = 'session_best';
export const BOARD_LAP_ID = 'board_best';

export interface KVLike { getItem(k: string): string | null; setItem(k: string, v: string): void }

const defaultKV = (): KVLike | null => { try { return localStorage; } catch { return null; } };

/** The device's choice (default: session best), persisted in localStorage; every access guarded. */
export class RefPref {
  private v: RefChoice;
  private subs: (() => void)[] = [];
  constructor(private kv: KVLike | null = defaultKV()) {
    let raw: string | null = null;
    try { raw = this.kv?.getItem(REF_KEY) ?? null; } catch { raw = null; }
    this.v = (REF_CHOICES as readonly string[]).includes(raw ?? '') ? (raw as RefChoice) : 'session';
  }
  get choice(): RefChoice { return this.v; }
  set(c: RefChoice): void {
    if (c === this.v) return;
    this.v = c;
    try { this.kv?.setItem(REF_KEY, c); } catch { /* private window */ }
    for (const f of this.subs) f();
  }
  onChange(f: () => void): void { this.subs.push(f); }
}

export interface BoardGhost { lap: GhostLap; name: string; time: number }
/** idle: not asked yet; loading; ready; none: the board has no #1 lap (empty, hidden or no stored trace); failed: the fetch or rebuild failed. */
export type BoardState = 'idle' | 'loading' | 'ready' | 'none' | 'failed';

/** m:ss.cc (the delta panel's precision for a reference lap). */
export function fmtRefTime(t: number): string {
  const m = Math.floor(t / 60);
  return `${m}:${(t - m * 60).toFixed(2).padStart(5, '0')}`;
}

export interface ActiveRef {
  /** What is in force after the fallbacks. */
  kind: RefChoice;
  lap: GhostLap | null;
  trace: GhostTrace | null;
  /** The HUD's reference line: "vs session best 2:01.22", "vs all-time best 1:53.71 by Name", "vs real lap 1:59.32", or "no reference lap yet". */
  label: string;
}

export interface RefOptions {
  pref: RefPref;
  /** The package's fastest real lap (Laguna), or null. */
  real: GhostLap | null;
  length: number;
  grid: number;
  /** Fetch + rebuild the leaderboard's #1 (null: none). Rejects on failure. Called at most once per success; failures are retried on the next request. */
  loadBoard(): Promise<BoardGhost | null>;
  /** Where the ghost cars live (GhostManager.setSlot / setVisible); optional for tests. */
  cars?: { setSlot(slot: GhostSlot, lap: GhostLap | null, visible?: boolean): unknown; setVisible(id: string, on: boolean): void };
}

export class RefController {
  session: GhostLap | null = null;
  board: BoardGhost | null = null;
  boardState: BoardState = 'idle';
  private sessionTrace: GhostTrace | null = null;
  private boardTrace: GhostTrace | null = null;
  private realTrace: GhostTrace | null;
  private pending: Promise<void> | null = null;
  private lastKey = '';

  constructor(readonly o: RefOptions) {
    this.realTrace = o.real ? new GhostTrace(o.real, o.grid, o.length) : null;
    o.pref.onChange(() => { this.ensureBoard(); this.sync(); });
    this.sync();
  }

  get hasReal(): boolean { return this.o.real !== null; }
  get choice(): RefChoice { return this.o.pref.choice; }

  /** A new session best (Hotlap mode, on a valid lap that beats the last). */
  setSession(lap: GhostLap): void {
    this.session = lap;
    this.sessionTrace = new GhostTrace(lap, this.o.grid, this.o.length);
    this.o.cars?.setSlot('session', lap, false);
    this.lastKey = '';   // the ghost car was rebuilt (same id): show it again
    this.sync();
  }
  /** A fresh session (mode start / restart). */
  clearSession(): void {
    this.session = null; this.sessionTrace = null;
    this.o.cars?.setSlot('session', null);
    this.lastKey = '';
    this.sync();
  }

  /** Fetch the leaderboard's #1 when the board reference is in force and nothing is cached or under way. */
  ensureBoard(): Promise<void> {
    if (this.choice !== 'board' || this.boardState === 'ready' || this.boardState === 'none') return this.pending ?? Promise.resolve();
    if (this.pending) return this.pending;
    this.boardState = 'loading';
    this.pending = (async () => {
      try {
        const b = await this.o.loadBoard();
        if (b) {
          this.board = b; this.boardTrace = new GhostTrace(b.lap, this.o.grid, this.o.length); this.boardState = 'ready';
          this.o.cars?.setSlot('board', b.lap, false);
        } else this.boardState = 'none';
      } catch { this.boardState = 'failed'; }
      this.pending = null;
      this.lastKey = '';
      this.sync();
    })();
    return this.pending;
  }

  /** The reference in force, after the fallbacks. */
  active(): ActiveRef {
    const sess = (note?: string): ActiveRef => this.session && this.sessionTrace
      ? { kind: 'session', lap: this.session, trace: this.sessionTrace, label: `vs session best ${fmtRefTime(this.session.lap_time_s)}${note ? ` · ${note}` : ''}` }
      : { kind: 'session', lap: null, trace: null, label: `no reference lap yet${note ? ` · ${note}` : ''}` };
    const c = this.choice;
    if (c === 'real') {
      if (this.o.real && this.realTrace) return { kind: 'real', lap: this.o.real, trace: this.realTrace, label: `vs real lap ${fmtRefTime(this.o.real.lap_time_s)}` };
      return sess('no real lap on this track');
    }
    if (c === 'board') {
      if (this.board && this.boardTrace) return { kind: 'board', lap: this.board.lap, trace: this.boardTrace, label: `vs all-time best ${fmtRefTime(this.board.time)} by ${this.board.name}` };
      if (this.boardState === 'loading' || this.boardState === 'idle') return sess('loading the all-time best…');
      return sess(this.boardState === 'failed' ? 'all-time best unavailable' : 'no all-time best on the board yet');
    }
    return sess();
  }

  /** Show the ghost car of the reference in force (and only that one of the player's own); cheap, called per frame. */
  sync(): void {
    const a = this.active();
    const key = `${a.kind}:${a.lap?.id ?? ''}`;
    if (key === this.lastKey) return;
    this.lastKey = key;
    const cars = this.o.cars;
    if (!cars) return;
    cars.setVisible(SESSION_LAP_ID, a.lap?.id === SESSION_LAP_ID);
    cars.setVisible(BOARD_LAP_ID, a.lap?.id === BOARD_LAP_ID);
    if (a.kind === 'real' && a.lap) cars.setVisible(a.lap.id, true);
  }
}

// ---------------------------------------------------------------- the session's own laps, sampled as they are driven

/**
 * Collects (t, s, v) at the timing ticks of the lap in progress. `feed` is called every physics step with the timer's
 * lap number; a new lap number closes the finished lap's samples (held for `finish`). The lap that just completed is the
 * previous one: the crossing tick already reports the next lap's number.
 */
export class LapRecorder {
  private cur: LapSample[] = [];
  private prev: LapSample[] = [];
  private lapNo = -1;
  private lastS = NaN;
  feed(started: boolean, lapNumber: number, t: number, s: number, v: number): void {
    if (!started) { this.cur = []; this.prev = []; this.lapNo = -1; this.lastS = NaN; return; }
    if (lapNumber !== this.lapNo) { this.prev = this.cur; this.cur = []; this.lapNo = lapNumber; this.lastS = NaN; }
    if (s === this.lastS) return;   // s moves at the 200 Hz timing ticks
    this.lastS = s;
    this.cur.push({ t, s, v: Math.abs(v) });
  }
  /** The completed lap as a ghost lap (call from onLap, before the next lap's first tick). */
  finish(lapTime: number, length: number, grid: number, id = SESSION_LAP_ID, driver = 'You'): GhostLap | null {
    const built = buildGhostLap(this.prev, lapTime, length, grid, { id, driver, label: `${driver} ${fmtRefTime(lapTime)}`, kind: 'session' });
    return built;
  }
  clear(): void { this.cur = []; this.prev = []; this.lapNo = -1; this.lastS = NaN; }
}
