"""Geometry gate for a track package's edges (18 Oct 2026). Pure python. Library (gate()) for build_track.py, which
fails the geometry stage on it, and a CLI for any package:

    python3 -I tools/track/edge_gate.py [--track public/tracks/laguna_seca] [--config laguna_seca]

Prints per side: (1) rms of the half-width about its 41-station running median over stations whose centre radius is
over 250 m (straights; gate `straight_rms`, Laguna's accepted edges 0.07/0.06 m); (2) the max adjacent half-width step
outside tight corners (radius > 100 m at every station within +-30) and outside the junctions in config
`gate.exempt` (gate `step`); (3) the max change between adjacent stations of each profile
column relative to the centre column, i.e. the cross-section shape (gate `profile_step`); then, when the package has a
scenery.json, the wall gaps of config `gate.wall_gaps` (p10/p50/p90, advisory) and the max adjacent half-width step
within +-35 stations of each bridge, and the exit-overshoot lines (advisory: they also fire on real features, each is
checked on the captures).
Also the fitted method's thresholds (FITTED) and, for an unpainted side (owner's decision of 20 Oct 2026, UNPAINTED;
asphalt_end_majority), the bias gate over all its readings that replaces the 0.25 m share there (side_within_gate,
bias_gate, unpainted_thresholds); per_kind_report prints the numbers per evidence kind, never gated.
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))


# Acceptance of the fitted method (build-track skill: 90 %+ of observations within 0.25 m; edges_spline.py: rolling
# waviness <= 0.04 m, peak <= 0.10 m, kink <= 0.5 deg/station; the share is of the associated observations, as the skill
# measured it, and at least 85 % of capture rows must hold a band within 1.2 m of the curve), coverage and gaps (20 Oct 2026: at least 60 % of
# stations with evidence, no stretch over 60 m without), and world-space continuity (the third difference of each edge
# polyline under 2 cm: a 2 cm step shows there, a smooth curve does not). Where the owner traced an edge (spline.owner_edges,
# Buttonwillow 21 Oct 2026; ported for Sonoma round 14B) the fitted edge follows his line: within owner_tol (0.25 m) of his reading at >= owner_within (90 %) of the
# window's stations and never more than owner_max (0.5 m) off (his stroke is ~0.3 m wide at 0.1 m/px). A config can
# tighten these, never loosen.
FITTED = dict(within=0.90, assoc=0.85, covered=0.60, gap=60, wave_rms=0.04, wave_peak=0.10, kink=0.5, world_d3=0.02,
              owner_within=0.90, owner_tol=0.25, owner_max=0.5)
_TIGHTER = dict(within=max, assoc=max, covered=max, gap=min, wave_rms=min, wave_peak=min, kink=min, world_d3=min,
                owner_within=max, owner_tol=min, owner_max=min)


def fitted_thresholds(g):
    g = g or {}
    return {k: _TIGHTER[k](v, g.get('fit_' + k, v)) for k, v in FITTED.items()}


# Unpainted sides (the owner's decision, 20 Oct 2026 14:00, Buttonwillow): on a side with no painted edge line the
# curve must run through the middle of the ragged evidence, with the fit-quality gates binding; painted circuits are
# untouched. A side is unpainted when asphalt_end readings are the majority of its associated readings
# (asphalt_end_majority). On Buttonwillow's 2026 captures and 2021 lidar the asphalt-to-dirt transition is 2-4 m wide:
# the readings agree across captures (98 % within 0.25 m of their station's median) but scatter along the track (46-50 %
# within 0.25 m of the fitted edge). An unpainted side's within gate is the BIAS gate over ALL its associated readings
# (asphalt_end and kerb pooled): over rolling 41-station windows holding at least 10 readings, the median signed residual
# (reading minus fitted edge) lies within +-0.25 m in at least 90 % of the windows (the worst window printed; the spread
# is the edge's own, printed, not gated), and its coverage is held to 50 % of stations. Kerb readings are pooled because
# the grey block bands of an unpainted circuit blur on the captures like the asphalt end (Buttonwillow: 85-86 % within
# 0.25 m, a 0.25-0.6 m tail, zone medians within +-0.05 m; first-centre round). The per-kind numbers are a printed report,
# never gated. A painted side keeps FITTED over all its readings, computed exactly as before. Longest gap, waviness, kink,
# the edge gate, world continuity and profile are unchanged; a config can tighten, never loosen (gate.fit_covered also
# applies when higher). The owner's named fallback for a circuit worse than this, "the owner draws the edges on the
# captures", is the owner-traced edge (spline.owner_edges): his red lines on a capwin frame, read by
# compare/owner_edges.py into world points per station, dominate the fit in their window (the gate above holds it).
UNPAINTED = dict(window=41, min_readings=10, bias=0.25, bias_windows=0.90, covered=0.50)


def asphalt_end_majority(kinds):
    """True when most of a side's associated readings come from the asphalt_end feature: the side is unpainted.
    kinds: the feature kind of each associated reading's station ('asphalt_end', 'kerb_band', None for painted ...)."""
    kinds = list(kinds)
    return bool(kinds) and sum(k == 'asphalt_end' for k in kinds) * 2 > len(kinds)


unpainted_side = asphalt_end_majority


def side_within_gate(r, n, G):
    """The within gate of one side from the fit's report r (edges_spline.fit_periodic): an unpainted side (asphalt_end
    majority) takes the bias gate over all its associated readings; a painted side FITTED's share over all its readings,
    the original computation. Returns dict(unpainted, ok, bias (or None))."""
    if asphalt_end_majority(r['assoc_kind']):
        bg = bias_gate(r['assoc_x'], r['assoc_res'], n)
        return dict(unpainted=True, ok=bool(bg['ok'] and r['assoc_share'] >= G['assoc']), bias=bg)
    return dict(unpainted=False, ok=r['within_gated'] >= G['within'] and r['assoc_share'] >= G['assoc'], bias=None)


def per_kind_report(kinds, residuals):
    """Report only (never gated): per evidence kind, readings, share of the side, and share within 0.25 m."""
    import numpy as np
    k = np.array([x or 'painted' for x in kinds], dtype=object); r = np.asarray(residuals, float); out = {}
    for name in sorted(set(k.tolist())):
        m = k == name
        out[name] = dict(n=int(m.sum()), share=float(m.mean()), within=float(np.mean(np.abs(r[m]) <= 0.25)))
    return out


def bias_gate(stations, residuals, n, window=None, min_readings=None, tol=None, share=None):
    """The unpainted side's bias gate: rolling `window`-station windows (wrapping the lap) holding at least
    `min_readings` associated readings; returns dict(ok, share (of windows with |median| <= tol), windows, worst
    (median, centre station, lo, hi), spread (p10, p50, p90 of |residual|))."""
    import numpy as np
    U = UNPAINTED; window = window or U['window']; min_readings = min_readings or U['min_readings']
    tol = U['bias'] if tol is None else tol; share = U['bias_windows'] if share is None else share
    st = np.asarray(stations, int) % n; r = np.asarray(residuals, float); h = window // 2
    order = np.argsort(st); st, r = st[order], r[order]
    meds = []
    for k in range(n):
        lo, hi = k - h, k + h
        if lo < 0: m = (st >= lo % n) | (st <= hi)
        elif hi >= n: m = (st >= lo) | (st <= hi % n)
        else: m = (st >= lo) & (st <= hi)
        if m.sum() >= min_readings: meds.append((float(np.median(r[m])), k))
    if not meds:
        return dict(ok=False, share=0.0, windows=0, worst=None, spread=None)
    good = np.mean([abs(v) <= tol for v, _ in meds]); worst = max(meds, key=lambda x: abs(x[0]))
    a = np.abs(r)
    return dict(ok=bool(good >= share), share=float(good), windows=len(meds),
                worst=(round(worst[0], 3), worst[1], (worst[1] - h) % n, (worst[1] + h) % n),
                spread=tuple(round(float(v), 3) for v in np.percentile(a, [10, 50, 90])) if len(a) else None)


def unpainted_thresholds(g):
    """FITTED for an unpainted side, with its coverage term (a config may only tighten)."""
    t = fitted_thresholds(g); g = g or {}
    t['covered'] = max(UNPAINTED['covered'], g.get('fit_covered', UNPAINTED['covered']))
    return t


# Width gates (Buttonwillow round 9, 22 Oct 2026; owner lap 3 note 27: "it seems to have a relatively uniform width
# (except where the 'usable' track interfaces with track segments that aren't used, or service roads)"). Both REQUIRED
# for a config with spline.width_model (its junction ranges declare the exceptions), both measured on the package:
#  (a) width consistency: the lap is split into sections at the declared junction ranges; a section's width is the
#      median of its stations' widths; at every station outside a junction range |width - section width| <= tol;
#  (b) waviness: each edge's lateral offset from the centreline, with the junction ranges bridged by a straight line,
#      band-passed to 20-80 m (difference of Gaussians, sigma = 0.1874 x wavelength: the half-power points at 20 and
#      80 m); |band-pass| <= wave at every station outside the junction ranges.
# The 41-station-median, step and third-difference gates measure smoothness only; these measure the width the owner
# sees. A config may tighten (gate.width_tol, gate.width_wave), never loosen.
WIDTH = dict(tol=0.30, wave=0.30, band=(20.0, 80.0))


def width_thresholds(g):
    g = g or {}
    return dict(tol=min(WIDTH['tol'], g.get('width_tol', WIDTH['tol'])), wave=min(WIDTH['wave'], g.get('width_wave', WIDTH['wave'])),
                band=WIDTH['band'])


# The owner's reference (Buttonwillow round 10, the owner's decision of 23 Oct 2026 18:32-18:35, point 3: "his red wins
# over the gates where he drew both edges"). On the stations where his traced red exists on BOTH sides
# (spline.owner_edges), the width gate measures the fit's width against the width between his lines instead of against
# a section constant, and on every edge he drew the per-edge gates (his-red tolerance, 20-80 m band, rolling waviness)
# measure that edge against his red instead of against its own shape; everywhere no owner edge exists every gate is
# computed exactly as before (owner=None: the unchanged
# code path, test_owner_reference.py holds it on a detected-edge fixture). Stations where his red runs ACROSS a mouth
# (the 'red across' cone-line segments of spline.owner_mouths, projected on the current centre by world position) are
# left out on that side, widened by `corner` stations at each end: there the cones hold the boundary and the asphalt
# edge rounds the corner. The numbers are derived, not tuned to pass:
#  - corner = 12 stations: half the support of one cubic B-spline basis function at the fit's 6-station knots (4 knot
#    intervals = 24 stations), the reach over which the spline cuts a corner in his red. Round 10: his red bulges up
#    to 1 m into a mouth before it crosses (right 2528-2537); the exceedances lie 1-12 stations past the segment ends.
#  - tol = 0.40 m at EVERY such station, for each edge (fit minus his reading, kerb shifts included) and for the width
#    (fit width minus the width between his lines), from his stroke accuracy: where two of his round-10 windows
#    overlap, his two drawings of one edge differ by more than 0.3 m at 756 of 1677 left and 639 of 1793 right
#    stations, a median 0.49 / 0.46 m where they do (compare/owner_merge.py tol 0.3, owner/r10/merged_report.json).
#    A fit within 0.40 m of the cross-faded line sits inside his own repeatability. The 0.25 m first proposed holds at
#    99.7 % of these stations; the approved fit's 12 edge and 21 width stations at 0.25-0.36 m are listed in
#    compare/buttonwillow/round10/LEDGER.md. The per-window share gate (>= 90 % within owner_tol 0.25 m) is unchanged.
#  - waviness: the 20-80 m band of (fit offset - his offset) <= WIDTH wave (0.30 m), the other stations bridged by a
#    straight line; the rolling-100 fit waviness (rms of the residual about a +-25-station quadratic, and its peak) may
#    not exceed max(FITTED wave_rms, his red's own rolling rms there) and max(FITTED wave_peak, his red's largest
#    |residual| in the same 100-station window): the fit adds no wave his red does not have. Measured on (fit - red)
#    alone it would gate the wiggle of his stroke, which the smoother fit does not follow.
# Sonoma round 14B: a 'junction step' of spline.owner_mouths (his red ending on one line and resuming on another where
# a lane joins, the pit-exit mouth after T1; compare/owner_mouths.py --step) is left out the same way: there too the
# asphalt edge turns a corner the spline cannot follow.
# A config may tighten tol (gate.owner_ref_tol), never loosen; corner is code-defined.
OWNER_REF = dict(tol=0.40, corner=12)


def owner_ref_thresholds(g):
    g = g or {}
    return dict(tol=min(OWNER_REF['tol'], g.get('owner_ref_tol', OWNER_REF['tol'])), corner=OWNER_REF['corner'])


def owner_reference(C, readings, across_lines, n, corner=None, fill=5):
    """The owner's reference on centre C (n x 2). readings {'left'|'right': {station: half-width}} (his red, kerb shifts
    included: edges_spline.owner_readings); across_lines [(side, P (m x 2 world xy))]: his red across a mouth.
    Gaps of <= `fill` stations in a side's readings are interpolated. Returns dict(left, right: n arrays (nan without
    a reading), both: bool n (both sides read), across / excl: {side: bool n} (the segments; widened by `corner`),
    edge: {side: his reading on that side & ~excl[side]} (the stations an edge is gated on against his red; an edge
    gate is per edge, so where he drew that edge his red is its reference), width: both & ~(excl left | excl right)
    (the width needs both of his lines))."""
    import numpy as np
    from scipy.spatial import cKDTree
    corner = OWNER_REF['corner'] if corner is None else corner
    C = np.asarray(C, float)[:, :2]; out = {}
    for side in ('left', 'right'):
        v = np.full(n, np.nan)
        for k, x in (readings.get(side) or {}).items():
            v[int(k) % n] = x
        ok = ~np.isnan(v)
        if ok.any() and not ok.all():
            for a, b in _runs(~ok, n):
                m = (b - a) % n + 1
                if m <= fill:
                    va, vb = v[(a - 1) % n], v[(b + 1) % n]
                    for j in range(m):
                        v[(a + j) % n] = va + (vb - va) * (j + 1) / (m + 1)
        out[side] = v
    both = ~np.isnan(out['left']) & ~np.isnan(out['right'])
    kd = cKDTree(C); across = {s: np.zeros(n, bool) for s in ('left', 'right')}; excl = {}
    for side, P in across_lines:
        _, i = kd.query(np.asarray(P, float)[:, :2]); i = np.sort(i)
        if i[-1] - i[0] > n / 2:
            i = np.sort(np.where(i < n / 2, i + n, i))
        across[side][np.arange(i[0], i[-1] + 1) % n] = True
    for side in ('left', 'right'):
        e = across[side].copy()
        for a, b in _runs(across[side], n):
            e[np.arange(a - corner, b + (n if b < a else 0) + corner + 1) % n] = True
        excl[side] = e
    return dict(left=out['left'], right=out['right'], both=both, across=across, excl=excl,
                edge={s: ~np.isnan(out[s]) & ~excl[s] for s in excl}, width=both & ~(excl['left'] | excl['right']))


def owner_station_gate(hl, hr, ref, g=None, log=print):
    """Each edge within tol of his reading at every reference station (OWNER_REF). Returns (metrics, fails)."""
    import numpy as np
    G = owner_ref_thresholds(g); met = {}; fails = []
    for side, hw in (('left', hl), ('right', hr)):
        m = ref['edge'][side]
        if not m.any():
            continue
        hw = np.asarray(hw, float); d = np.where(m, np.abs(hw - np.nan_to_num(ref[side])), 0.0)
        k = int(np.argmax(d)); over = np.flatnonzero(m & (d > G['tol'])); o25 = np.flatnonzero(m & (d > 0.25))
        met[side] = dict(max=float(d[k]), at=k, stations=int(m.sum()), over=over.tolist(),
                         over_025=[(int(j), round(float(hw[j] - ref[side][j]), 3)) for j in o25])
        ok = not len(over)
        log(f"[{'ok' if ok else 'FAIL'}] owner reference {side:5s}: {int(m.sum())} stations of his {side} edge (mouth segments +-{G['corner']} left out): "
            f"max |fit - his red| {d[k]:.3f} m at station {k} (<= {G['tol']} at every station); {len(o25)} stations over 0.25 m")
        if not ok: fails.append(f'owner reference {side}')
    return met, fails


def owner_waviness(qq_fit, roll_fit, loose, own, mask, n):
    """The rolling-100 fit waviness against his red (OWNER_REF): his reading bridged over the non-reference stations,
    its residual about a +-25-station quadratic and its rolling rms over the loose reference stations; returns
    (roll_limit, peak_limit) per station = max(FITTED, his red's own) and the stations over either."""
    import numpy as np
    from edges_spline import local_quad_resid
    idx = np.flatnonzero(mask)
    o = np.interp(np.arange(n), idx, np.asarray(own)[idx], period=n)
    qo = local_quad_resid(np.r_[o[-25:], o, o[:25]], 25)[25:-25]
    lo = loose & mask
    ro = np.zeros(n); po = np.zeros(n)
    for k in range(n):
        w = np.arange(k - 50, k + 50) % n; m = lo[w]
        if m.sum() >= 50:   # the rms needs the original's 50-station sample (edges_spline / build_track roll)
            ro[k] = np.sqrt(np.mean(qo[w][m] ** 2))
        if m.any():         # a peak is a max: any loose reference station of the window
            po[k] = np.abs(qo[w][m]).max()
    rl = np.maximum(FITTED['wave_rms'], ro); pl = np.maximum(FITTED['wave_peak'], po)
    bad_r = lo & (np.asarray(roll_fit) > rl); bad_p = lo & (np.abs(qq_fit) > pl)
    return dict(roll_limit=rl, peak_limit=pl, bad_roll=bad_r, bad_peak=bad_p, red_roll_max=float(ro[lo].max()) if lo.any() else 0.0)


def junction_mask(n, junctions):
    import numpy as np
    jm = np.zeros(n, bool)
    for j in junctions:
        lo, hi = j[1], j[2]
        jm[np.arange(lo, hi + (n if hi < lo else 0) + 1) % n] = True
    return jm


def _runs(mask, n):
    import numpy as np
    idx = np.flatnonzero(mask)
    if not len(idx):
        return []
    out = []; a = b = idx[0]
    for k in idx[1:]:
        if k == b + 1: b = k
        else: out.append((int(a), int(b))); a = b = k
    out.append((int(a), int(b)))
    if len(out) > 1 and out[0][0] == 0 and out[-1][1] == n - 1:
        out = [(out[-1][0], out[0][1])] + out[1:-1]
    return out


def half_widths(T):
    import numpy as np
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
    return ((L - C) * NL).sum(1), -((R - C) * NL).sum(1)


def band_pass(v, jm, sp, band):
    """the 20-80 m band of a periodic per-station signal, junction stations bridged by a straight line first"""
    import numpy as np
    from scipy.ndimage import gaussian_filter1d
    n = len(v); x = np.asarray(v, float).copy()
    for a, b in _runs(jm, n):
        if (b - a) % n + 1 >= n: continue
        va, vb = x[(a - 1) % n], x[(b + 1) % n]; m = (b - a) % n + 1
        for j in range(m):
            x[(a + j) % n] = va + (vb - va) * (j + 1) / (m + 1)
    s1, s2 = 0.1874 * band[0] / sp, 0.1874 * band[1] / sp
    return gaussian_filter1d(x, s1, mode='wrap') - gaussian_filter1d(x, s2, mode='wrap')


def width_gates(T, junctions, g=None, log=print, owner=None):
    """(a) width consistency and (b) 20-80 m waviness (WIDTH). Returns (metrics, fails). With `owner`
    (owner_reference on this package's centre), the stations where he drew both edges are measured against his red
    (OWNER_REF) and left out of the section and offset checks, which run on the other stations exactly as before;
    owner=None is the original computation."""
    import numpy as np
    G = width_thresholds(g); n, sp = T['n'], T['spacing_m']
    hl, hr = half_widths(T); w = hl + hr
    jm = junction_mask(n, junctions); fails = []; met = {'sections': []}
    if owner is not None:
        return _width_gates_owner(T, jm, G, g, log, owner, hl, hr, w, n, sp)
    worst = (0.0, None, None); bad = 0
    for a, b in _runs(~jm, n):
        ks = np.arange(a, b + (n if b < a else 0) + 1) % n
        W = float(np.median(w[ks])); d = w[ks] - W; i = int(np.argmax(np.abs(d)))
        bad += int(np.sum(np.abs(d) > G['tol']))
        met['sections'].append(dict(lo=int(a), hi=int(b), W=round(W, 2), max_dev=round(float(np.abs(d).max()), 3), at=int(ks[i])))
        if abs(d[i]) > worst[0]: worst = (float(abs(d[i])), int(ks[i]), (int(a), int(b)))
    ok = bad == 0
    met['width'] = dict(max_dev=worst[0], at=worst[1], stations_over=bad, of=int((~jm).sum()))
    log(f"[{'ok' if ok else 'FAIL'}] width consistency: {len(met['sections'])} sections outside the junction ranges; max |width - section width| "
        f"{worst[0]:.3f} m at station {worst[1]} (section {worst[2]}); {bad} of {int((~jm).sum())} stations over {G['tol']} m (<= {G['tol']} everywhere)")
    if not ok: fails.append('width consistency')
    for side, v in (('left', hl), ('right', hr)):
        bp = band_pass(v, jm, sp, G['band']); a_ = np.abs(bp); a_[jm] = 0
        k = int(np.argmax(a_)); over = int(np.sum(a_ > G['wave']))
        met['wave_' + side] = dict(max=float(a_[k]), at=k, p95=float(np.percentile(np.abs(bp)[~jm], 95)), stations_over=over)
        ok = over == 0
        log(f"[{'ok' if ok else 'FAIL'}] edge waviness {side:5s}: 20-80 m band of the offset from the centre, max {a_[k]:.3f} m at station {k}, "
            f"p95 {met['wave_' + side]['p95']:.3f} m; {over} stations over {G['wave']} m outside the junction ranges (<= {G['wave']})")
        if not ok: fails.append(f'edge waviness {side}')
    return met, fails


def _width_gates_owner(T, jm, G, g, log, ref, hl, hr, w, n, sp):
    """width_gates with the owner's reference: (a) on his both-edge stations (mouth segments +-corner left out)
    |fit width - his width| <= OWNER_REF tol at every station; on the stations he did not draw on both sides, the
    section check as before; (b) on his stations the 20-80 m band of (fit offset - his offset) <= wave, elsewhere the
    band of the offset as before."""
    import numpy as np
    GO = owner_ref_thresholds(g); fails = []; met = {'sections': []}
    own = ref['both']; old = ~jm & ~own   # the section check where the width has no reference (not both of his lines)
    worst = (0.0, None, None); bad = 0
    for a, b in _runs(old, n):
        ks = np.arange(a, b + (n if b < a else 0) + 1) % n
        W = float(np.median(w[ks])); d = w[ks] - W; i = int(np.argmax(np.abs(d)))
        bad += int(np.sum(np.abs(d) > G['tol']))
        met['sections'].append(dict(lo=int(a), hi=int(b), W=round(W, 2), max_dev=round(float(np.abs(d).max()), 3), at=int(ks[i])))
        if abs(d[i]) > worst[0]: worst = (float(abs(d[i])), int(ks[i]), (int(a), int(b)))
    mw = ref['width']; wo = ref['left'] + ref['right']
    dw = np.where(mw, np.abs(w - np.nan_to_num(wo)), 0.0); kw = int(np.argmax(dw))
    over = np.flatnonzero(mw & (dw > GO['tol'])); o25 = np.flatnonzero(mw & (dw > 0.25))
    ok = bad == 0 and not len(over)
    met['width'] = dict(max_dev=worst[0], at=worst[1], stations_over=bad, of=int(old.sum()))
    met['width_owner'] = dict(max=float(dw[kw]), at=kw, stations=int(mw.sum()), over=over.tolist(),
                              over_025=[(int(j), round(float(w[j] - wo[j]), 3)) for j in o25])
    log(f"[{'ok' if ok else 'FAIL'}] width consistency: on his both-edge stations ({int(mw.sum())}, mouth segments +-{GO['corner']} left out) "
        f"max |fit width - his width| {dw[kw]:.3f} m at station {kw} (<= {GO['tol']} at every station; {len(o25)} over 0.25 m); "
        f"elsewhere {len(met['sections'])} sections outside the junction ranges, max |width - section width| {worst[0]:.3f} m at station {worst[1]}, "
        f"{bad} of {int(old.sum())} stations over {G['tol']} m")
    if not ok: fails.append('width consistency')
    for side, v in (('left', hl), ('right', hr)):
        mo = ref['edge'][side]
        hs = ~np.isnan(ref[side])   # his line on this side: its band is measured against it
        bp = band_pass(v, jm | hs, sp, G['band']); a_ = np.abs(bp); a_[jm | hs] = 0
        dev = v - np.nan_to_num(ref[side])
        bq = band_pass(dev, ~mo, sp, G['band']); b_ = np.where(mo, np.abs(bq), 0.0)
        k = int(np.argmax(a_)); ko = int(np.argmax(b_))
        over = int(np.sum(a_ > G['wave'])) + int(np.sum(b_ > G['wave']))
        met['wave_' + side] = dict(max=float(a_[k]), at=k, owner_max=float(b_[ko]), owner_at=ko,
                                   owner_p95=float(np.percentile(b_[mo], 95)) if mo.any() else 0.0, stations_over=over)
        ok = over == 0
        log(f"[{'ok' if ok else 'FAIL'}] edge waviness {side:5s}: 20-80 m band of (fit - his red) on his {int(mo.sum())} stations max {b_[ko]:.3f} m at station {ko} "
            f"(p95 {met['wave_' + side]['owner_p95']:.3f}); of the offset from the centre elsewhere max {a_[k]:.3f} m at station {k}; "
            f"{over} stations over {G['wave']} m (<= {G['wave']})")
        if not ok: fails.append(f'edge waviness {side}')
    return met, fails


def owner_gates(T, ref, g=None, log=print):
    """The owner's reference gates for a circuit WITHOUT a width model (Sonoma round 14B, decision d14: the tolerance
    design accepted for Buttonwillow round 10, OWNER_REF): (a) on his both-edge stations (mouth segments +-corner left
    out) |fit width - the width between his lines| <= OWNER_REF tol at every station; (b) on each edge he drew, the
    20-80 m band of (fit offset - his offset) <= WIDTH wave (0.30 m), the other stations bridged. Where he drew nothing
    no station is measured here; every other gate is computed exactly as before. Returns (metrics, fails)."""
    import numpy as np
    GO = owner_ref_thresholds(g); G = width_thresholds(g); n, sp = T['n'], T['spacing_m']
    hl, hr = half_widths(T); w = hl + hr; fails = []; met = {}
    mw = ref['width']
    if mw.any():
        wo = ref['left'] + ref['right']
        dw = np.where(mw, np.abs(w - np.nan_to_num(wo)), 0.0); kw = int(np.argmax(dw))
        over = np.flatnonzero(mw & (dw > GO['tol'])); o25 = np.flatnonzero(mw & (dw > 0.25))
        met['width_owner'] = dict(max=float(dw[kw]), at=kw, stations=int(mw.sum()), over=over.tolist(),
                                  over_025=[(int(j), round(float(w[j] - wo[j]), 3)) for j in o25])
        ok = not len(over)
        log(f"[{'ok' if ok else 'FAIL'}] owner width: on his both-edge stations ({int(mw.sum())}, mouth segments +-{GO['corner']} left out) "
            f"max |fit width - his width| {dw[kw]:.3f} m at station {kw} (<= {GO['tol']} at every station); {len(o25)} stations over 0.25 m")
        if not ok: fails.append('owner width')
    for side, v in (('left', hl), ('right', hr)):
        mo = ref['edge'][side]
        if not mo.any():
            continue
        dev = v - np.nan_to_num(ref[side])
        bq = band_pass(dev, ~mo, sp, G['band']); b_ = np.where(mo, np.abs(bq), 0.0); ko = int(np.argmax(b_))
        over = int(np.sum(b_ > G['wave']))
        met['band_' + side] = dict(max=float(b_[ko]), at=ko, p95=float(np.percentile(b_[mo], 95)), stations=int(mo.sum()), stations_over=over)
        ok = over == 0
        log(f"[{'ok' if ok else 'FAIL'}] owner band {side:5s}: 20-80 m band of (fit - his red) on his {int(mo.sum())} stations max {b_[ko]:.3f} m "
            f"at station {ko} (p95 {met['band_' + side]['p95']:.3f}); {over} stations over {G['wave']} m (<= {G['wave']})")
        if not ok: fails.append(f'owner band {side}')
    return met, fails


# Declared junction corners (config gate.continuity_exemptions, Sonoma round 14B part 1b, coordinator decision 24 Oct 2026):
# [dict(side, lo, hi, reason, evidence)] on config stations (trackcfg remaps them). Where the course edge has a
# real pavement angle (his red across an escape road's mouth and its two corners), the world-continuity gate and the
# stage-1 edge-jump gate leave those stations out and REPORT them as "exempt (junction corner)" with the measured value,
# never as a pass; within each entry the published edge must be straight (
# every edge point within EXEMPT_CHORD m of the chord between the stretch's end points) OR smooth per metre (resampled at
# 1 m arc length: |third difference| <= the gate's limit, curvature radius >= EXEMPT_RADIUS), checked here, so an
# exemption cannot hide a kink. Absent (every other config): nothing changes.
EXEMPT_CHORD = 0.10
EXEMPT_RADIUS = 6.0
STEP_SPAN = 2   # a declared step's jog spans at most this many station intervals


def exemptions(g, C):
    """gate.continuity_exemptions on centre C (n x 2): each entry's stretch from its two world points on his red ('enu',
    ENU x, y: the stretch's corners) as the nearest stations of C, so re-stationing cannot move it. Returns
    [dict(entry, lo, hi)] in driving order (lo before hi)."""
    import numpy as np
    from scipy.spatial import cKDTree
    out = []
    E = (g or {}).get('continuity_exemptions') or []
    if not E:
        return out
    C = np.asarray(C, float)[:, :2]; n = len(C); kd = cKDTree(C)
    for e in E:
        a, b = (int(kd.query(np.asarray(p, float))[1]) for p in e['enu'])
        if (b - a) % n > n // 2:
            a, b = b, a
        out.append(dict(e, lo=a, hi=a + (b - a) % n))
    return out


def exempt_stations(g, side, n, C=None, pad=(0, 0)):
    """the stations a side's exemptions cover on centre C, widened by pad (before, after): the world-continuity stencil
    (k-1 .. k+2) of a station within (lo - 2, hi + 1) reaches the stretch's corners"""
    out = set()
    if C is None:
        return out
    for e in exemptions(g, C):
        if e['side'] == side:
            out |= {k % n for k in range(e['lo'] - pad[0], e['hi'] + pad[1] + 1)}
    return out


def continuity_exemption_report(T, g):
    """one line per declared entry: the third difference and the edge-jump inside it (exempt), and its shape check"""
    import numpy as np
    out = []
    n = T['n']; C = np.array(T['center'])[:, :2]
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
    for e in exemptions(g, C):
        side = e['side']; sg = 1 if side == 'left' else -1
        E = np.array(T[side])[:, :2]
        ks = np.array([k % n for k in range(int(e['lo']), int(e['hi']) + (n if int(e['hi']) < int(e['lo']) else 0) + 1)])
        d3 = np.linalg.norm(E[(ks + 2) % n] - 3 * E[(ks + 1) % n] + 3 * E[ks] - E[(ks - 1) % n], axis=1)
        h = sg * ((E - C) * NL).sum(1); jump = np.abs(h[(ks + 1) % n] - h[ks])
        P = E[ks]; c = P[-1] - P[0]; L = float(np.linalg.norm(c)) or 1.0
        dev = float(np.abs((P - P[0]) @ (np.array([-c[1], c[0]]) / L)).max())
        # or smooth per metre (coordinator, 24 Oct 2026): the stretch with 3 stations either side, resampled at 1 m arc
        # length: |third difference| <= the gate's limit and the curvature radius >= EXEMPT_RADIUS (the per-station limit
        # is spacing-dependent: on the outside of a tight corner the edge stations sit 1.3-1.6 m apart)
        thr = fitted_thresholds(g)['world_d3']
        kx = np.array([k % n for k in range(int(e['lo']) - 3, int(e['hi']) + (n if int(e['hi']) < int(e['lo']) else 0) + 4)])
        Q = E[kx]; u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
        from scipy.interpolate import CubicSpline
        # the curve through the edge's stations (a cubic in arc length; a linear resample would read each station's
        # own vertex as a kink) sampled every metre
        um = np.arange(0, u[-1] + 1e-9, 1.0); M = CubicSpline(u, Q)(um)
        d3m = float(np.linalg.norm(M[3:] - 3 * M[2:-1] + 3 * M[1:-2] - M[:-3], axis=1).max()) if len(M) > 3 else 0.0
        hd = np.arctan2(np.diff(M[:, 1]), np.diff(M[:, 0])); dh = np.abs((np.diff(hd) + np.pi) % (2 * np.pi) - np.pi)
        rmin = float(1.0 / max(dh.max(), 1e-9)) if len(dh) else float('inf')
        straight = dev <= EXEMPT_CHORD
        smooth = d3m <= thr and rmin >= EXEMPT_RADIUS
        ok = straight or smooth
        case = 'straight' if straight else ('smooth per metre' if smooth else 'neither')
        if e.get('kind') == 'step' and not ok:
            # a declared step in his red (the hairpin apron's ends): the edge jogs over ONE station interval (a straight
            # segment, its two ends the corners) and is smooth per metre on either side of it inside the stretch
            # the jog: the station intervals round the largest one where the half-width changes by more than max(0.2 m,
            # 0.35 x the largest), at
            # most STEP_SPAN of them (his notch crosses one or two stations' normals); the pieces either side smooth per
            # metre. The jog's own points lie on his notch (the owner gates hold them to his red)
            i0 = int(np.argmax(jump[:-1])); a_i = b_i = i0; thj = max(0.2, 0.35 * float(jump[i0]))
            while a_i - 1 >= 0 and jump[a_i - 1] > thj: a_i -= 1
            while b_i + 1 < len(ks) - 1 and jump[b_i + 1] > thj: b_i += 1
            j, j2 = int(ks[a_i]), int(ks[b_i]) + 1
            devj = 0.0 if (j2 - j) <= STEP_SPAN else 9.9
            parts = []
            for a_, b_ in ((int(e['lo']) - 3, j), (j2, int(e['hi']) + 3)):
                Q = E[np.arange(a_, b_ + 1) % n]; u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
                M = CubicSpline(u, Q)(np.arange(0, u[-1] + 1e-9, 1.0)) if len(Q) > 2 else Q
                dd = float(np.linalg.norm(M[3:] - 3 * M[2:-1] + 3 * M[1:-2] - M[:-3], axis=1).max()) if len(M) > 3 else 0.0
                hd_ = np.arctan2(np.diff(M[:, 1]), np.diff(M[:, 0])); dh_ = np.abs((np.diff(hd_) + np.pi) % (2 * np.pi) - np.pi)
                parts.append((dd, float(1.0 / max(dh_.max(), 1e-9)) if len(dh_) else float('inf')))
            ok = all(dd <= thr and rr >= EXEMPT_RADIUS for dd, rr in parts) and devj <= EXEMPT_CHORD
            case = (f"step (jog {j}-{j2}, {j2 - j} station interval(s) <= {STEP_SPAN}; either side per metre "
                    + ", ".join(f"|d3| {dd:.4f} R {rr:.1f}" for dd, rr in parts) + ")") if ok else 'neither'
            d3m, rmin = max(p_[0] for p_ in parts), min(p_[1] for p_ in parts)
        out.append((f"[{'exempt' if ok else 'FAIL'}] world continuity / edge jumps {side:5s} {int(e['lo'])}-{int(e['hi'])}: exempt (junction corner): "
                    f"per station max |third difference| {d3.max():.4f} m, max half-width change {jump.max():.3f} m; shape {case}: "
                    f"chord deviation {dev:.3f} m (<= {EXEMPT_CHORD}); at 1 m arc length |third difference| {d3m:.4f} m (<= {thr}), "
                    f"min radius {rmin:.1f} m (>= {EXEMPT_RADIUS}); {e.get('reason', '')[:80]}", ok))
    return out


def world_continuity(T, exempt=None):
    """max |third difference| of the left and right edge polylines (world metres) and where; exempt: stations left out
    (gate.continuity_exemptions, the same set for both sides' call; each side passes its own through gate())."""
    out = {}
    for side in ('left', 'right'):
        E = T[side]; n = len(E); best = (0.0, 0)
        ex = exempt.get(side, set()) if isinstance(exempt, dict) else set()
        for k in range(n):
            if k in ex:
                continue
            a, b, c, d = E[(k - 1) % n], E[k], E[(k + 1) % n], E[(k + 2) % n]
            v = math.hypot(d[0] - 3 * c[0] + 3 * b[0] - a[0], d[1] - 3 * c[1] + 3 * b[1] - a[1])
            if v > best[0]: best = (v, k)
        out[side] = best
    return out


def gate(T, SC=None, g=None, log=print, world=False):
    """T: track.json dict; SC: scenery.json dict or None; g: config `gate` dict. Returns (metrics, fails)."""
    g = g or dict(straight_rms=0.10, step=0.10, profile_step=0.10)
    n, sp = T['n'], T['spacing_m']; C, L, R, Z = T['center'], T['left'], T['right'], T['profile']['z']; ci = T['profile']['fractions'].index(0)
    fails, met = [], {}

    def nl(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l
    H = []
    for k in range(n):
        nx, ny = nl(k); c = C[k]
        H.append(((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny)))
    head = [math.atan2(C[(k + 1) % n][1] - C[k][1], C[(k + 1) % n][0] - C[k][0]) for k in range(n)]
    kap = [abs(((head[(k + 1) % n] - head[k] + math.pi) % (2 * math.pi) - math.pi) / sp) for k in range(n)]
    kap = [sum(kap[(k + d) % n] for d in range(-5, 6)) / 11 for k in range(n)]
    rad = [1 / max(x, 1e-6) for x in kap]
    # outside tight corners: the centre radius over 100 m at every station within +-30 (an S-bend's inflection, where the
    # local radius is large between two tight corners, does not count)
    loose = [all(rad[(k + d) % n] > 100 for d in range(-30, 31)) for k in range(n)]
    for si, side in enumerate(('left', 'right')):
        v = [h[si] for h in H]
        med = [sorted(v[(k + d) % n] for d in range(-20, 21))[20] for k in range(n)]
        st = [k for k in range(n) if rad[k] > 250]
        rms = math.sqrt(sum((v[k] - med[k]) ** 2 for k in st) / len(st))
        ex = set()
        for sd, lo, hi, _ in g.get('exempt', []):
            if sd == side: ex |= set(k % n for k in range(lo, hi + (n if hi < lo else 0) + 1))
        steps = [(abs(v[(k + 1) % n] - v[k]), k) for k in range(n) if loose[k] and k not in ex]
        col = 0 if side == 'left' else len(Z[0]) - 1
        zs = max((abs((Z[(k + 1) % n][col] - Z[(k + 1) % n][ci]) - (Z[k][col] - Z[k][ci])), k) for k in range(n))
        top = sorted(steps, reverse=True)[:3]
        met[side] = dict(straight_rms=rms, step=top[0][0], step_at=top[0][1], edge_col_step=zs[0])
        ok = rms <= g['straight_rms'] and top[0][0] <= g['step']
        log(f'[{"ok" if ok else "FAIL"}] edge gate {side:5s}: rms vs 41-st median (R>250 m, {len(st)} st) {rms:.3f} m '
            f'(<= {g["straight_rms"]}) | max adjacent step (R>100 m within +-30) {top[0][0]:.3f} m at {top[0][1]} (next {top[1][0]:.3f}@{top[1][1]}, '
            f'{top[2][0]:.3f}@{top[2][1]}; <= {g["step"]}) | max edge-column cross-section step {zs[0]:.3f} m at {zs[1]}')
        if not ok: fails.append(f'edge gate {side}')
    if world:
        import numpy as np
        thr = fitted_thresholds(g)['world_d3']
        for side, (v, k) in world_continuity(T, {sd: exempt_stations(g, sd, n, np.array(T['center'])[:, :2], (2, 1)) for sd in ('left', 'right')}).items():
            met[side]['world_d3'] = v
            ok = v <= thr
            log(f'[{"ok" if ok else "FAIL"}] world continuity {side:5s}: max |third difference| of the edge polyline {v:.4f} m at station {k} (<= {thr})'
                + (' outside the declared junction corners' if g.get('continuity_exemptions') else ''))
            if not ok: fails.append(f'world continuity {side}')
        for line, ok in continuity_exemption_report(T, g):
            log(line)
            if not ok: fails.append('continuity exemption shape')
    allcol = max((abs((Z[(k + 1) % n][c] - Z[(k + 1) % n][ci]) - (Z[k][c] - Z[k][ci])), k, c) for k in range(n) for c in range(len(Z[0])))
    met['profile_step'] = allcol[0]
    ok = allcol[0] <= g['profile_step']
    log(f'[{"ok" if ok else "FAIL"}] profile gate: max cross-section step any column {allcol[0]:.3f} m at station {allcol[1]} column {allcol[2]} (<= {g["profile_step"]})')
    if not ok: fails.append('profile gate')
    if SC:
        for side, kind, lo, hi in g.get('wall_gaps', []):
            sg = 1 if side == 'left' else -1
            pts = [p for b in SC['barriers'] if b['kind'] == kind for p in b['pts']]; gaps = []
            for k in (list(range(lo, n)) + list(range(0, hi + 1)) if hi < lo else range(lo, hi + 1)):
                e = (L if side == 'left' else R)[k]; nx, ny = nl(k); nx, ny = nx * sg, ny * sg; best = None
                for p in pts:
                    d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
                    if -2 < d < 15 and lat < 2 and (best is None or d < best): best = d
                if best is not None: gaps.append(best)
            if gaps:
                gaps.sort(); q = lambda f: gaps[int(f * (len(gaps) - 1))]
                log(f'wall gap {side} to {kind} ({lo}-{hi}, {len(gaps)} st): p10 {q(0.1):.2f} p50 {q(0.5):.2f} p90 {q(0.9):.2f} m')
        for br in SC.get('bridges', []):
            k0 = int(round(br['s'] / sp))
            for si, side in enumerate(('left', 'right')):
                m = max(abs(H[(k + 1) % n][si] - H[k % n][si]) for k in range(k0 - 35, k0 + 35))
                log(f'bridge s={br["s"]:7.1f} (station {k0}) {side}: max adjacent half-width step within +-35 {m:.3f} m')
    # corner exits widen once (owner, 18 Oct 2026, T11 exit: a 2.8 m swell 100 m after the apex): within the first 120
    # stations after the centre radius is back over 150 m, the ROAD WIDTH must not overshoot its value at the window end
    # by more than 1 m. Advisory: it fires on real features too (pit-out merge, pit rejoin, a kerb narrowing the road).
    kap = [abs(((head[(k + 1) % n] - head[k] + math.pi) % (2 * math.pi) - math.pi) / sp) for k in range(n)]
    kap = [sum(kap[(k + d) % n] for d in range(-3, 4)) / 7 for k in range(n)]
    for c in T.get('corners', []):
        k0 = int(round(c['s'] / sp))
        ks = [k for k in range(k0, k0 + 150) if kap[k % n] < 1 / 150.0]
        if len(ks) < 40: continue
        start = ks[0]; wid = [H[k % n][0] + H[k % n][1] for k in range(start, start + 120)]
        mx = max(wid); im = wid.index(mx); over = mx - wid[-1]
        if over > 1.0 and im < 110: log(f"exit overshoot (advisory) {c.get('name', '?'):14s}: road width +{over:.2f} m over its value 120 m on, at station {(start + im) % n} (exit from {start}, end width {wid[-1]:.1f} m)")
    return met, fails


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', default=os.path.join(ROOT, 'public/tracks/laguna_seca'))
    ap.add_argument('--config', default=None, help='track id whose config `gate` thresholds apply')
    a = ap.parse_args()
    d = a.track if os.path.isdir(a.track) else os.path.dirname(a.track)
    T = json.load(open(os.path.join(d, 'track.json')))
    scp = os.path.join(d, 'scenery.json'); SC = json.load(open(scp)) if os.path.exists(scp) else None
    g = None
    if a.config:
        sys.path.insert(0, HERE); import trackcfg; cfg = trackcfg.load(a.config); g = cfg['gate']
    _, fails = gate(T, SC, g)
    if a.config and cfg['spline'].get('width_model'):
        # the width gates on this package's stations (junction ranges mapped by world position, SKILL 1.3)
        import numpy as np
        cw = trackcfg.remap_stations(cfg, T['n'], T['n'] * T['spacing_m'], C=np.array(T['center'])[:, :2])
        ref = None
        if cfg['spline'].get('owner_edges') and cfg['spline'].get('owner_mouths'):
            # the owner's reference on this package's centre (round 10)
            import build_track
            C = np.array(T['center'])[:, :2]
            ref = build_track.owner_ref(cfg, cw, C, T['n'])
            _, f3 = owner_station_gate(*half_widths(T), ref, g); fails += f3
        _, f2 = width_gates(T, cw['spline']['width_model']['junctions'], g, owner=ref)
        fails += f2
    elif a.config and cfg['spline'].get('owner_edges') and cfg['spline'].get('owner_mouths'):
        # no width model (Sonoma round 14B): the owner's reference gates on this package's centre where he drew
        import numpy as np
        import build_track
        C = np.array(T['center'])[:, :2]
        cw = trackcfg.remap_stations(cfg, T['n'], T['n'] * T['spacing_m'], C=C)
        ref = build_track.owner_ref(cfg, cw, C, T['n'])
        fails += owner_station_gate(*half_widths(T), ref, g)[1]
        fails += owner_gates(T, ref, g)[1]
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
