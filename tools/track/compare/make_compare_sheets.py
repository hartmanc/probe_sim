"""Compare sheets of the drive proxy (build-track stage 4): the onboard frame at the mapped time on the left, the sim's
hood still at the same station on the right, 6 pairs per sheet, for every 50 m step of the lap and for every inventory
row's side view. These are what the orchestrator and the judge review before the owner drives (JUDGE.md).

    uv run --python 3.12 --with pillow python -I tools/track/compare/make_compare_sheets.py --track sonoma

Inputs under tools/track/compare/<id>/: compare_sheets/walk.json and sim/ (camera_walk.ts), compare_sheets/onboard/
s####.jpg with onboard.json (the onboard frame at the time-to-station map's time of every step, captured from the video
in Chrome: reference only), inventory.json and inventory/frames/ (the 2 s inventory frames, for the side views).
Output: compare_sheets/sheet_fwd_##.jpg, sheet_side_##.jpg and index.md (local only: ignored by git).
"""
import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IW, IH = 560, 315          # one image of a pair
CAP = 74                   # caption strip under a pair
GAP = 10


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc',
              '/Library/Fonts/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except OSError:
                pass
    return ImageFont.load_default()


F, FS = font(17), font(14)


def fit(path):
    if not path or not os.path.exists(path):
        im = Image.new('RGB', (IW, IH), (40, 40, 40))
        ImageDraw.Draw(im).text((20, IH // 2), 'no frame', fill=(200, 200, 200), font=F)
        return im
    im = Image.open(path).convert('RGB')
    r = min(IW / im.width, IH / im.height)
    im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))))
    out = Image.new('RGB', (IW, IH), (0, 0, 0))
    out.paste(im, ((IW - im.width) // 2, (IH - im.height) // 2))
    return out


def corner_at(track, s):
    L = track['n'] * track['spacing_m']
    best = min(track['corners'], key=lambda c: min(abs(c['s'] - s), L - abs(c['s'] - s)))
    d = (s - best['s'] + L / 2) % L - L / 2
    return f"{best['turn']} {'+' if d >= 0 else '-'}{abs(d):.0f} m"


def rows_near(inv, s, L, tol=25, side=None):
    out = {}
    for r in inv['rows']:
        if r.get('scope', 'lap') != 'lap' or r['kind'] in ('paint', 'runoff'):
            continue
        d = abs(r['s'] - s); d = min(d, L - d)
        if d > tol or (side and r['side'] != side):
            continue
        h = r['attrs'].get('h_m')
        out.setdefault(r['side'], set()).add(r['kind'] + (f" {h}m" if h and r['kind'] in ('wall', 'fence', 'tyre_wall') else ''))
    return out


def sheet(pairs, title, path):
    cols, rows = 2, 3
    pw = 2 * IW + GAP
    W = cols * pw + (cols + 1) * 20
    H = 50 + rows * (IH + CAP + GAP) + 10
    im = Image.new('RGB', (W, H), (18, 18, 18))
    d = ImageDraw.Draw(im)
    d.text((20, 14), title, fill=(255, 255, 255), font=F)
    for k, p in enumerate(pairs):
        cx = 20 + (k % cols) * (pw + 20)
        cy = 50 + (k // cols) * (IH + CAP + GAP)
        im.paste(fit(p['left']), (cx, cy))
        im.paste(fit(p['right']), (cx + IW + GAP, cy))
        d.rectangle([cx, cy, cx + 120, cy + 22], fill=(0, 0, 0)); d.text((cx + 4, cy + 3), 'ONBOARD', fill=(255, 220, 0), font=FS)
        d.rectangle([cx + IW + GAP, cy, cx + IW + GAP + 80, cy + 22], fill=(0, 0, 0)); d.text((cx + IW + GAP + 4, cy + 3), 'SIM', fill=(0, 220, 255), font=FS)
        y = cy + IH + 4
        for line in p['caption'][:3]:
            d.text((cx, y), line[:150], fill=(230, 230, 230), font=FS)
            y += 22
    im.save(path, quality=86)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--track', required=True)
    args = ap.parse_args()
    root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
    cdir = os.path.join(HERE, args.track)
    sdir = os.path.join(cdir, 'compare_sheets')
    walk = json.load(open(os.path.join(sdir, 'walk.json')))
    onb = json.load(open(os.path.join(sdir, 'onboard.json')))
    inv = json.load(open(os.path.join(cdir, 'inventory.json')))
    track = json.load(open(os.path.join(root, 'public', 'tracks', args.track, 'track.json')))
    L = track['n'] * track['spacing_m']
    ob = {round(f['s']): f for f in onb['frames']}
    tmap = {round(f['t']): f for f in inv['frames']}
    fwd = [s for s in walk['shots'] if s['side'] == 'fwd']
    side = [s for s in walk['shots'] if s['side'] != 'fwd']
    index = []
    pairs = []
    for sh in fwd:
        o = ob.get(round(sh['s']))
        near = rows_near(inv, sh['s'], L)
        cap = [f"s {sh['s']:.0f} m ({corner_at(track, sh['s'])})   onboard {onb['video']} t {o['t']:.2f} s" if o else f"s {sh['s']:.0f} m: no onboard frame",
               'inventory L: ' + ', '.join(sorted(near.get('left', []))) if near.get('left') else 'inventory L: -',
               'inventory R: ' + ', '.join(sorted(near.get('right', []))) if near.get('right') else 'inventory R: -']
        pairs.append({'left': os.path.join(sdir, o['file']) if o else None, 'right': os.path.join(sdir, sh['file']), 'caption': cap, 's': sh['s']})
    for k in range(0, len(pairs), 6):
        grp = pairs[k:k + 6]
        name = f'sheet_fwd_{k // 6:02d}.jpg'
        sheet(grp, f"{args.track}: forward, s {grp[0]['s']:.0f}-{grp[-1]['s']:.0f} m (onboard left at the mapped time, sim hood still right)", os.path.join(sdir, name))
        index.append(('forward', name, grp[0]['s'], grp[-1]['s'], ', '.join(sorted({corner_at(track, p['s']).split()[0] for p in grp}))))
    spairs = []
    for sh in side:
        # the inventory frame the row came from: nearest 2 s frame whose mapped s is within 15 m, else the nearest
        fr = min(inv['frames'], key=lambda f: min(abs(f['s'] - sh['s']), L - abs(f['s'] - sh['s'])))
        rows = [r for r in inv['rows'] if r.get('scope', 'lap') == 'lap' and r['side'] == sh['side'] and abs(r['s'] - sh['s']) < 10]
        kinds = sorted({r['kind'] for r in rows})
        what = '; '.join(sorted({str(r['attrs'].get('type', ''))[:50] for r in rows if r['kind'] not in ('paint', 'runoff')}))[:300]
        cap = [f"s {sh['s']:.0f} m {sh['side'].upper()} ({corner_at(track, sh['s'])}), sim turned {walk['yaw_deg']} deg {sh['side']}; onboard frame t {fr['t']} s looks ahead",
               f"inventory {sh['side']}: {', '.join(kinds)}", what]
        spairs.append({'left': os.path.join(cdir, 'inventory', 'frames', fr['frame']), 'right': os.path.join(sdir, sh['file']), 'caption': cap, 's': sh['s']})
    spairs.sort(key=lambda p: p['s'])
    for k in range(0, len(spairs), 6):
        grp = spairs[k:k + 6]
        name = f'sheet_side_{k // 6:02d}.jpg'
        sheet(grp, f"{args.track}: side views toward inventory rows, s {grp[0]['s']:.0f}-{grp[-1]['s']:.0f} m (onboard 2 s frame left, sim turned to the side right)", os.path.join(sdir, name))
        index.append(('side', name, grp[0]['s'], grp[-1]['s'], ', '.join(sorted({corner_at(track, p['s']).split()[0] for p in grp}))))
    md = [f'# {args.track}: compare sheets (drive proxy)', '',
          f'Generated by `tools/track/compare/camera_walk.ts` (sim stills: hood camera `{walk["camera"]}`, {walk["size"][0]}x{walk["size"][1]}, '
          f'{walk["gl"]}) and `make_compare_sheets.py`. Onboard: youtube.com/watch?v={onb["video"]}, frames at the time-to-station map\'s '
          f'time of each {walk["step"]} m step (`inventory.json` anchors). Reference imagery: local only, never committed, never a texture.', '',
          'Review every sheet before the owner drives (build-track stage 4, `tools/track/compare/JUDGE.md`): list every difference '
          'as an inventory-style row (s, side, kind, what the onboard shows, what the sim shows).', '',
          '| sheet | kind | stations (m) | corners |', '|---|---|---|---|']
    for kind, name, a, b, c in index:
        md.append(f'| [{name}]({name}) | {kind} | {a:.0f}-{b:.0f} | {c} |')
    open(os.path.join(sdir, 'index.md'), 'w').write('\n'.join(md) + '\n')
    print(f'{len(pairs)} forward pairs, {len(spairs)} side pairs -> {len(index)} sheets in {sdir} (index.md)')


if __name__ == '__main__':
    main()
