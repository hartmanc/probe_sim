"""Side-by-side sheets for the IMSA YouTube onboard (8fGzs8Lnn0Q) vs the sim hood camera.

    uv run --python 3.12 --with pillow python -I tools/track/compare/make_youtube_sheets.py SIM_DIR [tag]

The 'before' sheets used s = 3480, 200, 440, 750, 1045, 1540, 1930, 2150, 2350, 2430, 2480, 2700, 2930, 3230 (sim dir youtube_sim). Round 5 (v6) stations are aligned by landmarks, with lateral offsets
(left +): T1 0, T2 +2, T3 +3, T4 +3, T5 +3, T6 +3, T7 -4, T8 +3, T8A -2, T9 +3, T10 -3, T11 +2.

youtube/<name>.png: reference frames (private, not textures). youtube_sim/<name>.jpg: sim hood camera at the
station in STATIONS. Output: youtube_sheets/<name>[_tag].jpg (onboard left, sim right) and an overview contact sheet.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SIMDIR = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else ''
# name: (video t s, track s m)
STATIONS = {
    'front_straight': (92.4, 3450), 'T1': (13.6, 180), 'T2_Andretti': (19.5, 450), 'T3': (27.2, 765),
    'T4': (34.5, 1030), 'T5': (45.5, 1545), 'T6': (54.5, 1940), 'Rahal_straight': (59.0, 2130), 'T7': (62.8, 2365),
    'T8_Corkscrew_entry': (65.0, 2452), 'T8A': (66.6, 2485), 'T9_Rainey': (72.5, 2708), 'T10': (78.0, 2955),
    'T11': (85.0, 3230),
}
W, H = 760, 427
font = ImageFont.load_default()
out = os.path.join(HERE, 'youtube_sheets'); os.makedirs(out, exist_ok=True)
pairs = []
for nm, (t, s) in STATIONS.items():
    ob = Image.open(os.path.join(HERE, 'youtube', nm + '.png')).convert('RGB').resize((W, H))
    sm = Image.open(os.path.join(HERE, SIMDIR, nm + '.jpg')).convert('RGB')
    sm = sm.resize((W, round(W * sm.height / sm.width)))
    sm = sm.crop((0, (sm.height - H) // 2, W, (sm.height - H) // 2 + H)) if sm.height > H else sm
    sheet = Image.new('RGB', (2 * W + 10, H + 22), (20, 20, 20))
    sheet.paste(ob, (0, 22)); sheet.paste(sm, (W + 10, 22))
    d = ImageDraw.Draw(sheet)
    d.text((4, 5), f'{nm}  ONBOARD (YouTube 8fGzs8Lnn0Q t={t}s, hood cam)', fill=(255, 255, 255), font=font)
    d.text((W + 14, 5), f'SIM hood camera, track s={s} m {TAG}', fill=(255, 255, 255), font=font)
    p = os.path.join(out, nm + (('_' + TAG) if TAG else '') + '.jpg')
    sheet.save(p, quality=85); pairs.append(sheet)
print('wrote', len(pairs), 'sheets to', out)
