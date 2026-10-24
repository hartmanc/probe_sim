// Stage 3 (config scenery.marks_on_surface, Sonoma round 14B): drape the ground marks of <dir>/scenery.json on the
// package's own driven surface (tools/track/gates/groundMarks.ts drapeMarks) and write it back.
//   npx tsx tools/track/drape_marks.ts <package dir> [lift]
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { drapeMarks, PAINT_LIFT } from './gates/groundMarks';
import { loadHeightfield } from '../../src/physics/index';

const dir = process.argv[2];
const lift = process.argv[3] ? Number(process.argv[3]) : PAINT_LIFT;
const track = JSON.parse(readFileSync(join(dir, 'track.json'), 'utf8'));
const sc = JSON.parse(readFileSync(join(dir, 'scenery.json'), 'utf8'));
const hf = loadHeightfield(Uint8Array.from(readFileSync(join(dir, 'heightfield.bin'))).buffer);
const r = drapeMarks(track, hf, sc, lift);
writeFileSync(join(dir, 'scenery.json'), JSON.stringify(sc));
console.log(`ground marks draped on the driven surface: ${r.paint} paint-line vertices (+${lift} m), ${r.cones} cones, ${r.kerbLines} kerb-line points, `
  + `${r.signs} ground signs; largest change ${r.maxChange} m (${r.worst})`);
