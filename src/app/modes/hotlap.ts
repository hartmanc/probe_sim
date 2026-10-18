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
import type { Ghost } from '../ghosts';
import type { MenuEntry } from '../menu';
import type { GameMode, ModeContext, ModeHud } from './mode';
import { pitExitConeWatcher } from '../scenery';

export function createHotLap(ctx: ModeContext): GameMode {
  const { ghosts, timer, hud, track } = ctx;
  let ref: Ghost | null = (() => {
    const fr = ghosts.fastestReal();
    return ghosts.ghosts.find((g) => g.lap === fr) ?? ghosts.ghosts[0] ?? null;
  })();

  const applyRef = () => {
    hud.setRefName(ref?.lap.label ?? '');
    ctx.setScheduleLap(ref?.lap ?? null);
  };

  const cornerTable = (lap: Lap) => {
    if (!ref) return;
    const r = ref;
    const rows: CornerRow[] = track.corners.map((c) => ({
      name: c.name,
      player: minAround(lap.speedTrace, TRACE_GRID_M, c.s),
      ref: minAround(r.lap.v_mps, ctx.ghostData.s_grid_m, c.s),
    }));
    hud.showCorners(lap, r.lap.driver, rows);
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

  const ghostsPage = (): MenuEntry[] => [
    ...ghosts.ghosts.map((g): MenuEntry => ({
      kind: 'toggle', id: `ghost:${g.lap.id}`, label: g.lap.label,
      get: () => g.visible, set: (on) => ghosts.setVisible(g.lap.id, on),
    })),
    {
      kind: 'choice', id: 'ref', label: 'Delta reference',
      options: ghosts.ghosts.map((g) => ({ value: g.lap.id, label: g.lap.label })),
      get: () => ref?.lap.id ?? '',
      set: (id) => { ref = ghosts.ghosts.find((g) => g.lap.id === id) ?? ref; applyRef(); },
      disabled: ghosts.ghosts.length < 2,
    },
    { kind: 'back', id: 'back', label: 'Back' },
  ];

  return {
    id: 'hotlap',
    label: 'Hot lap',
    start() {
      ghosts.group.visible = true;
      applyRef();
      timer.clearSession();
      hud.hideCorners();
      hud.setBanner(null);
      blackFlags = 0; flagUntil = -1;
      cones?.clear();
      ctx.rollingStart({ launch: true });
    },
    restart() { this.start(); },
    reset() { cones?.clear(); ctx.rollingStart({ launch: true }); ctx.toast('Reset: launching'); },
    step() { /* nothing per step: timing is fed by the core */ },
    onLap(lap) {
      cornerTable(lap);
      ctx.toast(`Lap ${lap.n}: ${fmtTime(lap.time)}${lap.valid ? '' : ' (invalid)'}`);
    },
    frame() {
      watchCones();
      const tau = timer.started ? timer.current(ctx.simTime()) : null;
      ghosts.update(tau, ctx.playerPos());
    },
    hud(): ModeHud {
      const delta = timer.started && ref ? timer.current(ctx.simTime()) - ref.trace.tAt(ctx.s()) : null;
      const t = ctx.simTime();
      // the launch countdown (3, 2, 1, GO) wins over the black-flag banner
      const launch = t < LAUNCH_S ? String(Math.ceil(LAUNCH_S - t)) : t < LAUNCH_S + 0.8 ? 'GO' : null;
      const flag = flagUntil >= 0 && t >= flagUntil - 4 && t < flagUntil ? `BLACK FLAG · pit-exit cones${blackFlags > 1 ? ` (${blackFlags})` : ''}` : null;
      return { banner: launch ?? flag, timing: true, delta, showDelta: true };
    },
    pauseEntries(): MenuEntry[] {
      if (!ghosts.ghosts.length) return [];
      return [{ kind: 'submenu', id: 'ghosts', label: 'Ghosts', page: () => ({ title: 'Ghosts', entries: ghostsPage }) }];
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
