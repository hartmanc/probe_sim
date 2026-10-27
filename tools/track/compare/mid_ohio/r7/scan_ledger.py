"""Mid-Ohio round 7, SKILL 3.4 / 3.8 / 3.9 scan ledgers: one row per clean z20 capture (satellite_clean/tiles.json, 91)
and side, with the track stations the capture covers, the modelled barrier runs, stations / masts / towers and boards of
the published package inside the capture's footprint on that side, and the reviewer's note for that capture (NOTES:
what the capture shows that the model does not, or "matches"), from a read of every capture (round7.md section 14).
Ground logos: none legible on any capture (the logo column).

    uv run --python 3.12 --with numpy python -I tools/track/compare/mid_ohio/r7/scan_ledger.py > ledger.md
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
T = json.load(open(os.path.join(ROOT, 'public/tracks/mid_ohio/track.json'))); S = json.load(open(os.path.join(ROOT, 'public/tracks/mid_ohio/scenery.json')))
tiles = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/satellite_clean/tiles.json')))
C = np.array(T['center'])[:, :2]; tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); NL = np.c_[-tg[:, 1], tg[:, 0]]
def proj(P):
    d = ((P[:, None, :] - C[None]) ** 2).sum(2); i = d.argmin(1); return i, ((P - C[i]) * NL[i]).sum(1)
NOTES = json.load(open(os.path.join(HERE, 'scan_notes.json')))
def short(src):
    s = src.replace('declared: ', '')
    return (s.split(' (')[0])[:28]
HW, HH = 1440 * 0.1132 / 2, 725 * 0.1132 / 2
print('| capture | stations | side | barrier runs (package) | stations / masts / towers | boards (panels) | logos | review |')
print('|---|---|---|---|---|---|---|---|')
for t in tiles:
    x, y = t['x'], t['y']
    inb = lambda P: (np.abs(P[:, 0] - x) <= HW) & (np.abs(P[:, 1] - y) <= HH)
    m = inb(C); ii = np.nonzero(m)[0]
    st = f"{ii.min()}-{ii.max()}" if len(ii) and ii.max() - ii.min() < 1800 else (f"{ii[ii > 1800].min()}-{ii[ii < 1800].max()}" if len(ii) else '-')
    for side, sg in (('left', 1), ('right', -1)):
        runs = []
        for b in S['barriers']:
            P = np.array(b['pts'])[:, :2]; k = inb(P)
            if k.sum() < 2: continue
            _, lat = proj(P[k])
            if (np.sign(lat) == sg).mean() > 0.5: runs.append(f"{b['kind']} {short(b['src'])}")
        lm = []; nb = 0
        for L in S['landmarks']:
            P = np.array([[L['x'], L['y']]])
            if not inb(P)[0]: continue
            _, lat = proj(P)
            if np.sign(lat[0]) != sg: continue
            if L['kind'] == 'sign': nb += 1
            elif L['kind'] in ('marshal', 'mast', 'brake', 'impact'): lm.append(L['kind'] + (f" {L.get('text','')}" if L.get('text') else ''))
        for s_ in S.get('structures', []):
            c = s_.get('c') or s_.get('a')
            if c and inb(np.array([c[:2]]))[0] and np.sign(proj(np.array([c[:2]]))[1][0]) == sg: lm.append(s_['type'] + ' ' + s_.get('name', ''))
        note = NOTES.get(t['name'], {}).get(side, 'examined: matches the package')
        print(f"| {t['name']} | {st} | {side} | {'; '.join(sorted(set(runs))) or 'none'} | {'; '.join(sorted(set(lm))) or '-'} | {nb or '-'} | none legible | {note} |")
