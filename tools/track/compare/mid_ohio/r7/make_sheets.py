"""Mid-Ohio round 7 compare sheets (build-track 4.1-4.2, the drive proxy): every still of a camera_walk.ts walk
(compare_sheets_r7/walk.json, sim/) beside the reference frame at the same station from the inventory's time maps:
  fwd    the N837 hood frame (Apr 2026, every 1 s) and the 2025 360 lap's ahead view (every 0.5 s): a triple
  left / right (rows)  the 360 lap's left / right view (0.5 s) at that station
  back   the 360 lap's back view (every 2 s) at that station
  pit    the 360 lap's left view abeam (the pit lane seen from the track: no 2024+ video drives the lane)
  runoff the 360 lap's view toward the runoff's side at the station
Six pairs (or four triples) per sheet, captioned with the station, the corner and the inventory rows near it. Images are
reference only and local (ignored by git); index.md lists the sheets.

    python3 -I tools/track/compare/mid_ohio/r7/make_sheets.py <package dir> <compare_sheets_r7 dir>
    (run with: uv run --python 3.12 --with pillow python -I ...)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'track', 'inventory'))
import inventory as INV  # noqa: E402

pkg, sdir = sys.argv[1:3]
T = json.load(open(os.path.join(pkg, 'track.json')))
n = T['n']; sp = T['spacing_m']; L = n * sp
IDIR = os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory')
src = json.load(open(os.path.join(IDIR, 'source.json')))
inv = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory.json')))
prof = INV.speed_profile(T)
anchors, _ = INV.anchors_from(src, T)
tm = INV.TimeMap(anchors, L, prof, sp)
m360 = next(m for m in src['extra_maps'] if m['name'].startswith('360'))
a360, _ = INV.anchors_from(m360, T)
tm360 = INV.TimeMap(a360, L, prof, sp, strict=True)
walk = json.load(open(os.path.join(sdir, 'walk.json')))


def n837(s):
    t = tm.t(s)
    tf = int(round(t))
    for d in (0, 1, -1, 2, -2):
        f = f'frames_n837/t{tf + d:03d}.jpg'
        if os.path.exists(os.path.join(IDIR, f)):
            return f, tf + d, INV.sigma_at(tm, t)
    return None, tf, None


def v360(s, view):
    s2 = s + L
    if s2 > a360[-1]['s']:
        s2 -= L
    t = tm360.t(s2)
    if view == 'back':
        k = int(round(t / 2)) * 2
        f = f'frames_360/t{k:03d}_back.jpg'
        tt = k
    else:
        k = int(round(t * 2))
        f = f'frames_360_half/h{k:04d}_{view}.jpg'
        tt = k / 2
    return (f if os.path.exists(os.path.join(IDIR, f)) else None), tt, INV.sigma_at(tm360, t)


def corner_at(s):
    best = min(T['corners'], key=lambda c: min(abs(c['s'] - s), L - abs(c['s'] - s)))
    d = (s - best['s'] + L / 2) % L - L / 2
    return f"{best['turn']} {'+' if d >= 0 else '-'}{abs(d):.0f} m"


def rows_near(s, side=None, tol=25):
    out = {}
    for r in inv['rows']:
        if r.get('scope', 'lap') != 'lap' or r['kind'] in ('paint', 'runoff'):
            continue
        d = abs(r['s'] - s); d = min(d, L - d)
        if d <= tol and (side is None or r['side'] == side):
            out.setdefault(r['side'], set()).add(r['kind'])
    return out


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


F, FS = font(18), font(15)
IW, IH = 560, 315


def fit(path, label):
    im = Image.new('RGB', (IW, IH), (40, 40, 40))
    if path and os.path.exists(path):
        a = Image.open(path).convert('RGB')
        r = min(IW / a.width, IH / a.height)
        a = a.resize((max(1, round(a.width * r)), max(1, round(a.height * r))))
        im.paste(a, ((IW - a.width) // 2, (IH - a.height) // 2))
    else:
        ImageDraw.Draw(im).text((20, IH // 2), 'no frame', fill=(200, 200, 200), font=F)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 + d.textlength(label, font=FS) + 8, 22], fill=(0, 0, 0))
    d.text((6, 3), label, fill=(255, 220, 0) if not label.startswith('SIM') else (0, 220, 255), font=FS)
    return im


def sheet(items, title, path, per_row):
    rows = len(items)
    W = per_row * IW + (per_row + 1) * 10
    H = 50 + rows * (IH + 66)
    im = Image.new('RGB', (W, H), (16, 16, 16))
    d = ImageDraw.Draw(im)
    d.text((12, 14), title, fill=(255, 255, 255), font=F)
    for k, it in enumerate(items):
        y = 50 + k * (IH + 66)
        for j, (p, lab) in enumerate(it['panels']):
            im.paste(fit(p, lab), (10 + j * (IW + 10), y))
        for q, line in enumerate(it['caption'][:2]):
            d.text((12, y + IH + 6 + q * 24), line[:220], fill=(230, 230, 230), font=FS)
    im.save(path, quality=86)


def ref(f):
    return os.path.join(IDIR, f) if f else None


groups = {'fwd': [], 'side': [], 'back': [], 'pit': [], 'runoff': []}
for sh in walk['shots']:
    s = sh['s']; simf = os.path.join(sdir, sh['file'])
    near = rows_near(s)
    rows_txt = 'inventory L: ' + (', '.join(sorted(near.get('left', []))) or '-') + '   R: ' + (', '.join(sorted(near.get('right', []))) or '-')
    if sh['side'] == 'fwd':
        a, ta, sa = n837(s); b, tb, sb = v360(s, 'ahead')
        groups['fwd'].append(dict(s=s, panels=[(simf, f'SIM hood s {s:.0f}'), (ref(a), f'N837 Apr 2026 t{ta:03d} (+-{sa or 0:.0f} m)'),
                                               (ref(b), f'360 lap 2025 ahead t {tb:.1f} (+-{sb or 0:.0f} m)')],
                                  caption=[f"s {s:.0f} m ({corner_at(s)}) forward", rows_txt]))
    elif sh['side'] in ('left', 'right'):
        b, tb, sb = v360(s, sh['side'])
        groups['side'].append(dict(s=s, panels=[(simf, f"SIM turned {sh['side']} s {s:.0f}"), (ref(b), f"360 lap 2025 {sh['side']} t {tb:.1f} (+-{sb or 0:.0f} m)")],
                                   caption=[f"s {s:.0f} m {sh['side'].upper()} ({corner_at(s)})",
                                            f"inventory {sh['side']}: " + (', '.join(sorted(rows_near(s, sh['side'], 10).get(sh['side'], []))) or '-')]))
    elif sh['side'] == 'back':
        b, tb, sb = v360(s, 'back')
        groups['back'].append(dict(s=s, panels=[(simf, f'SIM looking back s {s:.0f}'), (ref(b), f'360 lap 2025 back t {tb:.0f} (+-{sb or 0:.0f} m)')],
                                   caption=[f"s {s:.0f} m ({corner_at(s)}) LOOKING BACK", rows_txt]))
    elif sh['side'] == 'pit':
        b, tb, sb = v360(s, 'left')
        groups['pit'].append(dict(s=s, panels=[(simf, f"SIM pit lane, abeam s {s:.0f}"), (ref(b), f'360 lap 2025 left (from the track) t {tb:.1f}')],
                                  caption=[f"{sh.get('label', 'pit lane')} abeam s {s:.0f} ({corner_at(s)}); no 2024+ video drives the lane", rows_txt]))
    elif sh['side'] == 'runoff':
        b, tb, sb = v360(s, 'right' if 'right' in sh.get('label', '') else 'left')
        groups['runoff'].append(dict(s=s, panels=[(simf, f"SIM from the runoff, s {s:.0f}"), (ref(b), f'360 lap 2025 side t {tb:.1f}')],
                                     caption=[f"from the runoff: {sh.get('label', '')}"[:200], rows_txt]))
index = []
for kind, items in groups.items():
    items.sort(key=lambda it: it['s'])
    per = 4 if kind == 'fwd' else 6
    for k in range(0, len(items), per):
        grp = items[k:k + per]
        name = f'sheet_{kind}_{k // per:02d}.jpg'
        sheet(grp, f"mid_ohio round 7 {kind}: s {grp[0]['s']:.0f}-{grp[-1]['s']:.0f} m (SIM left, references right)", os.path.join(sdir, name),
              3 if kind == 'fwd' else 2)
        index.append((kind, name, grp[0]['s'], grp[-1]['s'], ', '.join(sorted({corner_at(it['s']).split()[0] for it in grp}))))
md = ['# mid_ohio round 7: compare sheets (drive proxy, local only)', '',
      'camera_walk.ts stills of the published package beside the N837 hood frame (Apr 2026) and the 2025 360 lap at the same '
      'station (time maps of inventory/source.json). Reference imagery: local only, never committed, never a texture.', '',
      '| sheet | kind | stations (m) | corners |', '|---|---|---|---|']
md += [f'| [{nm}]({nm}) | {k} | {a:.0f}-{b:.0f} | {c} |' for k, nm, a, b, c in index]
open(os.path.join(sdir, 'index.md'), 'w').write('\n'.join(md) + '\n')
print(', '.join(f'{k} {len(v)}' for k, v in groups.items()), f'-> {len(index)} sheets in {sdir}')
