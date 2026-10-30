# Power split (30 Oct 2026): the stage-A comparison table from the saved traffic_sim sets.
#   python3 tools/race/power_table.py 0.5:x 0.75:x   (reads tools/race/out/power/p<share>_<planner>.json and the C5 p = 0 baselines in the planner-c5 worktree's tools/race/out)
import json,sys,glob,os
def row(name, js, runs):
    d=json.load(open(js)); P=d['pooled']; byD={x['d']:x for x in P['byD']}
    pc=lambda k: 100*byD[k]['rate']
    # passed-lap loss (pooled), from lostByD
    L={x['d']:x for x in P['lostByD']}
    pl=[L[k]['passed']['med'] for k in ['0-1','1-3','3-8','8-15']]
    t=d['perTrack']; lg,bw=t['laguna_seca'],t['buttonwillow']
    tr=d['train']; w=d['wait']
    # landings from run files
    land={}
    for tk in ['laguna_seca','buttonwillow']:
        fs=sorted(glob.glob(f'{runs}/{tk}_*.json')); h=dn=cm=0
        for f in fs:
            a=json.load(open(f))['metrics'].get('att') or {}
            h+=a.get('1>2',0); dn+=sum(v for k,v in a.items() if k.startswith('done')); cm+=sum(v for k,v in a.items() if k.startswith('train in') or k.startswith('train out'))
        n=max(1,len(fs)); land[tk]=(h/n,dn/n,cm/n)
    f=lambda x:f'{x:.1f}'
    print(f"| {name} | {pc('0-1'):.1f} / {pc('1-3'):.1f} / {pc('3-8'):.1f} / {pc('8-15'):.1f} / {pc('>15'):.1f}, floor {pc('Yfaster'):.1f} | {pl[0]:.1f} / {pl[1]:.1f} / {pl[2]:.1f} / {pl[3]:.1f} | {lg['contactsPerCarLap']:.4f} / {bw['contactsPerCarLap']:.4f} | {lg['fourOffPerCarLap']:.4f} / {bw['fourOffPerCarLap']:.4f} | {lg['passesTotal']} / {bw['passesTotal']} | {f(tr['laguna_seca']['passesPerRace'])} / {f(tr['buttonwillow']['passesPerRace'])} | {f(tr['buttonwillow']['pitPerRace'])} | {f(land['laguna_seca'][0])} / {f(land['buttonwillow'][0])} ({f(land['laguna_seca'][1])} / {f(land['buttonwillow'][1])} done of {f(land['laguna_seca'][2])} / {f(land['buttonwillow'][2])}) | {w['laguna_seca']['median']:.1f} / {w['laguna_seca']['p90']:.0f}; {w['buttonwillow']['median']:.1f} / {w['buttonwillow']['p90']:.0f} | {w['laguna_seca']['straightDvArrive']['median']:.1f} / {w['buttonwillow']['straightDvArrive']['median']:.1f}; {w['laguna_seca']['straightDvSteps']['median']:.2f} / {w['buttonwillow']['straightDvSteps']['median']:.2f} |")
C='/Users/cobyhartman/dev/probe_sim-wt/planner-c5/tools/race/out'
W='/Users/cobyhartman/dev/probe_sim-wt/power/tools/race/out'
print('| run | cells 0-1/1-3/3-8/8-15/>15 % (g<2 s), floor | passing lap loss 0-1/1-3/3-8/8-15 s | contacts L / BW | four-off L / BW | green passes L / BW | train passes per race L / BW | BW pit straight | landings (HOLD) per race L / BW (done of commits) | wait median / p90 L; BW | straight dv arrival L / BW; over the wait |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
specs=[('lanes p=0 (C5 screen)',C+'/c5/lanes_screen.json',C+'/traffic/runs/full_lanes'),('offset p=0 (C5 s1)',C+'/c5/s1.json',C+'/traffic/runs/s1')]
for a in sys.argv[1:]:
    p,pl=a.split(':'); 
    for planner in ['lanes','offset']:
        if os.path.exists(f'{W}/power/p{p}_{planner}.json'): specs.append((f'{planner} p={p}',f'{W}/power/p{p}_{planner}.json',f'{W}/traffic/runs/pw{p}_{planner}'))
for s in specs:
    try: row(*s)
    except Exception as e: print('ERR',s[0],e)
