// Tyre marks, dust and smoke. Any wheel past its grip peak on pavement lays a skid mark (one mesh for every car's
// marks: a ring buffer of quads with per-vertex alpha); a wheel off the pavement kicks up dust and a locked or
// spinning wheel on it makes tyre smoke (one Points cloud: particles are born on the CPU and move in the shader).
import * as THREE from 'three';
import type { VehicleState, WheelState } from './physics-types';

export const MARK_SEGMENTS = 6000;
export const MARK_WIDTH = 0.2;
/** metres between quads along a mark */
export const MARK_STEP = 0.3;
/** combined slip / peak at which a mark starts, and the alpha of a full-strength mark */
export const MARK_USE_ON = 1.05;
export const MARK_ALPHA = 0.55;
export const PARTICLES = 1200;
/** emission (particles / s per wheel) at full rate */
export const DUST_RATE = 28;
export const SMOKE_RATE = 24;
/** emit nothing from cars farther than this from the camera (m) */
export const EMIT_RANGE = 160;

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

/** Pure: mark strength 0..1 for a wheel (0 unloaded or inside the grip peak). */
export function markIntensity(w: Pick<WheelState, 'slipUse' | 'slipRatio' | 'slipAngle' | 'load'>): number {
  if (!(w.load > 400)) return 0;
  const use = w.slipUse ?? Math.max(Math.abs(w.slipRatio) / 0.12, Math.abs(w.slipAngle) / 0.1);
  return clamp((use - MARK_USE_ON) * 2, 0, 1);
}

/** Pure: on pavement? (the track or a paved pit lane / runoff) */
export function onPavement(w: Pick<WheelState, 'onTrack' | 'paved'>): boolean { return w.onTrack || !!w.paved; }

export interface GroundSampler { (x: number, y: number): { z: number } }

interface WheelTrail { x: number; y: number; lx: number; ly: number; rx: number; ry: number; active: boolean; dust: number; smoke: number }

function softDisc(): THREE.Texture {
  const cv = document.createElement('canvas'); cv.width = cv.height = 64;
  const g = cv.getContext('2d')!;
  const gr = g.createRadialGradient(32, 32, 2, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(cv);
  t.minFilter = THREE.LinearFilter;
  return t;
}

export class TrackMarks {
  readonly marks: THREE.Mesh;
  readonly particles: THREE.Points;
  private readonly mPos: THREE.BufferAttribute;
  private readonly mCol: THREE.BufferAttribute;
  private mCount = 0; private mDirty = false;
  private readonly pP0: THREE.BufferAttribute; private readonly pVel: THREE.BufferAttribute;
  private readonly pBorn: THREE.BufferAttribute; private readonly pLife: THREE.BufferAttribute;
  private readonly pSize: THREE.BufferAttribute; private readonly pKind: THREE.BufferAttribute;
  private pCursor = 0; private pDirty = false;
  private readonly pMat: THREE.ShaderMaterial;
  private time = 0;
  private readonly trails = new Map<number, WheelTrail>();
  private readonly camPos = new THREE.Vector3();

  constructor(scene: THREE.Scene, private readonly ground: GroundSampler) {
    // marks
    const mg = new THREE.BufferGeometry();
    this.mPos = new THREE.BufferAttribute(new Float32Array(MARK_SEGMENTS * 4 * 3), 3).setUsage(THREE.DynamicDrawUsage);
    this.mCol = new THREE.BufferAttribute(new Float32Array(MARK_SEGMENTS * 4 * 4), 4).setUsage(THREE.DynamicDrawUsage);
    const idx = new Uint32Array(MARK_SEGMENTS * 6);
    for (let i = 0; i < MARK_SEGMENTS; i++) { const v = i * 4, o = i * 6; idx[o] = v; idx[o + 1] = v + 1; idx[o + 2] = v + 2; idx[o + 3] = v + 1; idx[o + 4] = v + 3; idx[o + 5] = v + 2; }
    mg.setAttribute('position', this.mPos);
    mg.setAttribute('color', this.mCol);
    mg.setIndex(new THREE.BufferAttribute(idx, 1));
    mg.setDrawRange(0, 0);
    this.marks = new THREE.Mesh(mg, new THREE.MeshBasicMaterial({
      color: 0x101010, vertexColors: true, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -16,
    }));
    this.marks.frustumCulled = false;
    this.marks.renderOrder = 1;
    this.marks.name = 'tyre_marks';
    // particles
    const pg = new THREE.BufferGeometry();
    const mk = (n: number) => new THREE.BufferAttribute(new Float32Array(PARTICLES * n), n).setUsage(THREE.DynamicDrawUsage);
    this.pP0 = mk(3); this.pVel = mk(3); this.pBorn = mk(1); this.pLife = mk(1); this.pSize = mk(1); this.pKind = mk(1);
    (this.pBorn.array as Float32Array).fill(-1e9);
    (this.pLife.array as Float32Array).fill(1);
    pg.setAttribute('position', this.pP0);
    pg.setAttribute('vel', this.pVel); pg.setAttribute('born', this.pBorn); pg.setAttribute('life', this.pLife);
    pg.setAttribute('size', this.pSize); pg.setAttribute('kind', this.pKind);
    this.pMat = new THREE.ShaderMaterial({
      uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, {
        uTime: { value: 0 }, uScale: { value: 500 }, uTex: { value: null },
        uDust: { value: new THREE.Color(0xc9b48c).multiplyScalar(0.85) }, uSmoke: { value: new THREE.Color(0xd8d8d8).multiplyScalar(0.9) },
      }]),
      vertexShader: `attribute vec3 vel; attribute float born; attribute float life; attribute float size; attribute float kind;
uniform float uTime; uniform float uScale;
varying float vT; varying float vKind;
#include <fog_pars_vertex>
void main() {
	float age = uTime - born;
	float t = age / life;
	vT = t; vKind = kind;
	float k = (1.0 - exp(-1.6 * max(age, 0.0))) / 1.6;   // drag: the puff slows to a drift
	vec3 p = position + vel * k + vec3(0.0, mix(0.25, 0.9, kind) * age, 0.0);
	vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
	gl_Position = projectionMatrix * mvPosition;
	float s = size * (0.45 + 1.6 * clamp(t, 0.0, 1.0));
	gl_PointSize = (t < 0.0 || t > 1.0) ? 0.0 : s * uScale / max(0.2, -mvPosition.z);
	#include <fog_vertex>
}`,
      fragmentShader: `uniform sampler2D uTex; uniform vec3 uDust; uniform vec3 uSmoke;
varying float vT; varying float vKind;
#include <fog_pars_fragment>
void main() {
	if (vT < 0.0 || vT > 1.0) discard;
	float a = texture2D(uTex, gl_PointCoord).a;
	float fade = smoothstep(0.0, 0.08, vT) * (1.0 - smoothstep(0.45, 1.0, vT));
	gl_FragColor = vec4(mix(uDust, uSmoke, vKind), a * fade * mix(0.4, 0.5, vKind));
	#include <fog_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,
      transparent: true, depthWrite: false, fog: true,
    });
    this.pMat.uniforms.uTex.value = typeof document === 'undefined' ? null : softDisc();
    this.particles = new THREE.Points(pg, this.pMat);
    this.particles.frustumCulled = false;
    this.particles.renderOrder = 2;
    this.particles.name = 'dust';
    scene.add(this.marks, this.particles);
  }

  /** Lay marks and emit dust / smoke for a car's four wheels this frame. `id`: 0 the player, AI cars 1.. */
  car(id: number, st: VehicleState, dt: number): void {
    const near = this.camPos.distanceToSquared(new THREE.Vector3(st.pos[0], st.pos[2], -st.pos[1])) < EMIT_RANGE * EMIT_RANGE;
    for (let k = 0; k < 4; k++) {
      const w = st.wheels[k];
      const key = id * 4 + k;
      let tr = this.trails.get(key);
      if (!tr) { tr = { x: w.pos[0], y: w.pos[1], lx: 0, ly: 0, rx: 0, ry: 0, active: false, dust: 0, smoke: 0 }; this.trails.set(key, tr); }
      const paved = onPavement(w);
      const inten = paved ? markIntensity(w) : 0;
      const dx = w.pos[0] - tr.x, dy = w.pos[1] - tr.y, d = Math.hypot(dx, dy);
      if (inten > 0 && d > 0.02) {
        if (d >= MARK_STEP || !tr.active) {
          if (d > 3) tr.active = false; // teleported (reset / recovery): start a fresh mark
          this.lay(tr, w.pos[0], w.pos[1], dx / d, dy / d, inten);
          tr.x = w.pos[0]; tr.y = w.pos[1];
        }
      } else if (inten <= 0) { tr.active = false; tr.x = w.pos[0]; tr.y = w.pos[1]; }
      if (!near || !(w.load > 200)) continue;
      // dust off the pavement, smoke under a locked / spinning wheel
      const speed = st.speed;
      if (!paved && speed > 3) {
        tr.dust += dt * DUST_RATE * clamp(speed / 25, 0.15, 1);
        while (tr.dust >= 1) { tr.dust -= 1; this.emit(w, st, 0, 0.9 + Math.random() * 1.0, 1.4 + Math.random() * 1.2); }
      } else tr.dust = 0;
      const spin = Math.abs(w.slipRatio) > 0.25 && inten > 0.2;
      if (paved && spin && speed > 1) {
        tr.smoke += dt * SMOKE_RATE * clamp(inten * 1.5, 0.3, 1);
        while (tr.smoke >= 1) { tr.smoke -= 1; this.emit(w, st, 1, 0.5 + Math.random() * 0.6, 1.0 + Math.random() * 0.8); }
      } else tr.smoke = 0;
    }
  }

  private lay(tr: WheelTrail, x: number, y: number, tx: number, ty: number, inten: number): void {
    const px = -ty * MARK_WIDTH / 2, py = tx * MARK_WIDTH / 2;
    const lx = x + px, ly = y + py, rx = x - px, ry = y - py;
    if (tr.active) {
      const i = this.mCount % MARK_SEGMENTS, v = i * 4;
      const P = this.mPos.array as Float32Array, C = this.mCol.array as Float32Array;
      const put = (n: number, ex: number, ey: number) => { const z = this.ground(ex, ey).z + 0.02; P[(v + n) * 3] = ex; P[(v + n) * 3 + 1] = z; P[(v + n) * 3 + 2] = -ey; };
      put(0, tr.lx, tr.ly); put(1, tr.rx, tr.ry); put(2, lx, ly); put(3, rx, ry);
      const a = inten * MARK_ALPHA;
      for (let n = 0; n < 4; n++) { C[(v + n) * 4] = 1; C[(v + n) * 4 + 1] = 1; C[(v + n) * 4 + 2] = 1; C[(v + n) * 4 + 3] = a; }
      this.mCount++; this.mDirty = true;
    }
    tr.lx = lx; tr.ly = ly; tr.rx = rx; tr.ry = ry; tr.active = true;
  }

  private emit(w: WheelState, st: VehicleState, kind: 0 | 1, size: number, life: number): void {
    const i = this.pCursor; this.pCursor = (this.pCursor + 1) % PARTICLES;
    const z = this.ground(w.pos[0], w.pos[1]).z;
    const j = Math.random() * 0.3 - 0.15;
    (this.pP0.array as Float32Array).set([w.pos[0] + j, z + 0.15, -(w.pos[1] + j)], i * 3);
    // part of the car's velocity (the puff trails the wheel), a little sideways scatter, more lift for smoke
    const f = kind === 0 ? 0.35 : 0.2;
    const vx = st.vel[0] * f + (Math.random() - 0.5) * 1.6, vy = st.vel[1] * f + (Math.random() - 0.5) * 1.6, vz = 0.6 + Math.random() * (kind === 0 ? 0.8 : 1.2);
    (this.pVel.array as Float32Array).set([vx, vz, -vy], i * 3);
    (this.pBorn.array as Float32Array)[i] = this.time;
    (this.pLife.array as Float32Array)[i] = life;
    (this.pSize.array as Float32Array)[i] = size;
    (this.pKind.array as Float32Array)[i] = kind;
    this.pDirty = true;
  }

  /** Per frame: advance time, size the sprites for this camera / canvas height (px), upload what changed. */
  update(dt: number, camera: THREE.PerspectiveCamera, heightPx: number): void {
    this.time += dt;
    this.camPos.copy(camera.position);
    this.pMat.uniforms.uTime.value = this.time;
    this.pMat.uniforms.uScale.value = (heightPx / 2) / Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    if (this.mDirty) {
      this.mPos.needsUpdate = true; this.mCol.needsUpdate = true;
      this.marks.geometry.setDrawRange(0, Math.min(this.mCount, MARK_SEGMENTS) * 6);
      this.mDirty = false;
    }
    if (this.pDirty) {
      for (const a of [this.pP0, this.pVel, this.pBorn, this.pLife, this.pSize, this.pKind]) a.needsUpdate = true;
      this.pDirty = false;
    }
  }

  /** Marks laid so far (tests). */
  get segments(): number { return Math.min(this.mCount, MARK_SEGMENTS); }

  dispose(): void {
    this.marks.removeFromParent(); this.particles.removeFromParent();
    this.marks.geometry.dispose(); (this.marks.material as THREE.Material).dispose();
    this.particles.geometry.dispose(); this.pMat.dispose();
  }
}
