"""The width-prior edge model (stage 1; Buttonwillow round 9, 22 Oct 2026; config `spline.width_model`).

Why (owner lap 3 note 27 and his zoomed crops): on Buttonwillow's 2026 captures the asphalt and the dirt are within ~18
grey levels, and the per-side asphalt-end detector, searching around the current edge, reads the far side of the
bleached shoulder: the fitted edges sat 1-2 m outside the asphalt and beyond the painted kerb bands, the width ran
10.7 / 13.1 / 16.4 m (p5 / p50 / p95) and wandered up to 1.8 m over 20-80 m. The owner: "In many of these, at least one
edge seems clearly detectable. If you assume a constant width, at least as a starting point, to find the opposite edge,
I think that would get you pretty close."

The model runs after the fitted method has converged (pass 1, edges_spline.fit_periodic as before) and keeps its
evidence fixed in WORLD coordinates, so the centre refits that follow cannot drag the detector's window:
 1. Evidence (gather_world): on every station and side, every clean capture's asphalt-end reading (the pipeline's own
    detector and window around the pass-1 edge) as a world point; and the kerb anchors: wherever the captures show a
    painted block band (compare/kerb_detect.py's periodic block pattern, searched from `kerb_offs` around the pass-1
    edge, runs of 6 m or more), the band's INSIDE line (the owner draws the edge to the inside of the kerb).
 2. Bias (estimate): the detector reads the kerb's own inner line where there is a kerb (reported: reading minus anchor
    at the kerb stations), so its outward bias on the asphalt-to-dirt shoulder is measured THROUGH the anchors, jointly
    with the section widths: a station with a kerb on one side and the detector on the other reads W + b(other side), a
    station with the detector on both sides reads W + b(left) + b(right); one robust (L1) fit over the lap gives one
    bias per side and one width per section. Every detector reading is corrected by its side's bias.
 3. One width per section (sections = the lap split at the declared junctions, `junctions` [(side, lo, hi, kind,
    src)]: road mouths, pit-in / pit-out, crossovers, aprons, and the owner's traced windows). Within a section the width
    is the constant W; in a junction range the measured local width (the corrected evidence's width, median over
    +-`local_half` stations) blended into the neighbouring section widths over `blend` stations at each end.
 4. Placement: at every station ONE mid-offset observation from the stronger side (kerb anchor, else the owner's line,
    else the corrected detector side with the higher confidence = the share of its captures within 0.25 m of their
    median), the other side at the width from it; a robust periodic spline through the mid observations (stiff:
    `mid_lam`); the edges mid +- w/2 enter the edge fit (edges_spline.fit_periodic) as constraints, with the corrected
    readings, the kerb anchors and the owner readings as its observations, so the edge is fitted, never traced, and the
    fit's gates run on the corrected evidence. Coverage counts evidence stations only (the constraints are not evidence).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- evidence (world points, gathered once)
def gather_world(cfg, C, NL, hl, hr, tiles, mpp, wm, mask=(), log=print):
    """Detector rows {side: (station0, capture, world xy)} and kerb anchors {side: (station0, world xy of the inside
    line, band width)} around the pass-1 edges (C, hl, hr)."""
    import edges_spline as ES
    from PIL import Image
    from captures import bilinear
    n = len(C); U = ES.U
    rows = {'left': [], 'right': []}
    for ti, t in enumerate(tiles):
        im = None
        for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
            lat = sg * (hw[:, None] + U[None, :])
            X = C[:, 0:1] + lat * NL[:, 0:1]; Y = C[:, 1:2] + lat * NL[:, 1:2]
            if not (np.hypot(X.mean(1) - t['x'], Y.mean(1) - t['y']) <= 100).any():
                continue
            if im is None:
                im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32)
                H, W = im.shape[:2]; mk = t['mask'](H, W)
            px = W / 2 + (X + t['dx'] - t['x']) / mpp; py = H / 2 - (Y + t['dy'] - t['y']) / mpp
            ins = (px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)
            rr = np.where(ins.mean(1) > 0.6)[0]
            if not len(rr):
                continue
            V = bilinear(im, np.clip(px[rr], 1, W - 2), np.clip(py[rr], 1, H - 2))
            val = ins[rr] & mk[np.clip(np.round(py[rr]).astype(int), 0, H - 1), np.clip(np.round(px[rr]).astype(int), 0, W - 1)]
            for v, ok, i in zip(V, val, rr):
                if any(m[0] == side and (i - m[1]) % n <= (m[2] - m[1]) % n for m in mask):
                    continue
                e = ES.asphalt_end(v, ok)
                if e is not None:
                    rows[side].append((int(i), ti, C[i] + sg * NL[i] * (hw[i] + e)))
    # kerb anchors: the periodic block pattern (compare/kerb_detect.py), the band nearest the pass-1 edge's kerb position
    sys.path.insert(0, os.path.join(HERE, 'compare'))
    import kerb_detect as KD
    from capsample import Sampler
    KD.OFFS = np.round(np.arange(wm.get('kerb_offs', (-5.0, 1.5))[0], wm.get('kerb_offs', (-5.0, 1.5))[1] + 0.01, 0.1), 2)
    T = dict(center=[[float(x), float(y), 0.0] for x, y in C], n=n, spacing_m=float(np.linalg.norm(np.roll(C, -1, 0) - C, axis=1).mean()),
             left=[[float(x), float(y)] for x, y in C + hl[:, None] * NL], right=[[float(x), float(y)] for x, y in C - hr[:, None] * NL])
    smp = Sampler(cfg)
    kerb = {}
    for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
        _, offs, _, _, _ = KD.detect(cfg, T, smp, sg)
        hit = np.array([bool(o) for o in offs])
        out = []
        for a, b in KD.runs(hit, n, gap=3, min_len=int(wm.get('kerb_min_len', 6))):
            ks, ins_, wid = [], [], []
            for k in range(a, b + 1):
                o = sorted(set(offs[k % n]))
                if not o:
                    continue
                cl = [[o[0], o[0]]]
                for v in o[1:]:
                    if v - cl[-1][1] <= 0.21: cl[-1][1] = v
                    else: cl.append([v, v])
                c = min(cl, key=lambda c: abs((c[0] + c[1]) / 2 - wm.get('kerb_expect', -0.45)))
                ks.append(k % n); ins_.append(c[0] - 0.05); wid.append(c[1] - c[0] + 0.1)
            if len(ks) < 4:
                continue
            from scipy.ndimage import median_filter
            ins_ = median_filter(np.array(ins_), min(5, len(ins_) - (1 - len(ins_) % 2)), mode='nearest')
            for k, e, w_ in zip(ks, ins_, wid):
                out.append((int(k), C[k] + sg * NL[k] * (hw[k] + e), float(w_)))
        kerb[side] = out
        log(f"width model: {side} kerb anchors on {len(out)} stations; detector rows {len(rows[side])}")
    return dict(rows=rows, kerb=kerb)


def project_pts(C, NL, P):
    from scipy.spatial import cKDTree
    P = np.asarray(P, float).reshape(-1, 2)
    _, k = cKDTree(C).query(P)
    return k, ((P - C[k]) * NL[k]).sum(1)


# ---------------------------------------------------------------- per-station evidence on the current centre
def station_evidence(C, NL, ev, n, owner=None):
    """Per side on the current centre: det_rows [(station, capture, half-width)], kerb (n,) inside-line half-width or
    nan, med / conf / cnt of the detector readings, owner (n,) the owner's reading or nan."""
    out = {}
    for side, sg in (('left', 1), ('right', -1)):
        R = ev['rows'][side]
        k, lat = project_pts(C, NL, [r[2] for r in R]) if R else (np.zeros(0, int), np.zeros(0))
        hw = sg * lat
        rows = [(int(a), R[j][1], float(b)) for j, (a, b) in enumerate(zip(k, hw))]
        by = {}
        for a, ti, v in rows:
            by.setdefault(a, []).append(v)
        med = np.full(n, np.nan); conf = np.zeros(n); cnt = np.zeros(n, int)
        for a, vs in by.items():
            m = float(np.median(vs)); med[a] = m; cnt[a] = len(vs)
            conf[a] = float(np.mean(np.abs(np.array(vs) - m) <= 0.25)) * min(1.0, len(vs) / 2.0)
        kb = np.full(n, np.nan)
        K = ev['kerb'][side]
        if K:
            kk, kl = project_pts(C, NL, [r[1] for r in K])
            acc = {}
            for a, v in zip(kk, sg * kl):
                acc.setdefault(int(a), []).append(float(v))
            for a, vs in acc.items():
                kb[a] = float(np.median(vs))
        ow = np.full(n, np.nan)
        for w in owner or []:
            if w['side'] == side:
                import edges_spline as ES
                for a, v in ES.owner_readings(C, NL, w, n).items():
                    if (a - w['lo']) % n <= (w['hi'] - w['lo']) % n:
                        ow[a] = v
        out[side] = dict(rows=rows, med=med, conf=conf, cnt=cnt, kerb=kb, owner=ow)
    return out


def span(lo, hi, n):
    return np.arange(lo, hi + (n if hi < lo else 0) + 1) % n


def sections(n, junctions, min_len=30):
    """jmask (n,) and the sections: maximal runs of non-junction stations [(lo, hi)] (wrapping); a run shorter than
    min_len stations between two junction ranges (Buttonwillow: 4 stations between the Pacific and infield-connector
    mouths) is part of the junction stretch, not a section."""
    jm = junction_stations(n, junctions)
    import edges_spline as ES
    for a, b in ES.ranges(~jm, n):
        if (b - a) % n + 1 < min_len:
            jm[span(a, b, n)] = True
    return jm, ES.ranges(~jm, n)


def junction_stations(n, junctions):
    jm = np.zeros(n, bool)
    for j in junctions:
        jm[span(j[1], j[2], n)] = True
    return jm


def junction_side(n, junctions):
    """per station the junction's side ('left', 'right', 'both' where both sides or two ranges meet, '' outside)"""
    js = np.full(n, '', dtype=object)
    for j in junctions:
        for k in span(j[1], j[2], n):
            js[k] = j[0] if js[k] in ('', j[0]) else 'both'
    return js


def sec_index(n, secs):
    si = np.full(n, -1)
    for i, (a, b) in enumerate(secs):
        si[span(a, b, n)] = i
    return si


# ---------------------------------------------------------------- bias and section widths
def estimate(E, n, secs, jm, min_obs=15, log=print, agree=0.6):
    """One L1 fit over the lap: per section W_s, per side bias b. Observations at non-junction stations:
    kerb L + kerb R = W; kerb L + det R = W + bR; det L + kerb R = W + bL; det L + det R = W + bL + bR."""
    si = sec_index(n, secs); S = len(secs)
    rows, y, kinds = [], [], []
    L, R = E['left'], E['right']
    for k in range(n):
        if jm[k] or si[k] < 0:
            continue
        kl, kr = not np.isnan(L['kerb'][k]), not np.isnan(R['kerb'][k])
        dl, dr = not np.isnan(L['med'][k]), not np.isnan(R['med'][k])
        # a detector side counts only where its captures agree (conf >= agree: the share of the station's captures
        # within 0.25 m of their median); a side whose captures scatter is not a width observation
        vl = L['kerb'][k] if kl else (L['med'][k] if dl and L['conf'][k] >= agree else None)
        vr = R['kerb'][k] if kr else (R['med'][k] if dr and R['conf'][k] >= agree else None)
        if vl is None or vr is None:
            continue
        a = np.zeros(S + 2); a[si[k]] = 1
        if not kl: a[S] = 1
        if not kr: a[S + 1] = 1
        rows.append(a); y.append(vl + vr); kinds.append(('K' if kl else 'D') + ('K' if kr else 'D'))
    A = np.array(rows); y = np.array(y); kinds = np.array(kinds)
    # sections with too few observations take the lap's width (their column is tied to a shared one)
    cnt = A[:, :S].sum(0)
    w = np.ones(len(y)); x = np.zeros(S + 2)
    for _ in range(60):
        Aw = A * w[:, None]
        reg = np.eye(S + 2) * 1e-6
        x = np.linalg.solve(Aw.T @ A + reg, Aw.T @ y)
        r = np.abs(A @ x - y); w = 1.0 / np.maximum(r, 0.05)
    W = x[:S].copy(); bL, bR = float(x[S]), float(x[S + 1])
    lapW = float(np.median(W[cnt >= min_obs])) if (cnt >= min_obs).any() else float(np.median(y))
    fallback = []
    for i in range(S):
        if cnt[i] < min_obs:
            W[i] = lapW; fallback.append(i)
    # the detector's reading minus the kerb anchor where both exist (report: at a kerb the detector reads the band)
    at_kerb = {}
    for side in ('left', 'right'):
        d = E[side]['med'] - E[side]['kerb']; d = d[~np.isnan(d)]
        at_kerb[side] = (int(len(d)), float(np.median(d)) if len(d) else float('nan'))
    res = y - A @ x
    log(f"width model: bias (outward, measured through the kerb anchors) left {bL:+.2f} m, right {bR:+.2f} m; "
        f"{len(y)} width observations ({', '.join(f'{t} {int(np.sum(kinds == t))}' for t in ('KK', 'KD', 'DK', 'DD'))}), "
        f"|residual| p50 {np.median(np.abs(res)):.2f} m; the detector at the kerb stations reads the band "
        f"{at_kerb['left'][1]:+.2f} (left, {at_kerb['left'][0]} st) / {at_kerb['right'][1]:+.2f} m (right, {at_kerb['right'][0]} st) from its inside line")
    return dict(W=W, bias={'left': bL, 'right': bR}, cnt=cnt.astype(int).tolist(), fallback=fallback, lapW=lapW,
                at_kerb=at_kerb, kinds={t: int(np.sum(kinds == t)) for t in ('KK', 'KD', 'DK', 'DD')},
                kinds_by_sec=[{t: int(np.sum((kinds == t) & (A[:, i] > 0))) for t in ('KK', 'KD', 'DK', 'DD')} for i in range(S)])


# ---------------------------------------------------------------- width function and placement
def corrected(E, bias):
    """per side (n,) the best evidence half-width: kerb anchor, else owner, else the detector median minus the bias;
    and its kind / weight"""
    out = {}
    for side in ('left', 'right'):
        e = E[side]; v = e['med'] - bias[side]
        # the owner's line rules his window; then the kerb anchor; then the corrected detector
        kind = np.where(~np.isnan(e['owner']), 'owner', np.where(~np.isnan(e['kerb']), 'kerb', np.where(~np.isnan(v), 'det', '')))
        val = np.where(~np.isnan(e['owner']), e['owner'], np.where(~np.isnan(e['kerb']), e['kerb'], v))
        out[side] = (val, kind, e['conf'])
    return out


def width_function(n, secs, W, junctions, Ev, local_half=15, blend=15):
    """w (n,): W of the section; in a junction range the local width, blended into the neighbouring sections' widths
    over `blend` stations at each end of the range (smoothstep). The local width by the range's kind:
      mouth (a road the course does not use): the road edge is carried across the mouth, i.e. the line between the
        neighbouring section widths (the pass-1 prior did the same, prior.interp);
      owner: the owner's two lines' width where he drew both; held from his nearest such station elsewhere in the range;
      pit-in / pit-out / apron (and any range where these meet a mouth): the corrected evidence's width, median over
        +-local_half stations where both sides have evidence (else the line between the section widths)."""
    jm = ~(sec_index(n, secs) >= 0)
    w = np.full(n, np.nan)
    for i, (a, b) in enumerate(secs):
        w[span(a, b, n)] = W[i]
    vl, kl = Ev['left'][0], Ev['left'][1]; vr, kr = Ev['right'][0], Ev['right'][1]
    both = vl + vr
    kinds = [set() for _ in range(n)]
    for jn in junctions:
        for k in span(jn[1], jn[2], n):
            kinds[k].add(jn[3])
    owner_both = (kl == 'owner') & (kr == 'owner')
    import edges_spline as ES
    for a, b in ES.ranges(jm, n):
        ks = span(a, b, n); m = len(ks)
        wa = w[(a - 1) % n]; wb = w[(b + 1) % n]
        kset = set().union(*[kinds[k] for k in ks])
        ob = [j for j, k in enumerate(ks) if owner_both[k]]
        loc = np.empty(m)
        for j, k in enumerate(ks):
            base = wa + (wb - wa) * (j + 0.5) / m
            if 'owner' in kset and ob:
                jj = min(ob, key=lambda x: abs(x - j)); loc[j] = both[ks[jj]]
            elif kset <= {'mouth'}:
                loc[j] = base
            else:
                win = both[span(k - local_half, k + local_half, n)]; win = win[~np.isnan(win)]
                loc[j] = np.clip(np.median(win), min(wa, wb) - 4, max(wa, wb) + 4) if len(win) >= 5 else base
        bl = min(blend, m // 2)
        for j, k in enumerate(ks):
            t = 1.0
            if j < bl: t = min(t, j / bl)
            if m - 1 - j < bl: t = min(t, (m - 1 - j) / bl)
            t = t * t * (3 - 2 * t)
            base = wa + (wb - wa) * (j + 0.5) / m
            w[k] = base + t * (loc[j] - base)
    return w


def weighted_periodic(x, y, wt, n, knot, lam, huber=0.3, iters=10):
    import edges_spline as ES
    K = int(round(n / knot)); B = ES.periodic_basis(x, K, n)
    D = np.zeros((K, K))
    for j in range(K):
        for o, cf in ((0, -1), (1, 3), (2, -3), (3, 1)): D[j, (j + o) % K] += cf
    P = lam * D.T @ D + 1e-6 * np.eye(K)
    rw = np.ones(len(y))
    for _ in range(iters):
        ww = wt * rw
        c = np.linalg.solve((B * ww[:, None]).T @ B + P, (B * ww[:, None]).T @ y)
        r = np.abs(B @ c - y); rw = np.where(r <= huber, 1.0, huber / np.maximum(r, 1e-9))
    return ES.periodic_basis(np.arange(n, dtype=float), K, n) @ c


def targets(n, Ev, w, wm, jside=None):
    """mid (n,) and the target half-widths: per station one mid observation from the stronger side. In a junction range
    of one side (jside) the observation comes from the other side, so the local width moves the junction's own edge;
    where the owner drew a side, that side's target is his line."""
    W_KERB, W_OWNER = float(wm.get('w_kerb', 10.0)), float(wm.get('w_owner', 40.0))
    x, y, wt, src = [], [], [], np.full(n, '', dtype=object)
    vl, kl, cl = Ev['left']; vr, kr, cr = Ev['right']
    rank = {'kerb': 3, 'owner': 2, 'det': 1, '': 0}
    for k in range(n):
        cands = []
        js = jside[k] if jside is not None else ''
        for side, v, kd, cf, sg in (('left', vl[k], kl[k], cl[k], 1), ('right', vr[k], kr[k], cr[k], -1)):
            if not kd or (js == side and kd != 'owner' and (kl[k] if side == 'right' else kr[k])):
                continue
            m = (v - w[k] / 2) if sg > 0 else (w[k] / 2 - v)
            wt_ = W_KERB if kd == 'kerb' else W_OWNER if kd == 'owner' else max(cf, 0.05)
            cands.append((rank[kd], wt_, m, side, kd))
        if not cands:
            continue
        cands.sort(key=lambda c: (c[0], c[1]), reverse=True)
        top = [c for c in cands if c[0] == cands[0][0] and (c[0] > 1 or abs(c[1] - cands[0][1]) < 1e-9)]
        if top[0][0] >= 2 and len(top) == 2:
            # both sides anchored (kerb / owner on both): both lines, the width there is theirs
            for c in top:
                x.append(k); y.append(c[2]); wt.append(c[1])
            src[k] = 'both ' + top[0][4]
        elif top[0][0] == 1 and len(cands) == 2 and cands[1][0] == 1:
            # detector on both sides: both observations, each weighted by its confidence (the more consistent side
            # dominates in proportion; a hard pick flips between sides from station to station)
            for c in cands:
                x.append(k); y.append(c[2]); wt.append(c[1])
            src[k] = 'det both'
        else:
            c = top[0]
            x.append(k); y.append(c[2]); wt.append(c[1]); src[k] = f"{c[3]} {c[4]}"
    mid = weighted_periodic(np.array(x, float), np.array(y), np.array(wt), n, int(wm.get('mid_knot', 6)), float(wm.get('mid_lam', 300.0)))
    tl, tr = mid + w / 2, w / 2 - mid
    tl = np.where(kl == 'owner', vl, tl); tr = np.where(kr == 'owner', vr, tr)
    return mid, tl, tr, src


def observations(E, bias, n):
    """the edge fit's observations (edges_spline.fit_periodic's obs format): the corrected detector rows (dropped at a
    kerb-anchored station and within 3 stations of an owner reading), one row per kerb-anchored station, one per owner
    reading"""
    obs = {}
    for side in ('left', 'right'):
        e = E[side]
        kb, ow = ~np.isnan(e['kerb']), ~np.isnan(e['owner'])
        near_ow = np.zeros(n, bool)
        for k in np.flatnonzero(ow):
            near_ow[span(k - 3, k + 3, n)] = True
        o = [(a, ti, [v - bias[side]], ['det']) for a, ti, v in e['rows'] if not kb[a] and not near_ow[a]]
        o += [(int(k), -2, [float(e['kerb'][k])], ['kerb']) for k in np.flatnonzero(kb) if not near_ow[k]]
        o += [(int(k), -1, [float(e['owner'][k])], ['owner']) for k in np.flatnonzero(ow)]
        obs[side] = o
    return obs
