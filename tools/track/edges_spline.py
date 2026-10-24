"""Fit the track edges as ONE smooth curve per side instead of tracing them (owner, 18 Oct 2026 evening: "How are you
detecting and eliminating track edge waviness when it's not there?" -> option B of the review in
tools/track/compare/edge_sweep_2026-10-18/t2_waviness_review/).

Stage 1 geometry of tools/track/build_track.py (was fit_edges_spline.py, 18 Oct 2026 evening); the runs, knot, lam,
huber, line_off, prior and the FEATURES table come from the track config (`spline`, `features`, `shapes`).

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
 4. Measured shapes (config `shapes`, was fix_edge_shape.py) are applied to the prior before the fit: a monotone cubic
    through station:half-width knots, blended over a few stations; a 'keep' feature over the same stations holds it.
 5. The profile is not touched here: build_track.py re-evaluates the profile columns at the fitted edges from each
    station's cross-section quadratic (centre.reprofile), and scenery parts are built on the final edges afterwards.
"""
import numpy as np
from PIL import Image

from captures import bilinear
from geo import log as _log

U = np.arange(-4.5, 4.0001, 0.04)


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


KEEP_W = 400.0
# the owner's traced edges (spline.owner_edges, Buttonwillow 21 Oct 2026, ported to this branch for Sonoma round 14B;
# build_track loads them into sp['_owner']): [{side, lo, hi, pts (world xy, n x 2), kerb_inside: [(lo, hi[, shift])],
# kerb_w}] on the current centre's stations. Empty (every config without spline.owner_edges): the fit is unchanged.
OWNER = []
KERB_RAMP = 6     # stations over which a kerb_inside shift ramps in at each end
KERB_STEP = 0.08  # a measured-shift kerb zone (kerb_inside (side, lo, hi, shift), Buttonwillow round 10): the shift ramps
                  # in OUTSIDE the zone at most this much per station, so the whole measured kerb lies inside the edge
                  # and the edge-gate step (0.10 m per station) holds
OWNER_W = 40.0   # anchor weight per owner station (40 unit rows: his line outweighs the third-difference penalty;
                 # as plain rows, 8 copies left 0.5-0.7 m bumps of 10-15 m unfollowed, Buttonwillow run 38)


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


def pchip(xs, ys):
    """Fritsch-Carlson monotone cubic interpolant; returns f(x) (fix_edge_shape.py)."""
    m = len(xs); h = [xs[i + 1] - xs[i] for i in range(m - 1)]; d = [(ys[i + 1] - ys[i]) / h[i] for i in range(m - 1)]
    t = [0.0] * m
    t[0] = d[0]; t[-1] = d[-1]
    for i in range(1, m - 1):
        if d[i - 1] * d[i] <= 0: t[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]
            t[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = max(j for j in range(m - 1) if xs[j] <= x)
        u = (x - xs[i]) / h[i]; h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
        return h00 * ys[i] + h10 * h[i] * t[i] + h01 * ys[i + 1] + h11 * h[i] * t[i + 1]
    return f


def apply_shape(hw, knots, blend, n):
    """Half-width over the knot span replaced by the monotone cubic through the knots, blended into the current edge
    over `blend` stations at both ends (smoothstep)."""
    xs = [k for k, _ in knots]; ys = [v for _, v in knots]; f = pchip(xs, ys)
    out = hw.copy(); a, b = xs[0], xs[-1]
    for k in range(a, b + 1):
        d = min(k - a, b - k); t = 1.0 if blend <= 0 or d >= blend else d / blend
        t = t * t * (3 - 2 * t)
        out[k % n] = (1 - t) * hw[k % n] + t * f(k)
    return out


def fit_run(C, NL, hl, hr, lo, hi, tiles, features, sp, mpp, side_sel="both", log=_log):
    """One spline run over stations lo..hi (may exceed n: wraps). hl/hr: current half-widths (full loop). sp: the
    `spline` config. Returns (hl, hr, report) with the fitted stretch replaced."""
    n = len(C)
    a = type('A', (), dict(lo=lo, hi=hi, side=side_sel, knot=sp['knot'], lam=sp['lam'], huber=sp['huber'],
                         init_stiff=sp['init_stiff'], prior=sp['prior'], line_off=sp['line_off']))
    FEATURES = features
    rep = {}
    ks = np.arange(a.lo, a.hi + 1); kk = ks % n
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
            px = W / 2 + (X + dx - t['x']) / mpp; py = H / 2 - (Y + dy - t["y"]) / mpp
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
            feat = next((f[3] for f in FEATURES if f[0] == side and f[1] <= ks[i] <= f[2]), None)
            if feat == 'kerb':
                # the edge is the kerb's outer limit here (apex kerb at the bottom of a V, dirt beyond): bands with red only
                c = [(u1, 2) for u0, u1, has_red, w in bl if has_red and 0.3 <= w <= 2.6]
            else:
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
        if not O: log(side, 'no observations'); continue
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
        rep[side] = dict(obs=int(len(xo)), covered=float(covered.mean()), longest_gap=int(gaps), within=float(np.mean(np.abs(res) <= 0.25)), rms=float(np.sqrt(np.mean(res ** 2))))
        old = hw[kk]
        full_old = np.r_[hw[(np.arange(a.lo - 40, a.lo)) % n], old, hw[(np.arange(a.hi + 1, a.hi + 41)) % n]]
        full_new = np.r_[hw[(np.arange(a.lo - 40, a.lo)) % n], cur, hw[(np.arange(a.hi + 1, a.hi + 41)) % n]]
        for lab, wv in (('before', full_old), ('after', full_new)):
            q = local_quad_resid(wv, 25)[40:-40]
            roll = [np.sqrt(np.nanmean(q[i:i + 100] ** 2)) for i in range(0, max(1, len(q) - 99), 5)]
            kk2 = np.degrees(np.abs(np.diff(wv, 2)))[39:-39]; kink = kk2.max(); kat = a.lo + int(kk2.argmax())   # 2nd difference of w ~ heading change rel. centre, deg/station
            rep.setdefault(side, {})
            rep['wave_' + side + '_' + lab] = (float(max(roll)), float(np.nanmax(np.abs(q))), float(kink))
            log(f'{side:5s} {lab:6s}: local-quadratic residual (+-25 st) rolling-100 rms max {max(roll):.3f} m, peak {np.nanmax(np.abs(q)):.3f} m; '
                  f'edge heading change rel. centre max {kink:.2f} deg/station at {kat}')
        log(f'{side:5s} fit   : {len(xo)} observations from {len({o[1] for o in O})} captures, {covered.mean() * 100:.0f} % of stations covered, longest gap {gaps} st; '
              f'residual within 0.25 m {np.mean(np.abs(res) <= 0.25) * 100:.0f} %, rms {np.sqrt(np.mean(res ** 2)):.3f} m; max move {np.abs(cur - old).max():.2f} m at {ks[int(np.abs(cur - old).argmax())]}')
        log('       station: now -> fit  ' + '  '.join(f'{ks[i]}:{old[i]:.1f}->{cur[i]:.1f}' for i in range(0, len(ks), 20)))
    hl, hr = hl.copy(), hr.copy()
    if 'left' in result: hl[kk] = result['left'][0]
    if 'right' in result: hr[kk] = result['right'][0]
    return hl, hr, rep


# ---------------------------------------------------------------- the fitted method (new circuits; 20 Oct 2026)
def feature_at(features, side, k, n):
    """the config feature covering station k on `side` (ranges may wrap past the lap end), or None"""
    for f in features:
        if f[0] == side and (k - f[1]) % n <= (f[2] - f[1]) % n:
            return f[3]
    return None


def gather(C, NL, hl, hr, tiles, features, line_off, mpp, U_=None):
    """Boundary evidence along every station's normal on every capture: for each side a list of (station, capture,
    [candidate half-widths], [kinds]). Features 'asphalt_end' and 'kerb' choose the kind of evidence; 'keep' is not a
    method here (it froze a prior) and is ignored."""
    n = len(C); U_ = U if U_ is None else U_
    ks = np.arange(n)
    raw = {'left': [], 'right': []}
    for ti, t in enumerate(tiles):
        im = None
        for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
            lat = sg * (hw[:, None] + U_[None, :])
            X = C[:, 0:1] + lat * NL[:, 0:1]; Y = C[:, 1:2] + lat * NL[:, 1:2]
            near = np.hypot(X.mean(1) - t['x'], Y.mean(1) - t['y']) <= 100
            if not near.any(): continue
            if im is None:
                im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32)
                H, W = im.shape[:2]; mask = t['mask'](H, W)
            px = W / 2 + (X + t['dx'] - t['x']) / mpp; py = H / 2 - (Y + t['dy'] - t['y']) / mpp
            inside = (px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)
            rows = np.where(inside.mean(1) > 0.6)[0]
            if not len(rows): continue
            V = bilinear(im, np.clip(px[rows], 1, W - 2), np.clip(py[rows], 1, H - 2))
            val = inside[rows] & mask[np.clip(np.round(py[rows]).astype(int), 0, H - 1), np.clip(np.round(px[rows]).astype(int), 0, W - 1)]
            for v, ok, i in zip(V, val, rows):
                feat = feature_at(features, side, ks[i], n)
                if feat == 'asphalt_end':
                    e = asphalt_end(v, ok)
                    if e is not None: raw[side].append((i, ti, [(e, e + 0.1, False, -1.0)]))
                    continue
                bl = bands(v, ok)
                if bl: raw[side].append((i, ti, bl))
    obs = {'left': [], 'right': []}
    for side, hw in (('left', hl), ('right', hr)):
        red_st = np.zeros(n, bool)
        for i, _, bl in raw[side]:
            if any(b_[2] and 0.3 <= b_[3] <= 2.6 for b_ in bl): red_st[i] = True
        kerb_at = np.array([red_st[np.arange(i - 4, i + 5) % n].any() for i in range(n)])
        for i, ti, bl in raw[side]:
            feat = feature_at(features, side, ks[i], n)
            if feat == 'kerb':
                c = [(u1, 2) for u0, u1, has_red, w in bl if has_red and 0.3 <= w <= 2.6]
            else:
                c = candidates(bl, line_off, kerb_at[i])
            if c: obs[side].append((i, ti, [hw[i] + e for e, _ in c], [kd for _, kd in c]))
    for side, hw in (('left', hl), ('right', hr)):
        for w in OWNER:
            if w['side'] != side:
                continue
            r = owner_readings(C, NL, w, n)
            if not r:
                continue
            # the owner's line replaces every other reading in its window on that side where he drew it (within 3
            # stations of a reading of his); where he drew nothing the captures stand
            inwin = {k % n for k in range(w['lo'], w['hi'] + (n if w['hi'] < w['lo'] else 0) + 1)}
            drawn = {(k + d) % n for k in r for d in range(-3, 4)} & inwin
            obs[side] = [o for o in obs[side] if o[0] not in drawn]
            for k, lat in r.items():
                if k in inwin:
                    # owner_readings gives the half-width (+ outward); one reading per station (the gates' statistics
                    # count it once); its weight in the fit comes from the anchors (fit_periodic, OWNER_W)
                    obs[side].append((k, -1, [lat], ['owner']))
    return obs


def owner_chains(pts, link=3.0, min_pts=5):
    """the owner's points (both labels pooled) split into continuous lines: single linkage at `link` m (his two lines
    stand >= 8 m apart, his points ~1 m apart along a line)"""
    from scipy.spatial import cKDTree
    P = np.asarray(pts, float)
    par = list(range(len(P)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i, j in cKDTree(P).query_pairs(link):
        par[f(i)] = f(j)
    r = np.array([f(i) for i in range(len(P))])
    # a line has many points; a lone pixel cluster is no line
    return [P[r == u] for u in np.unique(r) if (r == u).sum() >= min_pts]


def owner_readings(C, NL, w, n):
    """the owner's line as one half-width reading per station of the current centre: each world point projected on
    the centre (nearest station, lateral along the normal), the median per station; where the owner drew on the track
    side of a block line (kerb_inside), moved outward by the kerb's width so the kit's strip stays inside the edge"""
    from scipy.spatial import cKDTree
    sg = 1 if w['side'] == 'left' else -1
    if w.get('chains'):
        # the drawing's continuous lines (owner_chains), each given to the side of the CURRENT centre that holds most of
        # it: the JSON's left / right labels came from the centre it was traced against
        T = cKDTree(C)
        keep = []
        for Q in w['chains']:
            _, kq = T.query(Q)
            if np.sign(np.median(((Q - C[kq]) * NL[kq]).sum(1))) == sg:
                keep.append(Q)
        P = np.vstack(keep) if keep else np.zeros((0, 2))
    else:
        P = np.asarray(w['pts'], float)
    if not len(P):
        return {}
    _, k = cKDTree(C).query(P)
    lat = sg * ((P - C[k]) * NL[k]).sum(1)
    out = {}
    for kk in np.unique(k):
        v = float(np.median(lat[k == kk]))
        add = 0.0
        for a, b, *shift in w.get('kerb_inside', []):
            if shift:
                # a measured shift (the band's outer limit from his line, compare/owner_kerbs.py): full over the zone,
                # ramped in over ceil(shift / KERB_STEP) stations before it and out after it; where two zones' ramps
                # meet, the larger shift (never their sum)
                r = int(np.ceil(shift[0] / KERB_STEP))
                d = 0 if (kk - a) % n <= (b - a) % n else min((a - kk) % n, (kk - b) % n)
                if d <= r:
                    add = max(add, shift[0] * (1.0 - d / (r + 1)))
                continue
            if (kk - a) % n <= (b - a) % n:
                # the kerb's width, ramped in over KERB_RAMP stations at each end of the run
                e = min((kk - a) % n, (b - kk) % n) + 1
                v += w.get('kerb_w', 0.9) * min(1.0, e / KERB_RAMP)
        out[int(kk)] = v + add
    return out


def periodic_basis(x, K, n):
    """cubic periodic B-spline design matrix: K coefficients on uniform knots over a loop of n stations."""
    h = n / K; t = (np.asarray(x, float) % n) / h; i = np.floor(t).astype(int); u = t - i
    B = np.zeros((len(t), K))
    b = [(1 - u) ** 3 / 6, (3 * u ** 3 - 6 * u ** 2 + 4) / 6, (-3 * u ** 3 + 3 * u ** 2 + 3 * u + 1) / 6, u ** 3 / 6]
    for m in range(4): np.add.at(B, (np.arange(len(t)), (i + m) % K), b[m])
    return B


# Local knot refinement (Sonoma round 14B part 1b, config spline.refine [(lo, hi, knot)] on the current centre's stations,
# set per local refit like OWNER): inside [lo, hi] a second layer of uniform cubic B-splines at `knot` stations is added to
# the periodic spline (only the functions whose support lies inside the zone, so the edge outside is the coarse spline's),
# with the same third-difference penalty on its coefficients. One curve per side, fitted in one least squares; empty
# (every config without spline.refine): the basis and the penalty are exactly the periodic ones.
REFINE = []


def _fine_basis(x, n):
    x = np.asarray(x, float) % n
    cols = []
    for lo, hi, h in REFINE:
        h = float(h); m = int((hi - lo) // h) - 3
        for j in range(max(m, 0)):
            u = (x - (lo + j * h)) / h
            b = np.zeros(len(x))
            for a, f in ((0, lambda v: v ** 3 / 6), (1, lambda v: (-3 * v ** 3 + 3 * v ** 2 + 3 * v + 1) / 6),
                         (2, lambda v: (3 * v ** 3 - 6 * v ** 2 + 4) / 6), (3, lambda v: (1 - v) ** 3 / 6)):
                sel = (u >= a) & (u < a + 1)
                b[sel] = f(u[sel] - a)
            cols.append(b)
    return np.array(cols).T if cols else np.zeros((len(x), 0))


def basis(x, K, n):
    """the fit's design matrix: the periodic spline, plus the refinement layer where REFINE is set"""
    B = periodic_basis(x, K, n)
    return np.hstack([B, _fine_basis(x, n)]) if REFINE else B


def _fine_penalty():
    blocks = []
    for lo, hi, h in REFINE:
        m = max(int((hi - lo) // float(h)) - 3, 0)
        blocks.append(np.diff(np.eye(m), 3, axis=0) if m >= 4 else np.zeros((0, m)))
    tot = sum(b.shape[1] for b in blocks)
    D = np.zeros((sum(b.shape[0] for b in blocks), tot)); r = c = 0
    for b in blocks:
        D[r:r + b.shape[0], c:c + b.shape[1]] = b; r += b.shape[0]; c += b.shape[1]
    return D


def periodic_fit(xo, yo, K, n, lam, huber, xp, yp, wp, xa=None, ya=None, wa=None, iters=8):
    """Robust penalised periodic spline: observations (Huber), a weak prior at every station (wp), and constraint
    anchors (declared straights, measured shapes: ya at stations xa with weights wa) inside the same least squares."""
    if REFINE:
        return _refined_fit(xo, yo, K, n, lam, huber, xp, yp, wp, xa, ya, wa, iters)
    B = periodic_basis(xo, K, n); Bp = periodic_basis(xp, K, n)
    D = np.zeros((K, K))
    for j in range(K):   # third difference, circulant
        for o, cf in ((0, -1), (1, 3), (2, -3), (3, 1)): D[j, (j + o) % K] += cf
    P = lam * D.T @ D + (Bp * np.asarray(wp)[:, None]).T @ Bp
    rhs0 = (Bp * np.asarray(wp)[:, None]).T @ yp
    if xa is not None and len(xa):
        Ba = periodic_basis(xa, K, n); P = P + (Ba * wa[:, None]).T @ Ba; rhs0 = rhs0 + (Ba * wa[:, None]).T @ ya
    rw = np.ones(len(xo))
    for _ in range(iters):
        A = (B * rw[:, None]).T @ B + P
        c = np.linalg.solve(A, (B * rw[:, None]).T @ yo + rhs0)
        r = np.abs(B @ c - yo); rw = np.where(r <= huber, 1.0, huber / np.maximum(r, 1e-9))
    return c


def _refined_fit(xo, yo, K, n, lam, huber, xp, yp, wp, xa, ya, wa, iters):
    """periodic_fit with the REFINE layer (same penalties: the coarse circulant third difference, the fine one per zone)"""
    B = basis(xo, K, n); Bp = basis(xp, K, n); M = B.shape[1]
    Dc = np.zeros((K, K))
    for j in range(K):
        for o, cf in ((0, -1), (1, 3), (2, -3), (3, 1)): Dc[j, (j + o) % K] += cf
    Df = _fine_penalty()
    P = np.zeros((M, M)); P[:K, :K] = lam * Dc.T @ Dc; P[K:, K:] = lam * Df.T @ Df
    P = P + (Bp * np.asarray(wp)[:, None]).T @ Bp
    rhs0 = (Bp * np.asarray(wp)[:, None]).T @ yp
    if xa is not None and len(xa):
        Ba = basis(xa, K, n); P = P + (Ba * wa[:, None]).T @ Ba; rhs0 = rhs0 + (Ba * wa[:, None]).T @ ya
    rw = np.ones(len(xo))
    for _ in range(iters):
        A = (B * rw[:, None]).T @ B + P
        c = np.linalg.solve(A, (B * rw[:, None]).T @ yo + rhs0)
        r = np.abs(B @ c - yo); rw = np.where(r <= huber, 1.0, huber / np.maximum(r, 1e-9))
    return c


def tight_mask(C, radius=100.0, win=30):
    """stations within +-win of a centre radius under `radius` (corners: the half-width legitimately bends there)."""
    from geo import curvature
    n = len(C); k = np.abs(curvature(C, sigma=5))
    tight = (1 / np.maximum(k, 1e-6)) < radius
    out = np.zeros(n, bool)
    for d in range(-win, win + 1): out |= np.roll(tight, d)
    return out


def ranges(mask, n):
    idx = np.flatnonzero(mask)
    if not len(idx): return []
    out = []; a = b = idx[0]
    for k in idx[1:]:
        if k == b + 1: b = k
        else: out.append((int(a), int(b))); a = b = k
    out.append((int(a), int(b)))
    if len(out) > 1 and out[0][0] == 0 and out[-1][1] == n - 1: out = [(out[-1][0], out[0][1])] + out[1:-1]
    return out


def fit_periodic(C, NL, hl, hr, tiles, features, sp, mpp, anchors=None, log=_log, hold=None):
    """ONE periodic robust spline per side over the whole lap (no runs, no seam, no post-fit overwrite). anchors:
    {'left'|'right': (stations, half-widths, weights)} from declared straights and measured shapes, inside the fit.
    Returns (hl, hr, report) with per-side metrics for the gates (build_track.py): share of associated observations
    within 0.25 m, share of capture rows with a band within 1.2 m, coverage, gaps, waviness and kink per station.
    hold (the local refit, config centre.local; None: off): {'w': (n,) weights, 'left' / 'right': (n,) half-widths}; the
    returned edge is w * fit + (1 - w) * held, and every metric is measured on that returned edge."""
    n = len(C); knot = sp['knot']; K = int(round(n / knot))
    OWNER[:] = list(sp.get('_owner') or [])
    REFINE[:] = list(sp.get('_refine') or [])
    win = sp.get('search', (-4.5, 4.0)); U_ = np.arange(win[0], win[1] + 1e-4, 0.04)
    obs = gather(C, NL, hl, hr, tiles, features, sp['line_off'], mpp, U_)
    xs = np.arange(n, dtype=float); Bx = basis(xs, K, n)
    tight = tight_mask(C)
    rep, out = {}, {}
    for side, hw in (('left', hl), ('right', hr)):
        O = obs[side]
        if not O:
            raise SystemExit(f'fit_periodic: no observations on the {side} side')
        xa = ya = wa = None
        if anchors and anchors.get(side):
            xa, ya, wa = (np.asarray(v, float) for v in anchors[side])
        # the owner's line (spline.owner_edges) as weighted anchors on this centre: it dominates its window
        for w in OWNER:
            if w['side'] == side:
                rd = owner_readings(C, NL, w, n)
                ks_ = [k for k in sorted(rd) if (k - w['lo']) % n <= (w['hi'] - w['lo']) % n]
                if ks_:
                    xa = np.r_[xa if xa is not None else [], np.array(ks_, float)]
                    ya = np.r_[ya if ya is not None else [], np.array([rd[k] for k in ks_])]
                    wa = np.r_[wa if wa is not None else [], np.full(len(ks_), OWNER_W)]
        wp = np.full(n, sp['prior'])
        xo_all = np.array([i for i, _, c, _ in O for _ in c], float); yo_all = np.array([y for _, _, c, _ in O for y in c])
        c0 = periodic_fit(xo_all, yo_all, K, n, sp['lam'] * sp['init_stiff'], 1.0, xs, hw, wp, xa, ya, wa)
        cur = Bx @ c0
        if hold is not None:   # the observations are associated with the edge that is returned (held outside the window)
            cur = hold['w'] * cur + (1.0 - hold['w']) * hold[side]
        # an owner window's stations associate his reading wherever it lies (his line is the evidence there; the outer
        # centre refits carry the edge to it); elsewhere the gate schedule below (zreach 0: unchanged)
        zreach = np.zeros(n)
        for w in OWNER:
            if w['side'] == side:
                zreach[np.arange(w['lo'], w['hi'] + (n if w['hi'] < w['lo'] else 0) + 1) % n] = 50.0
        for gate in (1.2, 1.0, 0.8, 0.6, 0.5, 0.5):
            xo, yo = [], []
            for i, _, c, _ in O:
                d = np.abs(np.array(c) - cur[i]); j = int(d.argmin())
                if d[j] <= max(gate, zreach[i]): xo.append(i); yo.append(c[j])
            xo = np.array(xo, float); yo = np.array(yo)
            cf = periodic_fit(xo, yo, K, n, sp['lam'], sp['huber'], xs, hw, wp, xa, ya, wa)
            cur = Bx @ cf
            if hold is not None:
                cur = hold['w'] * cur + (1.0 - hold['w']) * hold[side]
        # every capture row's nearest band to the final curve (not only the gated ones)
        allres = np.array([min(abs(y - cur[i]) for y in c) for i, _, c, _ in O])
        assoc = allres <= 1.2   # rows whose nearest band lies within the association window: observations OF this edge
        covered = np.zeros(n, bool); covered[xo.astype(int)] = True
        if xa is not None: covered[xa.astype(int) % n] = True     # a declared straight / shape is evidence too
        gaps = ranges(~covered, n); glen = [(b - a) % n + 1 for a, b in gaps]
        gi = int(np.argmax(glen)) if glen else 0
        qq = local_quad_resid(np.r_[cur[-25:], cur, cur[:25]], 25)[25:-25]
        roll = np.array([np.sqrt(np.mean(qq[np.arange(k - 50, k + 50) % n] ** 2)) for k in range(n)])
        cp = np.r_[cur[-1], cur, cur[0]]
        kink = np.degrees(np.abs(cp[2:] - 2 * cur + cp[:-2]))
        loose = ~tight
        rep[side] = dict(obs=int(len(xo)), candidates=int(len(O)), within=float(np.mean(allres[assoc] <= 0.25)),
                         within_all=float(np.mean(allres <= 0.25)), assoc_share=float(assoc.mean()),
                         off_hist=np.histogram(allres[assoc & (allres > 0.25)], bins=[0.25, 0.4, 0.6, 0.8, 1.0, 1.2])[0].tolist(),
                         within_gated=float(np.mean(np.abs(yo - (Bx[xo.astype(int)] @ cf if hold is None else cur[xo.astype(int)])) <= 0.25)),
                         covered=float(covered.mean()), longest_gap=int(glen[gi]) if glen else 0,
                         gap_at=gaps[gi] if glen else None, wave_rms=float(roll[loose].max()), wave_peak=float(np.abs(qq)[loose].max()),
                         kink=float(kink[loose].max()), kink_all=float(kink.max()), kink_at=int(np.argmax(np.where(loose, kink, 0))),
                         seam_kink=float(kink[0]), roll=roll, qq=qq, kinkv=kink, loose=loose, gaps=list(zip(gaps, glen)))
        # the associated readings' stations and signed residuals (diagnosis dumps, work/; never in the package)
        rep[side]['assoc_x'] = xo.astype(int); rep[side]['assoc_res'] = yo - cur[xo.astype(int)]
        own_k = {int(i_) for i_, ti_, c_, kd in O if ti_ == -1 and kd and kd[0] == 'owner'}
        rep[side]['assoc_owner'] = np.array([int(i) in own_k for i in xo.astype(int)], bool)
        out[side] = cur
        log(f"{side:5s} periodic fit: {len(xo)} of {len(O)} capture rows kept; within 0.25 m: {rep[side]['within_gated'] * 100:.1f} % of the "
            f"associated, {rep[side]['within'] * 100:.1f} % of the {rep[side]['assoc_share'] * 100:.0f} % of rows with a band within 1.2 m; "
            f"{covered.mean() * 100:.0f} % of stations covered, longest gap {rep[side]['longest_gap']} st at {rep[side]['gap_at']}; "
            f"station 0 kink {rep[side]['seam_kink']:.2f} deg")
    return out['left'], out['right'], rep
