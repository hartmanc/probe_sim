// Asset loading with fallbacks. Every asset is fetched by a relative URL so
// the site works under any base path. A missing asset (404, or Vite's HTML
// fallback page) is replaced by a synthetic stand-in and reported.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { GhostsJson, TrackJson } from './physics-types';
import { makeDevTrack, makeFlatHeightfield, makeOrthoCanvas } from './devtrack';
import { buildFallbackCar } from './car';
import { synthesizeGhosts } from './ghosts';
import type { SceneryAssets, SceneryJson } from './scenery';
import { TRACK } from './track-choice';

export interface Assets {
  track: TrackJson;
  heightfield: Float32Array;
  ortho: THREE.Texture;
  ghosts: GhostsJson;
  carSpecJson: unknown;
  carModel: THREE.Object3D;
  /** scenery.json + far terrain; null when missing (the world then shows only terrain, track and signs). */
  scenery: SceneryAssets | null;
  fallbacks: string[];   // human-readable list of what was synthesized
}

/** The page's track package (?track=, src/app/track-choice.ts). */
const TRACK_DIR = TRACK.dir;
const CAR_DIR = 'cars/probe_gt/';

async function fetchOk(url: string): Promise<Response | null> {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    const ct = r.headers.get('content-type') ?? '';
    if (ct.includes('text/html')) return null; // dev-server SPA fallback
    return r;
  } catch {
    return null;
  }
}

async function fetchJson<T>(url: string): Promise<T | null> {
  const r = await fetchOk(url);
  if (!r) return null;
  try { return (await r.json()) as T; } catch { return null; }
}

export async function loadAssets(onProgress: (frac: number, label: string) => void): Promise<Assets> {
  const fallbacks: string[] = [];
  const forceDev = new URLSearchParams(location.search).get('devtrack') === '1';
  const weights = { track: 0.12, hf: 0.12, ortho: 0.2, ghosts: 0.04, spec: 0.02, glb: 0.35, scenery: 0.15 };
  let done = 0;
  const glbFrac = { v: 0 };
  const tick = (w: number, label: string) => { done += w; onProgress(Math.min(1, done + glbFrac.v * weights.glb), label); };

  // ---- track + heightfield
  let track = forceDev ? null : await fetchJson<TrackJson>(TRACK_DIR + 'track.json');
  let heightfield: Float32Array | null = null;
  let isDev = false;
  if (!track) {
    const dev = makeDevTrack();
    track = dev.track; heightfield = dev.heightfield; isDev = true;
    fallbacks.push('track (synthetic oval)');
  }
  tick(weights.track, 'track');
  if (!heightfield) {
    const r = await fetchOk(TRACK_DIR + (track.heightfield?.file ?? 'heightfield.bin'));
    const hf = track.heightfield;
    if (r) {
      const buf = await r.arrayBuffer();
      if (buf.byteLength >= hf.nx * hf.ny * 4) heightfield = new Float32Array(buf, 0, hf.nx * hf.ny);
    }
    if (!heightfield) { heightfield = makeFlatHeightfield(track); fallbacks.push('heightfield (flat)'); }
  }
  tick(weights.hf, 'heightfield');
  const t = track;

  // ---- the rest in parallel
  const orthoP = (async () => {
    let tex: THREE.Texture | null = null;
    if (!isDev) {
      try { tex = await new THREE.TextureLoader().loadAsync(TRACK_DIR + (t.ortho?.file ?? 'ortho.jpg')); } catch { tex = null; }
    }
    if (!tex) {
      tex = new THREE.CanvasTexture(makeOrthoCanvas(t));
      if (!isDev) fallbacks.push('ortho (procedural)');
    }
    tex.colorSpace = THREE.SRGBColorSpace;
    tick(weights.ortho, 'aerial imagery');
    return tex;
  })();
  const ghostsP = (async () => {
    let g = isDev ? null : await fetchJson<GhostsJson>(TRACK_DIR + 'ghosts.json');
    // a track built without logger laps has a racing line and no ghost laps: keep it (no ghosts to show, the line is real)
    const lineOnly = !!g && Array.isArray(g.laps) && g.laps.length === 0 && (g.line?.offset_m?.length ?? 0) > 0;
    if (!g || (!lineOnly && (!Array.isArray(g.laps) || g.laps.length === 0))) {
      g = synthesizeGhosts(t);
      if (!isDev) fallbacks.push('ghosts (synthetic)');
    }
    tick(weights.ghosts, 'ghosts');
    return g;
  })();
  const specP = (async () => {
    const j = await fetchJson<unknown>(CAR_DIR + 'car.json');
    if (j == null) fallbacks.push('car.json (stub defaults)');
    tick(weights.spec, 'car spec');
    return j ?? {};
  })();
  const glbP = (async () => {
    let model: THREE.Object3D | null = null;
    const head = await fetchOk(CAR_DIR + 'probe.glb');
    if (head) {
      try {
        const buf = await head.arrayBuffer();
        glbFrac.v = 0.7; onProgress(done + glbFrac.v * weights.glb, 'car model');
        const gltf = await new GLTFLoader().parseAsync(buf, CAR_DIR);
        model = gltf.scene;
      } catch (e) {
        console.warn('probe.glb failed to parse', e);
      }
    }
    if (!model) { model = buildFallbackCar(); fallbacks.push('car model (box on wheels)'); }
    glbFrac.v = 0;
    tick(weights.glb, 'car model');
    return model;
  })();

  const sceneryP = (async (): Promise<SceneryAssets | null> => {
    if (isDev) { tick(weights.scenery, 'scenery'); return null; }
    const json = await fetchJson<SceneryJson>(TRACK_DIR + 'scenery.json');
    if (!json) { fallbacks.push('scenery (none)'); tick(weights.scenery, 'scenery'); return null; }
    let farHeightfield: Float32Array | null = null;
    let farOrtho: THREE.Texture | null = null;
    const far = json.far;
    await Promise.all([
      (async () => {
        if (!far?.heightfield) return;
        const r = await fetchOk(TRACK_DIR + far.heightfield.file);
        if (!r) return;
        const buf = await r.arrayBuffer();
        const n = far.heightfield.nx * far.heightfield.ny;
        if (buf.byteLength >= n * 4) farHeightfield = new Float32Array(buf, 0, n);
      })(),
      (async () => {
        if (!far?.ortho) return;
        try {
          farOrtho = await new THREE.TextureLoader().loadAsync(TRACK_DIR + far.ortho.file);
          farOrtho.colorSpace = THREE.SRGBColorSpace;
        } catch { farOrtho = null; }
      })(),
    ]);
    if (far?.heightfield && !farHeightfield) fallbacks.push('far terrain (none)');
    tick(weights.scenery, 'scenery');
    return { json, farHeightfield, farOrtho };
  })();

  const [ortho, ghosts, carSpecJson, carModel, scenery] = await Promise.all([orthoP, ghostsP, specP, glbP, sceneryP]);
  return { track: t, heightfield, ortho, ghosts, carSpecJson, carModel, scenery, fallbacks };
}

// ---------------------------------------------------------------- race field (lazy: fetched when a race starts)

const FIELD_DIR = 'cars/field/';

/** One row of public/cars/field/models.json. */
export interface FieldModelInfo {
  number: string;
  file: string;
  tris?: number;
  tyre_radius_m?: number;
  tyre_radius_rear_m?: number;
  /** rear lamp lens centres [x, y, z, r] in the model's frame (+z forward): lit discs under braking */
  brake_lamps?: number[][];
  /** the lamp positions were synthesised (the model has no lamps): keep the discs visible as dim tail lights */
  brake_lamps_fallback?: boolean;
  /** id of the same physical car's model at an earlier event (one body, livery per event; each keeps its own glb) */
  same_car?: string;
  [k: string]: unknown;
}

/** The race field's data files. `pace` is required for a race; identity / models are optional. */
export interface FieldData {
  pace: unknown | null;
  identity: unknown | null;
  models: FieldModelInfo[];
  /** Human-readable notes on what is missing. */
  missing: string[];
}

let fieldDataP: Promise<FieldData> | null = null;

/** The track's pace.json + identity.json + models.json (fetched once, cached). */
export function loadFieldData(): Promise<FieldData> {
  if (!fieldDataP) {
    fieldDataP = (async () => {
      const [pace, identity, models] = await Promise.all([
        fetchJson<unknown>(TRACK.pace),   // per track (src/scoreboard/config.ts TRACKS)
        fetchJson<unknown>(FIELD_DIR + 'identity.json'),
        fetchJson<{ cars?: FieldModelInfo[] }>(FIELD_DIR + 'models.json'),
      ]);
      const missing: string[] = [];
      if (!pace) missing.push('pace.json');
      if (!identity) missing.push('identity.json (cars are Probe clones)');
      if (!models) missing.push('models.json (placeholder cars)');
      const list = Array.isArray(models?.cars) ? models!.cars.filter((m) => m && m.number != null && typeof m.file === 'string').map((m) => ({ ...m, number: String(m.number) })) : [];
      return { pace, identity, models: list, missing };
    })();
    fieldDataP.catch(() => { fieldDataP = null; });
  }
  return fieldDataP;
}

const fieldModels = new Map<string, Promise<THREE.Object3D | null>>();

/**
 * A field car's glb (models.json `file`, relative to cars/field/), parsed once; resolves null when it is
 * missing or fails to parse (the caller keeps its placeholder). Callers clone the returned scene.
 */
export function loadFieldModel(file: string): Promise<THREE.Object3D | null> {
  let p = fieldModels.get(file);
  if (!p) {
    p = (async () => {
      const r = await fetchOk(FIELD_DIR + file);
      if (!r) return null;
      try {
        const buf = await r.arrayBuffer();
        const gltf = await new GLTFLoader().parseAsync(buf, FIELD_DIR + file.slice(0, file.lastIndexOf('/') + 1));
        return gltf.scene;
      } catch (e) {
        console.warn(`field model ${file} failed to parse`, e);
        return null;
      }
    })();
    fieldModels.set(file, p);
  }
  return p;
}
