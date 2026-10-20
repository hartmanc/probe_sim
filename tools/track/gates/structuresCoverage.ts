// Structures (src/app/structures.ts, scenery.json `structures`) as coverage-gate objects (21 Oct 2026): a grandstand is a
// stand (its front line and back corners), a garage / block / fuel island a building (centre and corners), each light
// mast a mast, a fence a fence. Paint, boards and terrace dressing are not inventory kinds.
type V2 = [number, number];
type Pt = { s: number; out: number; lat: number };
type BySide = (kind: string, pts: Pt[], src: string, label: string, h?: number) => void;

export function structureObjects(list: any[] | undefined, project: (P: V2[], r?: number) => Pt[], densify: (P: ArrayLike<ArrayLike<number>>, step?: number) => V2[], bySide: BySide): void {
  for (const [k, st] of (list ?? []).entries()) {
    const label = `structure ${k} ${st.type} '${st.name ?? ''}'`;
    if (st.type === 'grandstand') {
      const fp: V2[] = st.collide?.[0]?.footprint ?? [st.a, st.b];
      bySide('stand', project(densify([st.a, st.b], 10), 320).concat(project(fp, 320)), st.src ?? '', label);
      // the light clusters on the deck roof are light masts seen from the track
      const L = Math.hypot(st.b[0] - st.a[0], st.b[1] - st.a[1]), su = st.suites;
      if (su?.lights && L > 0) for (const t of su.lights.t) {
        const d = su.d0 + (su.d1 - su.d0) * su.roof[3] * 0.5;
        const x = st.a[0] + ((st.b[0] - st.a[0]) / L) * t + st.dir[0] * d, y = st.a[1] + ((st.b[1] - st.a[1]) / L) * t + st.dir[1] * d;
        bySide('mast', project([[x, y]], 200), st.src ?? '', `${label} roof light at t ${t}`, su.roof[0] + su.lights.h);
      }
    } else if (st.type === 'garage' || st.type === 'block' || st.type === 'fuel') {
      const fp: V2[] = st.collide?.[0]?.footprint ?? [];
      const h = st.type === 'garage' ? Math.max(st.eave, st.ridge) : st.type === 'block' ? st.h : st.h + st.fascia;
      bySide('building', project([st.c, ...fp], 320), st.src ?? '', label, h);
    } else if (st.type === 'mast') {
      for (const a of st.at ?? []) bySide('mast', project([[a[0], a[1]]], 200), st.src ?? '', `${label} at (${a[0]}, ${a[1]})`, st.h);
    } else if (st.type === 'fence') {
      bySide('fence', project(densify(st.pts, 2)), st.src ?? '', label, st.h);
    }
  }
}
