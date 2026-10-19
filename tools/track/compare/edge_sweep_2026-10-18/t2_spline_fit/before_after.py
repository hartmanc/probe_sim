import json, math, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT='/Users/cobyhartman/dev/probe_sim'; OUTP=sys.argv[1]; OLD=sys.argv[2]
MPP=156543.03*math.cos(math.radians(36.5843))/2**20
tiles={t['name']:t for t in json.load(open(f'{ROOT}/tools/track/compare/satellite_clean/tiles.json'))}
def geo(p):
    T=json.load(open(p)); return np.array(T['center'])[:,:2],np.array(T['left'])[:,:2],np.array(T['right'])[:,:2]
Cn,Ln,Rn=geo(f'{ROOT}/public/tracks/laguna_seca/track.json'); Co,Lo,Ro=geo(OLD)
panels=[]
for nm,lo,hi in [('c20_a2',300,390),('c20_a4',350,440),('c20_a5',390,480),('c20_a8',430,560)]:
    t=tiles[nm]; dx,dy=-0.3+t['rel_dx'],t['rel_dy']
    im=Image.open(f'{ROOT}/tools/track/compare/satellite_clean/{nm}_google.jpg').convert('RGB'); W,H=im.size
    px=lambda p:(W/2+(p[0]+dx-t['x'])/MPP, H/2-(p[1]+dy-t['y'])/MPP)
    d=ImageDraw.Draw(im)
    for E,col in ((Lo,(255,40,40)),(Ro,(255,40,40)),(Ln,(40,160,255)),(Rn,(40,160,255))):
        d.line([px(E[s]) for s in range(lo,hi)],fill=col,width=2)
    for s in range(lo,hi,10): x,y=px(Cn[s]); d.text((x+4,y-6),str(s),fill=(255,255,255))
    P=np.r_[Ln[lo:hi],Rn[lo:hi]]; xs=[px(p)[0] for p in P]; ys=[px(p)[1] for p in P]
    box=(max(0,int(min(xs))-40),max(0,int(min(ys))-20),min(W,int(max(xs))+40),min(H,int(max(ys))+20))
    panels.append(im.crop(box))
h=max(p.height for p in panels); sheet=Image.new('RGB',(sum(p.width for p in panels)+10*len(panels),h+28),(20,20,20)); x=0
for p in panels: sheet.paste(p,(x,28)); x+=p.width+10
ImageDraw.Draw(sheet).text((8,7),'T2 approach to Andretti exit on clean Google captures (UI and labels off).  RED = edge before (branch ab4b15d)   BLUE = spline fit (this change)',fill=(255,255,255))
sheet.save(OUTP,quality=90); print(OUTP, sheet.size)
