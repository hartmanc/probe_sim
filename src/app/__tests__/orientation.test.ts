import { describe, expect, it } from 'vitest';
import { portraitFrom } from '../orientation';

const win = { innerWidth: 844, innerHeight: 390 };
describe('portraitFrom', () => {
  it('trusts screen.orientation.type when present', () => {
    expect(portraitFrom({ ...win, orientationType: 'portrait-primary' })).toBe(true);
    expect(portraitFrom({ ...win, orientationType: 'portrait-secondary' })).toBe(true);
    expect(portraitFrom({ ...win, orientationType: 'landscape-primary' })).toBe(false);
    expect(portraitFrom({ ...win, orientationType: 'landscape-secondary' })).toBe(false);
  });
  it('the type beats window.orientation, the media query and the window shape', () => {
    expect(portraitFrom({ innerWidth: 390, innerHeight: 844, orientationType: 'landscape-primary', windowOrientation: 0, mqPortrait: true })).toBe(false);
    expect(portraitFrom({ ...win, orientationType: 'portrait-primary', windowOrientation: 90, mqPortrait: false })).toBe(true);
  });
  it('without a type, window.orientation: 0 and 180 are portrait, 90 and -90 landscape', () => {
    expect(portraitFrom({ ...win, orientationType: null, windowOrientation: 0 })).toBe(true);
    expect(portraitFrom({ ...win, windowOrientation: 180 })).toBe(true);
    expect(portraitFrom({ ...win, windowOrientation: 90, mqPortrait: true })).toBe(false);
    expect(portraitFrom({ ...win, windowOrientation: -90, mqPortrait: true })).toBe(false);
  });
  it('without those, the media query; without that, the window shape', () => {
    expect(portraitFrom({ ...win, mqPortrait: true })).toBe(true);
    expect(portraitFrom({ innerWidth: 390, innerHeight: 844, mqPortrait: false })).toBe(false);
    expect(portraitFrom({ innerWidth: 390, innerHeight: 844 })).toBe(true);
    expect(portraitFrom({ innerWidth: 844, innerHeight: 390, mqPortrait: null })).toBe(false);
  });
  it('an unknown orientation type falls through to the next source', () => {
    expect(portraitFrom({ ...win, orientationType: 'natural', windowOrientation: 0 })).toBe(true);
  });
});
