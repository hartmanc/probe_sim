// Chase / hood / driver cameras. C or gamepad Y cycles.
//
// Field of view: each camera has a HORIZONTAL field of view; the vertical one follows the aspect ratio
// (verticalFov), capped at 1.05× its 16:9 value so a near-square window or a portrait-ish layout does not fill
// the frame with headliner and dash. The driver camera sits at the glb's cam_driver plus the player's seat
// offsets (Driver view menu: eye height, seat fore/aft, field of view; persisted in localStorage).
//
// Look-around (input.ts lookX / lookY / lookBack): driver and hood yaw up to ±120° and pitch ±25° about the car's
// axes; the chase camera orbits the car (±180°, elevation). Moving out follows the stick quickly; letting go
// springs back, rate limited. Look back snaps to 180° and back.
import * as THREE from 'three';
import type { CarRig } from './car';

export type CameraMode = 'chase' | 'hood' | 'driver';
export const CAMERA_MODES: CameraMode[] = ['chase', 'hood', 'driver'];

// ---------------------------------------------------------------- field of view

const DEG = Math.PI / 180;
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

/** Horizontal field of view (deg) per camera; the driver's comes from DriverView.fov. */
export const HFOV: Record<Exclude<CameraMode, 'driver'>, number> = { chase: 90, hood: 95 };
/** Vertical cap, relative to the vertical FOV the same horizontal FOV gives at 16:9. */
export const VFOV_CAP = 1.05;
export const VFOV_MIN = 20;

function vfovFor(hfovDeg: number, aspect: number): number {
  return 2 * Math.atan(Math.tan((hfovDeg * DEG) / 2) / Math.max(0.1, aspect)) / DEG;
}
/** Vertical FOV (deg) that keeps the horizontal FOV at hfovDeg, capped for narrow aspect ratios. */
export function verticalFov(hfovDeg: number, aspect: number): number {
  return clamp(vfovFor(hfovDeg, aspect), VFOV_MIN, vfovFor(hfovDeg, 16 / 9) * VFOV_CAP);
}

// ---------------------------------------------------------------- driver view settings

export interface DriverView {
  /** Eye height offset over the glb cam_driver, m (+ up). */
  eyeY: number;
  /** Seat fore/aft offset, m (+ toward the nose). */
  seatZ: number;
  /** Horizontal field of view, deg. */
  fov: number;
}
export const DRIVER_VIEW_DEFAULTS: Readonly<DriverView> = { eyeY: 0.04, seatZ: -0.04, fov: 90 };
export const EYE_RANGE: readonly [number, number] = [-0.10, 0.15];
export const SEAT_RANGE: readonly [number, number] = [-0.15, 0.15];
export const OFFSET_STEP = 0.01;
export const FOV_CHOICES: readonly number[] = [70, 75, 80, 85, 90, 95, 100, 105, 110];

const VIEW_KEY = 'probeSim.camera.v1.driverView';

/** Saved settings, validated and clamped; anything unreadable falls back to the defaults. */
export function parseDriverView(json: string | null): DriverView {
  const d = { ...DRIVER_VIEW_DEFAULTS };
  if (!json) return d;
  try {
    const o = JSON.parse(json) as Record<string, unknown>;
    const n = (v: unknown, def: number, lo: number, hi: number) => (typeof v === 'number' && isFinite(v) ? clamp(v, lo, hi) : def);
    return {
      eyeY: n(o?.eyeY, d.eyeY, EYE_RANGE[0], EYE_RANGE[1]),
      seatZ: n(o?.seatZ, d.seatZ, SEAT_RANGE[0], SEAT_RANGE[1]),
      fov: n(o?.fov, d.fov, FOV_CHOICES[0], FOV_CHOICES[FOV_CHOICES.length - 1]),
    };
  } catch { return d; }
}
export function loadDriverView(): DriverView {
  try { return parseDriverView(window.localStorage.getItem(VIEW_KEY)); } catch { return { ...DRIVER_VIEW_DEFAULTS }; }
}
export function saveDriverView(v: DriverView | null): void {
  try { if (v) window.localStorage.setItem(VIEW_KEY, JSON.stringify(v)); else window.localStorage.removeItem(VIEW_KEY); } catch { /* storage unavailable */ }
}

// ---------------------------------------------------------------- look-around

/** Look limits (rad): driver / hood yaw and pitch; chase orbit yaw and elevation. */
export const LOOK = { yaw: 120 * DEG, pitch: 25 * DEG, orbitYaw: Math.PI, orbitPitch: 25 * DEG };
/** Moving out: exponential follow + rate cap. Springing back: slower, rate limited. */
const LOOK_OUT = { k: 14, rate: 9 };
const LOOK_BACK = { k: 6, rate: 4.5 };

/** One step of a look angle toward its target: quick outward, a rate-limited spring back toward centre. */
export function stepLookAngle(cur: number, target: number, dt: number): number {
  const outward = Math.abs(target) > Math.abs(cur) && Math.sign(target) !== -Math.sign(cur);
  const p = outward ? LOOK_OUT : LOOK_BACK;
  const d = (target - cur) * (1 - Math.exp(-p.k * dt));
  const m = p.rate * dt;
  return cur + clamp(d, -m, m);
}

const _fwd = new THREE.Vector3();
const _up = new THREE.Vector3();
const _p = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _q2 = new THREE.Quaternion();
const _look = new THREE.Vector3();
const _off = new THREE.Vector3();
const FLIP = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI); // camera looks -Z, model nose is +Z
const X = new THREE.Vector3(1, 0, 0);
const Y = new THREE.Vector3(0, 1, 0);

export class CameraRig {
  readonly camera: THREE.PerspectiveCamera;
  mode: CameraMode = 'chase';
  /** Driver seat / FOV (Driver view menu). Change through setDriverView so it is saved. */
  driverView: DriverView = loadDriverView();
  private chasePos = new THREE.Vector3();
  private chaseLook = new THREE.Vector3();
  private initialised = false;
  private lookYaw = 0;           // steer-follow glance (driver)
  private look = { x: 0, y: 0, back: false };
  private yaw = 0; private pitch = 0;  // look-around, rad
  private backSnap = false;

  constructor(aspect: number) {
    this.camera = new THREE.PerspectiveCamera(60, aspect, 0.05, 8000);
    this.applyFov();
  }

  /** Horizontal FOV of the current camera, deg. */
  get hfov(): number { return this.mode === 'driver' ? this.driverView.fov : HFOV[this.mode]; }

  private applyFov(): void {
    const cam = this.camera;
    const fov = verticalFov(this.hfov, cam.aspect);
    const near = this.mode === 'chase' ? 0.1 : 0.03;
    if (Math.abs(cam.fov - fov) > 1e-6 || cam.near !== near) { cam.fov = fov; cam.near = near; cam.updateProjectionMatrix(); }
  }

  setMode(m: CameraMode): void {
    this.mode = m;
    this.applyFov();
    this.initialised = false;
    this.yaw = 0; this.pitch = 0; this.backSnap = false;
  }

  setDriverView(v: Partial<DriverView>): DriverView {
    this.driverView = parseDriverView(JSON.stringify({ ...this.driverView, ...v }));
    saveDriverView(this.driverView);
    this.applyFov();
    return this.driverView;
  }
  resetDriverView(): DriverView {
    this.driverView = { ...DRIVER_VIEW_DEFAULTS };
    saveDriverView(null);
    this.applyFov();
    return this.driverView;
  }

  /** Look-around target from the input: x, y −1..1 (+ left, + up); back = look behind. */
  setLook(x: number, y: number, back: boolean): void {
    this.look.x = clamp(x, -1, 1); this.look.y = clamp(y, -1, 1); this.look.back = back;
  }
  /** Current look angles (rad), for tests and the console. */
  get lookAngles(): { yaw: number; pitch: number } { return { yaw: this.yaw, pitch: this.pitch }; }

  cycle(): CameraMode {
    const i = CAMERA_MODES.indexOf(this.mode);
    this.setMode(CAMERA_MODES[(i + 1) % CAMERA_MODES.length]);
    return this.mode;
  }

  private launchFrom: THREE.Vector3 | null = null;

  /** Space-launch camera: rises after the car from where the camera was, looking at it. null ends it. */
  setLaunched(on: boolean): void {
    this.launchFrom = on ? this.camera.position.clone() : null;
    if (!on) this.initialised = false;
  }

  private stepLook(dt: number): void {
    const chase = this.mode === 'chase';
    const ymax = chase ? LOOK.orbitYaw : LOOK.yaw, pmax = chase ? LOOK.orbitPitch : LOOK.pitch;
    if (this.look.back) {
      this.yaw = Math.PI; this.pitch = 0; this.backSnap = true; // snap: a mirror-like glance behind
      return;
    }
    if (this.backSnap) { this.backSnap = false; this.yaw = this.look.x * ymax; this.pitch = this.look.y * pmax; return; }
    this.yaw = stepLookAngle(this.yaw, this.look.x * ymax, dt);
    this.pitch = stepLookAngle(this.pitch, this.look.y * pmax, dt);
  }

  /** steer: driver input -1..1 (+left); speed m/s. */
  update(rig: CarRig, dt: number, steer: number, speed: number): void {
    const cam = this.camera;
    this.applyFov();
    rig.root.updateMatrixWorld(true);
    if (this.launchFrom) {
      // follow the car up: stay level with it at a widening distance, look at it
      const car = rig.root.position;
      const off = _look.copy(this.launchFrom).sub(car);
      off.y = 0;
      if (off.lengthSq() < 1) off.set(6, 0, 0);
      const climb = Math.max(0, car.y - this.launchFrom.y);
      off.setLength(8 + climb * 0.12);
      const target = _p.copy(car).add(off).add(_up.set(0, -2 - climb * 0.05, 0));
      cam.position.lerp(target, 1 - Math.exp(-dt * 4));
      cam.lookAt(car);
      return;
    }
    this.stepLook(dt);
    _fwd.set(0, 0, 1).applyQuaternion(rig.root.quaternion);
    if (this.mode === 'chase') {
      // spring arm behind and above, using flattened heading so pitch doesn't swing the camera
      const flat = _p.set(_fwd.x, 0, _fwd.z);
      if (flat.lengthSq() < 1e-6) flat.set(0, 0, 1);
      flat.normalize();
      const dist = 6.2 + Math.min(Math.abs(speed), 50) * 0.03;
      const target = new THREE.Vector3().copy(rig.root.position).addScaledVector(flat, -dist).add(_up.set(0, 2.1, 0));
      const look = new THREE.Vector3().copy(rig.root.position).addScaledVector(flat, 7 + Math.abs(speed) * 0.1).add(_up.set(0, 0.9, 0));
      if (!this.initialised) { this.chasePos.copy(target); this.chaseLook.copy(look); this.initialised = true; }
      const kp = 1 - Math.exp(-dt * 7);
      const kl = 1 - Math.exp(-dt * 12);
      this.chasePos.lerp(target, kp);
      this.chaseLook.lerp(look, kl);
      // keep the arm length roughly constant even while lagging
      const car = rig.root.position;
      const off = _look.copy(this.chasePos).sub(car);
      const h = off.y; off.y = 0;
      const len = off.length();
      if (len > 1e-3) { off.multiplyScalar(Math.min(Math.max(len, dist * 0.8), dist * 1.25) / len); }
      let y = Math.max(h, 1.2);
      // orbit: swing the arm around the car (yaw) and up / down (elevation), looking at the car as it swings
      const orbit = Math.min(1, Math.abs(this.yaw) / 0.6 + Math.abs(this.pitch) / 0.3);
      if (orbit > 0) {
        off.applyAxisAngle(Y, this.yaw);
        const r = Math.hypot(off.length(), y);
        const el = clamp(Math.atan2(y, off.length()) + this.pitch, 0.06, 1.2);
        off.setLength(r * Math.cos(el)); y = r * Math.sin(el);
      }
      cam.position.set(car.x + off.x, car.y + y, car.z + off.z);
      _p.copy(car).add(_up.set(0, 0.9, 0));
      cam.lookAt(_look.copy(this.chaseLook).lerp(_p, orbit));
      return;
    }
    const driver = this.mode === 'driver';
    const node = driver ? rig.camDriver : rig.camHood;
    node.updateMatrixWorld(true);
    node.getWorldPosition(cam.position);
    node.getWorldQuaternion(_q);
    if (driver) {
      // seat offsets in the model frame (+Y up, +Z nose)
      const v = this.driverView;
      cam.position.add(_off.set(0, v.eyeY, v.seatZ).applyQuaternion(_q));
    }
    // nodes follow the model frame (+Z nose); the camera looks along its -Z
    cam.quaternion.copy(_q).multiply(FLIP);
    let yaw = this.yaw;
    if (driver) {
      const target = steer * 0.22 * Math.min(1, Math.abs(speed) / 8 + 0.3);
      this.lookYaw += (target - this.lookYaw) * (1 - Math.exp(-dt * 5));
      yaw += this.lookYaw * (1 - Math.min(1, Math.abs(this.yaw) / 0.5)); // the steer glance fades while looking around
    }
    cam.quaternion.multiply(_q2.setFromAxisAngle(Y, yaw)).multiply(_q2.setFromAxisAngle(X, this.pitch));
  }

  resize(aspect: number): void {
    this.camera.aspect = aspect;
    this.camera.updateProjectionMatrix();
    this.applyFov();
  }
}
