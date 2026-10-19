"""Rebuild the track edges (track.json left/right + profile) from the painted road edge on Google satellite captures.

    uv run --offline --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib \
        python tools/track/rebuild_edges.py [--write]

Owner, 18 Oct 2026: the v2 edges (NAIP asphalt extent) sit 1-4 m outside the painted road in places, so the driveable
ribbon is too wide. Source priority for conflicts: 2026 onboard video > Google satellite > the sim's ortho.jpg.

Keeps the centre line, station numbering, corners, heightfield and ortho exactly as published. Changes only:
  - left/right edge points (half-widths per side) -> the first painted line / kerb / non-asphalt surface met going
    out from the centre along each station's normal, measured on every satellite capture covering the station
    (z19 lap tiles, z20 corner captures; tools/track/compare/satellite/), median across captures, then cleaned
    (median 9 stations, Gaussian 2 m, floors, width cap 16 m, slope limit 0.25 m per station);
    stations with no measurement keep the old edge
  - profile.z re-sampled at the new lateral positions from the DEM + lidar returns, same steps as build_laguna_v2.py
    (dem sigma 0.7, along-s gaussian, lidar_correct, clean_profile, T6 repave crest fix)
  - center/left/right z from the new profile
Writes public/tracks/laguna_seca/track.json with --write; always writes tools/track/out/edges_report.json.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, median_filter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_laguna as B  # noqa: E402
import build_laguna_v2 as V2  # noqa: E402

SAT = os.path.join(HERE, 'compare', 'satellite')
R_EARTH, LAT0, LON0 = 6378137.0, 36.5843, -121.7535
COSL = math.cos(math.radians(LAT0))
def ll2xy(lat, lon): return math.radians(lon - LON0) * R_EARTH * COSL, math.radians(lat - LAT0) * R_EARTH

def captures(C):
    """(image array, centre x, y, metres per image px, mask) for every saved Google capture."""
    out = []
    tiles = json.load(open(os.path.join(SAT, 'tiles.json')))
    for t in tiles:                                    # z19, 1210x633 (0.8 of a 1512x791 screenshot)
        im = np.asarray(Image.open(os.path.join(SAT, t['name'] + '_google.jpg')).convert('RGB')).astype(np.int16)
        m = np.ones(im.shape[:2], bool); m[:410, :335] = False; m[:45, :] = False; m[:, :55] = False
        m[540:, 1090:] = False; m[590:, 560:] = False; m[555:, 60:125] = False
        out.append((im, t['x'], t['y'], 0.23984 * 1710 / 1210, m))
    for name, s in (('T1', 232), ('T2', 479), ('T3', 785), ('T4', 1061), ('T11', 3257)):   # z20, 907x475
        im = np.asarray(Image.open(os.path.join(SAT, name + '_google.jpg')).convert('RGB')).astype(np.int16)
        m = np.ones(im.shape[:2], bool); m[:300, :250] = False; m[:30, :] = False; m[:, :40] = False; m[400:, 860:] = False; m[455:, :] = False
        out.append((im, C[s, 0], C[s, 1], 0.11992 * 1710 / 907, m))
    z20 = {'T3': (36.584772, -121.756803), 'T4': (36.584317, -121.754001), 'T5': (36.580070, -121.754096),
           'T6': (36.580476, -121.749958), 'T7': (36.584140, -121.749089), 'T8': (36.584968, -121.749289),
           'T9': (36.586823, -121.750229), 'T10': (36.586544, -121.752641)}
    for name, (la, lo) in z20.items():                 # z20, 1512x791
        p = os.path.join(SAT, f'z20_{name}_google.jpg')
        if not os.path.exists(p): continue
        im = np.asarray(Image.open(p).convert('RGB')).astype(np.int16)
        m = np.ones(im.shape[:2], bool); m[:500, :415] = False; m[:52, :] = False; m[:, :66] = False; m[650:, 1450:] = False; m[770:, :] = False; m[690:, 70:160] = False
        x, y = ll2xy(la, lo)
        out.append((im, x, y, 0.11992 * 1710 / 1512, m))
    return out

def classify(px):
    """1 = asphalt (grey, low saturation, mid brightness, or dark), 0 = anything else (paint, kerb, dirt, verge)."""
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    grey = (mx - mn < 24) & (mx < 200)
    return grey | (mx < 70)

def measure(C, nl, caps, reach=14.0, step=0.1, gap=0.1, core=1.5):
    """Per station: the asphalt band across the section (-reach..+reach, + = left) that contains the most asphalt
    within `core` m of the centre line, bridging non-asphalt gaps up to `gap` m (tyre marks, labels, seams). Its two
    ends are the painted edges (paint, kerb and runoff are not asphalt). Returns per-station lists of (left, right)
    signed lateral positions (right is negative when the edge lies to the right of the centre line)."""
    n = len(C); lats = np.arange(-reach, reach + 1e-6, step); g = int(round(gap / step))
    meas = [[] for _ in range(n)]
    X = C[:, 0:1] + lats[None, :] * nl[:, 0:1]; Y = C[:, 1:2] + lats[None, :] * nl[:, 1:2]
    for im, cx, cy, mpp, mask in caps:
        H, W = mask.shape
        px = np.round(W / 2 + (X - cx) / mpp).astype(int); py = np.round(H / 2 - (Y - cy) / mpp).astype(int)
        inside = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        for i in np.where(inside.all(1))[0]:
            if not mask[py[i], px[i]].all(): continue
            pxv = im[py[i], px[i]]
            road = classify(pxv)
            # painted lines are narrow (0.12 m) and smear into a lighter-than-asphalt pixel at z19; pale paved runoff is
            # also lighter than the racing surface: anything clearly brighter than this section's own asphalt is not road
            br = pxv.mean(1); cen0 = np.abs(lats) <= core
            if road[cen0].mean() < 0.5: continue
            ref = np.median(br[cen0 & road])
            road = (road & (br < ref + 22)).astype(int)
            # bridge short non-asphalt gaps
            r = road.copy(); k = 0
            while k < len(r):
                if r[k] == 0:
                    j = k
                    while j < len(r) and r[j] == 0: j += 1
                    if 0 < k and j < len(r) and j - k <= g: r[k:j] = 1
                    k = j
                else: k += 1
            # runs of asphalt
            runs = []; k = 0
            while k < len(r):
                if r[k]:
                    j = k
                    while j < len(r) and r[j]: j += 1
                    runs.append((k, j - 1)); k = j
                else: k += 1
            if not runs: continue
            cen = np.abs(lats) <= core
            best = max(runs, key=lambda ab: (r[ab[0]:ab[1] + 1] * cen[ab[0]:ab[1] + 1]).sum() * 1000 + (ab[1] - ab[0]))
            if (cen[best[0]:best[1] + 1]).sum() == 0: continue
            a, b = lats[best[0]], lats[best[1]]
            if b - a < 6.0 or b - a > 20.0: continue        # not a plausible road section
            if best[0] == 0 or best[1] == len(lats) - 1: continue   # ran off the sampled reach: no edge seen
            meas[i].append((b, a))
    return meas

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true'); args = ap.parse_args()
    tp = os.path.join(B.OUT, 'track.json'); T = json.load(open(tp))
    C3 = np.array(T['center']); C = C3[:, :2]; n = len(C)
    nl = B.left_normals(C)
    Lp0 = np.array(T['left'])[:, :2]; Rp0 = np.array(T['right'])[:, :2]
    hl0 = ((Lp0 - C) * nl).sum(1); hr0 = -((Rp0 - C) * nl).sum(1)
    caps = captures(C)
    meas = measure(C, nl, caps)
    raw = np.full((n, 2), np.nan); cnt = np.zeros((n, 2), int)
    for i in range(n):
        if meas[i]:
            a = np.array(meas[i]); raw[i, 0] = np.median(a[:, 0]); raw[i, 1] = -np.median(a[:, 1]); cnt[i] = len(a)
    old = np.c_[hl0, hr0]
    have = np.isfinite(raw)
    filled = np.where(have, raw, old)
    # floors: (1) the racing line (ghosts.json, from the team's logged laps) plus 1.2 m stays on the road: where the
    # painted inner edge is at or past the centre line (T1, T6, T8, T9, T11 apexes) the GPS-derived centre/line and
    # the imagery disagree by 2-3 m and the centre line is fixed, so the line wins there (flagged in the report);
    # (2) where a pit-lane part touches the track edge (merge/split, pit straight) the old edge is kept so the lane
    # stays connected; (3) at least 2 m each side
    G = json.load(open(os.path.join(B.OUT, 'ghosts.json')))
    off = np.interp(np.arange(n), np.arange(len(G['line']['offset_m'])) * G['s_grid_m'], G['line']['offset_m'], period=n)
    floor = np.c_[np.maximum(off + 1.2, 2.0), np.maximum(-off + 1.2, 2.0)]
    SC = json.load(open(os.path.join(B.OUT, 'scenery.json')))
    keep = np.zeros((n, 2), bool)
    from scipy.spatial import cKDTree
    kd = cKDTree(C)
    for part in (SC.get('pit_lane') or {}).get('parts', []):
        for E, gap in ((part['left'], part['gap_left']), (part['right'], part['gap_right'])):
            E = np.array(E)[:, :2]; _, ii = kd.query(E)
            latE = ((E - C[ii]) * nl[ii]).sum(1)
            for i, l, gp in zip(ii, latE, gap):
                if gp <= 0.3: keep[i, 0 if l > 0 else 1] = True
    for k in range(2):
        keep[:, k] = np.convolve(keep[:, k].astype(int), np.ones(21, int), 'same') > 0
    floor = np.where(keep, old, floor)
    filled = np.maximum(filled, floor)
    new = np.empty_like(filled)
    for k in range(2):
        new[:, k] = gaussian_filter1d(median_filter(filled[:, k], 9, mode='wrap'), 2, mode='wrap')
    new = np.maximum(new, floor)
    w = new.sum(1); new *= (np.minimum(w, 16.0) / w)[:, None]      # cap 16 m; narrow sections keep their floors
    new = np.maximum(new, floor)
    for k in range(2):                                   # slope limit 0.25 m per station by raising dips (stays >= floor)
        v = new[:, k]
        for _ in range(3):
            for i in range(1, 2 * n):
                j = i % n; v[j] = max(v[j], v[(j - 1) % n] - 0.25)
            for i in range(2 * n - 2, -1, -1):
                j = i % n; v[j] = max(v[j], v[(j + 1) % n] - 0.25)
        new[:, k] = v
    hl, hr = new[:, 0], new[:, 1]
    # profile from the DEM + lidar, as build_laguna_v2.py
    box = (T['heightfield']['x0'], T['heightfield']['y0'], T['ortho']['x1'], T['ortho']['y1'])
    dem_s = B.Dem(box, sigma=0.7); z0 = float(B.Dem(box)(C[:1, 0], C[:1, 1])[0])
    fr = np.array(B.FRACTIONS)
    lat = np.where(fr[None, :] < 0, -fr[None, :] * hl[:, None], -fr[None, :] * hr[:, None])
    PX = C[:, 0:1] + lat * nl[:, 0:1]; PY = C[:, 1:2] + lat * nl[:, 1:2]
    prof = gaussian_filter1d(dem_s(PX, PY) - z0, 1.5, axis=0, mode='wrap')
    prof = V2.lidar_correct(PX, PY, prof, z0)
    prof = V2.clean_profile(prof, lat)
    for a, b, c0, c1, why in V2.REPAVE_FIXES:
        zn, cv, rb, ra = V2.crest_fix(prof[:, 3], a, b, c0, c1)
        prof[a:b + 1] += (zn - prof[a:b + 1, 3])[:, None]
    old_prof = np.array(T['profile']['z'])
    Lp = C + hl[:, None] * nl; Rp = C - hr[:, None] * nl
    rep = {'z0_check': [z0, T['z0_navd88']], 'stations_measured': [int(have[:, 0].sum()), int(have[:, 1].sum())],
           'half_width_change_p50': [float(np.median(hl - hl0)), float(np.median(hr - hr0))],
           'centre_z_change_max': float(np.abs(prof[:, 3] - old_prof[:, 3]).max()),
           'flag_gt_4m': [int(i) for i in np.where((np.abs(hl - hl0) > 4) | (np.abs(hr - hr0) > 4))[0]],
           'line_floor_binding': [int(i) for i in np.where(((raw[:, 0] < floor[:, 0] - 0.3) | (raw[:, 1] < floor[:, 1] - 0.3)) & ~keep.any(1))[0]][::10],
           'kept_for_pit_lane': [int(keep[:, 0].sum()), int(keep[:, 1].sum())],
           'max_step': float(np.abs(np.diff(np.c_[hl, hr], axis=0)).max()),
           'width': [float(np.median(hl + hr)), float((hl + hr).min()), float((hl + hr).max())]}
    rows = {}
    for c in T['corners'] + [{'turn': 'front straight', 's': 3500}, {'turn': 'Rahal', 's': 2163}]:
        s = c['s']; rows[c.get('turn') or c['name']] = dict(s=s, hl_old=round(hl0[s], 2), hl_new=round(hl[s], 2), hr_old=round(hr0[s], 2), hr_new=round(hr[s], 2), n_meas=[int(cnt[s, 0]), int(cnt[s, 1])])
    rep['table'] = rows
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    json.dump(rep, open(os.path.join(HERE, 'out', 'edges_report.json'), 'w'), indent=1)
    np.savez(os.path.join(HERE, 'out', 'edges_arrays.npz'), hl0=hl0, hr0=hr0, hl=hl, hr=hr, raw=raw, cnt=cnt)
    print(json.dumps({k: v for k, v in rep.items() if k != 'table'}, indent=1))
    for k, v in rows.items(): print(k, v)
    if args.write:
        r3 = lambda a: np.round(a, 3).tolist()
        T['center'] = r3(np.c_[C, prof[:, 3]]); T['left'] = r3(np.c_[Lp, prof[:, 0]]); T['right'] = r3(np.c_[Rp, prof[:, -1]])
        T['profile']['z'] = r3(prof)
        T['notes']['edges'] = ('painted road edge (first painted line / kerb / non-asphalt surface from the centre) traced on '
                               'Google satellite captures, 18 Oct 2026 (tools/track/rebuild_edges.py); stations without a '
                               'capture keep the NAIP edge; profile re-sampled from the DEM + lidar returns')
        json.dump(T, open(tp, 'w'), separators=(',', ':'))
        print('wrote', tp)

if __name__ == '__main__':
    main()
