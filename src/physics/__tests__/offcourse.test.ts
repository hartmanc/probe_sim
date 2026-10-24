// Round 14B (Sonoma's T9A escape road): a paved part marked off_course is paved and drivable (pavement grip, its own
// profile) but SurfaceSample.offCourse is set, so the lap-validity checks count a car on it as off the course; an
// unmarked part, the track and the dirt are unchanged (offCourse false).
import { describe, expect, it } from 'vitest';
import { createTrackSurface } from '../index';
import { continuation, heightfieldOf, ovalTrack, stripPart } from './terrain_fixture';

const track = ovalTrack();
const hf = heightfieldOf(track, continuation);
const surf = (off: boolean) => createTrackSurface(track, hf, { pitLane: { spacing_m: 1, fractions: track.profile.fractions, parts: [{ ...stripPart(continuation), ...(off ? { off_course: true } : {}) }] } });

describe('off-course paving', () => {
  it('a part marked off_course is paved with pavement grip but off the course', () => {
    const a = surf(true).sample(0, -11), b = surf(false).sample(0, -11);
    expect(a.paved).toBe(true); expect(a.offCourse).toBe(true);
    expect(b.paved).toBe(true); expect(b.offCourse).toBe(false);
    expect(a.mu).toBe(b.mu); expect(a.z).toBe(b.z);
  });
  it('the track and the dirt are not off-course paving', () => {
    const s = surf(true);
    const t = s.sample(0, 0); expect(t.onTrack).toBe(true); expect(t.offCourse).toBe(false);
    const d = s.sample(0, -30); expect(d.paved).toBe(false); expect(d.offCourse).toBe(false);
  });
});
