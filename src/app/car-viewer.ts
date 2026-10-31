// The Cars page (owner, 31 Oct 2026): one field car at a time on a stage, with a card, an orbit camera and its engine.
//
// The page is reached from the main menu's Cars row. The main menu stays open underneath (hidden by a class), so the
// pad / key navigation keeps flowing as NavEvents and Back returns to the same row. The scene is the game's own
// (world.scene, Look, the chase camera object): the track and the player's car are hidden for the studio stage, the
// player's car and the ghosts for the track stage. Models come through loadFieldModel and prepareCarMaterials, as the
// race loads them; one at a time, the neighbours prefetched, what is paged away freed (only what this page loaded).
import * as THREE from 'three';
import { CarRig } from './car';
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
  SETTLE_END, cardFor, creditFor, engineAt, fieldSize, indexByNumber, nextBlip, safeUrl, viewerOrder,
  type AwardEntry, type Card, type CreditRow, type IdentityRow, type PhotoRow, type ViewerCar,
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
  private lastInputAt = -Infinity;
  private pointers = new Map<number, { x: number; y: number }>();
  private pinch = 0;
  private lastT = 0;
  // models this page parsed itself (freed when paged away)
  private owned = new Map<string, THREE.Object3D>();
  // sound
  private fa: FieldAudio | null = null;
  private engine: { id: number; t0: number; idle: number; family: string; snd: { trim: number; muffler: number; rpmScale: number }; redline: number; blips: number[]; nextAt: number } | null = null;
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
    this.root.append(top, prev, next, this.card, this.loadingEl, this.typedEl, this.hintEl);
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
    void d.audio.start();
    setTimeout(() => { if (this.opened && d.audio.suspended) d.toast('Press any key or tap the screen for sound', 5000); }, 700);
    d.audio.hush();
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
      identity, cars, skipped, total: fieldSize(identity), models, photos: photos ?? {}, credits: credits?.cars ?? {},
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

  private getTemplate(key: string): Promise<THREE.Object3D | null> {
    if (key === PROBE_KEY && !this.modelFile(key)) return Promise.resolve(this.d.probeModel);
    const m = this.modelFile(key);
    if (!m) return Promise.resolve(null);
    if (!this.owned.has(m.file) && !fieldModelCached(m.file)) {
      return loadFieldModel(m.file).then((t) => { if (t) this.owned.set(m.file, t); return t; });
    }
    return loadFieldModel(m.file);
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
    this.renderCard(cardFor(car, i, data.cars.length, data.total, creditFor(data.credits, car.key), data.photos[car.key]));
    this.getTemplate(car.key).then((tpl) => {
      if (my !== this.token || !this.opened) return;
      if (!tpl) { this.loadingEl.textContent = 'This model did not load.'; return; }
      this.buildRig(car, tpl);
      this.loadingEl.classList.add('hidden');
      void this.startEngine(car, my);
    }).catch(() => { if (my === this.token) this.loadingEl.textContent = 'This model did not load.'; });
    // prefetch the neighbours, free what fell out of the window
    const n = data.cars.length;
    const win = new Set([i, (i + 1) % n, (i - 1 + n) % n].map((k) => data.cars[k].key));
    for (const k of win) if (k !== car.key) void this.getTemplate(k);
    for (const [file, tpl] of [...this.owned]) {
      const keep = [...win].some((k) => this.modelFile(k)?.file === file);
      if (!keep) { this.owned.delete(file); disposeTree(tpl); releaseFieldModel(file); }
    }
  }

  private buildRig(car: ViewerCar, tpl: THREE.Object3D): void {
    const shared = tpl === this.d.probeModel;
    const clone = tpl.clone(true);
    if (!shared) prepareCarMaterials(clone);
    const m = this.modelFile(car.key);
    const r = m?.tyre_radius_m;
    const rig = new CarRig(clone, { tyreRadius: r, physicsRadius: r, castShadow: this.d.shadows });
    const p = this.d.parking();
    rig.poseSimple(p.pos, p.heading, 0);
    if (m?.brake_lamps?.length) rig.addBrakeLamps(m.brake_lamps, { alwaysOn: !!m.brake_lamps_fallback });
    this.group.add(rig.root);
    rig.root.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(rig.root);
    const size = box.getSize(new THREE.Vector3());
    this.targetY = Math.max(0.45, Math.min(1.1, size.y * 0.45));
    this.baseDist = Math.max(5.2, Math.min(10, Math.max(size.x, size.z, size.y * 2.2) * 1.55));
    this.rig = { rig, key: car.key, shared, tpl };
  }

  private dropRig(): void {
    const r = this.rig;
    if (!r) return;
    this.rig = null;
    r.rig.root.removeFromParent();
    if (r.shared) return;
    const base = r.tpl ? materialsOf(r.tpl) : new Set<THREE.Material>();
    for (const m of materialsOf(r.rig.root)) if (!base.has(m)) disposeMaterial(m, false); // the clone's own (upgraded paint, glass)
  }

  private freeAll(): void {
    for (const [file, tpl] of this.owned) { disposeTree(tpl); releaseFieldModel(file); }
    this.owned.clear();
  }

  // ------------------------------------------------------------ card

  private renderCard(c: Card): void {
    const k = this.card;
    const num = el('div', 'cv-num', `#${c.number}`);
    const team = el('div', 'cv-team', c.team);
    const car = el('div', 'cv-car', c.car + (c.cls ? `  ·  Class ${c.cls}` : ''));
    const parts: Node[] = [num, team, car];
    if (c.awards.length) {
      const aw = el('div', 'cv-awards');
      for (const a of c.awards) aw.append(el('span', 'cv-award', a));
      parts.push(aw);
    }
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
    this.posEl.textContent = c.position;
  }

  // ------------------------------------------------------------ sound

  private async startEngine(car: ViewerCar, token: number): Promise<void> {
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
      this.engine = { id: token, t0: performance.now() / 1000, idle: (fam?.idle ?? 800) / snd.rpmScale, family: snd.family, snd, redline, blips: [], nextAt: SETTLE_END + nextBlip(0, Math.random()) };
    } catch (e) { console.warn('cars page: engine sound', e); }
  }

  private stopEngine(now: boolean): void {
    this.engine = null;
    if (this.fa) this.fa.update({ pos: [-3, 0, 0], vel: [0, 0, 0] }, []);
    if (now) this.d.audio.hush();
  }

  private tickEngine(): void {
    const e = this.engine, fa = this.fa;
    if (!e || !fa) return;
    const t = performance.now() / 1000 - e.t0;
    if (t > e.nextAt) { e.blips.push(e.nextAt); if (e.blips.length > 3) e.blips.shift(); e.nextAt = nextBlip(e.nextAt, Math.random()); }
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
    const dist = Math.max(2.2, Math.min(22, this.baseDist * this.zoom));
    const elMin = Math.asin(Math.max(-1, Math.min(1, (0.3 - this.targetY) / dist)));
    this.el = Math.max(elMin, Math.min(1.35, this.el));
    const cam = d.cams.camera;
    if (cam.fov !== FOV || cam.far !== 4000) { cam.fov = FOV; cam.near = 0.05; cam.far = 4000; cam.updateProjectionMatrix(); }
    const c = this.stagePos;
    const ce = Math.cos(this.el);
    cam.position.set(c.x + dist * Math.sin(this.az) * ce, c.y + this.targetY + dist * Math.sin(this.el), c.z + dist * Math.cos(this.az) * ce);
    cam.lookAt(c.x, c.y + this.targetY, c.z);
    d.world.follow(this.rig?.rig.root.position ?? c, cam);
    this.tickEngine();
    if (!document.hidden) d.look.render(dt, 0);
  }
}
