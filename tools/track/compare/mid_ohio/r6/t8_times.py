"""Mid-Ohio round 6, T8: the video time of each T8 station on every time map (N837, 360 lap, IndyCar A) and the N837
position by speed integration between its T7 and T9 anchors (Catalyst 1 Hz readings, r4/speed_lap_n837.json).

    python3 -I tools/track/compare/mid_ohio/r6/t8_times.py <package dir>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'track', 'inventory'))
import inventory as INV  # noqa: E402

pkg = sys.argv[1]
T = json.load(open(os.path.join(pkg, 'track.json')))
L = T['n'] * T['spacing_m']
src = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory/source.json')))
prof = INV.speed_profile(T)
a, _ = INV.anchors_from(src, T)
maps = {'N837': INV.TimeMap(a, L, prof, T['spacing_m'])}
for m in src['extra_maps']:
    if m['name'].startswith('360') or 'segment A' in m['name']:
        q, _ = INV.anchors_from(m, T)
        maps[m['name'][:20]] = INV.TimeMap(q, L, prof, T['spacing_m'], strict=True)
for s in range(2420, 2681, 20):
    print(s, '  '.join(f"{k}: t {tm.t(s + L if k != 'N837' else s):6.2f}" for k, tm in maps.items()))
# N837 by speed integration: Catalyst mph at ~1 Hz; position from the T7 anchor (t 83.8, s 2386.7)
lap = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/r4/speed_lap_n837.json')))
rows = [r for r in lap['rows'] if r['reading'] is not None and 82 <= r['t'] <= 96]
MS = 0.44704
t7, s7 = 83.8, 2386.7
import bisect
ts = [r['t'] for r in rows]; vs = [r['reading'] * MS for r in rows]
def v_at(t):
    i = bisect.bisect_left(ts, t)
    if i <= 0: return vs[0]
    if i >= len(ts): return vs[-1]
    f = (t - ts[i - 1]) / (ts[i] - ts[i - 1]); return vs[i - 1] + f * (vs[i] - vs[i - 1])
s, t, dt = s7, t7, 0.01
out = {}
while t < 95.5:
    s += v_at(t) * dt; t += dt
    for tf in range(84, 96):
        if abs(t - tf) < dt / 2: out[tf] = s
for tf in sorted(out):
    print(f"N837 t{tf:03d}: speed-integrated s {out[tf]:.1f} (time map {maps['N837'].s(tf):.1f}), {v_at(tf) / MS:.0f} mph = {v_at(tf) * 3.6:.1f} km/h")
print('T9 anchor check: integrated s at t 93.43 =', round(s7 + sum(v_at(t7 + k * dt) * dt for k in range(int((93.43 - t7) / dt))), 1), '(anchor 2642.8)')
