"""Re-trace track.json edges on the painted line / kerb outer limit with a corrected detector window (18 Oct 2026).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/fix_edges_paint.py [--only NAME,...] [--write]

Why: tools/track/measure_paint.py walked out from the logged racing line and, where the paint is faint or a pale or
painted apron, a kerb at the apex or a shadow lies beyond it, drifted: the inside edges of T6, T10 and T11 ran 2-4 m
out over the dirt past the apex kerb, the T10 entry edge bowed 1.5 m into the runoff past the straight painted line,
and on the Rahal straight the edges wandered on and off the painted lines (sweep: tools/track/sweep_paint.py; view:
tools/track/compare/straight_strip.py --side). This script re-measures each listed stretch in the frame of the
CURRENT edge on the Google z20 lap captures (UI masked, registration shift from tools/track/out/paint_regs.json):
for each station the image is sampled along the normal at 0.03 m steps inside a per-stretch window [lo, hi] (metres
outward from the current edge) chosen to contain the real paint and to exclude the shadows, aprons and boards that
misled the original detector; a feature score is computed per sample on the most central capture, and a dynamic-programming path through the
stations (at most --max-step m of lateral change per station, as a painted line is smooth) picks the paint. Features:
  line  - a white painted line (bright, unsaturated, not warm dirt), its middle;
  kerb  - the outer limit of a red/white kerb band (kerb then not-kerb going outward);
  both  - the better of the two at each sample (a kerb that starts or ends inside the stretch);
  chord - no image search: the paint is a straight line in the world (checked on the captures) and the edge between
          the end stations, both on it, is put on the straight segment joining them.
'feature@x[@lam[@sigma]]' allows x m of lateral change per station instead of 0.12 (the hairpin apexes, where the paint
leaves the current edge at up to 0.5 m per metre), a step cost lam per 0.03 m (default 0.02) and a smoothing sigma in
stations (default 3; 7 under the 2586 bridge, whose interpolated edge must stay as smooth as it was).
The traced offset is Gaussian-smoothed (sigma 3 stations), blended into the untouched edge at both ends over at least
--blend stations and long enough that no blend step exceeds --max-step-blend m per station, and the half-width moved by it; profile.z columns are re-evaluated at the moved lateral positions from
each station's cross-section quadratic (as fix_edge_waves.py), the centre is untouched. Stations where a pit-lane or
paved-zone part touches this edge (gap <= 0.3 m) are never moved. Every stretch, its window and the evidence are in
STRETCHES below; a report of the move per stretch is printed, and with --dump the traced offsets.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sweep_paint import ui_mask, bilinear, geometry, MPP, SAT, OUTD, EXCLUDE_TILES  # noqa: E402
from fix_edge_waves import quad_eval  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')
DL = 0.03

# name, side, first station, last station, feature, window lo, hi (m outward from the current edge), why
# Not re-traced (18 Oct 2026): T8A exit right 2500-2551, white line 1.2-1.5 m outside the edge at 2540-2560 (world view on
# z20_s2550), but the stretch abuts the 2586 bridge window (2551-2621, fix_bridge_edges' interpolation) and with blends
# under 0.07 m per station less than 0.4 m of the move survives; a 1.9 m move through the window put a self-play car
# four wheels off at station 2584.
STRETCHES = [
    ('T10_entry_left', 'left', 2860, 2940, 'chord', -2.2, 0.6,
     'owner: bows 1.5 m into the runoff; the white line runs straight past the entry kerb (z20_s2890)'),
    ('T8_apex_left', 'left', 2405, 2495, 'both@0.6', -5.0, 0.3,
     'Corkscrew top: edge ran up to 4 m out over the dirt V beyond the apex kerb (z20_s2465). 18 Oct evening: the kerb version (kerb@0.6) was tried again and reverted, one car four wheels off in the alone test; traced to the outer limit of '
     'the painted (green-blue) apex apron, 1.6 m in, not to the kerb at the bottom of the V (3.8 m in): that version moved '
     'the racing line 3.2 m and put a self-play car four wheels off at the T8A exit (station 2582). No chord.'),
    ('T6_apex_left', 'left', 1905, 1975, 'both', -4.0, 0.8,
     'edge ran 2 m out over the dirt V beyond the apex kerb (z20_s1955)'),
    ('T10_apex_right', 'right', 2930, 3005, 'both', -4.0, 0.8,
     'edge ran 1.5 m out over the dirt beyond the apex kerb and sausage (z20_s2975)'),
    ('T11_apex_left', 'left', 3212, 3292, 'both@0.6', -5.0, 0.15,
     'edge ran 3 m out over the dirt and through the tyre wall beyond the apex kerb (z20_s3230)'),
    ('T2_entry_right', 'right', 380, 450, 'line', -3.5, 0.6,
     'edge 2-2.9 m out on the paved braking apron past the white line (z20_s0425); apron -> paved zone'),
    ('Rahal_left', 'left', 2122, 2250, 'line', -2.6, 0.6,
     'edge 1-2 m out on the pale paved apron left of the painted line (z20_s2125/s2210; NAIP ridge agrees); before 2122 the T6 exit apron is kept'),
    ('Rahal_right', 'right', 2150, 2250, 'line', -0.4, 1.8,
     'edge 1.0-1.4 m inside the painted line (z20_s2210)'),
    ('T1_right', 'right', 140, 345, 'both', -0.4, 2.0,
     'edge 0.6-1.1 m inside the white line through T1 and inside the exit kerb (z20_s0170/s0255/s0340)'),
    ('T4T5_right', 'right', 1225, 1480, 'kerb', -0.3, 1.8,
     'edge on the inner side of the long red/white strip; its outer limit is 0.6-1.0 m out (z20_s1275/s1360/s1445)'),
    ('T9_approach_right', 'right', 2615, 2680, 'both', -0.8, 3.2,
     'edge on the inner side of the T9-approach kerb; its outer limit is 1.0-1.6 m out (z20_s2635)'),
]


def tiles_and_images():
    regs = {r[0]: r for r in json.load(open(os.path.join(OUTD, 'paint_regs.json')))}
    tiles = [t for t in json.load(open(os.path.join(SAT, 'z20_tiles.json'))) if t['name'] not in EXCLUDE_TILES]; cache = {}
    def img(t):
        if t['name'] not in cache:
            im = np.asarray(Image.open(os.path.join(SAT, t['name'] + '_google.jpg')).convert('RGB')).astype(np.float32)
            cache[t['name']] = (im, ui_mask(*im.shape[:2]))
        return cache[t['name']]
    return tiles, regs, img


def sample_profiles(C, NL, hw, sg, ks, offs, tiles, regs, img):
    """RGB along the outward normal at offsets `offs` from the current edge, per station and per capture covering the
    whole profile clear of the UI. Returns (best, all): best (len(ks), len(offs), 3) from the capture where the profile
    sits most central (for the evidence image, NaN where none) and all = per station a list of profiles."""
    P = np.full((len(ks), len(offs), 3), np.nan, np.float32); ALL = [[] for _ in ks]
    for i, k in enumerate(ks):
        lat = sg * (hw[k] + offs); X = C[k, 0] + lat * NL[k, 0]; Y = C[k, 1] + lat * NL[k, 1]; best = None
        for t in tiles:
            im, m = img(t); H, W = im.shape[:2]; r = regs.get(t['name']); dx, dy = (r[1], r[2]) if r and r[3] >= 8 else (0, 0)
            px = W / 2 + (X + dx - t['x']) / MPP; py = H / 2 - (Y + dy - t['y']) / MPP
            if not ((px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)).all(): continue
            if not m[np.round(py).astype(int), np.round(px).astype(int)].all(): continue
            v = bilinear(im, px, py); ALL[i].append(v)
            sc = abs(px.mean() - W * 0.6) / W + abs(py.mean() - H / 2) / H
            if best is None or sc < best[0]: best = (sc, v)
        if best: P[i] = best[1]
    return P, ALL


def box(a, w):
    """running mean over w samples along the last axis (same length, edge-clamped)"""
    k = np.ones(w) / w; pad = w // 2
    ap = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(pad, w - 1 - pad)], mode='edge')
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode='valid'), -1, ap)


def scores(P, feature):
    br = P.mean(2); sat = P.max(2) - P.min(2); warm = P[..., 0] - P[..., 2]
    whiteness = np.clip((br - 150) / 60, 0, 1) * (sat < 40) * (warm < 25)
    red = ((P[..., 0] > 100) & (P[..., 0] - P[..., 1] > 22) & (P[..., 0] - P[..., 2] > 18) & (np.abs(P[..., 1] - P[..., 2]) < 22)).astype(float)
    band = np.maximum(red, whiteness)
    q = lambda m: max(1, int(round(m / DL)))
    out = {}
    if feature in ('line', 'both'):
        # a bright ridge 0.06-0.35 m wide: centre brighter than both sides 0.3 m away
        cen = box(whiteness, q(0.12)); side = 0.5 * (np.roll(box(whiteness, q(0.15)), q(0.3), -1) + np.roll(box(whiteness, q(0.15)), -q(0.3), -1))
        out['line'] = np.clip(cen - side, 0, 1)
    if feature in ('kerb', 'both'):
        # band just inside (with red somewhere in the 0.8 m inside), not-band just outside
        inside = np.roll(box(band, q(0.3)), q(0.15), -1); outside = np.roll(box(band, q(0.3)), -q(0.2), -1)
        redin = np.roll(box(red, q(0.8)), q(0.4), -1)
        out['kerb'] = np.clip(inside - outside, 0, 1) * np.clip(redin * 4, 0, 1)
    if feature == 'both': return np.maximum(out['line'], out['kerb'])
    return out[feature]


def dp_path(S, max_step_cells, lam):
    """maximise sum S[i, j_i] - lam * |j_i - j_{i-1}| with |j_i - j_{i-1}| <= max_step_cells"""
    n, m = S.shape; acc = S[0].copy(); back = np.zeros((n, m), int)
    for i in range(1, n):
        best = np.full(m, -1e9); arg = np.zeros(m, int)
        for d in range(-max_step_cells, max_step_cells + 1):
            src = np.roll(acc, d) - lam * abs(d)
            if d > 0: src[:d] = -1e9
            elif d < 0: src[d:] = -1e9
            better = src > best; best[better] = src[better]; arg[better] = (np.arange(m) - d)[better]
        acc = best + S[i]; back[i] = arg
    j = np.zeros(n, int); j[-1] = int(np.argmax(acc))
    for i in range(n - 1, 0, -1): j[i - 1] = back[i, j[i]]
    return j


def gauss(v, s):
    r = int(3 * s); w = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); w /= w.sum()
    return np.convolve(np.pad(v, r, mode='edge'), w, mode='valid')


def trace(T, st, tiles, regs, img, max_step=0.12, lam=0.02, sigma=3.0):
    name, side, s0, s1, feature, lo, hi = st[:7]
    if '@' in feature:                          # 'both@0.6': steep hairpin flanks; 'both@0.6@0.005': and a lower step cost
        parts_ = feature.split('@'); feature = parts_[0]; max_step = float(parts_[1])
        if len(parts_) > 2: lam = float(parts_[2])
        if len(parts_) > 3: sigma = float(parts_[3])       # 4th field: smoothing sigma in stations (default 3)
    C, NL, hl, hr = geometry(T); n = len(C); sg = 1 if side == 'left' else -1; hw = hl if side == 'left' else hr
    ks = [k % n for k in range(s0, s1 + 1)]; offs = np.arange(lo, hi + 1e-9, DL)
    P, ALL = sample_profiles(C, NL, hw, sg, ks, offs, tiles, regs, img)
    if feature == 'chord':
        # the painted line is straight in the world here: the edge between the end stations (both on the paint)
        # becomes the straight segment between their edge points, each station moved along its own normal onto it
        E = np.array(T[side])[:, :2]; a_, b_ = E[ks[0]], E[ks[-1]]; t_ = (b_ - a_) / np.linalg.norm(b_ - a_)
        o = np.zeros(len(ks))
        for i, k in enumerate(ks):
            nout = sg * NL[k]; p = E[k] - a_; dperp = p @ np.array([-t_[1], t_[0]])     # signed distance to the line
            denom = nout @ np.array([-t_[1], t_[0]]); o[i] = -dperp / denom if abs(denom) > 1e-6 else 0.0
        return ks, o, np.ones(len(ks)), P, offs
    have = ~np.isnan(P[:, 0, 0])
    S = np.zeros((len(ks), len(offs)))
    # the most central capture per station (what the evidence image shows). A consensus over all captures blurred the
    # paint where two captures' registrations differ by ~0.7 m (z20_s1870 / z20_s1955 at T6)
    if have.any(): S[have] = scores(P[have], feature)
    j = dp_path(S, max(1, int(round(max_step / DL))), lam)
    o = offs[j].astype(float); conf = S[np.arange(len(ks)), j]
    o[~have] = np.nan
    if np.isnan(o).all(): return ks, o, conf
    idx = np.arange(len(o)); o = np.interp(idx, idx[~np.isnan(o)], o[~np.isnan(o)])
    return ks, gauss(o, sigma), conf, P, offs


def junction_stations(T, SC, tol=0.3, near=1.5):
    """Track stations per side where a pit_lane or paved_zones part touches that edge (part gap <= tol m): each such
    part point is mapped to the nearest track station whose edge on that side lies within `near` m of it."""
    E = {s: np.array(T[s])[:, :2] for s in ('left', 'right')}; out = {'left': set(), 'right': set()}
    for grp in ('pit_lane', 'paved_zones'):
        for part in (SC.get(grp) or {}).get('parts', []):
            for key, gaps in (('left', part['gap_left']), ('right', part['gap_right'])):
                for i, g in enumerate(gaps):
                    if g is None or g > tol: continue
                    q = np.array(part[key][i][:2])
                    for side in ('left', 'right'):
                        d = np.hypot(*(E[side] - q).T); k = int(np.argmin(d))
                        if d[k] < near: out[side].add(k)
    return out


def evidence_png(path, st, ks, P, offs, dv):
    """edge-relative strip (station along x, 4 px each; offset up = outward, 0.03 m/px): green = current edge,
    magenta = +-0.4 m, red = the re-traced edge"""
    from PIL import ImageDraw
    os.makedirs(os.path.dirname(path), exist_ok=True)
    A = np.nan_to_num(P[:, ::-1, :]).clip(0, 255).astype(np.uint8).transpose(1, 0, 2)   # rows: outward at top
    im = Image.fromarray(A).resize((len(ks) * 4, len(offs)), Image.NEAREST); d = ImageDraw.Draw(im)
    y = lambda o: (offs[-1] - o) / DL
    for i, k in enumerate(ks):
        x = i * 4
        if i % 2 == 0: d.line([(x, y(0)), (x + 3, y(0))], fill=(40, 255, 40), width=2)
        if i % 4 == 0:
            for v in (0.4, -0.4): d.point([(x, y(v))], fill=(255, 0, 255))
        d.line([(x, y(dv[i])), (x + 3, y(dv[i]))], fill=(255, 30, 30), width=2)
        if k % 10 == 0: d.line([(x, 0), (x, 5)], fill=(255, 255, 0)); d.text((x + 2, 0), str(k), fill=(255, 255, 0))
    im.save(path)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true'); ap.add_argument('--only', default='')
    ap.add_argument('--blend', type=int, default=12); ap.add_argument('--max-step-blend', type=float, default=0.07); ap.add_argument('--dump', action='store_true'); ap.add_argument('--png', default='')
    ap.add_argument('--track', default=os.path.join(OUT, 'track.json'))
    a = ap.parse_args()
    T = json.load(open(a.track)); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']; Cc, L, R = T['center'], T['left'], T['right']
    prot = junction_stations(T, SC)
    tiles, regs, img = tiles_and_images()
    C, NL, hl, hr = geometry(T)
    move = {'left': np.zeros(n), 'right': np.zeros(n)}
    only = set(a.only.split(',')) if a.only else None
    for st in STRETCHES:
        name, side = st[0], st[1]
        if only and name not in only: continue
        ks, o, conf, P, offs = trace(T, st, tiles, regs, img)
        # blend length per end: at least --blend stations, long enough that the smoothstep's steepest step stays
        # under --max-step-blend m per station (1.5 x the mean slope), at most half the stretch
        m = len(ks); w = np.ones(m)
        def blen(v): return int(min(m // 2, max(a.blend, math.ceil(1.5 * abs(v) / a.max_step_blend))))
        b0 = blen(o[min(m - 1, a.blend)]); b1 = blen(o[max(0, m - 1 - a.blend)])
        for i in range(m):
            if i < b0: t = i / b0; w[i] = min(w[i], t * t * (3 - 2 * t))
            if m - 1 - i < b1: t = (m - 1 - i) / b1; w[i] = min(w[i], t * t * (3 - 2 * t))
        dv = o * w
        P_ = sorted(prot[side])
        for i, k in enumerate(ks):                 # junction stations keep their edge, 15-station blend around them
            if P_:
                d = min(min(abs(k - p_), n - abs(k - p_)) for p_ in P_)
                if d < 15: dv[i] *= d / 15
            move[side][k] = dv[i]
        print(f'{name:28s} {side:5s} {st[2]:4d}-{st[3]:4d} {st[4]:4s} win [{st[5]:+.1f},{st[6]:+.1f}]  move p50 {np.median(dv):+.2f} '
              f'min {dv.min():+.2f} max {dv.max():+.2f}  score p50 {np.median(conf):.2f}')
        if a.png: evidence_png(os.path.join(a.png, f'retrace_{name}.png'), st, ks, P, offs, dv)
        if a.dump:
            print('   ' + ' '.join(f'{k}:{v:+.2f}' for k, v in list(zip(ks, dv))[::5]))
    if not a.write: print('dry run; --write to apply'); return
    for k in range(n):
        dl, dr = move['left'][k], move['right'][k]
        if dl == 0 and dr == 0: continue
        hl_o, hr_o = hl[k], hr[k]; hl_n, hr_n = hl_o + dl, hr_o + dr
        xs_old = [(-f) * hl_o if f < 0 else -f * hr_o for f in fr]; xs_new = [(-f) * hl_n if f < 0 else -f * hr_n for f in fr]
        znew = [quad_eval(xs_old, Z[k], x) for x in xs_new]; znew[fr.index(0)] = Z[k][fr.index(0)]
        Z[k] = [round(z, 3) for z in znew]; nx, ny = NL[k]; c = Cc[k]
        L[k] = [round(c[0] + nx * hl_n, 3), round(c[1] + ny * hl_n, 3), Z[k][0]]
        R[k] = [round(c[0] - nx * hr_n, 3), round(c[1] - ny * hr_n, 3), Z[k][-1]]
    names = [s[0] for s in STRETCHES if not only or s[0] in only]
    note = ('18 Oct 2026: fix_edges_paint.py ' + ' '.join(f'--{k}' for k in ('write',)) + f' --blend {a.blend} --max-step-blend {a.max_step_blend}: edges re-traced on '
            'the z20 captures (excluded: ' + ','.join(sorted(EXCLUDE_TILES)) + ') over ' + '; '.join(
                f'{s_[0]} {s_[1]} {s_[2]}-{s_[3]} {s_[4]} [{s_[5]},{s_[6]}]' for s_ in STRETCHES if not only or s_[0] in only))
    if isinstance(T.get('notes'), dict):
        T['notes']['paint_retrace'] = note
        T['notes']['edge_convention'] = ('track edge = the painted edge line where there is no kerb, the outer limit of the flat '
                                         'kerb where there is one (sausage strips sit behind the kerb); 18 Oct 2026')
        T['notes']['excluded_captures'] = 'z20_s3400 never traced: its ortho registration (-1.8,+0.9 m) is ~1.3 m off its neighbours (sweep_paint.EXCLUDE_TILES)'
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')


if __name__ == '__main__':
    sys.exit(main())
