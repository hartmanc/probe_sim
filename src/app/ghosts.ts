// Ghost laps from ghosts.json: semi-transparent tinted clones of the car,
// placed on the racing line at the s where t(s) equals the current lap time.
import * as THREE from 'three';
import type { GhostLap, GhostsJson, PhysicsApi, TrackJson } from './physics-types';
import { CarRig } from './car';
import { curvatures } from './trackmath';

const TINTS = [0x37c8ff, 0xffb020, 0x7cff6b, 0xff5fd2, 0xb58cff, 0xff6b4a, 0x4affd0];

/** Time and speed at distance s for a ghost lap (linear interpolation on the s grid). */
export class GhostTrace {
  constructor(readonly lap: GhostLap, readonly grid: number, readonly length: number) {}

  tAt(s: number): number {
    const t = this.lap.t, u = s / this.grid;
    const i = Math.floor(u);
    if (i >= t.length - 1) {
      const last = t[t.length - 1], sLast = (t.length - 1) * this.grid;
      return last + (this.lap.lap_time_s - last) * Math.min(1, (s - sLast) / Math.max(1e-6, this.length - sLast));
    }
    return t[i] + (t[i + 1] - t[i]) * (u - i);
  }

  vAt(s: number): number {
    const v = this.lap.v_mps, u = s / this.grid;
    const i = Math.min(Math.floor(u), v.length - 1), j = Math.min(i + 1, v.length - 1);
    return v[i] + (v[j] - v[i]) * (u - i);
  }

  /** s at lap time τ (binary search; clamps to the finish line). */
  sAt(tau: number): number {
    const t = this.lap.t;
    if (tau <= 0) return 0;
    const last = t[t.length - 1];
    if (tau >= last) {
      const sLast = (t.length - 1) * this.grid;
      const f = Math.min(1, (tau - last) / Math.max(1e-6, this.lap.lap_time_s - last));
      return sLast + (this.length - sLast) * f;
    }
    let lo = 0, hi = t.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (t[mid] <= tau) lo = mid; else hi = mid; }
    return (lo + (tau - t[lo]) / Math.max(1e-9, t[hi] - t[lo])) * this.grid;
  }
}

export function makeOffsetFn(ghosts: GhostsJson, length: number): (s: number) => number {
  const off = ghosts.line?.offset_m ?? [];
  const g = ghosts.s_grid_m;
  if (off.length === 0) return () => 0;
  return (s: number) => {
    const u = (((s % length) + length) % length) / g;
    const i = Math.floor(u) % off.length, j = (i + 1) % off.length;
    return off[i] + (off[j] - off[i]) * (u - Math.floor(u));
  };
}

/** Speed-profile ghosts for a track without ghosts.json (dev track or missing file). */
export function synthesizeGhosts(track: TrackJson): GhostsJson {
  const grid = 2;
  const m = Math.floor(track.length_m / grid);
  const kap = curvatures(track, 8);
  const kAt = (s: number) => kap[Math.min(track.n - 1, Math.floor(s / track.spacing_m))];
  const make = (id: string, driver: string, kind: string, mu: number, accel: number, decel: number): GhostLap => {
    const vmax = new Float64Array(m);
    for (let i = 0; i < m; i++) vmax[i] = Math.min(58, Math.sqrt(mu * 9.81 / Math.max(1e-4, Math.abs(kAt(i * grid)))));
    const v = Float64Array.from(vmax);
    for (let pass = 0; pass < 2; pass++) {
      for (let i = 1; i < 2 * m; i++) { // forward: acceleration limit (falls with speed)
        const a = i % m, b = (i - 1) % m;
        const acc = accel * Math.max(0.15, 1 - v[b] / 62);
        v[a] = Math.min(v[a], Math.sqrt(v[b] * v[b] + 2 * acc * grid));
      }
      for (let i = 2 * m - 2; i >= 0; i--) { // backward: braking limit
        const a = i % m, b = (i + 1) % m;
        v[a] = Math.min(v[a], Math.sqrt(v[b] * v[b] + 2 * decel * grid));
      }
    }
    const t: number[] = [0];
    for (let i = 1; i < m; i++) t.push(t[i - 1] + 2 * grid / (v[i] + v[i - 1]));
    const lapTime = t[m - 1] + 2 * (track.length_m - (m - 1) * grid) / (v[m - 1] + v[0]);
    const mm = Math.floor(lapTime / 60), ss = (lapTime - mm * 60).toFixed(2).padStart(5, '0');
    return {
      id, driver, kind, lap_time_s: lapTime, t, v_mps: Array.from(v),
      label: `${driver} ${mm}:${ss}`,
    };
  };
  return {
    track: track.name,
    s_grid_m: grid,
    line: { offset_m: new Array(m).fill(0) },
    laps: [
      make('synthetic_optimal', 'Optimal', 'optimal', 1.05, 4.2, 9.5),
      make('synthetic_driver', 'Dev Driver', 'real', 0.92, 3.6, 8.0),
      make('synthetic_slow', 'Cautious', 'real', 0.8, 3.0, 6.5),
    ],
  };
}

function labelSprite(text: string, color: number): THREE.Sprite {
  const cv = document.createElement('canvas');
  cv.width = 512; cv.height = 96;
  const g = cv.getContext('2d')!;
  g.font = '600 52px system-ui, -apple-system, Segoe UI, sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  const w = Math.min(500, g.measureText(text).width + 40);
  g.fillStyle = 'rgba(10,12,16,0.65)';
  g.beginPath(); g.roundRect((512 - w) / 2, 6, w, 84, 18); g.fill();
  g.fillStyle = '#' + color.toString(16).padStart(6, '0');
  g.fillText(text, 256, 50);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
  sp.scale.set(3.2, 0.6, 1);
  sp.position.set(0, 2.2, 0);
  return sp;
}

export interface Ghost {
  lap: GhostLap;
  trace: GhostTrace;
  rig: CarRig;
  color: number;
  visible: boolean;
}

export class GhostManager {
  readonly ghosts: Ghost[] = [];
  readonly group = new THREE.Group();
  private offset: (s: number) => number;
  private _p = new THREE.Vector3();

  constructor(private physics: PhysicsApi, private track: TrackJson, readonly data: GhostsJson, template: THREE.Object3D) {
    this.offset = makeOffsetFn(data, track.length_m);
    const fastestReal = this.fastestReal();
    data.laps.forEach((lap, k) => {
      const color = TINTS[k % TINTS.length];
      const model = template.clone(true);
      const tint = new THREE.Color(color);
      const cache = new Map<THREE.Material, THREE.Material>();
      model.traverse((o) => {
        const mesh = o as THREE.Mesh;
        if (!mesh.isMesh) return;
        const conv = (mat: THREE.Material) => {
          let c = cache.get(mat);
          if (!c) {
            c = mat.clone();
            c.transparent = true; c.opacity = 0.35; c.depthWrite = false;
            const anyc = c as THREE.MeshStandardMaterial;
            if (anyc.color) anyc.color.lerp(tint, 0.65);
            if (anyc.emissive) anyc.emissive.copy(tint).multiplyScalar(0.25);
            cache.set(mat, c);
          }
          return c;
        };
        mesh.material = Array.isArray(mesh.material) ? mesh.material.map(conv) : conv(mesh.material);
        mesh.castShadow = false;
      });
      const rig = new CarRig(model);
      rig.root.traverse((o) => { o.castShadow = false; });
      rig.root.add(labelSprite(lap.label, color));
      this.group.add(rig.root);
      const visible = lap.kind === 'optimal' || lap === fastestReal;
      rig.root.visible = visible;
      this.ghosts.push({ lap, trace: new GhostTrace(lap, data.s_grid_m, track.length_m), rig, color, visible });
    });
  }

  fastestReal(): GhostLap | null {
    let best: GhostLap | null = null;
    for (const l of this.data.laps) if (l.kind === 'real' && (!best || l.lap_time_s < best.lap_time_s)) best = l;
    return best ?? this.data.laps[0] ?? null;
  }

  setVisible(id: string, on: boolean): void {
    const g = this.ghosts.find((x) => x.lap.id === id);
    if (g) g.visible = on;
  }

  /** Place visible ghosts at lap time τ (null: park on the start line). */
  update(tau: number | null, playerPos: THREE.Vector3): void {
    for (const g of this.ghosts) {
      if (!g.visible) { g.rig.root.visible = false; continue; }
      const s = tau == null ? 0 : g.trace.sAt(tau);
      const w = this.physics.lineToWorld(this.track, this.offset, s % this.track.length_m);
      g.rig.poseSimple(w.pos, w.heading, s);
      // hide when overlapping the player (cockpit views)
      g.rig.root.visible = g.rig.root.position.distanceTo(playerPos) > 3.5;
    }
  }
}
