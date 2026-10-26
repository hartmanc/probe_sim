// Game modes: the interface every mode implements, the context the
// composition root (index.ts) hands it, and ModeHost (switching; unit-tested).
//
// Per rendered frame, index.ts does, while no menu is open:
//   input → driving actions (shift, camera, reset → mode.reset(), …)
//   for each 1 ms physics step: HotlapSim.step() (src/scoreboard/sim.ts: input sampled
//     on a 100 Hz grid, vehicle step, every 5th step projection + lap timer + gear
//     schedule); mode.step(STEP); mode.onLap(lap) when the player completes a lap
//   mode.frame(dt, now); hud.update({...core, ...mode.hud()}); render
// While a menu is open nothing is stepped and audio is suspended.
import type * as THREE from 'three';
import type { TrackMarks } from '../marks';
import type { MenuEntry } from '../menu';
import type { GhostLap, GhostsJson, PhysicsApi, TrackJson, VehicleLike } from '../physics-types';
import type { GhostManager } from '../ghosts';
import type { Hud } from '../hud';
import type { Input } from '../input';
import type { Lap, LapTimer } from '../timing';
import type { Menu } from '../menu';
import type { HotlapSim } from '../../scoreboard';

/** Per-frame engine data for one AI car (FieldAudio's FieldCar; src/app/audio-field.ts). */
export interface FieldAudioCar {
  id: string | number;
  pos: [number, number, number]; vel: [number, number, number];
  rpm: number; throttle: number; redline: number;
  family: string;
  trim?: number; muffler?: number;
}
/**
 * The AI engine sounds as the race mode sees them: FieldAudio (audio-field.ts) satisfies this structurally.
 * index.ts builds it (on by default; pause-menu toggle, `?fieldaudio=0`) and hands it over through RaceServices.
 */
export interface FieldAudioLike {
  update(listener: { pos: [number, number, number]; vel: [number, number, number]; quat?: [number, number, number, number] }, cars: FieldAudioCar[]): void;
  dispose(): void;
}
/** How one car sounds: family, pitch trim, muffler and the rpm factor (index.json `cars[num]`, else guessed). */
export interface FieldCarSound { family: string; trim: number; muffler: number; rpmScale: number }
export interface FieldAudioHook {
  /** null until the family index has loaded (or while it is missing: the hook retries). */
  readonly audio: FieldAudioLike | null;
  /** Resolves when the first index fetch settled (sounds are re-resolved then). */
  ready?: Promise<void>;
  /** A car's sound (index.json `cars` entry by field key `id`, else number; else identity.json engine family / make / model, else cylinders + layout). */
  sound(car: { number: string; id?: string; identity: unknown; engine: { layout: string; cylinders: number; exhaustNote?: string | null } }): FieldCarSound;
  /** Per frame while racing: retries a missing index now and then. */
  tick?(): void;
  dispose(): void;
}
/** The pit-exit cone line (trackmath.ts PitExitCones via scenery.ts pitExitConeWatcher()): true when the player crossed it. */
export interface ConeLineLike {
  /** Feed the player's position (world ENU x, y) once per frame; true on a crossing. */
  update(x: number, y: number): boolean;
  /** Forget the previous position (after a reset / recovery / restart). */
  clear(): void;
}

/** What only the race mode needs (index.ts); optional so tests and the hot lap can omit it. */
export interface RaceServices {
  /** The player's car: the director steps it through `sim.stepVehicle`; `sim.record` is turned off in a race. */
  sim: HotlapSim;
  scene: THREE.Scene;
  menu: Menu;
  /** Back to the main menu (results screen). */
  mainMenu(): void;
  quality: { maxAiCarsDrawn: number; shadows: boolean; aiShadowCasters: number; /** phones and tablets race the 40 pace neighbours (field-select.ts); absent = desktop */ device?: 'phone' | 'tablet' | 'desktop' };
  /** Impact thump (audio.impact), normal speed m/s. */
  impact(speedNormal: number): void;
  /** Field engine sounds (null: off / not available yet, e.g. no AudioContext). Called when the race wants them. */
  fieldAudio?(): FieldAudioHook | null;
  /** The pause-menu "AI engine sounds" setting (false also under ?fieldaudio=0); read every frame. */
  fieldAudioEnabled?(): boolean;
  /** The pit-exit cone line (null: no data). */
  coneLine?(): ConeLineLike | null;
  /** location.search, for the dev overrides (?seed=, ?laps=). */
  search: string;
}

export type ModeId = 'hotlap' | 'race';

/** Per-mode HUD state, merged into the core HUD frame. */
export interface ModeHud {
  /** Top-centre banner (null: none). */
  banner: string | null;
  /** Show the timing panel. */
  timing: boolean;
  /** Delta to the reference (null: no reference / not timing). */
  delta: number | null;
  /** Show the delta bar at all. */
  showDelta: boolean;
}

/** Shared sim services a mode may use. Owned by index.ts; modes never construct these. */
export interface ModeContext {
  physics: PhysicsApi;
  track: TrackJson;
  /** The player's car. A getter: every reset builds a new Vehicle (HotlapSim), so read it each time, never cache it. */
  readonly vehicle: VehicleLike;
  timer: LapTimer;
  ghosts: GhostManager;
  ghostData: GhostsJson;
  hud: Hud;
  input: Input;
  /** Sim time since the last start procedure / reset (s); stops while the car is launched. */
  simTime(): number;
  /** Player's projected distance along the track (m), updated at 200 Hz. */
  s(): number;
  /** Player position in the scene (for ghost hiding near the cockpit cameras). */
  playerPos(): THREE.Vector3;
  /** Rolling start before T11 (or a standing start behind the line without a T11); resets timer and sim time. */
  /** Rolling start = HotlapSim reset. `launch`: the hot lap's auto-launch (LAUNCH_S of full throttle on the racing line
   *  with a countdown, then the driver takes over); a race never launches. */
  rollingStart(o?: { launch?: boolean }): void;
  /** Put the car back on the track centreline at distance s, stopped (keeps the lap timer running). */
  recoverAt(s: number): void;
  /** The ghost lap whose gear schedule auto-shift follows (null: rpm rules). */
  setScheduleLap(lap: GhostLap | null): void;
  toast(msg: string): void;
  /** Race-only services (see RaceServices). */
  race?: RaceServices;
  /** Tyre marks, dust and smoke (marks.ts): a mode feeds it the AI cars it draws. */
  marks?: TrackMarks;
}

export interface GameMode {
  readonly id: ModeId;
  readonly label: string;
  /** Enter the mode: run its start procedure. */
  start(): void;
  /** Pause menu → Restart: the start procedure again, fresh session. */
  restart(): void;
  /** Reset control (Back / R): hot lap → rolling start; race → recover on track. */
  reset(): void;
  /** Every physics step (dt = 0.001 s), after the player's vehicle step. */
  step(dt: number): void;
  /** The player completed a lap. */
  onLap(lap: Lap): void;
  /** Once per rendered frame after the physics steps (ghosts, AI cars, banners). */
  frame(dt: number, now: number): void;
  hud(): ModeHud;
  /** Sim time scale for this frame (1 when absent): the race returns 10 while a stop-and-go is fast-forwarded. */
  timeScale?(): number;
  /** Mode-specific pause menu rows (inserted after ABS). */
  pauseEntries(): MenuEntry[];
  /** Leave the mode: hide its objects, drop listeners. */
  dispose(): void;
}

export type ModeFactory<C> = (ctx: C) => GameMode;

/** Owns the current mode; switching disposes the old one before the new one starts. */
export class ModeHost<C = ModeContext> {
  private cur: GameMode | null = null;
  constructor(private factories: Record<ModeId, ModeFactory<C>>, private ctx: C) {}

  get current(): GameMode | null { return this.cur; }

  /** Switch to (or restart into) mode id. Picking the current mode again gives a fresh instance. */
  set(id: ModeId): GameMode {
    this.cur?.dispose();
    this.cur = null;
    const m = this.factories[id](this.ctx);
    this.cur = m;
    m.start();
    return m;
  }

  restart(): void { this.cur?.restart(); }

  dispose(): void { this.cur?.dispose(); this.cur = null; }
}

export const MODE_LABELS: Record<ModeId, string> = { hotlap: 'Hot lap', race: 'Race' };
