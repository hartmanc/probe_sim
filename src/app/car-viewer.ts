// The Cars page (owner, 31 Oct 2026): one field car at a time on a stage, with a card, an orbit camera and its engine.
//
// The page is reached from the main menu's Cars row. The main menu stays open underneath (hidden by a class), so the
// pad / key navigation keeps flowing as NavEvents and Back returns to the same row. The scene is the game's own
// (world.scene, Look, the chase camera object): the track and the player's car are hidden for the studio stage, the
// player's car and the ghosts for the track stage. Models come through loadFieldModel and prepareCarMaterials, as the
// race loads them; one at a time, the neighbours prefetched, what is paged away freed (only what this page loaded).
import * as THREE from 'three';
import { CarRig, bodyQuatToThree, enuToThree } from './car';
import type { CameraRig } from './cameras';
import type { CarAudio } from './audio';
import { FieldAudio, type FieldCar } from './audio-field';
import { prepareCarMaterials } from './field-cars';
import { fieldModelCached, loadFieldData, loadFieldModel, releaseFieldModel, type FieldModelInfo } from './loader';
import type { Look } from './look';
import type { Menu, NavEvent } from './menu';
import { carSound, parseSoundIndex, type FieldSoundIndex } from './modes/race';
import type { World } from './scene';
import type { TrackJson } from './physics-types';
import {
  SETTLE_END, makeBlip, cardFor, creditFor, fitPlane, seatOffset, engineAt, classSizes, fieldSize, indexByNumber, safeUrl, viewerOrder,
  type AwardEntry, type Blip, type Card, type CreditRow, type IdentityRow, type PhotoRow, type ViewerCar,
} from './car-viewer-data';

export type StageKind = 'studio' | 'track';
/** `?stage=studio|track` (default studio). */
export function stageFromUrl(search: string): StageKind {
  return new URLSearchParams(search).get('stage') === 'track' ? 'track' : 'studio';
}

/** The event each field belongs to, for the page title. */
const EVENT_TITLES: Record<string, string> = {
  laguna_seca: 'Twenty Ridiculous Years, Laguna Seca, Oct 2026',
  sonoma: 'Sears Pointless, Sonoma, Mar 2026',
  buttonwillow: 'Button Turrible, Buttonwillow, Sep 2026',
  mid_ohio: 'Mid-West Crisis, Mid-Ohio, Apr 2026',
};

const FOV = 38;
const AUTO_TURN_S = 20, AUTO_RESUME_MS = 4000;
const PROBE_KEY = '619';
/** The page's engine sound is off (owner, 31 Oct 2026); `?viewersound=1` turns the scripted cold start and warm-up back on for listening. */
export const VIEWER_SOUND: boolean = typeof location !== 'undefined' && new URLSearchParams(location.search).get('viewersound') === '1';

export interface ViewerDeps {
  app: HTMLElement;
  trackId: string;
  trackShort: string;
  stage: StageKind;
  world: World;
  look: Look;
  cams: CameraRig;
  renderer: THREE.WebGLRenderer;
  menu: Menu;
  input: { lookX: number; lookY: number; lookInNav: boolean; pedal: { throttle: { value: number }; brake: { value: number } } };
  audio: CarAudio;
  track: TrackJson;
  /** ENU start point and heading of the parking place, and the ground height there. */
  parking: () => { pos: [number, number, number]; heading: number };
  /** The game's own Probe model (the #619 row has no field model). */
  probeModel: THREE.Object3D;
  shadows: boolean;
  /** Surface height (ENU z) at ENU (x, y): the track stage seats the car on the road's camber and crown. */
  ground: (x: number, y: number) => number;
  /** Objects to hide on either stage (the player's car, the ghosts). */
  hide: () => THREE.Object3D[];
  toast(m: string, ms?: number): void;
  onClose(): void;
}

interface ViewerData {
  identity: IdentityRow[];
  cars: ViewerCar[];
  skipped: number;
  total: number;
  classes: Record<string, number>;
  models: Map<string, FieldModelInfo>;
  photos: Record<string, PhotoRow[]>;
  credits: unknown;
  sound: FieldSoundIndex | null;
  title: string;
}

async function getJson<T>(url: string): Promise<T | null> {
  try {
    const r = await fetch(url);
    if (!r.ok || (r.headers.get('content-type') ?? '').includes('text/html')) return null;
    return (await r.json()) as T;
  } catch { return null; }
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}
/** A trophy (cup, two handles, stem and base) as inline SVG, filled with the badge's text colour. */
function trophy(): SVGElement {
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true'); svg.setAttribute('class', 'cv-trophy');
  const path = document.createElementNS(NS, 'path');
  path.setAttribute('fill', 'currentColor');
  path.setAttribute('d', 'M7 3h10v6a5 5 0 0 1-10 0V3zM7 5H3v2a4 4 0 0 0 4 4V9.2A2 2 0 0 1 5 7V6.5h2V5zm10 0h4v2a4 4 0 0 1-4 4V9.2A2 2 0 0 0 19 7V6.5h-2V5zM11 14h2v3h-2zM8 18h8v3H8z');
  svg.append(path);
  return svg;
}
function link(href: string, text: string): HTMLAnchorElement {
  const a = el('a', undefined, text);
  a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
  return a;
}

function disposeMaterial(m: THREE.Material, textures: boolean): void {
  if (textures) for (const v of Object.values(m)) if (v && (v as THREE.Texture).isTexture) (v as THREE.Texture).dispose();
  m.dispose();
}
function materialsOf(root: THREE.Object3D): Set<THREE.Material> {
  const s = new Set<THREE.Material>();
  root.traverse((o) => { const m = (o as THREE.Mesh).material; for (const x of Array.isArray(m) ? m : m ? [m] : []) s.add(x); });
  return s;
}
function disposeTree(root: THREE.Object3D): void {
  root.traverse((o) => { (o as THREE.Mesh).geometry?.dispose(); });
  for (const m of materialsOf(root)) disposeMaterial(m, true);
}

export class CarViewer {
  private root = el('div', 'cv hidden');
  private group = new THREE.Group();
  private titleEl = el('div', 'cv-title');
  private posEl = el('div', 'cv-pos');
  private card = el('div', 'cv-card');
  private loadingEl = el('div', 'cv-loading', 'Loading…');
  private typedEl = el('div', 'cv-typed hidden');
  private awardsEl = el('div', 'cv-awards');
  private hintEl = el('div', 'cv-hint');
  private opened = false;
  private data: ViewerData | null = null;
  private dataP: Promise<ViewerData> | null = null;
  private index = 0;
  private lastKey: string | null = null;
  private token = 0;
  // stage
  private hidden: { o: THREE.Object3D; v: boolean }[] = [];
  private floor: THREE.Object3D | null = null;
  private stagePos = new THREE.Vector3();
  private rig: { rig: CarRig; key: string; shared: boolean; tpl: THREE.Object3D | null } | null = null;
  // camera
  private az = 0; private el = 0.22; private zoom = 1;
  private baseDist = 6.5; private targetY = 0.6;
  private box: THREE.Box3 | null = null;
  private lastInputAt = -Infinity;
  private pointers = new Map<number, { x: number; y: number }>();
  private pinch = 0;
  private lastT = 0;
  // sound
  private fa: FieldAudio | null = null;
  private engine: { id: number; t0: number; idle: number; family: string; snd: { trim: number; muffler: number; rpmScale: number }; redline: number; blips: Blip[]; last: number } | null = null;
  private typed = ''; private typedAt = 0;
  private padPrev: boolean[] = [];
  private onKey = (e: KeyboardEvent) => this.key(e);

  constructor(private d: ViewerDeps) {
    const top = el('div', 'cv-top');
    const back = el('button', 'cv-back', '‹ Back');
    back.type = 'button';
    back.addEventListener('click', () => this.close());
    const head = el('div', 'cv-head');
    head.append(this.titleEl, this.posEl);
    top.append(back, head);
    const prev = el('button', 'cv-arrow cv-prev', '‹'), next = el('button', 'cv-arrow cv-next', '›');
    prev.type = next.type = 'button';
    prev.setAttribute('aria-label', 'Previous car'); next.setAttribute('aria-label', 'Next car');
    prev.addEventListener('click', () => this.step(-1));
    next.addEventListener('click', () => this.step(1));
    this.root.append(top, prev, next, this.awardsEl, this.card, this.loadingEl, this.typedEl, this.hintEl);
    d.app.appendChild(this.root);
    d.world.scene.add(this.group);
    this.group.visible = false;
    const cv = d.renderer.domElement;
    cv.addEventListener('pointerdown', (e) => this.pDown(e));
    cv.addEventListener('pointermove', (e) => this.pMove(e));
    const up = (e: PointerEvent) => { this.pointers.delete(e.pointerId); this.pinch = 0; };
    cv.addEventListener('pointerup', up);
    cv.addEventListener('pointercancel', up);
    cv.addEventListener('wheel', (e) => { if (!this.opened) return; e.preventDefault(); this.dolly(Math.exp(e.deltaY * 0.001)); }, { passive: false });
  }

  get isOpen(): boolean { return this.opened; }
  /** For the console / tests. */
  get state() { return { index: this.index, key: this.lastKey, count: this.data?.cars.length ?? 0, skipped: this.data?.skipped ?? 0, stage: this.d.stage }; }

  // ------------------------------------------------------------ open / close

  open(): void {
    if (this.opened) return;
    this.opened = true;
    const d = this.d;
    d.menu.root.classList.add('cv-hide');
    this.root.classList.remove('hidden');
    d.input.lookInNav = true;
    if (VIEWER_SOUND) {
      void d.audio.start();
      setTimeout(() => { if (this.opened && d.audio.suspended) d.toast('Press any key or tap the screen for sound', 5000); }, 700);
      d.audio.hush();
    }
    this.hintEl.textContent = document.documentElement.classList.contains('touch')
      ? 'Drag to orbit · pinch to zoom · arrows for the next car'
      : 'Left / right: cars · right stick or drag: orbit · triggers, wheel: zoom · type a number · Esc: back';
    this.buildStage();
    window.addEventListener('keydown', this.onKey);
    this.lastT = performance.now();
    this.loadingEl.classList.remove('hidden');
    this.titleEl.textContent = `Cars · ${EVENT_TITLES[d.trackId] ?? d.trackShort}`;
    this.dataP ??= this.loadData();
    void this.dataP.then((data) => {
      if (!this.opened) return;
      this.data = data;
      this.titleEl.textContent = `Cars · ${data.title}`;
      if (!data.cars.length) { this.loadingEl.textContent = 'No cars with models for this event.'; return; }
      const at = this.lastKey ? data.cars.findIndex((c) => c.key === this.lastKey) : 0;
      this.show(at >= 0 ? at : 0);
    }).catch((e) => { this.loadingEl.textContent = `Could not load the field: ${String(e)}`; });
  }

  close(): void {
    if (!this.opened) return;
    this.opened = false;
    const d = this.d;
    this.token++;
    window.removeEventListener('keydown', this.onKey);
    this.stopEngine(true);
    this.fa?.dispose(); this.fa = null;
    this.dropRig();
    this.freeAll();
    this.group.visible = false;
    if (this.floor) { this.group.remove(this.floor); disposeTree(this.floor); this.floor = null; }
    for (const h of this.hidden) h.o.visible = h.v;
    this.hidden = [];
    d.input.lookInNav = false;
    this.root.classList.add('hidden');
    d.menu.root.classList.remove('cv-hide');
    this.pointers.clear();
    d.cams.resize(window.innerWidth / window.innerHeight);
    d.cams.setMode(d.cams.mode);
    d.onClose();
  }

  // ------------------------------------------------------------ data

  private async loadData(): Promise<ViewerData> {
    const f = await loadFieldData();
    const identity = (Array.isArray(f.identity) ? f.identity : []) as IdentityRow[];
    const dir = (f.identityPath ?? 'cars/field/identity.json').replace(/identity\.json$/, '');
    const [awards, photos, credits, soundRaw] = await Promise.all([
      getJson<AwardEntry[]>(dir + 'awards.json'), getJson<Record<string, PhotoRow[]>>(dir + 'photos.json'),
      getJson<{ cars?: unknown }>('cars/field/credits.json'), getJson<unknown>('audio/families/index.json'),
    ]);
    const models = new Map<string, FieldModelInfo>(f.models.map((m) => [m.id, m]));
    const { cars, skipped } = viewerOrder(identity, Array.isArray(awards) ? awards : [], (k) => models.has(k) || k === PROBE_KEY);
    return {
      identity, cars, skipped, total: fieldSize(identity), classes: classSizes(identity), models, photos: photos ?? {}, credits: credits?.cars ?? {},
      sound: parseSoundIndex(soundRaw), title: EVENT_TITLES[this.d.trackId] ?? this.d.trackShort,
    };
  }

  // ------------------------------------------------------------ stage

  private buildStage(): void {
    const d = this.d, sc = d.world.scene;
    const keep = new Set<THREE.Object3D>([this.group, d.look.sky]);
    if (d.stage === 'studio') {
      for (const o of sc.children) {
        if (keep.has(o) || (o as THREE.Light).isLight) continue;
        this.hidden.push({ o, v: o.visible }); o.visible = false;
      }
    } else {
      for (const o of d.hide()) { this.hidden.push({ o, v: o.visible }); o.visible = false; }
    }
    for (const o of sc.children) if (o.name === 'field_cars' && o.visible) { this.hidden.push({ o, v: true }); o.visible = false; }
    const p = d.parking();
    // ENU (x, y, z up) to three (x, z, -y)
    this.stagePos.set(p.pos[0], p.pos[2], -p.pos[1]);
    if (d.stage === 'studio') {
      const floor = new THREE.Group();
      const mat = new THREE.MeshStandardMaterial({ color: 0x8d949c, roughness: 0.92, metalness: 0 });
      const big = new THREE.Mesh(new THREE.CircleGeometry(900, 48).rotateX(-Math.PI / 2), mat);
      big.receiveShadow = true;
      const ring = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.6, 0.03, 64), new THREE.MeshStandardMaterial({ color: 0xc7ccd2, roughness: 0.75 }));
      ring.position.y = 0.012; ring.receiveShadow = true;
      floor.add(big, ring);
      floor.position.copy(this.stagePos);
      floor.position.y -= 0.005;
      this.group.add(floor);
      this.floor = floor;
    }
    this.group.visible = true;
    const cam = d.cams.camera;
    cam.fov = FOV; cam.near = 0.05; cam.far = 4000; cam.updateProjectionMatrix();
    // three-quarter front view to start
    // ENU heading h points along (cos h, sin h): three (x, z) = (cos h, -sin h)
    this.az = Math.atan2(Math.cos(p.heading), -Math.sin(p.heading)) + 0.75;
    this.el = 0.2; this.zoom = 1; this.lastInputAt = -Infinity;
  }

  // ------------------------------------------------------------ cars

  private step(dir: 1 | -1): void {
    const n = this.data?.cars.length ?? 0;
    if (n < 2) return;
    this.show((this.index + dir + n) % n);
  }

  private modelFile(key: string): FieldModelInfo | undefined { return this.data?.models.get(key); }

  /**
   * Models by file. An entry is created when a car is shown or prefetched; `tpl` stays undefined while the load is pending.
   * `mine`: this page parsed it (nobody else had it cached), so this page frees it. An entry is never freed while it is
   * pending or inside the window (the shown car and its two neighbours); a pending one out of the window is freed when it lands.
   */
  private ents = new Map<string, { p: Promise<THREE.Object3D | null>; tpl?: THREE.Object3D | null; mine: boolean }>();
  private windowFiles = new Set<string>();

  private getTemplate(key: string): Promise<THREE.Object3D | null> {
    if (key === PROBE_KEY && !this.modelFile(key)) return Promise.resolve(this.d.probeModel);
    const m = this.modelFile(key);
    if (!m) return Promise.resolve(null);
    let e = this.ents.get(m.file);
    if (!e) {
      const ent: { p: Promise<THREE.Object3D | null>; tpl?: THREE.Object3D | null; mine: boolean } = { p: Promise.resolve(null), mine: !fieldModelCached(m.file) };
      ent.p = this.loadWithRetry(key, m.file).then((t) => { ent.tpl = t; this.sweep(); return t; });
      this.ents.set(m.file, ent);
      e = ent;
    }
    return e.p;
  }

  /** One retry: a null (fetch or parse failed) is dropped from the loader's cache first so the second try fetches again. */
  private async loadWithRetry(key: string, file: string): Promise<THREE.Object3D | null> {
    for (let attempt = 1; attempt <= 2; attempt++) {
      try {
        const t = await loadFieldModel(file);
        if (t) return t;
        console.warn(`[viewer] model ${key} (${file}) attempt ${attempt}: the loader returned nothing (fetch or parse failed)`);
      } catch (err) {
        console.warn(`[viewer] model ${key} (${file}) attempt ${attempt} failed:`, err);
      }
      releaseFieldModel(file);
    }
    return null;
  }

  /** Free the entries outside the window that are not pending. */
  private sweep(): void {
    for (const [file, e] of [...this.ents]) {
      if (this.windowFiles.has(file) || e.tpl === undefined) continue;
      this.ents.delete(file);
      if (e.mine && e.tpl) { disposeTree(e.tpl); releaseFieldModel(file); }
    }
  }

  private show(i: number): void {
    const data = this.data!;
    this.index = i;
    const car = data.cars[i];
    this.lastKey = car.key;
    const my = ++this.token;
    this.stopEngine(false);
    this.dropRig();
    this.loadingEl.textContent = 'Loading…';
    this.loadingEl.classList.remove('hidden');
    this.renderCard(cardFor(car, i, data.cars.length, data.total, creditFor(data.credits, car.key), data.photos[car.key], data.classes));
    // the window first (so nothing it needs is swept), then the loads
    const n = data.cars.length;
    const keys = [i, (i + 1) % n, (i - 1 + n) % n].map((k) => data.cars[k].key);
    this.windowFiles = new Set(keys.map((k) => this.modelFile(k)?.file).filter((f): f is string => !!f));
    this.getTemplate(car.key).then((tpl) => {
      if (my !== this.token || !this.opened) return;
      if (!tpl) { this.loadingEl.textContent = 'This model did not load.'; return; }
      this.buildRig(car, tpl);
      this.loadingEl.classList.add('hidden');
      void this.startEngine(car, my);
    }).catch((err) => {
      console.warn(`[viewer] showing ${car.key} failed:`, err);
      if (my === this.token) this.loadingEl.textContent = 'This model did not load.';
    });
    for (const k of keys) if (k !== car.key) void this.getTemplate(k);
    this.sweep();
  }

  private buildRig(car: ViewerCar, tpl: THREE.Object3D): void {
    const shared = tpl === this.d.probeModel;
    const clone = tpl.clone(true);
    if (!shared) prepareCarMaterials(clone);
    // the page's own double-sided copies of the materials (the field models are single-sided: from inside the body the
    // panels vanish); the shared race materials are never touched
    const copies = new Map<THREE.Material, THREE.Material>();
    clone.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      const own = (m: THREE.Material) => { let c = copies.get(m); if (!c) { c = m.clone(); c.side = THREE.DoubleSide; copies.set(m, c); } return c; };
      mesh.material = Array.isArray(mesh.material) ? mesh.material.map(own) : own(mesh.material);
    });
    const m = this.modelFile(car.key);
    const r = m?.tyre_radius_m;
    const rig = new CarRig(clone, { tyreRadius: r, physicsRadius: r, castShadow: this.d.shadows });
    const p = this.d.parking();
    rig.poseSimple(p.pos, p.heading, 0);
    if (this.d.stage === 'track') this.seatOnRoad(rig, p);
    if (m?.brake_lamps?.length) rig.addBrakeLamps(m.brake_lamps, { alwaysOn: !!m.brake_lamps_fallback });
    this.group.add(rig.root);
    rig.root.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(rig.root);
    const size = box.getSize(new THREE.Vector3());
    this.targetY = Math.max(0.45, Math.min(1.1, size.y * 0.45));
    this.baseDist = Math.max(5.2, Math.min(10, Math.max(size.x, size.z, size.y * 2.2) * 1.55));
    this.box = box;
    this.rig = { rig, key: car.key, shared, tpl };
  }

  /**
   * Track stage: fit a plane through the road height under the four tyre contacts, tilt the car to it (pitch and roll)
   * and lower it until its lowest contact is exactly on the surface. Re-done for each car (wheelbase, track, tyre radius differ).
   */
  private seatOnRoad(rig: CarRig, p: { pos: [number, number, number]; heading: number }): void {
    const f = [Math.cos(p.heading), Math.sin(p.heading)], l = [-Math.sin(p.heading), Math.cos(p.heading)];
    // contacts in the car's frame: model x is left, z is forward; the hub rest pose less the tyre radius
    const pts: [number, number, number][] = rig.wheels.map((w) => {
      const u = w.rest.z, v = w.rest.x;
      return [u, v, this.d.ground(p.pos[0] + u * f[0] + v * l[0], p.pos[1] + u * f[1] + v * l[1])];
    });
    if (pts.some((q) => !isFinite(q[2]))) return;
    const fit = fitPlane(pts);
    const cy = rig.wheels.reduce((a, w) => a + (w.rest.y - rig.tyreRadius), 0) / 4;   // contact height in the model frame
    const N = new THREE.Vector3(-fit.b * f[0] - fit.c * l[0], -fit.b * f[1] - fit.c * l[1], 1).normalize();
    const F = new THREE.Vector3(f[0], f[1], 0);
    F.addScaledVector(N, -F.dot(N)).normalize();
    const L = new THREE.Vector3().crossVectors(N, F);
    const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(F, L, N));
    bodyQuatToThree([q.x, q.y, q.z, q.w], rig.root.quaternion);
    const base = new THREE.Vector3(p.pos[0], p.pos[1], fit.a + seatOffset(fit)).addScaledVector(N, -cy);
    enuToThree([base.x, base.y, base.z], rig.root.position);
    rig.root.updateMatrixWorld(true);
  }

  private dropRig(): void {
    const r = this.rig;
    if (!r) return;
    this.rig = null;
    r.rig.root.removeFromParent();
    if (r.shared) return;
    for (const m of materialsOf(r.rig.root)) disposeMaterial(m, false); // the page's own copies (textures stay with the template)
  }

  private freeAll(): void {
    this.windowFiles.clear();
    this.sweep();   // anything still pending is freed when it lands
  }

  // ------------------------------------------------------------ card

  private renderCard(c: Card): void {
    const k = this.card;
    const num = el('div', 'cv-num', `#${c.number}`);
    const team = el('div', 'cv-team', c.team);
    const car = el('div', 'cv-car', c.car + (c.cls ? `  ·  Class ${c.cls}` : ''));
    const parts: Node[] = [num, team, car];
    const stats = el('div', 'cv-stats');
    for (const [l, v] of [['Overall', c.overall], ['Class', c.classRank], ['Laps', c.laps], ['Fastest', c.fastest]] as const) {
      const s = el('div', 'cv-stat'); s.append(el('span', 'cv-sl', l), el('span', 'cv-sv', v)); stats.append(s);
    }
    parts.push(stats);
    const second = el('div', 'cv-second');
    const mline = el('div', 'cv-model');
    if (c.model.title || c.model.author) {
      const tu = safeUrl(c.model.titleUrl), lu = safeUrl(c.model.licenceUrl);
      mline.append('Model: ', tu ? link(tu, c.model.title ?? 'model') : (c.model.title ?? 'model'));
      if (c.model.author) mline.append(` by ${c.model.author}`);
      if (c.model.licence) { mline.append(', '); mline.append(lu ? link(lu, c.model.licence) : c.model.licence); }
    } else mline.append(c.model.text);
    second.append(mline);
    if (c.model.changes) second.append(el('div', 'cv-changes', `Changes: ${c.model.changes}`));
    if (c.photos.length || c.ownerPhotos) {
      const ph = el('div', 'cv-photos', 'Photos: ');
      c.photos.forEach((p, i) => { const u = safeUrl(p.url); if (u) { if (i) ph.append(' '); ph.append(link(u, String(p.n))); } });
      if (c.ownerPhotos) ph.append(`${c.photos.length ? ' ' : ''}+ owner's photo${c.ownerPhotos > 1 ? 's' : ''}`);
      second.append(ph);
    }
    parts.push(second);
    k.replaceChildren(...parts);
    this.awardsEl.replaceChildren(...c.awards.map((a) => { const b = el('div', 'cv-award'); b.append(trophy(), el('span', undefined, a)); return b; }));
    this.posEl.textContent = c.position;
  }

  // ------------------------------------------------------------ sound

  private async startEngine(car: ViewerCar, token: number): Promise<void> {
    if (!VIEWER_SOUND) return;
    const d = this.d, data = this.data!;
    const ctx = d.audio.context, bus = d.audio.fieldBus();
    if (!ctx || !bus || !data.sound) return;
    try {
      if (!this.fa) this.fa = new FieldAudio(ctx, bus, { index: data.sound, maxVoices: 1, range: 80 });
      const id = car.row.engine ?? {};
      const snd = carSound(data.sound, { number: String(car.row.number), id: car.key, identity: car.row, engine: { layout: id.layout ?? '', cylinders: id.cylinders ?? 4, exhaustNote: id.exhaust_note ?? null } });
      if (!snd.family) return;   // an electric car makes no sound
      await this.fa.ready();
      await this.fa.preload([snd.family]);
      if (token !== this.token || !this.opened) return;
      const fam = data.sound.families[snd.family] ?? data.sound.families[data.sound.default];
      const redline = id.redline_rpm ?? fam?.redline ?? 6500;
      this.engine = { id: token, t0: performance.now() / 1000, idle: (fam?.idle ?? 800) / snd.rpmScale, family: snd.family, snd, redline, blips: [makeBlip(SETTLE_END, Math.random)], last: 0 };
    } catch (e) { console.warn('cars page: engine sound', e); }
  }

  private stopEngine(now: boolean): void {
    this.engine = null;
    if (this.fa) this.fa.update({ pos: [-3, 0, 0], vel: [0, 0, 0] }, []);
    if (now && VIEWER_SOUND) this.d.audio.hush();
  }

  private tickEngine(): void {
    const e = this.engine, fa = this.fa;
    if (!e || !fa) return;
    const t = performance.now() / 1000 - e.t0;
    const tail = e.blips[e.blips.length - 1];
    if (t > tail.t0 - 0.5) { e.blips.push(makeBlip(tail.t0 + tail.rise + tail.fall, Math.random)); if (e.blips.length > 4) e.blips.shift(); }
    const f = engineAt(t, e.idle, e.blips);
    const car: FieldCar = {
      id: e.id, pos: [0, 0, 0], vel: [0, 0, 0], rpm: f.rpm * e.snd.rpmScale, throttle: f.throttle, redline: e.redline * e.snd.rpmScale,
      family: e.family, trim: e.snd.trim, muffler: e.snd.muffler,
    };
    fa.update({ pos: [-3, 0, 0], vel: [0, 0, 0], quat: [0, 0, 0, 1] }, [car]);
  }

  // ------------------------------------------------------------ input

  private key(e: KeyboardEvent): void {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const dig = /^[0-9]$/.test(e.key) ? e.key : null;
    if (dig !== null) {
      const now = performance.now();
      this.typed = (now - this.typedAt > 1500 ? '' : this.typed) + dig;
      if (this.typed.length > 5) this.typed = dig;
      this.typedAt = now;
      const i = this.data ? indexByNumber(this.data.cars, this.typed) : -1;
      this.typedEl.textContent = i >= 0 ? `#${this.typed}` : `#${this.typed} …`;
      this.typedEl.classList.remove('hidden');
      if (i >= 0 && i !== this.index) this.show(i);
      return;
    }
    if (e.key === '+' || e.key === '=') this.dolly(0.85);
    else if (e.key === '-' || e.key === '_') this.dolly(1 / 0.85);
  }

  /** NavEvents from the pad / keys (the main menu's own routing is bypassed while the page is open). */
  nav(ev: NavEvent): void {
    if (!this.opened) return;
    switch (ev) {
      case 'left': this.step(-1); break;
      case 'right': this.step(1); break;
      case 'up': this.dolly(0.85); break;
      case 'down': this.dolly(1 / 0.85); break;
      case 'back': case 'menu': this.close(); break;
      default: break;
    }
  }

  private dolly(f: number): void {
    this.zoom = Math.max(0.4, Math.min(2.6, this.zoom * f));
    this.lastInputAt = performance.now();
  }

  private pDown(e: PointerEvent): void {
    if (!this.opened || (e.pointerType === 'mouse' && e.button !== 0)) return;
    this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    try { (e.target as Element).setPointerCapture(e.pointerId); } catch { /* not capturable */ }
    this.lastInputAt = performance.now();
    this.pinch = this.pointers.size === 2 ? this.pinchDist() : 0;
  }
  private pinchDist(): number { const [a, b] = [...this.pointers.values()]; return Math.hypot(a.x - b.x, a.y - b.y); }
  private pMove(e: PointerEvent): void {
    const p = this.pointers.get(e.pointerId);
    if (!p || !this.opened) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    p.x = e.clientX; p.y = e.clientY;
    this.lastInputAt = performance.now();
    if (this.pointers.size >= 2) {
      const dist = this.pinchDist();
      if (this.pinch > 0 && dist > 0) this.dolly(this.pinch / dist);
      this.pinch = dist;
      return;
    }
    this.az -= dx * 0.007;
    this.el += dy * 0.006;
  }

  private pollPad(): void {
    const pads = typeof navigator !== 'undefined' && navigator.getGamepads ? navigator.getGamepads() : [];
    const pad = [...pads].find((p) => p && p.connected);
    if (!pad) { this.padPrev = []; return; }
    const on = (i: number) => !!pad.buttons[i] && (pad.buttons[i].pressed || pad.buttons[i].value > 0.5);
    const edge = (i: number) => on(i) && !this.padPrev[i];
    if (pad.mapping === 'standard') { if (edge(4)) this.step(-1); if (edge(5)) this.step(1); }
    this.padPrev = pad.buttons.map((_, i) => on(i));
  }

  // ------------------------------------------------------------ frame

  /** One rendered frame (called from the sim's frame while the page is open). */
  frame(now: number): void {
    if (!this.opened) return;
    const d = this.d;
    const dt = Math.min(0.05, Math.max(0, (now - this.lastT) / 1000));
    this.lastT = now;
    this.pollPad();
    const inp = d.input;
    // the look stick orbits (rate), the triggers zoom
    const sx = inp.lookX, sy = inp.lookY;
    if (Math.abs(sx) > 0.05 || Math.abs(sy) > 0.05) { this.az += sx * 2.0 * dt; this.el -= sy * 1.2 * dt; this.lastInputAt = now; }
    const z = inp.pedal.brake.value - inp.pedal.throttle.value;
    if (Math.abs(z) > 0.05) this.dolly(Math.exp(z * 1.4 * dt));
    if (now - this.lastInputAt > AUTO_RESUME_MS) this.az += (Math.PI * 2 / AUTO_TURN_S) * dt;
    if (this.typed && now - this.typedAt > 1500) { this.typed = ''; this.typedEl.classList.add('hidden'); }

    // orbit camera; the pitch never takes it under the floor
    const c = this.stagePos;
    const ty = c.y + this.targetY;
    // the closest zoom keeps the camera 0.4 m outside the model's box along the view direction, and the pitch keeps it above the floor
    const dirv = new THREE.Vector3();
    const distFor = (el: number): number => {
      const want = Math.max(2.2, Math.min(22, this.baseDist * this.zoom));
      if (!this.box) return want;
      dirv.set(Math.sin(this.az) * Math.cos(el), Math.sin(el), Math.cos(this.az) * Math.cos(el));
      const o = [c.x, ty, c.z], dd = [dirv.x, dirv.y, dirv.z], lo = [this.box.min.x, this.box.min.y, this.box.min.z], hi = [this.box.max.x, this.box.max.y, this.box.max.z];
      let exit = Infinity;
      for (let k = 0; k < 3; k++) {
        if (dd[k] > 1e-6) exit = Math.min(exit, (hi[k] - o[k]) / dd[k]);
        else if (dd[k] < -1e-6) exit = Math.min(exit, (lo[k] - o[k]) / dd[k]);
      }
      return Math.max(want, Math.max(0, exit) + 0.4);
    };
    this.el = Math.min(1.35, this.el);
    let dist = distFor(this.el);
    for (let k = 0; k < 4; k++) {
      const elMin = Math.asin(Math.max(-1, Math.min(1, (0.3 - this.targetY) / dist)));
      if (this.el >= elMin) break;
      this.el = elMin; dist = distFor(this.el);
    }
    const cam = d.cams.camera;
    if (cam.fov !== FOV || cam.far !== 4000) { cam.fov = FOV; cam.near = 0.05; cam.far = 4000; cam.updateProjectionMatrix(); }
    const ce = Math.cos(this.el);
    cam.position.set(c.x + dist * Math.sin(this.az) * ce, c.y + this.targetY + dist * Math.sin(this.el), c.z + dist * Math.cos(this.az) * ce);
    cam.lookAt(c.x, c.y + this.targetY, c.z);
    d.world.follow(this.rig?.rig.root.position ?? c, cam);
    this.tickEngine();
    if (!document.hidden) d.look.render(dt, 0);
  }
}
