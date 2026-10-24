"""Boundary audit (build-track stage 4, required before the owner drives; Buttonwillow owner lap 2 note 13: "Check texture
mash-ups and transitions along the track edges, pit in, pit out"). For every surface boundary of a package (the track
edges, each paved area's outline, each paved zone's edges, each kerb run's outer edge, the pit lane's edges), one pose
per `--step` m (default 25) of boundary: the camera 1.2 m up, 6 m to the unpaved side, turned to look across the
boundary so both surfaces fill the frame (round 8, checkpoint 4: looking along it showed mostly one side). Then contact sheets with captions (boundary kind, stations / name, side).

    python3 -I tools/track/compare/boundary_sheets.py poses --pkg public/tracks/<id>/ --out <dir> [--step 30]
    npx tsx tools/track/compare/pose_walk.ts --track <id> --poses <dir>/poses.json --out <dir> --tag b --port <dev server>

Every pose name is unique (round 11): the parts of one paved road share a label and carry their index (-p00, -p01, ...).
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
    C = T['center']; n = len(C)
    P = []

    def along(line, kind, label, inside):
        """inside(x, y) -> a point on the paved side; the camera stands 6 m to the other side, 1.2 m up, looking across"""
        L = [0.0]
        for i in range(1, len(line)):
            L.append(L[-1] + math.dist(line[i][:2], line[i - 1][:2]))
        d = 0.0; k = 0
        while d <= L[-1] and len(line) > 1:
            while k < len(line) - 2 and L[k + 1] < d:
                k += 1
            a, b = line[k], line[k + 1]; t = (d - L[k]) / max(1e-6, L[k + 1] - L[k])
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            tx, ty = b[0] - a[0], b[1] - a[1]; l = math.hypot(tx, ty) or 1; nx, ny = -ty / l, tx / l
            ix, iy = inside(x, y)
            if (ix - x) * nx + (iy - y) * ny > 0:
                nx, ny = -nx, -ny                       # (nx, ny) now points to the unpaved side
            # the car 10 m out facing the boundary: pose_walk's eye stands the camera 4 m ahead of it, i.e. 6 m out
            h = math.atan2(-ny, -nx)
            P.append(dict(name=f"{kind}_{label}_{int(d):04d}", x=round(x + 10 * nx, 2), y=round(y + 10 * ny, 2), z=None,
                          heading=round(h, 3), pitch=-12, eye=1.2))
            d += step

    def nearest_centre(x, y):
        i = min(range(0, n, 3), key=lambda k: (C[k][0] - x) ** 2 + (C[k][1] - y) ** 2); return C[i][0], C[i][1]
    for side, E in (('L', T['left']), ('R', T['right'])):
        along([E[i] for i in range(0, n, 2)] + [E[0]], 'edge', side, nearest_centre)
    for a in S.get('paved_areas', []):
        cx = sum(p[0] for p in a['poly']) / len(a['poly']); cy = sum(p[1] for p in a['poly']) / len(a['poly'])
        along(a['poly'] + [a['poly'][0]], 'area', a['name'].replace(' ', '-')[:24], lambda x, y, cx=cx, cy=cy: (cx, cy))
    for parts, kind in (((S.get('paved_zones') or {}).get('parts', []), 'zone'), ((S.get('pit_lane') or {}).get('parts', []), 'pit')):
        # round 11 (Buttonwillow round-10 audit: 214 stills overwritten): the parts of one road (the 12 paddock-lane
        # parts, the 2 parts of the front-straight pale strips and of the front-straight crossover) share a label, so
        # each part of a label used more than once gets its index (-p00, -p01, ...), as the round-10 reshoot named them
        lab = lambda z: z.get('turn', kind)[:18]  # noqa: E731
        count, seen = {}, {}
        for z in parts:
            count[lab(z)] = count.get(lab(z), 0) + 1
        for z in parts:
            Cz = z['center']
            def inside(x, y, Cz=Cz):
                i = min(range(len(Cz)), key=lambda k: (Cz[k][0] - x) ** 2 + (Cz[k][1] - y) ** 2); return Cz[i][0], Cz[i][1]
            k_ = seen.get(lab(z), 0); seen[lab(z)] = k_ + 1
            part = f"-p{k_:02d}" if count[lab(z)] > 1 else ''
            for sd in ('left', 'right'):
                along(z[sd], kind, (lab(z) + '-' + sd + part).replace(' ', '-'), inside)
    # every pose name unique (pose_walk writes <name>_<tag>.jpg: a repeated name overwrites a still); any repeat left
    # (two paved areas with one truncated name) gets a running suffix
    used = {}
    for q in P:
        k_ = used.get(q['name'], 0); used[q['name']] = k_ + 1
        if k_:
            q['name'] = f"{q['name']}-{k_}"
    assert len({q['name'] for q in P}) == len(P), 'pose names not unique'
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
    ap.add_argument('--pkg'); ap.add_argument('--out', required=True); ap.add_argument('--step', type=float, default=25.0)
    a = ap.parse_args()
    poses(a.pkg, a.out, a.step) if a.cmd == 'poses' else sheets(a.out)
