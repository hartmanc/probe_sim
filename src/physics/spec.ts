// Car physics specification: the schema of public/cars/<car>/car.json.
//
// Units are SI throughout (m, kg, s, N, N·m, rad/s) unless a field name says
// otherwise (…Deg, …Rpm). Frames follow CONTRACTS.md §1: body frame ISO 8855,
// x forward, y left, z up, origin at mid-wheelbase / mid-track on the ground
// at static ride height.
//
// Keys starting with "_" anywhere in car.json are comments and are ignored.
// Every field listed here without a "default" note is required; loadCarSpec
// throws a descriptive error if one is missing or not a finite number.

export interface AxleSuspension {
  /** Wheel rate of the main spring, N/m. */
  springRate: number;
  /** Damper coefficient in bump (compression), N·s/m at the wheel. */
  damperBump: number;
  /** Damper coefficient in rebound (extension), N·s/m at the wheel. */
  damperRebound: number;
  /** Anti-roll bar wheel rate, N/m: force on each wheel = rate · (c_this − c_other). */
  antiRollRate: number;
  /**
   * Suspension compression from full droop at static ride height, m. The
   * spring preload is derived from it so the car sits at the contract's
   * static ride height. Smaller = less droop travel, more bump travel.
   */
  staticCompression: number;
  /**
   * Lateral-force compliance steer, degrees of toe per kN of that wheel's
   * lateral force (bushings, rack and subframe mounts). Positive = toward
   * understeer: a front wheel steers out of the turn, a rear wheel steers
   * into it (in phase with the fronts). Default 0.
   */
  complianceSteerDegPerKN: number;
}

export interface TyreAxis {
  /** Peak friction coefficient at the reference load Fz0. */
  mu0: number;
  /** Magic Formula shape factor C (must be > 1 so a peak exists). */
  C: number;
  /** Magic Formula curvature factor E (≤ 1). */
  E: number;
  /** Relaxation length, m. */
  relaxationLength: number;
}

export interface CarSpec {
  name: string;
  /** Total mass incl. driver and fuel, kg. */
  mass: number;
  /** CG height above ground at static ride height, m. */
  cgHeight: number;
  /** Static front axle share of the weight, 0..1. Sets the CG x position. */
  frontWeightFraction: number;
  wheelbase: number;
  trackFront: number;
  trackRear: number;
  /** Principal moments of inertia about the CG, kg·m² (body x = roll, y = pitch, z = yaw). */
  inertia: { roll: number; pitch: number; yaw: number };
  /**
   * Unsprung mass per corner, kg. Included in `mass`; the wheel is modelled as
   * massless vertically (no wheel-hop DOF), so this only enters reporting /
   * future use. See README "Known limitations".
   */
  unsprungMassPerCorner: number;

  wheel: {
    /** Tyre unloaded radius, m. Used as rolling radius. */
    radius: number;
    /** Spin inertia of wheel + tyre + brake disc + half-shaft, kg·m². */
    spinInertia: number;
  };

  suspension: {
    front: AxleSuspension;
    rear: AxleSuspension;
    /** Total suspension travel (droop to full bump), m. */
    travel: number;
    /** The bump stop engages this far before full travel, m. */
    bumpStopRange: number;
    /** Extra bump-stop force when compressed to full travel, N (quadratic engagement, keeps rising beyond). */
    bumpStopForceAtFull: number;
    /** Tyre vertical stiffness, N/m (in series with the spring; gives a smooth load → 0 at lift-off). Default 250000. */
    tyreVerticalRate: number;
  };

  tyre: {
    /** Reference load for mu0, N. */
    Fz0: number;
    /** Load sensitivity exponent: mu(Fz) = mu0 · (Fz/Fz0)^loadSensitivity. */
    loadSensitivity: number;
    lateral: TyreAxis & { /** Slip angle of the pure-lateral peak, degrees. B is derived from it. */ peakSlipAngleDeg: number };
    longitudinal: TyreAxis & { /** Slip ratio of the pure-longitudinal peak. B is derived from it. */ peakSlipRatio: number };
    /**
     * Speed sensitivity of the lateral friction peak: mu_y × (1 − slope·max(0, |vx| − refSpeed)),
     * floored at 0.6. Stands in for the fall of rubber friction with sliding speed and heat in fast
     * corners. Longitudinal grip is left alone (it is calibrated to the logger's braking).
     * Defaults refSpeed 25 m/s, slope 0 (off).
     */
    speedSensitivity: { refSpeed: number; slope: number };
    /** Low-speed treatment. All optional. */
    lowSpeed: {
      /** Floor on |vx| when computing steady-state slip, m/s. Default 1.0. */
      velocityFloor: number;
      /** Below this speed extra contact-patch damping blends in, m/s. Default 1.0. */
      blendSpeed: number;
      /** Longitudinal contact damping at standstill, N·s/m. Default 3000. */
      dampingLong: number;
      /** Lateral contact damping at standstill, N·s/m. Default 8000. */
      dampingLat: number;
    };
  };

  engine: {
    /** Full-throttle torque curve at the crank, N·m, linear between points, rpm ascending. */
    torqueCurve: { rpm: number[]; torque: number[] };
    idleRpm: number;
    revLimitRpm: number;
    /** Fuel-cut dwell once the limiter trips, s. Default 0.03. */
    limiterCutTime: number;
    /** Rotating inertia of the engine + flywheel + clutch, kg·m². */
    inertia: number;
    /** Closed-throttle (friction / pumping) torque at idle, N·m, negative. */
    brakingTorqueIdle: number;
    /** Closed-throttle torque at the rev limit, N·m, negative. */
    brakingTorqueLimit: number;
  };

  drivetrain: {
    /** Driven axle(s): "fwd" (default, open differential on the front axle), "rwd" (open rear
     *  differential) or "awd" (open centre differential with a fixed torque split, awdFrontShare). */
    layout: 'fwd' | 'rwd' | 'awd';
    /** AWD only: front share of the drive torque, 0..1. Default 0.4. */
    awdFrontShare: number;
    /** Overall ratios (engine revs per wheel rev) for gears 1..N. */
    gearRatios: number[];
    /** Overall reverse ratio, positive number. */
    reverseRatio: number;
    /** Fraction of positive engine torque that reaches the wheels. */
    efficiency: number;
    /** Time with the clutch open and fuel cut during a shift, s. */
    shiftTime: number;
    clutch: {
      /** Torque capacity when fully engaged, N·m. */
      maxTorque: number;
      /** Auto-clutch starts to bite at this engine rpm. */
      engageRpm: number;
      /** At zero throttle the auto-clutch is fully closed at this rpm (and opens below it). */
      fullRpm: number;
      /** At full throttle the full-closure rpm is raised by this much (launch rpm). */
      launchRpmBoost: number;
      /** After a shift the clutch capacity ramps up (quadratically) over this time, s. Default 0.2. */
      engageTime: number;
    };
    autoShift: {
      /** Upshift when engine rpm reaches this. */
      upshiftRpm: number;
      /** Downshift when gearbox-side rpm falls below this… */
      downshiftRpm: number;
      /** …unless the lower gear would put the engine above this rpm. */
      downshiftMaxRpm: number;
      /** Minimum time between automatic shifts, s. */
      minInterval: number;
      /**
       * Kickdown (load-based downshift): with throttle ≥ kickdownThrottle, engine rpm below kickdownRpm and
       * longitudinal acceleration below kickdownAccel (g), shift down if the lower gear lands at or under
       * upshiftRpm (never above 0.5 g lateral). After a kickdown the next upshift waits for kickdownHoldRpm while the throttle stays
       * above 0.5 (hysteresis, so it does not hunt). Defaults 0.8 / 0 (off) / 0.15 / upshiftRpm.
       */
      /** With a gear schedule (setScheduledGear) an upshift also waits for this engine rpm. Default 4000. */
      scheduleMinUpshiftRpm: number;
      kickdownThrottle: number;
      kickdownRpm: number;
      kickdownAccel: number;
      kickdownHoldRpm: number;
    };
  };

  brakes: {
    /** Total brake torque at full pedal, all four wheels, N·m. */
    maxTorque: number;
    /** Front share of the brake torque, 0..1. */
    frontBias: number;
    /** Handbrake torque, total on the rear axle, N·m. */
    handbrakeTorque: number;
    /**
     * Rear proportioning valve: above `knee` (pedal fraction ∝ line pressure)
     * rear pressure rises only at `slope` × the front rate. knee = 1 disables.
     * frontBias is the split below the knee. Defaults 1 / 1.
     */
    proportioningKnee: number;
    proportioningSlope: number;
    /**
     * Early-90s 3-channel ABS (fronts individually, rears together on the
     * lower wheel). All fields optional; see README "ABS".
     */
    abs: {
      /** 1 = fitted and on by default, 0 = no ABS. Default 1. */
      enabled: number;
      /** A wheel must stay above lockSlip this long before the ABS wakes up, s. Default 0.45. */
      wakeDelay: number;
      /** Slip counted as "locking" for the wake-up timer. Default 0.35. */
      lockSlip: number;
      /** While active: release when slip exceeds this. Default 0.25. */
      releaseSlip: number;
      /** Brake torque fraction during a release. Default 0.3. */
      releaseFactor: number;
      /** Re-apply ramp, torque fraction per second. Default 7. */
      applyRate: number;
      /** Minimum release time per pulse, s. Default 0.04. */
      holdTime: number;
      /** No ABS below this speed, m/s. Default 2.2 (8 km/h). */
      minSpeed: number;
    };
    /** Pedal → line pressure map: pressure = pedal^pedalExponent. >1 puts the top of the trigger travel into modulation. Default 1. */
    pedalExponent: number;
  };

  aero: { cd: number; frontalArea: number; airDensity: number };

  /** Rolling resistance coefficient at low speed. */
  rollingResistance: number;
  /** Speed term: Crr(v) = rollingResistance + rollingResistanceSpeed · v² (v in m/s). Default 0. */
  rollingResistanceSpeed: number;

  /**
   * How the tyres behave off pavement (surface sample `dirt` > 0). All optional; see src/physics/NOTES-surface.md.
   * Each effect is scaled by the surface's dirt weight, so it fades in over the first metre past the paved edge.
   */
  surfaces: {
    /** Tyre friction on dry dirt / grass relative to pavement. Overrides the surface's muOffTrack when set
     *  (NaN = use the surface's mu). Default NaN. */
    offPavementMu: number;
    /** Lateral (cornering) stiffness factor on dirt: the peak slip angle grows by 1/factor, so the car slides
     *  progressively instead of snapping. 1 = same as pavement. Default 0.65. */
    offPavementLateralStiffness: number;
    /** Extra rolling resistance / sinkage drag on dirt: ΔCrr = rollingResistance + rollingResistanceSpeed · |v|
     *  (v in m/s), applied per wheel × load. Defaults 0.04 and 0.0015. */
    offPavementRollingResistance: number;
    offPavementRollingResistanceSpeed: number;
  };

  steering: {
    /** Maximum road-wheel angle (centre/bicycle angle) at standstill, degrees. */
    maxAngleDeg: number;
    /** Ackermann factor 0..1 (1 = full geometric Ackermann). */
    ackermann: number;
    /** Max angle at speed v: maxAngle / (1 + (v/shapingSpeed)²), m/s. Huge value disables. */
    shapingSpeed: number;
    /** Lower bound on the speed-limited max angle, degrees. */
    minAngleDeg: number;
    /** Steering command rate limit at standstill, full-scale units per second (2/rate = lock-to-lock flick time). */
    rate: number;
    /** Rate falls as rate / (1 + v/rateSpeed), m/s. */
    rateSpeed: number;
  };

  /** Collision hull (box) used only when the body touches the ground (roll-over, big crests). */
  hull: {
    front: number;   // body x of the nose, m
    rear: number;    // body x of the tail (negative), m
    halfWidth: number;
    floor: number;   // body z of the floor corners
    roof: number;    // body z of the roof corners
    friction: number;
    /** Body z of the bumper line: the footprint corners tested against walls, trees and buildings. Default 0.45. */
    bumper: number;
    /** Body x range of the roof (for roof-vs-fence contacts). Defaults 0.6 / −1.3. */
    roofFront: number;
    roofRear: number;
  };
}

/** Peak slip of the tyre's pure-slip force curves (where slipUse = 1 on each axis). Pure helper. */
export function tyrePeakSlip(spec: CarSpec): { angleRad: number; ratio: number } {
  return { angleRad: (spec.tyre.lateral.peakSlipAngleDeg * Math.PI) / 180, ratio: spec.tyre.longitudinal.peakSlipRatio };
}

// ---------------------------------------------------------------------------

type Obj = Record<string, unknown>;

class SpecError extends Error {}

function isObj(v: unknown): v is Obj {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function obj(o: Obj, key: string, path: string, optional = false): Obj {
  const v = o[key];
  if (v === undefined && optional) return {};
  if (!isObj(v)) throw new SpecError(`car spec: ${path}${key} must be an object`);
  return v;
}

function num(o: Obj, key: string, path: string, opts: { def?: number; min?: number; max?: number } = {}): number {
  let v = o[key];
  if (v === undefined && opts.def !== undefined) v = opts.def;
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new SpecError(`car spec: ${path}${key} must be a finite number (got ${JSON.stringify(v)})`);
  if (opts.min !== undefined && v < opts.min) throw new SpecError(`car spec: ${path}${key} = ${v} is below ${opts.min}`);
  if (opts.max !== undefined && v > opts.max) throw new SpecError(`car spec: ${path}${key} = ${v} is above ${opts.max}`);
  return v;
}

function numArr(o: Obj, key: string, path: string, minLen: number): number[] {
  const v = o[key];
  if (!Array.isArray(v) || v.length < minLen || !v.every((x) => typeof x === 'number' && Number.isFinite(x))) {
    throw new SpecError(`car spec: ${path}${key} must be an array of ≥ ${minLen} finite numbers`);
  }
  return v.slice() as number[];
}

const POS = { min: 1e-9 };
const FRAC = { min: 0, max: 1 };

function axleSusp(o: Obj, p: string): AxleSuspension {
  return {
    springRate: num(o, 'springRate', p, POS),
    damperBump: num(o, 'damperBump', p, POS),
    damperRebound: num(o, 'damperRebound', p, POS),
    antiRollRate: num(o, 'antiRollRate', p, { min: 0 }),
    staticCompression: num(o, 'staticCompression', p, POS),
    complianceSteerDegPerKN: num(o, 'complianceSteerDegPerKN', p, { def: 0, min: -1, max: 1 }),
  };
}

function tyreAxis(o: Obj, p: string): TyreAxis {
  const C = num(o, 'C', p, { min: 1.0001, max: 1.9999 });
  return {
    mu0: num(o, 'mu0', p, POS),
    C,
    E: num(o, 'E', p, { min: -10, max: 1 }),
    relaxationLength: num(o, 'relaxationLength', p, POS),
  };
}

/** Validate and normalize a parsed car.json. Throws Error with the offending path. */
export function loadCarSpec(json: unknown): CarSpec {
  if (!isObj(json)) throw new SpecError('car spec: root must be an object');
  const j = json;
  const inertia = obj(j, 'inertia', '');
  const wheel = obj(j, 'wheel', '');
  const susp = obj(j, 'suspension', '');
  const tyre = obj(j, 'tyre', '');
  const lat = obj(tyre, 'lateral', 'tyre.');
  const lon = obj(tyre, 'longitudinal', 'tyre.');
  const low = obj(tyre, 'lowSpeed', 'tyre.', true);
  const eng = obj(j, 'engine', '');
  const curve = obj(eng, 'torqueCurve', 'engine.');
  const dt = obj(j, 'drivetrain', '');
  const clutch = obj(dt, 'clutch', 'drivetrain.');
  const auto = obj(dt, 'autoShift', 'drivetrain.');
  const brakes = obj(j, 'brakes', '');
  const aero = obj(j, 'aero', '');
  const steer = obj(j, 'steering', '');
  const hull = obj(j, 'hull', '', true);
  const surf = obj(j, 'surfaces', '', true);

  const rpm = numArr(curve, 'rpm', 'engine.torqueCurve.', 2);
  const torque = numArr(curve, 'torque', 'engine.torqueCurve.', 2);
  if (rpm.length !== torque.length) throw new SpecError('car spec: engine.torqueCurve.rpm and .torque differ in length');
  for (let i = 1; i < rpm.length; i++) if (!(rpm[i] > rpm[i - 1])) throw new SpecError('car spec: engine.torqueCurve.rpm must be ascending');

  const layout = dt.layout ?? 'fwd';
  if (layout !== 'fwd' && layout !== 'rwd' && layout !== 'awd') throw new SpecError(`car spec: drivetrain.layout "${String(layout)}" not supported (fwd, rwd, awd)`);
  const gearRatios = numArr(dt, 'gearRatios', 'drivetrain.', 1);
  if (!gearRatios.every((g) => g > 0)) throw new SpecError('car spec: drivetrain.gearRatios must be positive');

  const spec: CarSpec = {
    name: typeof j.name === 'string' ? j.name : 'car',
    mass: num(j, 'mass', '', POS),
    cgHeight: num(j, 'cgHeight', '', POS),
    frontWeightFraction: num(j, 'frontWeightFraction', '', { min: 0.05, max: 0.95 }),
    wheelbase: num(j, 'wheelbase', '', POS),
    trackFront: num(j, 'trackFront', '', POS),
    trackRear: num(j, 'trackRear', '', POS),
    inertia: { roll: num(inertia, 'roll', 'inertia.', POS), pitch: num(inertia, 'pitch', 'inertia.', POS), yaw: num(inertia, 'yaw', 'inertia.', POS) },
    unsprungMassPerCorner: num(j, 'unsprungMassPerCorner', '', { min: 0, def: 0 }),
    wheel: { radius: num(wheel, 'radius', 'wheel.', POS), spinInertia: num(wheel, 'spinInertia', 'wheel.', POS) },
    suspension: {
      front: axleSusp(obj(susp, 'front', 'suspension.'), 'suspension.front.'),
      rear: axleSusp(obj(susp, 'rear', 'suspension.'), 'suspension.rear.'),
      travel: num(susp, 'travel', 'suspension.', POS),
      bumpStopRange: num(susp, 'bumpStopRange', 'suspension.', POS),
      bumpStopForceAtFull: num(susp, 'bumpStopForceAtFull', 'suspension.', { min: 0 }),
      tyreVerticalRate: num(susp, 'tyreVerticalRate', 'suspension.', { min: 1000, def: 250000 }),
    },
    tyre: {
      Fz0: num(tyre, 'Fz0', 'tyre.', POS),
      loadSensitivity: num(tyre, 'loadSensitivity', 'tyre.', { min: -0.9, max: 0.5 }),
      lateral: { ...tyreAxis(lat, 'tyre.lateral.'), peakSlipAngleDeg: num(lat, 'peakSlipAngleDeg', 'tyre.lateral.', { min: 0.5, max: 45 }) },
      longitudinal: { ...tyreAxis(lon, 'tyre.longitudinal.'), peakSlipRatio: num(lon, 'peakSlipRatio', 'tyre.longitudinal.', { min: 0.005, max: 0.8 }) },
      speedSensitivity: (() => {
        const o = obj(tyre, 'speedSensitivity', 'tyre.', true);
        return { refSpeed: num(o, 'refSpeed', 'tyre.speedSensitivity.', { def: 25, min: 0 }), slope: num(o, 'slope', 'tyre.speedSensitivity.', { def: 0, min: 0, max: 0.1 }) };
      })(),
      lowSpeed: {
        velocityFloor: num(low, 'velocityFloor', 'tyre.lowSpeed.', { def: 1.0, min: 0.1 }),
        blendSpeed: num(low, 'blendSpeed', 'tyre.lowSpeed.', { def: 1.0, min: 0.01 }),
        dampingLong: num(low, 'dampingLong', 'tyre.lowSpeed.', { def: 3000, min: 0 }),
        dampingLat: num(low, 'dampingLat', 'tyre.lowSpeed.', { def: 8000, min: 0 }),
      },
    },
    engine: {
      torqueCurve: { rpm, torque },
      idleRpm: num(eng, 'idleRpm', 'engine.', POS),
      revLimitRpm: num(eng, 'revLimitRpm', 'engine.', POS),
      limiterCutTime: num(eng, 'limiterCutTime', 'engine.', { def: 0.03, min: 0 }),
      inertia: num(eng, 'inertia', 'engine.', POS),
      brakingTorqueIdle: num(eng, 'brakingTorqueIdle', 'engine.', { max: 0 }),
      brakingTorqueLimit: num(eng, 'brakingTorqueLimit', 'engine.', { max: 0 }),
    },
    drivetrain: {
      layout: layout as 'fwd' | 'rwd' | 'awd',
      awdFrontShare: num(dt, 'awdFrontShare', 'drivetrain.', { def: 0.4, min: 0, max: 1 }),
      gearRatios,
      reverseRatio: num(dt, 'reverseRatio', 'drivetrain.', POS),
      efficiency: num(dt, 'efficiency', 'drivetrain.', { min: 0.1, max: 1 }),
      shiftTime: num(dt, 'shiftTime', 'drivetrain.', { min: 0 }),
      clutch: {
        maxTorque: num(clutch, 'maxTorque', 'drivetrain.clutch.', POS),
        engageRpm: num(clutch, 'engageRpm', 'drivetrain.clutch.', POS),
        fullRpm: num(clutch, 'fullRpm', 'drivetrain.clutch.', POS),
        launchRpmBoost: num(clutch, 'launchRpmBoost', 'drivetrain.clutch.', { min: 0 }),
        engageTime: num(clutch, 'engageTime', 'drivetrain.clutch.', { min: 0, def: 0.2 }),
      },
      autoShift: {
        upshiftRpm: num(auto, 'upshiftRpm', 'drivetrain.autoShift.', POS),
        downshiftRpm: num(auto, 'downshiftRpm', 'drivetrain.autoShift.', POS),
        downshiftMaxRpm: num(auto, 'downshiftMaxRpm', 'drivetrain.autoShift.', POS),
        minInterval: num(auto, 'minInterval', 'drivetrain.autoShift.', { min: 0 }),
        scheduleMinUpshiftRpm: num(auto, 'scheduleMinUpshiftRpm', 'drivetrain.autoShift.', { def: 4000, min: 0 }),
        kickdownThrottle: num(auto, 'kickdownThrottle', 'drivetrain.autoShift.', { def: 0.8, min: 0, max: 1 }),
        kickdownRpm: num(auto, 'kickdownRpm', 'drivetrain.autoShift.', { def: 0, min: 0 }),
        kickdownAccel: num(auto, 'kickdownAccel', 'drivetrain.autoShift.', { def: 0.15 }),
        kickdownHoldRpm: num(auto, 'kickdownHoldRpm', 'drivetrain.autoShift.', { def: num(auto, 'upshiftRpm', 'drivetrain.autoShift.', POS), min: 0 }),
      },
    },
    brakes: {
      maxTorque: num(brakes, 'maxTorque', 'brakes.', { min: 0 }),
      frontBias: num(brakes, 'frontBias', 'brakes.', FRAC),
      handbrakeTorque: num(brakes, 'handbrakeTorque', 'brakes.', { min: 0 }),
      proportioningKnee: num(brakes, 'proportioningKnee', 'brakes.', { ...FRAC, def: 1 }),
      proportioningSlope: num(brakes, 'proportioningSlope', 'brakes.', { ...FRAC, def: 1 }),
      pedalExponent: num(brakes, 'pedalExponent', 'brakes.', { def: 1, min: 0.5, max: 4 }),
      abs: (() => {
        const a = obj(brakes, 'abs', 'brakes.', true);
        const P = 'brakes.abs.';
        return {
          enabled: num(a, 'enabled', P, { def: 1, min: 0, max: 1 }),
          wakeDelay: num(a, 'wakeDelay', P, { def: 0.45, min: 0 }),
          lockSlip: num(a, 'lockSlip', P, { def: 0.35, min: 0.01, max: 1 }),
          releaseSlip: num(a, 'releaseSlip', P, { def: 0.25, min: 0.01, max: 1 }),
          releaseFactor: num(a, 'releaseFactor', P, { def: 0.3, min: 0, max: 1 }),
          applyRate: num(a, 'applyRate', P, { def: 7, min: 0.1 }),
          holdTime: num(a, 'holdTime', P, { def: 0.04, min: 0 }),
          minSpeed: num(a, 'minSpeed', P, { def: 2.2, min: 0 }),
        };
      })(),
    },
    aero: {
      cd: num(aero, 'cd', 'aero.', { min: 0 }),
      frontalArea: num(aero, 'frontalArea', 'aero.', { min: 0 }),
      airDensity: num(aero, 'airDensity', 'aero.', { min: 0 }),
    },
    rollingResistance: num(j, 'rollingResistance', '', { min: 0 }),
    rollingResistanceSpeed: num(j, 'rollingResistanceSpeed', '', { min: 0, def: 0 }),
    surfaces: {
      offPavementMu: surf.offPavementMu === undefined ? NaN : num(surf, 'offPavementMu', 'surfaces.', { min: 0.05, max: 2 }),
      offPavementLateralStiffness: num(surf, 'offPavementLateralStiffness', 'surfaces.', { def: 0.65, min: 0.2, max: 1 }),
      offPavementRollingResistance: num(surf, 'offPavementRollingResistance', 'surfaces.', { def: 0.04, min: 0 }),
      offPavementRollingResistanceSpeed: num(surf, 'offPavementRollingResistanceSpeed', 'surfaces.', { def: 0.0015, min: 0 }),
    },
    steering: {
      maxAngleDeg: num(steer, 'maxAngleDeg', 'steering.', { min: 1, max: 60 }),
      ackermann: num(steer, 'ackermann', 'steering.', FRAC),
      shapingSpeed: num(steer, 'shapingSpeed', 'steering.', POS),
      minAngleDeg: num(steer, 'minAngleDeg', 'steering.', { min: 0 }),
      rate: num(steer, 'rate', 'steering.', POS),
      rateSpeed: num(steer, 'rateSpeed', 'steering.', POS),
    },
    hull: {
      front: num(hull, 'front', 'hull.', { def: 2.25 }),
      rear: num(hull, 'rear', 'hull.', { def: -2.25 }),
      halfWidth: num(hull, 'halfWidth', 'hull.', { def: 0.86, min: 0.1 }),
      floor: num(hull, 'floor', 'hull.', { def: 0.14 }),
      roof: num(hull, 'roof', 'hull.', { def: 1.3 }),
      friction: num(hull, 'friction', 'hull.', { def: 0.5, min: 0 }),
      bumper: num(hull, 'bumper', 'hull.', { def: 0.45 }),
      roofFront: num(hull, 'roofFront', 'hull.', { def: 0.6 }),
      roofRear: num(hull, 'roofRear', 'hull.', { def: -1.3 }),
    },
  };

  const s = spec.suspension;
  if (s.bumpStopRange >= s.travel) throw new SpecError('car spec: suspension.bumpStopRange must be < travel');
  for (const ax of [s.front, s.rear]) {
    if (ax.staticCompression >= s.travel) throw new SpecError('car spec: staticCompression must be < travel');
  }
  if (spec.engine.revLimitRpm <= spec.engine.idleRpm) throw new SpecError('car spec: engine.revLimitRpm must exceed idleRpm');
  return spec;
}
