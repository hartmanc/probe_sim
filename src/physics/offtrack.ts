// Lost in the hills (owner, 23 Oct 2026: "shoot the user into space if they drive way off the track bounds. Just like
// when they smash into a wall at speed"). The player's car is launched like a hard wall hit once it has been far off
// the track for OFFTRACK_HOLD_S of sim time. "Far" comes from the track data, not one track's numbers:
//   - outside the near heightfield (track.json `heightfield`, the modelled terrain band; beyond it only the coarse far
//     grid), or
//   - more than the local limit past the nearer track.json edge: OFFTRACK_FAR_M, raised where the track's own
//     containment (scenery armco, concrete, tyre walls) stands farther out than that, to that barrier's distance plus
//     OFFTRACK_BARRIER_MARGIN_M, so a car in a wide runoff in front of its barrier is never "far" (Laguna's T2, T6 and
//     Rainey runoffs end at armco 45-71 m from the edge; Sonoma's widest at concrete 46-91 m);
//   - and every wheel off any pavement (the caller decides that: pit lane and paved zones never count).
// HotlapSim applies it to the player only; AI cars never see it. Pure (no DOM).
import { createEdgeDistance, type HeightGrid, type TrackJson } from './track';

/** Default "far": metres past the nearer track edge (a track can set its own: TrackInfo.offTrackFarM). */
export const OFFTRACK_FAR_M = 40;
/** Sim time the car must stay far off before it is launched, s: a brief excursion past the limit does not count. */
export const OFFTRACK_HOLD_S = 2;
/** Where a containment barrier stands beyond OFFTRACK_FAR_M, the limit is that barrier's distance plus this, m. */
export const OFFTRACK_BARRIER_MARGIN_M = 10;
/** A barrier raises the limit over this many metres of track either side of its nearest station. */
export const OFFTRACK_BARRIER_REACH_M = 30;
/** Barrier kinds that contain a runoff (fences and pit walls do not: catch fences stand by the spectators). */
const CONTAINMENT = new Set(['armco', 'concrete', 'tyres']);

export interface OffTrackOptions {
  /** Default limit past the edge, m (OFFTRACK_FAR_M). */
  farM?: number;
  /** Near heightfield grid; outside it counts as far (default track.json `heightfield`; null = no grid test). */
  grid?: HeightGrid | null;
  /** scenery.json `barriers` (containment kinds raise the local limit). */
  barriers?: readonly { kind: string; pts: readonly (readonly number[])[] }[] | null;
}

export interface OffTrackJudge {
  /** True when (x, y) is far off the track. */
  far(x: number, y: number): boolean;
  /** Horizontal unit vector away from the track at the last far() query (the launch direction). */
  readonly away: { x: number; y: number };
  /** The limit past the edge at centreline segment `seg` on `side` (+1 left, -1 right), m. */
  limit(seg: number, side: 1 | -1): number;
}

/** The far-off-track test for one track. */
export function createOffTrackJudge(track: TrackJson, opts: OffTrackOptions = {}): OffTrackJudge {
  const farM = opts.farM ?? OFFTRACK_FAR_M;
  const grid = opts.grid === undefined ? track.heightfield : opts.grid;
  const edge = createEdgeDistance(track);
  const n = track.n, reach = Math.ceil(OFFTRACK_BARRIER_REACH_M / (track.spacing_m || 1));
  const limL = new Float64Array(n).fill(farM), limR = new Float64Array(n).fill(farM);
  for (const b of opts.barriers ?? []) {
    if (!CONTAINMENT.has(b.kind)) continue;
    for (const p of b.pts) {
      const e = edge(p[0], p[1]);
      const lim = e.d + OFFTRACK_BARRIER_MARGIN_M;
      if (lim <= farM) continue;
      const arr = e.side > 0 ? limL : limR;
      for (let k = -reach; k <= reach; k++) {
        const i = (((e.seg + k) % n) + n) % n;
        if (lim > arr[i]) arr[i] = lim;
      }
    }
  }
  const away = { x: 0, y: 0 };
  const outsideGrid = (x: number, y: number): boolean => {
    if (!grid) return false;
    const fx = (x - grid.x0) / grid.dx, fy = (y - grid.y0) / grid.dx;
    return !(fx >= 0 && fy >= 0 && fx <= grid.nx - 1 && fy <= grid.ny - 1);
  };
  return {
    away,
    limit: (seg, side) => (side > 0 ? limL : limR)[seg],
    far(x, y) {
      const e = edge(x, y);
      away.x = e.ux; away.y = e.uy;
      return e.d > (e.side > 0 ? limL : limR)[e.seg] || outsideGrid(x, y);
    },
  };
}

/** Holds the "far" state: update() turns true once, after `far` has held for holdS of (sim) time; any tick back
 *  inside starts the count again; reset() re-arms it. */
export class OffTrackWatch {
  private held = 0;
  private fired = false;
  constructor(readonly holdS = OFFTRACK_HOLD_S) {}
  update(far: boolean, dt: number): boolean {
    if (this.fired) return false;
    this.held = far ? this.held + dt : 0;
    if (this.held >= this.holdS - 1e-9) { this.fired = true; return true; }
    return false;
  }
  /** Seconds far off so far (0 when inside). */
  get heldS(): number { return this.held; }
  reset(): void { this.held = 0; this.fired = false; }
}
