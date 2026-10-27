"""Mid-Ohio round 3: the owner's round-2 red (tracks/mid_ohio/owner/r2/<window>.json, owner_edges.py --by-stroke) against
the round-2 fitted edges, per window, side and 10-station block: (owner half-width - fitted half-width) on the r2 centre,
read at the foot of each point's normal. Printed, nothing written."""
import json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import edges_spline as ES  # noqa
T = json.load(open(os.path.join(ROOT, 'tools/track/out/mid_ohio_r2/track.json')))
C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]; n = len(C)
t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
hl = ((L - C) * NL).sum(1); hr = -((R - C) * NL).sum(1)
d = os.path.join(ROOT, 'tools/track/tracks/mid_ohio/owner/r2')
for f in sorted(os.listdir(d)):
    J = json.load(open(os.path.join(d, f)))
    for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
        P = np.array([[x, y] for x, y, *_ in J[side + '_enu_xys']], float)
        if not len(P):
            continue
        s, lat = ES.foot_project(C, NL, P)
        res = sg * lat - np.interp(s, np.arange(n + 1), np.r_[hw, hw[0]])
        far = np.abs(res) > 15
        k = np.round(s).astype(int) % n
        blocks = {}
        for kk, r in zip(k[~far], res[~far]):
            blocks.setdefault(kk // 10 * 10, []).append(r)
        txt = ' '.join(f"{b}:{np.median(v):+.2f}" for b, v in sorted(blocks.items()))
        print(f"{f[:-5]:12s} {side:5s} n={len(P)} far={far.sum()} | {txt}")
