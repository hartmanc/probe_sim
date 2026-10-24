"""A kerb's width across it on the ground, read on an onboard frame (Buttonwillow round 11, the owner's rule of 23 Oct
2026: "Use the onboard" for the kerbs). Reference frames are reference only: nothing is copied from them.

    uv run --python 3.12 --with numpy,pillow python -I tools/track/compare/kerb_onboard_width.py <frame.jpg> L|R \
        [--cam-h 1.08] [--f 385]

Level pinhole (compare/HEIGHTS.md) at the camera height H above the road: the horizon row y_h is the first row of warm
land (r > b + 6) from the top in the centre columns (the valley floor is flat to the far hills); per image row of the
nearest 40 % of the rows the paint is found in (above the hood, row < 520), the longest run of red / blue / white paint
on that side gives the lateral extent X = (x - cx) H / (y - y_h) at Z = f H / (y - y_h); the kerb's direction is the
slope of its centre X(Z) (f only matters for this angle), and the width = (X_out - X_in) cos(atan(dX/dZ)), p50 and p80
over the rows (a partly found row only cuts a run short, so p80 is the reading). A reading is VALID when the kerb runs
within 25 deg of the view, p50 / p80 >= 0.75 (the rows agree), at least 8 near rows spanning 40 px or more (not a corner strip beside the overlay), the rows reach row 440 (near), and
the run does not touch the frame's side (a kerb cut by the frame edge reads short).

Buttonwillow's onboard 7QS2M-HGSI4: H = 1.08 m, the mean of the pit-wall Jersey reference (1.05 m, inventory t004) and the
240SX ahead at s 4500 (1.12 m: its 1.69 m width, 145 px at its tyres' row 378, horizon 282).
"""
import argparse
import math

import numpy as np
from PIL import Image


def measure(path, side, H=1.08, fp=385.0):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int); Hh, W, _ = a.shape; cx = W / 2
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    land = r > b + 6
    hz = [80 + np.flatnonzero(land[80:520, x])[0] for x in range(300, 980, 20) if land[80:520, x].any()]
    yh = float(np.median(hz))
    red = (r > 130) & (r - g > 35) & (r - b > 25); blue = (b > 125) & (b - r > 15) & (b - g > 5)
    white = (a.min(2) > 160) & (b > 165) & (r - b < 40); paint = red | blue | white
    x0, x1 = (W // 2, W - 1) if side == 'R' else (0, W // 2)
    rows = []
    for y in range(int(yh) + 40, 520, 3):
        k = np.flatnonzero(paint[y, x0:x1])
        if len(k) < 4:
            continue
        run = max(np.split(k, np.flatnonzero(np.diff(k) > 4) + 1), key=len)
        if run[-1] - run[0] < 6:
            continue
        rows.append((y, x0 + run[0], x0 + run[-1]))
    if len(rows) < 6:
        return dict(frame=path, side=side, valid=False, why=f'{len(rows)} rows')
    near = rows[int(len(rows) * 0.6):]
    Y = np.array([q[0] for q in near], float); lo = np.array([q[1] for q in near], float); hi = np.array([q[2] for q in near], float)
    Z = fp * H / (Y - yh); Xl = (lo - cx) * H / (Y - yh); Xh = (hi - cx) * H / (Y - yh)
    m = np.polyfit(Z, (Xl + Xh) / 2, 1)[0] if len(Z) > 2 and np.ptp(Z) > 0.3 else 0.0
    w = (Xh - Xl) * math.cos(math.atan(m))
    p50, p80 = float(np.percentile(w, 50)), float(np.percentile(w, 80))
    ang = math.degrees(math.atan(m))
    edge = bool(((lo <= 1) | (hi >= W - 2)).any())
    valid = bool(abs(ang) <= 25 and p50 / max(p80, 1e-6) >= 0.75 and len(near) >= 8 and Y.max() >= 440 and Y.max() - Y.min() >= 40 and not edge)
    return dict(frame=path, side=side, horizon=yh, rows=(int(Y.min()), int(Y.max()), len(near)), angle=round(ang), p50=round(p50, 2),
                p80=round(p80, 2), touches_side=edge, valid=valid)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('frame'); ap.add_argument('side', choices=['L', 'R'])
    ap.add_argument('--cam-h', type=float, default=1.08); ap.add_argument('--f', type=float, default=385.0)
    a = ap.parse_args()
    print(measure(a.frame, a.side, a.cam_h, a.f))
