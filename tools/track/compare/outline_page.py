"""The owner's outline review page (Buttonwillow round 9, 22 Oct 2026): the fitted edges over the clean captures for the
whole lap as capwin windows (capwin.py --light: white edges, yellow station ticks, no scenery), plus close-ups, and a
plain index.html listing them in lap order with the station range and the section width under each; the header holds
the width table per section (before / after) and the width gates' numbers.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/outline_page.py --track buttonwillow \
        --pkg tools/track/out/bw_r9e --before public/tracks/buttonwillow --out tools/track/compare/buttonwillow/edges_r9 \
        [--every 125 --half 75 --mpp 0.12] [--close 4180,4354,4475 --close-half 30 --close-mpp 0.06]

Round 10 (23 Oct 2026) adds, for every window the owner drew on, an overlay beside the plain window: his strokes as he
drew them (--strokes: compare/edge_draw_render.py's strokes.json, image pixels of the window he drew on, whose frame
--stroke-frames gives: the owner_edges.py JSON per window, frame centre / half / mpp) in thin red and green over the new
fit, and the cone lines of the mouths he closed (--mouths: compare/owner_mouths.py) as orange dots. --intro / --extra:
html fragments for the header paragraph and a section after the width tables (the round's own record).

Sonoma round 14B (23 Oct 2026): a circuit without a width model gets the owner-reference gates (where his red is drawn)
in place of the width gates, a per-window width table, and every caption carries the width before (the --before
package at the same world points) and after.

The PNGs are reference imagery and stay local (gitignored); the html is tracked.
"""
import argparse
import html
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import edge_gate  # noqa: E402


def gates(T, cfg):
    cw = trackcfg.remap_stations(cfg, T['n'], T['n'] * T['spacing_m'], C=np.array(T['center'])[:, :2])
    lines = []
    if not cw['spline'].get('width_model'):
        # a circuit without a width model (Sonoma round 14B): no sections; the owner-reference gates where he drew
        if cw['spline'].get('owner_edges') and cw['spline'].get('owner_mouths'):
            import build_track
            C = np.array(T['center'])[:, :2]
            ref = build_track.owner_ref(cfg, cw, C, T['n'])
            edge_gate.owner_station_gate(*edge_gate.half_widths(T), ref, cfg['gate'], log=lines.append)
            edge_gate.owner_gates(T, ref, cfg['gate'], log=lines.append)
        return {'sections': []}, lines, []
    J = cw['spline']['width_model']['junctions']
    met, fails = edge_gate.width_gates(T, J, cfg['gate'], log=lines.append)
    return met, lines, J


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True); ap.add_argument('--before', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--every', type=float, default=125.0); ap.add_argument('--half', type=float, default=75.0); ap.add_argument('--mpp', type=float, default=0.12)
    ap.add_argument('--close', default='4180,4354,4475'); ap.add_argument('--close-half', type=float, default=30.0); ap.add_argument('--close-mpp', type=float, default=0.06)
    ap.add_argument('--title', default='Edges, round 9')
    ap.add_argument('--skip-render', action='store_true')
    ap.add_argument('--strokes'); ap.add_argument('--stroke-frames'); ap.add_argument('--mouths')
    # round 14B (owner: "the white line is not very high contrast"): the capwin edge / zone style, passed through
    ap.add_argument('--edge-color'); ap.add_argument('--edge-width'); ap.add_argument('--halo')
    ap.add_argument('--zones-color'); ap.add_argument('--zones-from')
    ap.add_argument('--intro'); ap.add_argument('--extra'); ap.add_argument('--before-label', default='ccf00b4')
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json'))); T0 = json.load(open(os.path.join(a.before, 'track.json')))
    n, sp = T['n'], T['spacing_m']; L = n * sp
    met1, lines1, J = gates(T, cfg); met0, lines0, J0 = gates(T0, cfg)
    wrp = os.path.join(a.pkg, 'work', 'width_model_report.json')
    wr = json.load(open(wrp)) if os.path.exists(wrp) else None   # absent without a width model (Sonoma round 14B)
    os.makedirs(a.out, exist_ok=True)
    capwin = os.path.join(HERE, 'capwin.py')
    hl, hr = edge_gate.half_widths(T); w = hl + hr
    hl0, hr0 = edge_gate.half_widths(T0); w0 = hl0 + hr0
    from scipy.spatial import cKDTree
    kd0 = cKDTree(np.array(T0['center'])[:, :2])

    def before(ks):
        """the width of the --before package at the same world points (its nearest stations)"""
        return w0[kd0.query(np.array(T['center'])[np.asarray(ks) % n, :2])[1]]
    jm = edge_gate.junction_mask(n, J)

    def where(k):
        k %= n
        if jm[k]:
            js = [j for j in J if (k - j[1]) % n <= (j[2] - j[1]) % n]
            return 'junction: ' + '; '.join(f"{j[3]} {j[0]} {j[1] * sp:.0f}-{j[2] * sp:.0f} m" for j in js)
        for s in met1['sections']:
            if (k - s['lo']) % n <= (s['hi'] - s['lo']) % n:
                return f"section {s['lo'] * sp:.0f}-{s['hi'] * sp:.0f} m, width {s['W']:.2f} m"
        return ''
    items = []
    s = 0.0
    while s < L - 1:
        items.append(('lap', s, a.half, a.mpp)); s += a.every
    for c in a.close.split(','):
        if c:
            items.append(('close', float(c), a.close_half, a.close_mpp))
    strokes = json.load(open(a.strokes)) if a.strokes else {}
    mouths = json.load(open(a.mouths))['mouths'] if a.mouths else []
    C_ = np.array(T['center'])[:, :2]

    def overlay(name, png, s, half, mpp):
        """the plain window plus his strokes (thin) and the cone lines, in the new window's pixels"""
        from PIL import Image, ImageDraw
        wid = name[:-4]
        fr = json.load(open(os.path.join(a.stroke_frames, wid + '.json')))['frame']
        ocx, ocy = fr['centre_enu']; oh, om = fr['half'], fr['mpp']
        cx, cy = C_[int(round(s / sp)) % n]
        im = Image.open(png).convert('RGB'); d = ImageDraw.Draw(im)
        to_px = lambda x, y: ((x - (cx - half)) / mpp, ((cy + half) - y) / mpp)  # noqa: E731
        for st in strokes[wid]['strokes']:
            P = [to_px(ocx - oh + px_ * om, ocy + oh - py_ * om) for px_, py_ in st['pts']]
            if len(P) == 1: P = P * 2
            d.line(P, fill=(0, 224, 0) if st.get('c') == 'green' else (255, 0, 0), width=1)
        for m in mouths:
            if not m.get('cones', True):
                continue
            for x, y in m['line_enu']:
                q = to_px(x, y); d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=(255, 140, 0), width=2)
        out = os.path.join(a.out, wid + '_owner.png'); im.save(out)
        return os.path.basename(out)
    rows = []
    for kind, s, half, mpp in items:
        name = f"{'w' if kind == 'lap' else 'close'}_s{int(round(s)):04d}.png"
        if not a.skip_render:
            style = [x for k, v in (('--edge-color', a.edge_color), ('--edge-width', a.edge_width), ('--halo', a.halo),
                                    ('--zones-color', a.zones_color), ('--zones-from', a.zones_from)) if v for x in (k, v)]
            subprocess.run([sys.executable, '-I', capwin, '--track', a.track, '--pkg', a.pkg, '--s', f'{s:.1f}', '--half', str(half),
                            '--mpp', str(mpp), '--light', *style, '--out', os.path.join(a.out, name)], check=True, capture_output=True)
        k = int(round(s / sp)) % n; k0, k1 = int(round((s - half) / sp)), int(round((s + half) / sp))
        ks = np.arange(k0, k1 + 1) % n
        ov = overlay(name, os.path.join(a.out, name), s, half, mpp) if name[:-4] in strokes and a.stroke_frames else None
        rows.append((kind, s, half, mpp, name, where(k), float(w[k]), float(np.median(w[ks])), k0 * sp, k1 * sp, ov,
                     float(before([k])[0]), float(np.median(before(ks))), float(w[ks].min()), float(w[ks].max()),
                     float(before(ks).min()), float(before(ks).max())))
    # the page
    e = html.escape
    sec_rows = []
    for s1 in met1['sections']:
        a0, b0 = s1['lo'] * sp, s1['hi'] * sp
        # the same world range on the old package: the old section whose span holds the new section's middle
        mid = ((s1['lo'] + ((s1['hi'] - s1['lo']) % n) // 2) % n) * sp
        k0 = int(round(mid / T0['spacing_m'])) % T0['n']
        old = next((s0 for s0 in met0['sections'] if (k0 - s0['lo']) % T0['n'] <= (s0['hi'] - s0['lo']) % T0['n']), None)
        ms = next((x for x in wr['sections'] if abs(x['lo'] - s1['lo']) <= 3), None) if wr else None
        sec_rows.append(f"<tr><td>{a0:.0f}-{b0:.0f}</td><td>{old['W'] if old else '-'}</td><td>{old['max_dev'] if old else '-'}</td>"
                        f"<td>{s1['W']:.2f}</td><td>{s1['max_dev']:.3f}</td><td>{ms['obs'] if ms else '-'}</td>"
                        f"<td>{e(', '.join(f'{k} {v}' for k, v in (ms['kinds'] if ms else {}).items() if v))}</td></tr>")
    if wr is None:
        # no width model (Sonoma round 14B): the width per window, before and after (each window's station range)
        sec_rows = [f"<tr><td>{r[8]:.0f}-{r[9]:.0f}{' (close-up)' if r[0] == 'close' else ''}</td><td>{r[12]:.2f}</td><td>{r[15]:.2f}-{r[16]:.2f}</td>"
                    f"<td>{r[7]:.2f}</td><td>{r[13]:.2f}-{r[14]:.2f}</td><td>-</td><td>-</td></tr>" for r in rows]
    j_rows = ''.join(f"<li>{e(j[0])} {j[1] * sp:.0f}-{j[2] * sp:.0f} m: {e(j[3])}</li>" for j in J)
    win_rows = ''.join(
        f"<figure><div class=\"pair\"><img src=\"{e(r[4])}\" alt=\"s {r[1]:.0f}, the new fit\" loading=\"lazy\">"
        + (f"<img src=\"{e(r[10])}\" alt=\"s {r[1]:.0f}, the new fit with your strokes\" loading=\"lazy\">" if r[10] else '')
        + f"</div><figcaption><b>s {r[1]:.0f} m</b> "
        + ("(second picture: your strokes as you drew them, thin bright red / green, over the haloed fit) " if r[10] else "")
        + f"({'close-up, ' if r[0] == 'close' else ''}{2 * r[2]:.0f} m across at {r[3]} m/px; stations {r[8]:.0f}-{r[9]:.0f} m): {e(r[5])}; "
        f"width here {r[6]:.2f} m (before {r[11]:.2f} m), window median {r[7]:.2f} m (before {r[12]:.2f} m), range {r[13]:.2f}-{r[14]:.2f} m "
        f"(before {r[15]:.2f}-{r[16]:.2f} m)</figcaption></figure>" for r in rows)
    b = wr['bias'] if wr else None; ak = wr['at_kerb'] if wr else None
    intro = open(a.intro).read() if a.intro else f"""<p>The new fitted edges (white) over the clean 2026 captures, station ticks every 10 m (yellow, labels every 50 m), the whole lap
every {a.every:.0f} m in windows {2 * a.half:.0f} m across at {a.mpp} m/px, then close-ups of your three crops. Model: kerb bands anchor the edge at
their inside line; the asphalt-end detector's outward bias, measured through the kerb anchors, is removed (left {b['left']:+.2f} m, right
{b['right']:+.2f} m; at the kerb stations themselves the detector reads the band, {ak['left'][1]:+.2f} / {ak['right'][1]:+.2f} m from its inside line);
one width per section between the junctions; the weaker side placed at that width from the stronger. Lap {L:.2f} m (before {T0['n'] * T0['spacing_m']:.2f} m).</p>"""
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(a.title)}</title>
<style>:root{{--bg:#fff;--fg:#111;--line:#bbb;--frame:#888}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#16181c;--fg:#e8e8e8;--line:#555;--frame:#666}}}}
:root[data-theme="dark"]{{--bg:#16181c;--fg:#e8e8e8;--line:#555;--frame:#666}}
body{{font:15px/1.45 system-ui,sans-serif;margin:16px;max-width:1300px;background:var(--bg);color:var(--fg)}}img{{max-width:100%;height:auto;border:1px solid var(--frame)}}
figure{{margin:0 0 22px}}figcaption{{font-size:14px}}table{{border-collapse:collapse;font-size:14px;display:block;overflow-x:auto}}td,th{{border:1px solid var(--line);padding:2px 6px;text-align:right}}
pre{{white-space:pre-wrap;font-size:13px}}.pair{{display:flex;gap:8px;flex-wrap:wrap}}.pair img{{flex:1 1 300px;min-width:0}}</style></head><body>
<h1>{e(a.title)}: {e(cfg['name'])}</h1>
{intro}
<h2>{'Width gates' if wr else "Owner-reference gates (where your red is drawn)"}</h2><pre>before ({e(a.before_label)}):
{e(chr(10).join(lines0))}
after:
{e(chr(10).join(lines1))}</pre>
<h2>Width per section{' (between the junctions)' if wr else ' (per window)'}</h2>
<table><tr><th>stations (m)</th><th>before: median width</th><th>before: {'max deviation' if wr else 'range'}</th><th>after: width</th><th>after: {'max deviation' if wr else 'range'}</th><th>observations</th><th>kinds (K kerb, D detector; left+right)</th></tr>
{''.join(sec_rows)}</table>
{open(a.extra).read() if a.extra else ""}
{'<h2>Junction ranges (measured local width, blended into the sections)</h2><ul>' + j_rows + '</ul>' if J else ''}
<h2>Windows in lap order</h2>
{win_rows}
</body></html>
"""
    open(os.path.join(a.out, 'index.html'), 'w').write(doc)
    print(f"{len(rows)} windows -> {a.out}/index.html")


if __name__ == '__main__':
    main()
