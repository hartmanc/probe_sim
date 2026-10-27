// Render tier: 'phone' (touch-first device, or ?phone=1), 'desktop' or 'balanced' (desktop field and device class, lighter
// rendering: 30 AI cars drawn, 4 AI shadow casters, 2.5 MP, anisotropy 8; perf round 1, 27 Oct 2026; chosen in the Graphics menu). The phone tier caps the canvas at about
// 1.2 MP with pixel ratio ≤ 1, turns shadow maps off, lowers texture anisotropy and thins the scenery after
// buildWorld (scene.ts / scenery.ts are not changed): tree instances away from the track are dropped.
// `quality.maxAiCarsDrawn` is the cap the race integration must respect when it adds AI car rigs.
//
// The user can force the tier in the menu (stored in localStorage, applied on reload); ?phone=1 / ?phone=0
// override both.
import type * as THREE from 'three';
import type { TrackJson } from './physics-types';

export type Tier = 'phone' | 'desktop' | 'balanced';
/** What the device is (memory class), independent of the render tier the player picks: phones and tablets (iPad Safari
 *  has the same memory limits as the iPhone) race a 40-car field (field-select.ts). */
export type DeviceClass = 'phone' | 'tablet' | 'desktop';
export type TierChoice = 'auto' | Tier;

export interface QualitySettings {
  tier: Tier;
  /** phone / tablet / desktop (deviceClass); the race field size follows it, the render tier does not */
  device: DeviceClass;
  /** How the tier was chosen. */
  reason: 'url' | 'forced' | 'auto';
  /** Touch controls are shown (touch-first device or ?phone=1); independent of a forced render tier. */
  touch: boolean;
  /** AI cars drawn at most (the rest are simulated but not rendered). */
  maxAiCarsDrawn: number;
  /** Canvas pixel budget (pixels) and pixel-ratio cap. */
  maxPixels: number;
  maxPixelRatio: number;
  shadows: boolean;
  maxAnisotropy: number;
  /** nearest AI cars that cast shadow-map shadows (the rest keep a contact-shadow blob); 0 on the phone tier */
  aiShadowCasters: number;
  /** half-size of the sun's orthographic shadow box around the player, m */
  shadowBoxM: number;
  shadowMapSize: number;
}

export const TIER_KEY = 'probeSim.quality.tier.v1';
/** AI shadows (desktop): the nearest AI_SHADOW_CASTERS cars cast real shadows inside a ±SHADOW_BOX_M box at SHADOW_MAP px,
 *  which keeps the player's shadow at the same texel density as the old ±7 m / 1024 px box (~70 px/m). `?aishadows=0`
 *  restores the small box and blobs for every AI car (owner, 17 Oct 2026: "open to not doing it if it hurts performance"). */
export const AI_SHADOW_CASTERS = 8;
export const SHADOW_BOX_M = 30;
export const SHADOW_MAP = 2048;
const PLAYER_BOX_M = 7, PLAYER_MAP = 1024;
/** Pure: dev `?shadowbox=<5..60>` (half-size of the sun's shadow box, m); null = the tier's own. */
export function shadowBoxFromUrl(search: string): number | undefined {
  const v = Number(new URLSearchParams(search).get('shadowbox'));
  return Number.isFinite(v) && v >= 5 && v <= 60 ? v : undefined;
}
/** Pure: `?aishadows=0` turns AI shadow casting off. */
export function aiShadowsUrlOff(search: string): boolean {
  const v = new URLSearchParams(search).get('aishadows');
  return v === '0' || v === 'false';
}
export const PHONE_MAX_PIXELS = 1.2e6;
/** Desktop pixel budget (perf round 1, 27 Oct 2026): a 4K display at ratio 1.5 would render 4.7 MP; this keeps it at 3.5. */
export const DESKTOP_MAX_PIXELS = 3.5e6;
/** The Balanced tier (menu choice): 30 AI cars, 4 shadow casters, 2.5 MP, anisotropy 8, shadows at 2048 px, no scenery thinning. */
export const BALANCED = { maxAiCarsDrawn: 30, maxPixels: 2.5e6, aiShadowCasters: 4, maxAnisotropy: 8 } as const;
const TREE_NEAR_M = 60;     // every tree within this of the centreline is kept on the phone tier
const TREE_MID_M = 400;     // beyond: keep 1 in 2; beyond TREE_MID_M: 1 in 4

export interface TierEnv { coarse: boolean; maxTouchPoints: number; search: string; stored: string | null }

/** Pure: pick the tier and whether touch controls are on. */
export function pickTier(env: TierEnv): { tier: Tier; reason: QualitySettings['reason']; touch: boolean } {
  const p = new URLSearchParams(env.search).get('phone');
  const touchDevice = env.coarse && env.maxTouchPoints > 0;
  if (p === '1' || p === 'true') return { tier: 'phone', reason: 'url', touch: true };
  if (p === '0' || p === 'false') return { tier: 'desktop', reason: 'url', touch: false };
  const touch = touchDevice;
  if (env.stored === 'phone' || env.stored === 'desktop' || env.stored === 'balanced') return { tier: env.stored, reason: 'forced', touch };
  return { tier: touchDevice ? 'phone' : 'desktop', reason: 'auto', touch };
}

export interface DeviceEnv { coarse: boolean; maxTouchPoints: number; search: string; platform: string; screenMin: number }

/** iPadOS Safari presents itself as a Mac ("MacIntel") with touch points. */
export const isIpad = (env: Pick<DeviceEnv, 'platform' | 'maxTouchPoints'>): boolean => env.platform === 'MacIntel' && env.maxTouchPoints > 1;

/** Pure: the device class. ?phone=1 / ?phone=0 force phone / desktop; an iPad, or a touch-first device whose short screen
 *  side is at least 600 CSS px, is a tablet; another touch-first device is a phone; the rest are desktops. */
export function deviceClass(env: DeviceEnv): DeviceClass {
  const p = new URLSearchParams(env.search).get('phone');
  if (p === '1' || p === 'true') return 'phone';
  if (p === '0' || p === 'false') return 'desktop';
  if (isIpad(env)) return 'tablet';
  if (env.coarse && env.maxTouchPoints > 0) return env.screenMin >= 600 ? 'tablet' : 'phone';
  return 'desktop';
}

export function settingsFor(tier: Tier, reason: QualitySettings['reason'], touch: boolean, opts: { aiShadows?: boolean; device?: DeviceClass; shadowBoxM?: number } = {}): QualitySettings {
  const device = opts.device ?? (tier === 'phone' ? 'phone' : 'desktop');
  if (tier === 'phone') {
    return { tier, device, reason, touch, maxAiCarsDrawn: 20, maxPixels: PHONE_MAX_PIXELS, maxPixelRatio: 1, shadows: false, maxAnisotropy: 2,
      aiShadowCasters: 0, shadowBoxM: PLAYER_BOX_M, shadowMapSize: PLAYER_MAP };
  }
  const ai = opts.aiShadows ?? true;
  if (tier === 'balanced') {
    return { tier, device, reason, touch, maxAiCarsDrawn: BALANCED.maxAiCarsDrawn, maxPixels: BALANCED.maxPixels, maxPixelRatio: 1.5, shadows: true, maxAnisotropy: BALANCED.maxAnisotropy,
      aiShadowCasters: ai ? BALANCED.aiShadowCasters : 0, shadowBoxM: ai ? (opts.shadowBoxM ?? SHADOW_BOX_M) : PLAYER_BOX_M, shadowMapSize: ai ? SHADOW_MAP : PLAYER_MAP };
  }
  return { tier, device, reason, touch, maxAiCarsDrawn: 45, maxPixels: DESKTOP_MAX_PIXELS, maxPixelRatio: 1.5, shadows: true, maxAnisotropy: 16,
    aiShadowCasters: ai ? AI_SHADOW_CASTERS : 0, shadowBoxM: ai ? (opts.shadowBoxM ?? SHADOW_BOX_M) : PLAYER_BOX_M, shadowMapSize: ai ? SHADOW_MAP : PLAYER_MAP };
}

/** Pure: device pixel ratio to render at for a CSS-pixel viewport. */
export function pixelRatioFor(q: Pick<QualitySettings, 'maxPixels' | 'maxPixelRatio'>, dpr: number, w: number, h: number): number {
  let r = Math.min(dpr || 1, q.maxPixelRatio);
  if (isFinite(q.maxPixels) && w > 0 && h > 0) r = Math.min(r, Math.sqrt(q.maxPixels / (w * h)));
  return Math.max(0.5, r);
}

function readStored(): string | null {
  try { return localStorage.getItem(TIER_KEY); } catch { return null; }
}

/** Save a forced tier ('auto' clears it). Takes effect on the next load. */
export function storeTierChoice(c: TierChoice): void {
  try { if (c === 'auto') localStorage.removeItem(TIER_KEY); else localStorage.setItem(TIER_KEY, c); } catch { /* no storage */ }
}
export function storedTierChoice(): TierChoice {
  const s = readStored();
  return s === 'phone' || s === 'desktop' || s === 'balanced' ? s : 'auto';
}

function detect(): QualitySettings {
  if (typeof window === 'undefined') return settingsFor('desktop', 'auto', false);
  const maxTouchPoints = navigator.maxTouchPoints ?? 0, platform = navigator.platform ?? '';
  // an iPad with a trackpad reports a fine pointer; it is still a touch device with phone-class memory
  const coarse = !!window.matchMedia?.('(pointer: coarse)').matches || isIpad({ platform, maxTouchPoints });
  const r = pickTier({ coarse, maxTouchPoints, search: location.search, stored: readStored() });
  const device = deviceClass({ coarse, maxTouchPoints, search: location.search, platform, screenMin: Math.min(screen.width || 0, screen.height || 0) });
  return settingsFor(r.tier, r.reason, r.touch, { aiShadows: !aiShadowsUrlOff(location.search), device, shadowBoxM: shadowBoxFromUrl(location.search) });
}

/** The settings for this page load. */
export const quality: QualitySettings = detect();

// ---------------------------------------------------------------- scenery thinning (after buildWorld)

/** Pure: stable per-position hash in [0, 1) (crowns and trunks of one tree share x, z, so they agree). */
export function posHash(x: number, z: number): number {
  const xi = Math.round(x * 4) | 0, zi = Math.round(z * 4) | 0;
  let h = Math.imul(xi, 73856093) ^ Math.imul(zi, 19349663);
  h = Math.imul(h ^ (h >>> 13), 0x5bd1e995);
  h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}

/** Pure: keep this tree? `d` = distance to the track centreline (m). */
export function keepTree(d: number, hash: number): boolean {
  if (d <= TREE_NEAR_M) return true;
  if (d <= TREE_MID_M) return hash < 0.5;
  return hash < 0.25;
}

/** Distance (m) from a point (ENU x, y) to the nearest centreline station, via a 50 m grid. */
export function trackDistance(track: Pick<TrackJson, 'center'>, cell = 50): (x: number, y: number) => number {
  const grid = new Map<string, [number, number][]>();
  for (const p of track.center) {
    const k = `${Math.floor(p[0] / cell)},${Math.floor(p[1] / cell)}`;
    let b = grid.get(k);
    if (!b) grid.set(k, (b = []));
    b.push([p[0], p[1]]);
  }
  return (x, y) => {
    const cx = Math.floor(x / cell), cy = Math.floor(y / cell);
    let best = Infinity;
    for (let r = 0; r <= 12; r++) {
      for (let i = cx - r; i <= cx + r; i++) for (let j = cy - r; j <= cy + r; j++) {
        if (r > 0 && i !== cx - r && i !== cx + r && j !== cy - r && j !== cy + r) continue; // ring only
        const b = grid.get(`${i},${j}`);
        if (b) for (const [px, py] of b) { const d = Math.hypot(px - x, py - y); if (d < best) best = d; }
      }
      if (best <= r * cell) return best; // nothing in a farther ring can be closer
    }
    return best;
  };
}

/**
 * Compact an InstancedMesh in place to the instances where keep(x, y, z) holds (three.js coordinates).
 * Returns [before, after].
 */
export function thinInstances(mesh: THREE.InstancedMesh, keep: (x: number, y: number, z: number) => boolean): [number, number] {
  const n = mesh.count, m = mesh.instanceMatrix.array as Float32Array;
  const c = mesh.instanceColor ? (mesh.instanceColor.array as Float32Array) : null;
  let k = 0;
  for (let i = 0; i < n; i++) {
    const o = i * 16;
    if (!keep(m[o + 12], m[o + 13], m[o + 14])) continue;
    if (k !== i) {
      for (let j = 0; j < 16; j++) m[k * 16 + j] = m[o + j];
      if (c) for (let j = 0; j < 3; j++) c[k * 3 + j] = c[i * 3 + j];
    }
    k++;
  }
  mesh.count = k;
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  if (k === 0) mesh.visible = false;
  else mesh.computeBoundingSphere();
  return [n, k];
}

export interface ThinReport { treesBefore: number; treesAfter: number; meshes: number }

/**
 * Phone tier: thin the tree instances of `scene` (the 'trees' group from scenery.ts) by distance to the track.
 * Three.js coordinates: X = east, Z = -north.
 */
export function thinScenery(scene: THREE.Object3D, track: Pick<TrackJson, 'center'>): ThinReport {
  const dist = trackDistance(track);
  const rep: ThinReport = { treesBefore: 0, treesAfter: 0, meshes: 0 };
  const trees = scene.getObjectByName('trees');
  if (!trees) return rep;
  const cache = new Map<string, boolean>();
  const keep = (x: number, _y: number, z: number) => {
    const key = `${Math.round(x * 4)},${Math.round(z * 4)}`;
    let v = cache.get(key);
    if (v === undefined) { v = keepTree(dist(x, -z), posHash(x, z)); cache.set(key, v); }
    return v;
  };
  trees.traverse((o) => {
    const im = o as THREE.InstancedMesh;
    if (!im.isInstancedMesh) return;
    const [a, b] = thinInstances(im, keep);
    rep.meshes++;
    // trunks and crowns are separate meshes of one tree; count crowns + trunks alike
    rep.treesBefore += a; rep.treesAfter += b;
  });
  return rep;
}

/** Apply the tier to the renderer and the built world. Call once after buildWorld. */
export function applyQuality(q: QualitySettings, renderer: THREE.WebGLRenderer, world: { scene: THREE.Scene; sun: THREE.DirectionalLight },
  track: Pick<TrackJson, 'center'>): ThinReport | null {
  renderer.shadowMap.enabled = q.shadows;
  world.sun.castShadow = q.shadows;
  // the sun's shadow box: ±shadowBoxM around the player at shadowMapSize px (buildWorld starts with the small player-only box)
  const sh = world.sun.shadow, sc = sh.camera, b = q.shadowBoxM;
  sc.left = -b; sc.right = b; sc.top = b; sc.bottom = -b; sc.updateProjectionMatrix();
  if (sh.mapSize.x !== q.shadowMapSize) { sh.mapSize.set(q.shadowMapSize, q.shadowMapSize); sh.map?.dispose(); sh.map = null; }
  if (q.tier !== 'phone') return null;
  return thinScenery(world.scene, track);
}
