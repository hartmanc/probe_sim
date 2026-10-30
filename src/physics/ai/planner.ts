// C1: the continuous offset planner (RaceConfig.planner 'offset'; NOTES "C1: the offset planner").
//
// The lane model (driver.ts) is the default. This planner replaces its pass machinery (planLane / passStep, the pinch guard,
// the give-way on a closing corridor) with one continuous choice made every PLAN_EVERY s while another car is near: the
// target lateral offset e* (m from the racing line, + left). Candidates across the corridor at my station, each the
// transition from where I am to that offset at the shift rate and then held (clamped to the road as the controller clamps
// it), are scored over a 10 s horizon sampled every 0.25 s against the other cars' projections (the lane model's: span
// e / eT / drift clamped to the road where the car will be, speed from its own profile scaled when held up). The costs are
// in seconds: time lost against my race-line profile (following a car in my band capped at its speed with my headway),
// lateral clearance to every neighbour while the bodies overlap, the corridor, damping and the one-move rule, the risk
// hook. Hard rules (BIG): overlap holds, never across, no move toward a clearly faster car behind, no pass in a no-pass
// window, no braking harder than the margin allows onto a car in my band.
//
// Pure: everything comes in through PlanWork (preallocated, no per-tick allocation) and PlanEnv (my profile, my lane
// speed factor, my corridor). Only + - * / and comparisons (no transcendental: docs/determinism.md).

export type Planner = 'lanes' | 'offset';

/** s between plans while a car is within the horizon (the lane model's PLAN_EVERY) */
export const PLAN_EVERY = 0.2;
/** horizon samples: PLAN_N x PLAN_DT = 10 s (the lane model's PLAN_T) */
export const PLAN_DT = 0.25, PLAN_N = 40;
/** s: a pass that would take longer than this is not started (the lane model's PLAN_T_MAX), as a cost */
export const PLAN_T_MAX = 40;
/** m ahead / behind in which a car is a neighbour (the horizon ahead; 25 m behind), at most NB_MAX of them by distance */
export const PLAN_AHEAD = 150, PLAN_BEHIND = 25, NB_MAX = 8;
/** candidates: a grid of CAND_N offsets CAND_STEP apart around where I am (a 6 m band), plus my current target, the racing
 *  line and a defending target */
export const CAND_STEP = 0.5, CAND_N = 13, CAND_MAX = CAND_N + 3;
/** lateral clearances, m edge to edge (driver.ts): followed below FOLLOW_CLR, steep cost below ALONG_CLR, BIG below LANE_CLR */
export const FOLLOW_CLR = 0.4, ALONG_CLR = 0.7, LANE_CLR = 0.3;
/** m from the track edge (car side) the corridor keeps (the lane model's PASS_EDGE) */
export const PASS_EDGE = 0.5;
/** "infinite". A broken rule of the move itself (never across, toward a clearly faster car, into the side of a car alongside, a
 *  no-pass window) costs 2 BIG; a conflict on the projection BIG + the samples left after it (an earlier conflict is worse), so
 *  when every candidate breaks a rule the least bad one is chosen and holding beats moving */
export const BIG = 1e6;
/** clearance cost: W x ((ALONG_CLR - c) / ALONG_CLR)² per s of overlap, by aggression (calm, normal, aggressive) */
export const CLR_W = [6, 4, 2.5];
/** s a new target must beat the current one by (hysteresis), by aggression */
export const HYST = [0.5, 0.35, 0.25];
/** s a new target is held before another may replace it (unless holding it breaks a rule) */
export const MIN_HOLD = 1;
/** s per m of change of the target (damping) */
export const DAMP = 0.02;
/** s: reversing the lateral move before the apex of the corner it was made for (one move, then hold) */
export const REVERSE_W = 2;
/** s: a pass that does not progress, or would take longer than PLAN_T_MAX */
export const LONG_W = 1.5;
/** m: ... for a car I am within this of at the end of the horizon (beside it or closing on it in another band) */
export const LONG_NEAR = 30;
/** s per s within CORR_NEAR m of the corridor's edge */
export const CORR_W = 0.05, CORR_NEAR = 0.3;
/** s per m away from a preferred offset (a light defending cover within 3 %) */
export const PREF_W = 0.3;
/** s per m away from the defending cover (C2: the cover is one move to the inside, then held; at PREF_W the plan never made it) */
export const COVER_W = 2;
/** m of change below which a target is "held" (no move for the one-move and no-defence rules) */
export const MOVE_EPS = 0.25;
/** s: the hard rules on the projection (clearance below LANE_CLR, braking onto a car in my band) hold over the first T_HARD s;
 *  further out the projection is a guess and a conflict is the steep clearance cost at its worst */
export const T_HARD = 2.5;
/** s per m off the racing line per s held (ties and the way back to the line), and LINE_FREE_W where no other car is within
 *  LINE_NEAR m of me on the projection (an offset there races nobody) */
export const LINE_W = 0.006, LINE_FREE_W = 0.04, LINE_NEAR = 30;
/** s per m off the racing line per s inside a no-pass window (the Corkscrew: the line runs edge to edge over a blind crest, a
 *  lane measured from it is no usable path; the lane model's rule) */
export const ZONE_W = 0.5;
/** s per s of a lateral move that asks more than the car's lateral grip: the line's own v²κ plus the pure-pursuit curvature
 *  of the shift, v · rate / Ld (Ld = 3 + 0.25 v), over the grip, per unit of excess (a move is made where the grip allows it:
 *  before the corner, not in it) */
export const GRIP_W = 4;
/** m: (C2 H2) a pass candidate holds its offset until my rear is this far clear of the passed car's front, then merges back to
 *  the line at the shift rate */
export const MERGE_GAP = 3;
/** (C2 H6) the road rule fires where the clamp moves my offset faster than this share of the shift rate (the car lags its
 *  shift target: Laguna T11 / T10 / T4 track-out four-offs at 2.5-2.8 m/s of clamp against a 2.86 m/s shift rate) */
export const ROAD_K = 0.6;
/** (C2, tools: the screens' A/B) the C2 steps that are switches; the defaults are the kept ones */
export const knobs = { h2: 1, grip: 0, tail: 1, h3: 0, h4: 1, h5: 0, h6: 1, roadk: ROAD_K, phw: 0.3, r1: 1, r2: 1, r3: 1, tv: 4, gr: 1, tailT: 10, ctl: 1, lift: 1, room: 1, fc: 0, vt: 0,
  // (C4, the Lemons pass; NOTES "C4" and "Knobs for the search")
  p1: 1, slow: 1, stk: 1, att1: 1, att2: 0, tc: 2, tcAg: 0.25, dmin: 60, ovl: 0.5, ovlAg: 0.2, attw: 1, attc: 0.9, ins: 0.5, feas: 1,
  tlap: 1, lapMin: 0.5, p2: 1, bo: 0, boDv: 1.5, p3: 1, p4: 1, ret: 40, retT: 10, p5: 1,
  // (C4 P6: the C1-C3 constants as knobs, defaults = the constants)
  damp: DAMP, revW: REVERSE_W, coverW: COVER_W, clrK: 1, hystK: 1, minHold: MIN_HOLD, tHard: T_HARD, lineW: LINE_W, lineFreeW: LINE_FREE_W, zoneW: ZONE_W,
  corrW: CORR_W, gripW: GRIP_W, longW: LONG_W, mergeGap: MERGE_GAP, alongClr: ALONG_CLR, laneClr: LANE_CLR, hwK: 1,
  // (C5, the train pass; NOTES "C5")
  t1: 1, vClose: 2, tTrain: 1.5, trMarg: 10, ovlTI: 0.3, trainW: 1, t2: 1, trF: 1, acrRel: 1, abSl: 0, pAcc: 1, nProj: 1, nA: 2.5 };
/* (C5 knobs) t1 1: the train pass (T1-T4): the target is the furthest car of the train ahead I get my nose ovl past before the
 * braking point less trMarg, decided at arrival; vClose: m/s my speed (or my profile at its station) must exceed the car ahead's
 * to look as far as the horizon (else tc's window); tTrain: s, the time gap between consecutive cars of a train; trMarg: m before
 * the braking point at which the landing is projected; ovlTI: share of my length my nose must be past the target's tail at its
 * turn-in (else back out behind it); trainW: weight of the commit's lap pricing (the train's pace deficits x the lap fraction
 * left); t2 1: committed, a hard rule on the attack offset or the landing out of reach aborts (tuck in behind the nearest car of
 * the train ahead of me); trF 1: committed, a car of the train clear of my band now is not followed for the road's squeeze
 * before the braking point; acrRel 1: the train pass in hand or judged, never-across against a car wholly ahead uses the sweep at
 * the closing speed (I cross behind it unless I reach it during the move); abSl: m of overlap below ovl the landing may fall on
 * the projection before the commit aborts for reach (the braking point still needs ovl); pAcc 1: my projected speed rises from my
 * speed now at my full-throttle acceleration (C1-C4: the profile's speed at once, which made a commit from behind a slower car
 * look a car length or more better than it was); nProj 1: a neighbour's projected speed rises from its speed now toward its
 * profile at nA m/s² (C1-C4 scaled its profile by its ratio now), and a car in the band of the car directly ahead of it is held
 * behind that car (driver.ts planStep) */
/* (C3, knobs.r1 / r2 / r3: the vortex round's rules; knobs.tv: the vortex rule's hard window, s; knobs.gr 1: the GRIP cost at the
 * rate the plan moves at (R3's shiftRate, so a move the grip allows is not priced as one it does not); knobs.tailT: TAIL_T, s;
 * knobs.ctl 1: the controller moves a held offset at that rate too, driver.ts; knobs.lift 1: the alongside lift only for a car
 * alongside, not one in my wake, driver.ts; knobs.room 1: room made for a passer my body overlaps, driver.ts; knobs.fc 1: the
 * friction circle in shiftRate and the controller's rate; knobs.vt 1: the vortex rule in the projection's tier) */
/* (C4 knobs) p1 1: the early commit on a clearly slower car ahead; tc: T_COMMIT, s of time gap (gap / v) within which it commits;
 * tcAg: the share of tc each aggression step adds (calm 1 - tcAg, aggressive 1 + tcAg); dmin: D_MIN, m: the next braking point at
 * least this far ahead; ovl: OVL_MIN, the share of my length my nose must be past its tail at the braking point; ovlAg: the share
 * of ovl each aggression step takes off; attw: ATT_W, s per m away from the attack offset; attc: m edge to edge the attack offset
 * keeps from the car ahead; ins: m to the inside of its line beyond which the car ahead "has the inside" (the pick goes outside);
 * feas 1: commit only when the plan's own projection of the attack (attackOverlap) puts the overlap before the braking point
 * (or the straight runs past the horizon); att1 1: committed, the attack offset is taken unless it breaks a hard rule; att2 1:
 * committed and clear of its band, the car attacked is not followed for the road's squeeze past the braking point; tlap 1: staying behind a clearly slower car is
 * priced over the rest of the lap (its pace delta x my lap time x the lap fraction left, at least lapMin of a lap); p2 1: back
 * out at the braking point without the overlap (lift, follow it, tuck in, re-plan past the apex); bo: m before the braking point
 * at which the overlap is judged; p3 1: with the overlap, hold the side to the track-out; p4 1: no car within ret m ahead and
 * none overlapping: the racing line, no plan; p5 1: the pick reads the car ahead's own pass (follow it through) and its passer's
 * side (taken) */
/** (C4 P1-P3) the attack phases: none, committed (alongside by the braking point), holding the side, backing out */
export const ATT_NONE = 0, ATT_COMMIT = 1, ATT_HOLD = 2, ATT_BACK = 3;
/** (C3 R3) m/s: the least lateral rate of the shift the controller delivers (driver.ts SHIFT_RATE_MIN) */
export const SHIFT_MIN = 0.8;
/** (C3 R2) the share of a corner's peak curvature above which the racing line is "in the corner": turn-in where |κ| rises above
 *  it before the apex, track-out where it falls below it after the apex (driver.ts vortexCorners) */
export const VORTEX_K = 0.3;
/* (knobs.phw: H4's following headway behind a clearly slower car, s; 0.3 = the lane model's PASS_HEADWAY) */
/** s: (C2 H2) the time lost at the end of the horizon behind a car in my band, at the rate it costs me there, carried on for
 *  this long (staying behind a slower car keeps costing after the horizon; a completed pass does not) */
export const TAIL_T = 10;
/** (C2, knobs.grip 2) the share of the lateral grip the line itself uses above which a lateral move is priced by the grip */
export const GRIP_CORNER = 0.5;
/** s: (C2 H3) the hard window per neighbour: the time to reach it at the closing speed now, clamped */
export const T_HARD_MIN = 1, T_HARD_MAX = 4;
/** risk hook: s per unit of passRisk (0 today) */
export const RISK_W = 4;
/** the clearly-faster pace ratio (driver.ts CLEARLY_FASTER) */
const CF = 0.97;

/** My side of the plan: my race-line speed, my lane speed factor and my corridor at s m ahead of my station. */
export interface PlanEnv {
  vRef(s: number): number;
  factor(e: number, s: number): number;
  lo(s: number): number;
  hi(s: number): number;
  /** the racing line's curvature at s, 1/m */
  curv(s: number): number;
  /** the pass-risk hook (0 today) for a target e */
  risk(e: number): number;
  /** (C5 knobs.pAcc) my full-throttle acceleration at speed v, m/s² (absent: the profile's speed is reached at once) */
  acc?(v: number): number;
}

const S = PLAN_N + 1;
/** the rules (PlanWork.why, tools): none, toward a clearly faster car, across, the road, braking, clearance, alongside, no-pass */
export const WHY = ['', 'faster', 'across', 'road', 'brake', 'clear', 'own', 'nopass', 'vortex'] as const;
/** (tools) the cost components of a candidate (PlanWork.comp): time lost, clearance (the soft road rule included), the soft road
 *  rule alone, line / corridor / zone, grip, LONG, reversal, damping + preference + risk */
export const COMP = ['lost', 'clear', 'road', 'line', 'grip', 'long', 'reverse', 'damp'] as const;
/** (tools) when set, plan() tallies the rule the current target broke when it had to be replaced */
export const planTally: { on: boolean; n: Float64Array } = { on: false, n: new Float64Array(WHY.length) };

/** Inputs, neighbour projections, candidates and outputs of one plan (preallocated, reused every plan). */
export class PlanWork {
  // ---- me
  v = 0; eCur = 0; eMeas = 0; ePrev = 0; rate = 2.86; hw = 0.9; front = 2.2; rear = 2.2; headway = 0.55; aggr = 1; bMax = 8;
  /** my lateral grip, m/s² */
  aLat = 9;
  /** a no-pass window [zoneLo, zoneHi] in m ahead of my station (NaN: none) */
  zoneLo = Number.NaN; zoneHi = Number.NaN;
  /** the lateral direction of the move in hand (+1 / -1, 0 none) and whether the apex it was made for is still ahead */
  moveDir = 0; moveOpen = false;
  /** the target was set less than MIN_HOLD s ago */
  locked = false;
  /** a preferred offset (NaN: none) */
  ePref = Number.NaN;
  /** a clearly faster car within 25 m behind: its side of me (+1 / -1), 2 straight behind me, 0 none */
  cfSide = 0;
  /** (C2 H0) the nearest car ahead within 25 m is clearly slower than me: a move out of its band is a pass, not a block of the
   *  clearly faster car behind me (straight behind me it does not freeze me; beside me, still no move toward it) */
  cfPassing = false;
  // ---- neighbours (k < nN): positions m ahead of my station now, lateral span edges (half width included), per sample
  nN = 0;
  readonly X = new Float64Array(NB_MAX * S); readonly LO = new Float64Array(NB_MAX * S); readonly HI = new Float64Array(NB_MAX * S);
  readonly nFront = new Float64Array(NB_MAX); readonly nRear = new Float64Array(NB_MAX); readonly nE = new Float64Array(NB_MAX);
  /** 1: following me in my band (its job: no clearance cost for me) */
  readonly nIgnore = new Uint8Array(NB_MAX);
  /** 1: off / recovering (passed freely: no no-pass rule) */
  readonly nOff = new Uint8Array(NB_MAX);
  /** side of me (+1 / -1) of a car my body overlaps along the track now (0: none): it owns that side */
  readonly nOwn = new Int8Array(NB_MAX);
  /** the driver's car index (tools, the yield) */
  readonly nIdx = new Int32Array(NB_MAX);
  /** (C2 H3) the hard window per neighbour, s */
  readonly tHard = new Float64Array(NB_MAX);
  /** (C3 R2) the corner each neighbour ahead drives next: its turn-in, apex and track-out stations (m ahead of my station now)
   *  and its direction (+1 left-hander, -1 right-hander; 0: none, no vortex) */
  readonly vIn = new Float64Array(NB_MAX); readonly vAp = new Float64Array(NB_MAX); readonly vOut = new Float64Array(NB_MAX);
  readonly vDir = new Int8Array(NB_MAX);
  /** (C3 R1) a passer told me it is passing me: my target is frozen (held; never moved for it) */
  frozen = false;
  /** (C4) the attack offset preferred at ATT_W (NaN: none), and holding it (P3: the target held unless it breaks a rule) */
  eAtt = Number.NaN; attHold = false;
  /** (C4 tlap) per neighbour: its pace deficit to me, 1 - my pace / its pace (> 0: slower than me) */
  readonly nD = new Float64Array(NB_MAX);
  /** (C4 tlap) s: my lap time x the lap fraction left (at least knobs.lapMin of a lap) */
  lapLeft = 0;
  /** (C4 P1, attackOverlap) the neighbour attacked and the braking point (m ahead); out: my nose past its tail there, m */
  attK = -1; attDB = 0; attOv = 0;
  /** (C5 T1) per neighbour: my nose past its tail at the landing point (attackOverlap; extrapolated at the closing speed of the
   *  horizon's end when the landing lies beyond it; -Infinity: a hard rule) */
  readonly attOvK = new Float64Array(NB_MAX);
  /** (C5 T1) 1: the neighbour is a car of the train ahead of me */
  readonly nTrain = new Uint8Array(NB_MAX);
  /** (C5 T2) the train pass in hand (or being judged): the attack offset is held to the landing (no merge back after the first
   *  car), and staying behind is priced for every car of the train */
  trainHold = false;
  // ---- candidates
  nC = 0;
  readonly cand = new Float64Array(CAND_MAX); readonly cost = new Float64Array(CAND_MAX); readonly culprit = new Int32Array(CAND_MAX);
  /** the rule a candidate broke (WHY_*; 0 none) */
  readonly why = new Uint8Array(CAND_MAX);
  /** (tools, filled only while planTally.on) a candidate's cost by component: COMP order */
  readonly comp = new Float64Array(CAND_MAX * 8);
  // ---- out
  best = 0; bestCost = 0; bestCulprit = -1; evaluated = 0;
}

/** (C3 R3) the lateral rate the controller delivers at speed v on a line of curvature k: the shift's pure-pursuit curvature
 *  v · rate / Ld (Ld = 3 + 0.25 v) within the grip the line leaves, a_lat - v²|k| (the GRIP cost's terms), never above the
 *  pass rate w.rate nor below SHIFT_MIN */
export function shiftRate(w: PlanWork, v: number, k: number, decel = 0): number {
  if (!knobs.r3) return w.rate;
  // (knobs.fc: braking at decel uses the tyres too, the friction circle: a_lat x √(1 - (decel / the brakes)²))
  const bF = w.bMax / 0.85, u = knobs.fc && decel > 0 ? decel / bF : 0, aL = u > 0 ? w.aLat * Math.sqrt(u >= 1 ? 0 : 1 - u * u) : w.aLat;
  const vv = v > 5 ? v : 5, kk = k < 0 ? -k : k, r = (aL - vv * vv * kk) * (3 + 0.25 * vv) / vv;
  return r > w.rate ? w.rate : r < SHIFT_MIN ? SHIFT_MIN : r;
}

/** (C3 R1) a neighbour behind me whose body does not overlap mine now: the lead car holds its line, invisible to my plan */
export function behindClear(w: PlanWork, k: number): boolean {
  return knobs.r1 === 1 && w.X[k * S] <= -(w.rear + w.nFront[k]);
}

/** Clamp e to the corridor [lo, hi] (the racing line always in it). */
function clampC(e: number, lo: number, hi: number): number {
  return e < lo ? lo : e > hi ? hi : e;
}

/** Fill the candidate list: the current target first (ties and hysteresis go to it), the racing line, the preferred offset,
 *  then CAND_N offsets CAND_STEP apart around the measured offset, inside the corridor here. */
export function candidates(w: PlanWork, env: PlanEnv): void {
  const lo = Math.min(0, env.lo(0)), hi = Math.max(0, env.hi(0));
  w.cand[0] = w.ePrev; w.nC = 1;
  addCand(w, 0, lo, hi);
  if (!Number.isNaN(w.ePref)) addCand(w, clampC(w.ePref, lo, hi), lo, hi);
  if (!Number.isNaN(w.eAtt)) addCand(w, clampC(w.eAtt, lo, hi), lo, hi);
  const base = Math.round(2 * w.eMeas) / 2, h = (CAND_N - 1) >> 1;
  for (let k = -h; k <= h; k++) addCand(w, base + k * CAND_STEP, lo, hi);
}

function addCand(w: PlanWork, e: number, lo: number, hi: number): void {
  if (e < lo - 1e-9 || e > hi + 1e-9 || w.nC >= CAND_MAX) return;
  for (let c = 0; c < w.nC; c++) if (Math.abs(w.cand[c] - e) < 1e-6) return;
  w.cand[w.nC++] = e;
}

/**
 * The cost of target eStar (s; >= BIG when a hard rule is broken), and the neighbour behind it (w.culprit[c]).
 */
export function candidateCost(w: PlanWork, env: PlanEnv, c: number): number {
  const eStar = w.cand[c], eCur = w.eCur, hw = w.hw, aggr = w.aggr;
  const dE = eStar - w.ePrev, mv = dE > MOVE_EPS ? 1 : dE < -MOVE_EPS ? -1 : 0;
  let cost = knobs.damp * Math.abs(dE);
  w.culprit[c] = -1; w.why[c] = 0;
  // no move toward a clearly faster car behind (it is let by: hold the line and the speed)
  if (mv !== 0 && w.cfSide !== 0 && (w.cfSide === 2 ? !w.cfPassing : mv === w.cfSide)) { w.why[c] = 1; return 2 * BIG; }
  // one move per corner approach
  const rev = mv !== 0 && w.moveOpen && w.moveDir !== 0 && mv === -w.moveDir ? knobs.revW : 0;
  if (rev) cost += knobs.revW;
  if (!Number.isNaN(w.ePref)) cost += knobs.coverW * Math.abs(eStar - w.ePref);
  if (!Number.isNaN(w.eAtt)) cost += knobs.attw * Math.abs(eStar - w.eAtt);
  cost += RISK_W * env.risk(eStar);
  const nN = w.nN, X = w.X, LO = w.LO, HI = w.HI;
  // (C3 R1) the cars behind me that do not overlap me now are invisible: no clearance, no across, no road rule beside them, no
  // pass of them, no 'racing' line rate, no one-move rule (what remains against a car behind: the overlap rule, the cover,
  // the no-defence rule, in the driver the alongside lift in a corner)
  let inv = 0;
  for (let k = 0; k < nN; k++) if (w.nIgnore[k] || behindClear(w, k)) inv |= 1 << k;
  // never across: a neighbour whose centre lies between where I am and where I go, within the sweep's length; from one side of
  // it to the other (C2 H0: a car right ahead of me, its centre within my half width of mine, is not crossed by a move out from
  // behind it, to either side)
  {
    const sw = Math.abs(eStar - eCur), sweep = w.v * sw / Math.max(0.1, w.rate);
    if (sw > MOVE_EPS) for (let k = 0; k < nN; k++) {
      if (inv & (1 << k)) continue;
      const eq = w.nE[k], d = X[k * S];
      if ((eq - eCur) * (eStar - eq) <= 0) continue;
      if (eq - eCur < hw && eCur - eq < hw) continue;
      // (C5 knobs.acrRel, the train pass in hand or judged: a car wholly ahead is crossed behind unless I reach it during the move,
      // at the closing speed on its projection)
      let swF = sweep;
      if (knobs.acrRel && w.trainHold && d > w.front + w.nRear[k]) { const vc = w.v - (X[k * S + 1] - X[k * S]) / PLAN_DT; swF = (vc > 0 ? vc : 0) * sw / Math.max(0.1, w.rate); }
      if (d < swF + w.front + w.nRear[k] && d > -(sweep + w.rear + w.nFront[k])) { w.culprit[c] = k; w.why[c] = 2; return 2 * BIG; }
    }
  }
  const T = PLAN_N * PLAN_DT;
  let sMe = 0, vMe = w.v, lost = 0, clr = 0, corr = 0, grip = 0, ePrevS = eCur, roadSoft = 0;
  // (C2 H2) candidates that end: the car being passed (the nearest one not yet behind me, slower than me on the projection);
  // a target out of its band is a pass of it: held until I am MERGE_GAP clear of it, then back to the line
  let pk = -1;
  for (let k = 0; k < nN; k++) {
    if ((inv & (1 << k)) || w.nOff[k]) continue;
    const x0 = X[k * S];
    if (x0 <= -(w.rear + w.nFront[k]) || (pk >= 0 && x0 >= X[pk * S])) continue;
    if (X[k * S + PLAN_N] - x0 < w.v * T) pk = k;
  }
  let ends = false;
  const holdT = w.trainHold && !Number.isNaN(w.eAtt) && Math.abs(eStar - w.eAtt) < 0.26;
  if (pk >= 0 && !holdT) { const o = pk * S; ends = (LO[o] - (eStar + hw) > (eStar - hw) - HI[o] ? LO[o] - (eStar + hw) : (eStar - hw) - HI[o]) >= FOLLOW_CLR; }
  let eTgt = eStar, eUp = eCur, tailR = 0, tailLap = 0;
  // (the lateral motion at the last sample, and whether it was away from the line: the car moving toward its old target now)
  let mvS = w.ePrev > eCur + 1e-9 ? 1 : w.ePrev < eCur - 1e-9 ? -1 : 0, awayS = (w.ePrev < 0 ? -w.ePrev : w.ePrev) > (eCur < 0 ? -eCur : eCur);
  // the path held so far (clamped offsets at the last two samples and the distance between them): its own curvature
  const lo0 = Math.min(0, env.lo(0)), hi0 = Math.max(0, env.hi(0));
  let e1 = eCur === 0 ? 0 : clampC(eCur, lo0, hi0), e2 = e1, d1 = 0;
  const aG = 0.97 * w.aLat;
  const W = CLR_W[aggr] * knobs.clrK, hwy = w.headway, ALONG = knobs.alongClr, LANE = knobs.laneClr, TH = knobs.tHard;
  // (C2 H3) per neighbour: the hard window, the time to reach it at the closing speed now (clamped T_HARD_MIN..T_HARD_MAX;
  // not closing: T_HARD_MIN)
  if (knobs.h3) for (let k = 0; k < nN; k++) {
    const vq = (X[k * S + 1] - X[k * S]) / PLAN_DT, vc = w.v - vq, gap = X[k * S] - (w.front + w.nRear[k]);
    const th = vc > 0.5 && gap > 0 ? gap / vc : T_HARD_MIN;
    w.tHard[k] = th < T_HARD_MIN ? T_HARD_MIN : th > T_HARD_MAX ? T_HARD_MAX : th;
  }
  // per neighbour: in my band ahead of me on the last sample (a car I already follow now is no new braking case)
  // (C3 R2) the vortex of each neighbour ahead: bit k of vSeenIn / vSeenAp once it has reached its turn-in / apex on the
  // projection, of vOvIn / vOvAp when my body overlapped it then (alongside by its turn-in: the move is allowed)
  let vSeenIn = 0, vSeenAp = 0, vOvIn = 0, vOvAp = 0, vort = 0;
  if (knobs.r2) for (let k = 0; k < nN; k++) {
    if (!w.vDir[k] || w.nOff[k] || (inv & (1 << k))) continue;
    vort |= 1 << k;
    const x0 = X[k * S], ov = x0 < w.front + w.nRear[k] && x0 > -(w.rear + w.nFront[k]);
    if (x0 >= w.vIn[k]) { vSeenIn |= 1 << k; if (ov) vOvIn |= 1 << k; }
    if (x0 >= w.vAp[k]) { vSeenAp |= 1 << k; if (ov) vOvAp |= 1 << k; }
  }
  let capOn = 0, attHit = false;
  for (let k = 0; k < nN; k++) {
    const o = k * S;
    if (X[o] <= w.front + w.nRear[k]) continue;
    const sep = LO[o] - (e1 + hw) > (e1 - hw) - HI[o] ? LO[o] - (e1 + hw) : (e1 - hw) - HI[o];
    if (sep < FOLLOW_CLR) capOn |= 1 << k;
  }
  for (let m = 1; m <= PLAN_N; m++) {
    const t = m * PLAN_DT;
    if (ends && knobs.h2 && eTgt !== 0 && sMe - X[pk * S + m - 1] > w.rear + w.nFront[pk] + knobs.mergeGap) eTgt = 0;
    const vR0 = env.vRef(sMe + vMe * PLAN_DT), rS = shiftRate(w, vMe, env.curv(sMe), (vMe - vR0) / PLAN_DT), de = eTgt - eUp, r = rS * PLAN_DT;
    const eU = de > r ? eUp + r : de < -r ? eUp - r : eTgt;
    eUp = eU;
    // my speed over the interval: my profile at my lane offset
    const vR = env.vRef(sMe);
    let vL = vR * (eU === 0 ? 1 : env.factor(eU, sMe));
    // (C5 knobs.pAcc) from a speed below the profile (held up behind a car) I accelerate to it, not jump to it
    if (knobs.pAcc && env.acc && vL > vMe) { const va = vMe + env.acc(vMe) * PLAN_DT; if (va < vL) vL = va; }
    let sN = sMe + vL * PLAN_DT;
    const lo = Math.min(0, env.lo(sN)), hi = Math.max(0, env.hi(sN));
    const e = eU === 0 ? 0 : clampC(eU, lo, hi);
    // the road clamping my offset back faster than a car can move sideways (the line meeting the edge at turn-in or
    // track-out with me held off it on that side): a path I cannot drive
    // (on the outside only: the inside clamped to the edge at an apex is a tighter, slower arc, priced by the curvature below)
    // (C2 H6: on the inside too while a car is beside me there: the clamp sweeps me into it at the turn-in, Mid-Ohio T1 / T2 / T4)
    let besideK = -1;
    if (e !== eU && knobs.h6 && eU * env.curv(sN) > 0) for (let k = 0; k < nN; k++) {
      if (inv & (1 << k)) continue;
      const rel = X[k * S + m] - sN;
      if (rel < w.front + w.nRear[k] + 3 && rel > -(w.rear + w.nFront[k] + 3)) { besideK = k; break; }
    }
    if (e !== eU && (eU * env.curv(sN) <= 0 || besideK >= 0)) {
      const dE = e - e1, rr = (dE < 0 ? -dE : dE) / PLAN_DT;
      // (C3 R3: against the rate the controller delivers here, the grip the line leaves: the clamp at track-out is a hard rule
      // for me whoever I race)
      if (rr > (knobs.r3 ? rS : (knobs.h6 ? knobs.roadk : 1) * w.rate)) {
        if (t <= (knobs.h5 && besideK < 0 ? T_HARD_MIN : TH)) { w.culprit[c] = besideK >= 0 ? besideK : -2; w.why[c] = 3; return BIG + PLAN_N - m; }
        clr += W * PLAN_DT; roadSoft += W * PLAN_DT;
      }
    }
    if (e !== 0 || e1 !== 0) {
      // the offset path's own curvature (the line's at my offset plus the second difference of the held offset, which the
      // road clamping it to the edge makes tight where the line meets the edge: turn-in and track-out): the grip's speed
      const d0 = sN - sMe;
      if (d0 > 0.5 && d1 > 0.5) {
        const kl = env.curv(sMe), kp = kl / Math.max(0.5, 1 - kl * e1) + 2 * ((e - e1) / d0 - (e1 - e2) / d1) / (d0 + d1);
        const ka = kp < 0 ? -kp : kp, kla = kl < 0 ? -kl : kl;
        if (ka > kla + 2e-3) {
          const vk = Math.sqrt(aG / ka);
          if (vk < vL) { vL = vk; sN = sMe + vL * PLAN_DT; }
        }
      }
      d1 = d0;
    } else d1 = sN - sMe;
    e2 = e1; e1 = e;
    if (e !== 0 && (e - lo < CORR_NEAR || hi - e < CORR_NEAR)) corr += knobs.corrW * PLAN_DT;
    if (e !== 0) {
      let racing = false;
      for (let k = 0; k < nN; k++) { if (knobs.r1 && (inv & (1 << k))) continue; const r = X[k * S + m] - sN; if (r < LINE_NEAR && r > -LINE_NEAR) { racing = true; break; } }
      corr += (sN >= w.zoneLo && sMe <= w.zoneHi ? knobs.zoneW : racing ? knobs.lineW : knobs.lineFreeW) * (e < 0 ? -e : e) * PLAN_DT;
    }
    {
      const away = (eU < 0 ? -eU : eU) > (ePrevS < 0 ? -ePrevS : ePrevS), dirS = eU > ePrevS ? 1 : eU < ePrevS ? -1 : 0;
      // moving away from the line: the lateral grip the shift asks on top of the line's (C2: only where the lateral motion starts
      // or stops, knobs.grip 1: a steady lateral rate asks a heading, not a curvature; C1 priced every sample of the move)
      // (knobs.grip 2: every sample of the move as C1, but only where the line itself uses more than GRIP_CORNER of the grip: in
      // a corner; on a straight the shift is the controller's to rate-limit)
      if (knobs.grip === 1 ? dirS !== mvS && (dirS !== 0 ? away : awayS) : eU !== ePrevS && away) {
        const k = env.curv(sMe), kk = k < 0 ? -k : k, ld = 3 + 0.25 * vL;
        const need = vL * vL * kk + vL * (knobs.gr ? rS : w.rate) / ld;
        if (need > w.aLat && (knobs.grip !== 2 || vL * vL * kk > GRIP_CORNER * w.aLat)) grip += knobs.gripW * (need / w.aLat - 1) * PLAN_DT;
      }
      mvS = dirS; awayS = away;
    }
    ePrevS = eU;
    // a car ahead in my band: capped behind it (its speed, my headway); braking onto it within the margin
    let capNow = 0;
    for (let k = 0; k < nN; k++) {
      const o = k * S + m, xq = X[o], xp = X[o - 1];
      if (xp - sMe <= w.front + w.nRear[k]) continue;           // not ahead of me (beside me: clearance below)
      if (knobs.r1 && (inv & (1 << k)) && !w.nIgnore[k]) continue;   // (C3 R1: a car from behind that passes me on the projection)
      const sep = LO[o] - (e + hw) > (e - hw) - HI[o] ? LO[o] - (e + hw) : (e - hw) - HI[o];
      if (sep >= FOLLOW_CLR) continue;
      const vq = (xq - xp) / PLAN_DT;
      if (!(capOn & (1 << k))) {
        // newly in my band in front of me: can I brake to its speed in the room to its bumper?
        const room = xq - (w.nRear[k] + w.front + 1) - sMe, dv2 = vMe * vMe - vq * vq;
        if (t <= (knobs.h3 ? w.tHard[k] : TH) && dv2 > 0 && (room <= 0.5 || dv2 / (2 * room) > w.bMax)) { w.culprit[c] = k; w.why[c] = 4; return BIG + PLAN_N - m + 0.5; }
      }
      capNow |= 1 << k;
      const cap = xq - (w.nRear[k] + w.front + 1.5 + hwy * (vq > 0 ? vq : 0));
      if (cap < sN) sN = cap > sMe ? cap : sMe;
      if (m === PLAN_N && vq < vR) { const r = 1 - (vq > 0 ? vq : 0) / (vR > 1 ? vR : 1); if (r > tailR) tailR = r; }
      // (C4 tlap) behind a clearly slower car at the end of the horizon: the rest of the lap behind it
      if (m === PLAN_N && knobs.tlap && w.nD[k] > 1 - CF) { const q = w.nD[k] * w.lapLeft; if (q > tailLap) tailLap = q; }
    }
    capOn = capNow;
    const dsMe = sN - sMe;
    lost += PLAN_DT - dsMe / (vR > 1 ? vR : 1);
    // (C3 R2) the passer's vortex: my body arriving alongside a neighbour inside its entry vortex (on its inside, after its
    // turn-in, before the apex) or its exit vortex (on its outside, after its apex, before its track-out), when I was not
    // alongside it at its turn-in (entry) / apex (exit): the dive it cannot see. The move is wrong (2 BIG within the window
    // knobs.tv; a steep cost beyond: the projection is a guess). Behind it in its wake, or alongside by its turn-in: allowed.
    if (vort) for (let k = 0; k < nN; k++) {
      const b = 1 << k;
      if (!(vort & b)) continue;
      const o = k * S + m, xq = X[o], rel = xq - sN;
      const ov = rel < w.front + w.nRear[k] && rel > -(w.rear + w.nFront[k]);
      if (!(vSeenIn & b) && xq >= w.vIn[k]) { vSeenIn |= b; if (ov) vOvIn |= b; }
      if (!(vSeenAp & b) && xq >= w.vAp[k]) { vSeenAp |= b; if (ov) vOvAp |= b; }
      if (!ov) continue;
      const dir = w.vDir[k], side = e - 0.5 * (LO[o] + HI[o]);
      let bad = false;
      if (xq <= w.vAp[k]) bad = (vSeenIn & b) !== 0 && !(vOvIn & b) && side * dir > 0;
      else if (xq <= w.vOut[k]) bad = (vSeenAp & b) !== 0 && !(vOvAp & b) && side * dir < 0;
      if (!bad) continue;
      // (knobs.vt 1: in the tier of the projection's conflicts, below a braking or clearance conflict at the same sample: when
      // backing out behind it would hit it, staying out is the least bad)
      if (t <= knobs.tv) { w.culprit[c] = -3; w.why[c] = 8; return (knobs.vt ? BIG + 0.25 : 2 * BIG) + PLAN_N - m; }
      clr += W * PLAN_DT;
    }
    // clearance to every neighbour my body overlaps along the track
    for (let k = 0; k < nN; k++) {
      if (inv & (1 << k)) continue;
      const o = k * S + m, rel = X[o] - sN;
      if (!(rel < w.front + w.nRear[k] + 1 && rel > -(w.rear + w.nFront[k] + 1))) continue;
      const cl = LO[o] - (e + hw) > (e - hw) - HI[o] ? LO[o] - (e + hw) : (e - hw) - HI[o];
      // a car alongside now owns its side: no move toward it into its margin
      if (cl < ALONG && mv !== 0 && w.nOwn[k] === mv) { w.culprit[c] = k; w.why[c] = 6; return 2 * BIG; }
      if (cl < LANE) {
        if (t <= (knobs.h3 ? w.tHard[k] : TH)) { w.culprit[c] = k; w.why[c] = 5; return BIG + PLAN_N - m + 0.5; }
        const q = 1 + (LANE - cl) / ALONG;
        clr += W * q * q * PLAN_DT;
        continue;
      }
      if (cl < ALONG) {
        const q = (ALONG - cl) / ALONG;
        clr += W * q * q * PLAN_DT;
      }
      // no-pass window: from behind to ahead of a running car inside it
      if (!w.nOff[k] && sN >= w.zoneLo && sMe <= w.zoneHi && X[o - 1] - sMe > 0 && rel <= 0) { w.culprit[c] = k; w.why[c] = 7; return 2 * BIG; }
    }
    vMe = dsMe / PLAN_DT;
    // (C4 P1) the overlap with the car attacked when I reach the braking point
    if (w.attK >= 0 && sN >= w.attDB && sMe < w.attDB) {
      w.attOv = sN + w.front - (X[w.attK * S + m] - w.nRear[w.attK]);
      for (let k = 0; k < nN; k++) w.attOvK[k] = sN + w.front - (X[k * S + m] - w.nRear[k]);
      attHit = true;
    }
    sMe = sN;
  }
  // (C5 T1) the landing beyond the horizon: each overlap carried on at the closing speed of the horizon's last interval
  if (w.attK >= 0 && !attHit) {
    const rem = w.attDB - sMe, tRem = rem / (vMe > 1 ? vMe : 1);
    for (let k = 0; k < nN; k++) { const o = k * S + PLAN_N, vq = (X[o] - X[o - 1]) / PLAN_DT; w.attOvK[k] = sMe + w.front - (X[o] - w.nRear[k]) + (vMe - vq) * tRem; }
  }
  // (C5 T2) the train pass in hand: ending the horizon held up behind the train costs every car of it still ahead of me, each at
  // its pace deficit over the rest of the lap
  if (w.trainHold && knobs.t1 && capOn) {
    let q = 0;
    for (let k = 0; k < nN; k++) if (w.nTrain[k] && X[k * S + PLAN_N] > sMe && w.nD[k] > 0) q += w.nD[k];
    q *= knobs.trainW * w.lapLeft;
    if (q > tailLap) tailLap = q;
  }
  // a pass that does not progress, or would take longer than PLAN_T_MAX (the cars I started behind and am now beside)
  let long = 0;
  for (let k = 0; k < nN; k++) {
    if ((inv & (1 << k)) || w.nOff[k]) continue;
    const rel0 = X[k * S], relN = X[k * S + PLAN_N] - sMe;
    if (rel0 <= 0) continue;
    const clear = w.rear + w.nFront[k] + 1;
    if (relN <= -clear || relN > LONG_NEAR) continue;            // past it, or not near it at the end of the horizon
    const o = k * S + PLAN_N, eEnd = eUp;
    const sep = LO[o] - (eEnd + hw) > (eEnd - hw) - HI[o] ? LO[o] - (eEnd + hw) : (eEnd - hw) - HI[o];
    if (sep < FOLLOW_CLR) continue;                              // still behind it in its band: following, not passing
    const gain = rel0 - relN;
    if (gain <= 0 || T + (relN + clear) * T / gain > PLAN_T_MAX) long = knobs.longW;
  }
  if (knobs.tail) { const q = tailR * knobs.tailT; lost += q > tailLap ? q : tailLap; tailR = 0; }
  if (planTally.on) {
    const q = c * 8, C = w.comp;
    C[q] = lost; C[q + 1] = clr; C[q + 2] = roadSoft; C[q + 3] = corr; C[q + 4] = grip; C[q + 5] = long; C[q + 6] = rev; C[q + 7] = cost - rev;
  }
  return cost + lost + clr + corr + grip + long;
}

/**
 * One plan: every candidate's cost, the minimum (ties to the current target), the hysteresis. Sets w.best, w.bestCost,
 * w.bestCulprit and returns the new target.
 */
export function plan(w: PlanWork, env: PlanEnv): number {
  candidates(w, env);
  let bi = 0;
  for (let c = 0; c < w.nC; c++) {
    w.cost[c] = candidateCost(w, env, c);
    if (w.cost[c] < w.cost[bi]) bi = c;
  }
  w.evaluated++;
  if (planTally.on && w.cost[0] >= BIG) planTally.n[w.why[0]]++;
  // commitment: a target is held MIN_HOLD s, and replaced only by one better by the margin (unless holding breaks a rule)
  // (C2 H4) a clearly faster car behind a clearly slower one commits at the aggressive margin, without the min hold
  const fast = knobs.h4 && w.cfPassing;
  if (bi !== 0 && w.cost[0] < BIG && ((w.locked && !fast) || w.cost[bi] > w.cost[0] - knobs.hystK * HYST[fast ? 2 : w.aggr])) bi = 0;
  // (C3 R1) told I am being passed: hold the target (never moved for the passer), unless holding breaks a rule
  if (bi !== 0 && w.frozen && w.cost[0] < BIG) bi = 0;
  // (C4 P3) alongside at the braking point: hold the side through the corner, unless holding breaks a rule
  if (bi !== 0 && w.attHold && w.cost[0] < BIG) bi = 0;
  w.best = w.cand[bi]; w.bestCost = w.cost[bi]; w.bestCulprit = w.culprit[bi];
  return w.best;
}

/**
 * (C4 P1) The early commit's feasibility, on the plan's own projection: the candidate "move to eAtt and hold it" (the lateral
 * move at the rate the grip leaves, capped behind any car in my band, the road clamping me) and where my nose is against the
 * tail of neighbour k when I reach the braking point dB m ahead (m past its tail; +Infinity when the braking point lies beyond
 * the horizon: a straight longer than it, checked again when it comes in). Returns the candidate's cost (>= BIG: a hard rule).
 */
export function attackOverlap(w: PlanWork, env: PlanEnv, k: number, eAtt: number, dB: number): number {
  w.cand[0] = eAtt; w.nC = 1;
  w.attK = k; w.attDB = dB; w.attOv = Number.POSITIVE_INFINITY; w.attOvK.fill(Number.NEGATIVE_INFINITY);
  const c = candidateCost(w, env, 0);
  w.attK = -1;
  return c;
}

/**
 * (C5 T1 / T2) The train pass on the plan's own projection: "move to eAtt clear of the whole train and hold it" (trainHold: no
 * merge back after the first car; judged as a pass, not a block of a faster car behind), and where my nose is against each car of
 * the train at the landing point dChk m ahead. ks[0..nK) are the train's neighbour indices in order from the car ahead (-1: passed
 * or not a neighbour). Returns the furthest q <= upTo whose tail my nose passes by ovlM (the target), -1 when none (no landing),
 * -2 when the move breaks a hard rule (w.why[0] says which).
 */
export function trainTarget(w: PlanWork, env: PlanEnv, ks: Int32Array, nK: number, upTo: number, eAtt: number, dChk: number, ovlM: number): number {
  const cfp = w.cfPassing, th = w.trainHold, ea = w.eAtt;
  w.trainHold = true; w.eAtt = eAtt; w.cfPassing = true;
  let k0 = -1;
  for (let q = 0; q < nK && k0 < 0; q++) k0 = ks[q];
  const c = k0 >= 0 ? attackOverlap(w, env, k0, eAtt, dChk) : 2 * BIG;
  w.trainHold = th; w.eAtt = ea; w.cfPassing = cfp;
  if (c >= BIG) return -2;
  let t = -1;
  for (let q = 0; q <= upTo && q < nK; q++) if (ks[q] >= 0 && w.attOvK[ks[q]] >= ovlM) t = q;
  return t;
}

/**
 * (C4 P1 pick) Another neighbour than k in the attack band [eAtt ± (hw + LANE_CLR)] beside where I will be when I reach the
 * braking point dB m ahead (at my present speed, the horizon's last sample at most): that side is taken.
 */
export function bandTaken(w: PlanWork, k: number, eAtt: number, dB: number, skipTrain = false): boolean {
  const vv = w.v > 5 ? w.v : 5, m0 = Math.round(dB / vv / PLAN_DT), m = m0 < 0 ? 0 : m0 > PLAN_N ? PLAN_N : m0, sAt = dB < vv * PLAN_N * PLAN_DT ? dB : vv * PLAN_N * PLAN_DT;
  for (let q = 0; q < w.nN; q++) {
    if (q === k || w.nOff[q] || (skipTrain && w.nTrain[q])) continue;
    const o = q * S + m, rel = w.X[o] - sAt;
    if (rel > w.front + w.nRear[q] + 3 || rel < -(w.rear + w.nFront[q] + 3)) continue;
    if (w.HI[o] > eAtt - w.hw - knobs.laneClr && w.LO[o] < eAtt + w.hw + knobs.laneClr) return true;
  }
  return false;
}

/**
 * (C4 P1-P3) The attack's next phase. ov: m my nose is past the tail of the car I attack (negative: behind it); dB / dAp / dOut:
 * m to the braking point, apex and track-out of the corner the commit was made for; reach: m I cover before the next check.
 * COMMIT: at the braking point (dB <= reach + knobs.bo) with the overlap, HOLD (P3); without it, BACK (P2). HOLD ends at the
 * track-out, BACK past the apex (re-plan after the corner): NONE.
 */
export function attackNext(phase: number, ov: number, ovl: number, dB: number, dAp: number, dOut: number, reach: number, dTi = Number.NaN, ovlTi = Number.NEGATIVE_INFINITY): number {
  if (phase === ATT_COMMIT) {
    if (dB > reach + knobs.bo) return ATT_COMMIT;
    return ov >= ovl && knobs.p3 ? ATT_HOLD : knobs.p2 ? ATT_BACK : ATT_NONE;
  }
  // (C5 T3) holding: at the target's turn-in without ovlTi of overlap, back out behind it
  if (phase === ATT_HOLD) return dOut < 0 ? ATT_NONE : dTi > 0 && dTi <= reach && ov < ovlTi ? ATT_BACK : ATT_HOLD;
  if (phase === ATT_BACK) return dAp < 0 ? ATT_NONE : ATT_BACK;
  return ATT_NONE;
}

/** (C4 P4) Nobody within knobs.ret m ahead and nobody my body overlaps now (or MERGE_GAP behind my rear): the racing line, no plan. */
export function lineFree(w: PlanWork): boolean {
  for (let k = 0; k < w.nN; k++) {
    const x = w.X[k * S];
    if (x < knobs.ret + w.front + w.nRear[k] && x > -(w.rear + w.nFront[k] + knobs.mergeGap)) return false;
    // (knobs.retT: ... nor one I reach within ret m of in retT s at my speed now, on its projection)
    if (knobs.retT > 0 && x > 0) {
      const m = Math.min(PLAN_N, Math.round(knobs.retT / PLAN_DT));
      if (w.X[k * S + m] - w.v * m * PLAN_DT < knobs.ret + w.front + w.nRear[k]) return false;
    }
  }
  return true;
}

/** (tools) Set knobs from "name=value" strings; an unknown name throws (a typo must not run a screen on the defaults). */
export function setKnobs(kvs: string[]): void {
  for (const kv of kvs) {
    const [k, v] = kv.split('=');
    if (!(k in knobs) || !Number.isFinite(Number(v))) throw new Error(`planner knob ${kv}: unknown name or not a number`);
    (knobs as Record<string, number>)[k] = Number(v);
  }
}
