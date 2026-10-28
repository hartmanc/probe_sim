// Hot lap: rolling start before T11 so lap 1 is a flying lap, ghost laps, lap
// timer, delta to a reference ghost and the corner min-speed table.
//
// HotlapLoop is the live fixed-step loop (docs/scoreboard.md §3.1): the player's car is stepped through the
// deterministic HotlapSim, input is sampled on its 100 Hz grid and held, shift presses are latched until the
// next sample, so the recorded trace replays to the same lap time on the server.
import { minAround, TRACE_GRID_M, type Lap } from '../timing';
import { STEP, type HotlapSim, type InputType, type RawInput } from '../../scoreboard';
import { LAUNCH_S } from '../../scoreboard/config';
import { fmtTime, type CornerRow } from '../hud';
import { LapRecorder, type RefChoice, type RefController } from '../refs';
import type { MenuEntry } from '../menu';
import type { GameMode, ModeContext, ModeHud } from './mode';
import { pitExitConeWatcher } from '../scenery';

/** The "Ghost & delta" row (Start menu settings and the pause menu): session best, the board's all-time best, the real lap. */
export function ghostRefEntry(refs: RefController): MenuEntry {
  return {
    kind: 'choice', id: 'ghostRef', label: 'Ghost & delta',
    options: ghostRefOptions(refs.hasReal),
    get: () => refs.choice, set: (v) => refs.o.pref.set(v as RefChoice),
    note: refs.o.pref.choice === 'real' && !refs.hasReal ? 'no real lap here: session best' : undefined,
  };
}
export function ghostRefOptions(hasReal: boolean): { value: string; label: string; disabled?: boolean }[] {
  return [
    { value: 'session', label: 'Session best' },
    { value: 'board', label: 'All-time best' },
    { value: 'real', label: hasReal ? 'Real lap' : 'Real lap (Laguna only)', disabled: !hasReal },
  ];
}

export function createHotLap(ctx: ModeContext): GameMode {
  const { ghosts, timer, hud, track } = ctx;
  const { refs } = ctx;
  const recorder = new LapRecorder();
  // the gear schedule auto-shift follows is the fastest real lap whatever the reference is (the reference only moves the
  // ghost car and the delta; the physics and the trace are as before)
  const applyRef = () => ctx.setScheduleLap(ghosts.fastestReal());
  let shownRef = '';

  const cornerTable = (lap: Lap) => {
    const r = refs.active().lap;
    if (!r) return;
    const rows: CornerRow[] = track.corners.map((c) => ({
      name: c.name,
      player: minAround(lap.speedTrace, TRACE_GRID_M, c.s),
      ref: minAround(r.v_mps, ctx.ghostData.s_grid_m, c.s),
    }));
    hud.showCorners(lap, r.driver, rows);
  };

  // pit-exit cones (scenery.json pit_exit_cones): crossing the line is a black flag; shown as a toast and, for a few
  // seconds, the banner with the session count
  const cones = pitExitConeWatcher();
  let blackFlags = 0, flagUntil = -1;
  const watchCones = () => {
    if (!cones) return;
    const p = ctx.vehicle.state.pos;
    if (!cones.update(p[0], p[1])) return;
    blackFlags++;
    flagUntil = ctx.simTime() + 4;
    ctx.toast('BLACK FLAG · crossed the pit-exit cones');
  };

  // the pit-exit blend line (scenery.json blend_line; HotlapSim invalidates the lap): the same black-flag words as the race
  let blendSeen = 0;
  const watchBlend = () => {
    const b = ctx.blendFlags();
    if (b.count > blendSeen) ctx.toast(`Black flag: ${b.reason ?? 'crossed the blend line'} (lap invalid)`);
    blendSeen = b.count;
  };

  // the team's ghosts toggle one by one; the player's own (session best, all-time best) follow the "Ghost & delta" choice
  const ghostsPage = (): MenuEntry[] => [
    ghostRefEntry(refs),
    ...ghosts.ghosts.filter((g) => !g.slot).map((g): MenuEntry => ({
      kind: 'toggle', id: `ghost:${g.lap.id}`, label: g.lap.label,
      get: () => g.visible, set: (on) => ghosts.setVisible(g.lap.id, on),
    })),
    { kind: 'back', id: 'back', label: 'Back' },
  ];

  return {
    id: 'hotlap',
    label: 'Hot lap',
    start() {
      ghosts.group.visible = true;
      applyRef();
      timer.clearSession();
      recorder.clear();
      refs.clearSession();
      void refs.ensureBoard();
      hud.hideCorners();
      hud.setBanner(null);
      blackFlags = 0; flagUntil = -1; blendSeen = 0;
      cones?.clear();
      ctx.rollingStart({ launch: true });
    },
    restart() { this.start(); },
    reset() { cones?.clear(); ctx.rollingStart({ launch: true }); ctx.toast('Reset: launching'); },
    step() {
      // timing is fed by the core; the session's laps are sampled here (every step, kept at the 200 Hz ticks) so the best one
      // can become a ghost
      recorder.feed(timer.started, timer.lapNumber, timer.current(ctx.simTime()), ctx.s(), ctx.vehicle.state.speed);
    },
    onLap(lap) {
      if (timer.best === lap) {   // valid and the session's fastest so far: it is the session-best ghost from now on
        const g = recorder.finish(lap.time, track.length_m, ctx.ghostData.s_grid_m);
        if (g) refs.setSession(g);
      }
      cornerTable(lap);
      ctx.toast(`Lap ${lap.n}: ${fmtTime(lap.time)}${lap.valid ? '' : ' (invalid)'}`);
    },
    frame() {
      watchCones();
      watchBlend();
      const tau = timer.started ? timer.current(ctx.simTime()) : null;
      ghosts.update(tau, ctx.playerPos());
    },
    hud(): ModeHud {
      const act = refs.active();
      if (act.label !== shownRef) { shownRef = act.label; hud.setRefName(act.label); }
      const delta = timer.started && act.trace ? timer.current(ctx.simTime()) - act.trace.tAt(ctx.s()) : null;
      const t = ctx.simTime();
      // the launch countdown (3, 2, 1, GO) wins over the black-flag banner
      const launch = t < LAUNCH_S ? String(Math.ceil(LAUNCH_S - t)) : t < LAUNCH_S + 0.8 ? 'GO' : null;
      const flag = flagUntil >= 0 && t >= flagUntil - 4 && t < flagUntil ? `BLACK FLAG · pit-exit cones${blackFlags > 1 ? ` (${blackFlags})` : ''}` : null;
      return { banner: launch ?? flag, timing: true, delta, showDelta: true };
    },
    pauseEntries(): MenuEntry[] {
      return [ghostRefEntry(refs), ...(ghosts.ghosts.some((g) => !g.slot) ? [{ kind: 'submenu', id: 'ghosts', label: 'Ghosts', page: () => ({ title: 'Ghosts', entries: ghostsPage }) } as MenuEntry] : [])];
    },
    dispose() {
      ghosts.group.visible = false;
      hud.hideCorners();
    },
  };
}

/** What the live loop reads from the device at each 100 Hz sample. */
export interface LiveSample { steer: number; throttle: number; brake: number; handbrake: boolean; tag: InputType }

/**
 * The live hot-lap loop: frame dt → fixed 1 ms HotlapSim steps (same accumulator as before). Owns the shift
 * latches and the per-lap input-type counts (most-used device at the 100 Hz samples since the last line crossing).
 */
export class HotlapLoop {
  acc = 0;
  /** Called after every physics step (mode.step). */
  onStep: (() => void) | null = null;
  /** A lap completed; `tag` is the input type used most during it. The trace is still exactly at the lap's step. */
  onLap: ((lap: Lap, tag: InputType) => void) | null = null;
  /** Checked after a lap event: true stops stepping for this frame (a prompt opened). */
  halt: () => boolean = () => false;
  /** Sim time scale for this frame: 1 normally; the race mode returns the director's scale (10 while a stop-and-go
   *  is fast-forwarded with the car held in the penalty box). */
  timeScale: () => number = () => 1;
  private up = false;
  private down = false;
  private tags: Record<InputType, number> = { pad: 0, keys: 0, phone: 0 };

  constructor(readonly sim: HotlapSim, private read: () => LiveSample) {}

  private readonly sample = (): RawInput => {
    if (this.sim.simTime < this.sim.launchUntil) {   // auto-launch: the car drives itself
      this.up = false; this.down = false;
      return { steer: this.sim.lineSteer(), throttle: 1, brake: 0, handbrake: false, shiftUp: false, shiftDown: false };
    }
    const r = this.read();
    this.tags[r.tag]++;
    const raw: RawInput = { steer: r.steer, throttle: r.throttle, brake: r.brake, handbrake: r.handbrake, shiftUp: this.up, shiftDown: this.down };
    this.up = false; this.down = false; // latched until the next sample
    return raw;
  };

  /** The shift presses latched since the last sample, cleared (the race Worker takes them with each frame's input). */
  takeShifts(): { up: boolean; down: boolean } { const r = { up: this.up, down: this.down }; this.up = false; this.down = false; return r; }

  shiftUp(): void { this.up = true; }
  shiftDown(): void { this.down = true; }

  /** Rolling start: a fresh vehicle + surface in the sim and a new recording. */
  reset(): void {
    this.sim.reset();
    this.up = false; this.down = false;
    this.clearTags();
  }

  private clearTags(): void { this.tags = { pad: 0, keys: 0, phone: 0 }; }

  /** Most used input type since the last line crossing / reset. */
  get tag(): InputType {
    const t = this.tags;
    return t.pad >= t.keys && t.pad >= t.phone && t.pad > 0 ? 'pad' : t.phone > t.keys ? 'phone' : 'keys';
  }

  /** Advance by a rendered frame's dt (already capped by the caller). */
  advance(dt: number): void {
    this.acc += dt * this.timeScale();
    while (this.acc >= STEP) {
      const ev = this.sim.step(this.sample);
      this.onStep?.();
      this.acc -= STEP;
      if (!ev) continue;
      if (ev === 'start') { this.clearTags(); continue; }
      const tag = this.tag;
      this.clearTags();
      this.onLap?.(ev, tag);
      if (this.halt()) break;
    }
  }
}
