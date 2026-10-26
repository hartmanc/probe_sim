// Race: RACE_LAPS laps (?laps= to shorten) against the 2026 Lemons field on the page's track. The race core is
// src/physics/ai (RaceDirector, see its NOTES.md); this file wires it into the app:
//
// - The player's car stays the HotlapSim car (input sampled on its 100 Hz grid, 200 Hz timing, gear schedule).
//   In a race `sim.stepVehicle` hands each 1 ms step to `director.step(STEP, input)`, which steps every car
//   (the player's with that input), resolves car-vs-car contacts and runs the rules; `sim.record` is off.
// - The director is built after a rolling start (fresh Vehicle + Surface, step counter 0) and is rebuilt on
//   every restart with a new seed, so a race is reproducible from (seed, AI_VERSION) and the player's inputs.
// - Per frame: director.hud() → race HUD + toasts; director.poses() → FieldCars (AI rigs); results at the end.
import * as THREE from 'three';
import { race as R, createTrackSurface, type DriverInput, type Surface, type PitLaneJson } from '../../physics';
import type { RaceDirector, RaceHud } from '../../physics/ai/race';
import type { RaceLine } from '../../physics/ai/line';
import type { PaceJson } from '../../physics/ai/field';
import { STEP, type SimAssets } from '../../scoreboard';
import { fmtTime } from '../hud';
import type { MenuEntry, MenuPage } from '../menu';
import { loadFieldData, loadFieldModel, type FieldData, type FieldModelInfo } from '../loader';
import { FieldCars, identityColor, type FieldCarInfo } from '../field-cars';
import { RaceHudDom, raceHudView, raceTable, resultRows, rowStatus, type TableRow } from '../race-hud';
export { rowStatus, type RowStatus } from '../race-hud';
import { fmtLapTime, fmtMetres, setBoardContext, submitRace, type RaceResult, type SubmitOutcome } from '../scoreboard-client';
import { LIMITS, TRACKS, resolveTrackId } from '../../scoreboard/config';
import { TRACK, TRACK_ID } from '../track-choice';
import { FieldAudio, familyFor, FIELD_VOICES_DESKTOP, FIELD_VOICES_PHONE, type FamilyIndex, type Layout } from '../audio-field';
import type { ConeLineLike, FieldAudioCar, FieldAudioHook, FieldAudioLike, FieldCarSound, GameMode, ModeContext, ModeHud, RaceServices } from './mode';

/** 5 since 17 Oct 2026 (owner: 10 is a long time alone in a sim); the server validates against the same number. */
export const RACE_LAPS: number = LIMITS.raceLaps;
export const PLAYER_NUMBER = '619';
// AI shadows: quality.aiShadowCasters nearest AI cars cast shadow-map shadows inside the sun's ±quality.shadowBoxM box
// (desktop 12 cars / ±30 m / 4096 px; phone and ?aishadows=0: none); the rest keep a contact-shadow blob (src/app/quality.ts).

// ---------------------------------------------------------------- pure helpers (unit-tested)

export interface RaceOverrides {
  /** ?seed=<int>: the first race uses it (restarts draw new seeds). */
  seed: number | null;
  /** ?laps=<1..10>: shorter race for testing (not posted to the scoreboard unless ?devsubmit=1). */
  laps: number | null;
  /** ?devsubmit=1: allow posting a shortened race (local API testing). */
  devSubmit: boolean;
}

export function parseRaceOverrides(search: string): RaceOverrides {
  const q = new URLSearchParams(search);
  const seedRaw = q.get('seed'), lapsRaw = q.get('laps');
  const seed = seedRaw !== null && /^\d{1,10}$/.test(seedRaw.trim()) ? Number(seedRaw) >>> 0 : null;
  const n = lapsRaw !== null ? Math.round(Number(lapsRaw)) : NaN;
  return { seed, laps: Number.isFinite(n) && n >= 1 && n <= RACE_LAPS ? n : null, devSubmit: q.get('devsubmit') === '1' };
}

/** A fresh race seed (shown in the pause menu and on the results; `?seed=` reuses one). */
export function newSeed(rand: () => number = Math.random): number {
  return 1 + Math.floor(rand() * 999_999_998);
}

/** The scoreboard payload for a finished race (`submitRace`). */
/** The race board's AI-version slot also carries the lap count, so 5-lap distances never compete with old 10-lap ones. */
export const raceBoardVersion = (aiVersion: number | string, laps = RACE_LAPS): string => `${aiVersion}-${laps}L`;

export function raceResultFor(rows: TableRow[], o: { seed: number; aiVersion: number | string; finished: boolean }): RaceResult | null {
  const me = rows.find((r) => r.player);
  if (!me) return null;
  return {
    metres: Math.round(Math.max(0, me.metres) * 10) / 10,
    laps: Math.max(0, me.laps),
    aiVersion: String(o.aiVersion),
    seed: o.seed,
    position: me.position,
    // finished = all laps completed: only then is there a race time, and the time is the score
    finished: o.finished && me.time != null && (me.status === 'running' || me.status === 'finished'),
    ...(o.finished && me.time != null ? { time: me.time } : {}),
  };
}

/** The physics surface factory for the race (same options as HotlapSim's private surface). */
export function surfaceFactory(a: SimAssets): () => Surface {
  const farGrid = a.scenery?.far?.heightfield;
  const far = farGrid && a.farHeightfield
    ? { heightfield: a.farHeightfield, x0: farGrid.x0, y0: farGrid.y0, dx: farGrid.dx, nx: farGrid.nx, ny: farGrid.ny } : null;
  const pit = a.scenery?.pit_lane ?? null, zones = a.scenery?.paved_zones ?? null;
  const pitLane: PitLaneJson | null = pit || zones
    ? { spacing_m: 1, fractions: (pit ?? zones)!.fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] }
    : null;
  return () => createTrackSurface(a.track, a.heightfield, { far, pitLane, sausages: a.scenery?.sausages ?? null, kerbs: a.scenery?.kerbs ?? null, terrainOverride: a.scenery?.terrain_override ?? null });
}

const lineCache = new WeakMap<object, RaceLine>();
function raceLine(a: SimAssets): RaceLine {
  let l = lineCache.get(a.track);
  if (!l) {
    l = new R.RaceLine(a.track, a.ghosts as unknown as ConstructorParameters<typeof R.RaceLine>[1]);
    const cones = (a.scenery as { pit_exit_cones?: { pts?: number[][] } | null } | null | undefined)?.pit_exit_cones;
    if (cones?.pts?.length) l.restrictLeft(cones.pts);   // the AI keeps right of the pit-exit cones, as the player must
    lineCache.set(a.track, l);
  }
  return l;
}

/** The per-track AI race parameters (TRACKS[id].ai) as RaceConfig fields; absent = Laguna's values (1, 1, 0). */
export function raceAiConfig(trackId: string): { followScale: number; laneMargin: number; shiftGrip: number } {
  const ai = TRACKS[resolveTrackId(trackId)].ai;
  return { followScale: ai?.followScale ?? 1, laneMargin: ai?.laneMargin ?? 1, shiftGrip: ai?.shiftGrip ?? 0 };
}

/** Build the RaceDirector for the player's current HotlapSim car (call right after a rolling start). */
export function buildDirector(sim: RaceServices['sim'], field: FieldData, o: { seed: number; laps: number }): RaceDirector {
  const a = sim.assets;
  const makeSurface = surfaceFactory(a);
  const pit = a.scenery?.pit_lane ?? null;
  return new R.RaceDirector({
    line: raceLine(a), surface: makeSurface(), makeSurface,
    probeJson: a.carJson, pace: field.pace as PaceJson, identity: field.identity ?? null,
    pitLane: pit ? { spacing_m: 1, ...pit } : null,
    collisionWorld: sim.collision,
    playerVehicle: sim.vehicle, playerSurface: sim.surface,
  }, { laps: o.laps, seed: o.seed, playerNumber: PLAYER_NUMBER, greenWindow: [5, 30], ...raceAiConfig(TRACK_ID) });
}

/** FieldCars inputs for every AI car of a director (colour from identity.json, size from its physics spec). */
export function fieldCarInfos(d: RaceDirector): FieldCarInfo[] {
  return d.cars.filter((c) => !c.isPlayer).map((c) => {
    const sp = c.spec, id = c.identity as Record<string, unknown> | null;
    const idH = id && typeof id.height_m === 'number' ? id.height_m : undefined;
    return {
      number: c.number, idx: c.idx, color: identityColor(id) ?? c.tint, physicsRadius: sp.wheel.radius,
      dims: {
        length: sp.hull.front - sp.hull.rear, width: 2 * sp.hull.halfWidth, height: idH ?? sp.hull.roof,
        wheelbase: sp.wheelbase, trackFront: sp.trackFront, trackRear: sp.trackRear, tyreRadius: sp.wheel.radius,
      },
    };
  });
}

/**
 * The models to load for a race: each models.json row (one global pool) whose `id` (loader.ts fills it with the number
 * when absent) is an AI car's model key (RaceCar.model: pace `model_id`, else identity `model_id`, else its `id`, else
 * the number), paired with that car's number
 * (FieldCars is keyed by number), while the car still shows its placeholder. A car without a model row keeps the
 * placeholder. Laguna (no ids anywhere) matches by number as before.
 */
export function modelQueue(models: readonly FieldModelInfo[], cars: readonly { id: string; model?: string; number: string; isPlayer: boolean }[], kindOf: (num: string) => 'placeholder' | 'model' | null): { car: string; model: FieldModelInfo }[] {
  const byKey = new Map<string, FieldModelInfo>();
  for (const m of models) { const k = m.id ?? m.number; if (!byKey.has(k)) byKey.set(k, m); }
  const out: { car: string; model: FieldModelInfo }[] = [];
  const seen = new Set<string>();
  // models.json order (the load order), one entry per car; two cars may share a model row
  for (const m of models) {
    const k = m.id ?? m.number;
    if (byKey.get(k) !== m) continue;
    for (const c of cars) {
      if (c.isPlayer || (c.model ?? c.id) !== k || seen.has(c.number) || kindOf(c.number) !== 'placeholder') continue;
      seen.add(c.number); out.push({ car: c.number, model: m });
    }
  }
  return out;
}

/** Per-car pitch trim 0.96..1.04 (stable per number): the fallback when index.json has no `cars` entry. */
export function audioTrim(num: string): number {
  let h = 2166136261;
  for (const ch of num) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return 0.96 + ((h >>> 0) % 1000) / 1000 * 0.08;
}
/** Muffler 0 (open) … 1 (muffled) from identity's exhaust note: index.json's `muffler` table when given, else built-in rules. */
export function mufflerFor(note: string | null | undefined, table?: unknown, dflt?: unknown): number {
  const d = typeof dflt === 'number' && dflt >= 0 && dflt <= 1 ? dflt : 0.3;
  if (!note) return d;
  if (Array.isArray(table)) {
    for (const row of table) {
      if (!Array.isArray(row) || typeof row[0] !== 'string' || typeof row[1] !== 'number') continue;
      try { if (new RegExp(row[0], 'i').test(note)) return Math.min(1, Math.max(0, row[1])); } catch { /* bad regex: skip */ }
    }
    return d;
  }
  if (/open|loud|straight|race/i.test(note)) return 0.1;
  if (/quiet|stock|muffled|soft/i.test(note)) return 0.6;
  return d;
}

// ---------------------------------------------------------------- field engine sounds (audio-field.ts)

const layoutOf = (l: string): Layout | undefined => (/^flat|^h\d|boxer/i.test(l) ? 'flat' : /^v/i.test(l) ? 'v' : /^i|inline|straight/i.test(l) ? 'inline' : undefined);

/** One row of index.json's `cars` table (tools/audio/families/make_index.py). */
export interface CarSoundEntry { family?: string; trim?: number; muffler?: number; rpm_scale?: number; redline?: number; engine?: string }
/** public/audio/families/index.json as the race reads it: the family index plus the per-car table. */
export interface FieldSoundIndex extends FamilyIndex {
  cars?: Record<string, CarSoundEntry>;
  muffler?: unknown;
  muffler_default?: unknown;
}

/** A fetched index.json, checked and normalised (null when it is not usable: missing, mid-rebuild, wrong shape). */
export function parseSoundIndex(raw: unknown): FieldSoundIndex | null {
  if (!raw || typeof raw !== 'object') return null;
  const i = raw as Partial<FieldSoundIndex>;
  if (!i.families || typeof i.families !== 'object' || !Object.keys(i.families).length) return null;
  const def = typeof i.default === 'string' && i.families[i.default] ? i.default : Object.keys(i.families)[0];
  return {
    ...(i as FieldSoundIndex),
    default: def,
    aliases: Array.isArray(i.aliases) ? i.aliases.filter((a) => Array.isArray(a) && typeof a[0] === 'string' && typeof a[1] === 'string') : [],
    fallback: Array.isArray(i.fallback) ? i.fallback.filter((f) => f && typeof f === 'object') : [],
    cars: i.cars && typeof i.cars === 'object' ? i.cars : {},
  };
}

const numIn = (v: unknown, lo: number, hi: number, d: number) => (typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi ? v : d);

/** An engine with no combustion sound: battery-electric (field.ts resolveCarType layout 'EV', cylinders 0). The race
 *  gives it no field-audio voice (silence) rather than a borrowed petrol family. */
export function silentEngine(e: { layout: string; cylinders: number }): boolean {
  return e.layout === 'EV' || !(e.cylinders > 0);
}

/**
 * How a car sounds: index.json's `cars[id]` row (the car's field key: pace.json `id`, else its number) (family, trim, muffler, rpm_scale) when present and its family
 * exists, else familyFor() over identity.json's engine family / make / model, then cylinders + layout.
 */
export function carSound(index: FieldSoundIndex | null, car: { number: string; id?: string; identity: unknown; engine: { layout: string; cylinders: number; exhaustNote?: string | null } }): FieldCarSound {
  const row = index?.cars?.[car.id ?? car.number];
  const id = (car.identity ?? {}) as { make?: string; model?: string; engine?: { family?: string; exhaust_note?: string } };
  let family = '';
  if (index && (row?.family || !silentEngine(car.engine))) {
    family = row?.family && index.families[row.family] ? row.family
      : familyFor(index, { engineFamily: id.engine?.family, make: id.make, model: id.model, cylinders: car.engine.cylinders, layout: layoutOf(car.engine.layout) });
  }
  const note = car.engine.exhaustNote ?? id.engine?.exhaust_note ?? null;
  return {
    family,
    trim: numIn(row?.trim, 0.9, 1.1, audioTrim(car.number)),
    muffler: numIn(row?.muffler, 0, 1, mufflerFor(note, index?.muffler, index?.muffler_default)),
    rpmScale: numIn(row?.rpm_scale, 0.25, 4, 1),
  };
}

/**
 * This frame's engine data for one AI car. rpm and redline are both scaled by the car's rpm_scale (e.g. #34's
 * three-cylinder plays an I4 family at 0.75 × rpm), so the voice's limiter still trips at the car's own redline.
 */
export function fillAudioCar(c: FieldAudioCar, st: { pos: [number, number, number]; vel: [number, number, number]; rpm: number; throttleOut: number }, redline: number, snd: FieldCarSound): FieldAudioCar {
  c.pos = st.pos; c.vel = st.vel;
  c.rpm = st.rpm * snd.rpmScale;
  c.redline = redline * snd.rpmScale;
  c.throttle = st.throttleOut;
  c.family = snd.family; c.trim = snd.trim; c.muffler = snd.muffler;
  return c;
}

/** Voice cap for the render tier (quality.ts). */
export function fieldVoicesFor(tier: string): number { return tier === 'phone' ? FIELD_VOICES_PHONE : FIELD_VOICES_DESKTOP; }

/** `?fieldaudio=0` forces the AI engine sounds off; anything else leaves the pause-menu setting in charge. */
export function fieldAudioUrlOff(search: string): boolean { return new URLSearchParams(search).get('fieldaudio') === '0'; }

export const SOUND_INDEX_RETRY_MS = 10_000;

/**
 * FieldAudio on the player's AudioContext. `ctx` / `destination` come from CarAudio (`context`, `fieldBus()`); the
 * family index is fetched from audio/families/index.json. While it is missing or unusable the field is silent and
 * the fetch is retried every SOUND_INDEX_RETRY_MS (from tick()); a family whose files fail is retried by FieldAudio.
 */
export function fieldAudioHook(
  ctx: BaseAudioContext | null, destination: AudioNode | null, maxVoices: number, base = 'audio/families/',
  fetchFn?: (u: string) => Promise<{ ok: boolean; json(): Promise<unknown>; arrayBuffer(): Promise<ArrayBuffer> }>,
): FieldAudioHook | null {
  if (!ctx || !destination) return null;
  let index: FieldSoundIndex | null = null;
  let fa: FieldAudio | null = null;
  let disposed = false, busy = false, warned = false, lastTry = -Infinity;
  const load = (): Promise<void> => {
    busy = true; lastTry = Date.now();
    // index.json is re-read on each race (no-cache): the families may be rebuilt while the page is open
    return (fetchFn ?? ((u: string) => fetch(u, { cache: 'no-cache' })))(base + 'index.json').then((r) => (r.ok ? r.json() : null)).catch(() => null).then((raw) => {
      busy = false;
      if (disposed) return;
      const i = parseSoundIndex(raw);
      if (!i) {
        if (!warned) console.warn(`field audio: ${base}index.json missing or unusable — AI cars are silent (retrying)`);
        warned = true;
        return;
      }
      index = i;
      try { fa = new FieldAudio(ctx, destination, { index: i, base, maxVoices, ...(fetchFn ? { fetchFn } : {}) }); } catch (e) { console.warn('field audio:', e); fa = null; }
    });
  };
  const ready = load();
  return {
    get audio() { return fa; },
    ready,
    sound: (car) => carSound(index, car),
    tick: () => { if (!fa && !busy && !disposed && Date.now() - lastTry > SOUND_INDEX_RETRY_MS) void load(); },
    dispose: () => { disposed = true; fa?.dispose(); fa = null; },
  };
}

// ---------------------------------------------------------------- results helpers (unit-tested)

/** The main-menu Race row: the configured lap count (`?laps=` included). */
export function raceMenuLabel(search: string, field?: string): string {
  const n = parseRaceOverrides(search).laps ?? RACE_LAPS;
  // `field` (TrackInfo.fieldLabel, Mid-Ohio round 7): a track racing a stand-in field says so; absent: the track's own field
  return `Race · ${n} lap${n === 1 ? '' : 's'} vs ${field ?? 'the 2026 field'}`;
}

// ---------------------------------------------------------------- the mode

export interface RaceDeps {
  loadField(): FieldData | Promise<FieldData>;
  loadModel(file: string): Promise<THREE.Object3D | null>;
  random(): number;
  /** DOM available (HUD, menus); false in unit tests. */
  dom: boolean;
}
const defaultDeps: RaceDeps = { loadField: loadFieldData, loadModel: loadFieldModel, random: Math.random, dom: typeof document !== 'undefined' };

export type RaceMode = GameMode & {
  readonly director: RaceDirector | null;
  readonly seed: number;
  readonly laps: number;
  readonly fieldCars: FieldCars | null;
  readonly out: { reason: string; metres: number } | null;
  /** The AI engine sounds (debug: FieldAudio, null while off / loading). */
  readonly fieldAudio: FieldAudioLike | null;
};

export function createRace(ctx: ModeContext, deps: RaceDeps = defaultDeps): RaceMode {
  const { ghosts, timer, hud } = ctx;
  const sv = ctx.race;
  const ov = parseRaceOverrides(sv?.search ?? '');
  const laps = ov.laps ?? RACE_LAPS;
  let seed = ov.seed ?? newSeed(deps.random);
  let d: RaceDirector | null = null;
  let field: FieldData | null = null;
  let fieldErr: string | null = null;
  let fieldCars: FieldCars | null = null;
  let dom: RaceHudDom | null = null;
  let marker: THREE.Object3D | null = null;
  let fieldAudio: FieldAudioHook | null = null;
  let audioCars: FieldAudioCar[] = [];
  let audioSounds: FieldCarSound[] = [];
  let audioPose: number[] = [];           // poses() index of each audioCars entry
  let audioFor: FieldAudioLike | null = null, audioDir: RaceDirector | null = null;
  let audioTriedAt = -Infinity, audioErr = false;
  let cone: ConeLineLike | null = null;
  let disposed = false;
  let modelsStarted = false;
  // per-race UI state
  let out: { reason: string; metres: number } | null = null;
  let outRaced = 0;   // the live counter's value when the player went out (display only)
  let resultsWanted = false;
  let submitState: 'idle' | 'busy' | 'done' = 'idle';
  let prev = { phase: '', lapIdx: 0, count: 0, position: 0 };
  let posCandidate = 0, posSince = 0;
  let thump = 0, lastThumpAt = -1;

  const teamOf = (num: string) => d?.cars.find((c) => c.number === num)?.team ?? '';
  const L = () => d?.line.L ?? ctx.track.length_m;

  // ---- build / rebuild the race
  const build = () => {
    if (!sv || !field || disposed) return;
    ctx.rollingStart();                 // fresh Vehicle + Surface + timer; step counter 0
    sv.sim.record = false;              // races are not replayed
    const t0 = performance.now();
    d = buildDirector(sv.sim, field, { seed, laps });
    const dir = d;
    sv.sim.stepVehicle = (di) => dir.step(STEP, di as DriverInput);
    console.info(`race: seed ${seed}, ${dir.cars.length} cars, ${laps} laps, built in ${(performance.now() - t0).toFixed(0)} ms${dir.calibrationStale ? ' (pace.json calibration is stale)' : ''}`);
    out = null; resultsWanted = false; submitState = 'idle';
    prev = { phase: 'formation', lapIdx: 0, count: 0, position: 0 };
    posCandidate = 0; posSince = 0; thump = 0;
    cone?.clear();
    if (!fieldCars) {
      fieldCars = new FieldCars({ maxDrawn: sv.quality.maxAiCarsDrawn, shadowCasters: sv.quality.shadows ? sv.quality.aiShadowCasters : 0 });
      fieldCars.build(fieldCarInfos(dir));
      sv.scene.add(fieldCars.group);
    }
    fieldCars.setVisible(true);
    placeMarker(dir);
    loadModelsInBackground();
    setBoardContext({ raceAiVersion: raceBoardVersion(R.AI_VERSION) });
    ctx.hud.toast(`Formation lap · seed ${seed} · you start P${dir.player.grid}`, 3000);
  };

  /** Swap placeholders for real models one at a time, in the background (models.json order; see modelQueue). */
  const loadModelsInBackground = () => {
    if (modelsStarted || !field || !fieldCars || !d) return;
    modelsStarted = true;
    const fc = fieldCars;
    const todo = modelQueue(field.models, d.cars, (num) => fc.kindOf(num));
    void (async () => {
      for (const { car: num, model: m } of todo) {
        if (disposed) return;
        const tpl = await deps.loadModel(m.file);
        if (disposed) return;
        if (tpl) fc.useModel(num, tpl, typeof m.tyre_radius_m === 'number' ? m.tyre_radius_m : undefined, Array.isArray(m.brake_lamps) ? m.brake_lamps : undefined, m.brake_lamps_fallback === true);
      }
    })();
  };

  /** A translucent yellow marker on the penalty box (shown while a stop-and-go is pending). */
  const placeMarker = (dir: RaceDirector) => {
    if (!sv || !deps.dom) return;
    const spot = dir.penaltyBoxSpot();
    if (!spot) return;
    if (!marker) {
      const g = new THREE.Group();
      g.name = 'penalty_box';
      const pad = new THREE.Mesh(new THREE.BoxGeometry(6, 0.06, 3.2), new THREE.MeshBasicMaterial({ color: 0xffd400, transparent: true, opacity: 0.45, depthWrite: false }));
      const cv = document.createElement('canvas'); cv.width = 512; cv.height = 96;
      const c2 = cv.getContext('2d')!;
      c2.fillStyle = 'rgba(10,10,10,0.75)'; c2.fillRect(0, 0, 512, 96);
      c2.fillStyle = '#ffd400'; c2.font = '800 54px system-ui, sans-serif'; c2.textAlign = 'center'; c2.textBaseline = 'middle';
      c2.fillText('PENALTY BOX', 256, 50);
      const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
      const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthWrite: false }));
      label.scale.set(5, 0.95, 1); label.position.set(0, 3, 0);
      g.add(pad, label);
      marker = g;
      sv.scene.add(g);
    }
    const z = surfaceFactory(sv.sim.assets)().sample(spot.x, spot.y).z;
    marker.position.set(spot.x, z + 0.04, -spot.y);
    marker.rotation.set(0, spot.heading + Math.PI / 2, 0);
    marker.visible = false;
  };

  /** The AI engine sounds, per frame: follow the pause-menu setting, (re)build the car list, feed FieldAudio. */
  const updateAudio = (dir: RaceDirector, now: number) => {
    if (!sv?.fieldAudio) return;
    if (!(sv.fieldAudioEnabled?.() ?? true)) {
      if (fieldAudio) { fieldAudio.dispose(); fieldAudio = null; audioFor = null; }
      return;
    }
    if (!fieldAudio) {
      if (now - audioTriedAt < 1000) return; // e.g. no AudioContext yet
      audioTriedAt = now;
      fieldAudio = sv.fieldAudio();
      if (!fieldAudio) return;
    }
    fieldAudio.tick?.();
    const fa = fieldAudio.audio;
    if (!fa) return;
    const poses = dir.poses();
    if (fa !== audioFor || dir !== audioDir) {
      audioFor = fa; audioDir = dir;
      audioCars = []; audioSounds = []; audioPose = [];
      poses.forEach((p, i) => {
        if (p.isPlayer) return;
        const snd = fieldAudio!.sound({ number: p.number, id: p.id, identity: p.identity, engine: p.engine });
        if (!snd.family && silentEngine(p.engine)) return;   // an electric car (#16 Bolt at Buttonwillow) with no index row: no voice
        audioSounds.push(snd); audioPose.push(i);
        audioCars.push(fillAudioCar({ id: p.number, pos: p.state.pos, vel: p.state.vel, rpm: 0, throttle: 0, redline: 0, family: '' }, p.state, p.engine.redline, snd));
      });
    }
    for (let k = 0; k < audioCars.length; k++) {
      const p = poses[audioPose[k]];
      fillAudioCar(audioCars[k], p.state, p.engine.redline, audioSounds[k]);
    }
    const st = dir.player.vehicle.state;
    try { fa.update({ pos: st.pos, vel: st.vel, quat: st.quat }, audioCars); } catch (e) {
      if (!audioErr) console.warn('field audio update:', e);
      audioErr = true;
    }
  };

  const start = () => {
    ghosts.group.visible = false;
    ctx.setScheduleLap(ghosts.fastestReal()); // auto-shift follows the fastest real lap's gears
    timer.clearSession();
    hud.hideCorners();
    hud.setRefName('');
    hud.setBanner(null);
    if (deps.dom && !dom) dom = new RaceHudDom(hud.root);
    cone = sv?.coneLine?.() ?? null;
    if (!sv) { ctx.rollingStart(); fieldErr = 'race services missing'; return; }
    if (field) { build(); return; }
    // hold the car on the start until the field data is in
    ctx.rollingStart();
    sv.sim.stepVehicle = () => {};
    dom?.waiting('Loading the field…');
    const got = deps.loadField();
    const use = (f: FieldData) => {
      if (disposed) return;
      if (!f.pace) { fieldErr = 'pace.json is missing — no field'; dom?.waiting('No race data (pace.json missing)'); sv.sim.stepVehicle = null; ctx.toast(fieldErr); return; }
      field = f;
      if (f.missing.length) console.warn('race field data missing:', f.missing.join(', '));
      build();
    };
    if (got instanceof Promise) got.then(use, (e) => { fieldErr = String(e); dom?.waiting('Could not load the field'); sv.sim.stepVehicle = null; });
    else use(got);
  };

  // ---- results
  /** Live running order (the player at its launch distance when out). */
  const standingsRows = (): TableRow[] => {
    if (!d) return [];
    const LL = L(), ej = d.hud().penalties.ejected, flagged = !!d.getResults();
    const eff = (c: RaceDirector['cars'][number]) => (c.isPlayer && out ? out.metres : c.U);
    return [...d.cars].sort((a, b) => eff(b) - eff(a) || a.grid - b.grid).map((c, k) => ({
      position: k + 1, number: c.number, team: c.team, class: c.cls,
      metres: Math.max(0, eff(c)), laps: Math.max(0, Math.floor(eff(c) / LL)),
      status: rowStatus({ player: c.isPlayer, out: !!out, ejected: ej, flagged }), player: c.isPlayer,
    }));
  };
  /** The classification at the flag; when the player is out before it, the order at the moment it is shown. */
  const finalRows = (): TableRow[] => {
    const r = d?.getResults();
    return r ? resultRows(r, out) : standingsRows();
  };
  const submit = () => {
    if (!d || submitState !== 'idle') return;
    const res = raceResultFor(finalRows(), { seed, aiVersion: raceBoardVersion(R.AI_VERSION), finished: d.player.finished });
    if (!res) return;
    submitState = 'busy';
    sv?.menu.refresh();
    void submitRace(res).then((o: SubmitOutcome) => {
      submitState = o.status === 'submitted' ? 'done' : 'idle';
      if (o.status === 'not-best') hud.toast('Scoreboard: not better than this device\'s best race', 4000);
      else if (o.status === 'unavailable') hud.toast('Scoreboard unavailable (stand-in assets loaded)', 4000);
      sv?.menu.refresh();
    });
  };
  const resultsPage = (): MenuPage => {
    const rows = finalRows();
    const me = rows.find((r) => r.player);
    const shortRace = laps !== RACE_LAPS && !ov.devSubmit;
    return {
      title: 'RESULTS',
      subtitle: `${laps} lap${laps === 1 ? '' : 's'} · seed ${seed}${me ? ` · P${me.position} of ${rows.length} · ${me.time != null ? `${me.laps} laps in ${fmtLapTime(me.time)}` : fmtMetres(me.metres, Math.max(0, me.laps), L())}` : ''}`,
      body: () => raceTable(rows, L(), d?.getResults() ? `CHEQUERED FLAG · ${TRACK.short.toUpperCase()} · 2026 LEMONS FIELD` : 'OUT OF THE RACE · ORDER WHEN YOU LEFT'),
      entries: (): MenuEntry[] => [
        {
          kind: 'action', id: 'raceSubmit', label: 'Submit to scoreboard',
          note: submitState === 'done' ? 'submitted' : submitState === 'busy' ? 'submitting…' : shortRace ? `${RACE_LAPS}-lap races only` : undefined,
          disabled: submitState !== 'idle' || shortRace || !me || !(me.metres > 0), run: submit,
        },
        { kind: 'action', id: 'raceAgain', label: 'Race again (new seed)', run: () => { mode.restart(); sv?.menu.close(); } },
        { kind: 'action', id: 'raceMain', label: 'Main menu', run: () => { resultsWanted = false; sv?.mainMenu(); } },
      ],
    };
  };
  const showResults = () => {
    if (!sv || !deps.dom) return;
    resultsWanted = true;
    sv.menu.show(resultsPage(), { closable: false, variant: 'pause' });
  };

  const standingsPage = (): MenuPage => ({
    title: 'Standings',
    subtitle: d ? `Lap ${d.hud().lap}/${laps} · seed ${seed}` : 'no race',
    body: () => (d ? (d.getResults() ? raceTable(finalRows(), L(), 'CLASSIFICATION AT THE FLAG') : raceTable(standingsRows(), L(), 'RUNNING ORDER')) : null),
    entries: () => [{ kind: 'back', id: 'back', label: 'Back' }],
  });

  // ---- per frame
  const toasts = (h: RaceHud, dir: RaceDirector) => {
    const P = dir.player;
    if (prev.phase === 'formation' && h.phase === 'green') hud.toast('GREEN FLAG — race!', 2500);
    if (prev.phase !== 'chequered' && h.phase === 'chequered') hud.toast(`Chequered flag · P${h.position}`, 3000);
    const li = Math.floor(Math.max(0, P.U) / dir.line.L);
    if (li > prev.lapIdx && h.phase !== 'formation') {
      hud.toast(`Lap ${li}/${laps} done${Number.isFinite(P.lastLap) ? ` · ${fmtTime(P.lastLap)}` : ''} · P${h.position}`, 2500);
    }
    if (h.penalties.count > prev.count) hud.toast(`Black flag: ${h.penalties.lastReason ?? ''}`, 3000);
    // position changes: toast once the new position held for 1 s (no flapping while side by side)
    if (h.phase === 'green' && prev.position > 0 && h.position !== prev.position) {
      if (h.position !== posCandidate) { posCandidate = h.position; posSince = dir.time; }
      else if (dir.time - posSince > 1) {
        const n = prev.position - h.position;
        hud.toast(n > 0 ? `▲ P${h.position} (+${n})` : `▼ P${h.position} (${n})`, 1800);
        prev.position = h.position;
      }
    } else { posCandidate = h.position; if (prev.position === 0 || h.phase !== 'green') prev.position = h.position; }
    prev.phase = h.phase; prev.lapIdx = Math.max(prev.lapIdx, li); prev.count = h.penalties.count;
  };

  const mode: RaceMode = {
    id: 'race',
    label: 'Race',
    get director() { return d; },
    get seed() { return seed; },
    get laps() { return laps; },
    get fieldCars() { return fieldCars; },
    get out() { return out; },
    get fieldAudio() { return fieldAudio?.audio ?? null; },
    start,
    restart() {
      seed = newSeed(deps.random);
      if (sv?.menu.isOpen && resultsWanted) sv.menu.close();
      resultsWanted = false;
      if (field) build(); else start();
    },
    reset() {
      // out of the race (space launch): the race is over for the player → the results card
      if (out) { hud.hideGameOver?.(); showResults(); return; }
      // in a race the car is recovered where it is rather than sent back to the start
      ctx.recoverAt(ctx.s());
      cone?.clear(); // a teleport is not a crossing
      ctx.toast('Recovered to the track');
    },
    step() {
      if (!d) return;
      // other cars' contacts near the player: a distant thump
      const P = d.player, pp = P.vehicle.state.pos;
      for (let k = 0; k < d.contactCount; k++) {
        const ev = d.contacts[k];
        if (ev.a === P.idx || ev.b === P.idx || ev.closing < 2) continue;
        const dist = Math.hypot(ev.x - pp[0], ev.y - pp[1]);
        if (dist < 40) thump = Math.max(thump, ev.closing * (1 - dist / 40) * 0.6);
      }
    },
    onLap() { /* laps come from the director (race distance), not the hot-lap timer */ },
    frame(dt, now) {
      const dir = d;
      if (!dir) return;
      const h = dir.hud();
      const P = dir.player, st = P.vehicle.state;
      if (st.launched && !out) {
        out = { reason: sv?.sim.launchedOffTrack ? 'Lost in the hills' : 'Launched into space', metres: Math.max(0, P.U) };
        outRaced = h.raced;
      }
      if (cone && !out && cone.update(st.pos[0], st.pos[1])) dir.reportViolation('pit_exit_cones');
      toasts(h, dir);
      if (dom) dom.update(raceHudView(h, { teamOf, metres: out ? outRaced : h.raced, out: out?.reason ?? null }));
      if (marker) marker.visible = h.penalties.pending.length > 0;
      if (fieldCars) {
        const poses = dir.poses();
        fieldCars.update(poses.map((p) => p.state), dir.traffic.s, P.idx, dir.line.L, poses.map((p) => p.brake));
        if (ctx.marks) {
          const pp = st.pos;
          poses.forEach((p, i) => { if (i !== P.idx && Math.hypot(p.state.pos[0] - pp[0], p.state.pos[1] - pp[1]) < 160) ctx.marks!.car(i + 1, p.state, dt); });
        }
      }
      if (thump > 0 && sv && now - lastThumpAt > 150) { sv.impact(thump); lastThumpAt = now; thump = 0; }
      updateAudio(dir, now);
      // the results card: at the end, and again whenever something (the scoreboard prompt, the pause menu) closed it
      if ((h.phase === 'finished' || (out && resultsWanted)) && sv && deps.dom && !sv.menu.isOpen) showResults();
    },
    hud(): ModeHud { return { banner: fieldErr && !d ? `Race · ${fieldErr}` : null, timing: false, delta: null, showDelta: false }; },
    timeScale() { return d?.timeScale ?? 1; },
    pauseEntries(): MenuEntry[] {
      return [
        { kind: 'submenu', id: 'standings', label: 'Standings', disabled: !d, page: standingsPage },
        { kind: 'action', id: 'seed', label: `Seed ${seed}`, note: `${laps} laps · ?seed=${seed} replays this grid`, disabled: true, run: () => {} },
        ...(d?.getResults() ? [{ kind: 'action', id: 'results', label: 'Results', run: showResults } as MenuEntry] : []),
      ];
    },
    dispose() {
      disposed = true;
      if (sv) { sv.sim.stepVehicle = null; sv.sim.record = true; }
      fieldCars?.dispose(); fieldCars = null;
      if (marker) { marker.removeFromParent(); marker = null; }
      fieldAudio?.dispose(); fieldAudio = null; audioFor = null;
      dom?.dispose(); dom = null;
      hud.setBanner(null);
      d = null;
    },
  };
  return mode;
}
