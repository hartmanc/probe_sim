import { describe, expect, it } from 'vitest';
import { axisGlyph, buttonGlyph, detectPadKind } from '../glyphs';
import { defaultKeyBindings, defaultPadProfile, describePad, helpRows } from '../controls';

describe('controller kind detection', () => {
  it('reads the vendor id', () => {
    expect(detectPadKind('Xbox 360 Controller (STANDARD GAMEPAD Vendor: 045e Product: 028e)')).toBe('xbox');
    expect(detectPadKind('Wireless Controller (STANDARD GAMEPAD Vendor: 054c Product: 09cc)')).toBe('playstation');
    expect(detectPadKind('Pro Controller (STANDARD GAMEPAD Vendor: 057e Product: 2009)')).toBe('nintendo');
    expect(detectPadKind('054c-0ce6-DualSense Wireless Controller')).toBe('playstation'); // Firefox style
    expect(detectPadKind('Generic USB Joystick (Vendor: 0079 Product: 0006)')).toBe('generic');
  });
  it('falls back to product words', () => {
    expect(detectPadKind('XInput STANDARD GAMEPAD')).toBe('xbox');
    expect(detectPadKind('Sony DualShock 4')).toBe('playstation');
    expect(detectPadKind('PLAYSTATION(R)3 Controller')).toBe('playstation');
    expect(detectPadKind('Joy-Con (L/R)')).toBe('nintendo');
    expect(detectPadKind('')).toBe('generic');
    expect(detectPadKind(null)).toBe('generic');
  });
});

describe('glyphs', () => {
  it('names standard buttons per family', () => {
    expect([0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => buttonGlyph('xbox', i))).toEqual(['A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'Back', 'Start']);
    expect([0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => buttonGlyph('playstation', i))).toEqual(['✕', '○', '□', '△', 'L1', 'R1', 'L2', 'R2', 'Share', 'Options']);
    // Nintendo: the bottom face button (index 0) is B
    expect([0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => buttonGlyph('nintendo', i))).toEqual(['B', 'A', 'Y', 'X', 'L', 'R', 'ZL', 'ZR', '−', '+']);
    expect(buttonGlyph('generic', 5)).toBe('Button 5');
    expect(buttonGlyph('xbox', 12)).toBe('D-pad ↑');
    expect(buttonGlyph('xbox', 40)).toBe('Button 40');
    expect(axisGlyph('playstation', 0)).toBe('Left stick X');
    expect(axisGlyph('generic', 0)).toBe('Axis 0');
  });
  it('help rows and binding labels follow the kind', () => {
    const p = defaultPadProfile(), k = defaultKeyBindings();
    const row = (kind: Parameters<typeof helpRows>[2], name: string) => helpRows(p, k, kind).find((r) => r[0] === name)![1];
    expect(row('xbox', 'Shift up')).toBe('RB');
    expect(row('playstation', 'Shift up')).toBe('R1');
    expect(row('nintendo', 'Shift down')).toBe('L');
    expect(row('xbox', 'Pause menu')).toBe('Start');
    expect(row('playstation', 'Pause menu')).toBe('Options');
    expect(row('playstation', 'Throttle')).toBe('R2');
    expect(describePad('shiftUp', p.pad.shiftUp, 'xbox', true)).toBe('RB (b5)');
    expect(describePad('throttle', p.pad.throttle, 'nintendo', true)).toBe('ZR (auto)');
  });
});
