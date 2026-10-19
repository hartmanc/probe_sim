#!/bin/sh
# move <PREFIX>_* renders from youtube_sim/ into youtube_sim_<TAG>/, build sheets and judge images
set -e; cd "$(dirname "$0")"; P=$1; TAG=$2
mkdir -p youtube_sim_$TAG
for f in youtube_sim/${P}_*.jpg; do b=$(basename $f); mv $f youtube_sim_$TAG/${b#${P}_}; done
U="uv run --python 3.12 --with pillow python -I"
$U make_youtube_sheets.py youtube_sim_$TAG $TAG; $U make_satellite_sheets.py youtube_sim_$TAG $TAG
rm -f youtube_sim_$TAG/td_*.jpg
$U -c "
import glob
from PIL import Image
for f in glob.glob('youtube_sim_$TAG/*.jpg'):
  im=Image.open(f)
  if im.width>1300: im.resize((1280,round(1280*im.height/im.width))).save(f,quality=85)"
$U make_judge_images.py $TAG
