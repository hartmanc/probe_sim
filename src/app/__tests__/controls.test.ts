import { describe, expect, it } from 'vitest';
import {
  SourceTracker, applyPedal, applySteer, defaultKeyBindings, defaultPadProfile, helpRows, parseKeyBindings, parsePadProfile, readPadProfile,
  serializePadProfile, shape, triggerAxisToPedal,
} from '../controls';

describe('response shaping', () => {
  it('applies deadzone and exponent', () => {
    expect(shape(0.05, 0.08, 1)).toBe(0);
    expect(shape(1, 0.08, 1.7)).toBeCloseTo(1);
    expect(shape(0.5, 0, 2)).toBeCloseTo(0.25);
  });
  it('defaults: steer 1.3, throttle 1.0, brake 1.4', () => {
    const p = defaultPadProfile();
    expect([p.cal.steer.expo, p.cal.throttle.expo, p.cal.brake.expo]).toEqual([1.3, 1.0, 1.4]);
  });
  it('brake is progressive: half trigger is well under half brake', () => {
    const c = defaultPadProfile().cal.brake;
    const v = applyPedal(0.5, c);
    expect(v).toBeGreaterThan(0.25);
    expect(v).toBeLessThan(0.45);
  });
  it('steer uses captured extremes and sign', () => {
    const c = { ...defaultPadProfile().cal.steer, min: -0.8, max: 0.9, deadzone: 0, expo: 1 };
    expect(applySteer(0.9, c)).toBeCloseTo(1);
    expect(applySteer(-0.8, c)).toBeCloseTo(-1);
    expect(applySteer(0.45, { ...c, invert: true })).toBeCloseTo(-0.5);
  });
  it('maps a −1..1 trigger axis to 0..1', () => {
    expect(triggerAxisToPedal(-1, true)).toBe(0);
    expect(triggerAxisToPedal(0, true)).toBe(0.5);
    expect(triggerAxisToPedal(1, true)).toBe(1);
    const c = { ...defaultPadProfile().cal.throttle, min: -1, max: 1, deadzone: 0, expo: 1 };
    expect(applyPedal(0, c)).toBeCloseTo(0.5);
  });
});

describe('analog detection', () => {
  it('flags digital sources and stale pressed triggers', () => {
    const t = new SourceTracker();
    t.observe('b7', 1);
    expect(t.isArmed('b7')).toBe(false);   // read pressed from the first sample: not trusted
    expect(t.isAnalog('b7')).toBe(false);
    t.observe('b7', 0);
    t.observe('b7', 1);
    expect(t.isArmed('b7')).toBe(true);
    expect(t.isAnalog('b7')).toBe(false);  // only 0/1 so far: digital, ramped
    t.observe('b7', 0.42);
    expect(t.isAnalog('b7')).toBe(true);
  });
});

describe('persistence parsing', () => {
  it('falls back to defaults on junk', () => {
    expect(parsePadProfile('not json')).toEqual(defaultPadProfile());
    expect(parseKeyBindings('{"brake": 5}')).toEqual(defaultKeyBindings());
  });
  it('round-trips a remap and clamps calibration', () => {
    const p = defaultPadProfile();
    p.pad.brake = { kind: 'axis', index: 2, sign: 1 };
    p.cal.brake.expo = 9;
    const q = parsePadProfile(JSON.stringify(p));
    expect(q.pad.brake).toEqual({ kind: 'axis', index: 2, sign: 1 });
    expect(q.cal.brake.expo).toBe(2.5);
  });
  it('never lets steer bind to a button and keeps reserved keys out', () => {
    const q = parsePadProfile(JSON.stringify({ pad: { steer: { kind: 'button', index: 3 } } }));
    expect(q.pad.steer.kind).toBe('axis');
    expect(parseKeyBindings(JSON.stringify({ camera: ['KeyK', 'KeyV'] })).camera).toEqual(['KeyV']);
  });
  it('help rows follow the bindings', () => {
    const p = defaultPadProfile(), k = defaultKeyBindings();
    k.camera = ['KeyV'];
    p.pad.brake = { kind: 'button', index: 5 };
    const rows = helpRows(p, k);
    expect(rows.find((r) => r[0] === 'Cycle camera')![2]).toBe('V');
    expect(rows.find((r) => r[0] === 'Brake')![1]).toContain('RB');
  });
});

describe('pad profile versions', () => {
  it('new defaults: paddles shift, X auto-shift, A free, Start reserved', () => {
    const p = defaultPadProfile().pad;
    expect([p.shiftUp, p.shiftDown, p.handbrake, p.camera, p.reset, p.autoShift]).toEqual([5, 4, 1, 3, 8, 2].map((index) => ({ kind: 'button', index })));
    const used = Object.values(p).filter((s) => s.kind === 'button').map((s) => (s as { index: number }).index);
    expect(used).not.toContain(0);
    expect(used).not.toContain(9);
  });
  it('a current-version profile round-trips without migration', () => {
    const p = defaultPadProfile();
    p.pad.camera = { kind: 'button', index: 10 };
    const r = readPadProfile(serializePadProfile(p));
    expect(r.migrated).toBe(false);
    expect(r.profile).toEqual(p);
  });
  it('migrates a v1 profile on the old defaults, keeping calibration', () => {
    const v1 = {
      pad: { ...defaultPadProfile().pad, shiftUp: { kind: 'button', index: 0 }, shiftDown: { kind: 'button', index: 2 }, autoShift: { kind: 'button', index: 9 } },
      cal: { ...defaultPadProfile().cal, brake: { min: 0.1, max: 0.9, deadzone: 0.05, invert: false, expo: 1.8 } },
    };
    const r = readPadProfile(JSON.stringify(v1));
    expect(r.migrated).toBe(true);
    expect(r.profile.pad).toEqual(defaultPadProfile().pad);
    expect(r.profile.cal.brake.expo).toBe(1.8);
  });
  it('keeps custom v1 buttons unless they clash, then resets the buttons', () => {
    const keep = readPadProfile(JSON.stringify({ pad: { camera: { kind: 'button', index: 10 }, shiftUp: { kind: 'button', index: 0 } } }));
    expect(keep.profile.pad.camera).toEqual({ kind: 'button', index: 10 });
    expect(keep.profile.pad.shiftUp).toEqual({ kind: 'button', index: 5 });
    // camera was custom on RB (5), which is now the shift-up default: clash → defaults
    const clash = readPadProfile(JSON.stringify({ pad: { camera: { kind: 'button', index: 5 } } }));
    expect(clash.migrated).toBe(true);
    expect(clash.profile.pad).toEqual(defaultPadProfile().pad);
  });
  it('never binds Start (pause menu), in any version', () => {
    const p = defaultPadProfile();
    const j = JSON.parse(serializePadProfile(p));
    j.pad.camera = { kind: 'button', index: 9 };
    expect(readPadProfile(JSON.stringify(j)).profile.pad.camera).toEqual({ kind: 'button', index: 3 });
  });
  it('Escape is reserved for the menu on the keyboard', () => {
    expect(parseKeyBindings(JSON.stringify({ reset: ['Escape', 'KeyR'] })).reset).toEqual(['KeyR']);
  });
});

describe('look-around controls', () => {
  it('looks with the stick not used for steering, never one a pedal uses', async () => {
    const { lookStickAxes, lookBackButton } = await import('../controls');
    const p = defaultPadProfile();
    expect(lookStickAxes(p)).toEqual([2, 3]);
    expect(lookBackButton(p)).toBe(11);
    p.pad.steer = { kind: 'axis', index: 2, sign: -1 };
    expect(lookStickAxes(p)).toEqual([0, 1]);
    expect(lookBackButton(p)).toBe(10);
    const q = defaultPadProfile();
    q.pad.throttle = { kind: 'axis', index: 3, sign: -1 };
    expect(lookStickAxes(q)).toBeNull();
    const r = defaultPadProfile();
    r.pad.camera = { kind: 'button', index: 11 };
    expect(lookBackButton(r)).toBeNull();
  });
  it('shapes the stick with a radial deadzone: left / up are positive', async () => {
    const { shapeLook } = await import('../controls');
    expect(shapeLook(0.1, 0.05)).toEqual([0, 0]);
    const [x, y] = shapeLook(-1, 0);
    expect(x).toBeCloseTo(1); expect(y).toBeCloseTo(0);
    expect(shapeLook(0, -1)[1]).toBeCloseTo(1);
    expect(Math.abs(shapeLook(-0.5, 0)[0])).toBeLessThan(0.5); // expo: gentle near the centre
  });
  it('hold full look: latches past 95 %, releases when moved again after centring', async () => {
    const { LookLatch } = await import('../controls');
    const l = new LookLatch();
    expect(l.update(1, [1, 0], true)).toEqual([1, 0]);
    expect(l.update(0.5, [0.3, 0], true)).toEqual([1, 0]);   // springing stick on its way back
    expect(l.update(0, [0, 0], true)).toEqual([1, 0]);       // released: held
    expect(l.update(0.4, [-0.2, 0], true)).toEqual([-0.2, 0]); // moved again: follows the stick
    expect(l.update(0, [0, 0], true)).toEqual([0, 0]);
    expect(l.update(1, [1, 0], false)).toEqual([1, 0]);
    expect(l.update(0, [0, 0], false)).toEqual([0, 0]);      // option off: springs back
  });
  it('look keys default to , . and Backspace and show in the help', () => {
    const k = defaultKeyBindings();
    expect([k.lookLeft, k.lookRight, k.lookBack]).toEqual([['Comma'], ['Period'], ['Backspace']]);
    expect(parseKeyBindings(JSON.stringify({ camera: ['KeyV'] })).lookLeft).toEqual(['Comma']);
    const rows = helpRows(defaultPadProfile(), k);
    expect(rows.find((r) => r[0] === 'Look around')!.slice(1)).toEqual(['Right stick', ', | . · mouse drag']);
    expect(rows.find((r) => r[0] === 'Look back')!.slice(1)).toEqual(['RS', 'Backspace']);
  });
});
