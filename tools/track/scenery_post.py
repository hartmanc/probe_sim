"""Stage 3 post steps on a freshly built scenery.json (tools/track/build_track.py --stage scenery), in this order, each
from the track config's `scenery` block. Each was a one-off script on 18 Oct 2026 (named in brackets); its effect is
now config:

  shoulder_zones   paved shoulder from the track edge to 1.5 m short of the nearest wall of `wall` kind, level with the
                   road (its own cross-slope continued, clamped to 3 %), tapered over 12 m [fix_front_straight.py (B)]
  aprons           paved aprons beyond the painted edge measured on the captures: walking out from the edge, pavement =
                   grey / olive-grey (red ~ green; the local dirt is red > green by 15-25) or green-blue apron paint;
                   the apron ends at the first 0.8 m that is not pavement (or at apron_max m); median 9 stations,
                   Gaussian 3, capped 1.5 m short of the nearest barrier, at least 0.4 m, 12 m tapers [add_paved_aprons.py]
  pitwall_end      pit-wall points in lo..hi within 3 m of the left edge removed (where a painted strip, not a wall,
                   separates the pit-out lane) [fix_pitwall_exit.py]
  pitwall_setback  pit-wall points in lo..hi closer than `min` outside the left edge moved out to it [fix_pitwall_nose.py]
  pitwall_straight pit-wall points in lo..hi more than tol off the RANSAC line of the wall over fit_lo..fit_hi projected
                   onto it [fix_pitwall_straight.py]
  kerb_extents     a kerb strip's s0/s1 set from a measurement [fix_kerb_strip.py]
  edge_line_runs   painted edge-line runs added or merged [fix_edge_line_run.py]
  pit_exit_cones   the cone line extended back to s0 along the pit-lane boundary (it starts where the wall ends)
                   [fix_pit_exit_cones.py]
Stations are track stations; s0/s1 values are metres, as in scenery.json.
"""
import math

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, median_filter

from captures import bilinear
from geo import log as _log
from straights import ransac


def geometry(T):
    C = np.array(T['center'])[:, :2]
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    return C, NL, ((L - C) * NL).sum(1), -((R - C) * NL).sum(1)


def span(lo, hi, n):
    return [k % n for k in range(lo, hi + (n if hi < lo else 0) + 1)]


def shoulder_zone(T, SC, z):
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']
    side = z.get('side', 'right')
    if side != 'right':
        raise SystemExit('shoulder_zones: only right-hand shoulders are implemented (Laguna front straight)')

    def rnormal(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return ty / l, -tx / l

    def hw(k):
        nx, ny = rnormal(k); c = C[k]
        return -((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny), (R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny
    stations = span(z['lo'], z['hi'], n)
    walls = [p for b in SC['barriers'] if b['kind'] == z.get('wall', 'concrete') for p in b['pts']]

    def wall_gap(k):
        e = R[k]; nx, ny = rnormal(k); best = None
        for p in walls:
            d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
            if 0 < d < 30 and lat < 3 and (best is None or d < best): best = d
        return best
    gaps = [wall_gap(k) for k in stations]
    last = next((g for g in gaps if g is not None), 4.0)
    for i, g in enumerate(gaps):
        if g is None: gaps[i] = last
        else: last = g
    w = [max(1.0, min(12.0, g - 1.5)) for g in gaps]
    w = [sum(w[max(0, i - 4):i + 5]) / len(w[max(0, i - 4):i + 5]) for i in range(len(w))]
    m = len(stations)
    for i in range(m):
        d = min(i, m - 1 - i)
        if d < 12: t = d / 12; w[i] = 0.4 + (w[i] - 0.4) * (t * t * (3 - 2 * t))
    pts_c, pts_l, pts_r, prof, gl, gr = [], [], [], [], [], []
    for i, k in enumerate(stations):
        e = R[k]; nx, ny = rnormal(k)
        hl, hr = hw(k); x5, x6 = -fr[5] * hr, -fr[6] * hr
        slope = (Z[k][6] - Z[k][5]) / (x6 - x5) if abs(x6 - x5) > 1e-6 else 0.0
        slope = max(-0.03, min(0.03, -slope))
        zc = [round(e[2] + slope * w[i] * (f + 1) / 2, 3) for f in fr]
        pts_l.append([round(e[0], 3), round(e[1], 3), zc[0]])
        pts_r.append([round(e[0] + nx * w[i], 3), round(e[1] + ny * w[i], 3), zc[-1]])
        pts_c.append([round(e[0] + nx * w[i] / 2, 3), round(e[1] + ny * w[i] / 2, 3), zc[3]])
        prof.append(zc); gl.append(0.0); gr.append(99)
    return {'n': m, 'turn': z['turn'], 'center': pts_c, 'left': pts_l, 'right': pts_r, 'profile_z': prof,
            'gap_left': gl, 'gap_right': gr, 'track_s': [round(z['lo'] * sp, 1), round(z['hi'] * sp, 1)], 'note': z.get('note', '')}


def sample_profiles(C, NL, hw, sg, ks, offs, tiles, mpp, regs=None):
    """RGB along the outward normal at offsets offs from the edge, per station, from the capture covering the whole
    profile (clear of its mask) where the profile sits most central. regs: per-capture shifts by name (else t dx/dy)."""
    P = np.full((len(ks), len(offs), 3), np.nan, np.float32); cache = {}
    for i, k in enumerate(ks):
        lat = sg * (hw[k] + offs); X = C[k, 0] + lat * NL[k, 0]; Y = C[k, 1] + lat * NL[k, 1]; best = None
        for t in tiles:
            if t['name'] not in cache:
                im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32); cache[t['name']] = (im, t['mask'](*im.shape[:2]))
            im, m = cache[t['name']]; H, W = im.shape[:2]
            if regs is not None:
                r = regs.get(t['name']); dx, dy = (r[1], r[2]) if r and r[3] >= 8 else (0, 0)
            else:
                dx, dy = t['dx'], t['dy']
            px = W / 2 + (X + dx - t['x']) / mpp; py = H / 2 - (Y + dy - t['y']) / mpp
            if not ((px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)).all(): continue
            if not m[np.round(py).astype(int), np.round(px).astype(int)].all(): continue
            v = bilinear(im, px, py)
            sc = abs(px.mean() - W * 0.6) / W + abs(py.mean() - H / 2) / H
            if best is None or sc < best[0]: best = (sc, v)
        if best: P[i] = best[1]
    return P


def aprons(T, SC, aprons_cfg, tiles, mpp, wmax=10.0, regs=None, log=_log):
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']
    C, NL, hl, hr = geometry(T)
    walls = [p for b in SC['barriers'] for p in b['pts']]
    parts = []
    for turn, side, s0, s1, why in aprons_cfg:
        sg = 1 if side == 'left' else -1; hw = hl if side == 'left' else hr; E = np.array(T[side])
        ks = list(range(s0, s1 + 1)); offs = np.arange(0.15, wmax + 1e-9, 0.1)
        P = sample_profiles(C, NL, hw, sg, ks, offs, tiles, mpp, regs)
        w = np.full(len(ks), np.nan)
        for i, v in enumerate(P):
            if np.isnan(v[0, 0]): continue
            br = v.mean(1); sat = v.max(1) - v.min(1)
            teal = (v[:, 2] - v[:, 0] > 15) & (v[:, 1] - v[:, 0] > 15)
            pave = ((np.abs(v[:, 0] - v[:, 1]) < 12) & (br > 60) & (sat < 45)) | teal
            bad = np.convolve(~pave, np.ones(8), 'valid') >= 7
            j = int(np.argmax(bad)) if bad.any() else len(offs) - 1
            w[i] = offs[j]
        idx = np.arange(len(w)); ok = ~np.isnan(w)
        if not ok.any():
            log(f'  apron {turn}: no capture covers it, skipped'); continue
        w = np.interp(idx, idx[ok], w[ok])
        w = gaussian_filter1d(median_filter(w, 9, mode='nearest'), 3, mode='nearest'); raw = np.median(w)
        for i, k in enumerate(ks):
            e = E[k, :2]; nx, ny = sg * NL[k]
            for p in walls:
                d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
                if 0 < d < w[i] + 1.5 and lat < 3: w[i] = max(0.4, d - 1.5)
        w = np.maximum(w, 0.4); m = len(ks)
        for i in range(m):
            d = min(i, m - 1 - i)
            if d < 12: t = d / 12; w[i] = 0.4 + (w[i] - 0.4) * (t * t * (3 - 2 * t))
        pc, pl, pr, prof, gl, gr = [], [], [], [], [], []
        for i, k in enumerate(ks):
            e = E[k]; nx, ny = sg * NL[k]
            x5, x6 = (fr[1] * -hw[k], fr[0] * -hw[k]) if side == 'left' else (-fr[5] * hw[k], -fr[6] * hw[k])
            za, zb = (Z[k][1], Z[k][0]) if side == 'left' else (Z[k][5], Z[k][6])
            slope = max(-0.03, min(0.03, (zb - za) / (abs(x6 - x5) or 1)))
            outer = [e[0] + nx * w[i], e[1] + ny * w[i]]
            zc = [round(e[2] + slope * w[i] * (f + 1) / 2, 3) for f in fr]
            if side == 'right':
                L_, R_ = [e[0], e[1], zc[0]], [outer[0], outer[1], zc[-1]]; gl.append(0.0); gr.append(99); prof.append(zc)
            else:
                zc = zc[::-1]; L_, R_ = [outer[0], outer[1], zc[0]], [e[0], e[1], zc[-1]]; gl.append(99); gr.append(0.0); prof.append(zc)
            pl.append([round(v, 3) for v in L_]); pr.append([round(v, 3) for v in R_])
            pc.append([round((L_[0] + R_[0]) / 2, 3), round((L_[1] + R_[1]) / 2, 3), zc[3]])
        parts.append({'n': m, 'turn': turn, 'center': pc, 'left': pl, 'right': pr, 'profile_z': prof, 'gap_left': gl,
                      'gap_right': gr, 'track_s': [round(s0 * sp, 1), round(s1 * sp, 1)], 'note': why})
        log(f'  apron {turn:16s} {side:5s} {s0}-{s1}: measured p50 {raw:.1f} m; width p50 {np.median(w):.1f} m, min {w.min():.1f}, max {w.max():.1f}')
    return parts


def station_finder(C):
    C = np.asarray(C)[:, :2]
    return lambda p: int(np.argmin(np.hypot(C[:, 0] - p[0], C[:, 1] - p[1])))


def pitwall_end(T, SC, c, log=_log):
    st = station_finder(T['center']); L = T['left']; removed = 0
    for run in SC['barriers']:
        if run.get('kind') != 'pitwall': continue
        keep = []
        for p in run['pts']:
            k = st(p)
            if c['lo'] < k <= c['hi'] and math.hypot(L[k][0] - p[0], L[k][1] - p[1]) < 3.0: removed += 1; continue
            keep.append(p)
        run['pts'] = keep
    SC['barriers'] = [b for b in SC['barriers'] if len(b['pts']) >= 2]
    log(f'  pit-wall end: {removed} points removed over stations {c["lo"]}..{c["hi"]}')


def pitwall_setback(T, SC, c, log=_log):
    n = T['n']; C, L = T['center'], T['left']; st = station_finder(C); moved = 0

    def lnormal(k):
        p, q = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = q[0] - p[0], q[1] - p[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l
    for run in SC['barriers']:
        if run.get('kind') != 'pitwall': continue
        for p in run['pts']:
            k = st(p)
            if not (c['lo'] <= k <= c['hi']): continue
            nx, ny = lnormal(k); g = (p[0] - L[k][0]) * nx + (p[1] - L[k][1]) * ny
            if -3.0 < g < c['min']:
                p[0] = round(L[k][0] + nx * c['min'], 3); p[1] = round(L[k][1] + ny * c['min'], 3); moved += 1
    log(f'  pit-wall set-back: {moved} points moved out to {c["min"]} m from the left edge over {c["lo"]}..{c["hi"]}')


def pitwall_straight(T, SC, c, log=_log):
    n = T['n']; st = station_finder(T['center'])
    ks = set(span(c['lo'], c['hi'], n)); fit = set(span(c['fit_lo'], c['fit_hi'], n))
    pw = np.array([p[:2] for b in SC['barriers'] if b['kind'] == 'pitwall' for p in b['pts']])
    sel = np.array([st(p) in fit for p in pw])
    m, d, nin = ransac(pw[sel], c.get('tol', 0.25), min_len=60); nr = np.array([-d[1], d[0]]); moved = 0
    for b in SC['barriers']:
        if b['kind'] != 'pitwall': continue
        for i, p in enumerate(b['pts']):
            r = (np.array(p[:2]) - m) @ nr
            if st(p) in ks and abs(r) > c.get('tol', 0.25):
                q = np.array(p[:2]) - r * nr; moved += 1; b['pts'][i] = [round(float(q[0]), 3), round(float(q[1]), 3)] + list(p[2:])
    log(f'  pit-wall straight: line from {nin} inliers; {moved} points projected onto it')


def kerb_extent(SC, c, log=_log):
    cands = [s for s in SC['kerbs']['strips'] if s['side'] == c['side'] and s.get('kind') == c['kind'] and abs(s['s0'] - c['near']) < 60]
    if len(cands) != 1:
        raise SystemExit(f'kerb_extents: {len(cands)} strips match {c}')
    cands[0]['s0'], cands[0]['s1'] = c['s0'], c['s1']; cands[0]['src'] = c.get('why', '')
    log(f'  kerb extent side {c["side"]} {c["kind"]}: s {c["s0"]}..{c["s1"]}')


def edge_line_run(SC, c, log=_log):
    runs = SC['edge_lines']['runs']; s0, s1 = c['s0'], c['s1']; keep = []
    for r in runs:
        if r['side'] == c['side'] and r['s0'] <= s1 + 2 and r['s1'] >= s0 - 2: s0, s1 = min(s0, r['s0']), max(s1, r['s1'])
        else: keep.append(r)
    keep.append({'side': c['side'], 's0': round(s0, 1), 's1': round(s1, 1)}); keep.sort(key=lambda r: (r['side'], r['s0']))
    SC['edge_lines']['runs'] = keep
    log(f'  edge line side {c["side"]}: run {s0}..{s1}')


def pit_exit_cones_from(T, SC, c, log=_log):
    pc = SC.get('pit_exit_cones')
    if not pc: return
    n, sp = T['n'], T['spacing_m']; first = pc['pts'][0]
    part = min(SC['pit_lane']['parts'], key=lambda p: min(math.hypot(q[0] - first[0], q[1] - first[1]) for q in p['left'] + p['right']))
    side = min(('left', 'right'), key=lambda s: min(math.hypot(q[0] - first[0], q[1] - first[1]) for q in part[s]))
    poly = part[side]
    j_first = min(range(len(poly)), key=lambda j: math.hypot(poly[j][0] - first[0], poly[j][1] - first[1]))
    cum = [0.0]
    for j in range(1, len(poly)): cum.append(cum[-1] + math.hypot(poly[j][0] - poly[j - 1][0], poly[j][1] - poly[j - 1][1]))
    s_first = pc['s0']; new = []; s = s_first - pc['spacing_m']
    while s >= c['s0'] - 1e-6:
        target = cum[j_first] - (s_first - s)
        if target < 0: break
        j = max(1, min(len(poly) - 1, next((i for i in range(1, len(poly)) if cum[i] >= target), len(poly) - 1)))
        u = (target - cum[j - 1]) / max(1e-9, cum[j] - cum[j - 1]); p, q = poly[j - 1], poly[j]
        new.append([round(p[0] + u * (q[0] - p[0]), 2), round(p[1] + u * (q[1] - p[1]), 2), round(p[2] + u * (q[2] - p[2]), 2)])
        s -= pc['spacing_m']
    new.reverse()
    pc['pts'] = new + pc['pts']; pc['s0'] = round(c['s0'], 1)
    log(f'  pit-exit cones: {len(new)} added back to s {c["s0"]}')


def run(T, SC, scfg, tiles, mpp, regs=None, log=_log):
    """All post steps in order on scenery dict SC (track dict T). Returns SC."""
    for z in scfg.get('shoulder_zones', []):
        part = shoulder_zone(T, SC, z)
        SC['paved_zones']['parts'] = [p for p in SC['paved_zones']['parts'] if p.get('turn') != z['turn']] + [part]
        log(f"  shoulder zone {z['turn']}: {part['n']} stations")
    if scfg.get('aprons'):
        parts = aprons(T, SC, scfg['aprons'], tiles, mpp, scfg.get('apron_max', 10.0), regs, log)
        names = {p['turn'] for p in parts}
        SC['paved_zones']['parts'] = [p for p in SC['paved_zones']['parts'] if p.get('turn') not in names] + parts
    if scfg.get('pitwall_end'): pitwall_end(T, SC, scfg['pitwall_end'], log)
    if scfg.get('pitwall_setback'): pitwall_setback(T, SC, scfg['pitwall_setback'], log)
    if scfg.get('pitwall_straight'): pitwall_straight(T, SC, scfg['pitwall_straight'], log)
    for c in scfg.get('kerb_extents', []): kerb_extent(SC, c, log)
    for c in scfg.get('edge_line_runs', []): edge_line_run(SC, c, log)
    if scfg.get('pit_exit_cones') and SC.get('pit_exit_cones'):
        pc = scfg['pit_exit_cones']
        if 'spacing' in pc: SC['pit_exit_cones']['spacing_m'] = pc['spacing']
        if 's0' in pc and pc['s0'] < SC['pit_exit_cones']['s0']: pit_exit_cones_from(T, SC, pc, log)
    return SC
