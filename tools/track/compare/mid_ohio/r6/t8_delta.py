"""Mid-Ohio round 6, T8 (c): the N837 session-best pace through the crest, T8 and T9, from the Catalyst overlay's DELTA
to its session best (1:53.71) read every 1 s from the local frames t084-t097 (by eye, recorded below), with lap 149's
speed-integrated positions (r6/t8_times.py). Over a section that lap 149 covers in dt seconds, delta grows by dd, so the
best lap covers it in dt - dd: its average speed = distance / (dt - dd). The result is set beside the race AI's profile
(r6/ai_profile_t8.json) averaged over the same stations.

    python3 -I tools/track/compare/mid_ohio/r6/t8_delta.py <out.json>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
# delta readout (s) per frame, read from inventory/frames_n837/t0NN.jpg (reference only)
DELTA = {84: 5.89, 85: 5.90, 86: 5.91, 87: 5.94, 88: 6.03, 89: 6.21, 90: 6.47, 91: 6.66, 92: 6.83, 93: 7.08, 94: 7.29,
         95: 7.43, 96: 7.54, 97: 7.62}
# lap 149 position at each frame: Catalyst speed integrated from the T7 anchor (t 83.8, s 2386.7); r6/t8_times.py
S149 = {84: 2392.2, 85: 2420.6, 86: 2450.4, 87: 2481.2, 88: 2511.6, 89: 2539.3, 90: 2564.1, 91: 2588.7, 92: 2612.1,
        93: 2632.7, 94: 2652.4, 95: 2672.7}
AI = {r['s']: r for r in json.load(open(os.path.join(HERE, 'ai_profile_t8.json')))['rows']}


def ai_avg(a, b, key='v_ai_kmh'):
    ss = [s for s in AI if a <= s <= b]
    # time-average: distance over the sum of time per 10 m
    t = sum(10 / (AI[s][key] / 3.6) for s in ss)
    return round(len(ss) * 10 / t * 3.6, 1)


secs = [('crest (T7 exit to the brow)', 84, 87), ('T8 (after the crest to the exit kerb)', 87, 91), ('T9', 91, 95)]
rows = []
for name, t0, t1 in secs:
    dist = S149[t1] - S149[t0]; dt = t1 - t0; dd = DELTA[t1] - DELTA[t0]
    v149 = dist / dt * 3.6; vbest = dist / (dt - dd) * 3.6
    rows.append(dict(section=name, frames=f't{t0:03d}-t{t1:03d}', s=[S149[t0], S149[t1]], distance_m=round(dist, 1), lap149_s=dt,
                     delta_gain_s=round(dd, 2), best_s=round(dt - dd, 2), lap149_avg_kmh=round(v149, 1), best_avg_kmh=round(vbest, 1),
                     ai_profile_avg_kmh=ai_avg(S149[t0], S149[t1]), best_over_ai=round(vbest / ai_avg(S149[t0], S149[t1]), 3)))
out = dict(source='N837 Catalyst overlay DELTA to the session best, frames t084-t097 (read by eye, 0.01 s); lap 149 positions '
                  'speed-integrated from the T7 anchor (1.6 m off at T9)', delta=DELTA, positions=S149, sections=rows,
           caveat='section averages only: the 1 s frames and the 0.01 s readout give about +-0.02 s per reading, +-3 % on a 3 s '
                  'section; the session best is the same car on the same day, not a Probe')
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for r in rows:
    print(r)
