"""Mid-Ohio round 3, the nominal-length question: lengths of the OSM loop (raw node polyline), the built centre and each
edge, per section between corners (OSM vs built centre, sections cut at the built corners' stations projected on OSM),
and the OSM chicane variant against the straight option it replaces (the official 2.400 mi vs 2.258 mi difference).
Reads the cached OSM XML and a package; prints, writes nothing."""
import argparse, json, math, os, sys
import xml.etree.ElementTree as ET
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import trackcfg  # noqa
ap = argparse.ArgumentParser(); ap.add_argument('--pkg', default='tools/track/out/mid_ohio_r3'); a = ap.parse_args()
cfg = trackcfg.load('mid_ohio')
r = ET.parse(os.path.join(ROOT, 'tools/track/cache/mid_ohio/osm/osm.xml')).getroot()
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in r.iter('node')}
ways = {w.get('id'): [nd.get('ref') for nd in w.iter('nd')] for w in r.iter('way')}
enu = lambda ids: np.array([cfg.enu(*nodes[i]) for i in ids])  # noqa
plen = lambda P: float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())  # noqa
# the loop, stitched by shared end nodes as geo.osm_loop does
by_start = {ways[w][0]: w for w in cfg['loop_ways']}
seq, wid = [], cfg['loop_ways'][0]
for _ in cfg['loop_ways']:
    seq += ways[wid][:-1]; wid = by_start[ways[wid][-1]]
P = enu(seq + [seq[0]])
print(f"OSM loop (raw node polyline, {len(seq)} nodes): {plen(P):.1f} m")
for wid in cfg['loop_ways'] + ['444205376', '444205377', '444205378']:
    print(f"  way {wid}: {plen(enu(ways[wid])):.1f} m, ends {ways[wid][0]} -> {ways[wid][-1]}")
# the chicane variant: way 444205376 from node 4416919184 (on way 1315957513) to 4416919596 (the Keyhole's start)
w13 = ways['1315957513']
if '4416919184' in w13:
    i = w13.index('4416919184')
    straight = plen(enu(w13[i:])) + plen(enu(ways['1315957512']))
    chic = plen(enu(ways['444205376']))
    print(f"straight option (1315957513 from 4416919184 + 1315957512): {straight:.1f} m; chicane 444205376: {chic:.1f} m; "
          f"difference {chic - straight:.1f} m (official 2.400 - 2.258 mi = {0.142 * 1609.344:.1f} m)")
T = json.load(open(os.path.join(ROOT, a.pkg, 'track.json')))
C = np.array(T['center'])[:, :2]; Lf = np.array(T['left'])[:, :2]; Rt = np.array(T['right'])[:, :2]
cl = lambda Q: plen(np.r_[Q, Q[:1]])  # noqa
print(f"built centre {cl(C):.1f} m, left edge {cl(Lf):.1f} m, right edge {cl(Rt):.1f} m, mean of edges {(cl(Lf) + cl(Rt)) / 2:.1f} m; "
      f"official 2.258 mi = {2.258 * 1609.344:.1f} m")
# per section: corners of the built package, projected on the densified OSM loop
from scipy.spatial import cKDTree
seg = np.linalg.norm(np.diff(P, axis=0), axis=1); m = np.maximum(1, np.ceil(seg / 0.5)).astype(int)
D = np.concatenate([P[k] + np.diff(P, axis=0)[k] * (np.arange(m[k])[:, None] / m[k]) for k in range(len(seg))])
sD = np.r_[0, np.cumsum(np.linalg.norm(np.diff(D, axis=0), axis=1))]
sp = T['spacing_m']; n = T['n']
cs = [(c.get('turn') or c.get('name'), c['s']) for c in T['corners']]
cuts = [('S/F', 0.0)] + cs
kd = cKDTree(D)
s0 = sD[kd.query(C[0])[1]]
Ltot = sD[-1] + np.linalg.norm(D[-1] - D[0])
print(f"| section | built centre (m) | OSM (m) | built - OSM (m) |\n|---|---|---|---|")
tot = 0
for (na, sa), (nb, sb) in zip(cuts, cuts[1:] + [('S/F', T['length_m'])]):
    ka, kb = int(round(sa / sp)) % n, int(round(sb / sp)) % n
    oa = (sD[kd.query(C[ka])[1]] - s0) % Ltot; ob = (sD[kd.query(C[kb])[1]] - s0) % Ltot
    if nb == 'S/F' and sb > 0:
        ob = Ltot
    b_ = sb - sa; o_ = (ob - oa) % Ltot if nb != 'S/F' else ob - oa
    tot += b_ - o_
    print(f"| {na} -> {nb} | {b_:.1f} | {o_:.1f} | {b_ - o_:+.1f} |")
print(f"sum of section differences {tot:+.1f} m")
