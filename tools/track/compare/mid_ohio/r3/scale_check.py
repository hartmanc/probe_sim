"""Mid-Ohio round 3, the scale check (Astra review item 5): is the course's scale right, independently of cfg.enu?
Three measures, each a scale factor with its uncertainty:
 A. capture placement vs NAIP over long baselines (both axes): each clean capture's registration against the NAIP ortho
    (satellite_clean/shift.json per_capture, phase correlation, peak >= 8) regressed on the capture's position: a scale
    error s of the capture pipeline puts features at (1 + s) x, so the shift grows as s * x (and s * y). Google and NAIP
    are georeferenced independently; the ortho and the captures both pass through cfg.enu, which cancels here.
 B. within-capture scale (the mpp; too noisy against the 0.6 m NAIP, printed only): each capture's two halves (east / west, then north / south) correlated against the
    NAIP ortho separately (edge maps at 0.15 m, sub-pixel peak); the difference of the halves' shifts over the distance
    between their centres is mpp's scale error on that axis.
 B2. within-capture scale (the mpp) from overlapping captures against each other at full resolution: a scale error s
    shows as a shift s * delta between two captures delta apart (the decisive mpp test; it checks mpp against the
    captures' own lat/lon placement, so its absolute reference is A's NAIP comparison).
 C. cfg.enu against the WGS84 ellipsoid: the round-3 centre and edges taken back to lat/lon (the exact inverse of
    cfg.enu) and measured geodesically (pyproj.Geod), per axis and for the lap.
Reads local caches and the round-3 package; prints; writes nothing."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import trackcfg  # noqa
cfg = trackcfg.load('mid_ohio'); cc = cfg['captures']; MPP = cc['mpp']
D = cfg.path(cc['clean_dir'])
tiles = {t['name']: t for t in json.load(open(os.path.join(D, cc['clean_index'])))}
shift = json.load(open(os.path.join(D, 'shift.json')))
PKG = os.path.join(ROOT, 'tools/track/out/mid_ohio_r3')
T = json.load(open(os.path.join(PKG, 'track.json'))); O = T['ortho']


def ols(x, y):
    X = np.c_[np.ones_like(x), x]; b, res, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b; s2 = (r @ r) / max(len(x) - 2, 1); cov = s2 * np.linalg.inv(X.T @ X)
    return b[1], math.sqrt(cov[1, 1]), float(np.sqrt(s2))


print('## A. Capture placement vs NAIP, long baselines')
pc = shift['per_capture']
rows = [(tiles[k]['x'], tiles[k]['y'], v[0], v[1]) for k, v in pc.items() if v[2] >= 8]
x, y, dx, dy = (np.array(c) for c in zip(*rows))
print(f"{len(rows)} of {len(pc)} captures (peak >= 8); extent x {x.min():.0f}..{x.max():.0f} m ({x.max() - x.min():.0f} m), "
      f"y {y.min():.0f}..{y.max():.0f} m ({y.max() - y.min():.0f} m)")
sx, ex, rx = ols(x, dx); sy, ey, ry = ols(y, dy)
print(f"east:  scale 1 {sx * 100:+.4f} % +- {ex * 100:.4f} % (1 sigma; residual {rx:.2f} m)")
print(f"north: scale 1 {sy * 100:+.4f} % +- {ey * 100:.4f} % (1 sigma; residual {ry:.2f} m)")
# the longest baselines directly: pairs > 600 m apart, (|p_capture_i - p_capture_j| / |p_i - p_j|) - 1
P = np.c_[x, y]; Dd = np.c_[dx, dy]
i, j = np.triu_indices(len(P), 1); L = np.linalg.norm(P[i] - P[j], axis=1); far = L > 600
ratio = (np.linalg.norm((P[i] + Dd[i]) - (P[j] + Dd[j]), axis=1) / L)[far] - 1
print(f"pairs > 600 m apart: {far.sum()}, length ratio - 1: median {np.median(ratio) * 100:+.4f} %, p5 {np.percentile(ratio, 5) * 100:+.4f} %, p95 {np.percentile(ratio, 95) * 100:+.4f} %")

print('\n## B. Within-capture scale (mpp), halves against NAIP (0.6 m imagery: too coarse for 38-75 m baselines; printed, not used)')
ORT = Image.open(os.path.join(PKG, 'work', 'ortho.jpg')).convert('L')
mx = (O['x1'] - O['x0']) / O['width_px']; my = (O['y1'] - O['y0']) / O['height_px']
S = 0.15
PEAK_B = float(os.environ.get("PEAK_B", "5"))   # the halves correlate weaker than a whole capture


def edges(a):
    b = np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)).filter(ImageFilter.FIND_EDGES), float)
    return (b - b.mean()) / (b.std() + 1e-6)


def corr(g, wx0, wy1, ww, wh):
    """the capture region (world box top-left wx0, wy1, size ww x wh m) against the ortho: (dx, dy, peak), sub-pixel"""
    W, H = int(ww / S), int(wh / S)
    Ga = np.asarray(g.resize((W, H)), float)
    px0 = (wx0 - O['x0']) / mx; py0 = (O['y1'] - wy1) / my
    Oa = np.asarray(ORT.crop((int(round(px0)), int(round(py0)), int(round(px0 + ww / mx)), int(round(py0 + wh / my)))).resize((W, H), Image.BILINEAR), float)
    # the crop's rounding offset (world m) is added back
    ox = (int(round(px0)) - px0) * mx; oy = -(int(round(py0)) - py0) * my
    w = np.outer(np.hanning(H), np.hanning(W))
    F = np.fft.fft2(edges(Ga) * w) * np.conj(np.fft.fft2(edges(Oa) * w)); r = np.fft.ifft2(F / (np.abs(F) + 1e-6)).real
    iy, ix = np.unravel_index(r.argmax(), r.shape)
    def sub(a_m, a0, a_p):
        den = a_m - 2 * a0 + a_p
        return 0.0 if den == 0 else 0.5 * (a_m - a_p) / den
    fx = sub(r[iy, ix - 1], r[iy, ix], r[iy, (ix + 1) % W]); fy = sub(r[iy - 1, ix], r[iy, ix], r[(iy + 1) % H, ix])
    if iy > H // 2: iy -= H
    if ix > W // 2: ix -= W
    return (ix + fx) * S - ox, -(iy + fy) * S - oy, r.max() / r.std()


ex_, ny_ = [], []
for name, t in tiles.items():
    if pc.get(name, [0, 0, 0])[2] < 8:
        continue
    g = Image.open(os.path.join(D, name + '_google.jpg')).convert('L'); Wp, Hp = g.size
    cx, cy = t['x'], t['y']; ww, wh = Wp * MPP, Hp * MPP
    # crop margins (the clean captures' page chrome is hidden, but keep 4 % off every border)
    m = 0.04
    halves = {}
    for nm, (a0, a1, b0, b1) in {'W': (m, 0.5, m, 1 - m), 'E': (0.5, 1 - m, m, 1 - m), 'N': (m, 1 - m, m, 0.5), 'S': (m, 1 - m, 0.5, 1 - m)}.items():
        crop = g.crop((int(a0 * Wp), int(b0 * Hp), int(a1 * Wp), int(b1 * Hp)))
        wx0 = cx - ww / 2 + a0 * ww; wy1 = cy + wh / 2 - b0 * wh
        halves[nm] = corr(crop, wx0, wy1, (a1 - a0) * ww, (b1 - b0) * wh) + (((a0 + a1) / 2 - 0.5) * ww, (0.5 - (b0 + b1) / 2) * wh)
    if min(h[2] for h in halves.values()) < PEAK_B:
        continue
    bx = halves['E'][3] - halves['W'][3]; by = halves['N'][4] - halves['S'][4]
    ex_.append((halves['E'][0] - halves['W'][0]) / bx); ny_.append((halves['N'][1] - halves['S'][1]) / by)
ex_, ny_ = np.array(ex_), np.array(ny_)
for nm, v, b in (('east (E-W halves, baseline %.0f m)' % (0.46 * 1440 * MPP), ex_, 0), ('north (N-S halves, baseline %.0f m)' % (0.46 * 725 * MPP), ny_, 0)):
    med = np.median(v); mad = 1.4826 * np.median(np.abs(v - med)); se = mad / math.sqrt(len(v))
    print(f"{nm}: {len(v)} captures, scale 1 {med * 100:+.3f} % +- {se * 100:.3f} % (median, 1 sigma from MAD; spread p10..p90 {np.percentile(v, 10) * 100:+.2f}..{np.percentile(v, 90) * 100:+.2f} %)")

print('\n## B2. Within-capture scale (mpp), overlapping captures against each other (full resolution)')
# a feature at world p sits in capture i at pixel c_i + (p - P_i) / mpp_true; placing it with the configured mpp puts it
# at P_i + (p - P_i) * mpp / mpp_true. Two captures whose centres are delta apart then disagree on it by s * delta
# (s = mpp / mpp_true - 1) along delta: their overlap, resampled on one world grid from each, correlates at that shift.
names = sorted(tiles); arr = {}
def img(nm):
    if nm not in arr:
        arr[nm] = np.asarray(Image.open(os.path.join(D, nm + '_google.jpg')).convert('L'), float)
    return arr[nm]
def sample(nm, gx, gy):
    a = img(nm); t = tiles[nm]; H_, W_ = a.shape
    px = W_ / 2 + (gx - t['x']) / MPP; py = H_ / 2 - (gy - t['y']) / MPP
    from scipy.ndimage import map_coordinates
    return map_coordinates(a, [py, px], order=1, mode='nearest')
B2 = []
for ii in range(len(names)):
    for jj in range(ii + 1, len(names)):
        ti, tj = tiles[names[ii]], tiles[names[jj]]
        dlt = np.array([tj['x'] - ti['x'], tj['y'] - ti['y']]); dist = float(np.linalg.norm(dlt))
        if not (50 <= dist <= 120):
            continue
        # the overlap box (each capture 1440 x 725 px), 6 % in from both captures' borders
        hw, hh = 1440 * MPP / 2 * 0.94, 725 * MPP / 2 * 0.94
        x0 = max(ti['x'], tj['x']) - hw; x1 = min(ti['x'], tj['x']) + hw; y0 = max(ti['y'], tj['y']) - hh; y1 = min(ti['y'], tj['y']) + hh
        if x1 - x0 < 25 or y1 - y0 < 25:
            continue
        S2 = MPP; gx, gy = np.meshgrid(np.arange(x0, x1, S2), np.arange(y1, y0, -S2))
        A_ = sample(names[ii], gx, gy); B_ = sample(names[jj], gx, gy)
        Hh, Ww = A_.shape
        def ed(a):
            gxx = np.zeros_like(a); gyy = np.zeros_like(a); gxx[:, 1:-1] = a[:, 2:] - a[:, :-2]; gyy[1:-1] = a[2:] - a[:-2]
            e = np.hypot(gxx, gyy); return (e - e.mean()) / (e.std() + 1e-6)
        w = np.outer(np.hanning(Hh), np.hanning(Ww))
        F = np.fft.fft2(ed(A_) * w) * np.conj(np.fft.fft2(ed(B_) * w)); r = np.fft.ifft2(F / (np.abs(F) + 1e-6)).real
        iy, ix = np.unravel_index(r.argmax(), r.shape); pk = r.max() / r.std()
        if pk < 10:
            continue
        def sub(a_m, a0, a_p):
            den = a_m - 2 * a0 + a_p
            return 0.0 if den == 0 else 0.5 * (a_m - a_p) / den
        fx = sub(r[iy, ix - 1], r[iy, ix], r[iy, (ix + 1) % Ww]); fy = sub(r[iy - 1, ix], r[iy, ix], r[(iy + 1) % Hh, ix])
        iy = iy - Hh if iy > Hh // 2 else iy; ix = ix - Ww if ix > Ww // 2 else ix
        # A at grid (x) shows what B shows at x - shift; shift > 0 along delta means the configured mpp is too large
        sh = np.array([(ix + fx) * S2, -(iy + fy) * S2])
        B2.append((dlt, dist, sh, pk))
if B2:
    # model: shift = s * delta (per axis: s_x * delta_x, s_y * delta_y) + common offset per pair (none expected)
    dx_ = np.array([b[0][0] for b in B2]); dy_ = np.array([b[0][1] for b in B2]); shx = np.array([b[2][0] for b in B2]); shy = np.array([b[2][1] for b in B2])
    print(f"{len(B2)} overlapping pairs 50-120 m apart (peak >= 10); |shift| median {np.median(np.hypot(shx, shy)):.3f} m")
    for nm, d_, s_ in (('east', dx_, shx), ('north', dy_, shy)):
        m_ = np.abs(d_) > 20
        if m_.sum() >= 5:
            X = d_[m_][:, None]; b, *_ = np.linalg.lstsq(X, s_[m_], rcond=None); r_ = s_[m_] - X[:, 0] * b[0]
            se = math.sqrt((r_ @ r_) / max(m_.sum() - 1, 1) / (X[:, 0] @ X[:, 0]))
            print(f"{nm}: {m_.sum()} pairs with |delta_{nm[0]}| > 20 m: |s| -> scale 1 {b[0] * 100:+.4f} % +- {se * 100:.4f} % (the sign convention: "
                  f"a shift of A against B along delta; either sign is a scale error of that size); residual {math.sqrt((r_ @ r_) / max(m_.sum() - 1, 1)):.3f} m")
print('\n## C. cfg.enu against the WGS84 ellipsoid')
from pyproj import Geod
G = Geod(ellps='WGS84'); lat0, lon0 = cfg['origin']; R = 6378137.0
inv = lambda X: (lon0 + np.degrees(X[:, 0] / (R * math.cos(math.radians(lat0)))), lat0 + np.degrees(X[:, 1] / R))  # noqa
for key in ('center', 'left', 'right'):
    X = np.array(T[key])[:, :2]; X = np.r_[X, X[:1]]
    lo, la = inv(X)
    geo = G.line_length(lo, la); enu = float(np.linalg.norm(np.diff(X, axis=0), axis=1).sum())
    print(f"{key}: ENU {enu:.2f} m, geodesic (ellipsoid surface) {geo:.2f} m, ENU / geodesic - 1 = {(enu / geo - 1) * 100:+.4f} %")
# per axis: 1 km east and 1 km north of the origin
for nm, dX in (('east', (1000.0, 0.0)), ('north', (0.0, 1000.0))):
    lo, la = inv(np.array([[0.0, 0.0], dX]))
    print(f"1000 m {nm} in ENU = {G.line_length(lo, la):.3f} m on the ellipsoid ({(1000 / G.line_length(lo, la) - 1) * 100:+.4f} % ENU vs ellipsoid)")
h = T['z0_navd88']
print(f"height above the ellipsoid ~{h - 34:.0f} m (NAVD88 z0 {h} m, geoid ~ -34 m): ground distances exceed ellipsoid ones by {h / 6371000 * 100:.4f} %")
