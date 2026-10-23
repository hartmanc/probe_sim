"""Unmodelled ground lines gate (round 13, Sonoma owner, 23 Oct 2026: "I think, as a general rule, if we are modeling
textures in a long line on the ground, it's likely we are missing a feature").

The T1 tyre wall, the T2 and T4 wall bases, the start/finish wall base and the bridge footprint all showed in the sim
as dark or pale bands in the ground ortho with the model standing behind them or over them. This gate scans the
package's own ortho.jpg (what the sim drapes on the terrain) for long, thin, dark or pale linear features in the
scenery band beside the track and reports every one that no modelled feature accounts for.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/gates/ground_lines.py <package dir> \
        [--config gl.json] [--json report.json] [--lines lines.json] [--strict]

Definition (defaults in DEFAULTS, overridable by config scenery.ground_lines):
  1. Line response: on the ortho's luminance, the Hessian of a Gaussian at sigma 0.6 and 1.2 m; a pixel is on a DARK
     line where the larger eigenvalue is positive and at least `aniso` (3) times the other's magnitude (a valley, not a
     blob), on a PALE line where it is negative likewise (a ridge); and it is darker (paler) than the ground on BOTH
     sides, `side` (1.5) m plus sigma away along the line's normal, by at least `contrast` (16 grey levels): a step
     between two surfaces (a road or field boundary) is not a line.
  2. Band: only pixels `band` (2 to 60) m beyond the nearest track edge, on either side.
  3. Lines: 8-connected components of those pixels; a component's length is the longer of its principal-axis extent and
     the polyline through its 5 m-binned centroids along the track; its width is area / length. A line is at least
     `min_len` (20) m long and at most `max_width` (3) m wide.
  4. Accounted for: within `cover` (2) m of a modelled feature: a barrier run (any kind), a cone line, a paint line,
     a kerb line, the edge of a pit-lane part, paved zone, closed road or paved area (and their inside: those surfaces
     are drawn over the ortho), a terrace row, a building, structure or bridge footprint (the ortho is inpainted there).
     A line whose unaccounted part is `min_len` m or longer is a FINDING, reported with its side, station range,
     distance from the edge, tone and length.
  5. Barrier-related: a finding is BARRIER-RELATED when at least `beside_frac` (0.5) of its unaccounted pixels lie
     within `beside` (6) m of a modelled barrier run (the model stands 2-6 m off the line the ortho shows: the T2 and T4
     walls of round 12) or it passes within `end_reach` (3) m of a run's end (the line goes on where the model stops:
     the T1 tyre wall and the T4 wall's end at the Chute). The gate fails on barrier-related findings (`strict_on`
     'barrier_related'; 'barrier_like': a lit line beside its shadow, at least `pair_frac` of its pixels with a line of
     the other tone within `pair` m; 'all': every finding); the rest (a path, a ditch, a field boundary, a stand's
     tiers far from any barrier) are listed for the round's review, not failed.
  6. Dispositions (config scenery.ground_lines.dispositions [{side, s: (s0, s1) m, tone: 'dark' | 'pale' | 'any',
     what, why}]): a finding whose side matches and whose station range overlaps a disposition's is DISPOSITIONED
     (shadow, drainage, a stand's tiers, ...). With --strict (the config has the key) an open barrier-like finding
     fails the gate (exit 1); without it the report is advisory (exit 0).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

DEFAULTS = dict(band=(2.0, 60.0), contrast=16.0, aniso=3.0, sigmas=(0.6, 1.2), min_len=20.0, max_width=3.0, cover=2.0,
                hess_min=0.6, side=1.5, pair=1.8, pair_frac=0.5, strict_on='barrier_related', beside=6.0, beside_frac=0.5, end_reach=3.0)


def load(pkg):
    T = json.load(open(os.path.join(pkg, 'track.json')))
    SC = json.load(open(os.path.join(pkg, 'scenery.json')))
    o = T['ortho']
    im = np.asarray(Image.open(os.path.join(pkg, o['file'])).convert('RGB')).astype(np.float32)
    return T, SC, o, im


def track_frame(T):
    C = np.array(T['center'])[:, :2]
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    N = np.c_[-tg[:, 1], tg[:, 0]]
    hl = ((np.array(T['left'])[:, :2] - C) * N).sum(1)
    hr = -((np.array(T['right'])[:, :2] - C) * N).sum(1)
    return C, N, hl, hr


def covered_mask(SC, o, shape, cover):
    """Pixels within `cover` m of a modelled feature (lines drawn 2 x cover wide; surfaces and footprints filled)."""
    H, W = shape
    mpp = (o['x1'] - o['x0']) / W
    img = Image.new('L', (W, H), 0); d = ImageDraw.Draw(img)
    px = lambda P: [((p[0] - o['x0']) / (o['x1'] - o['x0']) * W, (o['y1'] - p[1]) / (o['y1'] - o['y0']) * H) for p in P]  # noqa: E731
    wpx = max(1, int(round(2 * cover / mpp)))

    def line(P):
        if len(P) >= 2:
            d.line(px(P), fill=255, width=wpx)
            for q in px([P[0], P[-1]]):
                d.ellipse([q[0] - wpx / 2, q[1] - wpx / 2, q[0] + wpx / 2, q[1] + wpx / 2], fill=255)

    def poly(P):
        if len(P) >= 3:
            d.polygon(px(P), fill=255)
            line(list(P) + [P[0]])

    for b in SC.get('barriers', []):
        line(b['pts'])
    for key in ('cone_lines', 'paint_lines', 'kerb_lines'):
        for c in SC.get(key) or []:
            line(c.get('pts') or c.get('line') or [])
    if SC.get('pit_exit_cones'):
        line(SC['pit_exit_cones']['pts'])
    for grp in ('pit_lane', 'paved_zones'):
        for p in (SC.get(grp) or {}).get('parts', []):
            poly([q[:2] for q in p['left']] + [q[:2] for q in p['right']][::-1])
    for a in SC.get('paved_areas') or []:
        poly(a['poly'])
    for t in SC.get('terraces') or []:
        for r in t.get('rows', []):
            line(r['pts'] if r.get('pts') else [r['a'], r['b']])
    for b in SC.get('buildings', []):
        poly(b['footprint'])
    for s in SC.get('structures', []):
        for c in s.get('collide') or []:
            poly(c['footprint'])
    for b in SC.get('bridges', []):
        a_, b_ = np.array(b['a'], float), np.array(b['b'], float)
        t = b_ - a_; t /= (np.linalg.norm(t) or 1); n = np.array([-t[1], t[0]]); h = b.get('width', 3.0) / 2
        poly([a_ + n * h, b_ + n * h, b_ - n * h, a_ - n * h])
    return np.asarray(img) > 0


def line_pixels(im, o, opt):
    """Boolean maps of dark-line and pale-line pixels and the luminance contrast. A line pixel is a Hessian valley (dark)
    or ridge (pale) that is darker (paler) than the ground on BOTH sides of it: the luminance `side` m away along the
    line's normal, each way, differs from the line's by at least `contrast` (a step edge between two surfaces, a road
    or field boundary, has one side only and is not a line)."""
    lum = im.mean(-1)
    mpp = (o['x1'] - o['x0']) / im.shape[1]
    H, W = lum.shape
    D = np.zeros(lum.shape, np.float32)
    dark = np.zeros(lum.shape, bool); pale = np.zeros(lum.shape, bool)
    ls = ndi.gaussian_filter(lum, 0.5)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for sg in opt['sigmas']:
        s = sg / mpp
        Lxx = ndi.gaussian_filter(lum, s, order=(0, 2)); Lyy = ndi.gaussian_filter(lum, s, order=(2, 0))
        Lxy = ndi.gaussian_filter(lum, s, order=(1, 1))
        tr = (Lxx + Lyy) / 2; dt = np.sqrt(((Lxx - Lyy) / 2) ** 2 + Lxy ** 2)
        e1, e2 = tr + dt, tr - dt          # e1 >= e2
        first = np.abs(e1) >= np.abs(e2)
        big = np.where(first, e1, e2); small = np.where(first, e2, e1)
        lineish = (np.abs(big) * s * s >= opt['hess_min']) & (np.abs(big) >= opt['aniso'] * np.abs(small))
        # the normal of the line: the eigenvector of `big` ((Lxy, big - Lxx), or (big - Lyy, Lxy)); x right, y down
        vx = np.where(np.abs(Lxy) > 1e-9, Lxy, np.where(np.abs(Lxx) >= np.abs(Lyy), 1.0, 0.0))
        vy = np.where(np.abs(Lxy) > 1e-9, big - Lxx, np.where(np.abs(Lxx) >= np.abs(Lyy), 0.0, 1.0))
        nn = np.hypot(vx, vy) + 1e-9; vx /= nn; vy /= nn
        k = (opt['side'] + sg) / mpp
        a = ndi.map_coordinates(ls, [yy + vy * k, xx + vx * k], order=1, mode='nearest')
        b = ndi.map_coordinates(ls, [yy - vy * k, xx - vx * k], order=1, mode='nearest')
        dk = np.minimum(a, b) - ls          # > 0: darker than both sides
        pl = ls - np.maximum(a, b)          # > 0: paler than both sides
        dd = lineish & (big > 0) & (dk >= opt['contrast'])
        pp = lineish & (big < 0) & (pl >= opt['contrast'])
        dark |= dd; pale |= pp
        D = np.where(dd, -np.maximum(-D, dk), np.where(pp, np.maximum(D, pl), D))
    return dark, pale, D


def chain_length(P, s, L):
    """Length of a pixel cloud P (world xy) with track stations s: the longer of its principal-axis extent and the
    polyline through its centroids in 5 m station bins (unwrapped)."""
    if len(P) < 3:
        return 0.0, None
    c = P.mean(0); u, sv, vt = np.linalg.svd(P - c, full_matrices=False)
    pr = (P - c) @ vt[0]
    ext = float(pr.max() - pr.min())
    su = np.unwrap(s / L * 2 * np.pi) * L / (2 * np.pi)
    b = np.floor(su / 5.0)
    cents = [P[b == k].mean(0) for k in np.unique(b)]
    ch = float(np.sum(np.linalg.norm(np.diff(np.array(cents), axis=0), axis=1))) if len(cents) > 1 else 0.0
    if ext >= ch:
        order = np.argsort(pr); pts = P[order][:: max(1, len(P) // 40)]
    else:
        pts = np.array(cents)
    return max(ext, ch), pts


def scan(pkg, cfg=None, log=print):
    opt = dict(DEFAULTS, **{k: v for k, v in (cfg or {}).items() if k in DEFAULTS})
    T, SC, o, im = load(pkg)
    H, W = im.shape[:2]
    mpp = (o['x1'] - o['x0']) / W
    C, N, hl, hr = track_frame(T)
    sp, n = T['spacing_m'], T['n']; L = n * sp
    dark, pale, D = line_pixels(im, o, opt)
    # the barrier signature: a wall or tyre stack in a summer aerial is a lit top beside its own shadow, so a dark line
    # with a pale line (at half the contrast) within `pair` m beside it, or a pale one with a dark one, is barrier-like
    dl, pl_, _ = line_pixels(im, o, dict(opt, contrast=opt['contrast'] / 2))
    rp = max(1, int(round(opt['pair'] / mpp)))
    near_pale = ndi.binary_dilation(pl_, iterations=rp); near_dark = ndi.binary_dilation(dl, iterations=rp)
    # band beyond the edge
    cand = dark | pale
    yy, xx = np.nonzero(cand)
    X = o['x0'] + (xx + 0.5) * mpp; Y = o['y1'] - (yy + 0.5) * (o['y1'] - o['y0']) / H
    kd = cKDTree(C)
    dist, i = kd.query(np.c_[X, Y], distance_upper_bound=200.0)
    ok = np.isfinite(dist)
    i = np.where(ok, i, 0)
    lat = (X - C[i, 0]) * N[i, 0] + (Y - C[i, 1]) * N[i, 1]
    out = np.abs(lat) - np.where(lat > 0, hl[i], hr[i])
    inband = ok & (out >= opt['band'][0]) & (out <= opt['band'][1])
    keep = np.zeros(cand.shape, bool); keep[yy[inband], xx[inband]] = True
    cov = covered_mask(SC, o, (H, W), opt['cover'])
    # barrier-related: beside a modelled run (within `beside` m of its line, i.e. the model stands 2-6 m off the line the
    # ortho shows) or continuing from a run's end (the line passes within `end_reach` m of an end: the model stops short)
    bars = {'barriers': [b for b in SC.get('barriers', []) if b['kind'] != 'fence']}
    near_bar = covered_mask(bars, o, (H, W), opt['beside'])
    ends = {'barriers': [{'pts': [b['pts'][k], b['pts'][k]]} for b in bars['barriers'] for k in (0, -1)]}
    near_end = covered_mask(ends, o, (H, W), opt['end_reach'])
    S_ = np.zeros(cand.shape, np.float32); S_[yy, xx] = i * sp
    LAT = np.zeros(cand.shape, np.float32); LAT[yy, xx] = lat
    OUT = np.zeros(cand.shape, np.float32); OUT[yy, xx] = out
    lines, findings = [], []
    for tone, m in (('dark', dark & keep), ('pale', pale & keep)):
        lab, nl = ndi.label(m, structure=np.ones((3, 3)))
        if not nl:
            continue
        objs = ndi.find_objects(lab)
        for k, sl in enumerate(objs, 1):
            sub = lab[sl] == k
            if sub.sum() * mpp * mpp < opt['min_len'] * mpp:   # too few pixels to be min_len long
                continue
            ys, xs = np.nonzero(sub); ys = ys + sl[0].start; xs = xs + sl[1].start
            P = np.c_[o['x0'] + (xs + 0.5) * mpp, o['y1'] - (ys + 0.5) * mpp]
            s = S_[ys, xs]
            ln, pts = chain_length(P, s, L)
            if ln < opt['min_len'] or (len(P) * mpp * mpp) / ln > opt['max_width']:
                continue
            un = ~cov[ys, xs]
            uln, upts = chain_length(P[un], s[un], L) if un.sum() >= 3 else (0.0, None)
            side = 'left' if np.median(LAT[ys, xs]) > 0 else 'right'
            paired = float((near_pale if tone == 'dark' else near_dark)[ys, xs].mean())
            beside = float(near_bar[ys, xs][~cov[ys, xs]].mean()) if (~cov[ys, xs]).any() else 0.0
            from_end = bool(near_end[ys, xs].any())
            su = np.unwrap(s / L * 2 * np.pi) * L / (2 * np.pi)
            rec = dict(tone=tone, side=side, s0=round(float(su.min() % L), 1), s1=round(float(su.max() % L), 1),
                       out0=round(float(OUT[ys, xs].min()), 1), out1=round(float(OUT[ys, xs].max()), 1),
                       length=round(ln, 1), unaccounted=round(uln, 1), contrast=round(float(np.abs(D[ys, xs]).mean()), 1),
                       paired=round(paired, 2), barrier_like=bool(paired >= opt['pair_frac']),
                       beside=round(beside, 2), from_end=from_end,
                       barrier_related=bool(beside >= opt['beside_frac'] or from_end),
                       pts=[[round(float(a), 1), round(float(b), 1)] for a, b in (upts if uln >= opt['min_len'] else pts)])
            lines.append(rec)
            if uln >= opt['min_len']:
                if un.sum() >= 3:
                    su_ = su[un]
                    rec.update(s0=round(float(su_.min() % L), 1), s1=round(float(su_.max() % L), 1),
                               out0=round(float(OUT[ys, xs][un].min()), 1), out1=round(float(OUT[ys, xs][un].max()), 1))
                findings.append(rec)
    disp = (cfg or {}).get('dispositions', [])

    def overlaps(f, d_):
        a, b = d_['s']
        if d_['side'] != f['side'] or (d_.get('tone', 'any') not in ('any', f['tone'])):
            return False
        fa, fb = f['s0'], f['s1'] if f['s1'] >= f['s0'] else f['s1'] + L
        for off in (0, L, -L):
            if fa < b + off and fb > a + off:
                return True
        return False
    for f in findings:
        m = next((d_ for d_ in disp if overlaps(f, d_)), None)
        f['disposition'] = None if m is None else f"{m['what']}: {m['why']}"
    gating = [f for f in findings if opt['strict_on'] == 'all' or f[opt['strict_on']]]
    return dict(options={k: v for k, v in opt.items()}, lines=len(lines), accounted=len(lines) - len(findings),
                findings=findings, open=[f for f in gating if not f['disposition']],
                other=[f for f in findings if f not in gating and not f['disposition']])


def report_lines(rep, strict):
    """The printed report: one summary line ([ok] / [FAIL] / [advisory]) and one line per finding."""
    o = rep['options']; nf, no, nx = len(rep['findings']), len(rep['open']), len(rep['other'])
    tag = 'FAIL' if (strict and no) else ('ok' if not no else 'advisory')
    out = [f"[{tag}] ground lines: {rep['lines']} long thin dark / pale lines in the ortho {o['band'][0]:.0f}-{o['band'][1]:.0f} m beyond "
           f"the edge (>= {o['min_len']:.0f} m, <= {o['max_width']:.0f} m wide, contrast >= {o['contrast']:.0f}); {rep['accounted']} on a "
           f"modelled feature (within {o['cover']:.0f} m); {nf} not: {nf - no - nx} dispositioned, {no} open {o['strict_on'].replace('_', '-')} "
           f"(beside a modelled barrier or going on from its end), {nx} other lines listed"]
    rank = lambda f: (0 if (f in rep['open']) else 1 if f in rep['other'] else 2, f['s0'])  # noqa: E731
    for f in sorted(rep['findings'], key=rank):
        st = 'OPEN ' if f in rep['open'] else ('other' if f in rep['other'] else 'disp ')
        out.append(f"       {st} {f['tone']:4s} {f['side']:5s} s {f['s0']:6.0f}-{f['s1']:6.0f} {f['out0']:4.0f}-{f['out1']:4.0f} m out, "
                   f"{f['unaccounted']:5.1f} of {f['length']:5.1f} m (contrast {f['contrast']:.0f}, beside a barrier {f['beside']:.2f}{', from a run end' if f['from_end'] else ''})"
                   + (f" -> {f['disposition'][:100]}" if f['disposition'] else ''))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pkg')
    ap.add_argument('--config', help='json: the config scenery.ground_lines block (options and dispositions)')
    ap.add_argument('--json', help='write the report here')
    ap.add_argument('--lines', help='write the findings as orthowin.py --lines json here')
    ap.add_argument('--strict', action='store_true', help='exit 1 on any finding without a disposition')
    a = ap.parse_args()
    cfg = json.load(open(a.config)) if a.config else {}
    rep = scan(a.pkg, cfg)
    for line in report_lines(rep, strict=a.strict):
        print(line)
    if a.json:
        json.dump(rep, open(a.json, 'w'), indent=1)
    if a.lines:
        json.dump([{'pts': f['pts']} for f in rep['findings']], open(a.lines, 'w'))
    no = len(rep['open'])
    print('GROUNDLINES_JSON ' + json.dumps({k: rep[k] for k in ('lines', 'accounted')} | {'findings': len(rep['findings']), 'open': no, 'other': len(rep['other'])}))
    sys.exit(1 if (a.strict and no) else 0)


if __name__ == '__main__':
    main()
