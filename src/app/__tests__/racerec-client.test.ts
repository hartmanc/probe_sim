// Race recordings, the app's side (src/app/race-record.ts): the dev switch, the owner token, the upload.
import { describe, expect, it } from 'vitest';
import { LS_OWNER_TOKEN, ownerToken, parseRecordMode, racesUrl, uploadRecording } from '../race-record';
import { gunzipCapped, type RaceRecording } from '../../scoreboard/racerec';

const mem = () => { const m = new Map<string, string>(); return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => { m.set(k, v); }, m }; };
const TOKEN = 'abcdefghijklmnopqrstuvwxyz012345';

describe('?record=', () => {
  it('on by default, 0 switches it off, download offers the file', () => {
    expect(parseRecordMode('')).toBe('on');
    expect(parseRecordMode('?seed=4')).toBe('on');
    expect(parseRecordMode('?record=0')).toBe('off');
    expect(parseRecordMode('?record=download')).toBe('download');
  });
});

describe('owner token', () => {
  it('?owner= stores a well-formed token, a stored one is used, junk is not', () => {
    const s = mem();
    expect(ownerToken('', s)).toBeNull();
    expect(ownerToken('?owner=short', s)).toBeNull();
    expect(ownerToken(`?owner=${TOKEN}`, s)).toBe(TOKEN);
    expect(s.m.get(LS_OWNER_TOKEN)).toBe(TOKEN);
    expect(ownerToken('', s)).toBe(TOKEN);
    expect(ownerToken('', null)).toBeNull();
    expect(ownerToken(`?owner=${TOKEN}`, { getItem: () => { throw new Error('private'); }, setItem: () => { throw new Error('private'); } })).toBe(TOKEN);
  });
});

describe('uploadRecording', () => {
  const rec = { v: 1, trackId: 'laguna_seca', inputs: { rows: [], steps: 10, ref: [] }, live: { crossings: [], lapTimes: [], results: null }, config: {}, owner: false, durationS: 1 } as unknown as RaceRecording;
  it('posts one gzipped body to /api/races with the owner token header only when there is one, and is silent on failure', async () => {
    expect(racesUrl('/api/scores')).toBe('/api/races');
    expect(racesUrl('http://localhost:3000/api/scores')).toBe('http://localhost:3000/api/races');
    const calls: { url: string; init: RequestInit }[] = [];
    const ok = async (url: string, init?: RequestInit) => { calls.push({ url, init: init! }); return new Response(null, { status: 204 }); };
    expect(await uploadRecording(rec, { fetchFn: ok, token: TOKEN })).toBe(true);
    expect(await uploadRecording(rec, { fetchFn: ok })).toBe(true);
    expect(calls[0].url).toBe('/api/races');
    expect((calls[0].init.headers as Record<string, string>)['Content-Type']).toBe('application/gzip');
    expect((calls[0].init.headers as Record<string, string>)['X-Owner-Token']).toBe(TOKEN);
    expect((calls[1].init.headers as Record<string, string>)['X-Owner-Token']).toBeUndefined();
    expect(JSON.parse((await gunzipCapped(calls[0].init.body as Uint8Array, 1e6))!).trackId).toBe('laguna_seca');
    expect(await uploadRecording(rec, { fetchFn: async () => new Response('x', { status: 429 }) })).toBe(false);
    expect(await uploadRecording(rec, { fetchFn: async () => { throw new Error('offline'); } })).toBe(false);
  });
});
