// Car model binding: glTF nodes `body`, `wheel_fl/fr/rl/rr`, `steering_wheel`, `flap_*` (wind-shaken inflatables),
// `cam_driver`, `cam_hood` (CONTRACTS §3). Poses the model from VehicleState.
//
// Frames: ENU world -> three (X=x, Y=z, Z=-y); body (x fwd, y left, z up) ->
// glTF model (+Z nose, +Y up, +X left).
import * as THREE from 'three';
import type { Vec3, VehicleState } from './physics-types';

/** Road-wheel angle -> steering-wheel angle. 2.9 turns lock to lock over ±0.58 rad. */
export const STEER_RATIO = (2.9 / 2) * 2 * Math.PI / 0.58;
const TYRE_R = 0.316;

export interface CarRigOptions {
  /** Radius of this model's wheel meshes, m (models.json `tyre_radius_m`). Default 0.316 (the Probe). */
  tyreRadius?: number;
  /** Rolling radius the physics uses for this car (spec.wheel.radius), m. Default 0.316. */
  physicsRadius?: number;
  /** Meshes cast shadows (default true; AI cars manage this themselves). */
  castShadow?: boolean;
}

export function enuToThree(p: Vec3 | readonly number[], out = new THREE.Vector3()): THREE.Vector3 {
  return out.set(p[0], p[2], -p[1]);
}

// world(ENU)->three and model->body as quaternions
const Q_T = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().set(
  1, 0, 0, 0,
  0, 0, 1, 0,
  0, -1, 0, 0,
  0, 0, 0, 1));
const Q_M2B = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().set(
  0, 0, 1, 0,
  1, 0, 0, 0,
  0, 1, 0, 0,
  0, 0, 0, 1));

/** Body->world quaternion (ENU, x,y,z,w) to the three.js orientation of the model. */
export function bodyQuatToThree(q: readonly number[], out = new THREE.Quaternion()): THREE.Quaternion {
  const qb = _qb.set(q[0], q[1], q[2], q[3]);
  return out.copy(Q_T).multiply(qb).multiply(Q_M2B);
}
const _qb = new THREE.Quaternion();

export function headingToThree(heading: number, out = new THREE.Quaternion()): THREE.Quaternion {
  return bodyQuatToThree([0, 0, Math.sin(heading / 2), Math.cos(heading / 2)], out);
}

interface WheelBind { pivot: THREE.Object3D; mesh: THREE.Object3D; base: THREE.Quaternion; rest: THREE.Vector3; spinSign: number }

const WHEEL_NAMES = ['wheel_fl', 'wheel_fr', 'wheel_rl', 'wheel_rr'] as const;
const _v = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _qs = new THREE.Quaternion();
const _qr = new THREE.Quaternion();
/** Wind-shaken inflatables (`flap_*` nodes, origin at the tie-down): steady lean-back up to FLAP_LEAN rad at
 *  FLAP_SPEED m/s (grows with speed squared, like drag) plus a flutter of FLAP_FLUTTER_MIN..MAX rad whose
 *  frequency also rises with speed (owner, 17 Oct 2026: "shake in the wind, increasing with speed"). */
export const FLAP_SPEED = 45;
export const FLAP_LEAN = 0.5;
export const FLAP_FLUTTER_MIN = 0.02;
export const FLAP_FLUTTER_MAX = 0.2;
/** Emissive intensity of a lit brake lamp (the lamp's own colour, under ACES at exposure 1). */
export const BRAKE_GLOW = 2.5;
/** Lamp-disc colours: lit under braking; dim is the resting tail-light red of a model without lamps of its own. */
export const BRAKE_LIT = 0xff2a1a;
export const BRAKE_DIM = 0x5c0c0c;
interface Flap { node: THREE.Object3D; base: THREE.Quaternion; phase: number; gain: number }
function nameHash(s: string): number { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return ((h >>> 0) % 10007) / 10007; }
const X_AXIS = new THREE.Vector3(1, 0, 0);
const Y_AXIS = new THREE.Vector3(0, 1, 0);
const Z_AXIS = new THREE.Vector3(0, 0, 1);

export class CarRig {
  readonly root = new THREE.Group();
  readonly wheels: WheelBind[] = [];
  readonly steeringWheel: THREE.Object3D | null;
  private steeringBase = new THREE.Quaternion();
  readonly camDriver: THREE.Object3D;
  readonly camHood: THREE.Object3D;
  readonly body: THREE.Object3D | null;
  /** Wind-shaken inflatables (`flap_*`), rocked in pose(). */
  readonly flaps: Flap[] = [];
  /** Brake-lamp materials (named `brake` or `car<N>_brake`): lit by setBrakeLights(). */
  private readonly brakeMats: THREE.MeshStandardMaterial[] = [];
  /** Emissive discs at the rear lamps of a model whose lamps are painted (field cars: models.json brake_lamps). */
  private brakeDiscs: THREE.Group | null = null;
  private brakeDiscMat: THREE.MeshBasicMaterial | null = null;
  /** fallback discs: always visible, dim red when off (the model has no tail lamps of its own) */
  private brakeDiscsAlways = false;
  private brakeOn = false;
  /** Model wheel radius, m. */
  readonly tyreRadius: number;
  /** Physics hub → model hub drop (m, along the body up axis) so a smaller / larger wheel still touches the road. */
  private hubDrop: number;
  /** Visual spin per physics spin (physics radius / model radius). */
  private spinScale: number;

  constructor(model: THREE.Object3D, opts: CarRigOptions = {}) {
    this.tyreRadius = opts.tyreRadius && opts.tyreRadius > 0 ? opts.tyreRadius : TYRE_R;
    const physR = opts.physicsRadius && opts.physicsRadius > 0 ? opts.physicsRadius : TYRE_R;
    this.hubDrop = physR - this.tyreRadius;
    this.spinScale = physR / this.tyreRadius;
    this.root.add(model);
    this.root.updateMatrixWorld(true);
    const find = (name: string) => model.getObjectByName(name) ?? null;
    this.body = find('body');
    const inv = new THREE.Matrix4().copy(this.root.matrixWorld).invert();
    for (const name of WHEEL_NAMES) {
      const mesh = find(name);
      const pivot = new THREE.Object3D();
      pivot.name = name + '_pivot';
      if (!mesh) {
        console.warn(`car model is missing node ${name}`);
        this.wheels.push({ pivot, mesh: new THREE.Object3D(), base: new THREE.Quaternion(), rest: new THREE.Vector3(), spinSign: 1 });
        continue;
      }
      const rel = new THREE.Matrix4().multiplyMatrices(inv, mesh.matrixWorld);
      const pos = new THREE.Vector3(), quat = new THREE.Quaternion(), scl = new THREE.Vector3();
      rel.decompose(pos, quat, scl);
      mesh.removeFromParent();
      pivot.position.copy(pos);
      mesh.position.set(0, 0, 0);
      mesh.quaternion.copy(quat);
      mesh.scale.copy(scl);
      pivot.add(mesh);
      this.root.add(pivot);
      const axis = X_AXIS.clone().applyQuaternion(quat);
      this.wheels.push({ pivot, mesh, base: quat.clone(), rest: pos.clone(), spinSign: axis.x >= 0 ? 1 : -1 });
    }
    this.steeringWheel = find('steering_wheel');
    if (this.steeringWheel) this.steeringBase.copy(this.steeringWheel.quaternion);
    this.camDriver = find('cam_driver') ?? this.makeEmpty('cam_driver', 0.37, 1.13, -0.4);
    this.camHood = find('cam_hood') ?? this.makeEmpty('cam_hood', 0, 1.08, 0.7);
    const cast = opts.castShadow ?? true;
    model.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) { o.castShadow = cast; o.receiveShadow = false; }
      if (o.name.startsWith('flap_')) { const h = nameHash(o.name); this.flaps.push({ node: o, base: o.quaternion.clone(), phase: h * Math.PI * 2, gain: 0.85 + 0.3 * ((h * 7.31) % 1) }); }
      const mm = (o as THREE.Mesh).material;
      for (const m of Array.isArray(mm) ? mm : mm ? [mm] : []) {
        const sm = m as THREE.MeshStandardMaterial;
        if (sm.isMeshStandardMaterial && /(^|_)brake$/.test(sm.name) && !this.brakeMats.includes(sm)) {
          sm.emissive.setHex(0x000000); sm.emissiveIntensity = 0;   // off until setBrakeLights(true)
          this.brakeMats.push(sm);
        }
      }
    });
  }

  /**
   * Add lit-lamp discs at rear lamp centres given in the model's frame ([x, y, z, r], +z forward): one small unlit red
   * disc per lamp just behind the lens, facing the tail, hidden until setBrakeLights(true).
   */
  addBrakeLamps(lamps: readonly (readonly number[])[], opts: { alwaysOn?: boolean } = {}): void {
    if (!lamps.length) return;
    const g = this.brakeDiscs ?? (this.brakeDiscs = new THREE.Group());
    g.name = 'brake_lamps';
    this.brakeDiscsAlways = !!opts.alwaysOn;
    const mat = this.brakeDiscMat ?? (this.brakeDiscMat = new THREE.MeshBasicMaterial({ color: this.brakeDiscsAlways ? BRAKE_DIM : BRAKE_LIT, toneMapped: false }));
    for (const [x, y, z, r] of lamps) {
      const m = new THREE.Mesh(new THREE.CircleGeometry(Math.max(0.025, (r ?? 0.05) * 0.9), 12), mat);
      m.position.set(x, y, z - 0.012);
      m.rotation.y = Math.PI;   // face the tail (-z)
      m.castShadow = false; m.receiveShadow = false;
      g.add(m);
    }
    g.visible = this.brakeOn || this.brakeDiscsAlways;
    this.root.add(g);
  }

  /** Light the brake lamps (emissive material and/or lamp discs) while braking; cheap to call every frame. */
  setBrakeLights(on: boolean): void {
    if (on === this.brakeOn) return;
    this.brakeOn = on;
    for (const m of this.brakeMats) { m.emissive.setHex(on ? 0xff2a1a : 0x000000); m.emissiveIntensity = on ? BRAKE_GLOW : 0; }
    if (this.brakeDiscs) {
      if (this.brakeDiscsAlways) this.brakeDiscMat!.color.setHex(on ? BRAKE_LIT : BRAKE_DIM);
      else this.brakeDiscs.visible = on;
    }
  }

  /** Rock the inflatables for this speed (m/s) at time t (s): lean back with speed squared, flutter with its own
   *  phase per node so they never move in unison. Visual only; nothing reads it back. */
  shakeFlaps(speed: number, t: number): void {
    if (!this.flaps.length) return;
    const q = Math.min(1, Math.abs(speed) / FLAP_SPEED);
    const lean = -FLAP_LEAN * q * q;
    const amp = FLAP_FLUTTER_MIN + (FLAP_FLUTTER_MAX - FLAP_FLUTTER_MIN) * q;
    const f1 = 2.2 + 3.5 * q, f2 = 6.5 + 7 * q;
    for (const f of this.flaps) {
      const w1 = 2 * Math.PI * f1 * f.gain * t + f.phase, w2 = 2 * Math.PI * f2 * f.gain * t + 1.7 * f.phase;
      const pitch = lean + amp * (Math.sin(w1) + 0.45 * Math.sin(w2));
      const roll = 0.6 * amp * Math.sin(0.8 * w1 + 2.3 * f.phase);
      f.node.quaternion.copy(f.base).multiply(_qs.setFromAxisAngle(X_AXIS, pitch)).multiply(_qr.setFromAxisAngle(Z_AXIS, roll));
    }
  }

  private makeEmpty(name: string, x: number, y: number, z: number): THREE.Object3D {
    console.warn(`car model is missing node ${name}; using a default`);
    const o = new THREE.Object3D(); o.name = name; o.position.set(x, y, z); this.root.add(o); return o;
  }

  /** Full pose from the physics state. */
  pose(st: VehicleState): void {
    enuToThree(st.pos, this.root.position);
    bodyQuatToThree(st.quat, this.root.quaternion);
    this.root.updateMatrixWorld(true);
    for (let k = 0; k < 4; k++) {
      const w = this.wheels[k], ws = st.wheels[k];
      this.root.worldToLocal(enuToThree(ws.pos, w.pivot.position));
      if (this.hubDrop !== 0) w.pivot.position.y -= this.hubDrop;
      w.pivot.quaternion.setFromAxisAngle(Y_AXIS, ws.steer);
      w.mesh.quaternion.copy(w.base).multiply(_qs.setFromAxisAngle(X_AXIS, w.spinSign * ws.spinAngle * this.spinScale));
    }
    const roadSteer = (st.wheels[0].steer + st.wheels[1].steer) / 2;
    this.setSteeringWheel(roadSteer);
    if (this.flaps.length) this.shakeFlaps(st.speed, (typeof performance !== 'undefined' ? performance.now() : Date.now()) / 1000);
  }

  /** Simple pose for ghosts: position, heading, wheels at rest spinning with distance. */
  poseSimple(pos: Vec3, heading: number, distance: number): void {
    enuToThree(pos, this.root.position);
    headingToThree(heading, this.root.quaternion);
    const spin = distance / this.tyreRadius;
    for (const w of this.wheels) {
      w.pivot.position.copy(w.rest);
      w.pivot.quaternion.identity();
      w.mesh.quaternion.copy(w.base).multiply(_qs.setFromAxisAngle(X_AXIS, w.spinSign * spin));
    }
  }

  setSteeringWheel(roadWheelAngle: number): void {
    if (!this.steeringWheel) return;
    this.steeringWheel.quaternion.copy(this.steeringBase).multiply(_q.setFromAxisAngle(Z_AXIS, roadWheelAngle * STEER_RATIO));
  }
}

/** Fallback car: box body, cylinder wheels, torus steering wheel; same node names as probe.glb. */
export function buildFallbackCar(): THREE.Object3D {
  const scene = new THREE.Group();
  scene.name = 'fallback_car';
  const paint = new THREE.MeshStandardMaterial({ color: 0xd8d8d2, roughness: 0.45, metalness: 0.1 });
  const stripe = new THREE.MeshStandardMaterial({ color: 0xc8102e, roughness: 0.5 });
  const glass = new THREE.MeshStandardMaterial({ color: 0x1a2430, roughness: 0.1, metalness: 0.3 });
  const tyre = new THREE.MeshStandardMaterial({ color: 0x1b1b1b, roughness: 0.9 });
  const rim = new THREE.MeshStandardMaterial({ color: 0xb0b0b0, roughness: 0.4, metalness: 0.6 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.7 });

  const body = new THREE.Group(); body.name = 'body';
  const lower = new THREE.Mesh(new THREE.BoxGeometry(1.72, 0.62, 4.5), paint);
  lower.position.set(0, 0.6, 0);
  const cabin = new THREE.Mesh(new THREE.BoxGeometry(1.46, 0.4, 1.9), glass);
  cabin.position.set(0, 1.1, -0.45);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.04, 1.4), paint);
  roof.position.set(0, 1.32, -0.55);
  const nose = new THREE.Mesh(new THREE.BoxGeometry(1.74, 0.08, 0.3), stripe);
  nose.position.set(0, 0.75, 2.12);
  const wing = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.04, 0.3), dark);
  wing.position.set(0, 1.12, -2.1);
  body.add(lower, cabin, roof, nose, wing);
  scene.add(body);

  const tyreGeo = new THREE.CylinderGeometry(TYRE_R, TYRE_R, 0.225, 24);
  tyreGeo.rotateZ(Math.PI / 2); // axle along X
  const spokeGeo = new THREE.BoxGeometry(0.235, 0.36, 0.06);
  for (const [name, x, z] of [['wheel_fl', 0.757, 1.307], ['wheel_fr', -0.757, 1.307], ['wheel_rl', 0.757, -1.307], ['wheel_rr', -0.757, -1.307]] as const) {
    const w = new THREE.Mesh(tyreGeo, tyre); w.name = name;
    w.position.set(x, TYRE_R, z);
    const spoke = new THREE.Mesh(spokeGeo, rim);
    w.add(spoke);
    scene.add(w);
  }

  const sw = new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.018, 8, 32), dark);
  sw.name = 'steering_wheel';
  sw.position.set(0.37, 0.9, 0.05);
  sw.quaternion.setFromUnitVectors(Z_AXIS, new THREE.Vector3(0, 0.45, -1).normalize());
  const swSpoke = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.03, 0.02), rim);
  const swTop = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.05, 0.02), stripe);
  swTop.position.set(0, 0.18, 0);
  sw.add(swSpoke, swTop);
  scene.add(sw);
  // dash so the driver view has a reference
  const dash = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.12, 0.3), dark);
  dash.position.set(0, 0.95, 0.38);
  scene.add(dash);

  const camDriver = new THREE.Object3D(); camDriver.name = 'cam_driver'; camDriver.position.set(0.37, 1.18, -0.5);
  const camHood = new THREE.Object3D(); camHood.name = 'cam_hood'; camHood.position.set(0, 1.12, 0.7);
  scene.add(camDriver, camHood);
  return scene;
}
