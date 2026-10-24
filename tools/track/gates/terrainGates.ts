// Terrain-override gates (Sonoma round 14A, 23 Oct 2026; the owner's round-13 drive: "the active and inactive track
// surfaces actually go together in a sensical way"). Run by build_track.py --stage scenery through run_gates.ts when
// the package's scenery.json has `terrain_override`; a package without one passes them trivially (no region).
//
// All three measure the surface the car drives on and the app draws the ground from (src/physics/track.ts with the
// package's paved parts and the override), without the raised kerb humps and sausages (a kerb is a deliberate object on
// that surface, gated by the kerb traversal gate and by KERBS ON SURFACE below). "In the region" = override weight 1
// (inside a polygon, deeper than its ramp); points in the ramp are counted and reported, not gated.
//
//   PAVEMENT JOINS     every course edge point in the region (every metre, both sides) and every metre of a paved part's
//                      edges and ends in the region (closed roads, runoff, pit lane): the height step across the boundary
//                      (0.02 m either side of it) at most `stepMax` (0.02 m) and the cross-slope change between the 1 m
//                      inside and the 1 m outside at most `slopeDegMax` (2 deg).
//   SURFACE SMOOTHNESS cross-profiles of the course at every station whose edge lies in the region, from 1 m inside each
//                      edge outward at 1 m spacing while in the region and off the course: |second difference| at most
//                      `d2Max` (0.01 m: a 1 % grade change per metre, a vertical radius of 100 m; paved lots are laid to
//                      ACI 330's 6 mm under a 3 m straightedge, which a uniform bend meets at 5 mm per metre squared, and
//                      their designed grade breaks, crowns and valley gutters, change 1-2 % over a metre or more), and no
//                      point more than `troughMax` (0.05 m) below (a trough) or above (a ridge) the line between its
//                      neighbours 5 m either side.
//   KERBS ON SURFACE   every kerb block in the region (scenery kerb_lines: the islands' red / white blocks, stripe_m long;
//                      and the course's kerb strips beyond the edge, 0.95 m blocks): the block's footprint plane (the
//                      surface at its four corners) tilted at most `kerbTiltDegMax` (2 deg) from the surface's own plane
//                      round it (least squares over +-4 m; for a course kerb strip the course's edge plane continued), and
//                      no gap under a kerb_lines block: the app stands each corner on its own ground with a 0.05 m skirt
//                      (src/app/scenery.ts buildKerbLines), so a gap is ground more than 0.05 m below the block's bottom
//                      face (its corners' ground) at the block's middle or the middle of a side.
import { createTrackSurface, packageSurfaceOptions, terrainOverrideWeightFn, type Surface, type TrackJson } from '../../../src/physics/index';

type V2 = [number, number];
export interface TerrainGateOptions { stepMax: number; slopeDegMax: number; d2Max: number; troughMax: number; kerbTiltDegMax: number; kerbGapMax: number }
export const TERRAIN_GATE_DEFAULTS: TerrainGateOptions = { stepMax: 0.02, slopeDegMax: 2, d2Max: 0.01, troughMax: 0.05, kerbTiltDegMax: 2, kerbGapMax: 0 };

export interface JoinFinding { what: string; x: number; y: number; step: number; slopeDeg: number }
export interface JoinReport { checked: number; ramp: number; maxStep: number; maxSlopeDeg: number; bad: JoinFinding[]; worst: JoinFinding[] }
export interface SmoothFinding { s: number; side: string; off: number; x: number; y: number; d2?: number; dev?: number }
export interface SmoothReport { profiles: number; points: number; maxD2: number; maxTrough: number; maxRidge: number; badD2: SmoothFinding[]; badDev: SmoothFinding[] }
export interface KerbFinding { what: string; x: number; y: number; tiltDeg: number; gap: number }
export interface KerbReport { blocks: number; maxTiltDeg: number; maxGap: number; bad: KerbFinding[] }
export interface TerrainReport { regions: number; joins: JoinReport; smooth: SmoothReport; kerbs: KerbReport; fail: boolean }

const deg = (a: number) => (a * 180) / Math.PI;

/** The plain driven surface of a package (no kerb humps, no sausages) and the override weight. */
export function plainSurface(track: TrackJson, hf: Float32Array, sc: any): { surf: Surface; w: (x: number, y: number) => number } {
  const o = packageSurfaceOptions(sc, null);
  return { surf: createTrackSurface(track, hf, { ...o, kerbs: null, sausages: null }), w: terrainOverrideWeightFn(sc?.terrain_override) };
}

function edgeFrame(track: TrackJson, i: number, side: number): { e: V2; n: V2; t: V2 } {
  const N = track.n, a = track.center[(i - 1 + N) % N], b = track.center[(i + 1) % N];
  let tx = b[0] - a[0], ty = b[1] - a[1];
  const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l;
  const e = side > 0 ? track.left[i] : track.right[i];
  return { e: [e[0], e[1]], n: [-ty * side, tx * side], t: [tx, ty] };
}

/** Step and cross-slope change across a boundary at point e with outward normal n. */
function across(z: (x: number, y: number) => number, e: V2, n: V2): { step: number; slopeDeg: number } {
  const at = (d: number) => z(e[0] + n[0] * d, e[1] + n[1] * d);
  const step = Math.abs(at(0.02) - at(-0.02));
  const si = at(-0.05) - at(-1.05), so = at(1.05) - at(0.05);
  return { step, slopeDeg: Math.abs(deg(Math.atan(so)) - deg(Math.atan(si))) };
}

export function pavementJoins(track: TrackJson, sc: any, surf: Surface, w: (x: number, y: number) => number, o: TerrainGateOptions): JoinReport {
  const z = (x: number, y: number) => surf.sample(x, y).z;
  const rep: JoinReport = { checked: 0, ramp: 0, maxStep: 0, maxSlopeDeg: 0, bad: [], worst: [] };
  const all: JoinFinding[] = [];
  const test = (what: string, e: V2, n: V2) => {
    const we = w(e[0], e[1]);
    if (we <= 0) return;
    if (we < 1) { rep.ramp++; return; }
    rep.checked++;
    const r = across(z, e, n);
    const f = { what, x: +e[0].toFixed(2), y: +e[1].toFixed(2), step: +r.step.toFixed(4), slopeDeg: +r.slopeDeg.toFixed(2) };
    all.push(f);
    rep.maxStep = Math.max(rep.maxStep, r.step); rep.maxSlopeDeg = Math.max(rep.maxSlopeDeg, r.slopeDeg);
    if (r.step > o.stepMax || r.slopeDeg > o.slopeDegMax) rep.bad.push(f);
  };
  // the course's edges, every station (~1 m)
  for (let i = 0; i < track.n; i++) for (const side of [1, -1]) {
    const { e, n } = edgeFrame(track, i, side);
    test(`course ${side > 0 ? 'left' : 'right'} edge s ${(i * track.spacing_m).toFixed(0)}`, e, n);
  }
  // every paved part's edges and ends, every metre, where they are not on the course edge
  const proj = (x: number, y: number) => surf.sample(x, y).onTrack;
  const parts: { name: string; p: any }[] = [
    ...((sc?.pit_lane?.parts ?? []) as any[]).map((p) => ({ name: 'pit lane', p })),
    ...((sc?.paved_zones?.parts ?? []) as any[]).map((p) => ({ name: p.turn ?? p.name ?? 'zone', p })),
  ];
  for (const { name, p } of parts) {
    const C = p.center as number[][], m = C.length;
    for (const [key, sgn] of [['left', 1], ['right', -1]] as const) {
      const E = p[key] as number[][];
      for (let j = 0; j + 1 < m; j++) {
        const a = E[j], b = E[j + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (L < 1e-6) continue;
        const tx = (b[0] - a[0]) / L, ty = (b[1] - a[1]) / L;
        // outward: away from the part's centre line
        const cx = (C[j][0] + C[j + 1][0]) / 2 - (a[0] + b[0]) / 2, cy = (C[j][1] + C[j + 1][1]) / 2 - (a[1] + b[1]) / 2;
        let nx = -ty * sgn, ny = tx * sgn;
        if (nx * cx + ny * cy > 0) { nx = -nx; ny = -ny; }
        for (let u = 0; u < L; u += 1) {
          const e: V2 = [a[0] + tx * u, a[1] + ty * u];
          // the course side of a mouth is the course edge, tested above; a part edge inside the course is no boundary
          if (proj(e[0] + nx * 0.3, e[1] + ny * 0.3) || proj(e[0] - nx * 0.3, e[1] - ny * 0.3)) continue;
          test(`${name} ${key} edge`, e, [nx, ny]);
        }
      }
    }
    for (const end of [0, m - 1]) {
      const l = p.left[end], r = p.right[end], c2 = C[end === 0 ? 1 : m - 2];
      const L = Math.hypot(r[0] - l[0], r[1] - l[1]);
      if (L < 1e-6) continue;
      const tx = (r[0] - l[0]) / L, ty = (r[1] - l[1]) / L;
      let nx = -ty, ny = tx;
      if (nx * (c2[0] - C[end][0]) + ny * (c2[1] - C[end][1]) > 0) { nx = -nx; ny = -ny; }
      for (let u = 0.5; u < L; u += 1) {
        const e: V2 = [l[0] + tx * u, l[1] + ty * u];
        if (proj(e[0] + nx * 0.3, e[1] + ny * 0.3) || proj(e[0] - nx * 0.3, e[1] - ny * 0.3)) continue;
        test(`${name} ${end === 0 ? 'start' : 'end'}`, e, [nx, ny]);
      }
    }
  }
  rep.worst = all.sort((a, b) => b.step / o.stepMax + b.slopeDeg / o.slopeDegMax - a.step / o.stepMax - a.slopeDeg / o.slopeDegMax).slice(0, 5);
  rep.maxStep = +rep.maxStep.toFixed(4); rep.maxSlopeDeg = +rep.maxSlopeDeg.toFixed(2);
  return rep;
}

export function surfaceSmoothness(track: TrackJson, surf: Surface, w: (x: number, y: number) => number, o: TerrainGateOptions, reach = 80): SmoothReport {
  const rep: SmoothReport = { profiles: 0, points: 0, maxD2: 0, maxTrough: 0, maxRidge: 0, badD2: [], badDev: [] };
  for (let i = 0; i < track.n; i++) for (const side of [1, -1]) {
    const { e, n } = edgeFrame(track, i, side);
    if (w(e[0], e[1]) < 1) continue;
    const zs: number[] = [], xs: V2[] = [];
    for (let d = -1; d <= reach; d += 1) {
      const x = e[0] + n[0] * d, y = e[1] + n[1] * d;
      if (w(x, y) < 1) break;
      const q = surf.sample(x, y);
      if (d > 0.5 && q.onTrack) break;      // reached the course again (another leg)
      zs.push(q.z); xs.push([x, y]);
    }
    if (zs.length < 3) continue;
    rep.profiles++; rep.points += zs.length;
    const s = +(i * track.spacing_m).toFixed(0), sd = side > 0 ? 'left' : 'right';
    for (let k = 1; k + 1 < zs.length; k++) {
      const d2 = Math.abs(zs[k - 1] - 2 * zs[k] + zs[k + 1]);
      rep.maxD2 = Math.max(rep.maxD2, d2);
      if (d2 > o.d2Max) rep.badD2.push({ s, side: sd, off: k - 1, x: +xs[k][0].toFixed(1), y: +xs[k][1].toFixed(1), d2: +d2.toFixed(4) });
    }
    for (let k = 5; k + 5 < zs.length; k++) {
      const dev = zs[k] - (zs[k - 5] + zs[k + 5]) / 2;
      rep.maxTrough = Math.max(rep.maxTrough, -dev); rep.maxRidge = Math.max(rep.maxRidge, dev);
      if (Math.abs(dev) > o.troughMax) rep.badDev.push({ s, side: sd, off: k - 1, x: +xs[k][0].toFixed(1), y: +xs[k][1].toFixed(1), dev: +dev.toFixed(4) });
    }
  }
  rep.maxD2 = +rep.maxD2.toFixed(4); rep.maxTrough = +rep.maxTrough.toFixed(4); rep.maxRidge = +rep.maxRidge.toFixed(4);
  return rep;
}

/** Angle (deg) between the plane through four corner points and a reference gradient (gx, gy). */
function tiltFrom(corners: [number, number, number][], gx: number, gy: number): number {
  // least-squares plane z = a x + b y + c through the corners
  let sx = 0, sy = 0, sz = 0, sxx = 0, syy = 0, sxy = 0, sxz = 0, syz = 0;
  const k = corners.length;
  for (const [x, y, z] of corners) { sx += x; sy += y; sz += z; sxx += x * x; syy += y * y; sxy += x * y; sxz += x * z; syz += y * z; }
  const mx = sx / k, my = sy / k, mz = sz / k;
  const cxx = sxx / k - mx * mx, cyy = syy / k - my * my, cxy = sxy / k - mx * my, cxz = sxz / k - mx * mz, cyz = syz / k - my * mz;
  const det = cxx * cyy - cxy * cxy || 1e-12;
  const a = (cxz * cyy - cyz * cxy) / det, b = (cyz * cxx - cxz * cxy) / det;
  const n1 = [-a, -b, 1], n2 = [-gx, -gy, 1];
  const dot = n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2];
  return deg(Math.acos(Math.min(1, dot / (Math.hypot(...n1) * Math.hypot(...n2)))));
}

/** The surface's own plane round (x, y): least squares over a 9 x 9 grid +-4 m. */
function localGradient(z: (x: number, y: number) => number, x: number, y: number): [number, number] {
  const pts: [number, number, number][] = [];
  for (let a = -4; a <= 4; a++) for (let b = -4; b <= 4; b++) pts.push([x + a, y + b, z(x + a, y + b)]);
  let sxx = 0, syy = 0, sxz = 0, syz = 0, mz = 0;
  for (const p of pts) mz += p[2];
  mz /= pts.length;
  for (const [px, py, pz] of pts) { const dx = px - x, dy = py - y; sxx += dx * dx; syy += dy * dy; sxz += dx * (pz - mz); syz += dy * (pz - mz); }
  return [sxz / sxx, syz / syy];
}

export function kerbsOnSurface(track: TrackJson, sc: any, surf: Surface, w: (x: number, y: number) => number, o: TerrainGateOptions): KerbReport {
  const z = (x: number, y: number) => surf.sample(x, y).z;
  const rep: KerbReport = { blocks: 0, maxTiltDeg: 0, maxGap: 0, bad: [] };
  const add = (f: KerbFinding) => {
    rep.blocks++;
    rep.maxTiltDeg = Math.max(rep.maxTiltDeg, f.tiltDeg); rep.maxGap = Math.max(rep.maxGap, f.gap);
    if (f.tiltDeg > o.kerbTiltDegMax || f.gap > o.kerbGapMax) rep.bad.push(f);
  };
  // the islands' kerb lines (drawn level across at the higher side's ground, a 0.05 m skirt below)
  (sc?.kerb_lines ?? []).forEach((k: any, li: number) => {
    const P = k.pts as number[][], hw = k.width / 2, step = k.stripe_m || 1;
    // resample the line every stripe_m: one block per stripe
    const cum = [0];
    for (let i = 1; i < P.length; i++) cum.push(cum[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const at = (u: number): [V2, V2] => {
      let i = 1; while (i < P.length - 1 && cum[i] < u) i++;
      const t = (u - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1);
      const x = P[i - 1][0] + t * (P[i][0] - P[i - 1][0]), y = P[i - 1][1] + t * (P[i][1] - P[i - 1][1]);
      const L = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]) || 1;
      return [[x, y], [-(P[i][1] - P[i - 1][1]) / L, (P[i][0] - P[i - 1][0]) / L]];
    };
    for (let u = 0; u + step <= cum[cum.length - 1] + 1e-6; u += step) {
      const [a, na] = at(u), [b, nb] = at(u + step), mid: V2 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      if (w(mid[0], mid[1]) < 1) continue;
      const c: [number, number, number][] = [];
      for (const [p, nn] of [[a, na], [b, nb]] as [V2, V2][]) for (const sg of [1, -1]) {
        const x = p[0] + nn[0] * hw * sg, y = p[1] + nn[1] * hw * sg; c.push([x, y, z(x, y)]);
      }
      const g = localGradient(z, mid[0], mid[1]);
      // corners: c0 a+, c1 a-, c2 b+, c3 b-; the bottom face through them; ground below it by more than the skirt = gap
      let gap = -Infinity;
      for (const [i, j] of [[0, 1], [2, 3], [0, 2], [1, 3], [0, 3]] as [number, number][]) {
        const mx = (c[i][0] + c[j][0]) / 2, my = (c[i][1] + c[j][1]) / 2;
        gap = Math.max(gap, (c[i][2] + c[j][2]) / 2 - 0.05 - z(mx, my));
      }
      add({ what: `kerb line ${li} (${(k.src ?? '').slice(0, 40)}) at ${u.toFixed(1)} m`, x: +mid[0].toFixed(1), y: +mid[1].toFixed(1), tiltDeg: +tiltFrom(c, g[0], g[1]).toFixed(2), gap: +Math.max(0, gap).toFixed(4) });
    }
  });
  // the course's kerb strips: the band beyond (or inside) the edge, 0.95 m blocks, against the course's edge plane
  const K = sc?.kerbs;
  if (K?.strips) {
    const fr = track.profile.fractions, nf = fr.length;
    for (const st of K.strips) {
      const off = st.off !== undefined ? st.off : (K.inside ?? true) ? -K.width / 2 : K.width / 2;
      const i0 = Math.round(st.s0 / track.spacing_m), i1 = Math.round(st.s1 / track.spacing_m);
      for (let i = i0; i < i1; i++) {
        const ii = ((i % track.n) + track.n) % track.n, jj = (ii + 1) % track.n;
        const A = edgeFrame(track, ii, st.side), B = edgeFrame(track, jj, st.side);
        const mid: V2 = [(A.e[0] + B.e[0]) / 2 + A.n[0] * off, (A.e[1] + B.e[1]) / 2 + A.n[1] * off];
        if (w(mid[0], mid[1]) < 1) continue;
        const c: [number, number, number][] = [];
        for (const F of [A, B]) for (const d of [off - K.width / 2, off + K.width / 2]) {
          const x = F.e[0] + F.n[0] * d, y = F.e[1] + F.n[1] * d; c.push([x, y, z(x, y)]);
        }
        // the course's edge plane: along the edge (its two edge heights) and across (the edge third's slope, outward)
        const zA = track.profile.z[ii], zB = track.profile.z[jj];
        const eA = st.side > 0 ? zA[0] : zA[nf - 1], eB = st.side > 0 ? zB[0] : zB[nf - 1];
        const hA = Math.hypot(A.e[0] - track.center[ii][0], A.e[1] - track.center[ii][1]);
        const third = hA * (fr[nf - 1] - fr[nf - 2]);
        const cs = ((st.side > 0 ? zA[0] - zA[1] : zA[nf - 1] - zA[nf - 2])) / third;   // dz per m outward
        const ds = Math.hypot(B.e[0] - A.e[0], B.e[1] - A.e[1]) || 1;
        const ga = (eB - eA) / ds;                                                    // dz per m along
        const gx = ga * A.t[0] + cs * A.n[0], gy = ga * A.t[1] + cs * A.n[1];
        add({ what: `course kerb ${st.side > 0 ? 'left' : 'right'} s ${(ii * track.spacing_m).toFixed(0)}`, x: +mid[0].toFixed(1), y: +mid[1].toFixed(1), tiltDeg: +tiltFrom(c, gx, gy).toFixed(2), gap: 0 });
      }
    }
  }
  rep.maxTiltDeg = +rep.maxTiltDeg.toFixed(2); rep.maxGap = +rep.maxGap.toFixed(4);
  return rep;
}

export function terrainGates(track: TrackJson, hf: Float32Array, sc: any, opts: Partial<TerrainGateOptions> = {}): TerrainReport {
  const o = { ...TERRAIN_GATE_DEFAULTS, ...opts };
  const regions = sc?.terrain_override?.regions?.length ?? 0;
  const { surf, w } = plainSurface(track, hf, sc);
  const joins = regions ? pavementJoins(track, sc, surf, w, o) : { checked: 0, ramp: 0, maxStep: 0, maxSlopeDeg: 0, bad: [], worst: [] };
  const smooth = regions ? surfaceSmoothness(track, surf, w, o) : { profiles: 0, points: 0, maxD2: 0, maxTrough: 0, maxRidge: 0, badD2: [], badDev: [] };
  const kerbs = regions ? kerbsOnSurface(track, sc, surf, w, o) : { blocks: 0, maxTiltDeg: 0, maxGap: 0, bad: [] };
  return { regions, joins, smooth, kerbs, fail: !!(joins.bad.length || smooth.badD2.length || smooth.badDev.length || kerbs.bad.length) };
}
