// Camera poses of the drive proxy (camera_walk.ts) that are not on the centre line (codify round, 20 Oct 2026): the
// owner's looks when he drives, inside the pit lane end to end and from every paved runoff looking back at the track.
// Pure functions over a package's track.json and scenery.json (tests: src/scoreboard/__tests__/poses.test.ts).
import { containment, escapeRuns, makeProjector, pavedTargets, trackFrame, type TrackLike, type V2 } from '../gates/sceneryGates';

export type Kind = 'fwd' | 'left' | 'right' | 'back' | 'pit' | 'runoff';
/** one camera pose: the car at pos (z null = the drivable surface's height there, sampled in the page), facing heading
 *  (rad, ENU), the hood camera turned by yaw (rad, + = left) */
export interface Shot { file: string; s: number; side: Kind; pos: [number, number, number | null]; heading: number; yaw: number; kind?: string; label?: string }

/** the owner's poses that are not on the centre line: inside the pit lane, and from each paved runoff looking back */
export function pitPoses(t: TrackLike & { spacing_m: number }, sc: any, stepM: number): Shot[] {
  const out: Shot[] = [];
  if (!(stepM > 0)) return out;
  const proj = makeProjector(t);
  const { nl } = trackFrame(t);
  (sc.pit_lane?.parts ?? []).forEach((p: any, k: number) => {
    const C: number[][] = p.center;
    if (!C || C.length < 3) return;
    // the lane's driving direction: its tangent against the track's at the abeam station, where they run side by side
    let dot = 0;
    for (let i = 2; i < C.length - 2; i += 5) {
      const q = proj([C[i][0], C[i][1]], 80); if (!q) continue;
      const tx = nl[q.i][1], ty = -nl[q.i][0];   // track tangent (left normal rotated back)
      dot += (C[i + 2][0] - C[i - 2][0]) * tx + (C[i + 2][1] - C[i - 2][1]) * ty;
    }
    const P = dot < 0 ? C.slice().reverse() : C;
    let acc = 0, next = 0, n = 0;
    for (let i = 0; i < P.length; i++) {
      if (i) acc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]);
      if (acc + 1e-6 < next && i !== P.length - 1) continue;
      const a = P[Math.max(0, i - 2)], b = P[Math.min(P.length - 1, i + 2)];
      const q = proj([P[i][0], P[i][1]], 120);
      out.push({ file: `sim/pit_p${k}_${String(n).padStart(3, '0')}.jpg`, s: q ? q.i * t.spacing_m : 0, side: 'pit',
        pos: [P[i][0], P[i][1], null], heading: Math.atan2(b[1] - a[1], b[0] - a[0]), yaw: 0, label: `pit lane ${k}, ${acc.toFixed(0)} m from its start` });
      n++; next += stepM;
      if (i === P.length - 1) break;
    }
  });
  return out;
}

/** metres beyond a runoff polygon's far side the car stands for a shallow polygon (the hood hides about the first 5 m) */
export const RUNOFF_BACK = 5;

export function runoffPoses(t: TrackLike & { spacing_m: number }, sc: any): Shot[] {
  const out: Shot[] = [];
  const { nl, hl, hr } = trackFrame(t);
  const n = t.n, sp = t.spacing_m, Lt = n * sp;
  // every paved polygon the containment rays reach before a barrier (allowed runoff and escapes alike: a passing
  // package has only allowed ones); the ray hits grouped into runs along the lap
  const rep = containment(t, sc, {});
  const hits = [...rep.escapes, ...rep.allowed].filter((e) => e.angle === 0);
  const targets = pavedTargets(sc);
  const inside = (p: V2, name: string) => targets.some((T) => T.name === name && p[0] >= T.box[0] && p[0] <= T.box[2] && p[1] >= T.box[1] && p[1] <= T.box[3] && inPoly(p, T.poly));
  let k = 0;
  for (const r of escapeRuns(hits)) {
    const len = r.s1 - r.s0, m = Math.max(1, Math.round(len / 150));
    for (let j = 0; j < m; j++) {
      const s = r.s0 + (len * (j + 0.5)) / m, i = Math.round(s / sp) % n, side = r.side === 'left' ? 1 : -1;
      const o: V2 = [nl[i][0] * side, nl[i][1] * side], hw = side > 0 ? hl[i] : hr[i];
      const e: V2 = [t.center[i][0] + o[0] * hw, t.center[i][1] + o[1] * hw];
      // round 11 (Buttonwillow round-10 prep: 15 of 31 runoff stills showed only dirt past the hood): the camera stood
      // 4 m inside the polygon's near side looking at the track, so the view left the paving after 0.5-5 m, about
      // where the hood ends. Now it stands at the polygon's FAR side on the same ray, looking back across it: the
      // paving's depth D along the ray (entry to exit) lies in view; for D < 30 m the car stands RUNOFF_BACK (5) m
      // beyond the far side so the hood's blind ground falls on the dirt behind it, for a deeper polygon (a road
      // running away from the track) 25 m into it
      let d = r.dmin;
      for (let dd = 0.5; dd <= 120; dd += 0.5) if (inside([e[0] + o[0] * dd, e[1] + o[1] * dd], r.target)) { d = dd; break; }
      let D = 0;
      for (let dd = d; dd <= d + 120; dd += 0.5) { if (!inside([e[0] + o[0] * dd, e[1] + o[1] * dd], r.target)) break; D = dd - d; }
      const at = D >= 30 ? d + 25 : d + D + RUNOFF_BACK;
      out.push({ file: `sim/runoff_${String(k++).padStart(2, '0')}.jpg`, s: Math.round(s), side: 'runoff', pos: [e[0] + o[0] * at, e[1] + o[1] * at, null],
        heading: Math.atan2(-o[1], -o[0]), yaw: 0, label: `${r.target}, ${r.side} of s ${r.s0.toFixed(0)}-${r.s1.toFixed(0)} (across ${D.toFixed(0)} m of its paving)` });
    }
  }
  // paved runoff zones (not containment targets): from the middle of each, looking at the nearest centre point
  const proj = makeProjector(t);
  for (const p of sc.paved_zones?.parts ?? []) {
    if (p.kind === 'closed_road' || !p.center?.length) continue;
    const c = p.center[Math.floor(p.center.length / 2)], q = proj([c[0], c[1]], 120);
    if (!q) continue;
    const tc = t.center[q.i];
    out.push({ file: `sim/runoff_${String(k++).padStart(2, '0')}.jpg`, s: Math.round(q.i * sp) % Lt, side: 'runoff', pos: [c[0], c[1], null],
      heading: Math.atan2(tc[1] - c[1], tc[0] - c[0]), yaw: 0, label: `${p.turn ?? p.name ?? 'paved runoff'} (paved runoff zone)` });
  }
  return out;
}

function inPoly(p: V2, poly: V2[]): boolean {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < ((b[0] - a[0]) * (p[1] - a[1])) / (b[1] - a[1]) + a[0]) c = !c;
  }
  return c;
}
