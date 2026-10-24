// Same car at two events (owner decision d07, 23 Oct 2026): a Sonoma identity row and its models.json row carry
// `same_car`, the id of that car's model at an earlier event. Each event keeps its own glb (livery per event);
// the link only says it is one car, so a later car picker does not list it twice.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const readJson = (p: string) => JSON.parse(readFileSync(pub + p, 'utf8'));

describe('field: same car at two events', () => {
  it('the Sonoma same_car links resolve to existing ids, in identity.json and models.json alike', () => {
    const sonoma = readJson('cars/field/sonoma/identity.json') as { id: string; same_car?: string }[];
    const models = (readJson('cars/field/models.json') as { cars: { id?: string; number: string; same_car?: string }[] }).cars;
    const byId = new Map(models.map((m) => [m.id ?? m.number, m]));
    const links = Object.fromEntries(sonoma.filter((r) => r.same_car).map((r) => [r.id, r.same_car]));
    expect(links).toEqual({ '21': '200', '685_sp': '685', '44_sp': '44' });
    for (const [id, earlier] of Object.entries(links)) {
      expect(byId.get(id)?.same_car).toBe(earlier);          // the model row carries the same link
      expect(byId.has(earlier!)).toBe(true);                  // the earlier event's model exists
      expect(byId.get(earlier!)?.same_car).toBeUndefined();   // and is the end of the chain
    }
  });
});
