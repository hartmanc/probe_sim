import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { APP_VERSION, CHANGELOG, compareSemver, formatDate, isSemver, validateChangelog, versionLine, type ChangeEntry } from '../changelog';

describe('change log data', () => {
  it('is well-formed: newest first, versions falling, dates not rising, every entry has items', () => {
    expect(validateChangelog(CHANGELOG)).toEqual([]);
  });

  it('APP_VERSION is the newest entry and package.json mirrors it', () => {
    expect(APP_VERSION).toBe(CHANGELOG[0].version);
    const pkg = JSON.parse(readFileSync(fileURLToPath(new URL('../../../package.json', import.meta.url)), 'utf8')) as { version: string };
    expect(pkg.version).toBe(APP_VERSION);
  });

  it('entries that reset lap times name the circuit', () => {
    for (const e of CHANGELOG) if (e.resets) expect(e.resets.every((r) => r.length > 0)).toBe(true);
  });
});

describe('change log helpers', () => {
  it('semver parse and compare', () => {
    expect(isSemver('0.3.1')).toBe(true);
    expect(isSemver('0.3')).toBe(false);
    expect(isSemver('v0.3.1')).toBe(false);
    expect(compareSemver('0.3.1', '0.3.0')).toBeGreaterThan(0);
    expect(compareSemver('0.10.0', '0.9.9')).toBeGreaterThan(0);
    expect(compareSemver('1.0.0', '1.0.0')).toBe(0);
  });

  it('formats ISO dates without a Date object', () => {
    expect(formatDate('2026-10-19')).toBe('19 Oct 2026');
    expect(formatDate('2026-01-05')).toBe('5 Jan 2026');
    expect(formatDate('yesterday')).toBe('yesterday');
  });

  it('version line shows the short commit only when known', () => {
    expect(versionLine('0.3.1')).toBe('v0.3.1');
    expect(versionLine('0.3.1', '')).toBe('v0.3.1');
    expect(versionLine('0.3.1', '1ffcd93abcdef')).toBe('v0.3.1 · 1ffcd93');
  });

  it('validation catches the mistakes a hand-edited log makes', () => {
    const ok: ChangeEntry[] = [{ version: '0.2.0', date: '2026-10-18', title: 'b', items: ['x'] }, { version: '0.1.0', date: '2026-10-17', title: 'a', items: ['y'] }];
    expect(validateChangelog(ok)).toEqual([]);
    expect(validateChangelog([ok[1], ok[0]])).toContain('0.1.0 is not newer than 0.2.0');
    expect(validateChangelog([{ ...ok[0], date: '2026-10-16' }, ok[1]])).toContain('0.2.0 is dated before 0.1.0');
    expect(validateChangelog([{ ...ok[0], version: '0.2' }])).toContain('0.2: not MAJOR.MINOR.PATCH');
    expect(validateChangelog([{ ...ok[0], items: [] }])).toContain('0.2.0: empty item');
    expect(validateChangelog([{ ...ok[0], resets: [] }])).toContain('0.2.0: empty resets');
    expect(validateChangelog([])).toContain('no entries');
  });
});
