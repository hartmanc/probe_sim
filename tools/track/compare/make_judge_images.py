"""Judge inputs: judge/<place>.jpg (onboard sheet over the matching top-down tile sheet) and judge/lap_1..4.jpg.
    uv run --python 3.12 --with pillow python -I tools/track/compare/make_judge_images.py TAG
"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE); TAG = sys.argv[1]
M = {'front_straight': 's3400-3570', 'T1': 's0170-0340', 'T2_Andretti': 's0340-0510', 'T3': 's0680-0850', 'T4': 's1020-1190',
     'T5': 's1530-1700', 'T6': 's1870-2040', 'Rahal_straight': 's2040-2210', 'T7': 's2210-2380', 'T8_Corkscrew_entry': 's2380-2550',
     'T8A': 's2380-2550', 'T9_Rainey': 's2720-2890', 'T10': 's2890-3060', 'T11': 's3230-3400'}
for k, t in M.items():
    a = Image.open(f'youtube_sheets/{k}_{TAG}.jpg'); b = Image.open(f'satellite_sheets/{t}_{TAG}.jpg').resize((a.width, round(545 * a.width / 2010)))
    o = Image.new('RGB', (a.width, a.height + b.height + 20), (20, 20, 20)); o.paste(a, (0, 0)); o.paste(b, (0, a.height + 20))
    ImageDraw.Draw(o).text((4, a.height + 5), f'{k}: TOP-DOWN tile {t} (left Google satellite, right sim)', fill=(255, 255, 0))
    o.save(f'judge/{k}.jpg', quality=82)
tiles = [x['name'] for x in json.load(open('satellite/tiles.json'))]
for k in range(0, 21, 6):
    ns = tiles[k:k + 6]; o = Image.new('RGB', (1610, len(ns) * 437))
    for i, n in enumerate(ns): o.paste(Image.open(f'satellite_sheets/{n}_{TAG}.jpg').resize((1610, 437)), (0, i * 437))
    o.save(f'judge/lap_{k // 6 + 1}.jpg', quality=80)
print('ok')
