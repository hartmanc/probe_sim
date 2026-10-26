// 0.4.0 client pieces: the error capture, the report payload, the WebGL 2 check, How to play and the fixed credits.
import { describe, expect, test } from 'vitest';
import { describeError, installErrorCapture, lastError, recordError } from '../errors';
import { buildFeedback, MAX_DESCRIPTION } from '../feedback';
import { webgl2Available } from '../webgl';
import { howtoSections } from '../howto';
import { ABOUT, DATA_CREDITS, NC_STATEMENT, PRIVACY, SOFTWARE_CREDITS, creditLine } from '../credits';

const text = (s: { lines: (string | { text: string })[] }) => s.lines.map((l) => (typeof l === 'string' ? l : l.text)).join(' ');

describe('error capture', () => {
  test('keeps the last uncaught error and rejection, trimmed', () => {
    const handlers: Record<string, (e: unknown) => void> = {};
    installErrorCapture({ addEventListener: (t: string, h: (e: unknown) => void) => { handlers[t] = h; } } as never);
    handlers.error({ error: new TypeError('boom'), message: 'boom' });
    expect(lastError()).toMatch(/^error: TypeError: boom/);
    handlers.unhandledrejection({ reason: 'nope' });
    expect(lastError()).toMatch(/^unhandled rejection: nope/);
    recordError(new Error('x'.repeat(5000)));
    expect(describeError(new Error('x'.repeat(5000))).length).toBeLessThanOrEqual(1500);
  });
});

describe('report payload', () => {
  const base = { kind: 'bug' as const, description: '  The T11 wall  ', version: '0.4.0', sha: 'abc1234', track: 'sonoma', device: 'phone', ua: 'UA', screen: '1x1@1', error: null as string | null, name: null as string | null, secret: undefined as string | undefined };
  test('context attached; the name only with a secret; no email field', () => {
    const p = buildFeedback(base);
    expect(p).toEqual({ kind: 'bug', description: 'The T11 wall', context: { version: '0.4.0', sha: 'abc1234', track: 'sonoma', device: 'phone', ua: 'UA', screen: '1x1@1' } });
    expect(buildFeedback({ ...base, name: 'Coby' }).name).toBeUndefined();
    const q = buildFeedback({ ...base, name: 'Coby', secret: 'a'.repeat(32), error: 'TypeError' });
    expect(q).toMatchObject({ name: 'Coby', secret: 'a'.repeat(32), context: { error: 'TypeError' } });
    expect(JSON.stringify(q)).not.toMatch(/mail/i);
    expect(buildFeedback({ ...base, description: 'y'.repeat(5000) }).description).toHaveLength(MAX_DESCRIPTION);
  });
});

describe('WebGL 2 check', () => {
  test('false without a context or when getContext throws, true with one', () => {
    const doc = (gl: unknown) => ({ createElement: () => ({ getContext: () => { if (gl === 'throw') throw new Error('x'); return gl; } }) }) as never;
    expect(webgl2Available(doc(null))).toBe(false);
    expect(webgl2Available(doc('throw'))).toBe(false);
    expect(webgl2Available(doc({ getExtension: () => null }))).toBe(true);
  });
});

describe('How to play and Credits', () => {
  test('How to play covers controls, modes, the scoreboard and the phone field', () => {
    const s = howtoSections({ raceLaps: 5, touch: false, fieldLine: '40 of 133 cars on this device' });
    expect(s.map((x) => x.title)).toEqual(['The car', 'Controls', 'Modes', 'Scoreboard']);
    expect(s[2].lines.join(' ')).toMatch(/40 of 133 cars on this device/);
    expect(s[3].lines.join(' ')).toMatch(/transfer code/);
  });
  test('the fixed credits: disclaimer, opt-out contact, data, software, NC statement, privacy', () => {
    expect(text(ABOUT)).toContain('An unofficial fan project, not affiliated with 24 Hours of Lemons, the circuits or the teams shown');
    expect(text(ABOUT)).toContain('cobylhartman@gmail.com');
    expect(text(ABOUT)).toContain('github.com/hartmanc/probe_sim/issues');
    expect(text(DATA_CREDITS)).toMatch(/© OpenStreetMap contributors.*ODbL/);
    expect(text(DATA_CREDITS)).toMatch(/3DEP.*public domain/);
    expect(text(DATA_CREDITS)).toMatch(/NAIP.*public domain/);
    expect(text(SOFTWARE_CREDITS)).toMatch(/three\.js.*MIT/);
    expect(text(SOFTWARE_CREDITS)).toMatch(/postprocessing.*zlib/i);
    expect(NC_STATEMENT).toMatch(/no ads, no sponsorship and no sales/);
    expect(NC_STATEMENT).toMatch(/same licence/);
    for (const k of ['name you type', 'device id', 'hash', '10 minutes', 'Report button', 'Analytics', 'without cookies']) expect(text(PRIVACY)).toContain(k);
  });
  test('engine-sound sources show the channel when recorded', () => {
    expect(creditLine({ title: 'Onboard', channel: 'SomeChannel', url: 'https://youtu.be/x', licence: 'CC BY 3.0' }, 'Engine sound')).toMatchObject({ author: 'SomeChannel', licence: 'CC BY 3.0', url: 'https://youtu.be/x' });
  });
});
