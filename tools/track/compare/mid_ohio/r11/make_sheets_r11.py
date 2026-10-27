"""Mid-Ohio round 11 sheets: each pose shot from the round-10 package (left) and the round-11 package (right), same hood camera.
    uv run --python 3.12 --with pillow python -I make_sheets_r11.py <compare_sheets_r11 dir>"""
import os, sys
from PIL import Image, ImageDraw
D = sys.argv[1]
SHEETS = {
 'sheet_owner_spot_r11': [('owner_fwd_s440', 's 440 ahead (the owner\'s view of note 1)'), ('owner_fwd_s455', 's 455, 2 m right, ahead'), ('owner_right_s440', 's 440 looking right 70 deg'), ('owner_right_s520', 's 520 looking right 70 deg'), ('owner_right_s600', 's 600 looking right 70 deg')],
 'sheet_verge_r11': [('verge_s500', 's 500, 7 m left of the centre, ahead'), ('verge_s1300', 's 1300 left verge'), ('verge_s1550', 's 1550 left verge'), ('verge_s2300', 's 2300 left verge'), ('verge_s2850', 's 2850 left verge'), ('verge_s3300', 's 3300 left verge')],
 'sheet_stand_r11': [('stand_trk_a', 'from the track, s 3580 looking ahead-left'), ('stand_trk_b', 'from the apron, s 3592, 3 m left of the centre'), ('stand_pit_a', 'from the pit lane, s 3572'), ('stand_pit_c', 'from the pit lane, s 3595, looking right')],
 'sheet_pit_exit_r11': [('exit_lane_s170', 'pit lane s 170, driver\'s eye'), ('exit_lane_s230', 'pit lane s 230, looking toward the ladder'), ('exit_course_s230', 'course s 230, looking left at the ladder'), ('exit_line_s270', 'course s 270, 3 m left of the centre, ahead')],
}
for name, rows in SHEETS.items():
    W, H = 640, 360
    M = Image.new('RGB', (2 * W, len(rows) * (H + 16)), (20, 20, 20)); dr = ImageDraw.Draw(M)
    for k, (f, cap) in enumerate(rows):
        y = k * (H + 16)
        for j, (tag, lab) in enumerate((('before', 'round 10 (ea1a07f8bd)'), ('after', 'round 11'))):
            M.paste(Image.open(os.path.join(D, tag, 'sim', f + '.jpg')).convert('RGB').resize((W, H)), (j * W, y + 16))
            dr.text((j * W + 6, y + 2), f'{lab}: {cap}', fill=(230, 230, 230))
    M.save(os.path.join(D, name + '.jpg'), quality=85)
    print(name, len(rows))
