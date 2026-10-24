// Kerb traversal probe (Oct 2026, the Sonoma rollover): drive the player's Probe over a kerb strip at line speed and
// measure what the kerb does to the car. Used by tools/physics/kerb_sweep.ts and the kerb traversal gate
// (kerbgate.test.ts). Pure physics: no app, no DOM.
import { Vehicle, loadCarSpec, createTrackSurface, loadHeightfield, type Surface, type TrackJson, type PitLaneJson } from '../index';
import { buildAiSpec, buildSpeedProfile, measureCarPerf } from '../ai/field';
import { AiDriver } from '../ai/driver';
import { Traffic } from '../ai/traffic';
import { kerbBandCentre } from '../track';
import { rollOf, ROLLOVER_RAD } from '../rollover';
import { RaceLine } from '../ai/line';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export interface KerbPack { track: TrackJson; scenery: any; surface: Surface; line: RaceLine; heightfield: Float32Array; pitLane: PitLaneJson | null }
export interface TraversalCase {
  kind: 'kerb' | 'sausage'; index: number;
  /** lateral offset from the racing line, m, + toward the strip's side */
  offset: number;
  /** > 0: a crossing path over the band at this angle (deg) instead of the offset line */
  angleDeg: number;
  speedScale?: number;
}
export interface TraversalResult {
  label: string; s0: number; s1: number; v0: number;
  /** ms with any wheel on the raised strip (ground under the hub above the plain road by > 5 mm) */
  onKerbMs: number; maxKerbH: number;
  /** max |roll| relative to the road under the CG (deg), over the run; the same path on the plain road: baseRollDeg */
  maxRollDeg: number; baseRollDeg: number; maxRollRateDeg: number;
  /** ms with a wheel at zero load; kerbLiftMs: ms with a wheel at zero load on the strip or within 0.3 s of leaving it,
   *  that wheel being on the ground at the same point (+-50 ms) of the plain-road run */
  liftMs: number; kerbLiftMs: number; baseLiftMs: number;
  maxLoad: number; hullMs: number;
  /** largest air gap under a wheel lifted by the strip (m, hub height above the ground minus the tyre radius) */
  kerbLiftGap: number;
  /** fastest suspension velocity (m/s, |d compression / dt|) */
  maxWheelVz: number;
  rolledOver: boolean; fail: boolean;
  rows?: string[];
}

const DT = 0.001;

/** A published package (public/<dir>) with the surface the app builds: track, pit lane, paved zones, sausages, kerbs. */
export function loadKerbPack(dir: string): KerbPack {
  const D = fileURLToPath(new URL('../../../public/' + dir.replace(/\/?$/, '/'), import.meta.url));
  const track = JSON.parse(readFileSync(D + 'track.json', 'utf8')) as TrackJson;
  const heightfield = loadHeightfield(Uint8Array.from(readFileSync(D + 'heightfield.bin')).buffer);
  const ghosts = JSON.parse(readFileSync(D + 'ghosts.json', 'utf8'));
  let scenery: any = null;
  try { scenery = JSON.parse(readFileSync(D + 'scenery.json', 'utf8')); } catch { scenery = null; }
  const pit = scenery?.pit_lane ?? null, zones = scenery?.paved_zones ?? null;
  const pitLane = pit || zones ? { spacing_m: 1, fractions: (pit ?? zones).fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] } : null;
  const surface = createTrackSurface(track, heightfield, { pitLane, sausages: scenery?.sausages ?? null, kerbs: scenery?.kerbs ?? null, terrainOverride: scenery?.terrain_override ?? null });
  const line = new RaceLine(track, ghosts);
  if (scenery?.pit_exit_cones?.pts?.length) line.restrictLeft(scenery.pit_exit_cones.pts);
  return { track, scenery, surface, line, heightfield, pitLane };
}

/** The kerb traversal gate's cases: every RAISED strip (kerbs with a profile, sausages) at line speed, line +-1 m. */
export function gateCases(p: KerbPack, offsets: number[] = [-1, 0, 1], angles: number[] = [0]): TraversalCase[] {
  const out: TraversalCase[] = [];
  const k = p.scenery?.kerbs, sa = p.scenery?.sausages;
  const add = (kind: 'kerb' | 'sausage', index: number) => {
    for (const a of angles) for (const o of a > 0 ? [0] : offsets) out.push({ kind, index, offset: o, angleDeg: a });
  };
  if (k?.profile) k.strips.forEach((st: any, i: number) => { if (st.kind !== 'verge') add('kerb', i); });
  if (sa) sa.strips.forEach((_: any, i: number) => add('sausage', i));
  return out;
}
/** Steps after the reset before anything is measured (the car settles on its springs; the strip is >= 100 m ahead). */
const SETTLE = 1500;
/** A wheel airborne this long (steps) after it was last on the strip counts as lifted by it. */
const KERB_WINDOW = 300;

/** Plain road (no kerb humps, no sausages): the reference for kerb height and the road normal. */
const plainCache = new WeakMap<object, Surface>();
function plainOf(p: KerbPack): Surface {
  let s = plainCache.get(p);
  if (!s) { s = createTrackSurface(p.track, p.heightfield, { pitLane: p.pitLane, terrainOverride: p.scenery?.terrain_override ?? null }); plainCache.set(p, s); }
  return s;
}

/** Lateral (+left) of the strip's band centre at s, from the track edges. */
function bandLat(p: KerbPack, kind: 'kerb' | 'sausage', st: any, s: number): number {
  const line = p.line, t = p.track, n = t.n, sp = t.spacing_m || 1;
  const i = ((Math.round(s / sp) % n) + n) % n;
  const e = st.side > 0 ? t.left[i] : t.right[i];
  const edge = Math.hypot(e[0] - line.cx[i], e[1] - line.cy[i]) * st.side;
  let off: number;
  if (kind === 'kerb') off = kerbBandCentre(p.scenery.kerbs, st);
  else { const j = p.scenery.sausages; off = j.kerb_width + j.gap + j.width / 2; }
  return edge + st.side * off;
}

const profCache = new WeakMap<object, Float64Array>();
function lineProfile(p: KerbPack, probe: any): Float64Array {
  let pr = profCache.get(p.line);
  if (!pr) {
    const spec = buildAiSpec(probe, null, 1);
    pr = buildSpeedProfile(p.line, measureCarPerf(spec), spec);
    profCache.set(p.line, pr);
  }
  return pr;
}

interface RunOut { gap: number; roll: number; rollRate: number; lift: Uint8Array; wl: Uint8Array; liftMs: number; onKerbMs: number; maxH: number; maxLoad: number; hullMs: number; maxVz: number; rolled: boolean; kerbRecent: Uint8Array; rows?: string[]; sAt: Float64Array }

function drive(p: KerbPack, surface: Surface, probe: any, c: TraversalCase, sA: number, sB: number, latAt: (s: number) => number, vAt: (s: number) => number, trace: boolean): RunOut {
  const line = p.line, plain = plainOf(p);
  const spec = loadCarSpec(probe);
  const car = new Vehicle(spec, { autoShift: true });
  const pos = new Float64Array(2);
  line.pointAt(sA, latAt(sA), pos);
  { const g = plain.sample(pos[0], pos[1]); car.reset([pos[0], pos[1], g.z], line.headingAt(sA), vAt(sA), [g.nx, g.ny, g.nz]); }
  const inp = { steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false, handbrake: false };
  const W = 2.614;
  const len = Math.round(((sB - sA + line.L) % line.L) / 4) * 4 + 4;
  const maxSteps = Math.round((len / Math.max(5, vAt(sA))) * 2.5 / DT) + 3000;
  const lift = new Uint8Array(maxSteps), wl = new Uint8Array(maxSteps), kerbRecent = new Uint8Array(maxSteps), sAt = new Float64Array(maxSteps);
  const lastK = [-1e9, -1e9, -1e9, -1e9], gapK = [0, 0, 0, 0];
  let hint = -1, lastKerb = -1e9, traveled = 0, sPrev = sA;
  let roll = 0, rollRate = 0, liftMs = 0, onKerbMs = 0, maxH = 0, maxLoad = 0, hullMs = 0, maxVz = 0, rolled = false;
  const hz = new Float64Array(4);
  const rows: string[] | undefined = trace ? ['t,s,lat,v,roll_deg,rollrate_dps,' + [0, 1, 2, 3].map((i) => `h${i},load${i},comp${i}`).join(',') + ',hull'] : undefined;
  const st0 = car.state;
  for (let w = 0; w < 4; w++) hz[w] = st0.wheels[w].compression;
  let step = 0;
  for (; step < maxSteps; step++) {
    const st = car.state;
    const q = st.quat;
    const yaw = Math.atan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] * q[1] + q[2] * q[2]));
    const pr = line.project(st.pos[0], st.pos[1], hint);
    hint = pr.index;
    let ds = pr.s - sPrev; if (ds > line.L / 2) ds -= line.L; else if (ds < -line.L / 2) ds += line.L;
    traveled += ds; sPrev = pr.s;
    sAt[step] = traveled;
    if (traveled > len) break;
    const v = Math.max(1, st.speed);
    const sl = pr.s + 4 + 0.5 * v;
    line.pointAt(sl, latAt(sl), pos);
    const dx = pos[0] - st.pos[0], dy = pos[1] - st.pos[1];
    const a = Math.atan2(-Math.sin(yaw) * dx + Math.cos(yaw) * dy, Math.cos(yaw) * dx + Math.sin(yaw) * dy);
    const k = (2 * Math.sin(a)) / Math.hypot(dx, dy);
    inp.steer = Math.max(-1, Math.min(1, (Math.atan(W * k) / 0.3) * (1 + (v / 18) ** 2)));
    const vT = vAt(pr.s), e = vT - st.speed;
    inp.throttle = e > 0 ? Math.min(1, 0.3 + 0.4 * e) : Math.max(0, 0.3 + 0.6 * e);
    inp.brake = e < -1 ? Math.min(1, 0.15 * (-e - 1)) : 0;
    car.step(inp, surface, DT);
    if (step < SETTLE) continue;
    const s2 = car.state;
    // road normal under the CG
    const g = plain.sample(s2.pos[0], s2.pos[1]);
    const r = rollOf(s2.quat, [g.nx, g.ny, g.nz]);
    if (Math.abs(r) > roll) roll = Math.abs(r);
    if (Math.abs(r) > ROLLOVER_RAD) rolled = true;
    const [x, y, z, w] = s2.quat;
    const ex = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)];
    const rr = Math.abs(ex[0] * s2.angVel[0] + ex[1] * s2.angVel[1] + ex[2] * s2.angVel[2]);
    if (rr > rollRate) rollRate = rr;
    let anyKerb = false, anyLift = false;
    const cols: number[] = [];
    for (let wi = 0; wi < 4; wi++) {
      const wh = s2.wheels[wi];
      const zp = plain.sample(wh.pos[0], wh.pos[1]).z;
      const zs = surface.sample(wh.pos[0], wh.pos[1]).z;
      const h = zs - zp;
      // air gap under the tyre (hub height above the ground minus the radius), for a kerb-caused lift
      if (wh.load <= 0 && step - lastK[wi] < KERB_WINDOW) { const g = wh.pos[2] - spec.wheel.radius - zs; if (g > gapK[wi]) gapK[wi] = g; }
      if (h > 0.005) { anyKerb = true; lastK[wi] = step; }
      if (h > maxH) maxH = h;
      if (wh.load <= 0) { anyLift = true; wl[step] |= 1 << wi; if (step - lastK[wi] < KERB_WINDOW) kerbRecent[step] |= 1 << wi; }
      if (wh.load > maxLoad) maxLoad = wh.load;
      const vz = Math.abs(wh.compression - hz[wi]) / DT; hz[wi] = wh.compression;
      if (step > SETTLE + 5 && vz > maxVz) maxVz = vz;
      if (rows) cols.push(h, wh.load, wh.compression);
    }
    // hull floor corners vs the ground
    let hull = 0;
    {
      const R00 = 1 - 2 * (y * y + z * z), R01 = 2 * (x * y - z * w), R02 = 2 * (x * z + y * w);
      const R10 = 2 * (x * y + z * w), R11 = 1 - 2 * (x * x + z * z), R12 = 2 * (y * z - x * w);
      const R20 = 2 * (x * z - y * w), R21 = 2 * (y * z + x * w), R22 = 1 - 2 * (x * x + y * y);
      const h = spec.hull;
      for (const hx of [h.front, h.rear]) for (const hy of [h.halfWidth, -h.halfWidth]) {
        const X = s2.pos[0] + R00 * hx + R01 * hy + R02 * h.floor;
        const Y = s2.pos[1] + R10 * hx + R11 * hy + R12 * h.floor;
        const Z = s2.pos[2] + R20 * hx + R21 * hy + R22 * h.floor;
        if (surface.sample(X, Y).z > Z) hull = 1;
      }
    }
    if (hull) hullMs++;
    if (anyKerb) { onKerbMs++; lastKerb = step; }
    if (anyLift) { lift[step] = 1; liftMs++; }
    if (rows && step % 2 === 0) rows.push([(step * DT).toFixed(3), pr.s.toFixed(2), pr.lateral.toFixed(3), s2.speed.toFixed(2), (r * 180 / Math.PI).toFixed(2), (rr * 180 / Math.PI).toFixed(1), ...cols.map((u) => u.toFixed(4)), hull].join(','));
    if (rolled && step - lastKerb > 3000) break;
  }
  return { gap: Math.max(...gapK), roll, rollRate, lift, wl, liftMs, onKerbMs, maxH, maxLoad, hullMs, maxVz, rolled, kerbRecent, rows, sAt: sAt.subarray(0, step) };
}

/** Drive one case on the kerbed surface and the same path on the plain road. */
export function kerbTraversal(p: KerbPack, probe: any, c: TraversalCase, opts: { trace?: boolean } = {}): TraversalResult {
  const line = p.line;
  const st = c.kind === 'kerb' ? p.scenery.kerbs.strips[c.index] : p.scenery.sausages.strips[c.index];
  const prof = lineProfile(p, probe), sc = c.speedScale ?? 1;
  const vAt = (s: number) => sc * line.at(prof, s);
  const sMid = st.s0 + ((st.s1 - st.s0 + line.L) % line.L) / 2;
  const sA = st.s0 - 100, sB = st.s1 + 30;
  let latAt: (s: number) => number;
  if (c.angleDeg > 0) {
    const tn = Math.tan((c.angleDeg * Math.PI) / 180);
    latAt = (s: number) => {
      let d = s - sMid; if (d > line.L / 2) d -= line.L; else if (d < -line.L / 2) d += line.L;
      const bl = bandLat(p, c.kind, st, s) * st.side;
      return st.side * Math.max(line.at(line.off, s) * st.side, bl + d * tn);
    };
  } else latAt = (s: number) => line.at(line.off, s) + st.side * c.offset;
  const a = drive(p, p.surface, probe, c, sA, sB, latAt, vAt, !!opts.trace);
  const b = drive(p, plainOf(p), probe, c, sA, sB, latAt, vAt, false);
  // a lift caused by the strip: a wheel airborne while on the strip or within KERB_WINDOW of leaving it, where the
  // plain-road run (matched by distance travelled, +-50 ms) had that wheel on the ground
  let kerbLift = 0, j = 0;
  for (let i = 0; i < a.sAt.length; i++) {
    const m = a.kerbRecent[i];
    if (!m) continue;
    while (j < b.sAt.length - 1 && b.sAt[j] < a.sAt[i]) j++;
    let bm = 0; for (let k = Math.max(0, j - 50); k < Math.min(b.sAt.length, j + 50); k++) bm |= b.wl[k];
    if (m & ~bm) kerbLift++;
  }
  const deg = 180 / Math.PI;
  const label = `${c.kind} ${String(c.index).padStart(2)} ${st.side > 0 ? 'L' : 'R'} s${Math.round(st.s0)}-${Math.round(st.s1)} ${c.angleDeg > 0 ? `x${c.angleDeg}deg` : `off ${c.offset >= 0 ? '+' : ''}${c.offset}`}`;
  const maxRollDeg = a.roll * deg;
  return {
    label, s0: st.s0, s1: st.s1, v0: vAt(sA), onKerbMs: a.onKerbMs, maxKerbH: a.maxH,
    maxRollDeg, baseRollDeg: b.roll * deg, maxRollRateDeg: a.rollRate * deg,
    liftMs: a.liftMs, kerbLiftMs: kerbLift, kerbLiftGap: a.gap, baseLiftMs: b.liftMs, maxLoad: a.maxLoad, hullMs: a.hullMs, maxWheelVz: a.maxVz,
    rolledOver: a.rolled, fail: a.rolled || maxRollDeg > 15 || kerbLift > 0, rows: a.rows,
  };
}

/** An AI-driven solo lap (the autopilot's driver, the player's spec) with roll / kerb-lift events and their lap time. */
export function runAiLap(p: KerbPack, probe: any, opts: { quiet?: boolean } = {}): { events: string[]; lapTime: number; maxRollDeg: number; maxRollT: number; maxRollS: number; rolled: boolean } {
  const line = p.line, surface = p.surface, plain = plainOf(p);
  const spec = buildAiSpec(probe, null, 1);
  const perf = measureCarPerf(spec);
  const profile = buildSpeedProfile(line, perf, spec);
  const car = new Vehicle(spec, { autoShift: true });
  const tr = new Traffic(1, line.L);
  tr.front[0] = spec.hull.front; tr.rear[0] = -spec.hull.rear; tr.hw[0] = spec.hull.halfWidth; tr.pace[0] = 120;
  const drv = new AiDriver(car, line, perf, spec, profile, { number: 'solo', scale: 1, targetLap: 120, sigma: 0, aggression: 1, seed: 1 }, 0, tr);
  drv.ctl.noise = false;
  const s0 = line.L - 520;
  const pos = new Float64Array(2);
  line.pointAt(s0, line.at(line.off, s0), pos);
  car.reset([pos[0], pos[1], surface.sample(pos[0], pos[1]).z], line.headingAt(s0), Math.min(18, 0.8 * line.at(profile, s0)));
  let t = 0, U = s0 - line.L, hint = -1, tStart = NaN, lapTime = NaN;
  let maxRoll = 0, maxRollT = 0, maxRollS = 0, rolled = false;
  const events: string[] = [];
  let lastEv = -1e9;
  for (let step = 0; step < 400000; step++) {
    if (step % 2 === 0) drv.update(2 * DT);
    car.step(drv.input, surface, DT);
    t += DT;
    const pr = line.project(car.state.pos[0], car.state.pos[1], hint);
    hint = pr.index;
    let d = pr.s - tr.s[0]; if (d > line.L / 2) d -= line.L; else if (d < -line.L / 2) d += line.L;
    const Uprev = U; U += d;
    tr.s[0] = pr.s; tr.lat[0] = pr.lateral; tr.v[0] = car.state.speed; tr.U[0] = U;
    if (Math.floor(U / line.L) > Math.floor(Uprev / line.L)) { if (Number.isNaN(tStart)) tStart = t; else { lapTime = t - tStart; break; } }
    const lapT = Number.isNaN(tStart) ? -1 : t - tStart;
    const st = car.state;
    const g = plain.sample(st.pos[0], st.pos[1]);
    const r = Math.abs(rollOf(st.quat, [g.nx, g.ny, g.nz])) * 180 / Math.PI;
    if (lapT >= 0 && r > maxRoll) { maxRoll = r; maxRollT = lapT; maxRollS = pr.s; }
    if (r > 60) rolled = true;
    let onK = 0, lifted = 0;
    for (const w of st.wheels) {
      if (surface.sample(w.pos[0], w.pos[1]).z - plain.sample(w.pos[0], w.pos[1]).z > 0.005) onK++;
      if (w.load <= 0) lifted++;
    }
    if ((r > 15 || (onK && lifted)) && t - lastEv > 0.25) {
      lastEv = t;
      events.push(`t ${lapT.toFixed(2)} s  s ${pr.s.toFixed(0)}  lat ${pr.lateral.toFixed(2)}  v ${st.speed.toFixed(1)}  roll ${r.toFixed(1)} deg  wheels on kerb ${onK} lifted ${lifted}`);
    }
    if (drv.needsRecovery) { events.push(`t ${lapT.toFixed(2)} recovery at s ${pr.s.toFixed(0)}`); break; }
  }
  void opts;
  return { events, lapTime, maxRollDeg: maxRoll, maxRollT, maxRollS, rolled };
}
