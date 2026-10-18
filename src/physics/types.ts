// Public API types (CONTRACTS.md §4). Keep these exactly in sync with the contract.

export type Vec3 = [number, number, number];

export interface SurfaceSample {
  z: number; nx: number; ny: number; nz: number; onTrack: boolean; mu: number;
  /** Paved surface: the track or the pit lane (onTrack is true only on the track). Not off track for lap validity. */
  paved?: boolean;
  /** Off-pavement weight: 0 on pavement (track, pit lane, paved runoff), rising smoothly to 1 over the first
   *  SURFACE_GRIP_BLEND_M past the paved edge. Surfaces without it are treated as pavement (0). */
  dirt?: number;
  /** Friction multiplier of the pavement (muOnTrack); lets a car apply its own off-pavement mu across the blend. */
  muPaved?: number;
}
/**
 * Ground under world (x, y). Implementations in this module return a reused
 * SurfaceSample object that is overwritten by the next call: copy the fields
 * you need before calling sample() again.
 */
export interface Surface { sample(x: number, y: number): SurfaceSample }

export interface DriverInput {
  steer: number;      // -1..1, positive = left
  throttle: number;   // 0..1
  brake: number;      // 0..1
  shiftUp: boolean;   // edge-triggered by the caller (true for one step)
  shiftDown: boolean;
  handbrake?: boolean;
}

export interface WheelState {
  pos: Vec3;                       // hub centre, world
  spinAngle: number;               // rad, accumulates
  steer: number;                   // road wheel angle, rad, + left
  compression: number;             // m, suspension travel from full droop
  omega: number;                   // rad/s
  /** Effective (relaxed) longitudinal slip ratio, + = driving. */
  slipRatio: number;
  /** Effective (relaxed) slip angle, rad, ISO 8855 sign: atan(vy/|vx|) of the contact patch. */
  slipAngle: number;
  /**
   * Combined slip relative to the tyre's peak: sqrt((κ/κ_peak)² + (α/α_peak)²) with the relaxed
   * slips, as the combined-slip model uses. 1.0 = at the peak of the force curve, > 1 = sliding.
   * 0 when the wheel is off the ground.
   */
  slipUse: number;
  /** Tyre normal load, N. */
  load: number;
  onTrack: boolean;
  /** Wheel is on pavement (track, pit lane or paved runoff), from the surface sample under it this step. */
  paved: boolean;
  /** Effective friction multiplier the tyre used this step (surface mu, or the car's off-pavement mu blended in). */
  mu: number;
}

export interface VehicleState {
  pos: Vec3;                       // body origin, world ENU
  quat: [number, number, number, number]; // body→world rotation (x, y, z, w)
  vel: Vec3;                       // world velocity of the body origin
  angVel: Vec3;                    // world
  wheels: [WheelState, WheelState, WheelState, WheelState]; // FL, FR, RL, RR
  rpm: number; gear: number;       // gear: -1 reverse, 0 neutral, 1..5
  speed: number;                   // m/s, forward
  gLat: number; gLong: number;     // body-frame accelerations in g
  throttleOut: number;             // after any shaping/rev limiter
  /** Last barrier/building/tree impact (null until the first one). Extra to §4; t is sim time in s. */
  impact?: ImpactInfo | null;
  /** True once the car has hit a wall hard enough to blast into space (easter egg). Cleared by reset(). */
  launched?: boolean;
  /** Sim time of the launch, s (NaN when not launched). */
  launchedAt?: number;
  /** True while the ABS is modulating any channel (for a HUD tag). */
  absActive?: boolean;
}

export interface ImpactInfo {
  /** Closing speed normal to the obstacle at the contact point, m/s (≥ 0): what decides a launch. */
  speedNormal: number;
  /** The car's speed over the ground at the impact, m/s: what the driver "hit the wall at" (HUD). */
  speed: number;
  /** Obstacle kind: concrete | armco | tyres | pitwall | fence | building | tree | boundary. */
  kind: string;
  /** Sim time of the impact, s. */
  t: number;
}
