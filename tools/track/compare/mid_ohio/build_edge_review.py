"""Render the Mid-Ohio stage-1 outline checkpoint, never a driveable preview.

Run with the pipeline's Python dependencies, from repo root:
  python -I tools/track/compare/mid_ohio/build_edge_review.py --pkg tools/track/out/mid_ohio
Reference captures stay local. Windows/metadata are reproducible from config+package.
"""
import argparse
import html
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', default='tools/track/out/mid_ohio')
    ap.add_argument('--out', default='tools/track/compare/mid_ohio/edges_r1')
    ap.add_argument('--close', default='', help='comma-separated extra stations, 0.06 m/px')
    ap.add_argument('--round', type=int, default=1)
    ap.add_argument('--kerb-edge', choices=['outer', 'inner'], default='outer')
    args = ap.parse_args()
    pkg, out = ROOT / args.pkg, ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    t = json.loads((pkg / 'track.json').read_text())
    c, le, ri = (np.asarray(t[k]) for k in ('center', 'left', 'right'))
    width = np.linalg.norm(le[:, :2] - ri[:, :2], axis=1)
    n, sp, length = t['n'], t['spacing_m'], t['length_m']
    stations = [('w', s, 75, .12) for s in range(0, int(length), 125)]
    stations += [('close', int(s), 40, .06) for s in args.close.split(',') if s]
    windows, figures = [], []
    for prefix, s, half, mpp in stations:
        name = f'{prefix}_s{s:04d}'
        indices = np.arange(int((s - half) / sp), int((s + half) / sp) + 1) % n
        q = np.percentile(width[indices], [5, 50, 95])
        cap = (f's {s-half} to {s+half} m (wraps at {length:.1f} m); '
               f'width p5 / median / p95 {q[0]:.2f} / {q[1]:.2f} / {q[2]:.2f} m; '
               f'{mpp:.2f} m/px. Red: fitted course edges; yellow: station ticks. North up.')
        cmd = [sys.executable, '-I', str(ROOT / 'tools/track/compare/capwin.py'),
               '--track', 'mid_ohio', '--pkg', str(pkg), '--s', str(s),
               '--half', str(half), '--mpp', str(mpp), '--light',
               '--edge-color', '255,55,55', '--edge-width', '2', '--halo', '1',
               '--out', str(out / f'{name}.jpg')]
        subprocess.run(cmd, cwd=ROOT, check=True)
        k = round(s / sp) % n
        windows.append(dict(id=name, s=s, half=half, mpp=mpp,
                            center_enu=c[k, :2].tolist(), width_p5_p50_p95=q.tolist()))
        figures.append(f'<figure id="{name}"><img src="{name}.jpg" loading="lazy" alt="{name}">'
                       f'<figcaption>{html.escape(cap)}</figcaption></figure>')
    limits = ('This is an outline review, not an accepted track. The 2019 elevation survey predates the '
              '2023 repave and the 2024 T4 reconstruction (banking reduced from 4 to 2 degrees). '
              'No claim is made that the T4 elevation profile matches the reconstructed road.')
    body = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" '
            'content="width=device-width,initial-scale=1">'
            f'<title>Mid-Ohio edge review — round {args.round}</title>'
            '<style>body{font:16px/1.5 system-ui;margin:24px auto;max-width:1100px;background:#181b20;color:#eee}'
            'h1,p{padding:0 16px}figure{margin:24px 0}img{width:100%;height:auto}figcaption{padding:8px 16px}'
            'a{color:#70c5ff}</style>'
            f'<h1>Mid-Ohio edge review — round {args.round}</h1>'
            f'<p>{html.escape(limits)}</p><p>Length {length:.3f} m. The full outer T1–T2 loop is retained; '
            f'only the inner chicane is omitted. Review the red line against the paint and {args.kerb_edge} kerb boundary.</p>'
            + ''.join(figures) + '</html>')
    (out / 'index.html').write_text(body)
    (out / 'windows.json').write_text(json.dumps(windows, indent=2) + '\n')
    print(f'{len(windows)} outline windows: {out / "index.html"}')


if __name__ == '__main__':
    main()
