"""After tools/track/rebuild_from_paint.py --write: keep scenery.json on the same world positions on the new track.

    uv run --python 3.12 --with numpy,scipy python tools/track/remap_scenery.py OLD_TRACK_JSON

- every station-keyed range (kerb/verge strips, sausages, edge-line runs, pit-exit cones, bridges, pit-lane and
  paved-zone track_s) is remapped old station -> new station through tools/track/out/station_map_u.npy (old station k
  sits at new fractional station u[k]), so it keeps its cross-section; the report lists the shift in metres and the
  world distance between the old and new anchor points (should be < 2 m);
- verge `inset` -> 0 (the new edge is the painted line);
- paved zones: the track-side edge follows the new track edge (outer edge kept), cross-profile re-sampled from the old
  one, gap to the track recomputed; pit-lane gaps recomputed against the new edges.
"""
import json, math, os, sys
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
TP = os.path.join(ROOT, 'public/tracks/laguna_seca/track.json'); SP = os.path.join(ROOT, 'public/tracks/laguna_seca/scenery.json')
T = json.load(open(TP)); T0 = json.load(open(sys.argv[1])); S = json.loads(open(SP).read())
u = np.load(os.path.join(HERE, 'out', 'station_map_u.npy')); n = len(u); SPm = float(T['spacing_m'])
assert float(T0.get('spacing_m', 1.0)) == 1.0, 'old track must have 1 m stations (s = station)'
C = np.array(T['center']); C0 = np.array(T0['center'])
def frame(P):
    t = np.roll(P[:, :2], -1, 0) - np.roll(P[:, :2], 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); return np.c_[-t[:, 1], t[:, 0]]
NL = frame(C); Lw = np.array(T['left']); Rw = np.array(T['right'])
hl = ((Lw[:, :2] - C[:, :2]) * NL).sum(1); hr = -((Rw[:, :2] - C[:, :2]) * NL).sum(1)
kd = cKDTree(C[:, :2])
def smap(s):  # old station (may exceed n for wrapped ranges) -> new station
    k, r = divmod(float(s), n)
    return k * n + float(np.interp(r, np.arange(n + 1), np.r_[u, n]))
TG = np.roll(C[:, :2], -1, 0) - C[:, :2]; SEG = np.linalg.norm(TG, axis=1); TG = TG / SEG[:, None]
def world_err(s_old, s_new):
    """along-track distance (m) between the old anchor's cross-section and the remapped station: project the old
    centre point onto the new centre line (the centre moved sideways, so the lateral part is not an error)"""
    a = C0[int(round(s_old)) % n, :2]; _, i = kd.query(a)
    best = None
    for j in ((i - 1) % n, i):
        t = np.dot(a - C[j, :2], TG[j]) / SEG[j]
        if -0.05 <= t <= 1.05: best = j + t
    if best is None: best = i
    d = (best - s_new + n / 2) % n - n / 2 + (s_new - round(s_new) if False else 0)
    return float(abs(((best - (s_new % n)) + n / 2) % n - n / 2) * T['spacing_m'])
rep = []
def remap(obj, keys, label, as_int=True):
    for k in keys:
        if k in obj:
            o = obj[k]; nv = smap(o)                  # new station
            obj[k] = round(nv * SPm, 1)               # s fields are metres: station * spacing_m
            rep.append((label, k, o, obj[k], round(world_err(o, nv), 2)))
for st in S['kerbs']['strips']:
    remap(st, ('s0', 's1'), 'kerb:' + st.get('kind', ''))
    if st.get('kind') == 'verge' and 'inset' in st: st['inset'] = 0.0
for st in S['sausages']['strips']: remap(st, ('s0', 's1'), 'sausage:' + st.get('corner', ''))
for r in S['edge_lines']['runs']: remap(r, ('s0', 's1'), 'edge_line')
remap(S['pit_exit_cones'], ('s0', 's1'), 'pit_exit_cones')
for b in S['bridges']: remap(b, ('s',), 'bridge:' + b.get('id', ''))
def project(P):
    _, i = kd.query(P[:, :2]); lat = ((P[:, :2] - C[i, :2]) * NL[i]).sum(1)
    out = np.where(lat > 0, lat - hl[i], -lat - hr[i])
    return i, lat, out
for grp in ('pit_lane', 'paved_zones'):
    for p in (S.get(grp) or {}).get('parts', []):
        ts = p['track_s']; p['track_s'] = [round((smap(ts[0]) % n) * SPm, 1), round((smap(ts[1]) % n) * SPm, 1)]
        rep.append((grp, 'track_s', ts, p['track_s'], None))
        L = np.array(p['left']); R = np.array(p['right'])
        if grp == 'paved_zones':
            inner_left = p['gap_left'][0] == 0
            prof = np.array(p['profile_z']); fr = np.array(S['paved_zones']['fractions'])
            E = L if inner_left else R
            i, lat, _ = project(E)
            side = np.sign(lat)
            edge = np.where(side > 0, hl[i], -hr[i])
            newE = C[i, :2] + edge[:, None] * NL[i]
            ez = np.where(side > 0, Lw[i, 2], Rw[i, 2])
            O = R if inner_left else L
            newP, newL, newR = [], [], []
            for j in range(len(E)):
                a, b = newE[j], O[j, :2]               # new track-side edge, kept outer edge
                old_a, old_b = E[j, :2], O[j, :2]
                span = np.linalg.norm(old_b - old_a) or 1e-6
                row = []
                for f in fr:
                    q = (f + 1) / 2 if not inner_left else (f + 1) / 2
                    # world point at fraction f across the new section (f=-1 left, +1 right)
                    pl, pr = (a, b) if inner_left else (b, a)
                    w = pl + (pr - pl) * (f + 1) / 2
                    # its fraction in the old section, measured from the old left edge
                    ol, orr = (old_a, old_b) if inner_left else (old_b, old_a)
                    t_ = np.dot(w - ol, orr - ol) / max(np.dot(orr - ol, orr - ol), 1e-9)
                    fo = 2 * t_ - 1
                    if (inner_left and fo < -1) or (not inner_left and fo > 1):   # beyond the old inner edge: on the track edge
                        row.append(float(ez[j]))
                    else:
                        row.append(float(np.interp(fo, fr, prof[j])))
                newP.append(row)
                pl, pr = (a, b) if inner_left else (b, a)
                newL.append([pl[0], pl[1], row[0]]); newR.append([pr[0], pr[1], row[-1]])
            newP = np.array(newP); newL = np.array(newL); newR = np.array(newR)
            # the track-side edge comes from per-point nearest-station snaps: smooth along the zone (no 1 m kinks)
            from scipy.ndimage import gaussian_filter1d as gf
            newP = gf(newP, 2.0, axis=0, mode='nearest'); newL = gf(newL, 2.0, axis=0, mode='nearest'); newR = gf(newR, 2.0, axis=0, mode='nearest')
            newL[:, 2] = newP[:, 0]; newR[:, 2] = newP[:, -1]
            cen = (newL + newR) / 2; cen[:, 2] = newP[:, len(fr) // 2]
            r3 = lambda a: [[round(float(v[0]), 2), round(float(v[1]), 2), round(float(v[2]), 3)] for v in a]
            p['left'], p['right'], p['center'] = r3(newL), r3(newR), r3(cen)
            p['profile_z'] = [[round(float(x), 3) for x in r] for r in newP]
            if inner_left: p['gap_left'] = [0.0] * len(newL)
            else: p['gap_right'] = [0.0] * len(newR)
        else:
            _, _, dl = project(L); _, _, dr = project(R)
            p['gap_left'] = [round(float(max(0.0, v)), 2) for v in dl]; p['gap_right'] = [round(float(max(0.0, v)), 2) for v in dr]
# the edge now runs along the kerbs' outer line (kerbs inside the edge): sausages sit `gap` m behind the kerb
S['sausages']['kerb_width'] = 0.0
open(SP, 'w').write(json.dumps(S, separators=(',', ':'), ensure_ascii=False))
big = [r for r in rep if r[4] is not None and r[4] > 2]
shift = [abs(r[3] - r[2]) for r in rep if isinstance(r[2], (int, float))]
print('remapped', len(rep), 'anchors; max station shift', max(shift), '; anchors more than 2 m along-track from their old cross-section:', len(big))
for r in big: print('  ', r)
json.dump(rep, open(os.path.join(HERE, 'out', 'remap_report.json'), 'w'), indent=0, default=str)
