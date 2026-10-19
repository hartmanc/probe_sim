window.scan = () => {
  const S = window.__sim, t = S.track, n = t.n, surf = S.surface;
  // station lookup (grid hash over centre points)
  const cell = 20, H = new Map();
  t.center.forEach((c, i) => { const k = `${Math.floor(c[0] / cell)},${Math.floor(c[1] / cell)}`; if (!H.has(k)) H.set(k, []); H.get(k).push(i); });
  const sAt = (x, y) => { const cx = Math.floor(x / cell), cy = Math.floor(y / cell); let b = -1, bd = 1e18;
    for (let dx = -2; dx <= 2; dx++) for (let dy = -2; dy <= 2; dy++) for (const i of H.get(`${cx + dx},${cy + dy}`) ?? []) { const d = (t.center[i][0] - x) ** 2 + (t.center[i][1] - y) ** 2; if (d < bd) { bd = d; b = i; } }
    return b; };
  const zs = (x, y) => surf.sample(x, y).z;
  const flags = [];
  const add = (surface, kind, x, y, v) => flags.push({ surface, kind, s: sAt(x, y), v: +v.toFixed(3) });
  // (1)(2) mesh vs driven surface
  const expect = { track: [0, 0], kerbs: [0.01, 0.05], edge_lines: [0.005, 0.02], pit_paint: [0.005, 0.02] };
  S.world.scene.traverse((o) => {
    if (!o.isMesh || !o.geometry) return;
    const nm = o.name;
    let ex = expect[nm];
    if (!ex && (nm.startsWith('pit_lane_') || nm.startsWith('paved_runoff_'))) ex = [0, 0];
    if (!ex) return;
    const p = o.geometry.attributes.position, idx = o.geometry.index, A = o.geometry.attributes.pgA;
    const nt = idx ? idx.count / 3 : p.count / 3;
    const V = (k) => { const j = idx ? idx.getX(k) : k; return [p.getX(j), -p.getZ(j), p.getY(j)]; };
    for (let tI = 0; tI < nt; tI++) {
      const a = V(tI * 3), b = V(tI * 3 + 1), c = V(tI * 3 + 2);
      // vertex deviations; ribbons: skip triangles that touch the terrain-stitched outer row (vertex far from surface)
      const dv = [a, b, c].map((q) => q[2] - zs(q[0], q[1]));
      const ja = idx ? idx.getX(tI * 3) : tI * 3, jb = idx ? idx.getX(tI * 3 + 1) : tI * 3 + 1, jc = idx ? idx.getX(tI * 3 + 2) : tI * 3 + 2;
      const part = A ? ((A.getX(ja) + A.getX(jb) + A.getX(jc)) === 3 ? ':road' : ':shoulder') : '';
      if ((ex[1] === 0) && dv.some((d) => Math.abs(d) > 0.05)) continue;
      for (const [u, w] of [[1 / 3, 1 / 3], [0.5, 0], [0, 0.5], [0.5, 0.5]]) {
        const x = a[0] + (b[0] - a[0]) * u + (c[0] - a[0]) * w, y = a[1] + (b[1] - a[1]) * u + (c[1] - a[1]) * w;
        const z = a[2] + (b[2] - a[2]) * u + (c[2] - a[2]) * w;
        const d = z - zs(x, y);
        const big = Math.abs(d - (d < ex[0] ? ex[0] : ex[1])) > 0.05 ? ' >5cm' : '';
        if (d < ex[0] - 0.02) add(nm + part, 'below surface' + big, x, y, d);
        else if (d > ex[1] + 0.02) add(nm + part, 'above surface' + big, x, y, d);
      }
    }
  });
  // (3) creases/steps in the driven surface itself: walk lines along s at fixed offsets beyond each edge
  for (const side of [1, -1]) for (const off of [-0.5, 0.25, 1, 2, 4, 6, 9, 13, 18]) {
    let prev = null, prevSlope = null;
    for (let i = 0; i < n; i++) {
      for (const f of [0, 0.5]) {
        const j = (i + 1) % n, e0 = side > 0 ? t.left[i] : t.right[i], e1 = side > 0 ? t.left[j] : t.right[j];
        const c0 = t.center[i], c1 = t.center[j];
        const ex0 = e0[0] + (e1[0] - e0[0]) * f, ey0 = e0[1] + (e1[1] - e0[1]) * f;
        const cx = c0[0] + (c1[0] - c0[0]) * f, cy = c0[1] + (c1[1] - c0[1]) * f;
        const l = Math.hypot(ex0 - cx, ey0 - cy) || 1;
        const x = ex0 + (ex0 - cx) / l * off, y = ey0 + (ey0 - cy) / l * off;
        const z = zs(x, y);
        if (prev) {
          const ds = Math.hypot(x - prev[0], y - prev[1]) || 0.5;
          const slope = (z - prev[2]) / ds;
          if (Math.abs(z - prev[2]) > 0.02 + 0.35 * ds) add(`surface ${side > 0 ? 'L' : 'R'}${off}`, 'step', x, y, z - prev[2]);
          if (prevSlope !== null && Math.abs(slope - prevSlope) > 0.08 * Math.max(1, ds / 0.5)) add(`surface ${side > 0 ? 'L' : 'R'}${off}`, 'kink', x, y, slope - prevSlope);
          prevSlope = slope;
        }
        prev = [x, y, z];
      }
    }
  }
  // summary: group by surface+kind into s ranges
  const groups = {};
  for (const f of flags) { const k = `${f.surface} | ${f.kind}`; (groups[k] ??= []).push(f); }
  const table = Object.entries(groups).map(([k, fs]) => {
    const ss = [...new Set(fs.map((f) => f.s))].sort((a, b) => a - b);
    const ranges = []; let r0 = ss[0], r1 = ss[0];
    for (const s of ss.slice(1)) { if (s - r1 <= 3) r1 = s; else { ranges.push([r0, r1]); r0 = r1 = s; } }
    ranges.push([r0, r1]);
    const worst = fs.reduce((m, f) => Math.max(m, Math.abs(f.v)), 0);
    return { k, n: fs.length, worst: +worst.toFixed(3), ranges: ranges.slice(0, 12).map((r) => r[0] === r[1] ? `${r[0]}` : `${r[0]}-${r[1]}`).join(' ') + (ranges.length > 12 ? ` ... (${ranges.length})` : '') };
  });
  return { total: flags.length, table };
};
'ok';
