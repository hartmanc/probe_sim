import { describe, expect, it } from 'vitest';
import {
  DRIVER_VIEW_DEFAULTS, EYE_RANGE, FOV_CHOICES, LOOK, VFOV_CAP, parseDriverView, stepLookAngle, verticalFov,
} from '../cameras';

const vf = (h: number, a: number) => (2 * Math.atan(Math.tan((h * Math.PI) / 360) / a) * 180) / Math.PI;

describe('field of view', () => {
  it('holds the horizontal FOV across aspect ratios', () => {
    expect(verticalFov(90, 16 / 9)).toBeCloseTo(vf(90, 16 / 9), 6); // 58.7°
    expect(verticalFov(90, 2.16)).toBeCloseTo(vf(90, 2.16), 6);     // phone landscape: narrower vertical
    expect(verticalFov(90, 2.16)).toBeLessThan(verticalFov(90, 16 / 9));
  });
  it('caps the vertical FOV in near-square and portrait windows', () => {
    const cap = vf(90, 16 / 9) * VFOV_CAP;
    expect(verticalFov(90, 1)).toBeCloseTo(cap, 6);
    expect(verticalFov(90, 0.5)).toBeCloseTo(cap, 6);
    expect(verticalFov(90, 1)).toBeLessThan(70); // the old fixed vertical 70° filled a square frame with headliner
  });
});

describe('driver view settings', () => {
  it('defaults when nothing or garbage is stored', () => {
    expect(parseDriverView(null)).toEqual(DRIVER_VIEW_DEFAULTS);
    expect(parseDriverView('{oops')).toEqual(DRIVER_VIEW_DEFAULTS);
    expect(parseDriverView(JSON.stringify({ eyeY: 'high' })).eyeY).toBe(DRIVER_VIEW_DEFAULTS.eyeY);
  });
  it('clamps stored values', () => {
    const v = parseDriverView(JSON.stringify({ eyeY: 2, seatZ: -0.05, fov: 500 }));
    expect(v.eyeY).toBe(EYE_RANGE[1]);
    expect(v.seatZ).toBe(-0.05);
    expect(v.fov).toBe(FOV_CHOICES[FOV_CHOICES.length - 1]);
  });
});

describe('look-around spring', () => {
  const run = (from: number, to: number, t: number) => { let a = from; for (let i = 0; i < t * 120; i++) a = stepLookAngle(a, to, 1 / 120); return a; };
  it('moves out quickly and springs back more slowly, rate limited', () => {
    expect(run(0, LOOK.yaw, 0.35)).toBeGreaterThan(LOOK.yaw * 0.95);
    const back = run(LOOK.yaw, 0, 0.2);
    expect(back).toBeGreaterThan(LOOK.yaw * 0.5);         // not snappy
    expect(LOOK.yaw - back).toBeLessThanOrEqual(4.5 * 0.2 + 1e-9); // ≤ 4.5 rad/s
    expect(run(LOOK.yaw, 0, 1.5)).toBeLessThan(0.01);      // but it does come home
  });
  it('a reversal counts as springing back through the centre', () => {
    const a = stepLookAngle(1, -1, 0.1);
    expect(1 - a).toBeLessThanOrEqual(0.45 + 1e-9);
  });
});
