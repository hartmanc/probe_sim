// Field wiring per track (23 Oct 2026): a track with its own identity.json (TRACKS[id].identity) races its own field.
// Every identity row has a pace row (except an entrant the pace file names as left out with no lap in the session:
// it has no pace to draw), every AI pace row has its identity row, and every AI car's model key (field.ts modelKey:
// pace `model_id`, else identity `model_id`, else the id) is a models.json row whose glb exists, as the app's
// loader (normaliseModelRows) and race mode (modelQueue) resolve them.
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { TRACKS } from '../../scoreboard/config';
import { fieldKey, modelKey, parseIdentity, type PaceJson } from '../../physics/ai/field';
import { normaliseModelRows } from '../loader';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const readJson = (p: string) => JSON.parse(readFileSync(pub + p, 'utf8'));
const models = normaliseModelRows(readJson('cars/field/models.json'));
const modelBy = new Map(models.map((m) => [m.id, m]));
const withIdentity = Object.entries(TRACKS).filter(([, t]) => t.identity);

describe('field wiring: tracks with their own identity.json', () => {
  it('Buttonwillow and Sonoma race their own fields', () => {
    expect(withIdentity.map(([id]) => id).sort()).toEqual(['buttonwillow', 'sonoma']);
  });
  for (const [track, t] of withIdentity) {
    it(`${track}: every identity row has a pace row, and every AI car an identity row and a model`, () => {
      const pace = readJson(t.pace) as PaceJson;
      const ident = parseIdentity(readJson(t.identity!));
      expect(ident.size).toBeGreaterThan(0);
      const ai = pace.cars.filter((c) => !c.player);
      const paceKeys = new Set(pace.cars.map((c) => fieldKey(c)));
      // the entrants the pace file names as left out with no lap in the session (pace_track.ts --own `source`)
      const noLap = new Set((/left out with no lap in the session: ([^;)]*)/.exec(pace.source ?? '')?.[1] ?? '').split(', ').map((s) => s.replace('#', '').trim()).filter(Boolean));
      const unpaced = [...ident.values()].filter((r) => !paceKeys.has(fieldKey(r)) && !noLap.has(String(r.number)));
      expect(unpaced.map((r) => fieldKey(r))).toEqual([]);
      // every left-out entrant is in identity.json (so the exemption names real rows)
      for (const n of noLap) expect([...ident.values()].some((r) => String(r.number) === n)).toBe(true);
      const keys = ai.map((c) => fieldKey(c));
      expect(new Set(keys).size).toBe(keys.length);                     // ids unique
      expect(new Set(ai.map((c) => c.number)).size).toBe(ai.length);    // numbers unique (calibration keys fits by number)
      const noIdent = ai.filter((c) => !ident.has(fieldKey(c))).map((c) => fieldKey(c));
      expect(noIdent).toEqual([]);
      const noModel = ai.map((c) => [fieldKey(c), modelKey(c, ident.get(fieldKey(c)))] as const)
        .filter(([, k]) => !modelBy.has(k) || !existsSync(pub + 'cars/field/' + modelBy.get(k)!.file));
      expect(noModel).toEqual([]);
      // the identity row's number is the pace row's number (an id never picks up another entrant's row)
      for (const c of ai) expect(String(ident.get(fieldKey(c))!.number)).toBe(c.number);
    });
  }
});
