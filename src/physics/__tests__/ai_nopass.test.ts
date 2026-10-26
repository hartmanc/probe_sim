// Issue #19: the Corkscrew no-passing zone belongs to Laguna Seca's T8 (track id + corner id), not to any corner named T8.
import { expect, test } from 'vitest';
import { RaceLine } from '../ai/line';
import { NO_PASS_CORNERS } from '../ai/driver';
import { loadTrackPack } from '../../../tools/race/load';

test('no-passing corners are keyed to the track id and the corner id (issue #19)', () => {
  expect(NO_PASS_CORNERS).toEqual({ laguna_seca: ['T8'] });
  const laguna = loadTrackPack('laguna_seca').line;
  expect(laguna.trackId).toBe('laguna_seca');
  const t8 = laguna.corners.filter((c) => c.turn === 'T8');
  expect(t8.map((c) => c.name)).toEqual(['T8 Corkscrew']);
  for (const id of ['sonoma', 'buttonwillow']) {
    const line = loadTrackPack(id).line;
    expect(line.trackId).toBe(id);
    // Buttonwillow's T8 is a passable braking zone (it was named "T8 Corkscrew" and closed to passing until issue #19);
    // (Sonoma's T8 finds its slowest point within 30 m of T7a's apex, so the line merges it into T7a: never named T8 there)
    if (id === 'buttonwillow') expect(line.corners.find((c) => c.turn === 'T8')?.passable).toBe(true);
    expect(line.corners.some((c) => /corkscrew/i.test(c.name))).toBe(false);
    expect(NO_PASS_CORNERS[id]).toBeUndefined();
  }
  // a line built without a track id (a tool, a test) has no track-specific rule and no Corkscrew
  const p = loadTrackPack('laguna_seca');
  const anon = new RaceLine(p.track, p.ghosts);
  expect(anon.trackId).toBe('');
  expect(anon.corners.some((c) => /corkscrew/i.test(c.name))).toBe(false);
});
