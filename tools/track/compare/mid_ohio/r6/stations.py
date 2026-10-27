"""Mid-Ohio round 6, hood sheet stations (build-track SKILL 1.10 driver's-eye sheet): every corner's entry, apex and
exit and the four longest straights' midpoints on the local package, with the N837 (Apr 2026 hood camera) and the 2025
360 lap (pace-car roof, 'ahead' view) source frames at the same station from the inventory's time maps.

    python3 -I tools/track/compare/mid_ohio/r6/stations.py <package dir> <out frames.json>

Apex = the package corner's s (track.json corners, the pipeline's curvature peak). Entry / exit = the stations either
side where the centre's curvature (circle through the points 10 m either side) falls below half the corner's peak,
clamped to 20-80 m from the apex (a long arc like T3 or Thunder Valley would otherwise run into the next corner).
Straights: the four longest corner-to-corner runs (exit of one corner to entry of the next), at their midpoint.
Frames: the nearest extracted frame to the map's time (N837 every 1 s: frames_n837/t###.jpg; 360 lap every 0.5 s:
frames_360_half/h####_ahead.jpg, k = 2 t); the station of that frame is given too (the frame's own position on the
map), and sigma = the map's bracketing leave-one-out residual (inventory.py sigma_at).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'track', 'inventory'))
import inventory as INV  # noqa: E402

pkg, out = sys.argv[1:3]
T = json.load(open(os.path.join(pkg, 'track.json')))
C = T['center']; n = len(C); sp = T['spacing_m']; L = n * sp
IDIR = os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory')
src = json.load(open(os.path.join(IDIR, 'source.json')))
prof = INV.speed_profile(T)
anchors, _ = INV.anchors_from(src, T)
tm = INV.TimeMap(anchors, L, prof, sp)
m360 = next(m for m in src['extra_maps'] if m['name'].startswith('360'))
a360, _ = INV.anchors_from(m360, T)
tm360 = INV.TimeMap(a360, L, prof, sp, strict=True)
res = {'primary': max(abs(r['loo_residual_m']) for r in tm.residuals()),
       '360': max(abs(r['loo_residual_m']) for r in tm360.residuals())}


def kappa(i, h=10):
    a, b, c = C[(i - h) % n], C[i % n], C[(i + h) % n]
    ab = math.hypot(b[0] - a[0], b[1] - a[1]); bc = math.hypot(c[0] - b[0], c[1] - b[1]); ac = math.hypot(c[0] - a[0], c[1] - a[1])
    cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 2 * cr / max(ab * bc * ac, 1e-9)


K = [kappa(i) for i in range(n)]
corners = sorted(T['corners'], key=lambda c: c['s'])
phases = []
for c in corners:
    i0 = int(round(c['s'] / sp)) % n
    pk = max(abs(K[(i0 + d) % n]) for d in range(-5, 6))
    def walk(sign):
        for d in range(1, 200):
            if abs(K[(i0 + sign * d) % n]) < 0.5 * pk:
                return d * sp
        return 200 * sp
    de, dx = min(max(walk(-1), 20), 80), min(max(walk(+1), 20), 80)
    phases.append(dict(corner=c['turn'], name=c['name'], radius_m=c['radius_m'], dir=c['dir'], apex=c['s'],
                       entry=(c['s'] - de) % L, exit=(c['s'] + dx) % L))
runs = []
for k, p in enumerate(phases):
    q = phases[(k + 1) % len(phases)]
    a, b = p['exit'], q['entry']
    length = (b - a) % L
    runs.append(dict(after=p['corner'], before=q['corner'], a=a, b=b, length=length, mid=(a + length / 2) % L))
straights = sorted(sorted(runs, key=lambda r: -r['length'])[:4], key=lambda r: r['mid'])


def n837(s):
    t = tm.t(s)
    tf = int(round(t))
    f = f't{tf:03d}.jpg'
    if not os.path.exists(os.path.join(IDIR, 'frames_n837', f)):   # t061 is missing: the next frame
        for d in (1, -1, 2, -2):
            if os.path.exists(os.path.join(IDIR, 'frames_n837', f't{tf + d:03d}.jpg')):
                tf += d; f = f't{tf:03d}.jpg'; break
    return dict(t_map=round(t, 2), t=tf, frame=f'frames_n837/{f}', s_frame=round(tm.s(tf) % L, 1),
                sigma_m=INV.sigma_at(tm, t), placement='direct' if res['primary'] <= 40 else 'corroborate')


def v360(s):
    s2 = s + L                                  # the lap between the two S/F crossings: s + L covers 3351 .. 7195
    if s2 > a360[-1]['s']:
        s2 -= L
    t = tm360.t(s2)
    k = int(round(t * 2))
    f = f'h{k:04d}_ahead.jpg'
    return dict(t_map=round(t, 2), t=k / 2, frame=f'frames_360_half/{f}', s_frame=round(tm360.s(k / 2) % L, 1),
                sigma_m=INV.sigma_at(tm360, t), placement='direct' if res['360'] <= 40 else 'corroborate',
                exists=os.path.exists(os.path.join(IDIR, 'frames_360_half', f)))


sheets = []
for p in phases:
    for ph in ('entry', 'apex', 'exit'):
        s = p[ph]
        sheets.append(dict(corner=p['corner'], name=p['name'], phase=ph, s=round(s, 1), radius_m=p['radius_m'], dir=p['dir'],
                           n837=n837(s), v360=v360(s)))
for r in straights:
    sheets.append(dict(corner=f"{r['after']}-{r['before']}", name=f"straight {r['after']} -> {r['before']}", phase='mid',
                       s=round(r['mid'], 1), length_m=round(r['length'], 1), n837=n837(r['mid']), v360=v360(r['mid'])))
# order: T8 first, then T4, then the rest in driving order from S/F
def key(sh):
    pri = 0 if sh['corner'] == 'T8' else 1 if sh['corner'] == 'T4' else 2
    return (pri, sh['s'] if pri == 2 else {'entry': 0, 'apex': 1, 'exit': 2}[sh['phase']])
sheets.sort(key=key)
for k, sh in enumerate(sheets, 1):
    tag = sh['corner'] if sh['phase'] == 'mid' else f"{sh['corner']}_{sh['phase']}"
    sh['id'] = f"sheet_{k:02d}_{tag.replace('-', '_')}"
json.dump(dict(track='mid_ohio', package=os.path.relpath(pkg, ROOT), length_m=L, time_maps=dict(
    n837=dict(video='OJaBJz18xEo', max_loo_residual_m=res['primary'], placement='direct' if res['primary'] <= 40 else 'corroborate'),
    v360=dict(video='e25u_vjn1uM', max_loo_residual_m=res['360'], placement='direct' if res['360'] <= 40 else 'corroborate')),
    phases=phases, straights=straights, sheets=sheets), open(out, 'w'), indent=1)
for sh in sheets:
    print(f"{sh['id']:28s} s {sh['s']:7.1f}  n837 {sh['n837']['frame']} (s {sh['n837']['s_frame']}, sig {sh['n837']['sigma_m']})"
          f"  360 {sh['v360']['frame']} (s {sh['v360']['s_frame']}) {'' if sh['v360']['exists'] else 'MISSING'}")
