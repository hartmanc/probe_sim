"""Green share along the lap's verges (0-30 m beyond each race edge) on a package's ortho.jpg, per 300 m sector and side.
green = G > R + 4 and G > B + 4; dark = luminance < 80 and not green; paved = low saturation and luminance >= 80 (asphalt, concrete, sand-grey).
    uv run --python 3.12 --with numpy --with pillow python -I verge_stats.py <package dir> <out.json>"""
import json, sys, numpy as np
from PIL import Image
pk = sys.argv[1]; t = json.load(open(pk + '/track.json')); o = t['ortho']
im = np.asarray(Image.open(pk + '/ortho.jpg').convert('RGB')).astype(np.float32); H, W = im.shape[:2]
n = t['n']; C = np.array(t['center'])[:, :2]
res = {}
for side in ('left', 'right'):
    E = np.array(t[side])[:, :2]
    for i in range(0, n, 2):
        A = C[(i - 1) % n]; B = C[(i + 1) % n]; tg = (B - A) / np.hypot(*(B - A)); nl = np.array([-tg[1], tg[0]]); sg = 1 if side == 'left' else -1
        d = np.arange(0.5, 30, 1.0)[:, None]; P = E[i] + sg * nl * d
        px = np.clip(((P[:, 0] - o['x0']) / (o['x1'] - o['x0']) * W).astype(int), 0, W - 1); py = np.clip(((o['y1'] - P[:, 1]) / (o['y1'] - o['y0']) * H).astype(int), 0, H - 1)
        p = im[py, px]; r, g, b = p[:, 0], p[:, 1], p[:, 2]; lum = .299 * r + .587 * g + .114 * b
        green = (g > r + 4) & (g > b + 4); dark = (lum < 80) & ~green
        k = (side, int(i * t['spacing_m'] // 300) * 300); a = res.setdefault(k, [0, 0, 0])
        a[0] += green.sum(); a[1] += dark.sum(); a[2] += len(p)
out = {f'{s}_{b:04d}': dict(green=round(float(a[0] / a[2]), 3), dark=round(float(a[1] / a[2]), 3)) for (s, b), a in sorted(res.items())}
tot = {s: dict(green=round(sum(v[0] for (ss, _), v in res.items() if ss == s) / sum(v[2] for (ss, _), v in res.items() if ss == s), 3),
               dark=round(sum(v[1] for (ss, _), v in res.items() if ss == s) / sum(v[2] for (ss, _), v in res.items() if ss == s), 3)) for s in ('left', 'right')}
out['total'] = tot; json.dump(out, open(sys.argv[2], 'w'), indent=1)
for b in range(0, 3600, 300): print(f'{b:4d}-{b+300:4d}  L green {out[f"left_{b:04d}"]["green"]:.2f} dark {out[f"left_{b:04d}"]["dark"]:.2f} | R green {out[f"right_{b:04d}"]["green"]:.2f} dark {out[f"right_{b:04d}"]["dark"]:.2f}')
print(tot)
