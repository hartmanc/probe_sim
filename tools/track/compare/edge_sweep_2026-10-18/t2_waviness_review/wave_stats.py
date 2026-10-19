import json, math, sys
import numpy as np
def load(p):
    T=json.load(open(p)); C=np.array(T['center'])[:,:2]; L=np.array(T['left'])[:,:2]; R=np.array(T['right'])[:,:2]
    Lz=np.array(T['left'])[:,2]; Rz=np.array(T['right'])[:,2]; Cz=np.array(T['center'])[:,2]
    n=T['n']; nxt=np.roll(C,-1,0); prv=np.roll(C,1,0); t=nxt-prv; t/=np.linalg.norm(t,axis=1)[:,None]; nrm=np.stack([-t[:,1],t[:,0]],1)
    hl=((L-C)*nrm).sum(1); hr=-((R-C)*nrm).sum(1)
    head=np.unwrap(np.arctan2(t[:,1],t[:,0]))
    return dict(T=T,C=C,L=L,R=R,hl=hl,hr=hr,head=head,n=n,Lz=Lz,Rz=Rz,Cz=Cz,nrm=nrm)
def gauss(v,s):
    k=int(4*s); x=np.arange(-k,k+1); w=np.exp(-0.5*(x/s)**2); w/=w.sum()
    return np.convolve(np.concatenate([v[-k:],v,v[:k]]),w,'same')[k:-k]
def kink_deg(P):
    """turn angle per station of a polyline, degrees"""
    d=np.roll(P,-1,0)-P; h=np.unwrap(np.arctan2(d[:,1],d[:,0])); return np.degrees(np.diff(np.concatenate([h,h[:1]])))
def report(name,d,lo,hi):
    sl=slice(lo,hi)
    hl,hr=d['hl'],d['hr']
    rl=hl-gauss(hl,15); rr=hr-gauss(hr,15)
    kl=kink_deg(d['L']); kr=kink_deg(d['R']); kc=kink_deg(d['C'])
    # kink of the edge relative to the centre (what the eye sees as a wiggle of the painted line)
    dkl=kl-kc; dkr=kr-kc
    zl=np.diff(d['Lz'],2); zr=np.diff(d['Rz'],2); zc=np.diff(d['Cz'],2)
    print(f"{name:10s} {lo}-{hi}: hw resid vs sigma15 | L rms {rl[sl].std():.3f} max {abs(rl[sl]).max():.2f} | R rms {rr[sl].std():.3f} max {abs(rr[sl]).max():.2f} || edge kink rel centre deg/station | L rms {dkl[sl].std():.2f} max {abs(dkl[sl]).max():.2f} | R rms {dkr[sl].std():.2f} max {abs(dkr[sl]).max():.2f} || centre kink rms {kc[sl].std():.2f} (2nd diff of heading rms {np.diff(kc)[sl].std():.3f}) || z 2nd diff rms L {zl[sl].std()*1000:.1f} R {zr[sl].std()*1000:.1f} C {zc[sl].std()*1000:.1f} mm")
    return rl,rr,dkl,dkr
paths={'main':'track_main.json','4c654a4':'track_4c654a4.json','d417367':'track_d417367.json','head':'track_head.json'}
D={k:load(sys.argv[1]+'/'+v) for k,v in paths.items()}
for lo,hi in [(150,520),(300,470),(0,3560)]:
    print('== stations',lo,hi)
    for k in paths: report(k,D[k],lo,hi)
print()
print('station  main hl/hr   4c654a4 hl/hr   d417367 hl/hr   head hl/hr   (head-main) dL dR  | head residual rl rr')
h=D['head']; m=D['main']
rl=h['hl']-gauss(h['hl'],15); rr=h['hr']-gauss(h['hr'],15)
for k in range(300,471,5):
    print(f"{k:5d}   {m['hl'][k]:4.1f}/{m['hr'][k]:4.1f}      {D['4c654a4']['hl'][k]:4.1f}/{D['4c654a4']['hr'][k]:4.1f}         {D['d417367']['hl'][k]:4.1f}/{D['d417367']['hr'][k]:4.1f}        {h['hl'][k]:4.1f}/{h['hr'][k]:4.1f}      {h['hl'][k]-m['hl'][k]:+5.2f} {h['hr'][k]-m['hr'][k]:+5.2f}   | {rl[k]:+5.2f} {rr[k]:+5.2f}")
# where around the lap is the head's residual largest (runs > 0.12 m)
print()
for side,r in (('L',rl),('R',rr)):
    bad=np.where(abs(r)>0.12)[0]; runs=[]
    for k in bad:
        if runs and k-runs[-1][1]<=3: runs[-1][1]=k
        else: runs.append([k,k])
    print(side,'residual >0.12 m runs (head):',[(a,b,round(float(abs(r[a:b+1]).max()),2)) for a,b in runs if b-a>=2][:40])
