// Phantom wall contacts: places where a car on the road gets a wall contact from a segment it has not touched.
// vehicle.ts collide() tests every hull point against each wall segment of the collision world: a point whose projection
// falls on the segment (0 <= t <= 1) and lies on the far side of the segment's infinite line from the car's CG, up to
// 2.9 m beyond it, is treated as through the wall ("a point that crossed a thin wall is still pushed back"). At the end
// of a wall or tyre run that turns away from the road at an angle, that band reaches back across the road: a car driving
// beside the end, never touching it, gets a contact up to ~1.5 m deep (Sonoma T7 brake, 24 Oct 2026: #56 stopped dead
// from 8.7 m/s at s 2081 on the racing line by the inner-face end segment of tyre run #9).
// Diagnosis only (no physics or package change): samples road points (hull corners) with a CG 1 m inboard and 2.5 m
// behind (front corner) or ahead (rear corner), and
// lists the segments whose phantom band covers road, with how far into the road it reaches and whether the racing-line
// corridor (line +- 1 m) is inside it.
//   npx tsx tools/race/wall_phantoms.ts --track <id> [--top 12]
import { createCollisionWorld, COLLISION_KINDS } from '../../src/physics/index';
import { loadTrackPack, trackArg } from './load';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const track = trackArg(argv), TOP = Number(arg('--top', '12'));
const pack = loadTrackPack(track);
const { line } = pack, T = pack.track, N = T.n, SP = T.spacing_m, L = line.L;
const cw = createCollisionWorld(pack.scenery, pack.track) as unknown as {
  nSeg: number; sax: Float64Array; say: Float64Array; sbx: Float64Array; sby: Float64Array; skind: Uint8Array };
const WALL_HALF = 0.1, MAX_DEPTH = 3;   // vehicle.ts WALL_HALF_THICKNESS and the depth cap
// a road point in the world at station s, lateral lat (+ left), from track.json's centre / left / right
function world(s: number, lat: number): [number, number] {
  const i = ((Math.round(s / SP) % N) + N) % N, c = T.center[i], e = lat >= 0 ? T.left[i] : T.right[i];
  const h = lat >= 0 ? line.halfL[i] : line.halfR[i], f = Math.abs(lat) / Math.max(0.5, h);
  return [c[0] + (e[0] - c[0]) * f, c[1] + (e[1] - c[1]) * f];
}
type Row = { seg: number; kind: string; s0: number; s1: number; reach: number; onLine: boolean; maxDepth: number; side: string };
const rows: Row[] = [];
for (let it = 0; it < cw.nSeg; it++) {
  const ax = cw.sax[it], ay = cw.say[it], ex = cw.sbx[it] - ax, ey = cw.sby[it] - ay, L2 = ex * ex + ey * ey;
  if (L2 < 1e-6) continue;
  const Ls = Math.sqrt(L2), nx = -ey / Ls, ny = ex / Ls;
  const pa = line.project(ax, ay), sa = pa.s, la = pa.lateral;
  const pb = line.project(ax + ex, ay + ey), sb = pb.s, lb = pb.lateral;
  const ha = la >= 0 ? line.at(line.halfL, sa) : line.at(line.halfR, sa);
  if (Math.abs(la) - ha > 6 && Math.abs(lb) - ha > 6) continue;   // far from the road
  let lo = Math.min(sa, sb), hi = Math.max(sa, sb);
  if (hi - lo > L / 2) { lo = Math.max(sa, sb); hi = Math.min(sa, sb) + L; }   // across the start line
  if (hi - lo > 60) continue;
  let reach = -1, onLine = false, maxDepth = 0, h0 = Infinity, h1 = -Infinity, side = '';
  for (let s = lo - 6; s <= hi + 6; s += 0.25) {
    const hl = line.at(line.halfL, s), hr = line.at(line.halfR, s), off = line.at(line.off, s);
    for (let lat = -hr; lat <= hl; lat += 0.1) {
      const [qx, qy] = world(s, lat);
      const t = ((qx - ax) * ex + (qy - ay) * ey) / L2;
      if (t < 0 || t > 1) continue;
      const dq = (qx - ax) * nx + (qy - ay) * ny;
      // the CG 1 m inboard of this hull corner (toward the centreline) and 2.5 m behind it (a front corner) or ahead
      // of it (a rear corner)
      let opp = false;
      for (const back of [-2.5, 2.5]) {
        const [gx, gy] = world(s + back, lat - Math.sign(lat || 1) * 1.0);
        const dg = (gx - ax) * nx + (gy - ay) * ny;
        if (dg !== 0 && Math.sign(dq) !== Math.sign(dg)) opp = true;
      }
      if (!opp) continue;
      const depth = WALL_HALF + Math.abs(dq);
      if (depth > MAX_DEPTH) continue;
      const into = lat >= 0 ? hl - lat : hr + lat;   // metres inside the road edge
      if (into > reach) { reach = into; side = lat >= 0 ? 'L' : 'R'; }
      if (Math.abs(lat - off) <= 1.0) onLine = true;
      maxDepth = Math.max(maxDepth, depth); h0 = Math.min(h0, s); h1 = Math.max(h1, s);
    }
  }
  if (reach >= 0) rows.push({ seg: it, kind: COLLISION_KINDS[cw.skind[it]] ?? String(cw.skind[it]), s0: ((h0 % L) + L) % L, s1: ((h1 % L) + L) % L, reach, onLine, maxDepth, side });
}
rows.sort((p, q) => (Number(q.onLine) - Number(p.onLine)) || q.reach - p.reach);
console.log(`${track}: ${rows.length} wall segments whose phantom band covers road (${rows.filter((r) => r.onLine).length} reach the racing line +- 1 m)`);
console.log('| station (m) | side | segment | kind | reaches into the road (m) | racing line inside | deepest phantom contact (m) |');
console.log('|---|---|---|---|---|---|---|');
for (const r of rows.slice(0, TOP)) console.log(`| ${r.s0.toFixed(0)}-${r.s1.toFixed(0)} | ${r.side} | ${r.seg} | ${r.kind} | ${r.reach.toFixed(1)} | ${r.onLine ? 'yes' : 'no'} | ${r.maxDepth.toFixed(2)} |`);
