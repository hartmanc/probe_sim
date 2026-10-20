// Coverage gate of the track pipeline's stage 3 and the pit-lane gate (21 Oct 2026): the package's scenery against the
// eye-level inventory (tools/track/compare/<id>/inventory.json, tools/track/inventory/inventory.py).
//
//   COVERAGE   every inventory row of a physical kind (wall, fence, kerb, tyre wall, tyre stack, stand, station, bridge,
//              building, mast, cone line) on the lap must have a scenery object of that kind on that side within +-tol
//              (15 m) of its station, else it is MISSING; every scenery object of those kinds must have an inventory row
//              of its kind and side within +-tol of any of its points, or a capture source (a z20 capture or a Street
//              View panorama in its src), else it is UNSUPPORTED. Passes when MISSING is empty for walls, fences,
//              kerbs, tyre walls and bridges and UNSUPPORTED is empty. Also lists HEIGHT mismatches (advisory): a wall,
//              fence or tyre-wall row with a measured height whose nearest matching object differs by more than
//              max(0.3 m, 25 %).
//   PIT LANE   every pit-scope inventory row of kind wall must be declared in the config's pit_lane.walls on that side
//              (UNDECLARED) and stand in the package as a barrier within +-tol along the lane on that side (ABSENT).
//
// Pure functions over track.json, scenery.json and inventory.json; the CLI is run_coverage.ts (and run_gates.ts).
import { makeProjector, trackFrame, type SceneryLike, type TrackLike, type V2, type V3 } from './sceneryGates';
import { structureObjects } from './structuresCoverage';

export type Side = 'left' | 'right' | 'both' | 'ahead';
export interface InvRow {
  s: number; t: number | null; side: Side; kind: string; attrs: Record<string, unknown>; confidence: number;
  frame?: string; source: string; scope?: 'lap' | 'pit'; note?: string;
}
export interface Inventory { track: string; length_m: number; rows: InvRow[] }

export const PHYSICAL = ['wall', 'fence', 'kerb', 'tyre_wall', 'tyre_stack', 'stand', 'station', 'bridge', 'building', 'mast', 'cone_line'];
/** MISSING rows of these kinds fail the gate */
export const MUST_COVER = ['wall', 'fence', 'kerb', 'tyre_wall', 'bridge'];
/** how far beyond the edge an object of the kind may stand and still be "the" object a row describes (m) */
export const REACH: Record<string, number> = {
  wall: 80, fence: 80, kerb: 6, tyre_wall: 80, tyre_stack: 60, cone_line: 40, station: 80, stand: 250, building: 300, mast: 150, bridge: 30,
};
/** a src naming one of these is a capture source (a clean z20 capture, a Street View panorama, the captures index) */
export const CAPTURE_SRC = /c20_[so]\d{4}|\bz20\b|street ?view|panorama|\bpano\b/i;

export interface SceneObj {
  kind: string; side: 'left' | 'right' | 'both'; pts: { s: number; out: number; lat: number }[]; src: string; h?: number; label: string;
}

/** Every scenery object of a physical kind, with its points projected onto the lap (station s, side, distance beyond
 *  the edge). A barrier is split into one object per side it runs on; a barrier with a catch fence also yields a fence. */
export function sceneryObjects(t: TrackLike, sc: SceneryLike & Record<string, any>): SceneObj[] {
  const proj = makeProjector(t);
  const L = t.n * t.spacing_m;
  const out: SceneObj[] = [];
  const project = (P: V2[], r = 120) => P.map((p) => proj(p, r)).filter((q): q is NonNullable<typeof q> => !!q)
    .map((q) => ({ s: q.i * t.spacing_m, out: q.out, lat: q.lat }));
  const densify = (P: ArrayLike<ArrayLike<number>>, step = 2): V2[] => {
    const o: V2[] = [];
    for (let i = 0; i + 1 < P.length; i++) {
      const a = P[i], b = P[i + 1], d = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(d / step));
      for (let k = 0; k < n; k++) o.push([a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]);
    }
    if (P.length) o.push([P[P.length - 1][0], P[P.length - 1][1]]);
    return o;
  };
  const bySide = (kind: string, pts: { s: number; out: number; lat: number }[], src: string, label: string, h?: number) => {
    for (const side of ['left', 'right'] as const) {
      const q = pts.filter((p) => (side === 'left' ? p.lat > 0 : p.lat < 0));
      if (q.length) out.push({ kind, side, pts: q, src, label, h });
    }
  };
  const BKIND: Record<string, string> = { concrete: 'wall', armco: 'wall', pitwall: 'wall', wall: 'wall', tyres: 'tyre_wall', fence: 'fence' };
  (sc.barriers ?? []).forEach((b: any, k: number) => {
    const kind = BKIND[b.kind] ?? 'wall';
    const pts = project(densify(b.pts));
    const label = `barrier ${k} (${b.kind}${b.fence ? ` + ${b.fence} m fence` : ''})`;
    bySide(kind, pts, b.src ?? '', label, kind === 'fence' ? (b.h || 0) + (b.fence || 0) : b.h);
    if (b.fence > 0 && kind !== 'fence') bySide('fence', pts, b.src ?? '', label + ' catch fence', (b.h || 0) + b.fence);
  });
  for (const st of sc.kerbs?.strips ?? []) {
    const n = Math.max(1, Math.ceil(((st.s1 - st.s0 + L) % L) / 2));
    const pts = Array.from({ length: n + 1 }, (_, k) => ({ s: (st.s0 + (((st.s1 - st.s0 + L) % L) * k) / n) % L, out: 0, lat: st.side > 0 ? 1 : -1 }));
    out.push({ kind: 'kerb', side: st.side > 0 ? 'left' : 'right', pts, src: st.src ?? '', label: `kerb ${st.s0}-${st.s1}` });
  }
  for (const m of (sc.landmarks ?? []) as { kind: string; text?: string; x: number; y: number; src?: string; h?: number }[]) {
    const kind = m.kind === 'marshal' ? 'station' : m.kind === 'mast' || m.kind === 'light' ? 'mast' : m.kind === 'tyres' ? 'tyre_stack' : null;
    if (!kind) continue;
    bySide(kind, project([[m.x, m.y]], 200), m.src ?? '', `${m.kind} '${m.text ?? ''}'`, m.h);
  }
  (sc.terraces ?? []).forEach((tr: any) => {
    const P: V2[] = [];
    for (const r of [tr.rows[0], tr.rows[tr.rows.length - 1]]) if (r) P.push(r.a, r.b);
    bySide('stand', project(densify(P, 10), 300), tr.src ?? '', `terrace ${tr.name}`);
  });
  (sc.buildings ?? []).forEach((b: any, k: number) => {
    const f: V2[] = b.footprint;
    const cx = f.reduce((a, p) => a + p[0], 0) / f.length, cy = f.reduce((a, p) => a + p[1], 0) / f.length;
    bySide(b.kind === 'grandstand' ? 'stand' : 'building', project([[cx, cy], ...f], 320), b.src ?? '', `building ${k} '${b.name ?? ''}' ${b.h} m`, b.h);
  });
  structureObjects(sc.structures, project, densify, bySide);
  for (const br of sc.bridges ?? []) {
    out.push({ kind: 'bridge', side: 'both', pts: [{ s: br.s, out: 0, lat: 0 }], src: br.src ?? br.deck_src ?? '', label: `bridge ${br.id} (${br.kind}) deck ${br.deck_z}` });
  }
  const cones = [...(sc.cone_lines ?? []).map((c: any) => ({ pts: c.pts, src: c.src ?? '' })),
    ...(sc.pit_exit_cones?.pts?.length ? [{ pts: sc.pit_exit_cones.pts, src: (sc.pit_exit_cones as any).src ?? '' }] : [])];
  cones.forEach((c, k) => bySide('cone_line', project(densify(c.pts, 2), 80), c.src, `cone line ${k}`));
  return out;
}

const sdist = (a: number, b: number, L: number) => { const d = Math.abs(a - b) % L; return Math.min(d, L - d); };

/** Whether object `o` stands within `tol` of station s on `side` (and within its kind's reach beyond the edge). */
export function objectNear(o: SceneObj, s: number, side: Side, tol: number, L: number): boolean {
  if (o.kind !== 'bridge' && side !== 'both' && side !== 'ahead' && o.side !== side) return false;
  const reach = REACH[o.kind] ?? 80;
  return o.pts.some((p) => sdist(p.s, s, L) <= tol && p.out <= reach);
}

export interface MissingRow { s: number; side: Side; kind: string; t: number | null; source: string; frame?: string; what: string; h?: number }
export interface Unsupported { kind: string; side: string; label: string; s0: number; s1: number; src: string }
export interface HeightMismatch { s: number; side: Side; kind: string; row_h: number; method: string; obj_h: number; obj: string; source: string }
export interface CoverageReport {
  checked: number; skipped: number; missing: MissingRow[]; unsupported: Unsupported[]; heights: HeightMismatch[];
  objects: number; pass: boolean; missingByKind: Record<string, number>; unsupportedByKind: Record<string, number>;
}
export interface CoverageConfig { tol?: number; mustCover?: string[] }

function rowSides(r: InvRow): ('left' | 'right' | 'any')[] | null {
  if (r.side === 'ahead' && typeof r.attrs?.ahead_m !== 'number') return null;
  if (r.kind === 'bridge') return ['any'];
  if (r.side === 'left' || r.side === 'right') return [r.side];
  if (r.side === 'both') return ['left', 'right'];
  // 'ahead': checkable only with a distance ahead (attrs.ahead_m, already added to s by inventory.py)
  return typeof r.attrs?.ahead_m === 'number' ? ['any'] : null;
}

export function coverage(t: TrackLike, sc: SceneryLike & Record<string, any>, inv: Inventory, cfg: CoverageConfig = {}): CoverageReport {
  const tol = cfg.tol ?? 15, must = cfg.mustCover ?? MUST_COVER, L = t.n * t.spacing_m;
  const objs = sceneryObjects(t, sc);
  const rep: CoverageReport = { checked: 0, skipped: 0, missing: [], unsupported: [], heights: [], objects: objs.length, pass: false, missingByKind: {}, unsupportedByKind: {} };
  const rows = inv.rows.filter((r) => PHYSICAL.includes(r.kind) && (r.scope ?? 'lap') === 'lap');
  for (const r of rows) {
    const sides = rowSides(r);
    if (!sides) { rep.skipped++; continue; }
    rep.checked++;
    for (const sd of sides) {
      const near = objs.filter((o) => o.kind === r.kind && objectNear(o, r.s, sd === 'any' ? 'both' : sd, tol, L));
      if (!near.length) {
        const a = r.attrs ?? {};
        rep.missing.push({ s: r.s, side: sd === 'any' ? r.side : sd, kind: r.kind, t: r.t, source: r.source, frame: r.frame,
          what: String(a.type ?? ''), h: typeof a.h_m === 'number' ? a.h_m : undefined });
        rep.missingByKind[r.kind] = (rep.missingByKind[r.kind] ?? 0) + 1;
        continue;
      }
      const hm = r.attrs?.h_m, meth = String(r.attrs?.h_method ?? '');
      if (typeof hm === 'number' && meth && meth !== 'unmeasured' && ['wall', 'fence', 'tyre_wall'].includes(r.kind)) {
        const best = near.filter((o) => typeof o.h === 'number').sort((a, b) => Math.abs((a.h ?? 0) - hm) - Math.abs((b.h ?? 0) - hm))[0];
        if (best && Math.abs((best.h ?? 0) - hm) > Math.max(0.3, 0.25 * hm)) {
          rep.heights.push({ s: r.s, side: r.side, kind: r.kind, row_h: hm, method: meth, obj_h: best.h ?? 0, obj: best.label, source: r.source });
        }
      }
    }
  }
  const support = inv.rows.filter((r) => PHYSICAL.includes(r.kind));
  for (const o of objs) {
    const cited = CAPTURE_SRC.test(o.src);
    const byRow = support.some((r) => r.kind === o.kind && o.pts.some((p) => sdist(p.s, r.s, L) <= tol)
      && (o.kind === 'bridge' || r.side === 'both' || r.side === 'ahead' || r.side === o.side));
    if (cited || byRow) continue;
    const ss = o.pts.map((p) => p.s);
    rep.unsupported.push({ kind: o.kind, side: o.side, label: o.label, s0: Math.round(Math.min(...ss)), s1: Math.round(Math.max(...ss)), src: o.src });
    rep.unsupportedByKind[o.kind] = (rep.unsupportedByKind[o.kind] ?? 0) + 1;
  }
  rep.pass = rep.missing.every((m) => !must.includes(m.kind)) && rep.unsupported.length === 0;
  return rep;
}

/** MISSING rows grouped into runs (same kind and side, stations within 40 m) for the log. */
export function missingRuns(ms: MissingRow[], gap = 40): { kind: string; side: string; s0: number; s1: number; n: number; first: MissingRow }[] {
  const out: { kind: string; side: string; s0: number; s1: number; n: number; first: MissingRow }[] = [];
  const sorted = ms.slice().sort((a, b) => (a.kind + a.side).localeCompare(b.kind + b.side) || a.s - b.s);
  for (const m of sorted) {
    const r = out[out.length - 1];
    if (r && r.kind === m.kind && r.side === m.side && m.s - r.s1 <= gap) { r.s1 = m.s; r.n++; }
    else out.push({ kind: m.kind, side: m.side, s0: m.s, s1: m.s, n: 1, first: m });
  }
  return out;
}

// ------------------------------------------------------------------ pit lane
export interface PitWallDecl { side: 'left' | 'right'; s0: number; s1: number; h?: number; src?: string }
export interface PitReportRow { s: number; side: Side; source: string; what: string }
export interface PitLaneReport { checked: number; undeclared: PitReportRow[]; absent: PitReportRow[]; pass: boolean; lane: boolean }

/** Every pit-lane centre point with the lap station abeam it (projected onto the track) and the lane's left normal. */
function laneFrame(t: TrackLike, sc: SceneryLike & Record<string, any>) {
  const proj = makeProjector(t);
  const parts: any[] = sc.pit_lane?.parts ?? [];
  const P: { s: number; c: V2; nl: V2 }[] = [];
  for (const p of parts) {
    const C: V3[] = p.center;
    for (let i = 0; i < C.length; i++) {
      const a = C[Math.max(0, i - 1)], b = C[Math.min(C.length - 1, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      const q = proj([C[i][0], C[i][1]], 100);
      if (q) P.push({ s: q.i * t.spacing_m, c: [C[i][0], C[i][1]], nl: [-dy / l, dx / l] });
    }
  }
  return P;
}

export function pitLaneWalls(t: TrackLike, sc: SceneryLike & Record<string, any>, inv: Inventory, decl: PitWallDecl[], tol = 15, laneReach = 14): PitLaneReport {
  const L = t.n * t.spacing_m;
  const lane = laneFrame(t, sc);
  const rep: PitLaneReport = { checked: 0, undeclared: [], absent: [], pass: false, lane: lane.length > 0 };
  const rows = inv.rows.filter((r) => (r.scope ?? 'lap') === 'pit' && r.kind === 'wall' && (r.side === 'left' || r.side === 'right'));
  const inRange = (s: number, a: number, b: number) => (a <= b ? s >= a - tol && s <= b + tol : s >= a - tol || s <= b + tol);
  const bars: V2[] = [];
  for (const b of sc.barriers ?? []) for (let i = 0; i + 1 < b.pts.length; i++) {
    const p = b.pts[i], q = b.pts[i + 1], d = Math.hypot(q[0] - p[0], q[1] - p[1]), n = Math.max(1, Math.ceil(d / 1));
    for (let k = 0; k <= n; k++) bars.push([p[0] + ((q[0] - p[0]) * k) / n, p[1] + ((q[1] - p[1]) * k) / n]);
  }
  for (const r of rows) {
    rep.checked++;
    const row = { s: r.s, side: r.side, source: r.source, what: String(r.attrs?.type ?? '') };
    if (!decl.some((d) => d.side === r.side && inRange(r.s, d.s0, d.s1))) rep.undeclared.push(row);
    // in the package: a barrier point within laneReach of the lane centre, on that side, at lane points within +-tol
    const near = lane.filter((q) => sdist(q.s, r.s, L) <= tol);
    const found = near.some((q) => bars.some((b) => {
      const dx = b[0] - q.c[0], dy = b[1] - q.c[1], lat = dx * q.nl[0] + dy * q.nl[1], along = Math.abs(-dx * q.nl[1] + dy * q.nl[0]);
      return along <= 2 && Math.abs(lat) <= laneReach && (r.side === 'left' ? lat > 0 : lat < 0);
    }));
    if (!found) rep.absent.push(row);
  }
  rep.pass = rep.lane && rep.undeclared.length === 0 && rep.absent.length === 0;
  return rep;
}

export { trackFrame };
