"""Side-by-side sheets tools/track/compare/<corner>.jpg: onboard windscreen crop (left) | sim driver camera (right).

    uv run --python 3.12 --with pillow python tools/track/compare/make_sheets.py
"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sel = json.load(open(os.path.join(HERE, 'selected.json')))
GROUPS = {
    'T1': ['T1_approach', 'T1_apex', 'T1_exit'], 'T2': ['T2_approach', 'T2_apex', 'T2_exit'],
    'T3': ['T3_approach', 'T3_apex', 'T3_exit'], 'T4': ['T4_approach', 'T4_apex', 'T4_exit'],
    'T5': ['T5_approach', 'T5_apex', 'T5_exit'], 'T6': ['T6_approach', 'T6_apex', 'T6_exit'],
    'Rahal_straight': ['Rahal_Straight_approach', 'Rahal_Straight_apex', 'Rahal_Straight_exit'],
    'T7': ['T7_approach', 'T7_apex', 'T7_exit'], 'Corkscrew_T8_T8A': ['T8_approach', 'T8_apex', 'T8A_apex', 'T8A_exit'],
    'T9_Rainey': ['T9_approach', 'T9_apex', 'T9_exit'], 'T10': ['T10_approach', 'T10_apex', 'T10_exit'],
    'T11': ['T11_approach', 'T11_apex', 'T11_exit'],
    'front_straight': ['front_straight_approach', 'front_straight_bridge', 'front_straight_exit'],
    'pit_exit': ['pit_lane_bridge', 'pit_exit_alongside', 'pit_exit_merge'],
}
W, H = 800, 200
font = ImageFont.load_default()
for g, names in GROUPS.items():
    sheet = Image.new('RGB', (2 * W + 10, len(names) * (H + 22)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for r, nm in enumerate(names):
        y = r * (H + 22)
        ob = os.path.join(HERE, 'onboard', nm + '.jpg')
        sm = os.path.join(HERE, 'sim', nm + '.jpg')
        if os.path.exists(ob):
            sheet.paste(Image.open(ob).resize((W, H)), (0, y + 20))
        if os.path.exists(sm):
            im = Image.open(sm)
            im = im.crop((0, 140, 1920, 620)).resize((W, H))
            sheet.paste(im, (W + 10, y + 20))
        s = sel.get(nm, {})
        d.text((4, y + 4), f"{nm}  onboard {s.get('file', '')} t={s.get('t', '')} s  (track s={s.get('s', '')})", fill=(255, 255, 255), font=font)
        d.text((W + 14, y + 4), 'sim, driver camera, same s and heading', fill=(255, 255, 255), font=font)
    sheet.save(os.path.join(HERE, g + '.jpg'), quality=85)
    print('wrote', g)
