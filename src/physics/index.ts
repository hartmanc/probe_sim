// Public physics API (CONTRACTS.md §4).
export type { SurfaceSample, Surface, DriverInput, WheelState, VehicleState, Vec3, ImpactInfo } from './types';
export type { CarSpec, AxleSuspension, TyreAxis } from './spec';
export { loadCarSpec, tyrePeakSlip } from './spec';
export { Vehicle, LAUNCH_SPEED } from './vehicle';
export type { VehicleOptions } from './vehicle';
export type { TrackJson, TrackSurfaceOptions, TrackProjection, HeightGrid, PitLaneJson, SausageJson, KerbsJson, KerbProfileJson } from './track';
export { SAUSAGE_RAMP_M, kerbBandCentre } from './track';
export { createTrackSurface, createTrackProjector, lineToWorld, loadHeightfield, SHOULDER_WIDTH_M, OFF_PAVEMENT_MU, SURFACE_GRIP_BLEND_M, DIRT_ROUGHNESS_M } from './track';
export { mfShape, solveMfB } from './tyre';
export { createCollisionWorld, CollisionWorld, COLLISION_KINDS, KIND_PROPS } from './collision';
export type { CollisionKind, KindProps, SceneryCollisionJson, CollisionWorldOptions } from './collision';
export { deriveGearSchedule, scheduleGearAt, scheduleTargetAt, shiftRpmSummary } from './gearschedule';
export type { GearSchedule, GhostLapLike } from './gearschedule';
// Race mode (src/physics/ai/NOTES.md): AI field, race director, car-vs-car contacts.
export * as race from './ai/index';
export { ROLLOVER_RAD, rollOf, isRolledOver } from './rollover';
