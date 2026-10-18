import { describe, expect, it } from 'vitest';
import { crossesPolyline, distanceToPolyline, PitExitCones } from '../trackmath';

const line: [number, number][] = [[0, 0], [10, 0], [20, 5], [30, 5]];

describe('crossesPolyline', () => {
  it('detects a segment crossing any piece of the line', () => {
    expect(crossesPolyline([5, -1], [5, 1], line)).toBe(true);
    expect(crossesPolyline([15, 0], [15, 5], line)).toBe(true);
    expect(crossesPolyline([25, 6], [25, 4], line)).toBe(true);
  });
  it('ignores segments on one side, parallel, or beyond the ends', () => {
    expect(crossesPolyline([5, 1], [8, 2], line)).toBe(false);
    expect(crossesPolyline([0, 1], [10, 1], line)).toBe(false);
    expect(crossesPolyline([-5, -1], [-5, 1], line)).toBe(false);
    expect(crossesPolyline([35, 4], [35, 6], line)).toBe(false);
  });
  it('counts touching the line', () => {
    expect(crossesPolyline([5, -1], [5, 0], line)).toBe(true);
  });
  it('handles empty and single-point lines', () => {
    expect(crossesPolyline([0, -1], [0, 1], [])).toBe(false);
    expect(crossesPolyline([0, -1], [0, 1], [[0, 0]])).toBe(false);
  });
});

describe('distanceToPolyline', () => {
  it('is the perpendicular distance to the nearest piece', () => {
    expect(distanceToPolyline([5, 3], line)).toBeCloseTo(3);
    expect(distanceToPolyline([-4, 3], line)).toBeCloseTo(5);
  });
});

describe('PitExitCones', () => {
  const cones = () => new PitExitCones({ pts: line.map(([x, y]) => [x, y, 0] as [number, number, number]) });
  const drive = (c: PitExitCones, pts: [number, number][]) => pts.filter(([x, y]) => c.update(x, y)).length;

  it('reports nothing while driving alongside', () => {
    const c = cones();
    expect(drive(c, Array.from({ length: 30 }, (_, i) => [i, -2] as [number, number]))).toBe(0);
  });
  it('one crossing is one event, crossing straight back does not count again', () => {
    const c = cones();
    expect(drive(c, [[5, -2], [5, -0.5], [5, 0.5], [5, 1.5], [5, 0.5], [5, -0.5], [5, -2]])).toBe(1);
    expect(c.count).toBe(1);
  });
  it('re-arms once the car is clear of the line', () => {
    const c = cones();
    expect(drive(c, [[5, -2], [5, 2], [5, 6], [6, 6], [6, -1]])).toBe(2);
  });
  it('ignores teleports and the first sample after clear()', () => {
    const c = cones();
    expect(drive(c, [[5, -50], [5, 50]])).toBe(0);
    c.update(5, -1);
    c.clear();
    expect(c.update(5, 1)).toBe(false);
  });
});
