// Mid-Ohio round 7: hash of the structure triangle soups (src/app/structures.ts structureSoups) of a published package, to
// prove an app change leaves another track's structures byte-identical (run before / after the change).
//   npx tsx tools/track/compare/mid_ohio/r7/soup_hash.ts sonoma laguna_seca buttonwillow
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { structureSoups } from '../../../../../src/app/structures';
for (const id of process.argv.slice(2)) {
  const sc = JSON.parse(readFileSync(`public/tracks/${id}/scenery.json`, 'utf8'));
  const S = structureSoups(sc.structures ?? [], sc.terraces ?? []);
  const h = createHash('sha256');
  for (const k of ['solid', 'paint', 'fabric', 'terrace'] as const) { h.update(Float64Array.from((S as any)[k].pos)); h.update(Float64Array.from((S as any)[k].col)); }
  console.log(id, h.digest('hex').slice(0, 16));
}
