// Re-record fixtures/onpave_drive.json after a track geometry change (18 Oct 2026: painted-edge rebuild).
//   npx tsx src/physics/__tests__/record_onpave.ts
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { onPavementDrive } from './onpave_drive';
const path = fileURLToPath(new URL('./fixtures/onpave_drive.json', import.meta.url));
const old = JSON.parse(readFileSync(path, 'utf8')) as Record<string, unknown>;
const r = onPavementDrive();
if (!r.allPaved) throw new Error('drive left the pavement: not a valid fixture');
writeFileSync(path, JSON.stringify({ ...old, ...r }));
console.log('recorded', r.trace.length, 'values');
