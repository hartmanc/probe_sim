"""Mid-Ohio round 7, step 3: every OSM barrier run the builder reads (scenery.json `barriers` of a stage-3 build), with its
side, station range and distance beyond the edge, beside the eye-level inventory rows of kind wall / fence within its
range on its side (what the 2025-26 video shows there). The table the osm_barrier_overrides are written from.

    uv run --python 3.12 --with numpy python -I tools/track/compare/mid_ohio/r7/barrier_table.py <pkg dir with scenery.json>
"""
import json, os, sys
import numpy as np
pkg = sys.argv[1]
T = json.load(open(os.path.join(pkg, 'track.json')))
S = json.load(open(os.path.join(pkg, 'scenery.json')))
inv = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'inventory.json')))
C = np.array(T['center'])[:, :2]; n = len(C); L = n * T['spacing_m']
tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); NL = np.c_[-tg[:, 1], tg[:, 0]]
hl = ((np.array(T['left'])[:, :2] - C) * NL).sum(1); hr = -((np.array(T['right'])[:, :2] - C) * NL).sum(1)
def proj(P):
    d = ((P[:, None, :] - C[None]) ** 2).sum(2); i = d.argmin(1)
    lat = ((P - C[i]) * NL[i]).sum(1)
    out = np.abs(lat) - np.where(lat > 0, hl[i], hr[i])
    return i, lat, out
rows = [r for r in inv['rows'] if r['kind'] in ('wall', 'fence')]
for k, b in enumerate(S['barriers']):
    P = np.array(b['pts'])[:, :2]
    i, lat, out = proj(P)
    for side in (1, -1):
        m = np.sign(lat) == side
        if m.sum() < 2: continue
        ii = i[m]; s0, s1 = int(ii.min()), int(ii.max())
        if s1 - s0 > n / 2:  # wraps
            ii2 = np.where(ii < n / 2, ii + n, ii); s0, s1 = int(ii2.min()), int(ii2.max()) % n
        sd = 'left' if side > 0 else 'right'
        def inr(s):
            return (s0 <= s <= s1) if s0 <= s1 else (s >= s0 or s <= s1)
        near = [r for r in rows if r['side'] == sd and inr(r['s'])]
        kinds = sorted({(r['kind'], r['attrs'].get('type', ''), r['attrs'].get('colour', '')) for r in near})
        print(f"{k:2d} {b['src'][:22]:22s} {b['kind']:8s} h{b.get('h',0):.2f} f{b.get('fence',0):.1f} {sd:5s} s {s0:4d}-{s1:4d} out {np.median(out[m]):5.1f} [{out[m].min():.1f}-{out[m].max():.1f}] rows {len(near)}: {'; '.join(f'{a}:{t} {c}' for a, t, c in kinds)[:160]}")
