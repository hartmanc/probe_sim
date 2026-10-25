// Which circuit this page runs: ?track=<id> (a TRACKS id, src/scoreboard/config.ts), else the default. Fixed for the
// page's life: picking another track in the Start menu reloads the page with the new ?track=.
import { DEFAULT_TRACK, TRACKS, resolveTrackId, type TrackInfo } from '../scoreboard/config';

const search = typeof location !== 'undefined' ? location.search : '';
export const TRACK_ID: string = resolveTrackId(new URLSearchParams(search).get('track'));
export const TRACK: TrackInfo = TRACKS[TRACK_ID];
/** Ids of the tracks the Start menu offers, registry order: every registered track that is not work in progress
 *  (TrackInfo.wip; a wip track still loads from its ?track= link). */
export const TRACK_IDS: readonly string[] = Object.keys(TRACKS).filter((id) => !TRACKS[id].wip);

/** This page's URL with another track (the default track drops the parameter). */
export function urlForTrack(id: string): string {
  const u = new URL(location.href);
  if (id === DEFAULT_TRACK) u.searchParams.delete('track'); else u.searchParams.set('track', id);
  return u.toString();
}
