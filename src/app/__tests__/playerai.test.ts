// ?playerai=1 (dev autopilot): an app-built director (HotlapSim car as the player, buildDirector as the race builds it) with
// playerAi true drives the player's car at the pack's pace, like an AI car.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { expect, it } from 'vitest';
import { HotlapSim, STEP } from '../../scoreboard';
import { lagunaAssets } from '../../scoreboard/__tests__/fixtures';
import { buildDirector } from '../race-build';
import type { FieldData } from '../loader';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const rj = (p: string) => JSON.parse(readFileSync(pub + p, 'utf8'));

it('the AI-driven player moves at pack pace over the first 20 s (speed and distance like the AI cars around its grid slot)', () => {
  const sim = new HotlapSim(lagunaAssets(), { record: false, autoShift: true });
  sim.reset();
  const field = { pace: rj('cars/field/pace.json'), identity: rj('cars/field/identity.json'), models: [], missing: [] } as unknown as FieldData;
  const dir = buildDirector(sim, field, { seed: 1, laps: 2, trackId: 'laguna_seca', playerAi: true });
  sim.stepVehicle = (di) => dir.step(STEP, di as never);
  const U0 = dir.cars.map((c) => c.U);
  let vSum = 0, n = 0;
  for (let i = 1; i <= 20000; i++) {
    sim.step(() => ({ steer: 0, throttle: 0, brake: 0 }));    // the human's input is ignored
    if (i > 10000 && i % 100 === 0) { vSum += dir.player.vehicle.state.speed; n++; }
  }
  const P = dir.player, grid = P.grid;
  const near = dir.cars.filter((c) => !c.isPlayer && Math.abs(c.grid - grid) <= 4);
  const dist = (c: typeof P) => c.U - U0[c.idx];
  const nearMed = near.map(dist).sort((a, b) => a - b)[Math.floor(near.length / 2)];
  expect(P.driver).not.toBeNull();
  expect(dist(P)).toBeGreaterThan(250);                         // it really drives
  expect(dist(P) / nearMed).toBeGreaterThan(0.7);               // like its neighbours on the grid
  expect(dist(P) / nearMed).toBeLessThan(1.4);
  expect(vSum / n).toBeGreaterThan(10);                          // m/s, the green-flag half of the window
  expect(P.recoveries).toBe(0);
}, 120000);
