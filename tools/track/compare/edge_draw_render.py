#!/usr/bin/env python3
"""Render the owner's strokes from the edge-drawing page (`edge_draw_page.py`) back onto the outline windows, as the
red / green PNGs `owner_edges.py` reads, plus one JSON of the strokes in image pixels.

    # 1. read the strokes out of the artifact's store (one JSON per window) with the ArtifactData tool:
    #    action list, collection edges, out_dir <docs dir>   ->  <docs dir>/edges/<window id>.json
    # 2. render them:
    uv run --python 3.12 --with pillow python -I tools/track/compare/edge_draw_render.py \
        --docs <docs dir>/edges --win <page dir>/win --out tools/track/compare/<track>/owner_edges_rN

Writes <out>/<window id>_marked.png (the window with the strokes drawn in pure red (255,0,0) / green (0,224,0), 4 px,
clipped to the image; points in the margin are kept in the JSON and clipped in the PNG), <out>/strokes.json
({window id: {w, h, margin, strokes}}) and <out>/windows.json ({window id: {s, kind, png}} with the station parsed from
`w_sNNNN` / `close_sNNNN`, for the per-window `owner_edges.py` runs). Windows with no strokes are listed and skipped.
The PNGs are derived from reference captures: local only, never committed; the JSON is the evidence and is tracked.
"""
import argparse
import json
import os
import re

from PIL import Image, ImageDraw

RED = (255, 0, 0)
GREEN = (0, 224, 0)


def load_docs(docs):
    out = {}
    for f in sorted(os.listdir(docs)):
        if not f.endswith('.json'):
            continue
        d = json.load(open(os.path.join(docs, f)))
        data = d.get('data', d)  # ArtifactData out_dir files wrap the document in {id, data, version}
        wid = d.get('id') or os.path.splitext(f)[0]
        strokes = [s for s in data.get('strokes', []) if s.get('pts') and len(s['pts']) >= 1]
        if strokes:
            out[wid] = {'w': data.get('w'), 'h': data.get('h'), 'margin': data.get('margin', 0), 'strokes': strokes}
    return out


def find_window(win, wid):
    for ext in ('.jpg', '.jpeg', '.png'):
        p = os.path.join(win, wid + ext)
        if os.path.exists(p):
            return p
    return None


def render(docs, win, out):
    os.makedirs(out, exist_ok=True)
    strokes = load_docs(docs)
    windows, missing = {}, []
    for wid, rec in strokes.items():
        src = find_window(win, wid)
        if not src:
            missing.append(wid)
            continue
        im = Image.open(src).convert('RGB')
        if rec['w'] and (im.width, im.height) != (rec['w'], rec['h']):
            raise SystemExit(f'{wid}: window is {im.width}x{im.height} but the strokes were drawn on {rec["w"]}x{rec["h"]}')
        dr = ImageDraw.Draw(im)
        for st in rec['strokes']:
            col = GREEN if st.get('c') == 'green' else RED
            pts = [(float(x), float(y)) for x, y in st['pts']]
            if len(pts) == 1:
                pts = pts * 2
            dr.line(pts, fill=col, width=4, joint='curve')
        png = os.path.join(out, wid + '_marked.png')
        im.save(png)
        m = re.search(r's(\d+)', wid)
        windows[wid] = {'s': int(m.group(1)) if m else None, 'kind': 'close' if wid.startswith('close_') else 'window',
                        'png': png, 'strokes': len(rec['strokes']),
                        'red': sum(1 for s in rec['strokes'] if s.get('c') != 'green'),
                        'green': sum(1 for s in rec['strokes'] if s.get('c') == 'green')}
    json.dump(strokes, open(os.path.join(out, 'strokes.json'), 'w'), indent=1)
    json.dump(windows, open(os.path.join(out, 'windows.json'), 'w'), indent=1)
    return windows, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--docs', required=True, help='directory of the per-window JSON documents (ArtifactData out_dir/<coll>)')
    ap.add_argument('--win', required=True, help='directory of the window images the page was built from')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    windows, missing = render(a.docs, a.win, a.out)
    for wid, w in windows.items():
        print(f'{wid}: s {w["s"]} {w["red"]} red, {w["green"]} green -> {w["png"]}')
    print(f'{len(windows)} windows rendered' + (f'; no image for {missing}' if missing else ''))


if __name__ == '__main__':
    main()
