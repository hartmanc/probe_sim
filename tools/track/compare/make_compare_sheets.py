"""Compare sheets of the drive proxy (build-track stage 4): the onboard frame at the mapped time on the left, the sim's
hood still at the same station on the right, 6 pairs per sheet, for every 50 m step of the lap and for every inventory
row's side view, and the owner's poses (codify round, 20 Oct 2026): looking back every 100 m (left: the onboard frame
100 m earlier, which looks at the same stretch from its other end), inside the pit lane (left: the nearest pit-lane
video frame of the inventory), and from each paved runoff looking back at the track (left: the onboard frame at that
station, the stretch seen from the track). These are what the orchestrator and the judge review before the owner drives
(JUDGE.md, whose checklist is answered per sheet).

    uv run --python 3.12 --with pillow python -I tools/track/compare/make_compare_sheets.py --track sonoma

Inputs under tools/track/compare/<id>/: compare_sheets/walk.json and sim/ (camera_walk.ts), compare_sheets/onboard/
s####.jpg with onboard.json (the onboard frame at the time-to-station map's time of every step, captured from the video
in Chrome: reference only), inventory.json and inventory/frames/ (the 2 s inventory frames, for the side views).
Output: compare_sheets/sheet_fwd_##.jpg, sheet_side_##.jpg, sheet_back_##.jpg, sheet_pit_##.jpg, sheet_runoff_##.jpg
and index.md (local only: ignored by git).
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
    side = [s for s in walk['shots'] if s['side'] in ('left', 'right')]
    index = []

    def emit(pairs, kind, title):
        for k in range(0, len(pairs), 6):
            grp = pairs[k:k + 6]
            name = f'sheet_{kind}_{k // 6:02d}.jpg'
            sheet(grp, title.format(a=grp[0]['s'], b=grp[-1]['s']), os.path.join(sdir, name))
            index.append((kind, name, grp[0]['s'], grp[-1]['s'], ', '.join(sorted({corner_at(track, p['s']).split()[0] for p in grp}))))

    def onboard_at(s):
        """the onboard step frame nearest station s (within half a step), else None"""
        k = min(ob, key=lambda q: min(abs(q - s), L - abs(q - s)), default=None)
        return ob[k] if k is not None and min(abs(k - s), L - abs(k - s)) <= walk['step'] / 2 + 1 else None

    def rows_caption(s, sd=None):
        near = rows_near(inv, s, L)
        if sd:
            return f"inventory {sd[0].upper()}: " + (', '.join(sorted(near.get(sd, []))) or '-')
        return ('inventory L: ' + (', '.join(sorted(near.get('left', []))) or '-') + '   R: ' + (', '.join(sorted(near.get('right', []))) or '-'))[:150]

    pairs = []
    for sh in fwd:
        o = ob.get(round(sh['s']))
        near = rows_near(inv, sh['s'], L)
        cap = [f"s {sh['s']:.0f} m ({corner_at(track, sh['s'])})   onboard {onb['video']} t {o['t']:.2f} s" if o else f"s {sh['s']:.0f} m: no onboard frame",
               'inventory L: ' + ', '.join(sorted(near.get('left', []))) if near.get('left') else 'inventory L: -',
               'inventory R: ' + ', '.join(sorted(near.get('right', []))) if near.get('right') else 'inventory R: -']
        pairs.append({'left': os.path.join(sdir, o['file']) if o else None, 'right': os.path.join(sdir, sh['file']), 'caption': cap, 's': sh['s']})
    emit(pairs, 'fwd', args.track + ": forward, s {a:.0f}-{b:.0f} m (onboard left at the mapped time, sim hood still right)")
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
    emit(spairs, 'side', args.track + ": side views toward inventory rows, s {a:.0f}-{b:.0f} m (onboard 2 s frame left, sim turned to the side right)")
    # the owner's poses: looking back, inside the pit lane, from the runoff
    back_m = walk.get('back_step', 100) or 100
    bpairs = []
    for sh in [s for s in walk['shots'] if s['side'] == 'back']:
        o = onboard_at((sh['s'] - back_m) % L)
        cap = [f"s {sh['s']:.0f} m ({corner_at(track, sh['s'])}) LOOKING BACK toward s {(sh['s'] - back_m) % L:.0f}",
               (f"onboard t {o['t']:.2f} s at s {o['s']:.0f}: the same stretch seen from its other end" if o else 'no onboard frame for the stretch'),
               rows_caption((sh['s'] - back_m / 2) % L)]
        bpairs.append({'left': os.path.join(sdir, o['file']) if o else None, 'right': os.path.join(sdir, sh['file']), 'caption': cap, 's': sh['s']})
    emit(bpairs, 'back', args.track + ": looking back every " + f"{back_m:.0f}" + " m, s {a:.0f}-{b:.0f} (onboard 100 m earlier looking forward left, sim looking back right)")
    pit_frames = [r for r in inv['rows'] if r.get('scope') == 'pit' and r.get('frame')]
    ppairs = []
    for sh in [s for s in walk['shots'] if s['side'] == 'pit']:
        fr = min(pit_frames, key=lambda r: min(abs(r['s'] - sh['s']), L - abs(r['s'] - sh['s'])), default=None)
        pr = sorted({f"{r['side'][0].upper()} {r['kind']}" + (f" {r['attrs'].get('h_m')}m" if r['attrs'].get('h_m') else '') for r in pit_frames
                     if min(abs(r['s'] - sh['s']), L - abs(r['s'] - sh['s'])) <= 25})
        cap = [f"{sh.get('label', 'pit lane')}, abeam s {sh['s']:.0f} ({corner_at(track, sh['s'])})",
               (f"pit-lane frame {fr['frame']} (abeam s {fr['s']:.0f})" if fr else 'no pit-lane frame'),
               ('pit rows: ' + ', '.join(pr))[:150] if pr else 'pit rows: -']
        ppairs.append({'left': os.path.join(cdir, 'inventory', 'frames', fr['frame']) if fr else None, 'right': os.path.join(sdir, sh['file']), 'caption': cap, 's': sh['s']})
    emit(ppairs, 'pit', args.track + ": inside the pit lane end to end, abeam s {a:.0f}-{b:.0f} (pit-lane video frame left, sim right)")
    rpairs = []
    for sh in [s for s in walk['shots'] if s['side'] == 'runoff']:
        o = onboard_at(sh['s'])
        cap = [f"from the runoff: {sh.get('label', '')}"[:150], f"sim looks back at the track at s {sh['s']:.0f} ({corner_at(track, sh['s'])}); "
               + (f"onboard t {o['t']:.2f} s shows the place from the track" if o else 'no onboard frame'), rows_caption(sh['s'])]
        rpairs.append({'left': os.path.join(sdir, o['file']) if o else None, 'right': os.path.join(sdir, sh['file']), 'caption': cap, 's': sh['s']})
    emit(rpairs, 'runoff', args.track + ": from each paved runoff looking back at the track, s {a:.0f}-{b:.0f} (onboard from the track left, sim from the runoff right)")
    md = [f'# {args.track}: compare sheets (drive proxy)', '',
          f'Generated by `tools/track/compare/camera_walk.ts` (sim stills: hood camera `{walk["camera"]}`, {walk["size"][0]}x{walk["size"][1]}, '
          f'{walk["gl"]}) and `make_compare_sheets.py`. Onboard: youtube.com/watch?v={onb["video"]}, frames at the time-to-station map\'s '
          f'time of each {walk["step"]} m step (`inventory.json` anchors). Reference imagery: local only, never committed, never a texture.', '',
          'Review every sheet before the owner drives (build-track stage 4, `tools/track/compare/JUDGE.md`): list every difference '
          'as an inventory-style row (s, side, kind, what the onboard shows, what the sim shows) and answer the checklist per sheet.', '',
          '| sheet | kind | stations (m) | corners |', '|---|---|---|---|']
    for kind, name, a, b, c in index:
        md.append(f'| [{name}]({name}) | {kind} | {a:.0f}-{b:.0f} | {c} |')
    open(os.path.join(sdir, 'index.md'), 'w').write('\n'.join(md) + '\n')
    print(f'{len(pairs)} forward, {len(spairs)} side, {len(bpairs)} back, {len(ppairs)} pit-lane, {len(rpairs)} runoff pairs -> '
          f'{len(index)} sheets in {sdir} (index.md)')


if __name__ == '__main__':
    main()
