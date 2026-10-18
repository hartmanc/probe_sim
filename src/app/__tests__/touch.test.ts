import { describe, expect, it } from 'vitest';
import {
  PEDAL_DEAD, PEDAL_FULL, TILT_FULL_DEG, effectiveSteer, hitZone, lowPass, pedalFromHeight, pedalFromY, sliderSteer,
  tiltAngle, tiltInitial, tiltNext, tiltSteer, wrapAngle, type TiltEvent, type TiltState,
} from '../touch';

const D = Math.PI / 180;

describe('zones', () => {
  const W = 844, H = 390;
  it('brake left third, throttle right third', () => {
    expect(hitZone(10, 200, W, H, 'tilt')).toBe('brake');
    expect(hitZone(W / 3 - 1, 10, W, H, 'tilt')).toBe('brake');
    expect(hitZone((2 * W) / 3, 10, W, H, 'tilt')).toBe('throttle');
    expect(hitZone(W - 1, 380, W, H, 'slider')).toBe('throttle');
  });
  it('middle third steers only in slider mode', () => {
    expect(hitZone(W / 2, 200, W, H, 'slider')).toBe('steer');
    expect(hitZone(W / 2, 200, W, H, 'tilt')).toBeNull();
    expect(hitZone(5, 5, 0, H, 'slider')).toBeNull();
  });
});

describe('pedal mapping', () => {
  it('dead band at the bottom, full near the top, monotonic', () => {
    expect(pedalFromHeight(0)).toBe(0);
    expect(pedalFromHeight(PEDAL_DEAD)).toBe(0);
    expect(pedalFromHeight(PEDAL_DEAD + 0.01)).toBeGreaterThan(0);
    expect(pedalFromHeight(PEDAL_FULL)).toBe(1);
    expect(pedalFromHeight(1)).toBe(1);
    expect(pedalFromHeight(NaN)).toBe(0);
    let prev = -1;
    for (let u = 0; u <= 1; u += 0.01) { const v = pedalFromHeight(u); expect(v).toBeGreaterThanOrEqual(prev); prev = v; }
  });
  it('from screen y (y grows down)', () => {
    expect(pedalFromY(390, 0, 390)).toBe(0);
    expect(pedalFromY(0, 0, 390)).toBe(1);
    expect(pedalFromY(195, 0, 390)).toBeCloseTo((0.5 - PEDAL_DEAD) / (PEDAL_FULL - PEDAL_DEAD), 6);
    expect(pedalFromY(100, 50, 50)).toBe(0);
  });
});

describe('slider steering', () => {
  it('centre 0, left positive, clamped', () => {
    expect(sliderSteer(422, 281, 563)).toBeCloseTo(0, 6);
    expect(sliderSteer(300, 281, 563)).toBeGreaterThan(0.8);
    expect(sliderSteer(281, 281, 563)).toBe(1);
    expect(sliderSteer(563, 281, 563)).toBe(-1);
    expect(sliderSteer(10, 281, 563)).toBe(1);
  });
});

/** beta / gamma (deg) of a phone held upright-ish in landscape (top edge to the left), tipped back `tip` deg
 *  from vertical and rotated `wheel` deg counter-clockwise (steering left). */
function pose(wheelDeg: number, tipDeg: number): { beta: number; gamma: number } {
  // build "down" in device coords: screen-plane part rotated by the wheel, plus the tip toward -z
  const c = Math.cos(tipDeg * D), s = Math.sin(tipDeg * D);
  // screen coords (right, up) of down: level = (0, -1); wheel left by θ → (-sinθ, -cosθ)
  const sx = -Math.sin(wheelDeg * D) * c, sy = -Math.cos(wheelDeg * D) * c;
  // landscape top-left: screen right = device -y, screen up = device +x
  const dx = sy, dy = -sx, dz = -s;
  // down = (cosβ sinγ, -sinβ, -cosβ cosγ)
  const beta = Math.asin(-dy) / D;
  const gamma = Math.atan2(dx, -dz) / D;
  return { beta, gamma };
}

describe('tilt mapping', () => {
  it('level wheel reads 0 whatever the tip-back angle', () => {
    for (const tip of [5, 30, 60]) {
      const p = pose(0, tip);
      expect(tiltAngle(p.beta, p.gamma, 90)).toBeCloseTo(0, 6);
    }
  });
  it('rotating the phone counter-clockwise steers left (+), independent of the tip', () => {
    for (const tip of [10, 40, 70]) {
      const p = pose(20, tip);
      expect(tiltAngle(p.beta, p.gamma, 90) / D).toBeCloseTo(20, 4);
      const q = pose(-15, tip);
      expect(tiltAngle(q.beta, q.gamma, 90) / D).toBeCloseTo(-15, 4);
    }
  });
  it('the other landscape side mirrors', () => {
    // top edge to the right: device -x up; mirror x
    const p = pose(20, 30);
    const flipped = { beta: -p.beta, gamma: -p.gamma }; // rotate the device 180° about its z axis
    expect(tiltAngle(flipped.beta, flipped.gamma, -90) / D).toBeCloseTo(20, 4);
  });
  it('steer: offset, dead zone, sensitivity, clamp', () => {
    expect(tiltSteer(0.5 * D, 0, 1)).toBe(0);
    expect(tiltSteer(10 * D, 10 * D, 1)).toBe(0);
    expect(tiltSteer(TILT_FULL_DEG * D, 0, 1)).toBeCloseTo(1, 6);
    expect(tiltSteer(-TILT_FULL_DEG * D, 0, 1)).toBeCloseTo(-1, 6);
    expect(tiltSteer(90 * D, 0, 1)).toBe(1);
    const half = tiltSteer(16 * D, 0, 1), sens = tiltSteer(16 * D, 0, 2);
    expect(sens).toBeGreaterThan(half);
    expect(tiltSteer(20 * D, 5 * D, 1)).toBeCloseTo(tiltSteer(15 * D, 0, 1), 9);
  });
  it('wraps across ±180°', () => {
    expect(wrapAngle(3 * Math.PI)).toBeCloseTo(Math.PI, 9);
    expect(tiltSteer(179 * D, -179 * D, 1)).toBeCloseTo(tiltSteer(-2 * D, 0, 1), 9);
  });
  it('low-pass: ~15 Hz corner, no change at dt 0', () => {
    expect(lowPass(0, 1, 0)).toBe(0);
    const k = lowPass(0, 1, 1 / 60);
    expect(k).toBeGreaterThan(0.75);
    expect(k).toBeLessThan(0.85);
    let y = 0;
    for (let i = 0; i < 30; i++) y = lowPass(y, 1, 1 / 60);
    expect(y).toBeCloseTo(1, 6);
  });
});

describe('tilt permission state machine', () => {
  const run = (s: TiltState, evs: TiltEvent[]) => evs.reduce(tiltNext, s);
  it('initial state', () => {
    expect(tiltInitial({ hasEvent: true, needsPermission: true, secure: true })).toBe('prompt');
    expect(tiltInitial({ hasEvent: true, needsPermission: true, secure: false })).toBe('unsupported');
    expect(tiltInitial({ hasEvent: true, needsPermission: false, secure: true })).toBe('granted');
    expect(tiltInitial({ hasEvent: false, needsPermission: false, secure: true })).toBe('unsupported');
  });
  it('iOS: prompt → requesting → granted → active', () => {
    expect(run('prompt', ['request'])).toBe('requesting');
    expect(run('prompt', ['request', 'grant'])).toBe('granted');
    expect(run('prompt', ['request', 'grant', 'reading'])).toBe('active');
    expect(run('prompt', ['grant', 'reading'])).toBe('prompt'); // nothing without a request
  });
  it('denied, retry', () => {
    expect(run('prompt', ['request', 'deny'])).toBe('denied');
    expect(run('prompt', ['request', 'deny', 'request', 'grant'])).toBe('granted');
  });
  it('granted but silent (no sensor), later readings revive it', () => {
    expect(run('granted', ['timeout'])).toBe('silent');
    expect(run('granted', ['timeout', 'reading'])).toBe('active');
    expect(run('active', ['timeout', 'deny'])).toBe('active');
  });
  it('unsupported stays unsupported', () => {
    expect(run('unsupported', ['request', 'grant', 'reading'])).toBe('unsupported');
  });
  it('tilt is used only while active; slider otherwise', () => {
    expect(effectiveSteer('tilt', 'active')).toBe('tilt');
    for (const s of ['unsupported', 'prompt', 'requesting', 'granted', 'silent', 'denied'] as TiltState[]) expect(effectiveSteer('tilt', s)).toBe('slider');
    expect(effectiveSteer('slider', 'active')).toBe('slider');
  });
});
