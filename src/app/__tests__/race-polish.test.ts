import { describe, expect, it } from 'vitest';
import type * as THREE from 'three';
import { audioCreditsFrom, carCreditsFrom, creditLine, loadCredits, mergeCarCredits, teamsFrom, PHOTO_CREDITS } from '../credits';
import { raceMenuLabel, raceResultFor, rowStatus } from '../modes/race';
import { resultRows } from '../race-hud';
import { boardColor, buildPlaceholderCar, triangleCount, PROBE_DIMS } from '../field-cars';
import type { ResultRow } from '../../physics/ai/race';

describe('credits', () => {
  const importer = {
    about: 'Third-party 3D models used as the base of field cars.',
    cars: {
      '58': { title: 'Mini Cooper S', author: 'cenobyte', licence: 'CC-BY-4.0', licence_url: 'http://creativecommons.org/licenses/by/4.0/', url: 'https://sketchfab.com/3d-models/mini', changes: 'decimated' },
      '1': { title: 'Mini Cooper Mk1', author: 'Ivan_WSK', licence: 'CC-BY-4.0', url: 'https://sketchfab.com/3d-models/mk1' },
    },
  };
  const decals = {
    '38': [
      { image: 'tools/cars/kit/reference/38/kji_face.jpg', source: 'https://commons.wikimedia.org/wiki/File:KJI.jpg', author: 'kremlin.ru', licence: 'CC BY 4.0' },
      { image: 'tools/cars/kit/reference/38/dprk_flag.png', source: 'self-drawn DPRK flag (public-domain design)', author: 'spec 38', licence: 'CC0' },
      { image: 'tools/cars/kit/reference/38/dprk_flag.png', source: 'self-drawn DPRK flag (public-domain design)', author: 'spec 38', licence: 'CC0' },
      { image: 'tools/cars/kit/reference/38/kji_frame.jpg', source: 'https://commons.wikimedia.org/wiki/File:KJI.jpg', author: 'kremlin.ru', licence: 'CC BY 4.0' },
    ],
    '58': { source: 'https://commons.wikimedia.org/wiki/File:UnionJack.svg', author: 'Wikimedia', license: 'Public domain' },
  };

  it('normalises one entry (url / non-url source, licence spellings, notes)', () => {
    expect(creditLine({ source: 'https://x.org/a', author: 'A', license: 'CC0' }, 'Decal image')).toEqual({ kind: 'Decal image', author: 'A', licence: 'CC0', url: 'https://x.org/a' });
    expect(creditLine({ source: 'self-drawn flag', by: 'spec' }, 'Decal image')).toEqual({ kind: 'Decal image', title: 'self-drawn flag', author: 'spec' });
    expect(creditLine({ image: 'only/a/path.png' }, 'x')).toBeNull();
    expect(creditLine('nope', 'x')).toBeNull();
  });

  it('reads both files in their shapes (and an array shape) by car number', () => {
    const a = carCreditsFrom(importer, '3D model');
    expect([...a.keys()].sort()).toEqual(['1', '58']);
    expect(a.get('58')![0]).toMatchObject({ kind: '3D model', title: 'Mini Cooper S', author: 'cenobyte', licence: 'CC-BY-4.0', note: 'decimated' });
    const b = carCreditsFrom(decals, 'Decal image');
    expect(b.get('38')!.length).toBe(4);
    const c = carCreditsFrom([{ number: 7, title: 'T', author: 'Z' }, { car: '8', url: 'https://u' }], '3D model');
    expect([...c.keys()]).toEqual(['7', '8']);
    expect(carCreditsFrom(null, 'x').size).toBe(0);
    expect(carCreditsFrom('garbage', 'x').size).toBe(0);
  });

  it('merges by car number and source: duplicates dropped, numeric order, team names', () => {
    const m = mergeCarCredits([carCreditsFrom(importer, '3D model'), carCreditsFrom(decals, 'Decal image'), carCreditsFrom(importer, '3D model')], { '38': 'Kim Jong Il Racing' });
    expect(m.map((c) => c.number)).toEqual(['1', '38', '58']);
    const c38 = m.find((c) => c.number === '38')!;
    expect(c38.team).toBe('Kim Jong Il Racing');
    expect(c38.lines.length).toBe(2); // the face and frame share a source; the flag is listed once
    const c58 = m.find((c) => c.number === '58')!;
    expect(c58.lines.map((l) => l.kind)).toEqual(['3D model', 'Decal image']); // both files merged into one car
    expect(m.find((c) => c.number === '1')!.lines.length).toBe(1);   // the importer file twice: no duplicates
  });

  it('engine-sound sources from the index and each family engine.json, deduplicated, skipped sources left out', () => {
    const index = { families: { fam_a: { engine: 'fam_a/engine.json', character: 'loud four', sources: [{ url: 'https://yt/1', title: 'One' }] }, fam_b: { engine: 'fam_b/engine.json' }, fam_c: { engine: 'x' } } };
    const engines = {
      fam_a: { sources: [{ url: 'https://yt/1', title: 'One' }, { url: 'https://yt/2', title: 'Two', licence: 'CC BY 3.0', uploader: 'U' }] },
      fam_b: { sources: [{ url: 'https://yt/3', title: 'Three', skip: true }, { url: 'https://yt/4', title: 'Four' }] },
    };
    const a = audioCreditsFrom(index, engines);
    expect(a.map((x) => x.family)).toEqual(['fam_a', 'fam_b']);
    expect(a[0].character).toBe('loud four');
    expect(a[0].lines.map((l) => l.url)).toEqual(['https://yt/1', 'https://yt/2']);
    expect(a[0].lines[1]).toMatchObject({ author: 'U', licence: 'CC BY 3.0' });
    expect(a[1].lines.map((l) => l.title)).toEqual(['Four']);
    expect(audioCreditsFrom(null)).toEqual([]);
  });

  it('loads everything, tolerating a missing file, and always has the photo line', async () => {
    const files: Record<string, unknown> = {
      'cars/field/credits.json': importer,
      'audio/families/index.json': { base: 'audio/families/', families: { fam_a: { engine: 'fam_a/engine.json' } } },
      'audio/families/fam_a/engine.json': { sources: [{ url: 'https://yt/9', title: 'Nine' }] },
      'cars/field/identity.json': [{ number: '58', team: 'Brits' }],
    };
    const f = async (u: string) => (u in files ? { ok: true, json: async () => files[u] } : { ok: false, json: async () => null });
    const d = await loadCredits(f);
    expect(d.cars.map((c) => c.number)).toEqual(['1', '58']);
    expect(d.cars[1].team).toBe('Brits');
    expect(d.audio[0].lines[0].title).toBe('Nine');
    expect(d.photos).toBe(PHOTO_CREDITS);
    expect(PHOTO_CREDITS[0].title).toBe('Twenty Ridiculous Years at Laguna');
    expect(d.about[0]).toMatch(/3D models/);
    expect(teamsFrom({ cars: [{ number: '3', team: 'T' }] })).toEqual({ '3': 'T' });
  });
});

describe('race menu label', () => {
  it('reflects the configured lap count, ?laps= included', () => {
    expect(raceMenuLabel('')).toBe('Race · 5 laps vs the 2026 field');
    expect(raceMenuLabel('?laps=3')).toBe('Race · 3 laps vs the 2026 field');
    expect(raceMenuLabel('?seed=5&laps=1')).toBe('Race · 1 lap vs the 2026 field');
    expect(raceMenuLabel('?laps=99')).toBe('Race · 5 laps vs the 2026 field'); // out of range: ignored
  });
});

describe('result statuses', () => {
  it('maps player / out / ejected / flag to one status', () => {
    expect(rowStatus({ player: true, out: false, ejected: false, flagged: false })).toBe('running');
    expect(rowStatus({ player: true, out: false, ejected: false, flagged: true })).toBe('finished');
    expect(rowStatus({ player: true, out: true, ejected: false, flagged: true })).toBe('out');
    expect(rowStatus({ player: true, out: false, ejected: true, flagged: true })).toBe('ejected');
    expect(rowStatus({ player: false, out: true, ejected: true, flagged: true })).toBe('finished'); // the player's state never leaks to AI rows
    expect(rowStatus({ player: false, out: false, ejected: false, flagged: false })).toBe('running');
  });
  it('the results table reads "finished" (or "out") at the flag, and the scoreboard still sees a finished race', () => {
    const rows: ResultRow[] = [
      // the player completed every lap (a race time): "finished" on the scoreboard means all laps done, ranked by that time
      { position: 1, number: '711', team: 'Eyesore', class: 'A', metres: 36_020, laps: 10, lapsCompleted: 10, bestLap: 108, time: 1130.2, status: 'running', player: false },
      { position: 2, number: '619', team: 'Probe', class: 'B', metres: 35_611, laps: 10.0, lapsCompleted: 10, bestLap: 121, time: 1180.5, status: 'running', player: true },
      { position: 3, number: '20', team: 'NSF', class: 'C', metres: 30_000, laps: 8.3, lapsCompleted: 8, bestLap: 150, time: null, status: 'running', player: false },
    ];
    const r = resultRows(rows, null);
    expect(r.map((x) => x.status)).toEqual(['finished', 'finished', 'finished']);
    expect(raceResultFor(r, { seed: 1, aiVersion: 2, finished: true })!.finished).toBe(true);
    const out = resultRows(rows, { metres: 5000 });
    expect(out.find((x) => x.player)!.status).toBe('out');
    expect(raceResultFor(out, { seed: 1, aiVersion: 2, finished: true })!.finished).toBe(false);
    const ej = resultRows(rows.map((x) => (x.player ? { ...x, status: 'ejected' as const } : x)), null);
    expect(ej.find((x) => x.player)!.status).toBe('ejected');
  });
});

describe('placeholder number boards', () => {
  it('stay within 400 triangles and use a board that contrasts with the body', () => {
    for (const dims of [PROBE_DIMS, { ...PROBE_DIMS, length: 3.4, width: 1.5, height: 1.25, wheelbase: 2.05, tyreRadius: 0.27 }, { ...PROBE_DIMS, length: 5.3, width: 1.95, height: 1.4, wheelbase: 3.0 }]) {
      const car = buildPlaceholderCar('801', '#ffffff', dims, null);
      expect(triangleCount(car)).toBeLessThanOrEqual(400);
      // the door board (the first plane of the merged boards) fills most of the height below the belt line
      const pos = (car.getObjectByName('number_boards') as THREE.Mesh).geometry.attributes.position;
      const ys = [0, 1, 2, 3].map((i) => pos.getY(i));
      expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(0.3);
    }
    expect(boardColor('#ffffff')).toBe('#121417'); // light body → dark board
    expect(boardColor('#f2c230')).toBe('#121417');
    expect(boardColor('#1a2b8c')).toBe('#f6f6f2'); // dark body → light board
    expect(boardColor('red')).toBe('#f6f6f2');
  });
});
