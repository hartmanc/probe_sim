"""Fit the track edges as ONE smooth curve per side instead of tracing them (owner, 18 Oct 2026 evening: "How are you
detecting and eliminating track edge waviness when it's not there?" -> option B of the review in
tools/track/compare/edge_sweep_2026-10-18/t2_waviness_review/).

    uv run --python 3.12 --with numpy,scipy,pillow,matplotlib python -I tools/track/fit_edges_spline.py \
        --lo 240 --hi 540 [--side both] [--knot 6] [--lam 3e3] [--huber 0.25] [--plot out.png] [--write]

Why: the per-station trace (one capture per station, holes, feature kind flipping between line / kerb / apron /
shadow) smoothed at 2-5 stations and patched stretch by stretch with blends into unverified neighbours left 20-80 m
waves of 0.3-1 m that the hood camera sees end-on. Here nothing is traced and nothing is blended:

 1. Candidates. For every station in lo..hi, side and z20 capture covering it (UI rectangles masked per sample, not per
    row; every capture shifted by ONE common Google-to-ortho shift: the captures agree with each other to a pixel, so the
    per-capture registrations, which differ by up to 0.6 m, were noise), the image is sampled along the station
    normal from 4.5 m inside to 4 m outside the current edge (0.04 m steps) and EVERY painted band with asphalt on
    its inner side is kept (bands(), candidates()); candidate edge positions: a white band 0.06-2.0 m wide (the hairpin apex band is ~1.2 m) counts by its inner side + --line-off
    0.26 m (the sim's painted line, drawn 0.15-0.27 m inside the edge, then starts where the real one does); a band
    with red by its outer limit; in a kerb zone (red seen within +-4 stations on that side, any capture; the scenery's
    kerb strips are not trusted for this: T2 exit right lists a kerb the imagery does not show) every band 0.3-2.6 m
    wide by its outer limit, since the kerb's white blocks read as a white band across the normal. Shadows and "non-asphalt" transitions are not boundary observations.
 2. Fit. Half-width w(s) per side is a cubic B-spline (knots every --knot stations) with a third-difference penalty
    (--lam), fitted by iteratively reweighted least squares with a Huber loss (--huber m): each (station, capture)
    contributes the candidate nearest the current curve within a gate that shrinks 1.2 -> 0.5 m. The first curve is a
    stiff fit to every candidate. The current edge enters with weight --prior per station (0.03; one capture's observation weighs 1), so it decides
    only where there are no observations (GPT 6: the old geometry as a weak fallback, not a strong prior). Outside lo..hi
    the edge is untouched: 12 stations of the current half-width on each
    side are heavy pseudo-observations, so value and slope continue across the joins without any blend.
 3. Gate (printed): the residual of w about a local quadratic over +-25 stations (waves of 15-100 m; tapers and
    corners are locally quadratic), as rms over rolling 100-station windows and peak, the edge heading change
    relative to the centre per station, the observation residuals (share within 0.25 m) and the longest stretch with
    no observation. Targets: rolling rms <= 0.04 m, peak <= 0.10 m, kink <= 0.5 deg/station, 95 % within 0.25 m.
 4. --write: new left/right points, profile columns re-evaluated from each station's cross-section quadratic (centre
    untouched), pit-lane / paved-zone boundary points that touched the old edge, or that now lie up to 2 m inside the
    new ribbon while the rest of their part is outside it, moved along the station normal onto the new edge (their
    profile row gets a linear ramp so it keeps its shape),
    track.json and scenery.json notes.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sweep_paint import ui_mask, bilinear, MPP, SAT, OUTD, EXCLUDE_TILES  # noqa: E402
from fix_edge_waves import quad_eval  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')
U = np.arange(-4.5, 4.0001, 0.04)


COMMON_SHIFT = (-0.3, 0.0)   # Google minus ortho, m: median of the 41 z20 registrations (paint_regs.json); the captures agree
                             # with each other to one pixel (register_clean.py), so per-capture registrations are noise
CLEAN = os.path.join(HERE, 'compare', 'satellite_clean')


def clean_mask(H, W):
    """clean captures (UI hidden by page CSS, labels off): only the Layers button, logo, attribution, one control, cursor"""
    m = np.ones((H, W), bool)
    m[620:712, 85:178] = False; m[675:712, 695:815] = False; m[705:, 850:] = False; m[575:620, 1380:1430] = False; m[:30, 1420:] = False
    m[222:268, 705:745] = False   # mouse cursor on c20_a1..a3 (taken before it was parked in the corner)
    return m


def capture_list(which):
    out = []
    if 'z20' in which:
        for t in json.load(open(os.path.join(SAT, 'z20_tiles.json'))):
            # z20_s3400 was excluded only for its ortho registration (1.3 m off); with one common shift its imagery
            # agrees with its neighbours and the clean capture c20_b3400 to a pixel (register_clean.py)
            out.append(dict(name=t['name'], path=os.path.join(SAT, t['name'] + '_google.jpg'), x=t['x'], y=t['y'],
                            dx=COMMON_SHIFT[0], dy=COMMON_SHIFT[1], mask=ui_mask))
    if 'clean' in which and os.path.exists(os.path.join(CLEAN, 'tiles.json')):
        for t in json.load(open(os.path.join(CLEAN, 'tiles.json'))):
            if 'rel_dx' not in t: continue
            out.append(dict(name=t['name'], path=os.path.join(CLEAN, t['name'] + '_google.jpg'), x=t['x'], y=t['y'],
                            dx=COMMON_SHIFT[0] + t['rel_dx'], dy=COMMON_SHIFT[1] + t['rel_dy'], mask=clean_mask))
    return out


def geometry(T):
    C = np.array(T['center'])[:, :2]
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    return C, NL, ((L - C) * NL).sum(1), -((R - C) * NL).sum(1)


def bands(v, valid):
    """v: (len(U), 3) RGB outward along the normal; valid: bool per sample. Returns the painted bands with asphalt just
    inside them: [(inner offset, outer offset from the current edge, has red, width)]."""
    br = v.mean(1); sat = v.max(1) - v.min(1)
    grey = (sat < 30) & valid
    inner = (U < -1.5) & grey
    if inner.sum() < 15: return []
    ref = np.median(br[inner])
    white = valid & (br > max(ref + 40, 160)) & (sat < 40) & (v[:, 0] - v[:, 2] < 22)
    # thin painted line on pale asphalt (after T2: asphalt 180, line 220): a strip under 0.4 m brighter than the ground
    # 0.35 m to both sides by 25 or more
    d = int(round(0.35 / 0.04)); thin = np.zeros_like(white)
    thin[d:-d] = (br[d:-d] - np.maximum(br[:-2 * d], br[2 * d:]) > 25) & (sat[d:-d] < 45)
    white = white | (thin & valid)
    red = valid & (v[:, 0] > 100) & (v[:, 0] - v[:, 1] > 25) & (v[:, 0] - v[:, 2] > 20)
    st = 0.04; q = lambda m: max(1, int(round(m / st))); out = []; N = len(U)
    k = 0
    while k < N:
        if not (white[k] or red[k]): k += 1; continue
        j = k; gap = 0; seen_red = False
        # a kerb's blocks blur into pinkish pixels that are neither red nor white: once red is seen, gaps up to 0.35 m
        # are bridged so the band runs to the kerb's outer limit (otherwise the outer limit lands mid-kerb)
        while j < N and gap <= (q(0.35) if seen_red else q(0.12)):
            if red[j]: seen_red = True
            gap = 0 if (white[j] or red[j]) else gap + 1; j += 1
        j -= gap
        # asphalt just inside the band: grey and darker than the band (the asphalt brightens toward the inside of a
        # hairpin, so a far-inside reference brightness is not used here)
        a0 = slice(max(0, k - q(0.6)), max(0, k - q(0.1))); bb = np.median(br[k:max(j, k + 1)])
        # (a kerb's red blocks are as dark as the asphalt, so for a band with red only grey asphalt inside is required)
        has_red_ = red[k:j].mean() > 0.15
        inner_ok = (grey[a0].mean() > 0.6) if has_red_ else ((grey[a0] & (br[a0] < bb - 30)).mean() > 0.6)
        if a0.stop - a0.start >= q(0.3) and inner_ok and valid[min(N - 1, j)]:
            out.append((U[k], U[min(j, N - 1)], bool(red[k:j].mean() > 0.15), (j - k) * st))
        k = j + 1
    return out


# Explicit feature table: (side, first station, last station, feature, why). 'asphalt_end' = the edge is where the dark
# asphalt ends (a step of 10+ in brightness held for 0.4 m), not the first white band.
FEATURES = [
    # 'keep': no observations; the current edge is followed closely (prior weight KEEP_W) and the spline joins it smoothly
    ('left', 2425, 2535, 'keep', 'Corkscrew: the S is too tight for the 6-station spline and the current edge was set and AI-checked on 18 Oct'),
    ('right', 2425, 2535, 'keep', 'Corkscrew, as the left side'),
    ('right', 3228, 3425, 'keep', 'T11 outside and exit: owner-approved shape (fix_edge_shape.py knots); the fit cut inside the outer line and read the exit kerb by its inner side'),
    ('left', 3330, 3633, 'keep', 'front straight left: 2.01 m from the pit wall (fix_front_straight_left.py); the fit reached the wall base'),
    ('left', 3633, 3800, 'keep', 'pit-out merge to T1 (stations 73-240): the left edge includes the pit-out lane; teal strip lines either side made the fit switch between them'),
    ('left', 478, 528, 'asphalt_end',
     'Andretti apex between the two apex kerbs: a pale painted band ~1.2 m wide (brightness 177-188 vs asphalt 160) with a thin '
     'white line on its outer side; the edge is the band\'s inner side (c20_a7/a8 profiles, station 500)'),
]


KEEP_W = 400.0


def asphalt_end(v, valid):
    """offset where the dark asphalt ends: first point whose next 0.4 m is 10+ brighter than the 0.3-1.0 m before it."""
    br = v.mean(1); sat = v.max(1) - v.min(1); st = 0.04; q = lambda m: max(1, int(round(m / st)))
    for k in range(q(1.0), len(U) - q(0.4)):
        if not valid[k - q(1.0):k + q(0.4)].all(): continue
        if U[k] < -1.2 or U[k] > 2.0: continue   # near the current edge only (the rubbered line brightens gently over 4 m)
        before = np.median(br[k - q(1.0):k - q(0.3)]); after = br[k:k + q(0.4)]
        if (after > before + 10).mean() > 0.9 and np.median(sat[k:k + q(0.4)]) < 30: return float(U[k])
    return None


def candidates(bl, line_off, kerb):
    """edge candidates from bands: in a kerb zone (red detected within +-4 stations on this side, any capture) every band
    0.3-2.6 m wide counts by its outer limit (the kerb's white blocks read as a white band across the normal); elsewhere
    a white band 0.06-2.0 m wide (the hairpin apex band is ~1.2 m) counts by its inner side + line_off and a red band
    by its outer limit."""
    out = []
    for u0, u1, has_red, w in bl:
        if w < 0: out.append((u0 + line_off, 1)); continue      # asphalt_end feature (FEATURES)
        if kerb:
            if 0.3 <= w <= 2.6: out.append((u1, 2))
        elif has_red:
            if w <= 2.6: out.append((u1, 2))
        elif 0.06 <= w <= 2.0: out.append((u0 + line_off, 1))
    return out


def bspline_basis(x, knots_x):
    """cubic B-spline design matrix on uniform knots (spacing h, first at knots_x[0]); columns = len(knots_x) + 2."""
    h = knots_x[1] - knots_x[0]; t = (x - knots_x[0]) / h; i = np.floor(t).astype(int); i = np.clip(i, 0, len(knots_x) - 2); u = t - i
    B = np.zeros((len(x), len(knots_x) + 2))
    b = [(1 - u) ** 3 / 6, (3 * u ** 3 - 6 * u ** 2 + 4) / 6, (-3 * u ** 3 + 3 * u ** 2 + 3 * u + 1) / 6, u ** 3 / 6]
    for m in range(4): B[np.arange(len(x)), i + m] = b[m]
    return B


def fit(xo, yo, wo, xa, ya, knots_x, lam, huber, iters=8, xp=None, yp=None, wp=0.0):
    """xa/ya: junction anchors (weight 200); xp/yp: weak prior (weight wp each), the current edge at every station."""
    B = bspline_basis(xo, knots_x); Ba = bspline_basis(xa, knots_x); nb = B.shape[1]
    D = np.diff(np.eye(nb), 3, axis=0); P = lam * D.T @ D
    if xp is not None and np.any(np.asarray(wp) > 0):
        wpv = np.broadcast_to(np.asarray(wp, float), xp.shape)
        Bp = bspline_basis(xp, knots_x); P = P + (Bp * wpv[:, None]).T @ Bp; prior_rhs = (Bp * wpv[:, None]).T @ yp
    else: prior_rhs = 0.0
    rw = np.ones(len(xo))
    for _ in range(iters):
        W = wo * rw
        A = (B * W[:, None]).T @ B + (Ba * 200.0).T @ Ba + P
        c = np.linalg.solve(A, (B * W[:, None]).T @ yo + (Ba * 200.0).T @ ya + prior_rhs)
        r = np.abs(B @ c - yo); rw = np.where(r <= huber, 1.0, huber / np.maximum(r, 1e-9))
    return c


def local_quad_resid(w, half):
    n = len(w); out = np.full(n, np.nan); x = np.arange(-half, half + 1); A = np.c_[np.ones_like(x), x, x * x]
    pinv = np.linalg.pinv(A)
    for k in range(half, n - half):
        co = pinv @ w[k - half:k + half + 1]; out[k] = w[k] - co[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lo', type=int, required=True); ap.add_argument('--hi', type=int, required=True)
    ap.add_argument('--side', choices=('left', 'right', 'both'), default='both')
    ap.add_argument('--knot', type=int, default=6); ap.add_argument('--lam', type=float, default=3e3)
    ap.add_argument('--huber', type=float, default=0.25); ap.add_argument('--init-stiff', type=float, default=30.0, help='first curve: --lam times this, Huber 1 m, to every candidate'); ap.add_argument('--prior', type=float, default=0.03, help='weight per station of the current edge (one capture = 1): decides only where there are no observations'); ap.add_argument('--line-off', type=float, default=0.26)
    ap.add_argument('--captures', default='z20,clean', help='z20 (masked Maps screenshots) and/or clean (UI hidden, labels off)'); ap.add_argument('--plot'); ap.add_argument('--dump', help='npz with the fit and every candidate (world xy) for overlays'); ap.add_argument('--write', action='store_true'); ap.add_argument('--why', default='')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n = T['n']; C, NL, hl, hr = geometry(T)
    ks = np.arange(a.lo, a.hi + 1); kk = ks % n
    tiles = capture_list(a.captures)
    raw = {'left': [], 'right': []}
       # (station index in ks, tile index, [candidate half-widths])
    for ti, t in enumerate(tiles):
        im = None
        for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
            if a.side not in (side, 'both'): continue
            lat = sg * (hw[kk][:, None] + U[None, :])
            X = C[kk, 0:1] + lat * NL[kk, 0:1]; Y = C[kk, 1:2] + lat * NL[kk, 1:2]
            if (np.hypot(X.mean(1) - t['x'], Y.mean(1) - t['y']) > 100).all(): continue
            dx, dy = t['dx'], t['dy']
            if im is None:
                im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32)
                H, W = im.shape[:2]; mask = t['mask'](H, W)
            px = W / 2 + (X + dx - t['x']) / MPP; py = H / 2 - (Y + dy - t['y']) / MPP
            inside = (px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)
            rows = np.where(inside.mean(1) > 0.6)[0]
            if not len(rows): continue
            V = bilinear(im, np.clip(px[rows], 1, W - 2), np.clip(py[rows], 1, H - 2))
            val = inside[rows] & mask[np.clip(np.round(py[rows]).astype(int), 0, H - 1), np.clip(np.round(px[rows]).astype(int), 0, W - 1)]
            for v, ok, i in zip(V, val, rows):
                feat = next((f[3] for f in FEATURES if f[0] == side and f[1] <= ks[i] <= f[2]), None)
                if feat == 'keep': continue
                if feat == 'asphalt_end':
                    e = asphalt_end(v, ok)
                    if e is not None: raw[side].append((i, ti, [(e, e + 0.1, False, -1.0)]))
                    continue
                bl = bands(v, ok)
                if bl: raw[side].append((i, ti, bl))
    obs = {'left': [], 'right': []}
    for side, hw in (('left', hl), ('right', hr)):
        red_st = np.zeros(len(ks), bool)
        for i, _, bl in raw[side]:
            if any(b_[2] and 0.3 <= b_[3] <= 2.6 for b_ in bl): red_st[i] = True
        kerb_at = np.array([red_st[max(0, i - 4):i + 5].any() for i in range(len(ks))])
        for i, ti, bl in raw[side]:
            c = candidates(bl, a.line_off, kerb_at[i])
            if c: obs[side].append((i, ti, [hw[kk[i]] + e for e, _ in c], [kd for _, kd in c]))
    knots_x = np.arange(a.lo - 3 * a.knot, a.hi + 3 * a.knot + 1, a.knot).astype(float)
    xa = np.r_[np.arange(a.lo - 12, a.lo), np.arange(a.hi + 1, a.hi + 13)].astype(float)
    result = {}
    for side, hw in (('left', hl), ('right', hr)):
        if a.side not in (side, 'both'): continue
        ya = hw[xa.astype(int) % n]; O = obs[side]
        wprior = np.full(len(ks), a.prior)
        for f in FEATURES:
            if f[0] == side and f[3] == 'keep': wprior[(ks >= f[1]) & (ks <= f[2])] = KEEP_W
        if not O: print(side, 'no observations'); continue
        xo_all = np.array([ks[i] for i, _, c, _ in O for _ in c], float); yo_all = np.array([y for _, _, c, _ in O for y in c])
        c0 = fit(xo_all, yo_all, np.ones(len(xo_all)), xa, ya, knots_x, a.lam * a.init_stiff, 1.0, xp=ks.astype(float), yp=hw[kk], wp=wprior)
        cur = bspline_basis(ks.astype(float), knots_x) @ c0
        for gate in (1.2, 1.0, 0.8, 0.6, 0.5, 0.5):
            xo, yo = [], []
            for i, _, c, _ in O:
                d = np.abs(np.array(c) - cur[i]); j = int(d.argmin())
                if d[j] <= gate: xo.append(ks[i]); yo.append(c[j])
            xo = np.array(xo, float); yo = np.array(yo)
            cf = fit(xo, yo, np.ones(len(xo)), xa, ya, knots_x, a.lam, a.huber, xp=ks.astype(float), yp=hw[kk], wp=wprior)
            cur = bspline_basis(ks.astype(float), knots_x) @ cf
        res = yo - bspline_basis(xo, knots_x) @ cf
        covered = np.zeros(len(ks), bool); covered[(xo - a.lo).astype(int)] = True
        gaps, run = 0, 0
        for cv in covered: run = 0 if cv else run + 1; gaps = max(gaps, run)
        result[side] = (cur, xo, yo, res, covered, gaps)
        old = hw[kk]
        full_old = np.r_[hw[(np.arange(a.lo - 40, a.lo)) % n], old, hw[(np.arange(a.hi + 1, a.hi + 41)) % n]]
        full_new = np.r_[hw[(np.arange(a.lo - 40, a.lo)) % n], cur, hw[(np.arange(a.hi + 1, a.hi + 41)) % n]]
        for lab, wv in (('before', full_old), ('after', full_new)):
            q = local_quad_resid(wv, 25)[40:-40]
            roll = [np.sqrt(np.nanmean(q[i:i + 100] ** 2)) for i in range(0, max(1, len(q) - 99), 5)]
            kk2 = np.degrees(np.abs(np.diff(wv, 2)))[39:-39]; kink = kk2.max(); kat = a.lo + int(kk2.argmax())   # 2nd difference of w ~ heading change rel. centre, deg/station
            print(f'{side:5s} {lab:6s}: local-quadratic residual (+-25 st) rolling-100 rms max {max(roll):.3f} m, peak {np.nanmax(np.abs(q)):.3f} m; '
                  f'edge heading change rel. centre max {kink:.2f} deg/station at {kat}')
        print(f'{side:5s} fit   : {len(xo)} observations from {len({o[1] for o in O})} captures, {covered.mean() * 100:.0f} % of stations covered, longest gap {gaps} st; '
              f'residual within 0.25 m {np.mean(np.abs(res) <= 0.25) * 100:.0f} %, rms {np.sqrt(np.mean(res ** 2)):.3f} m; max move {np.abs(cur - old).max():.2f} m at {ks[int(np.abs(cur - old).argmax())]}')
        print('       station: now -> fit  ' + '  '.join(f'{ks[i]}:{old[i]:.1f}->{cur[i]:.1f}' for i in range(0, len(ks), 20)))
    if a.plot:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        CH = 460; chunks = [(c0, min(a.hi, c0 + CH - 1)) for c0 in range(a.lo, a.hi + 1, CH)]
        for ci, (c0, c1) in enumerate(chunks):
            fig, axs = plt.subplots(len(result), 1, figsize=(14, 4.2 * len(result)), squeeze=False)
            for ax, (side, (cur, xo, yo, res, cov, g)) in zip(axs[:, 0], result.items()):
                hw = hl if side == 'left' else hr; sel = (ks >= c0) & (ks <= c1)
                for i, _, c, kd in obs[side]:
                    if c0 <= ks[i] <= c1: ax.scatter([ks[i]] * len(c), c, s=3, c=['#bbbbbb' if k_ == 1 else '#f0a0f0' for k_ in kd], zorder=1)
                m_ = (xo >= c0) & (xo <= c1)
                ax.scatter(xo[m_], yo[m_], s=4, c='k', zorder=2, label='associated observations')
                ax.plot(ks[sel], hw[kk][sel], 'r', lw=1.5, label='current edge (branch)'); ax.plot(ks[sel], cur[sel], 'b', lw=2, label='spline fit')
                lo_y = min(np.min(cur[sel]), np.min(hw[kk][sel])) - 1.5; hi_y = max(np.max(cur[sel]), np.max(hw[kk][sel])) + 1.5
                ax.set_title(f'{side} half-width, stations {c0}-{c1} (mod {n})'); ax.set_ylim(lo_y, hi_y); ax.legend(loc='upper left', fontsize=8); ax.grid(alpha=0.3)
            fig.tight_layout(); out = a.plot if len(chunks) == 1 else a.plot.replace('.png', f'_{ci}.png'); fig.savefig(out, dpi=100); plt.close(fig); print('wrote', out)
    if a.dump:
        D = {'ks': ks}
        for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
            if side not in result: continue
            D[side + '_fit'] = result[side][0]
            pts = [(C[kk[i]] + sg * NL[kk[i]] * y, kd_) for i, _, c, kd in obs[side] for y, kd_ in zip(c, kd)]
            D[side + '_cand'] = np.array([[p[0][0], p[0][1], p[1]] for p in pts])
        np.savez(a.dump, **D); print('wrote', a.dump)
    if not a.write: print('dry run; --write to apply'); return
    fr = T['profile']['fractions']; Z = T['profile']['z']; Lp, Rp = T['left'], T['right']
    oldL = {int(k): list(Lp[k]) for k in kk}; oldR = {int(k): list(Rp[k]) for k in kk}
    for i, k in enumerate(kk):
        hl_old, hr_old = hl[k], hr[k]
        hln = result['left'][0][i] if 'left' in result else hl_old; hrn = result['right'][0][i] if 'right' in result else hr_old
        xs_old = [(-g) * hl_old if g < 0 else -g * hr_old for g in fr]; xs_new = [(-g) * hln if g < 0 else -g * hrn for g in fr]
        zn = [quad_eval(xs_old, Z[k], x) for x in xs_new]; zn[fr.index(0)] = Z[k][fr.index(0)]; Z[k] = [round(z, 3) for z in zn]
        c = C[k]; nx, ny = NL[k]
        Lp[k] = [round(c[0] + nx * hln, 3), round(c[1] + ny * hln, 3), Z[k][0]]
        Rp[k] = [round(c[0] - nx * hrn, 3), round(c[1] - ny * hrn, 3), Z[k][-1]]
    snapped = 0
    kset = {int(k): i for i, k in enumerate(kk)}
    HL = {int(k): (hl[k], result['left'][0][i] if 'left' in result else hl[k]) for i, k in enumerate(kk)}
    HR = {int(k): (hr[k], result['right'][0][i] if 'right' in result else hr[k]) for i, k in enumerate(kk)}
    def lat_of(q):
        k = int(np.argmin(np.hypot(C[:, 0] - q[0], C[:, 1] - q[1]))); return k, float((np.array(q[:2]) - C[k]) @ NL[k])
    for grp in ('pit_lane', 'paved_zones'):
        frs = (SC.get(grp) or {}).get('fractions')
        for p in (SC.get(grp) or {}).get('parts', []):
            for bside, other in (('left', 'right'), ('right', 'left')):
                for j, q in enumerate(p[bside]):
                    k, lq = lat_of(q)
                    if k not in kset or k in (int(kk[0]), int(kk[-1])): continue
                    _, lo_ = lat_of(p[other][j])
                    sg = 1 if lq > 0 else -1; H_ = HL if sg > 0 else HR; E_new = Lp if sg > 0 else Rp
                    # boundary points sit between stations: interpolate the edge's width and height to the point's
                    # position along the track (station heights shared by two points made a staircase)
                    tg = np.array([-NL[k][1], NL[k][0]]); u = float((np.array(q[:2]) - C[k]) @ tg) / T['spacing_m']
                    k2 = k + (1 if u > 0 else -1); w2 = min(1.0, abs(u)) if k2 in H_ else 0.0; k2 = k2 if k2 in H_ else k
                    old_hw = (1 - w2) * H_[k][0] + w2 * H_[k2][0]; new_hw = (1 - w2) * H_[k][1] + w2 * H_[k2][1]
                    E_old = oldL if sg > 0 else oldR
                    dz_edge = (1 - w2) * (E_new[k][2] - E_old[k][2]) + w2 * (E_new[k2][2] - E_old[k2][2])
                    # touched the old edge (lateral distance along the station normal; boundary points sit between
                    # stations), or lies up to 2 m inside the new ribbon while the rest of the part is outside it
                    touch = abs(abs(lq) - old_hw) < 0.3
                    inside = sg * lo_ > new_hw and new_hw - 2.0 < sg * lq < new_hw and new_hw - old_hw > 0.05   # caused by this move
                    if not (touch or inside): continue
                    shift = new_hw - abs(lq)
                    if abs(new_hw - old_hw) < 0.05 and not inside: continue   # the edge barely moved: leave the part as built
                    p[bside][j] = [round(q[0] + sg * NL[k][0] * shift, 3), round(q[1] + sg * NL[k][1] * shift, 3), round(q[2] + dz_edge, 3)]
                    p['gap_' + bside][j] = 0.0; snapped += 1
                    # the moved boundary's column changes by the edge's height change; the rest of the row gets a linear
                    # ramp (1 at that column, 0 at the far one) so the row keeps its shape (pitlane.test.ts continuity)
                    row = p['profile_z'][j]; col = 0 if bside == 'left' else len(row) - 1; dz = dz_edge   # the edge's height change at this point
                    wts = [(1 - f) / 2 if bside == 'left' else (1 + f) / 2 for f in frs]
                    p['profile_z'][j] = [round(z + dz * w, 3) for z, w in zip(row, wts)]
                    # the far boundary stays at least 0.3 m beyond the new edge (a tapered zone end the edge moved
                    # past), and the row's centre point is the midpoint of its boundaries again
                    oq = p[other][j]; _, lo2 = lat_of(oq)
                    if sg * lo2 < new_hw + 0.3:
                        s2 = new_hw + 0.3 - sg * lo2
                        p[other][j] = [round(oq[0] + sg * NL[k][0] * s2, 3), round(oq[1] + sg * NL[k][1] * s2, 3), oq[2]]
                    L_, R_ = p['left'][j], p['right'][j]; zc = p['profile_z'][j][frs.index(0)]
                    p['center'][j] = [round((L_[0] + R_[0]) / 2, 3), round((L_[1] + R_[1]) / 2, 3), zc]
    print(f'{snapped} pit-lane / paved-zone boundary points snapped to the new edge')
    note = (f'18 Oct 2026: fit_edges_spline.py --lo {a.lo} --hi {a.hi} --side {a.side} --knot {a.knot} --lam {a.lam} --huber {a.huber} '
            f'--line-off {a.line_off}: edge = one robust penalised cubic spline per side through every painted-line / kerb candidate '
            f'of every capture (no tracing, no blends). {a.why}')
    T['notes'][f'spline_{a.side}_{a.lo}'] = note
    SC.setdefault('notes', {})[f'spline_{a.side}_{a.lo}'] = f'{snapped} boundary points snapped by ' + note[:60]
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':'))
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote track.json, scenery.json')


if __name__ == '__main__':
    sys.exit(main())
