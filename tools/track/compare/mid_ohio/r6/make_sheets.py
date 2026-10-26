"""Mid-Ohio round 6 hood sheet: one PNG per station of hood_r6/frames.json, the sim's hood still (centre; for T8 and
T4 also on the solver's line) beside the N837 Apr 2026 hood frame and the 2025 360 lap's ahead view at the same
station, with the caption the owner judges by; plus sheet_00_overview.png (the stations over the package ortho).
Images are reference only and local (ignored by git).

    uv run --python 3.12 --with pillow python -I tools/track/compare/mid_ohio/r6/make_sheets.py <package dir> <hood_r6 dir>
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
IDIR = os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory')
pkg, hd = sys.argv[1:3]
F = json.load(open(os.path.join(hd, 'frames.json')))
CAP = json.load(open(os.path.join(HERE, 'captions.json')))
T = json.load(open(os.path.join(pkg, 'track.json')))


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


F18, F22, F28 = font(18), font(22), font(28)
PW, PH = 640, 360


def panel(path, label):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    sc = min(PW / w, PH / h)
    im = im.resize((int(w * sc), int(h * sc)), Image.LANCZOS)
    out = Image.new('RGB', (PW, PH + 30), (24, 24, 24))
    out.paste(im, ((PW - im.size[0]) // 2, 30))
    ImageDraw.Draw(out).text((8, 5), label, fill=(240, 240, 240), font=F18)
    return out


def wrap(d, text, width_px, f):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) > width_px:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


for sh in F['sheets']:
    ps = [panel(os.path.join(hd, 'sim', sh['id'] + '.jpg'), f"SIM hood, centre, s {sh['s']:.0f}")]
    if os.path.exists(os.path.join(hd, 'sim', sh['id'] + '_line.jpg')):
        ps.append(panel(os.path.join(hd, 'sim', sh['id'] + '_line.jpg'), f"SIM hood, solver's line, s {sh['s']:.0f}"))
    a, b = sh['n837'], sh['v360']
    ps.append(panel(os.path.join(IDIR, a['frame']), f"N837 Apr 2026, t{a['t']:03d}, s {a['s_frame']:.0f} (+-{a['sigma_m']:.0f} m)"))
    ps.append(panel(os.path.join(IDIR, b['frame']), f"360 lap 2025 ahead, t {b['t']:.1f}, s {b['s_frame']:.0f} (+-{b['sigma_m']:.0f} m)"))
    cols = 2 if len(ps) == 4 else 3
    rows = math.ceil(len(ps) / cols)
    W = cols * PW + (cols + 1) * 8
    cap = CAP.get(sh['id'].split('_', 2)[2], CAP.get(sh['corner'], ''))
    d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    lines = wrap(d0, 'Judge: ' + cap, W - 24, F22)
    top = 48
    Hh = top + rows * (PH + 30 + 8) + 10 + 28 * len(lines) + 12
    img = Image.new('RGB', (W, Hh), (14, 14, 14))
    d = ImageDraw.Draw(img)
    ttl = (f"{sh['id']}  |  {sh['corner']} {sh['name'] if sh['name'] != sh['corner'] else ''} {sh['phase']}  |  s {sh['s']:.0f} m"
           + (f"  |  centre R {sh['radius_m']:.0f} m {sh['dir']}" if 'radius_m' in sh else f"  |  run {sh.get('length_m', 0):.0f} m"))
    d.text((12, 10), ttl, fill=(255, 220, 120), font=F28)
    for k, p in enumerate(ps):
        r, c = divmod(k, cols)
        img.paste(p, (8 + c * (PW + 8), top + r * (PH + 38)))
    y = top + rows * (PH + 38) + 6
    for ln in lines:
        d.text((12, y), ln, fill=(230, 230, 230), font=F22); y += 28
    img.save(os.path.join(hd, sh['id'] + '.png'))

# overview: the stations over the ortho
o = T['ortho']
im = Image.open(os.path.join(pkg, o['file'])).convert('RGB')
sx = im.size[0] / (o['x1'] - o['x0']); sy = im.size[1] / (o['y1'] - o['y0'])
px = lambda x, y: ((x - o['x0']) * sx, (o['y1'] - y) * sy)
d = ImageDraw.Draw(im)
for key, col in (('left', (255, 255, 255)), ('right', (255, 255, 255))):
    P = [px(p[0], p[1]) for p in T[key]]
    d.line(P + [P[0]], fill=col, width=2)
C = T['center']; n = len(C); sp = T['spacing_m']
for sh in F['sheets']:
    i = int(round(sh['s'] / sp)) % n
    x, y = px(C[i][0], C[i][1])
    col = (255, 60, 60) if sh['corner'] == 'T8' else (255, 170, 0) if sh['corner'] == 'T4' else (60, 200, 255)
    d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=col)
    d.text((x + 9, y - 10), sh['id'][6:8], fill=col, font=F22)
d.text((20, 20), 'Mid-Ohio round 6 hood sheet: stations (sheet number); red T8, orange T4', fill=(255, 255, 0), font=F28)
im.save(os.path.join(hd, 'sheet_00_overview.png'))
print('sheets written:', len(F['sheets']) + 1)
