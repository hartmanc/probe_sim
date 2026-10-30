// Re-render the jam report of saved results (tools/race/out/jams/*.json, or a replay's JSON): npx tsx tools/race/jams_render.ts <file.json> [more]
import { readFileSync } from 'node:fs';
import { basename } from 'node:path';
import { jamsMd, type JamsResult } from './jams_core';
for (const f of process.argv.slice(2)) {
  const j = JSON.parse(readFileSync(f, 'utf8')) as JamsResult | { analysis: { jams?: JamsResult } };
  const r = 'analysis' in j ? j.analysis.jams : j;
  if (r) console.log(jamsMd(r, basename(f).replace(/\.json$/, '')));
}
