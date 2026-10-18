import { describe, expect, it } from 'vitest';
import { ModeHost, type GameMode, type ModeContext, type ModeId } from '../modes/mode';
import { createRace, RACE_LAPS } from '../modes/race';
import { LapTimer } from '../timing';

function fakeMode(id: ModeId, log: string[]): GameMode {
  return {
    id, label: id,
    start: () => log.push(`${id}:start`),
    restart: () => log.push(`${id}:restart`),
    reset: () => log.push(`${id}:reset`),
    step: () => {}, onLap: () => {}, frame: () => {},
    hud: () => ({ banner: null, timing: true, delta: null, showDelta: false }),
    pauseEntries: () => [],
    dispose: () => log.push(`${id}:dispose`),
  };
}

describe('mode host', () => {
  it('disposes the old mode before starting the new one', () => {
    const log: string[] = [];
    const host = new ModeHost({ hotlap: () => fakeMode('hotlap', log), race: () => fakeMode('race', log) }, {});
    expect(host.current).toBeNull();
    host.set('hotlap');
    host.set('race');
    host.restart();
    expect(log).toEqual(['hotlap:start', 'hotlap:dispose', 'race:start', 'race:restart']);
    expect(host.current?.id).toBe('race');
  });
  it('picking the current mode again gives a fresh instance', () => {
    const log: string[] = [];
    let made = 0;
    const host = new ModeHost({ hotlap: () => { made++; return fakeMode('hotlap', log); }, race: () => fakeMode('race', log) }, {});
    const a = host.set('hotlap');
    const b = host.set('hotlap');
    expect(a).not.toBe(b);
    expect(made).toBe(2);
    expect(log).toEqual(['hotlap:start', 'hotlap:dispose', 'hotlap:start']);
  });
});

describe('race mode without race services', () => {
  it('rolls the car and reports the missing services instead of crashing', () => {
    const calls: string[] = [];
    const ctx = {
      timer: new LapTimer(3600), track: { length_m: 3600 },
      ghosts: { group: { visible: true }, fastestReal: () => null },
      hud: { hideCorners: () => {}, setRefName: () => {}, setBanner: () => {}, toast: () => {} },
      simTime: () => 0, s: () => 1234,
      rollingStart: () => calls.push('rollingStart'),
      recoverAt: (s: number) => calls.push(`recover:${s}`),
      setScheduleLap: () => calls.push('schedule'),
      toast: (m: string) => calls.push(`toast:${m}`),
    } as unknown as ModeContext;
    const race = createRace(ctx, { loadField: () => { throw new Error('unused'); }, loadModel: async () => null, random: () => 0.5, dom: false });
    race.start();
    expect((ctx.ghosts.group as { visible: boolean }).visible).toBe(false);
    expect(calls).toContain('rollingStart');
    expect(race.hud().banner).toMatch(/race services missing/);
    expect(race.hud().timing).toBe(false);
    expect(RACE_LAPS).toBe(5);
    race.reset();
    expect(calls).toContain('recover:1234');
    race.dispose();
  });
});
