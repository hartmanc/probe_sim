// Rollover game over (owner game note, 21-22 Oct 2026): "we should make a game over screen (just like when you blast
// into space) if you roll the car"; exact text from the owner. Pure (no DOM): index.ts shows it with hud.showGameOver.
import { isRolledOver } from '../physics/rollover';

export const ROLLOVER_LINE = 'You are banned from Lemons for one year for rolling your hooptie';
/** GAME OVER this long after the car first rolls over (the launch screen waits 2.5 s while the camera follows). */
export const ROLLOVER_DELAY_MS = 1500;

/** Watches the player's car: show() turns true once, ROLLOVER_DELAY_MS after its roll first passes the physics'
 *  rollover state (|roll relative to the road| > 60 deg, the kerb gate's `rolledOver`); reset() re-arms it. */
export class RolloverWatch {
  private seenAt = -1;
  private shown = false;
  /** quat: the car body's [x, y, z, w]; normal: the road normal under the car; now: ms. True when the screen is due. */
  update(quat: readonly number[], normal: readonly number[], now: number): boolean {
    if (this.shown) return false;
    if (this.seenAt < 0 && isRolledOver(quat, normal)) this.seenAt = now;
    if (this.seenAt >= 0 && now - this.seenAt >= ROLLOVER_DELAY_MS) { this.shown = true; return true; }
    return false;
  }
  get rolled(): boolean { return this.seenAt >= 0; }
  reset(): void { this.seenAt = -1; this.shown = false; }
}
