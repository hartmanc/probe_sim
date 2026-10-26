"""Mid-Ohio round 6, T8 evidence from the package (no change to it): the centre elevation, grade and vertical curvature
over s 2380-2680, the crest, and the hood camera's sight line over it; the solver's line (offset, clearance to each race
edge, plan radius) and the centre's plan radius; the road width; the heightfield across the road around the crest
(paved run-off or an apron would show as a flat shelf level with the road beyond an edge).

    python3 -I tools/track/compare/mid_ohio/r6/t8_profile.py <package dir> <out.json>
"""
import json
import math
import os
import struct
import sys

pkg, out = sys.argv[1:3]
T = json.load(open(os.path.join(pkg, 'track.json')))
G = json.load(open(os.path.join(pkg, 'ghosts.json')))
C = T['center']; Lf = T['left']; Rt = T['right']; n = len(C); sp = T['spacing_m']; L = n * sp
off = G['line']['offset_m']; ds = G['s_grid_m']; m = len(off)
EYE = 1.1    # hood camera height over the road (m): the sim's hood camera ~1.0-1.1 m; N837's hood camera about the same
hf = T['heightfield']
raw = open(os.path.join(pkg, hf['file']), 'rb').read()
nx, ny = hf['nx'], hf['ny']
fmt = 'f' if len(raw) == 4 * nx * ny else 'e'
H = struct.unpack(f'<{nx * ny}{fmt}', raw[:nx * ny * (4 if fmt == "f" else 2)])


def hz(x, y):
    u = (x - hf['x0']) / hf['dx']; v = (y - hf['y0']) / hf['dx']
    i, j = int(u), int(v); fu, fv = u - i, v - j
    g = lambda a, b: H[b * nx + a]
    return (g(i, j) * (1 - fu) * (1 - fv) + g(i + 1, j) * fu * (1 - fv) + g(i, j + 1) * (1 - fu) * fv + g(i + 1, j + 1) * fu * fv)


def idx(s):
    return int(round(s / sp)) % n


def z(s):
    return C[idx(s)][2]


def grade(s, h=5):
    return (z(s + h) - z(s - h)) / (2 * h)


def vcurv(s, h=10):
    return (grade(s + h) - grade(s - h)) / (2 * h)


def tang(i):
    a, b = C[(i - 1) % n], C[(i + 1) % n]
    tx, ty = b[0] - a[0], b[1] - a[1]; l = math.hypot(tx, ty); return tx / l, ty / l


def halfw(i):
    tx, ty = tang(i); nx_, ny_ = -ty, tx
    hl = (Lf[i][0] - C[i][0]) * nx_ + (Lf[i][1] - C[i][1]) * ny_
    hr = -((Rt[i][0] - C[i][0]) * nx_ + (Rt[i][1] - C[i][1]) * ny_)
    return hl, hr


def line_off(s):
    u = s / ds; i = int(math.floor(u)) % m; f = u - math.floor(u)
    return (1 - f) * off[i] + f * off[(i + 1) % m]


def pt(s, e):
    i = idx(s); tx, ty = tang(i); return C[i][0] - e * ty, C[i][1] + e * tx


def radius(P, k, h=10):
    a, b, c = P[k - h], P[k], P[k + h]
    ab = math.dist(a, b); bc = math.dist(b, c); ac = math.dist(a, c)
    cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (ab * bc * ac) / (2 * cr) if abs(cr) > 1e-9 else float('inf')


S = list(range(2380, 2681, 2))
prof = []
Pc = [(C[idx(s)][0], C[idx(s)][1]) for s in range(2340, 2721)]
Pl = [pt(s, line_off(s)) for s in range(2340, 2721)]
for s in S:
    i = idx(s); hl, hr = halfw(i); e = line_off(s); k = s - 2340
    prof.append(dict(s=s, z=round(z(s), 3), grade_pct=round(100 * grade(s), 2), vcurv_per_km=round(1000 * vcurv(s), 2),
                     width=round(hl + hr, 2), half_left=round(hl, 2), half_right=round(hr, 2), line_off=round(e, 2),
                     clear_left=round(hl - e, 2), clear_right=round(hr + e, 2),
                     R_centre=round(radius(Pc, k), 1), R_line=round(radius(Pl, k), 1)))
crest = max(prof, key=lambda r: r['z'])
vmin = min(prof, key=lambda r: r['vcurv_per_km'])


def sight(s0, eye=EYE, tgt=0.0, upto=250):
    """Farthest station whose road centre (raised by tgt) is visible from an eye `eye` m over the centre at s0,
    along the centre's vertical profile (plan curvature ignored)."""
    ze = z(s0) + eye
    best = s0
    for d in range(2, upto, 1):
        st = s0 + d
        zt = z(st) + tgt
        ok = True
        for d2 in range(1, d):
            zl = ze + (zt - ze) * d2 / d
            if z(s0 + d2) > zl - 0.02:
                ok = False; break
        if ok:
            best = st
        elif tgt == 0 and st - best > 15:
            pass
    return best


sl = []
for s0 in range(crest['s'] - 100, crest['s'] + 21, 10):
    sl.append(dict(eye_s=s0, before_crest_m=crest['s'] - s0, see_road_to_s=sight(s0), see_road_m=sight(s0) - s0,
                   see_kerb_0p3_to_s=sight(s0, tgt=0.3), see_car_roof_1p3_to_s=sight(s0, tgt=1.3)))
# cross-sections: heightfield 0-12 m beyond each edge relative to the edge height (a paved shelf would be ~0 out to its end)
xs = []
for s in range(2440, 2601, 20):
    i = idx(s); tx, ty = tang(i); nx_, ny_ = -ty, tx
    row = dict(s=s)
    for side, E, sg in (('left', Lf, 1), ('right', Rt, -1)):
        ze_ = E[i][2]
        row[side] = [round(hz(E[i][0] + sg * d * nx_, E[i][1] + sg * d * ny_) - ze_, 2) for d in (0, 2, 4, 6, 8, 12)]
    xs.append(row)
res = dict(eye_m=EYE, crest=crest, max_convex=vmin, vertical_radius_at_crest_m=round(-1000 / crest['vcurv_per_km'], 0) if crest['vcurv_per_km'] < 0 else None,
           sight_lines=sl, cross_sections_beyond_edge_m=dict(offsets_m=[0, 2, 4, 6, 8, 12], rows=xs), profile=prof)
json.dump(res, open(out, 'w'), indent=1)
print('crest', crest)
print('strongest convexity', vmin, 'R_v', round(-1000 / vmin['vcurv_per_km']))
for r in prof[::5]:
    print(r)
for r in sl:
    print(r)
for r in xs:
    print(r)
