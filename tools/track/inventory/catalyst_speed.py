"""Speed-integrated lap from a Garmin Catalyst onboard (build-track stage 0, the length check of the Buttonwillow rule;
Mid-Ohio round 4): read the overlay's speed digits frame by frame (template OCR: the white digits of the speed dial,
templates cut from frames whose reading was typed by eye, every reading reported with its match score), then
integrate the speed over the lap between two start/finish crossings (trapezoid in video time).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/inventory/catalyst_speed.py \
        --frames <dir of t###.jpg 1280x720 frames> --labels 0:55,9:78,... --t0 5.03 --t1 129.87 [--units mph] \
        [--crop 60,580,160,627] [--out speeds.json] [--sheet sheet.png]

--t0 / --t1: the video times of the two S/F crossings (from the overlay's lap-time readout: t - lap time). The frame
times come from the capture's _frames_<id>.json (media_t) when present. The distance is reported for the trapezoid at
the full step and at twice the step (a sampling-error indicator) and with the display's quantisation bound
(+-0.5 unit over the lap: a reading rounded or truncated to whole units). Reads reference imagery, writes numbers (and
an optional local check sheet: every crop with its reading, never committed).
"""
import argparse
import glob
import json
import os
import re

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

UNIT = {'mph': 0.44704, 'kmh': 1 / 3.6}
TW, TH = 16, 24


def glyphs(path, crop, thr=170):
    """The white digit glyphs of the crop, left to right, each a TH x TW float mask, plus their boxes."""
    im = np.asarray(Image.open(path).convert('RGB')).astype(int)
    x0, y0, x1, y1 = crop
    c = im[y0:y1, x0:x1]
    white = c.min(2) > thr
    lab, n = ndimage.label(white)
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if h < 0.45 * (y1 - y0) or (lab[sl] == k).sum() < 40:      # the digits are tall; drop specks and the dial ticks
            continue
        m = (lab[sl] == k).astype(float)
        parts = [(0, w)]
        if w > 0.95 * h:
            # two digits touching (a "71"): split at the thinnest column of the middle third
            col = m.sum(0); a_, b_ = w // 3, 2 * w // 3
            cut = a_ + int(np.argmin(col[a_:b_]))
            parts = [(0, cut), (cut, w)]
        for c0, c1 in parts:
            mm = m[:, c0:c1]
            g = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).resize((TW, TH), Image.BILINEAR)) / 255.0
            out.append((sl[1].start + c0, g, (sl[1].start + c0 + x0, sl[0].start + y0, sl[1].start + c1 + x0, sl[0].stop + y0)))
    out.sort(key=lambda q: q[0])
    return [g for _, g, _ in out], [b for _, _, b in out]


def frame_times(frames_dir):
    meta = glob.glob(os.path.join(frames_dir, '_frames_*.json'))
    t = {}
    if meta:
        for f in json.load(open(meta[0]))['frames']:
            mt = f.get('media_t', -1)
            t[f['file']] = mt if mt is not None and mt >= 0 else None
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--frames', required=True, nargs='+', help='one or more frame dirs (later dirs replace earlier files)')
    ap.add_argument('--labels', required=True); ap.add_argument('--crop', default='60,580,160,627')
    ap.add_argument('--t0', type=float, required=True); ap.add_argument('--t1', type=float, required=True)
    ap.add_argument('--units', default='mph'); ap.add_argument('--out'); ap.add_argument('--sheet')
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(','))
    files, times = {}, {}
    for d in a.frames:
        mt = frame_times(d)
        for p in sorted(glob.glob(os.path.join(d, 't[0-9][0-9][0-9].jpg'))):
            name = os.path.basename(p)
            t_nom = int(re.findall(r'\d+', name)[0])
            m = mt.get(name)
            if m is None and mt:
                continue        # a stale frame (no presented media time): left out, a later dir may supply it
            files[t_nom] = p; times[t_nom] = m if m is not None else float(t_nom)
    # templates from the labelled frames
    bank = {str(d): [] for d in range(10)}
    for item in a.labels.split(','):
        t, val = item.split(':')
        gs, _ = glyphs(files[int(t)], crop)
        if len(gs) != len(val):
            raise SystemExit(f'label t{t}={val}: {len(gs)} glyphs found')
        for g, ch in zip(gs, val):
            bank[ch].append(g)
    missing = [d for d, v in bank.items() if not v]
    if missing:
        raise SystemExit(f'no template for digits {missing}: label more frames')
    T = {d: np.mean(v, axis=0) for d, v in bank.items()}
    rows = []
    for tn in sorted(files):
        gs, boxes = glyphs(files[tn], crop)
        val, score = '', 1.0
        for g in gs:
            d = {k: float(np.abs(g - tp).mean()) for k, tp in T.items()}
            best = sorted(d.items(), key=lambda kv: kv[1])
            val += best[0][0]
            score = min(score, 1 - best[0][1])          # 1 = identical to the template
            margin = best[1][1] - best[0][1]
        rows.append(dict(t=round(times[tn], 3), frame=os.path.basename(files[tn]), reading=int(val) if val else None,
                         glyphs=len(gs), score=round(score, 3)))
    ok = [r for r in rows if r['reading'] is not None]
    # integrate between the crossings: samples inside, the speed at the crossings interpolated
    t = np.array([r['t'] for r in ok]); v = np.array([r['reading'] for r in ok], float) * UNIT[a.units]

    def integrate(tt, vv):
        inside = (tt > a.t0) & (tt < a.t1)
        T_ = np.r_[a.t0, tt[inside], a.t1]
        V_ = np.r_[np.interp(a.t0, tt, vv), vv[inside], np.interp(a.t1, tt, vv)]
        return float(np.trapezoid(V_, T_)), int(inside.sum())

    D1, n1 = integrate(t, v)
    D2, n2 = integrate(t[::2], v[::2])
    D2b, _ = integrate(t[1::2], v[1::2])
    lap = a.t1 - a.t0
    q = 0.5 * UNIT[a.units] * lap
    res = dict(t0=a.t0, t1=a.t1, lap_s=round(lap, 3), samples=n1, distance_m=round(D1, 1),
               distance_2step_m=[round(D2, 1), round(D2b, 1)], quantisation_bound_m=round(q, 1),
               mean_speed_ms=round(D1 / lap, 3), min_score=min(r['score'] for r in ok), rows=rows)
    print(f"lap {lap:.2f} s, {n1} samples: {D1:.1f} m (every other sample: {D2:.1f} / {D2b:.1f} m); display quantisation "
          f"+-{q:.1f} m; mean {D1 / lap:.2f} m/s; lowest match score {res['min_score']}")
    low = sorted(ok, key=lambda r: r['score'])[:5]
    print('lowest scores:', [(r['frame'], r['reading'], r['score']) for r in low])
    if a.out:
        json.dump(res, open(a.out, 'w'), indent=1)
    if a.sheet:
        cw, ch = (crop[2] - crop[0]), (crop[3] - crop[1])
        cols = 12
        S = Image.new('RGB', (cols * cw, ((len(rows) + cols - 1) // cols) * (ch + 14)), (40, 40, 40))
        for k, r in enumerate(rows):
            im = Image.open(files[int(re.findall(r'\d+', r['frame'])[0])]).crop(crop)
            x, y = (k % cols) * cw, (k // cols) * (ch + 14)
            S.paste(im, (x, y))
            ImageDraw.Draw(S).text((x + 2, y + ch), f"{r['frame'][1:4]}={r['reading']}", fill=(255, 255, 0))
        S.save(a.sheet)


if __name__ == '__main__':
    main()
