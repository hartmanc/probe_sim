"""Pose file for camera_walk.ts --replay: python3 mkwalk.py <track.json> <out.json> name:s:lateral_m:yaw_deg ...
lateral is metres left of the centre line (negative = right); yaw +left, 0 = along the lap; s>0, a suffix 'b' on the yaw = facing back."""
import json, math, sys
t = json.load(open(sys.argv[1])); n = t['n']; sp = t['spacing_m']; shots = []
for a in sys.argv[3:]:
    name, s, lat, yaw = a.split(':'); s = float(s); lat = float(lat); back = yaw.endswith('b'); yaw = float(yaw.rstrip('b'))
    i = int(round(s / sp)) % n; A = t['center'][(i - 2) % n]; B = t['center'][(i + 2) % n]; C = t['center'][i]
    h = math.atan2(B[1] - A[1], B[0] - A[0])
    x = C[0] - math.sin(h) * lat; y = C[1] + math.cos(h) * lat
    shots.append(dict(file=f'sim/{name}.jpg', s=s, side='fwd' if yaw == 0 else ('left' if yaw > 0 else 'right'), pos=[round(x, 3), round(y, 3), None],
                      heading=h + (math.pi if back else 0), yaw=math.radians(yaw)))
json.dump(dict(track='mid_ohio', shots=shots), open(sys.argv[2], 'w'))
