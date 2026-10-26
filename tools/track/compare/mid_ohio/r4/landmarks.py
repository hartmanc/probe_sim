"""Mid-Ohio round 4: lap stations of the time-map landmarks on a package (default tools/track/out/mid_ohio_r4), from
evidence with a world position: the timing line (s 0 / L), the config's footbridge point, the package corners, the
OSM bridge=yes ways crossing the loop (nearest crossing point), the OSM pit lane's ends (lap station abeam), and the
profile's low point between T9 and T11 and its summit between T11 and T12 (Thunder Valley crest). Prints JSON."""
import argparse, json, os, sys
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import trackcfg  # noqa
ap = argparse.ArgumentParser(); ap.add_argument('--pkg', default='tools/track/out/mid_ohio_r4'); a = ap.parse_args()
cfg = trackcfg.load('mid_ohio')
T = json.load(open(os.path.join(ROOT, a.pkg, 'track.json')))
C = np.array(T['center'])[:, :2]; sp = T['spacing_m']; L = T['length_m']; z = np.array(T['profile']['z'])[:, 3]
kd = cKDTree(C)
def s_of(xy):  # noqa
    d, i = kd.query(xy); return round(float(i * sp), 1), round(float(d), 1)
out = {'length_m': L, 'S/F': 0.0}
out['footbridge (config profile_gaps latlon)'] = s_of(cfg.enu(*cfg['profile_gaps'][0]['latlon']))[0]
for c in T['corners']:
    out[c['turn'] or c['name']] = c['s']
r = ET.parse(os.path.join(ROOT, 'tools/track/cache/mid_ohio/osm/osm.xml')).getroot()
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in r.iter('node')}
for w in r.iter('way'):
    tg = {t.get('k'): t.get('v') for t in w.iter('tag')}
    P = np.array([cfg.enu(*nodes[n.get('ref')]) for n in w.iter('nd') if n.get('ref') in nodes])
    if len(P) < 2:
        continue
    if tg.get('bridge') == 'yes':
        # densify, take the point nearest the centre
        D = np.concatenate([np.linspace(P[k], P[k + 1], 50) for k in range(len(P) - 1)])
        d, i = kd.query(D); k = int(np.argmin(d))
        if d[k] < 8:
            out[f"OSM bridge way {w.get('id')} ({tg.get('highway') or tg.get('man_made') or tg.get('name', '')})"] = round(float(i[k] * sp), 1)
    if tg.get('name') == cfg['pit_lane_way'] or tg.get('highway') == 'raceway' and 'pit' in (tg.get('name', '') + tg.get('service', '')).lower():
        out[f"pit lane way {w.get('id')} first node abeam"] = s_of(P[0])[0]
        out[f"pit lane way {w.get('id')} last node abeam"] = s_of(P[-1])[0]
k9, k11, k12 = (int(c['s'] / sp) for c in T['corners'] if c['turn'] in ('T9', 'T11', 'T12'))
seg = np.arange(k9, k11 + 1)
out['Thunder Valley low point (profile min T9..T11)'] = round(float(seg[np.argmin(z[seg])] * sp), 1)
seg = np.arange(k11, k12 + 1)
out['Thunder Valley crest (profile max T11..T12)'] = round(float(seg[np.argmax(z[seg])] * sp), 1)
print(json.dumps(out, indent=1))
