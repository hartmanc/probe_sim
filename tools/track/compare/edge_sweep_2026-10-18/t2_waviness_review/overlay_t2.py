import json, math, sys, numpy as np
from PIL import Image, ImageDraw
sp=sys.argv[1]; ROOT='/Users/cobyhartman/dev/probe_sim'
MPP=156543.03*math.cos(math.radians(36.5843))/2**20
regs={r[0]:r for r in json.load(open(f'{ROOT}/tools/track/out/paint_regs.json'))}
tiles={t['name']:t for t in json.load(open(f'{ROOT}/tools/track/compare/satellite/z20_tiles.json'))}
S=np.load(f'{ROOT}/tools/track/out/sweep_final.npz')
def geom(p):
    T=json.load(open(p)); C=np.array(T['center'])[:,:2]; L=np.array(T['left'])[:,:2]; R=np.array(T['right'])[:,:2]
    t=np.roll(C,-1,0)-np.roll(C,1,0); t/=np.linalg.norm(t,axis=1)[:,None]; N=np.c_[-t[:,1],t[:,0]]
    return C,L,R,N
V={k:geom(f'{sp}/track_{k}.json') for k in ('main','4c654a4','head')}
C,L,R,N=V['head']
for nm,(lo,hi) in [('z20_s0340',(290,392)),('z20_s0425',(380,480)),('z20_s0510',(460,560))]:
    t=tiles[nm]; dx,dy=regs[nm][1:3]
    im=Image.open(f'{ROOT}/tools/track/compare/satellite/{nm}_google.jpg').convert('RGB'); W,H=im.size
    def px(x,y): return (W/2+(x+dx-t['x'])/MPP, H/2-(y+dy-t['y'])/MPP)
    d=ImageDraw.Draw(im)
    cols={'main':(255,230,0),'4c654a4':(0,220,255),'head':(255,40,40)}
    for k,(c,l,r,n) in V.items():
        for P in (l,r):
            pts=[px(*P[s]) for s in range(lo,hi)]; d.line(pts,fill=cols[k],width=2 if k=='head' else 1)
    kc={1:(255,255,255),2:(255,0,255),3:(255,140,0),4:(60,60,255),0:(0,0,0)}
    for s in range(lo,hi):
        for side,sg in (('left',1),('right',-1)):
            dv=S['dev_'+side][s]; kd=int(S['kind_'+side][s])
            if np.isfinite(dv):
                E=L[s] if side=='left' else R[s]; p=E+sg*N[s]*dv; x,y=px(*p); d.ellipse([x-2,y-2,x+2,y+2],fill=kc.get(kd,(0,0,0)))
        if s%10==0:
            x,y=px(*C[s]); d.text((x+3,y-5),str(s),fill=(255,255,255))
    xs=[px(*C[s])[0] for s in range(lo,hi)]+[px(*L[s])[0] for s in range(lo,hi)]+[px(*R[s])[0] for s in range(lo,hi)]
    ys=[px(*C[s])[1] for s in range(lo,hi)]+[px(*L[s])[1] for s in range(lo,hi)]+[px(*R[s])[1] for s in range(lo,hi)]
    x0,x1=max(0,int(min(xs))-60),min(W,int(max(xs))+60); y0,y1=max(0,int(min(ys))-40),min(H,int(max(ys))+40)
    cr=im.crop((x0,y0,x1,y1)); sc=2 if (x1-x0)<800 else 1; cr=cr.resize((cr.width*sc,cr.height*sc),Image.LANCZOS)
    dd=ImageDraw.Draw(cr); dd.rectangle([0,0,cr.width,16],fill=(0,0,0)); dd.text((4,2),f'{nm} stations {lo}-{hi}  yellow=main  cyan=4c654a4 (paint rebuild)  red=branch head;  dots = sweep detections: white=line magenta=kerb orange=non-asphalt blue=shadow',fill=(255,255,255))
    cr.save(f'{sp}/overlay_{nm}.png'); print('wrote',f'{sp}/overlay_{nm}.png',cr.size)
