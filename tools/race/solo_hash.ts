// Solo identity (traffic round gate G5): 3 cars per track (first, middle, last of the pace file by grid, at their fitted
// scales) drive 2 laps alone with runSolo; prints each car's laps and one sha256 per track over the exact lap bits. A driver
// change that leaves the alone path untouched prints the same hashes before and after.
//   npx tsx tools/race/solo_hash.ts [--tracks laguna_seca,sonoma,buttonwillow,mid_ohio] [--planner lanes|offset] [--corner-pass]
import { createHash } from 'node:crypto';
import { runSolo } from '../../src/physics/ai/solo';
import { parseIdentity, fieldKey, AI_VERSION, setPowerShare } from '../../src/physics/ai/field';
import { loadTrackPack, loadProbeJson, loadPace, loadIdentityJson } from './load';

const argv = process.argv.slice(2);
const i = argv.indexOf('--tracks');
const tracks = i >= 0 ? argv[i + 1].split(',') : ['laguna_seca', 'sonoma', 'buttonwillow', 'mid_ohio'];
const planner = argv.includes('--planner') && argv[argv.indexOf('--planner') + 1] === 'offset' ? 'offset' : 'lanes';
if (argv.includes('--power-share')) setPowerShare(Number(argv[argv.indexOf('--power-share') + 1]));
const cornerPass = argv.includes('--corner-pass');
console.log(`AI_VERSION ${AI_VERSION}, planner ${planner}${cornerPass ? ', cornerPass' : ''}`);
for (const t of tracks) {
  const pack = loadTrackPack(t), pace = loadPace(t), idj = loadIdentityJson(t);
  const ident = idj ? parseIdentity(idj) : new Map();
  const cars = pace.cars.filter((c) => !c.player && c.scale && c.scale > 0).sort((a, b) => a.grid - b.grid);
  const pick = [cars[0], cars[Math.floor(cars.length / 2)], cars[cars.length - 1]];
  const h = createHash('sha256');
  const rows: string[] = [];
  for (const c of pick) {
    const r = runSolo(pack.line, pack.makeSurface(), loadProbeJson(), ident.get(fieldKey(c)) ?? null, c.scale!, 2, { planner, cornerPass });
    const bits = r.laps.map((x) => x.toString()).join(',') + `|${r.recoveries}|${r.offSteps}`;
    h.update(`${c.number}:${bits};`);
    rows.push(`#${c.number} ${r.laps.map((x) => x.toFixed(4)).join(' ')}`);
  }
  console.log(`${t}: ${h.digest('hex').slice(0, 16)}  (${rows.join(', ')})`);
}
