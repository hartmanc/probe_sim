"""Mid-Ohio round 10 sheets: each sim still of compare_sheets_r10/sim (shot from the published package) beside the reference
frame at the same station (360 lap Jul 2025 views, the IndyCar onboard Jul 2026, N837 Apr 2026; time maps in inventory.json).
Reference frames are local and never committed.
    uv run --python 3.12 --with pillow python -I make_sheets_r10.py <compare_sheets_r10 dir>"""
import os, sys
from PIL import Image, ImageDraw
D = sys.argv[1]; INV = os.path.join(D, '..', 'inventory')
def ref(kind, f): return os.path.join(INV, {'360': 'frames_360', 'indy': 'frames_indy', 'n837': 'frames_n837'}[kind], f)
SHEETS = {
 'sheet_owner_spot_r10': [('owner_t1_keyhole_right_s440', '360', 't036_right.jpg', 's 440 right | 360 lap t36 right'),
                           ('owner_t1_keyhole_right_s520', '360', 't038_right.jpg', 's 520 right | 360 lap t38 right'),
                           ('owner_t1_keyhole_right_s600', '360', 't040_right.jpg', 's 600 right | 360 lap t40 right'),
                           ('owner_t1_keyhole_fwd_s500', 'indy', 't038.jpg', 's 500 ahead | IndyCar t38'),
                           ('owner_t1_keyhole_fwd_s500_y25', 'n837', 't021.jpg', 's 500 ahead-right 25 deg | N837 t21')],
 'sheet_back_straight_r10': [('back_straight_left_s1560', '360', 't066_left.jpg', 's 1560 left | 360 t66 left'),
                             ('back_straight_right_s1560', '360', 't066_right.jpg', 's 1560 right | 360 t66 right'),
                             ('back_straight_left_s1700', '360', 't070_left.jpg', 's 1700 left | 360 t70 left'),
                             ('back_straight_right_s1700', '360', 't070_right.jpg', 's 1700 right | 360 t70 right')],
 'sheet_thunder_valley_r10': [('thunder_valley_left_s2760', '360', 't104_left.jpg', 's 2760 left | 360 t104 left'),
                              ('thunder_valley_right_s2760', '360', 't104_right.jpg', 's 2760 right | 360 t104 right'),
                              ('thunder_valley_left_s2950', '360', 't110_left.jpg', 's 2950 left | 360 t110 left'),
                              ('thunder_valley_right_s2950', '360', 't110_right.jpg', 's 2950 right | 360 t110 right')],
 'sheet_pit_straight_r10': [('pit_straight_left_s3540', '360', 't130_left.jpg', 's 3540 left | 360 t130 left'),
                            ('pit_straight_right_s3540', '360', 't130_right.jpg', 's 3540 right | 360 t130 right'),
                            ('pit_straight_left_s60', '360', 't026_left.jpg', 's 60 left | 360 t26 left'),
                            ('pit_straight_right_s60', '360', 't026_right.jpg', 's 60 right | 360 t26 right')],
 'sheet_china_beach_r10': [('china_beach_braking_s1880', '360', 't074_left.jpg', 's 1880 left 45 deg | 360 t74 left'),
                           ('china_beach_braking_s1920', '360', 't076_left.jpg', 's 1920 left 60 deg | 360 t76 left'),
                           ('china_beach_braking_s1950', '360', 't078_left.jpg', 's 1950 left 75 deg | 360 t78 left'),
                           ('china_beach_braking_s1975', 'n837', 't066.jpg', 's 1975 left 85 deg | N837 t66')],
}
for name, rows in SHEETS.items():
    W = 640; H = 360; M = Image.new('RGB', (2 * W, len(rows) * (H + 18)), (20, 20, 20)); dr = ImageDraw.Draw(M)
    for k, (sim, kind, f, cap) in enumerate(rows):
        y = k * (H + 18)
        a = Image.open(os.path.join(D, 'sim', sim + '.jpg')).convert('RGB').resize((W, H)); M.paste(a, (0, y + 18))
        b = Image.open(ref(kind, f)).convert('RGB').resize((W, H)); M.paste(b, (W, y + 18))
        dr.text((6, y + 3), 'sim (published package): ' + cap, fill=(230, 230, 230))
    M.save(os.path.join(D, name + '.jpg'), quality=86)
    print(name, len(rows))
