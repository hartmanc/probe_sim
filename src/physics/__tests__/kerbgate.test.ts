// Kerb traversal gate (20 Oct 2026, the Sonoma rollover: compare/sonoma/kerb_rollover.md). The player's Probe drives
// over every RAISED strip of every registered track (kerbs with a profile, sausage kerbs) at the racing line's speed on
// the line and 1 m either side of it (kerbprobe.ts, the same probe as tools/physics/kerb_sweep.ts), and must not roll
// past 15 deg relative to the road or roll over (the gate). A wheel lifted by the strip is REPORTED, not gated (21 Oct
// 2026, the owner, Buttonwillow lap 2): "Lifting a wheel isn't inherently a realism issue. Driving over a kerb and
// rolling over is an issue." and "I drove over a kerb at Buttonwillow and lifted at least one wheel a few weeks ago."
// The advisory report prints per pass the lifted time, the largest air gap and the plain-road control.
import { describe, expect, it } from 'vitest';
import { TRACKS } from '../../scoreboard/config';
import { crestCases, gateCases, kerbTraversal, loadKerbPack } from './kerbprobe';
import carJson from '../../../public/cars/probe_gt/car.json';

const probe = JSON.parse(JSON.stringify(carJson));

describe.each(Object.keys(TRACKS))('kerb traversal gate: %s', (id) => {
  const pack = loadKerbPack(TRACKS[id].dir);
  const results = gateCases(pack).map((c) => kerbTraversal(pack, probe, c));
  it('no roll past 15 deg and no rollover at line speed, line +-1 m', () => {
    const bad = results.filter((r) => r.rolledOver || r.maxRollDeg > 15).map((r) => `${r.label}: ${r.maxRollDeg.toFixed(1)} deg`);
    expect(bad).toEqual([]);
  });
  // round 15 (Buttonwillow, the owner's decision of 26 Oct 2026, item 18): the crest case, the player's car at the
  // player's speed (the fastest ghost lap's, else the onboard's overlay speed at that station; not the AI line's) with
  // its strip-side wheels 2 m past each raised strip's track-side edge: no rollover and no roll past 15 deg. A track with
  // no player speed has no crest cases (printed).
  const crest = pack.playerSpeed ? crestCases(pack).map((c) => kerbTraversal(pack, probe, c)) : [];
  it('crest case: no roll past 15 deg and no rollover at the player\'s speed, 2 m onto each raised strip', () => {
    console.log(`kerb crest cases ${id}: player speed ${pack.playerSpeedSrc}; ${crest.length} passes\n  ${crest.map((r) => `${r.label}: max roll ${r.maxRollDeg.toFixed(1)} deg${r.rolledOver ? ' ROLLED' : ''}, lifted ${r.kerbLiftMs} ms`).join('\n  ')}`);
    const bad = crest.filter((r) => r.rolledOver || r.maxRollDeg > 15).map((r) => `${r.label}: ${r.maxRollDeg.toFixed(1)} deg`);
    expect(bad).toEqual([]);
  });
  // advisory (the owner's decision above): wheel lifts per pass, printed for the judge and the owner, never a failure
  it('advisory: wheel lifts per pass (reported, not gated)', () => {
    const rows = results.filter((r) => r.kerbLiftMs > 0 || r.baseLiftMs > 0)
      .map((r) => `${r.label}: lifted ${r.kerbLiftMs} ms by the strip, air gap ${(r.kerbLiftGap * 100).toFixed(1)} cm, max roll ${r.maxRollDeg.toFixed(1)} deg; plain road ${r.baseLiftMs} ms, ${r.baseRollDeg.toFixed(1)} deg`);
    console.log(`kerb lift report ${id}: ${results.length} passes, ${rows.length} with a lift\n  ${rows.join('\n  ')}`);
    expect(results.length).toBeGreaterThanOrEqual(0);
  });
}, 120000);
