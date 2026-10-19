"""Front straight edges as two straight lines (owner, 18-19 Oct 2026 night: "this hump on the start/finish straight ... The
painted lines are basically straight all the way down. There is pavement between the walls, but the painted outline of
the track, and the bounds of the track, are straight").

    uv run --python 3.12 --with numpy,pillow python -I tools/track/fix_front_straight_lines.py [--write]

Right edge: a straight line RANSAC-fitted (0.15 m tolerance) to every thin painted-line detection right of the track
from the end of the T11 green strip to T1 (stations --r-lo..--r-hi) on all clean and z20 captures (one common shift).
Left edge: parallel to a straight line RANSAC-fitted to the pit-wall polyline (--l-lo..--l-hi), at the median gap the
edge already keeps where it was straight (stations 3460..10). Each side: the half-width becomes the crossing of the
station normal with its line, from the station where the line meets the current edge (searched in --join windows) to
--*-end, blended in and out over --blend stations (smoothstep). Profile columns re-evaluated from each station's
cross-section quadratic (centre untouched). Afterwards: fix_front_straight.py --zone-only --write (shoulder zone to the
wall rebuilt from the new right edge).
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fit_edges_spline as F  # noqa: E402
from fix_edge_waves import quad_eval  # noqa: E402
OUT = F.OUT


def ransac(xy, tol, it=4000, seed=1, min_len=30):
    rng = np.random.default_rng(seed); best = None
    for _ in range(it):
        i, j = rng.choice(len(xy), 2, replace=False); d = xy[j] - xy[i]; l = np.linalg.norm(d)
        if l < min_len: continue
        nr = np.array([-d[1], d[0]]) / l; inl = np.abs((xy - xy[i]) @ nr) < tol
        if best is None or inl.sum() > best.sum(): best = inl
    p = xy[best]; m = p.mean(0); _, _, vt = np.linalg.svd(p - m); return m, vt[0], int(best.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r-lo', type=int, default=3385); ap.add_argument('--r-hi', type=int, default=30)
    ap.add_argument('--l-lo', type=int, default=3390); ap.add_argument('--l-hi', type=int, default=30)
    ap.add_argument('--join-r', default='3360,3400'); ap.add_argument('--join-l', default='3355,3395')
    ap.add_argument('--r-end', type=int, default=40); ap.add_argument('--l-end', type=int, default=15)
    ap.add_argument('--blend', type=int, default=12); ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n = T['n']; C, NL, hl, hr = F.geometry(T)
    span = lambda lo, hi: [k % n for k in range(lo, hi + (n if hi < lo else 0) + 1)]
    # right painted line: thin bright strips 0.3 m brighter than both sides, centre position
    ks = np.array(span(a.r_lo, a.r_hi)); U = np.arange(-3.0, 3.0, 0.04); pts = []
    for t in F.capture_list('z20,clean'):
        if np.min(np.hypot(C[ks, 0] - t['x'], C[ks, 1] - t['y'])) > 110: continue
        im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32); H, W = im.shape[:2]; mask = t['mask'](H, W)
        lat = -(hr[ks][:, None] + U[None, :]); X = C[ks, 0:1] + lat * NL[ks, 0:1]; Y = C[ks, 1:2] + lat * NL[ks, 1:2]
        px = W / 2 + (X + t['dx'] - t['x']) / F.MPP; py = H / 2 - (Y + t['dy'] - t['y']) / F.MPP
        for i in range(len(ks)):
            ok = (px[i] >= 1) & (px[i] < W - 2) & (py[i] >= 1) & (py[i] < H - 2)
            if ok.mean() < 0.9: continue
            ok &= mask[np.clip(py[i].round().astype(int), 0, H - 1), np.clip(px[i].round().astype(int), 0, W - 1)]
            v = F.bilinear(im, np.clip(px[i], 1, W - 2), np.clip(py[i], 1, H - 2)); br = v.mean(1); sat = v.max(1) - v.min(1)
            d = int(0.3 / 0.04); th = np.zeros(len(U), bool)
            th[d:-d] = (br[d:-d] - np.maximum(br[:-2 * d], br[2 * d:]) > 25) & (sat[d:-d] < 45) & ok[d:-d]
            j = 0
            while j < len(U):
                if th[j]:
                    e = j
                    while e < len(U) and th[e]: e += 1
                    pts.append(C[ks[i]] - NL[ks[i]] * (hr[ks[i]] + U[(j + e) // 2])); j = e
                else: j += 1
    rm, rd, rin = ransac(np.array(pts), 0.15)
    pw = np.array([p[:2] for b in SC['barriers'] if b['kind'] == 'pitwall' for p in b['pts']])
    kp = np.array([int(np.argmin(np.hypot(*(C - p).T))) for p in pw]); lks = set(span(a.l_lo, a.l_hi))
    wm, wd, win = ransac(pw[np.array([k in lks for k in kp])], 0.25, min_len=60)

    def cross(k, m, d, sg):
        nn = NL[k] * sg; den = nn[0] * (-d[1]) - nn[1] * (-d[0]); r = m - C[k]
        return (r[0] * (-d[1]) - r[1] * (-d[0])) / den
    gap = float(np.median([cross(k, wm, wd, 1) - hl[k] for k in span(3460, 10)]))
    tgt = {'right': lambda k: cross(k, rm, rd, -1), 'left': lambda k: cross(k, wm, wd, 1) - gap}
    print(f'right line: {rin} inliers of {len(pts)} detections; pit-wall line: {win} inliers; left edge gap to the wall line {gap:.2f} m')
    new = {}
    for side, hw, join, end in (('right', hr, a.join_r, a.r_end), ('left', hl, a.join_l, a.l_end)):
        j0, j1 = map(int, join.split(','))
        k0 = min(range(j0, j1 + 1), key=lambda k: abs(tgt[side](k % n) - hw[k % n]))
        st = span(k0, end); m_ = len(st); vals = {}
        for i, k in enumerate(st):
            d0, d1 = i, m_ - 1 - i; w = 1.0
            if d0 < a.blend: w = min(w, (d0 / a.blend) ** 2 * (3 - 2 * d0 / a.blend))
            if d1 < a.blend: w = min(w, (d1 / a.blend) ** 2 * (3 - 2 * d1 / a.blend))
            vals[k] = hw[k] + w * (tgt[side](k) - hw[k])
        ext = [st[0] - 1] + st + [(st[-1] + 1) % n]; seq = [vals.get(k, hw[k]) for k in ext]
        print(f'{side}: join at {k0}, to {end}; max move {max(abs(vals[k] - hw[k]) for k in st):.2f} m; max step {max(abs(seq[i + 1] - seq[i]) for i in range(len(seq) - 1)):.3f} m')
        print('   ' + '  '.join(f'{k}:{hw[k]:.2f}->{vals[k]:.2f}' for k in st[::12]))
        new[side] = vals
    if not a.write: print('dry run; --write to apply'); return
    fr = T['profile']['fractions']; Z = T['profile']['z']; Lp, Rp = T['left'], T['right']
    for k in set(new['left']) | set(new['right']):
        hl0, hr0 = hl[k], hr[k]; hln = new['left'].get(k, hl0); hrn = new['right'].get(k, hr0)
        xs0 = [(-g) * hl0 if g < 0 else -g * hr0 for g in fr]; xs1 = [(-g) * hln if g < 0 else -g * hrn for g in fr]
        zn = [quad_eval(xs0, Z[k], x) for x in xs1]; zn[fr.index(0)] = Z[k][fr.index(0)]; Z[k] = [round(z, 3) for z in zn]
        c = C[k]; nx, ny = NL[k]
        Lp[k] = [round(c[0] + nx * hln, 3), round(c[1] + ny * hln, 3), Z[k][0]]
        Rp[k] = [round(c[0] - nx * hrn, 3), round(c[1] - ny * hrn, 3), Z[k][-1]]
    T['notes']['front_straight_lines'] = (f'18-19 Oct 2026: fix_front_straight_lines.py: right edge on one straight line fitted to the painted line '
        f'({rin} detections), left edge parallel to the pit-wall line at {gap:.2f} m; joins {a.join_r}/{a.join_l}, ends {a.r_end}/{a.l_end}, blend {a.blend}')
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')


if __name__ == '__main__':
    sys.exit(main())
