// Terrain sampler (Sonoma round 14A, 23 Oct 2026): the driven surface of a package as the app builds it (track profile,
// pit lane and paved zones, kerbs, the terrain override of scenery.json), sampled along cross-profiles at given stations
// or on a grid, for the before / after profile plots and height maps of compare/<id>/round14a/.
//
//   npx tsx tools/track/compare/terrain_sample.ts <package dir> profiles <out.json> --s 2080,2120 [--lat -60:90] [--step 0.5]
//   npx tsx tools/track/compare/terrain_sample.ts <package dir> grid <out.json> --box x0,y0,x1,y1 [--step 0.5]
//
// profiles: per station s (m) and lateral offset (m, + = left of the course), the surface height, what it is (track /
// zone name / ground), every paved zone part's own height there (where its footprint covers the point) and the raw
// heightfield. grid: the surface height and its kind on a regular grid.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { createTrackSurface, loadHeightfield, type PitLaneJson, type TrackJson } from '../../../src/physics/index';
import { packageSurfaceOptions } from '../../../src/physics/track';

const [dir, mode, outPath, ...rest] = process.argv.slice(2);
const opt = (k: string, d?: string) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? rest[i + 1] : d; };
const track = JSON.parse(readFileSync(join(dir, 'track.json'), 'utf8')) as TrackJson;
const hf = loadHeightfield(Uint8Array.from(readFileSync(join(dir, 'heightfield.bin'))).buffer);
const sc = JSON.parse(readFileSync(join(dir, 'scenery.json'), 'utf8'));
const surf = createTrackSurface(track, hf, packageSurfaceOptions(sc, null));
const H = track.heightfield;
const rawHf = (x: number, y: number) => {
  const fx = (x - H.x0) / H.dx, fy = (y - H.y0) / H.dx, j = Math.floor(fx), i = Math.floor(fy), tx = fx - j, ty = fy - i;
  const k = i * H.nx + j, a = hf[k] + tx * (hf[k + 1] - hf[k]), b = hf[k + H.nx] + tx * (hf[k + H.nx + 1] - hf[k + H.nx]);
  return a + ty * (b - a);
};
const zones = (sc.paved_zones?.parts ?? []) as (PitLaneJson['parts'][number] & { name?: string; turn?: string })[];
const zoneSurf = zones.map((p) => createTrackSurface(track, hf, { pitLane: { spacing_m: 1, fractions: sc.paved_zones.fractions, parts: [p] } }));
const zname = (p: { name?: string; turn?: string }, i: number) => p.name ?? p.turn ?? `zone ${i}`;
const pit = sc.pit_lane?.parts ?? [];
const pitSurf = pit.length ? createTrackSurface(track, hf, { pitLane: sc.pit_lane }) : null;
const step = Number(opt('step', '0.5'));

function kindAt(x: number, y: number): { z: number; kind: string; zones: Record<string, number> } {
  const s = surf.sample(x, y);
  const z = s.z;
  let kind = s.onTrack ? 'track' : 'ground';
  const zs: Record<string, number> = {};
  zoneSurf.forEach((zsurf, i) => {
    const q = zsurf.sample(x, y);
    if (q.paved && !q.onTrack) { zs[zname(zones[i], i)] = q.z; if (kind === 'ground' && s.paved) kind = zname(zones[i], i); }
  });
  if (kind === 'ground' && s.paved && pitSurf) { const q = pitSurf.sample(x, y); if (q.paved && !q.onTrack) kind = 'pit lane'; }
  return { z, kind, zones: zs };
}

if (mode === 'profiles') {
  const S = (opt('s', '2080,2120,2160,2200,2240,2280,2320')!).split(',').map(Number);
  const [l0, l1] = (opt('lat', '-60:90')!).split(':').map(Number);
  const n = track.n, sp = track.spacing_m;
  const out: unknown[] = [];
  for (const s of S) {
    const i = Math.round(s / sp) % n, a = track.center[i], b = track.center[(i + 1) % n], c = track.center[(i - 1 + n) % n];
    let tx = b[0] - c[0], ty = b[1] - c[1];
    const L = Math.hypot(tx, ty); tx /= L; ty /= L;
    const nx = -ty, ny = tx; // + = left
    const hl = Math.hypot(track.left[i][0] - a[0], track.left[i][1] - a[1]), hr = Math.hypot(track.right[i][0] - a[0], track.right[i][1] - a[1]);
    const rows = [];
    for (let l = l0; l <= l1 + 1e-9; l += step) {
      const x = a[0] + nx * l, y = a[1] + ny * l, k = kindAt(x, y);
      rows.push({ lat: +l.toFixed(2), x: +x.toFixed(2), y: +y.toFixed(2), z: +k.z.toFixed(4), kind: k.kind, hf: +rawHf(x, y).toFixed(4), zones: k.zones });
    }
    out.push({ s, i, centre: a, half_left: hl, half_right: hr, profile_z: track.profile.z[i], rows });
  }
  writeFileSync(outPath, JSON.stringify(out));
} else if (mode === 'grid') {
  const [x0, y0, x1, y1] = opt('box')!.split(',').map(Number);
  const nx = Math.floor((x1 - x0) / step) + 1, ny = Math.floor((y1 - y0) / step) + 1;
  const z = new Array(nx * ny), kind = new Array(nx * ny), raw = new Array(nx * ny);
  const kinds: string[] = [];
  for (let r = 0; r < ny; r++) for (let c = 0; c < nx; c++) {
    const x = x0 + c * step, y = y0 + r * step, k = kindAt(x, y);
    let ki = kinds.indexOf(k.kind); if (ki < 0) { kinds.push(k.kind); ki = kinds.length - 1; }
    z[r * nx + c] = +k.z.toFixed(4); kind[r * nx + c] = ki; raw[r * nx + c] = +rawHf(x, y).toFixed(4);
  }
  writeFileSync(outPath, JSON.stringify({ x0, y0, step, nx, ny, z, kind, kinds, hf: raw }));
} else {
  console.error('mode: profiles | grid'); process.exit(2);
}
