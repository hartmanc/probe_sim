# usage: python3 -I tools/determinism/pow_or_tables.py <dir with optimized-routines math_pow_log_data.c, math_exp_data.c> src/physics/dmath_pow_data.ts
# Compare the port's pow tables (src/physics/dmath_pow_data.ts) with Arm optimized-routines' math/pow_log_data.c and
# math/exp_data.c, after a tiny C preprocessor pass with the x86-64 configuration (reference files are only parsed).
import re, sys
orp, tsp = sys.argv[1], sys.argv[2]
ts = open(tsp).read()
def pp(text, defs):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    out, stack = [], []   # stack of (active, taken)
    def cond(c):
        c = c.replace('&&', ' and ').replace('||', ' or ')
        c = re.sub(r'!(?!=)', ' not ', c)
        c = re.sub(r'defined\s*\(?\s*(\w+)\s*\)?', lambda m: str(m.group(1) in defs), c)
        c = re.sub(r'\b([A-Za-z_]\w*)\b', lambda m: m.group(1) if m.group(1) in ('and','or','not','True','False') else str(defs.get(m.group(1), 0)), c)
        c = c.replace('<<', '<<')
        return bool(eval(c, {'__builtins__': {}}, {}))
    for line in text.split('\n'):
        st = line.strip()
        act = all(a for a, _ in stack)
        if st.startswith('#if'):
            v = cond(st[3:]) if act else False
            stack.append((v, v)); continue
        if st.startswith('#elif'):
            a, taken = stack.pop(); outer = all(x for x, _ in stack)
            v = (not taken) and outer and cond(st[5:])
            stack.append((v, taken or v)); continue
        if st.startswith('#else'):
            a, taken = stack.pop(); stack.append((not taken, True)); continue
        if st.startswith('#endif'):
            stack.pop(); continue
        if st.startswith('#'):
            continue
        if act: out.append(line)
    return '\n'.join(out)
def ev(e):
    v = 1.0
    for x in [t.strip() for t in e.split('*')]:
        v *= float.fromhex(x) if re.match(r'-?0x', x) else float(defs_num.get(x, x))
    return v
defs = {'POW_LOG_TABLE_BITS': 7, 'POW_LOG_POLY_ORDER': 8, 'EXP_TABLE_BITS': 7, 'EXP_POLY_ORDER': 5, 'EXP_POLY_WIDE': 0, 'EXP_USE_TOINT_NARROW': 0, 'EXP2_POLY_ORDER': 5, 'EXP2_POLY_WIDE': 0, 'TOINT_INTRINSICS': 0, 'N': 128}
defs_num = {'N': 128}
pl = pp(open(orp + '/math_pow_log_data.c').read(), defs)
poly = pl[pl.index('.poly'):]; poly = poly[poly.index('{') + 1:poly.index('}')]
A = [ev(x) for x in poly.split(',') if x.strip()]
rows = re.findall(r'A\(([^()]*)\)', pl[pl.index('.tab'):])
T = []
for r in rows:
    a, b, c = [float.fromhex(v.strip()) for v in r.split(',')]
    T += [a, b, c]
ln2hi = float.fromhex(re.search(r'\.ln2hi\s*=\s*([^,]+),', pl).group(1)); ln2lo = float.fromhex(re.search(r'\.ln2lo\s*=\s*([^,]+),', pl).group(1))
def tsarr(name):
    m = re.search(r'export const ' + name + r'\s*=\s*(?:new \w+\()?\[([^\]]*)\]', ts)
    return [x.strip() for x in m.group(1).split(',') if x.strip()]
tA = [float(x) for x in tsarr('POW_A')]; tT = [float(x) for x in tsarr('POW_TAB')]
tl = re.search(r'POW_LN2HI = ([^,]+), POW_LN2LO = ([^;]+);', ts)
print('pow log: ln2hi', float(tl.group(1)) == ln2hi, 'ln2lo', float(tl.group(2)) == ln2lo, '| poly', len(A), len(tA), A == tA, '| table', len(T) // 3, 'entries', T == tT)
if A != tA: print('  OR poly', A, '\n  TS poly', tA)
ed = pp(open(orp + '/math_exp_data.c').read(), defs)
ed = ed[ed.index('__exp_data = {'):]
g = lambda k: re.search(r'\.' + k + r'\s*=\s*([^,]+),', ed).group(1)
poly = ed[ed.index('.poly'):]; poly = poly[poly.index('{') + 1:poly.index('}')]
C = [ev(x) for x in poly.split(',') if x.strip()]
tab = ed[ed.index('.tab'):]; tab = tab[tab.index('{') + 1:tab.index('}')]
U = [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', tab)]
pairs = []
for u in U: pairs += [u >> 32, u & 0xffffffff]
tu = [int(x, 16) for x in tsarr('EXP_TAB_U32')]
cs = re.search(r'EXP_INVLN2N = ([^,]+), EXP_NEGLN2HIN = ([^,]+), EXP_NEGLN2LON = ([^,]+), EXP_SHIFT = ([^;,]+)', ts).groups()
print('exp: invln2N', ev(g('invln2N')) == float(cs[0]), 'negln2hiN', float.fromhex(g('negln2hiN')) == float(cs[1]), 'negln2loN', float.fromhex(g('negln2loN')) == float(cs[2]), 'shift', float.fromhex(g('shift')) == float(cs[3]),
      '| poly', len(C), C == [float(x) for x in tsarr('EXP_C')], '| table', len(U), 'entries', pairs == tu)
