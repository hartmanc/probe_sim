// Race mode: AI field, drivers, car-vs-car contacts and the race director. See NOTES.md here.
export { RaceDirector, DEFAULT_RACE_CONFIG } from './race';
export type { RaceConfig, RaceInputs, RaceHud, RacePhase, RaceFlag, GapInfo, PenaltyHud, ResultRow, CarPose, EngineInfo, RaceCar } from './race';
export { RaceLine } from './line';
export type { GhostsJsonLike, LineProjection } from './line';
export { AiDriver } from './driver';
export type { AiDriverParams, DriverControl } from './driver';
export { AI_VERSION, parseIdentity, fieldKey, modelKey, resolveCarType, aiCarJson, buildAiSpec, describeAiCar, measureCarPerf, buildSpeedProfile } from './field';
export type { PaceCar, PaceJson, IdentityCar, IdentityEngine, CarType, ResolvedCar, CarPerf } from './field';
export { Traffic } from './traffic';
export { Rng, hashSeed, aggressionFor } from './rng';
export { runSolo } from './solo';
export { CarCollider } from '../cars';
export type { CarBody, CarContactEvent, CarColliderOptions } from '../cars';
