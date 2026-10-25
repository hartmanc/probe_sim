import { describe, expect, it } from 'vitest';
import { TRACK_IDS } from '../track-choice';
import { DEFAULT_TRACK, TRACKS, resolveTrackId } from '../../scoreboard/config';

// A publish can carry a circuit that is still being iterated on its branch without releasing it (TrackInfo.wip, owner,
// 25 Oct 2026: Buttonwillow stays out of the 0.3.0 Start menu while Sonoma ships).
describe('track choice: the Start menu offers every registered track that is not work in progress', () => {
  it('TRACK_IDS is the registry without its wip tracks, in registry order', () => {
    expect(TRACK_IDS).toEqual(Object.keys(TRACKS).filter((id) => !TRACKS[id].wip));
    for (const id of TRACK_IDS) expect(TRACKS[id].wip).toBeFalsy();
  });

  it('the released circuits are offered and the default is one of them', () => {
    expect(TRACK_IDS).toContain('laguna_seca');
    expect(TRACK_IDS).toContain('sonoma');
    expect(TRACK_IDS).toContain(DEFAULT_TRACK);
  });

  it('a wip track is registered (its ?track= link still loads it) but not offered', () => {
    const wip = Object.keys(TRACKS).filter((id) => TRACKS[id].wip);
    for (const id of wip) {
      expect(TRACK_IDS).not.toContain(id);
      expect(resolveTrackId(id)).toBe(id);
    }
  });
});
