"""Declared straights (stage 1 geometry; was fix_front_straight_lines.py, owner 18-19 Oct 2026 night: "this hump on the
start/finish straight ... The painted lines are basically straight all the way down. There is pavement between the
walls, but the painted outline of the track, and the bounds of the track, are straight").

Config `straights`, applied in order after the spline fit, each one side:
  fit 'paint'    - a straight line RANSAC-fitted (tol m) to every thin painted-line detection along that side over lo..hi
                   on every capture (a strip under 0.6 m brighter than 0.3 m to both sides by 25+, unsaturated);
  fit 'parallel' - parallel to the line already fitted for ref_side, at the median distance the current edge keeps from
                   it over ref_lo..ref_hi;
  fit 'asphalt_end' - a straight line RANSAC-fitted (tol m) to the asphalt-end readings along that side over lo..hi on
                   every capture (edges_spline.asphalt_end with `detector` {jump, sat_max, lo, hi}; circuits with no
                   painted edge line, Buttonwillow's front straight, 20 Oct 2026);
  fit 'pitwall'  - `gap` m inside a straight line RANSAC-fitted (0.25 m) to the pit-wall polyline over lo..hi (Laguna's
                   left: the edge is 2.0 m off the straight pit wall).
The half-width becomes the crossing of the station normal with the line, from the station in `join` where the line
meets the current edge to `end`, blended in and out over `blend` stations (smoothstep). The profile columns are
re-evaluated by the caller (centre.reprofile).
"""
import numpy as np
from PIL import Image

from captures import bilinear
from geo import log as _log


_ONCE = {}   # straights with `once`: (side, lo, hi) -> the line read on the first call


def ransac(xy, tol, it=4000, seed=1, min_len=30):
    rng = np.random.default_rng(seed); best = None
    for _ in range(it):
        i, j = rng.choice(len(xy), 2, replace=False); d = xy[j] - xy[i]; l = np.linalg.norm(d)
        if l < min_len: continue
        nr = np.array([-d[1], d[0]]) / l; inl = np.abs((xy - xy[i]) @ nr) < tol
        if best is None or inl.sum() > best.sum(): best = inl
    p = xy[best]; m = p.mean(0); _, _, vt = np.linalg.svd(p - m); return m, vt[0], int(best.sum())


def span(lo, hi, n):
    return [k % n for k in range(lo, hi + (n if hi < lo else 0) + 1)]


def paint_points(C, NL, hw, sg, ks, tiles, mpp):
    """World points of thin painted lines within +-3 m of the current edge on side sg (+1 left, -1 right)."""
    U = np.arange(-3.0, 3.0, 0.04); pts = []
    for t in tiles:
        if np.min(np.hypot(C[ks, 0] - t['x'], C[ks, 1] - t['y'])) > 110: continue
        im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32); H, W = im.shape[:2]; mask = t['mask'](H, W)
        lat = sg * (hw[ks][:, None] + U[None, :]); X = C[ks, 0:1] + lat * NL[ks, 0:1]; Y = C[ks, 1:2] + lat * NL[ks, 1:2]
        px = W / 2 + (X + t['dx'] - t['x']) / mpp; py = H / 2 - (Y + t['dy'] - t['y']) / mpp
        for i in range(len(ks)):
            ok = (px[i] >= 1) & (px[i] < W - 2) & (py[i] >= 1) & (py[i] < H - 2)
            if ok.mean() < 0.9: continue
            ok &= mask[np.clip(py[i].round().astype(int), 0, H - 1), np.clip(px[i].round().astype(int), 0, W - 1)]
            v = bilinear(im, np.clip(px[i], 1, W - 2), np.clip(py[i], 1, H - 2)); br = v.mean(1); sat = v.max(1) - v.min(1)
            d = int(0.3 / 0.04); th = np.zeros(len(U), bool)
            th[d:-d] = (br[d:-d] - np.maximum(br[:-2 * d], br[2 * d:]) > 25) & (sat[d:-d] < 45) & ok[d:-d]
            j = 0
            while j < len(U):
                if th[j]:
                    e = j
                    while e < len(U) and th[e]: e += 1
                    pts.append(C[ks[i]] + sg * NL[ks[i]] * (hw[ks[i]] + U[(j + e) // 2])); j = e
                else: j += 1
    return np.array(pts)


def aend_points(C, NL, hw, sg, ks, tiles, mpp, det):
    """World points of the asphalt-end readings near the current edge on side sg (fit 'asphalt_end')."""
    import edges_spline as ES
    keep = dict(ES.AEND); ES.AEND.update(jump=10.0, sat_max=30.0, lo=-1.2, hi=2.0); ES.AEND.update(det or {})
    U = ES.U; pts = []
    try:
        for t in tiles:
            if np.min(np.hypot(C[ks, 0] - t['x'], C[ks, 1] - t['y'])) > 110: continue
            im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32); H, W = im.shape[:2]; mask = t['mask'](H, W)
            lat = sg * (hw[ks][:, None] + U[None, :]); X = C[ks, 0:1] + lat * NL[ks, 0:1]; Y = C[ks, 1:2] + lat * NL[ks, 1:2]
            px = W / 2 + (X + t['dx'] - t['x']) / mpp; py = H / 2 - (Y + t['dy'] - t['y']) / mpp
            for i in range(len(ks)):
                ok = (px[i] >= 1) & (px[i] < W - 2) & (py[i] >= 1) & (py[i] < H - 2)
                if ok.mean() < 0.9: continue
                ok &= mask[np.clip(py[i].round().astype(int), 0, H - 1), np.clip(px[i].round().astype(int), 0, W - 1)]
                v = bilinear(im, np.clip(px[i], 1, W - 2), np.clip(py[i], 1, H - 2))
                e = ES.asphalt_end(v, ok)
                if e is not None: pts.append(C[ks[i]] + sg * NL[ks[i]] * (hw[ks[i]] + e))
    finally:
        ES.AEND.clear(); ES.AEND.update(keep)
    return np.array(pts)


def apply(C, NL, hl, hr, straights, tiles, mpp, pitwall=None, log=_log):
    """pitwall: (k, 2) pit-wall polyline points (for fit 'pitwall'). Returns (hl, hr, report)."""
    n = len(C); hl, hr = hl.copy(), hr.copy(); lines = {}; rep = []

    def cross(k, m, d, sg):
        nn = NL[k] * sg; den = nn[0] * (-d[1]) - nn[1] * (-d[0]); r = m - C[k]
        return (r[0] * (-d[1]) - r[1] * (-d[0])) / den
    for st_ in straights:
        side = st_['side']; sg = 1 if side == 'left' else -1; hw = hl if side == 'left' else hr
        if st_['fit'] in ('paint', 'asphalt_end'):
            ks = np.array(span(st_['lo'], st_['hi'], n))
            pts = paint_points(C, NL, hw, sg, ks, tiles, mpp) if st_['fit'] == 'paint' else aend_points(C, NL, hw, sg, ks, tiles, mpp, st_.get('detector'))
            m, d, nin = ransac(pts, st_.get('tol', 0.15))
            log(f"straight {side}: line from {nin} inliers of {len(pts)} {st_['fit']} detections")
        elif st_['fit'] == 'parallel':
            m0, d = lines[st_['ref_side']]; nr = np.array([-d[1], d[0]])
            ref = span(st_['ref_lo'], st_['ref_hi'], n)
            off = float(np.median([(C[k] + sg * NL[k] * hw[k] - m0) @ nr for k in ref]))
            m = m0 + off * nr; nin = len(ref)
            log(f"straight {side}: parallel to the {st_['ref_side']} line at {abs(off):.2f} m (median of the current edge over {st_['ref_lo']}..{st_['ref_hi']})")
        elif st_['fit'] == 'pitwall':
            if pitwall is None or not len(pitwall):
                raise SystemExit('straights: fit pitwall needs the pit-wall polyline')
            ks = set(span(st_['lo'], st_['hi'], n))
            near = np.array([int(np.argmin(np.hypot(*(C - p).T))) in ks for p in pitwall])
            wm, d, nin = ransac(pitwall[near], 0.25, min_len=60)
            m = wm - sg * st_['gap'] * np.array([-d[1], d[0]]) * np.sign(np.array([-d[1], d[0]]) @ NL[st_['lo'] % n])
            log(f"straight {side}: {st_['gap']} m inside the pit-wall line ({nin} inliers of {int(near.sum())} wall points)")
        else:
            raise SystemExit(f"straights: unknown fit {st_['fit']!r}")
        lines[side] = (m, d)
        tgt = lambda k: cross(k, m, d, sg)
        j0, j1 = st_['join']
        k0 = min(range(j0, j1 + 1), key=lambda k: abs(tgt(k % n) - hw[k % n]))
        sts = span(k0, st_['end'], n); m_ = len(sts); vals = {}; bl = st_.get('blend', 12)
        for i, k in enumerate(sts):
            d0, d1 = i, m_ - 1 - i; w = 1.0
            if d0 < bl: w = min(w, (d0 / bl) ** 2 * (3 - 2 * d0 / bl))
            if d1 < bl: w = min(w, (d1 / bl) ** 2 * (3 - 2 * d1 / bl))
            vals[k] = hw[k] + w * (tgt(k) - hw[k])
        mv = max(abs(vals[k] - hw[k]) for k in sts)
        log(f"straight {side}: join at {k0}, to {st_['end']}; max move {mv:.2f} m")
        for k, v in vals.items(): hw[k] = v
        rep.append(dict(side=side, fit=st_['fit'], inliers=nin, join=int(k0), end=st_['end'], max_move=float(mv)))
    return hl, hr, rep


def targets(C, NL, hl, hr, straights, tiles, mpp, pitwall=None, log=_log):
    """The declared straights as constraints for the fitted method (edges_spline.fit_periodic): for each, the straight
    line is fitted to its evidence (painted-line detections, or the pit-wall polyline less `gap`) and returned as the
    half-width where each station's normal crosses it, over lo..hi. Nothing is overwritten or blended here: the
    periodic spline takes these as anchor observations next to the image evidence. Returns
    {'left'|'right': (stations, half-widths)} and a report."""
    n = len(C); lines = {}; out = {'left': ([], []), 'right': ([], [])}; rep = []

    def cross(k, m, d, sg):
        nn = NL[k] * sg; den = nn[0] * (-d[1]) - nn[1] * (-d[0]); r = m - C[k]
        return (r[0] * (-d[1]) - r[1] * (-d[0])) / den
    for st_ in straights:
        side = st_['side']; sg = 1 if side == 'left' else -1; hw = hl if side == 'left' else hr
        ks = np.array(span(st_['lo'], st_['hi'], n))
        if st_['fit'] in ('paint', 'asphalt_end') and st_.get('once') and (side, st_.get('why', '')) in _ONCE:
            # `once` (Buttonwillow Sunset, round 8): the line is read once, around the first fit's edge, and reused on every
            # refit (read around the moving edge, an outward reading pulls the edge out and the next window further)
            m, d, nin = _ONCE[(side, st_.get('why', ''))]
        elif st_['fit'] in ('paint', 'asphalt_end') and st_.get('width_shared'):
            # `width_shared` (Buttonwillow's drag strip, round 8, owner notes 20-21: one width end to end): this side is
            # the line PARALLEL to the other side's line already fitted (same direction), at the robust median distance of
            # this side's own readings from it (the readings within 0.5 m of the first median)
            os_ = 'right' if side == 'left' else 'left'
            if os_ not in lines:
                raise SystemExit(f"straights: width_shared on {side} needs the {os_} line declared first")
            m0, d = lines[os_]; nr = np.array([-d[1], d[0]])
            pts = paint_points(C, NL, hw, sg, ks, tiles, mpp) if st_['fit'] == 'paint' else aend_points(C, NL, hw, sg, ks, tiles, mpp, st_.get('detector'))
            dist = (pts - m0) @ nr; med = float(np.median(dist)); near = np.abs(dist - med) < 0.5
            off = float(np.median(dist[near])); m = m0 + off * nr; nin = int(near.sum())
            if st_.get('once'):
                _ONCE[(side, st_.get('why', ''))] = (m, d, nin)
            log(f"straight {side} {st_['lo']}..{st_['hi']}: parallel to the {os_} line, width {abs(off):.2f} m ({nin} of {len(pts)} readings)")
        elif st_['fit'] in ('paint', 'asphalt_end'):
            pts = paint_points(C, NL, hw, sg, ks, tiles, mpp) if st_['fit'] == 'paint' else aend_points(C, NL, hw, sg, ks, tiles, mpp, st_.get('detector'))
            m, d, nin = ransac(pts, st_.get('tol', 0.15))
            if st_.get('once'):
                _ONCE[(side, st_.get('why', ''))] = (m, d, nin)
        elif st_['fit'] == 'parallel':
            m0, d = lines[st_['ref_side']]; nr = np.array([-d[1], d[0]])
            ref = span(st_['ref_lo'], st_['ref_hi'], n)
            off = float(np.median([(C[k] + sg * NL[k] * hw[k] - m0) @ nr for k in ref])); m = m0 + off * nr; nin = len(ref)
        elif st_['fit'] == 'pitwall':
            if pitwall is None or not len(pitwall):
                raise SystemExit('straights: fit pitwall needs the pit-wall polyline')
            kset = set(ks.tolist())
            near = np.array([int(np.argmin(np.hypot(*(C - p).T))) in kset for p in pitwall])
            wm, d, nin = ransac(pitwall[near], 0.25, min_len=60)
            m = wm - sg * st_['gap'] * np.array([-d[1], d[0]]) * np.sign(np.array([-d[1], d[0]]) @ NL[st_['lo'] % n])
        else:
            raise SystemExit(f"straights: unknown fit {st_['fit']!r}")
        lines[side] = (m, d)
        v = np.array([cross(k, m, d, sg) for k in ks])
        out[side][0].extend(ks.tolist()); out[side][1].extend(v.tolist())
        log(f"straight {side} {st_['lo']}..{st_['hi']} ({st_['fit']}, {nin} inliers): constraint inside the fit, "
            f"{np.abs(v - hw[ks]).max():.2f} m from the prior at most")
        rep.append(dict(side=side, fit=st_['fit'], inliers=int(nin), lo=int(st_['lo']), hi=int(st_['hi'])))
    return out, rep
