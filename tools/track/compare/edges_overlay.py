"""Overlay old (main) vs new (edges-from-paint-wip) track edges on the z20 satellite captures and the ortho.
Reads both track.json / ghosts.json versions from git; writes two sheets to ~/Desktop/probe_sim_look/."""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = '/Users/cobyhartman/dev/probe_sim'
SAT = f'{ROOT}/tools/track/compare/satellite'
OUT = os.environ.get('OVERLAY_OUT', os.path.expanduser('~/Desktop/probe_sim_look'))
os.makedirs(OUT, exist_ok=True)
MPP = 156543.03 * math.cos(math.radians(36.5843)) / 2 ** 20   # z20 ground resolution, m per px


def git_json(ref, path):
    return json.loads(subprocess.check_output(['git', '-C', ROOT, 'show', f'{ref}:{path}']))


OLD_REF = os.environ.get('OLD_REF', 'main')
old = git_json(OLD_REF, 'public/tracks/laguna_seca/track.json')
new = json.load(open(f'{ROOT}/public/tracks/laguna_seca/track.json')) if os.environ.get('NEW_FROM_TREE') else git_json('edges-from-paint-wip', 'public/tracks/laguna_seca/track.json')
gold = git_json(OLD_REF, 'public/tracks/laguna_seca/ghosts.json')
gnew = json.load(open(f'{ROOT}/public/tracks/laguna_seca/ghosts.json')) if os.environ.get('NEW_FROM_TREE') else git_json('edges-from-paint-wip', 'public/tracks/laguna_seca/ghosts.json')
tiles = [t for t in json.load(open(f'{SAT}/z20_tiles.json')) if t['name'] not in os.environ.get('EXCLUDE_TILES', 'z20_s3400').split(',')]
REGS = {r[0]: r for r in json.load(open(f'{ROOT}/tools/track/out/paint_regs.json'))}


def line_world(t, g):
    """Racing line as world points: centre at s + normal * offset (positive offset toward track.left)."""
    n, sp = t['n'], t.get('spacing_m', 1.0)
    off = g['line']['offset_m']; grid = g['s_grid_m']
    pts = []
    for j, o in enumerate(off):
        s = j * grid; k = int(round(s / sp)) % n
        a, b = t['center'][(k - 1) % n], t['center'][(k + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        c = t['center'][k]
        pts.append((c[0] + nx * o, c[1] + ny * o))
    return pts


LOLD, LNEW = line_world(old, gold), line_world(new, gnew)
SAUSAGES = []
try:
    _sc = json.load(open(f'{ROOT}/public/tracks/laguna_seca/scenery.json')); _sa = _sc.get('sausages')
    if _sa:
        _off = _sa['kerb_width'] + _sa['gap'] + _sa['width'] / 2      # the tube centre, as src/physics/track.ts places it
        for st in _sa['strips']:
            pts = []
            for k in range(int(round(st['s0'] / new['spacing_m'])), int(round(st['s1'] / new['spacing_m'])) + 1):
                k %= new['n']; a_, b_ = new['center'][(k - 1) % new['n']], new['center'][(k + 1) % new['n']]
                tx, ty = b_[0] - a_[0], b_[1] - a_[1]; L = math.hypot(tx, ty) or 1; nx, ny = -ty / L, tx / L
                e = new['left'][k] if st['side'] > 0 else new['right'][k]
                pts.append((e[0] + nx * st['side'] * _off, e[1] + ny * st['side'] * _off))
            SAUSAGES.append(pts)
except Exception as ex: print('no sausages drawn:', ex)
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 22)
    FONT_S = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
except Exception:
    FONT = FONT_S = ImageFont.load_default()

COL = {'old_edge': (255, 60, 60), 'new_edge': (80, 255, 80), 'old_line': (255, 0, 255), 'new_line': (0, 230, 255)}


def draw_track(dr, to_px, t, col_edge, col_centre, width=3, every=1, lo=None, hi=None):
    n = t['n']
    rng = range(n) if lo is None else [(k % n) for k in range(lo, hi)]
    for side in ('left', 'right'):
        pts = [to_px(*t[side][k][:2]) for k in rng]
        dr.line(pts, fill=col_edge, width=width)
    if col_centre:
        pts = [to_px(*t['center'][k][:2]) for k in rng]
        dr.line(pts, fill=col_centre, width=1)


def draw_line(dr, to_px, pts, col, lo_xy=None, r=None, width=2):
    sel = pts if lo_xy is None else [p for p in pts if math.hypot(p[0] - lo_xy[0], p[1] - lo_xy[1]) < r]
    if len(sel) > 1:
        # break the polyline where consecutive points are far apart (wrap / selection gaps)
        seg = [to_px(*sel[0])]
        for a, b in zip(sel, sel[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 6:
                if len(seg) > 1: dr.line(seg, fill=col, width=width)
                seg = []
            seg.append(to_px(*b))
        if len(seg) > 1: dr.line(seg, fill=col, width=width)


# ---------------- corner panels on z20 captures
places = [('T1', 232), ('T2 Andretti', 479), ('T3', 785), ('T4', 1061), ('T5', 1560), ('T6', 1949),
          ('Rahal gantry', 2290), ('T7', 2378), ('T8 Corkscrew', 2448), ('T8A', 2512), ('T9 Rainey', 2729),
          ('T10', 2957), ('T11', 3257), ('Front straight', 3500)]
import os as _os
if _os.environ.get('PLACES_JSON'): places = [tuple(x) for x in json.loads(_os.environ['PLACES_JSON'])]
OUT_TAG = _os.environ.get('OUT_TAG', 'corners')
PW, PH = 900, 560
panels = []
for name, k in places:
    cx, cy = new['center'][k][:2]
    def _score(t):                     # nearest capture whose UI panel (left 480 px, top 600 px) does not hide the station
        px_, py_ = 720 + (cx - t['x']) / MPP, 362 - (cy - t['y']) / MPP
        return math.hypot(px_ - 860, py_ - 380) + (900 if (px_ < 500 and py_ < 620) or py_ < 80 else 0)
    tile = min(tiles, key=_score)
    im = Image.open(f"{SAT}/{tile['name']}_google.jpg").convert('RGB')
    W, H = im.size
    _r = REGS.get(tile['name']); _dx, _dy = (_r[1], _r[2]) if _r and _r[3] >= 8 else (0.0, 0.0)
    def to_px(x, y, tile=tile, W=W, H=H, dx=_dx, dy=_dy):     # registration shift (paint_regs.json), as the edges were traced
        return (W / 2 + (x + dx - tile['x']) / MPP, H / 2 - (y + dy - tile['y']) / MPP)
    dr = ImageDraw.Draw(im)
    lo, hi = k - 120, k + 120
    draw_track(dr, to_px, old, COL['old_edge'], None, width=3, lo=lo, hi=hi)
    draw_track(dr, to_px, new, COL['new_edge'], None, width=3, lo=lo, hi=hi)
    draw_line(dr, to_px, LOLD, COL['old_line'], (cx, cy), 130, width=2)
    draw_line(dr, to_px, LNEW, COL['new_line'], (cx, cy), 130, width=2)
    for pts in SAUSAGES:
        if any(math.hypot(p[0] - cx, p[1] - cy) < 150 for p in pts): dr.line([to_px(*p) for p in pts], fill=(255, 230, 0), width=6)
    px, py = to_px(cx, cy)
    crop = im.crop((int(px - PW / 2), int(py - PH / 2), int(px + PW / 2), int(py + PH / 2)))
    d2 = ImageDraw.Draw(crop)
    d2.rectangle((0, 0, PW, 34), fill=(0, 0, 0))
    ol, orr = old['left'][k], old['right'][k]; nl, nr = new['left'][k], new['right'][k]
    def hw(t, k):
        c = t['center'][k]; return (math.hypot(t['left'][k][0] - c[0], t['left'][k][1] - c[1]), math.hypot(t['right'][k][0] - c[0], t['right'][k][1] - c[1]))
    ho, hn = hw(old, k), hw(new, k)
    d2.text((8, 6), f"{name}  station {k}   old L/R {ho[0]:.1f}/{ho[1]:.1f} m  ->  new {hn[0]:.1f}/{hn[1]:.1f} m   ({tile['name']}, {MPP:.2f} m/px)", fill=(255, 255, 255), font=FONT_S)
    panels.append(crop)

cols = 2; rows = (len(panels) + 1) // 2
sheet = Image.new('RGB', (cols * PW + 30, rows * PH + 90), (18, 18, 18))
d = ImageDraw.Draw(sheet)
d.text((10, 8), f"Laguna Seca edges: {OLD_REF} (RED edges, MAGENTA racing line) vs working tree (GREEN edges, CYAN line), YELLOW = sausage tube centre. Google z20, registration-shifted, north up.", fill=(255, 255, 255), font=FONT)
d.text((10, 40), "Half-widths in each title are metres from the centreline at that station, left/right in the driving direction. Green lines should sit on the white painted edge lines; red shows the extra room the old track had.", fill=(200, 200, 200), font=FONT_S)
for i, p in enumerate(panels):
    sheet.paste(p, (10 + (i % cols) * (PW + 10), 70 + (i // cols) * (PH + 10)))
sheet.save(f'{OUT}/edges_old_vs_new_{OUT_TAG}.jpg', quality=88)

# ---------------- whole lap on the ortho
ob = new['ortho']
im = Image.open(f'{ROOT}/public/tracks/laguna_seca/ortho.jpg').convert('RGB')
W, H = im.size
sx, sy = W / (ob['x1'] - ob['x0']), H / (ob['y1'] - ob['y0'])
def to_px_o(x, y): return ((x - ob['x0']) * sx, (ob['y1'] - y) * sy)
dr = ImageDraw.Draw(im)
draw_track(dr, to_px_o, old, COL['old_edge'], None, width=2)
draw_track(dr, to_px_o, new, COL['new_edge'], None, width=2)
for c in new['corners']:
    k = int(round(c['s'] / new['spacing_m'])) % new['n']
    px, py = to_px_o(*new['center'][k][:2])
    dr.text((px + 8, py - 8), c['name'], fill=(255, 255, 0), font=FONT_S)
# crop to the track bbox
xs = [p[0] for p in new['center']]; ys = [p[1] for p in new['center']]
x0, y0 = to_px_o(min(xs) - 60, max(ys) + 60); x1, y1 = to_px_o(max(xs) + 60, min(ys) - 60)
lap = im.crop((int(x0), int(y0), int(x1), int(y1)))
d = ImageDraw.Draw(lap)
d.rectangle((0, 0, lap.width, 30), fill=(0, 0, 0))
d.text((8, 5), f"Whole lap on the NAIP ortho: RED = {OLD_REF} edges, GREEN = working tree edges.", fill=(255, 255, 255), font=FONT_S)
lap.save(f'{OUT}/edges_old_vs_new_lap.jpg', quality=88)

# ---------------- numbers for the reply
def hwk(t, k):
    c = t['center'][k]; return math.hypot(t['left'][k][0] - c[0], t['left'][k][1] - c[1]) + math.hypot(t['right'][k][0] - c[0], t['right'][k][1] - c[1])
wo = sorted(hwk(old, k) for k in range(old['n'])); wn = sorted(hwk(new, k) for k in range(new['n']))
print('width median old/new', round(wo[len(wo) // 2], 2), round(wn[len(wn) // 2], 2))
print('centre shift p50/max', end=' ')
sh = sorted(math.hypot(new['center'][k][0] - old['center'][k][0], new['center'][k][1] - old['center'][k][1]) for k in range(old['n']))
print(round(sh[len(sh) // 2], 2), round(sh[-1], 2))
print('wrote', f'{OUT}/edges_old_vs_new_corners.jpg', f'{OUT}/edges_old_vs_new_lap.jpg')
