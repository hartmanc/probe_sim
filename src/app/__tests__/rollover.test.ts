import { describe, expect, it } from 'vitest';
import { ROLLOVER_DELAY_MS, ROLLOVER_LINE, RolloverWatch } from '../rollover';
import { ROLLOVER_RAD } from '../../physics/rollover';

// body rolled by a about its long (x) axis: q = [sin(a/2), 0, 0, cos(a/2)]
const rolled = (deg: number) => { const a = (deg * Math.PI) / 180; return [Math.sin(a / 2), 0, 0, Math.cos(a / 2)]; };
const UP = [0, 0, 1];

describe('rollover game over', () => {
  it('shows the owner\'s exact text', () => {
    expect(ROLLOVER_LINE).toBe('You are banned from Lemons for one year for rolling your hooptie');
  });
  it('uses the kerb gate\'s rollover state (60 deg relative to the road)', () => {
    expect(ROLLOVER_RAD).toBeCloseTo(Math.PI / 3, 12);
  });
  it('triggers once, ROLLOVER_DELAY_MS after the roll passes the rollover state, and not below it', () => {
    const w = new RolloverWatch();
    expect(w.update(rolled(55), UP, 0)).toBe(false);
    expect(w.update(rolled(55), UP, 10_000)).toBe(false);   // a hard lean is no rollover
    expect(w.rolled).toBe(false);
    expect(w.update(rolled(-95), UP, 20_000)).toBe(false);  // rolled (either side): armed
    expect(w.rolled).toBe(true);
    expect(w.update(rolled(-95), UP, 20_000 + ROLLOVER_DELAY_MS - 1)).toBe(false);
    expect(w.update(rolled(-170), UP, 20_000 + ROLLOVER_DELAY_MS)).toBe(true);
    expect(w.update(rolled(-170), UP, 30_000)).toBe(false);  // once
    w.reset();
    expect(w.update(rolled(0), UP, 40_000)).toBe(false);
  });
  it('measures roll relative to the road, not the world (a car on a 40 deg bank is no rollover)', () => {
    const a = (40 * Math.PI) / 180, bank = [0, Math.sin(a), Math.cos(a)];
    const lean = [-40, 40].map((d) => { const w = new RolloverWatch(); w.update(rolled(d), bank, 0); return w.rolled; });
    expect(lean.filter(Boolean)).toHaveLength(1);   // lying with the bank: 0 deg off the road; against it: 80 deg
  });
});
