// Synthetic development track: a flat 1.5 km stadium oval (CCW) with a hill on
// the back straight. Produces a valid track.json object plus its heightfield,
// used when the track package's track.json is missing.
// Also: a procedural "ortho" canvas for any track whose ortho.jpg is missing,
// and a flat heightfield for a track whose heightfield.bin is missing.
import type { TrackJson, Vec3 } from './physics-types';

const LENGTH = 1500;
const R = 100;
const STRAIGHT = (LENGTH - 2 * Math.PI * R) / 2; // ≈ 435.8 m
const HALF_W = 6;

function hill(x: number, y: number): number {
  return 9 * Math.exp(-(x * x) / (2 * 140 * 140) - ((y - R) ** 2) / (2 * 110 * 110)) + 0.004 * x;
}

/** Centre point and unit tangent at distance s (CCW, s = 0 mid bottom straight heading east). */
function centreAt(s: number): { p: [number, number]; t: [number, number] } {
  const h = STRAIGHT / 2;
  const arc = Math.PI * R;
  let u = ((s % LENGTH) + LENGTH) % LENGTH;
  if (u < h) return { p: [u, -R], t: [1, 0] };
  u -= h;
  if (u < arc) { // right semicircle, centre (h, 0)
    const a = -Math.PI / 2 + u / R;
    return { p: [h + R * Math.cos(a), R * Math.sin(a)], t: [-Math.sin(a), Math.cos(a)] };
  }
  u -= arc;
  if (u < STRAIGHT) return { p: [h - u, R], t: [-1, 0] };
  u -= STRAIGHT;
  if (u < arc) { // left semicircle, centre (-h, 0)
    const a = Math.PI / 2 + u / R;
    return { p: [-h + R * Math.cos(a), R * Math.sin(a)], t: [-Math.sin(a), Math.cos(a)] };
  }
  u -= arc;
  return { p: [-h + u, -R], t: [1, 0] };
}

export function makeDevTrack(): { track: TrackJson; heightfield: Float32Array } {
  const n = LENGTH;
  const fractions = [-1, -0.6667, -0.3333, 0, 0.3333, 0.6667, 1];
  const center: Vec3[] = [], left: Vec3[] = [], right: Vec3[] = [], prof: number[][] = [];
  for (let i = 0; i < n; i++) {
    const { p, t } = centreAt(i);
    const nx = -t[1], ny = t[0];
    const row = fractions.map((f) => {
      const off = -f * HALF_W; // +left
      return hill(p[0] + nx * off, p[1] + ny * off) + 0.08 * (1 - f * f) + 0.12;
    });
    prof.push(row);
    center.push([p[0], p[1], row[3]]);
    left.push([p[0] + nx * HALF_W, p[1] + ny * HALF_W, row[0]]);
    right.push([p[0] - nx * HALF_W, p[1] - ny * HALF_W, row[6]]);
  }
  const margin = 160, dx = 2;
  const x0 = -STRAIGHT / 2 - R - margin, y0 = -R - margin;
  const nx = Math.ceil((STRAIGHT + 2 * R + 2 * margin) / dx) + 1;
  const ny = Math.ceil((2 * R + 2 * margin) / dx) + 1;
  const heightfield = new Float32Array(nx * ny);
  for (let i = 0; i < ny; i++) for (let j = 0; j < nx; j++) heightfield[i * nx + j] = hill(x0 + j * dx, y0 + i * dx);
  const x1 = x0 + (nx - 1) * dx, y1 = y0 + (ny - 1) * dx;
  const h = STRAIGHT / 2, arc = Math.PI * R;
  const track: TrackJson = {
    name: 'Dev Oval (synthetic)',
    origin: { lat: 36.5843, lon: -121.7535 },
    z0_navd88: 230,
    direction: 'ccw',
    spacing_m: 1,
    n,
    length_m: LENGTH,
    center, left, right,
    profile: { fractions, z: prof },
    start_finish: { index: 0 },
    corners: [
      { name: 'East Hairpin', s: h + arc / 2 },
      { name: 'Hill Crest', s: h + arc + STRAIGHT / 2 },
      { name: 'West Hairpin', s: h + arc + STRAIGHT + arc / 2 },
    ],
    heightfield: { file: 'heightfield.bin', x0, y0, dx, nx, ny },
    ortho: { file: 'ortho.jpg', x0, y0, x1, y1, width_px: 2048, height_px: Math.round(2048 * (y1 - y0) / (x1 - x0)) },
    sources: 'synthetic',
  };
  return { track, heightfield };
}

/** Flat heightfield under a track whose heightfield.bin is missing. */
export function makeFlatHeightfield(track: TrackJson): Float32Array {
  let zmin = Infinity;
  for (const c of track.center) zmin = Math.min(zmin, c[2]);
  return new Float32Array(track.heightfield.nx * track.heightfield.ny).fill(zmin - 0.5);
}

/** Procedural aerial image: grass, run-off and asphalt drawn from the track edges. */
export function makeOrthoCanvas(track: TrackJson): HTMLCanvasElement {
  const o = track.ortho;
  const W = 2048;
  const H = Math.max(64, Math.round(W * (o.y1 - o.y0) / (o.x1 - o.x0)));
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d')!;
  const px = (x: number) => (x - o.x0) / (o.x1 - o.x0) * W;
  const py = (y: number) => (o.y1 - y) / (o.y1 - o.y0) * H; // north up
  const mpp = (o.x1 - o.x0) / W;
  g.fillStyle = '#6f7f45';
  g.fillRect(0, 0, W, H);
  // mottled grass
  for (let k = 0; k < 9000; k++) {
    g.fillStyle = Math.random() < 0.5 ? 'rgba(90,105,55,0.35)' : 'rgba(140,140,85,0.25)';
    const r = 2 + Math.random() * 10;
    g.beginPath(); g.arc(Math.random() * W, Math.random() * H, r, 0, Math.PI * 2); g.fill();
  }
  const strokeLine = (pts: Vec3[], color: string, widthM: number) => {
    g.strokeStyle = color; g.lineWidth = Math.max(1, widthM / mpp); g.lineJoin = 'round';
    g.beginPath();
    pts.forEach((p, i) => (i ? g.lineTo(px(p[0]), py(p[1])) : g.moveTo(px(p[0]), py(p[1]))));
    g.closePath(); g.stroke();
  };
  // run-off (sand/dirt) then asphalt polygon
  let w = 0;
  for (let i = 0; i < track.n; i += 10) w += Math.hypot(track.left[i][0] - track.right[i][0], track.left[i][1] - track.right[i][1]);
  w /= Math.ceil(track.n / 10);
  strokeLine(track.center, '#b8a77c', w + 10);
  strokeLine(track.center, '#55575a', w);
  strokeLine(track.left, '#d8d8d0', 0.25);
  strokeLine(track.right, '#d8d8d0', 0.25);
  return cv;
}
