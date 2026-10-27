// The AI field on screen: one CarRig per AI car. A car's own glb (public/cars/field/models/<num>.glb, listed in
// models.json) is loaded lazily in the background once the race has started; until it arrives, and for cars
// without one, a cheap placeholder (≈300 triangles built in code, the car's primary colour from identity.json,
// its number on large contrasting boards with a team-colour band on the doors, roof and tail) stands in. Every car is simulated; only the
// `maxDrawn` nearest by track distance are drawn (phone: quality.maxAiCarsDrawn = 20), and only the
// `shadowCasters` nearest cast shadow-map shadows and hide their blob (desktop 8 inside the ±30 m sun box, phone 0). three.js frustum culling stays on.
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { CarRig } from './car';
import { upgradeCarMaterials } from './car-materials';
import type { VehicleState } from './physics-types';

// ---------------------------------------------------------------- pure helpers (unit-tested)

/** identity.json colour: `colors.primary`, `colors[0]`, or `color`; null when none is a #rrggbb string. */
export function identityColor(id: unknown): string | null {
  if (!id || typeof id !== 'object') return null;
  const o = id as { colors?: unknown; color?: unknown };
  const c = o.colors;
  const pick = Array.isArray(c) ? c[0] : c && typeof c === 'object' ? (c as { primary?: unknown }).primary : undefined;
  for (const v of [pick, o.color]) if (typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v.trim())) return v.trim();
  return null;
}

/**
 * Indices of the cars to draw: the `cap` nearest to the player by track distance (wrapped around the lap),
 * nearest first. `s[i]` is each car's lap distance (m); `skip` (the player) is never returned.
 */
export function selectDrawn(s: ArrayLike<number>, playerS: number, L: number, cap: number, skip = -1): number[] {
  const idx: number[] = [];
  const d: number[] = [];
  for (let i = 0; i < s.length; i++) {
    if (i === skip) continue;
    let x = Math.abs(s[i] - playerS) % L;
    if (x > L / 2) x = L - x;
    idx.push(i); d[i] = x;
  }
  idx.sort((a, b) => d[a] - d[b] || a - b);
  return cap >= idx.length ? idx : idx.slice(0, Math.max(0, cap));
}

/** Text colour that reads on a board of this colour. */
export function contrastInk(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  const l = 0.2126 * ((n >> 16) & 255) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255);
  return l > 140 ? '#111111' : '#ffffff';
}

// ---------------------------------------------------------------- placeholder car

export interface PlaceholderDims {
  /** overall length / width / height, m */
  length: number; width: number; height: number;
  wheelbase: number; trackFront: number; trackRear: number;
  tyreRadius: number;
}

export const PROBE_DIMS: PlaceholderDims = { length: 4.5, width: 1.72, height: 1.32, wheelbase: 2.614, trackFront: 1.514, trackRear: 1.514, tyreRadius: 0.316 };

const _c = new THREE.Color();
function painted(g: THREE.BufferGeometry, hex: string | number): THREE.BufferGeometry {
  _c.set(hex as THREE.ColorRepresentation);
  const n = g.attributes.position.count;
  const col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { col[3 * i] = _c.r; col[3 * i + 1] = _c.g; col[3 * i + 2] = _c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}
const box = (w: number, h: number, l: number, x: number, y: number, z: number) => new THREE.BoxGeometry(w, h, l).translate(x, y, z);

/** Number-board background that stands out from a body of this colour: near-black on light bodies, else near-white. */
export function boardColor(body: string): string {
  return /^#[0-9a-f]{6}$/i.test(body) && contrastInk(body) === '#111111' ? '#121417' : '#f6f6f2';
}

/**
 * Canvas texture for the number boards: big, heavy digits on a board that contrasts with the body, a dark (or
 * light) frame, and a band in the team's primary colour along the bottom. Sized to read from ~60 m. null without
 * a DOM (tests).
 */
export function numberTexture(num: string, primary = '#f4f4f0'): THREE.Texture | null {
  if (typeof document === 'undefined') return null;
  const W = 512, H = 256;
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d');
  if (!g) return null;
  const board = boardColor(primary), ink = contrastInk(board);
  const band = 40, frame = 14;
  g.fillStyle = ink; g.fillRect(0, 0, W, H);                                  // frame
  g.fillStyle = board; g.fillRect(frame, frame, W - 2 * frame, H - 2 * frame);  // board
  if (/^#[0-9a-f]{6}$/i.test(primary)) { g.fillStyle = primary; g.fillRect(frame, H - frame - band, W - 2 * frame, band); }
  g.fillStyle = ink;
  const px = num.length > 3 ? 150 : num.length > 2 ? 190 : 220;
  g.font = `900 ${px}px "Arial Black", "Helvetica Neue", Arial, system-ui, sans-serif`;
  g.textAlign = 'center'; g.textBaseline = 'middle';
  const cy = (frame + H - frame - band) / 2 + px * 0.04;
  g.lineJoin = 'round'; g.lineWidth = 8; g.strokeStyle = ink;
  g.strokeText(num, W / 2, cy, W - 2 * frame - 24);                           // heavier strokes
  g.fillText(num, W / 2, cy, W - 2 * frame - 24);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

/**
 * A low-poly box car with the same nodes as probe.glb (`body`, `wheel_fl/fr/rl/rr`; glTF frame: +Z nose, +Y up,
 * +X left, origin on the ground at mid-wheelbase): a wedge-nosed lower body and a tapered glasshouse in the car's
 * colour (one merged, vertex-coloured mesh), four 14-sided wheels, and number boards on both doors, the roof and
 * the tail (one mesh with a canvas texture). About 300 triangles, 6 draw calls.
 */
export function buildPlaceholderCar(num: string, color: string, dims: PlaceholderDims = PROBE_DIMS, tex: THREE.Texture | null = numberTexture(num, color)): THREE.Group {
  const { length: L, width: W, height: H, wheelbase: WB, tyreRadius: R } = dims;
  const root = new THREE.Group();
  root.name = `placeholder_${num}`;
  const floor = 0.2;
  const belt = Math.max(0.62, Math.min(H - 0.35, 0.58 * H + 0.05));
  const dark = '#1d2126', glass = '#2a3644';
  // lower body: wedge nose (top front edge dropped), slightly lower tail
  const lower = new THREE.BoxGeometry(W, belt - floor, L, 1, 1, 2).translate(0, (belt + floor) / 2, 0);
  const p = lower.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i), z = p.getZ(i);
    if (y > (belt + floor) / 2 && z > 0.4 * L) p.setY(i, y - 0.16);
    if (y > (belt + floor) / 2 && z < -0.4 * L) p.setY(i, y - 0.05);
  }
  lower.computeVertexNormals();
  // glasshouse: tapered toward the roof, set back from the centre
  const cabL = 0.48 * L, cabZ = -0.06 * L;
  const cabin = new THREE.BoxGeometry(0.9 * W, H - belt - 0.04, cabL).translate(0, (H + belt - 0.04) / 2, cabZ);
  const q = cabin.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < q.count; i++) {
    if (q.getY(i) > belt + 0.05) {
      q.setX(i, q.getX(i) * 0.86);
      q.setZ(i, cabZ + (q.getZ(i) - cabZ) * (q.getZ(i) > cabZ ? 0.62 : 0.8));
    }
  }
  cabin.computeVertexNormals();
  const roofL = cabL * 0.66;
  const roof = box(0.9 * W * 0.86 - 0.02, 0.05, roofL, 0, H - 0.04, cabZ - 0.03 * L);
  const bumperF = box(W * 0.98, 0.16, 0.12, 0, floor + 0.12, L / 2 - 0.04);
  const bumperR = box(W * 0.98, 0.16, 0.12, 0, floor + 0.14, -L / 2 + 0.04);
  const sill = box(W + 0.01, 0.07, WB - 2 * R - 0.1, 0, floor + 0.03, 0);
  const bodyGeo = mergeGeometries([
    painted(lower.toNonIndexed(), color), painted(cabin.toNonIndexed(), glass), painted(roof.toNonIndexed(), color),
    painted(bumperF.toNonIndexed(), dark), painted(bumperR.toNonIndexed(), dark), painted(sill.toNonIndexed(), dark),
  ])!;
  const body = new THREE.Mesh(bodyGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0.05 }));
  body.name = 'body';
  // number boards: doors (both sides), roof, tail; u runs to the viewer's right on every board. As large as the
  // panels allow (2:1), so the number reads from ~60 m: the door board fills the door height below the belt line.
  const bh = Math.max(0.3, Math.min(0.56, belt - floor - 0.03)), bw = Math.min(2 * bh, 0.46 * L);
  const doorY = (floor + belt) / 2 + 0.01;
  const doorL = new THREE.PlaneGeometry(bw, bw / 2).rotateY(Math.PI / 2).translate(W / 2 + 0.012, doorY, -0.02 * L);
  const doorR = new THREE.PlaneGeometry(bw, bw / 2).rotateY(-Math.PI / 2).translate(-W / 2 - 0.012, doorY, -0.02 * L);
  const roofW = 0.9 * W * 0.86 - 0.04;
  const rw = Math.min(roofW, roofL * 2) * 0.98;
  const roofB = new THREE.PlaneGeometry(rw, Math.min(rw / 2, roofL * 0.98)).rotateX(-Math.PI / 2).rotateY(Math.PI).translate(0, H + 0.005, cabZ - 0.03 * L);
  const tw = Math.min(0.84, 0.5 * W);
  const tail = new THREE.PlaneGeometry(tw, tw / 2).rotateY(Math.PI).translate(0, Math.max(floor + tw / 4 + 0.02, belt - tw / 4 - 0.06), -L / 2 - 0.012);
  const boardGeo = mergeGeometries([doorL, doorR, roofB, tail])!;
  // a little self-light so the board still reads on the shaded side of the car
  const boards = new THREE.Mesh(boardGeo, new THREE.MeshStandardMaterial({
    map: tex, color: tex ? 0xffffff : 0xf4f4f0, roughness: 0.6, emissive: tex ? 0xffffff : 0x000000, emissiveMap: tex, emissiveIntensity: tex ? 0.35 : 0,
  }));
  boards.name = 'number_boards';
  body.add(boards);
  root.add(body);
  // wheels: hub-centred, axle along local +X (CONTRACTS §3)
  const tyreGeo = new THREE.CylinderGeometry(R, R, 0.2, 14).rotateZ(Math.PI / 2);
  const tyreMat = new THREE.MeshStandardMaterial({ color: 0x1b1b1b, roughness: 0.9 });
  for (const [name, side, front] of [['wheel_fl', 1, 1], ['wheel_fr', -1, 1], ['wheel_rl', 1, -1], ['wheel_rr', -1, -1]] as const) {
    const w = new THREE.Mesh(tyreGeo, tyreMat);
    w.name = name;
    w.position.set(side * (front > 0 ? dims.trackFront : dims.trackRear) / 2, R, front * WB / 2);
    root.add(w);
  }
  // camera mounts (CarRig expects them; nobody rides in an AI car)
  for (const [name, y, z] of [['cam_driver', H - 0.2, -0.1 * L], ['cam_hood', belt + 0.1, 0.15 * L]] as const) {
    const o = new THREE.Object3D(); o.name = name; o.position.set(0.37, y, z); root.add(o);
  }
  return root;
}

/** Triangle count of an object tree (tests, budget). */
export function triangleCount(o: THREE.Object3D): number {
  let n = 0;
  o.traverse((x) => {
    const m = x as THREE.Mesh;
    if (!m.isMesh) return;
    const g = m.geometry;
    n += (g.index ? g.index.count : g.attributes.position.count) / 3;
  });
  return n;
}

// ---------------------------------------------------------------- lighting helpers

/**
 * A small sky / ground environment for the AI cars' materials (canvas cube map; three PMREMs it on first use).
 * Without one, a car's faces turned away from the sun get only the hemisphere fill, so dark liveries go black.
 * Only field-car materials use it; the world and the player's Probe are unchanged.
 */
let envTex: THREE.CubeTexture | null | undefined;
export function fieldEnvMap(): THREE.CubeTexture | null {
  if (envTex !== undefined) return envTex;
  if (typeof document === 'undefined') return (envTex = null);
  const face = (top: string, mid: string, bottom: string) => {
    const cv = document.createElement('canvas'); cv.width = cv.height = 32;
    const g = cv.getContext('2d')!;
    const gr = g.createLinearGradient(0, 0, 0, 32);
    gr.addColorStop(0, top); gr.addColorStop(0.5, mid); gr.addColorStop(1, bottom);
    g.fillStyle = gr; g.fillRect(0, 0, 32, 32);
    return cv;
  };
  const flat = (c: string) => face(c, c, c);
  const side = face('#7fa6d6', '#c4d3e0', '#8f7a5c');           // sky → haze at the horizon → dry ground
  // +x, -x, +y (up), -y (down), +z, -z
  envTex = new THREE.CubeTexture([side, side, flat('#6f9bd4'), flat('#7a6448'), side, side]);
  envTex.colorSpace = THREE.SRGBColorSpace;
  envTex.needsUpdate = true;
  return envTex;
}
/** envMap intensity on AI car materials (diffuse + specular sky fill). */
export const FIELD_ENV_INTENSITY = 1.0;
/** The look (look.ts): with `sceneEnv` the cars reflect scene.environment instead of the canvas cube; `clearcoat` upgrades their paint. */
let fieldLook = { clearcoat: false, sceneEnv: false };
export function setFieldLook(l: { clearcoat: boolean; sceneEnv: boolean }): void { fieldLook = l; }

/** Field-car material normalisation: sky env fill, no metal on painted surfaces (glTF defaults metallic to 1). */
export function prepareCarMaterials(root: THREE.Object3D, env: THREE.Texture | null = fieldEnvMap()): void {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
      const st = mat as THREE.MeshStandardMaterial;
      if (!st.isMeshStandardMaterial || st.userData.fieldPrepared) continue;
      st.userData.fieldPrepared = true;
      if (!st.transparent && st.metalness > 0.2) st.metalness = 0;
      if (env && !fieldLook.sceneEnv) { st.envMap = env; st.envMapIntensity = FIELD_ENV_INTENSITY; }
      st.needsUpdate = true;
    }
  });
  upgradeCarMaterials(root, { clearcoat: fieldLook.clearcoat });
}

let blobTex: THREE.Texture | null | undefined;
let blobGeo: THREE.PlaneGeometry | null = null;
let blobMat: THREE.MeshBasicMaterial | null = null;
/**
 * A soft contact shadow under an AI car (shared geometry / material; one draw call). Cars beyond the sun's shadow box
 * (±quality.shadowBoxM) or past the caster count keep it; a car that casts a real shadow hides its blob.
 */
export function contactShadow(length: number, width: number): THREE.Mesh {
  if (blobTex === undefined) {
    if (typeof document === 'undefined') blobTex = null;
    else {
      const cv = document.createElement('canvas'); cv.width = cv.height = 64;
      const g = cv.getContext('2d')!;
      const gr = g.createRadialGradient(32, 32, 4, 32, 32, 32);
      gr.addColorStop(0, 'rgba(0,0,0,0.85)'); gr.addColorStop(0.55, 'rgba(0,0,0,0.6)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
      blobTex = new THREE.CanvasTexture(cv);
    }
  }
  blobGeo ??= new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
  blobMat ??= new THREE.MeshBasicMaterial({
    map: blobTex ?? null, color: 0x000000, transparent: true, opacity: blobTex ? 0.7 : 0.35, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  });
  const m = new THREE.Mesh(blobGeo, blobMat);
  m.name = 'contact_shadow';
  m.scale.set(width * 1.3, 1, length * 1.15);
  m.position.y = 0.03;
  m.renderOrder = -1;
  m.castShadow = false; m.receiveShadow = false;
  return m;
}

// ---------------------------------------------------------------- the field

/** What FieldCars needs to know about one AI car (built from the director's cars + identity.json). */
export interface FieldCarInfo {
  number: string;
  /** index into the director's car list / poses() */
  idx: number;
  color: string;
  dims: PlaceholderDims;
  /** physics rolling radius (spec.wheel.radius) */
  physicsRadius: number;
}

interface Entry {
  info: FieldCarInfo;
  rig: CarRig;
  kind: 'placeholder' | 'model';
  meshes: THREE.Mesh[];
  /** the contact-shadow blob under the car (hidden while the car casts a real shadow) */
  blob: THREE.Mesh;
  shadow: boolean;
  disposables: { dispose(): void }[];
}

export interface FieldCarsOptions {
  /** cars drawn at most (quality.maxAiCarsDrawn) */
  maxDrawn: number;
  /** nearest N cars cast shadows (0: none, phone) */
  shadowCasters: number;
  /** a car casts only inside this distance of the player (the sun's shadow box half-size); beyond it it keeps its blob */
  shadowRangeM?: number;
}

export class FieldCars {
  readonly group = new THREE.Group();
  private entries: Entry[] = [];
  private byNumber = new Map<string, Entry>();
  /** cars drawn in the last update (diagnostics) */
  drawn = 0;
  private disposed = false;

  constructor(private opts: FieldCarsOptions) {
    this.group.name = 'field_cars';
  }

  get size(): number { return this.entries.length; }
  /** Cars currently showing their own model. */
  get modelCount(): number { return this.entries.filter((e) => e.kind === 'model').length; }
  kindOf(num: string): 'placeholder' | 'model' | null { return this.byNumber.get(num)?.kind ?? null; }
  rigOf(num: string): CarRig | null { return this.byNumber.get(num)?.rig ?? null; }

  /** Build placeholders for every AI car (call once per race; the rigs survive restarts). */
  build(cars: FieldCarInfo[]): void {
    for (const info of cars) {
      if (this.byNumber.has(info.number)) continue;
      const tex = numberTexture(info.number, info.color);
      const model = buildPlaceholderCar(info.number, info.color, info.dims, tex);
      const e = this.makeEntry(info, model, 'placeholder', { tyreRadius: info.dims.tyreRadius });
      if (tex) e.disposables.push(tex);
      model.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        e.disposables.push(m.geometry);
        for (const mat of Array.isArray(m.material) ? m.material : [m.material]) e.disposables.push(mat);
      });
      this.entries.push(e);
      this.byNumber.set(info.number, e);
      this.group.add(e.rig.root);
    }
  }

  private makeEntry(info: FieldCarInfo, model: THREE.Object3D, kind: Entry['kind'], o: { tyreRadius: number }): Entry {
    prepareCarMaterials(model);
    const rig = new CarRig(model, { tyreRadius: o.tyreRadius, physicsRadius: info.physicsRadius, castShadow: false });
    const meshes: THREE.Mesh[] = [];
    rig.root.traverse((x) => { const m = x as THREE.Mesh; if (m.isMesh) { m.castShadow = false; m.receiveShadow = false; meshes.push(m); } });
    const blob = contactShadow(info.dims.length, info.dims.width);
    rig.root.add(blob);
    rig.root.name = `ai_${info.number}`;
    rig.root.visible = false;
    return { info, rig, kind, meshes, blob, shadow: false, disposables: [] };
  }

  /** Swap a car's placeholder for its own model (a template scene; it is cloned, geometry shared). */
  useModel(num: string, template: THREE.Object3D, tyreRadius: number | undefined, brakeLamps?: readonly (readonly number[])[], lampsFallback = false): boolean {
    const old = this.byNumber.get(num);
    if (!old || this.disposed || old.kind === 'model') return false;
    const e = this.makeEntry(old.info, template.clone(true), 'model', { tyreRadius: tyreRadius ?? old.info.physicsRadius });
    if (brakeLamps?.length) e.rig.addBrakeLamps(brakeLamps, { alwaysOn: lampsFallback });
    e.rig.root.visible = old.rig.root.visible;
    this.group.remove(old.rig.root);
    for (const d of old.disposables) d.dispose();
    this.group.add(e.rig.root);
    this.entries[this.entries.indexOf(old)] = e;
    this.byNumber.set(num, e);
    return true;
  }

  /**
   * Per frame: draw the nearest `maxDrawn` cars by track distance (`s` = lap distance per director car index,
   * `playerIdx` the player's index), pose them from their VehicleState, nearest `shadowCasters` cast shadows.
   */
  update(states: readonly VehicleState[], s: ArrayLike<number>, playerIdx: number, L: number, brakes?: ArrayLike<number>): void {
    const order = selectDrawn(s, s[playerIdx], L, Number.POSITIVE_INFINITY, playerIdx);
    const rank = new Map<number, number>();
    order.forEach((i, k) => rank.set(i, k));
    let drawn = 0;
    for (const e of this.entries) {
      const r = rank.get(e.info.idx) ?? Infinity;
      const show = r < this.opts.maxDrawn;
      e.rig.root.visible = show;
      if (!show) continue;
      drawn++;
      e.rig.pose(states[e.info.idx]);
      if (brakes) e.rig.setBrakeLights(brakes[e.info.idx] > 0.05);
      const ps = states[playerIdx];
      const cast = r < this.opts.shadowCasters && (this.opts.shadowRangeM === undefined || !ps
        || Math.hypot(states[e.info.idx].pos[0] - ps.pos[0], states[e.info.idx].pos[1] - ps.pos[1]) < this.opts.shadowRangeM);
      if (cast !== e.shadow) { e.shadow = cast; e.blob.visible = !cast; for (const m of e.meshes) m.castShadow = cast; }
    }
    this.drawn = drawn;
  }

  /** Adaptive quality (perf.ts): change the draw cap and the shadow casters between frames. */
  setLimits(maxDrawn: number, shadowCasters: number): void { this.opts = { ...this.opts, maxDrawn, shadowCasters }; }
  get limits(): Readonly<FieldCarsOptions> { return this.opts; }

  setVisible(on: boolean): void { this.group.visible = on; }

  dispose(): void {
    this.disposed = true;
    this.group.removeFromParent();
    for (const e of this.entries) for (const d of e.disposables) d.dispose();
    this.entries = []; this.byNumber.clear();
  }
}
