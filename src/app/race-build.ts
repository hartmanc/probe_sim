// The race's physics-side construction, free of the DOM and three.js so the race Worker (race-worker.ts) can share it with
// the main thread (modes/race.ts re-exports these).
import { race as R, createTrackSurface, type Surface, type PitLaneJson } from '../physics';
import type { RaceDirector } from '../physics/ai/race';
import type { RaceLine } from '../physics/ai/line';
import type { PaceJson } from '../physics/ai/field';
import type { HotlapSim, SimAssets } from '../scoreboard';
import { TRACKS, resolveTrackId } from '../scoreboard/config';
import type { FieldData } from './loader';

export const PLAYER_NUMBER = '619';

/** The physics surface factory for the race (same options as HotlapSim's private surface). */
export function surfaceFactory(a: SimAssets): () => Surface {
  const farGrid = a.scenery?.far?.heightfield;
  const far = farGrid && a.farHeightfield
    ? { heightfield: a.farHeightfield, x0: farGrid.x0, y0: farGrid.y0, dx: farGrid.dx, nx: farGrid.nx, ny: farGrid.ny } : null;
  const pit = a.scenery?.pit_lane ?? null, zones = a.scenery?.paved_zones ?? null;
  const pitLane: PitLaneJson | null = pit || zones
    ? { spacing_m: 1, fractions: (pit ?? zones)!.fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] }
    : null;
  return () => createTrackSurface(a.track, a.heightfield, { far, pitLane, sausages: a.scenery?.sausages ?? null, kerbs: a.scenery?.kerbs ?? null, terrainOverride: a.scenery?.terrain_override ?? null });
}

const lineCache = new WeakMap<object, RaceLine>();
function raceLine(a: SimAssets): RaceLine {
  let l = lineCache.get(a.track);
  if (!l) {
    l = new R.RaceLine(a.track, a.ghosts as unknown as ConstructorParameters<typeof R.RaceLine>[1], undefined, resolveTrackId(a.trackId));
    const cones = (a.scenery as { pit_exit_cones?: { pts?: number[][] } | null } | null | undefined)?.pit_exit_cones;
    if (cones?.pts?.length) l.restrictLeft(cones.pts);   // the AI keeps right of the pit-exit cones, as the player must
    lineCache.set(a.track, l);
  }
  return l;
}

/** The per-track AI race parameters (TRACKS[id].ai) as RaceConfig fields; absent = Laguna's values (1, 1, 0). */
export function raceAiConfig(trackId: string): { followScale: number; laneMargin: number; shiftGrip: number } {
  const ai = TRACKS[resolveTrackId(trackId)].ai;
  return { followScale: ai?.followScale ?? 1, laneMargin: ai?.laneMargin ?? 1, shiftGrip: ai?.shiftGrip ?? 0 };
}

/** Build the RaceDirector for the player's current HotlapSim car (call right after a rolling start). */
export function buildDirector(sim: HotlapSim, field: FieldData, o: { seed: number; laps: number; trackId: string; realGrid?: boolean; playerAi?: boolean; lod?: boolean; strengthPct?: number }): RaceDirector {
  const a = sim.assets;
  const makeSurface = surfaceFactory(a);
  const pit = a.scenery?.pit_lane ?? null;
  return new R.RaceDirector({
    line: raceLine(a), surface: makeSurface(), makeSurface,
    probeJson: a.carJson, pace: field.pace as PaceJson, identity: field.identity ?? null,
    pitLane: pit ? { spacing_m: 1, ...pit } : null,
    blendLine: a.scenery?.blend_line ?? null,
    collisionWorld: sim.collision,
    playerVehicle: sim.vehicle, playerSurface: sim.surface,
  }, { laps: o.laps, seed: o.seed, playerNumber: PLAYER_NUMBER, greenWindow: [5, 30], ...raceAiConfig(o.trackId), strength: (o.strengthPct ?? 100) / 100,
    playerRefLap: TRACKS[resolveTrackId(o.trackId)].probeRefLap ?? Number.NaN,
    // phones and tablets (a selected 40-car field): the real grid order; desktop keeps the seeded shuffle
    ...(o.realGrid ? { gridOrder: 'real' as const } : {}),
    // ?playerai=1 (dev only, docs/performance.md): the player's car is AI-driven, the race is deterministic
    ...(o.playerAi ? { playerAi: true } : {}),
    // physics LOD for far AI cars (RaceConfig.lod): ?lod=1 / ?lod=0, else LOD_DEFAULT
    ...(o.lod ? { lod: true } : {}) });
}

