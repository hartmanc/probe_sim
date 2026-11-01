import { describe, expect, it } from 'vitest';
import {
  awardClass, cardFor, viewFit, projectBox, relativeYawDeg, DEFAULT_ELEVATION, clearAreaShift, classifyGesture, stripLines, classSizes, fitPlane, seatOffset, creditFor, engineAt, fieldSize, indexByNumber, lapText, makeBlip, ordinal, safeUrl, viewerOrder,
  CRANK_END, REV_RPM, SETTLE_END, type AwardEntry, type IdentityRow,
} from '../car-viewer-data';

const row = (number: string, finish: number, extra: Partial<IdentityRow> = {}): IdentityRow => ({ number, team: `T${number}`, class: 'A', finish, class_finish: finish, laps: 100 - finish, best_lap_s: 100 + finish, make: 'Mazda', model: 'Miata', year: 1994, ...extra });
const field: IdentityRow[] = [row('1', 1), row('2', 2), row('3', 3, { id: '3_x' }), row('4', 4), row('5', 5), row('619', 7), row('9', 6)];

describe('awardClass', () => {
  it('reads the verbatim award names', () => {
    expect(awardClass('Winner on Index of Effluency')).toBe('index');
    expect(awardClass('Winner, Class B (The Bad)')).toBe('B');
    expect(awardClass('Winner on Laps')).toBe('other');
    expect(awardClass("Judges' Choice")).toBe('other');
  });
});

describe('viewerOrder', () => {
  const awards: AwardEntry[] = [
    { number: '1', id: '1', awards: ['Winner on Laps', 'Winner, Class A (The Good)'] },
    { number: '3', id: '3_x', awards: ['Winner on Index of Effluency'] },
    { number: '4', id: '4', awards: ['Winner, Class C (The Ugly)'] },
    { number: '2', id: '2', awards: ['Winner, Class B (The Bad)'] },
    { number: '9', id: '9', awards: ["Judges' Choice"] },
    { number: '5', id: '5', awards: ['Heroic Fix'] },
  ];
  it('index winner, class winners A B C, other winners in page order, then finishing order', () => {
    const { cars, skipped } = viewerOrder(field, awards, () => true);
    expect(cars.map((c) => c.key)).toEqual(['3_x', '1', '2', '4', '9', '5', '619']);
    expect(skipped).toBe(0);
    expect(cars[1].awards).toEqual(['Winner on Laps', 'Winner, Class A (The Good)']);
  });
  it('puts the Probe at its finishing place and skips cars without a model', () => {
    const { cars, skipped } = viewerOrder(field, [], (k) => k !== '2');
    expect(cars.map((c) => c.key)).toEqual(['1', '3_x', '4', '5', '9', '619']);
    expect(skipped).toBe(1);
  });
  it('ignores award entries for cars that are not in the field', () => {
    const { cars } = viewerOrder(field, [{ number: '77', id: '77', awards: ['Winner on Index of Effluency'] }], () => true);
    expect(cars.length).toBe(7);
    expect(cars[0].key).toBe('1');
  });
  it('a car without a finishing place goes last', () => {
    const f = [row('1', 0), row('2', 5), row('3', 1)];
    expect(viewerOrder(f, [], () => true).cars.map((c) => c.key)).toEqual(['3', '2', '1']);
  });
});

describe('typed numbers', () => {
  it('jumps to the car with that number', () => {
    const { cars } = viewerOrder(field, [], () => true);
    expect(indexByNumber(cars, '619')).toBe(cars.findIndex((c) => c.key === '619'));
    expect(indexByNumber(cars, '61')).toBe(-1);
    expect(indexByNumber(cars, '')).toBe(-1);
  });
});

describe('card text', () => {
  it('formats laps and ordinals', () => {
    expect(lapText(108.15)).toBe('1:48.150');
    expect(lapText(59.0004)).toBe('0:59.000');
    expect(lapText(0)).toBe('–');
    expect([1, 2, 3, 4, 11, 12, 13, 21, 22, 103].map(ordinal)).toEqual(['1st', '2nd', '3rd', '4th', '11th', '12th', '13th', '21st', '22nd', '103rd']);
  });
  it('builds the card', () => {
    const { cars } = viewerOrder(field, [], () => true);
    const c = cardFor(cars[6], 6, 7, fieldSize(field), { title: 'Probe', author: 'A', licence: 'CC-BY-4.0', licence_url: 'https://x/l', url: 'https://x/m', changes: 'recoloured' },
      [{ file: 'a.jpg', page_url: 'https://p/1' }, { file: 'owner_b.jpg', owner: true }, { file: 'c.jpg', page_url: 'https://p/2' }], classSizes(field));
    expect(c).toMatchObject({ position: '7 / 7', number: '619', car: '1994 Mazda Miata', overall: 'P7 of 7', classRank: 'P7 of 7 in A', laps: '93', fastest: '1:47.000' });
    expect(c.model).toMatchObject({ text: 'Model', title: 'Probe', titleUrl: 'https://x/m', licence: 'CC-BY-4.0' });
    expect(c.photos).toEqual([{ n: 1, url: 'https://p/1' }, { n: 2, url: 'https://p/2' }]);
    expect(c.ownerPhotos).toBe(1);
  });
  it('built-for-the-sim cars have no credit; missing finish and class read as a dash', () => {
    const car = { key: 'x', row: { ...row('8', 0), class: '', class_finish: null, best_lap_s: 0 }, awards: [] };
    const c = cardFor(car, 0, 1, 10, null, undefined);
    expect(c.model.text).toBe('Built for the sim');
    expect([c.overall, c.classRank, c.fastest]).toEqual(['–', '–', '–']);
    expect(c.photos).toEqual([]);
  });
  it('field size is the larger of the entry list and the last finishing place', () => {
    expect(fieldSize([row('1', 1), row('2', 140)])).toBe(140);
  });
  it('finds credits in a dict or a list, and only http links are links', () => {
    expect(creditFor({ '1': { title: 'a' } }, '1')).toEqual({ title: 'a' });
    expect(creditFor([{ id: '2', title: 'b' }], '2')).toMatchObject({ title: 'b' });
    expect(creditFor({}, '3')).toBeNull();
    expect(safeUrl('https://a.b/c')).toBe('https://a.b/c');
    expect(safeUrl('javascript:alert(1)')).toBeNull();
  });
});

describe('scripted engine', () => {
  it('cranks, catches, revs to 3000 and settles to idle', () => {
    expect(engineAt(-1, 800, []).rpm).toBe(0);
    expect(engineAt(0.5, 800, []).rpm).toBeLessThan(400);
    expect(engineAt(CRANK_END + 0.01, 800, []).throttle).toBeGreaterThan(0);
    expect(engineAt(2.0, 800, []).rpm).toBe(REV_RPM);
    expect(engineAt(SETTLE_END, 800, []).rpm).toBeCloseTo(800, 5);
    expect(engineAt(20, 800, []).rpm).toBe(800);
  });
  it('blips lift the rpm and come back', () => {
    const blips = [{ t0: 10, peak: 3000, rise: 0.2, fall: 0.6 }];
    expect(engineAt(10.2, 800, blips).rpm).toBeCloseTo(3000, 5);
    expect(engineAt(10.1, 800, blips).throttle).toBeGreaterThan(0.4);
    expect(engineAt(11.5, 800, blips).rpm).toBe(800);
  });
  it('random blips start 0.5 to 1.5 s after the end of the last, peak 2000 to 4000, and differ', () => {
    const lo = makeBlip(10, () => 0), hi = makeBlip(10, () => 1);
    expect([lo.t0, hi.t0]).toEqual([10.5, 11.5]);
    expect([lo.peak, hi.peak]).toEqual([2000, 4000]);
    let n = 0; const r = () => ((n = (n * 7 + 3) % 11) / 11);
    expect(makeBlip(0, r)).not.toEqual(makeBlip(0, r));
  });
});

describe('parking on a cambered road', () => {
  it('fits a plane through four contacts and seats the lowest one on the surface', () => {
    // 2.6 m wheelbase, 1.5 m track; the road rises 2 % to the front and 3 % to the left
    const z = (u: number, v: number) => 10 + 0.02 * u + 0.03 * v;
    const pts: [number, number, number][] = [[1.3, 0.75, z(1.3, 0.75)], [1.3, -0.75, z(1.3, -0.75)], [-1.3, 0.75, z(-1.3, 0.75)], [-1.3, -0.75, z(-1.3, -0.75)]];
    const f = fitPlane(pts);
    expect([f.a, f.b, f.c].map((x) => +x.toFixed(6))).toEqual([10, 0.02, 0.03]);
    expect(Math.max(...f.residuals.map(Math.abs))).toBeLessThan(1e-9);
    // a bump under one wheel: that plane is lifted by the smallest residual, so the lowest wheel just touches
    const bumpy = fitPlane([[1.3, 0.75, 10.05], [1.3, -0.75, 10], [-1.3, 0.75, 10], [-1.3, -0.75, 10]]);
    const off = seatOffset(bumpy);
    expect(Math.min(...bumpy.residuals.map((r) => r - off))).toBeCloseTo(0, 12);
    expect(off).toBeLessThan(0);
  });
});

describe('touch gestures', () => {
  const track = (pts: [number, number, number][]) => pts.map(([t, x, y]) => ({ t, x, y }));
  it('a quick horizontal flick pages: left is next, right is previous', () => {
    expect(classifyGesture([track([[0, 300, 200], [60, 270, 204], [120, 230, 205]])])).toBe('next');
    expect(classifyGesture([track([[0, 100, 200], [80, 150, 198], [160, 190, 200]])])).toBe('prev');
  });
  it('a short very fast flick counts by speed', () => {
    expect(classifyGesture([track([[0, 300, 200], [40, 265, 200]])])).toBe('next');
  });
  it('a slow drag orbits, however far', () => {
    expect(classifyGesture([track([[0, 100, 200], [400, 160, 200], [900, 260, 200]])])).toBe('orbit');
  });
  it('a diagonal drag orbits, a tap does not page', () => {
    expect(classifyGesture([track([[0, 100, 100], [100, 170, 160]])])).toBe('orbit');
    expect(classifyGesture([track([[0, 100, 100], [30, 104, 101]])])).toBe('orbit');
  });
  it('two fingers (a pinch) never page', () => {
    expect(classifyGesture([track([[0, 100, 200], [100, 40, 200]]), track([[0, 300, 200], [100, 360, 200]])])).toBe('orbit');
  });
  it('the strip lines for a phone', () => {
    const [l1, l2] = stripLines({ number: '20', team: 'NSF Racing', car: '1985 Chrysler LeBaron Town & Country wagon', cls: 'C', overall: 'P33 of 45', classRank: 'P16 of 27 in C', laps: '116', fastest: '2:38.495' });
    expect(l1).toBe('#20 NSF Racing · 1985 Chrysler LeBaron Town & Country wagon · Class C');
    expect(l2).toBe('P33 of 45 · P16 of 27 in C · 116 laps · 2:38.495');
  });
});

describe('the camera fit on a phone', () => {
  const STRIP = 56, TITLE = 50, CHEV = 28;
  it('desktop and tablet keep 7.5 m and no shift', () => {
    expect(viewFit(false, 1280, 720, 0, 0, 0)).toEqual({ distance: 7.5, shiftPx: 0 });
    expect(viewFit(false, 844, 390, STRIP, TITLE, CHEV, 90)).toEqual({ distance: 7.5, shiftPx: 0 });
  });
  for (const [w, h] of [[844, 316], [844, 390]]) {
    it(`${w}x${h}: at every angle the box is inside the clear area with 4 % to spare and fills it`, () => {
      const clearH = h - STRIP - TITLE, clearW = w - 2 * CHEV;
      for (const yaw of [0, 30, 45, 60, 90]) {
        const f = viewFit(true, w, h, STRIP, TITLE, CHEV, yaw);
        const e = projectBox(f.distance, DEFAULT_ELEVATION, yaw, w / h);
        const top = h / 2 - (e.y1 * h) / 2 - f.shiftPx, bottom = h / 2 - (e.y0 * h) / 2 - f.shiftPx;
        expect(top).toBeGreaterThanOrEqual(TITLE + 0.04 * clearH);
        expect(bottom).toBeLessThanOrEqual(h - STRIP - 0.04 * clearH);
        const bw = ((e.x1 - e.x0) * w) / 2, bh = ((e.y1 - e.y0) * h) / 2;
        expect(bw).toBeLessThanOrEqual(0.85 * clearW + 1e-6);
        expect(bh).toBeLessThanOrEqual(0.78 * clearH + 1e-6);
        expect(bh >= 0.7 * clearH || bw >= 0.8 * clearW).toBe(true);   // the car is actually big
      }
    });
  }
  it('is continuous in the angle and nearer the more side-on it is', () => {
    const a = viewFit(true, 844, 316, STRIP, TITLE, CHEV, 44).distance, b = viewFit(true, 844, 316, STRIP, TITLE, CHEV, 46).distance;
    expect(Math.abs(a - b) / a).toBeLessThan(0.03);
    expect(viewFit(true, 844, 316, STRIP, TITLE, CHEV, 0).distance).not.toBeCloseTo(viewFit(true, 844, 316, STRIP, TITLE, CHEV, 90).distance, 1);
  });
  it('the relative yaw: 0 side-on, 90 end-on, folded over the car being symmetric', () => {
    expect(relativeYawDeg(Math.PI / 2, 0)).toBeCloseTo(0, 6);
    expect(relativeYawDeg(0, 0)).toBeCloseTo(90, 6);
    expect(relativeYawDeg(Math.PI, 0)).toBeCloseTo(90, 6);
    expect(relativeYawDeg(-Math.PI / 2, 0)).toBeCloseTo(0, 6);
    expect(relativeYawDeg(0.75, 0)).toBeCloseTo(47.0, 0);
  });
  it('a narrow tall viewport is fitted by its width', () => {
    const f = viewFit(true, 390, 844, 90, 50, CHEV, 0);
    const e = projectBox(f.distance, DEFAULT_ELEVATION, 0, 390 / 844);
    expect(((e.x1 - e.x0) * 390) / 2).toBeLessThanOrEqual(0.85 * (390 - 2 * CHEV) + 1e-6);
  });
  it('the clear-area shift stays available', () => {
    expect(clearAreaShift(56, 50)).toBe(3);
    expect(clearAreaShift(40, 60)).toBe(-10);
  });
});
