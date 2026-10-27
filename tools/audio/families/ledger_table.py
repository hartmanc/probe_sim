"""Round-two before / after table for LEDGER.md from quality.py outputs.

    python3 -I tools/audio/families/ledger_table.py Q_BEFORE.json Q_AFTER.json
"""
import json
import sys

B = json.load(open(sys.argv[1]))
A = json.load(open(sys.argv[2]))


def cell(s, f):
    fails = f
    return (f"{s['real_on']}/{s['real_off']} | {s['speech']} | {s['ratio_fail']} ({s['ratio_min']:.2f}-{s['ratio_max']:.2f}) | "
            f"{'yes' if s['idle_ok'] else 'no'} | {s['loop_med']:.2f} ({s['loop_fail']}) | {s['seam_corr_med']:.2f} | {s['bytes'] // 1000} KB")


print("| Family | when | real on/off | speech loops | ratio fails (min-max) | real idle in gate | loop median s (fails) "
      "| seam corr median | Ogg + json |")
print("|---|---|---|---|---|---|---|---|---|")
for fam in B:
    b = B[fam]["summary"]
    a = A.get(fam, B[fam])["summary"]
    print(f"| `{fam}` | before | {cell(b, B[fam]['fails'])} |")
    print(f"| | after | {cell(a, A.get(fam, B[fam])['fails'])} |")
