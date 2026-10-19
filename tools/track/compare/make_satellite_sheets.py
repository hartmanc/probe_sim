"""Top-down sheets: Google Maps satellite tile (left) | sim top-down render (right), same centre, north-up, same scale
(Google z19 = 0.2398 m per CSS px, 1710x895 viewport, ~410 x 215 m).

    uv run --python 3.12 --with pillow python -I tools/track/compare/make_satellite_sheets.py SIM_DIR [tag]

satellite/<tile>_google.jpg: reference captures (private, never textures). SIM_DIR/td_<tile>.jpg: sim renders from the
app with a temporary top-down camera (fov 20 deg, altitude 608 m over the tile centre). Writes satellite/<tile>_sim[_tag].jpg
and satellite_sheets/<tile>[_tag].jpg.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else ''
sat = os.path.join(HERE, 'satellite'); out = os.path.join(HERE, 'satellite_sheets'); os.makedirs(out, exist_ok=True)
font = ImageFont.load_default()
W, H = 1000, 523
for t in json.load(open(os.path.join(sat, 'tiles.json'))):
    nm = t['name']
    g = Image.open(os.path.join(sat, nm + '_google.jpg')).convert('RGB').resize((W, H))
    s = Image.open(os.path.join(SIM, 'td_' + nm + '.jpg')).convert('RGB')
    s.resize((1210, 633)).save(os.path.join(sat, nm + '_sim' + (('_' + TAG) if TAG else '') + '.jpg'), quality=85)
    s = s.resize((W, H))
    sh = Image.new('RGB', (2 * W + 10, H + 22), (20, 20, 20)); sh.paste(g, (0, 22)); sh.paste(s, (W + 10, 22))
    d = ImageDraw.Draw(sh)
    d.text((4, 5), f'{nm}  GOOGLE MAPS satellite, north up, centre = track s {t["c"]} ({t["lat"]}, {t["lon"]})', fill=(255, 255, 255), font=font)
    d.text((W + 14, 5), f'SIM top-down, same centre and scale {TAG}', fill=(255, 255, 255), font=font)
    sh.save(os.path.join(out, nm + (('_' + TAG) if TAG else '') + '.jpg'), quality=85)
print('ok')
