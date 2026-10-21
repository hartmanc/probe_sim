"""Boundary audit (build-track stage 4, required before the owner drives; Buttonwillow owner lap 2 note 13: "Check texture
mash-ups and transitions along the track edges, pit in, pit out"). For every surface boundary of a package (the track
edges, each paved area's outline, each paved zone's edges, each kerb run's outer edge, the pit lane's edges), one pose
per `--step` m of boundary: from 0.8 m looking along it and from 2.5 m looking down at it (-35 deg), 4 m ahead of the
car (compare/pose_walk.ts `eye`). Then contact sheets with captions (boundary kind, stations / name, side).

    python3 -I tools/track/compare/boundary_sheets.py poses --pkg public/tracks/<id>/ --out <dir> [--step 30]
    npx tsx tools/track/compare/pose_walk.ts --track <id> --poses <dir>/poses.json --out <dir> --tag b --port 5183
    uv run --python 3.12 --with pillow python -I tools/track/compare/boundary_sheets.py sheets --out <dir>

Read every sheet and list each seam, overlap, gap, z-fight or tone step as a manifest row (kind, stations, side, what,
fixed / open). Stills and sheets are local (git-ignored).
"""
import argparse
import glob
import json
import math
import os


def poses(pkg, out, step):
    T = json.load(open(os.path.join(pkg, 'track.json'))); S = json.load(open(os.path.join(pkg, 'scenery.json')))
    C = T['center']; n = len(C); sp = T['spacing_m']
    P = []

    def along(line, kind, label, closed=False):
        L = [0.0]
        for i in range(1, len(line)):
            L.append(L[-1] + math.dist(line[i][:2], line[i - 1][:2]))
        d = 0.0; k = 0
        while d <= L[-1] and len(line) > 1:
            while k < len(line) - 2 and L[k + 1] < d:
                k += 1
            a, b = line[k], line[k + 1]; t = (d - L[k]) / max(1e-6, L[k + 1] - L[k])
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t; h = math.atan2(b[1] - a[1], b[0] - a[0])
            nm = f"{kind}_{label}_{int(d):04d}"
            # stand 3 m back along the boundary (the pose_walk eye puts the camera 4 m ahead of the car)
            bx, by = x - 7 * math.cos(h), y - 7 * math.sin(h)
            P.append(dict(name=nm + '_low', x=round(bx, 2), y=round(by, 2), z=None, heading=round(h, 3), pitch=-6, eye=0.8))
            P.append(dict(name=nm + '_high', x=round(bx, 2), y=round(by, 2), z=None, heading=round(h, 3), pitch=-35, eye=2.5))
            d += step
    for side, E in (('L', T['left']), ('R', T['right'])):
        along([E[i] for i in range(0, n, 2)] + [E[0]], 'edge', side)
    for a in S.get('paved_areas', []):
        along(a['poly'] + [a['poly'][0]], 'area', a['name'].replace(' ', '-')[:24])
    for z in (S.get('paved_zones') or {}).get('parts', []):
        for sd in ('left', 'right'):
            along(z[sd], 'zone', (z.get('turn', 'zone')[:18] + '-' + sd).replace(' ', '-'))
    for p in (S.get('pit_lane') or {}).get('parts', []):
        for sd in ('left', 'right'):
            along(p[sd], 'pit', sd)
    os.makedirs(out, exist_ok=True)
    json.dump(P, open(os.path.join(out, 'poses.json'), 'w'))
    print(f"{len(P)} poses -> {out}/poses.json")


def sheets(out):
    from PIL import Image, ImageDraw
    fs = sorted(glob.glob(os.path.join(out, '*_b.jpg')))
    W, H, per = 480, 270, 24
    for p in range(0, len(fs), per):
        ch = fs[p:p + per]; sh = Image.new('RGB', (W * 4, H * ((len(ch) + 3) // 4))); d = ImageDraw.Draw(sh)
        for i, f in enumerate(ch):
            x, y = (i % 4) * W, (i // 4) * H
            sh.paste(Image.open(f).resize((W, H)), (x, y)); d.rectangle([x, y, x + W, y + 13], fill='black')
            d.text((x + 3, y + 1), os.path.basename(f)[:-6], fill='yellow')
        sh.save(os.path.join(out, f'sheet_{p // per:03d}.jpg'), quality=85)
    print(f"{len(fs)} stills -> {(len(fs) + per - 1) // per} sheets in {out}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['poses', 'sheets'])
    ap.add_argument('--pkg'); ap.add_argument('--out', required=True); ap.add_argument('--step', type=float, default=30.0)
    a = ap.parse_args()
    poses(a.pkg, a.out, a.step) if a.cmd == 'poses' else sheets(a.out)
