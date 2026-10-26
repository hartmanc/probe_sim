// Name ownership primitives (owner.ts) and the whitelists (Object.hasOwn, not `in`).
import { describe, expect, test } from 'vitest';
import { CODE_ALPHABET, CODE_LEN, adopt, claim, issueCode, newTransferCode, normalizeCode, ownership, secretHash } from '../owner';
import { MemoryStore } from '../store';
import { parseBoardKey, validateSubmission } from '../validate';
import { resolveTrackId } from '../config';

const A = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', B = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';

describe('device secret and transfer code', () => {
  test('a claimed name answers you / other; free before; the hash is not the secret', async () => {
    const s = new MemoryStore();
    expect(await ownership(s, 'coby', A)).toBe('free');
    expect(await claim(s, 'coby', A)).toBe(true);
    expect(await claim(s, 'coby', B)).toBe(false);
    expect(await ownership(s, 'coby', A)).toBe('you');
    expect(await ownership(s, 'coby', B)).toBe('other');
    expect(await ownership(s, 'coby', undefined)).toBe('other');
    expect(await secretHash(A)).toMatch(/^[0-9a-f]{64}$/);
    expect(await s.kvGet('sb:own:coby')).not.toContain(A);
  });
  test('codes: six characters of the unambiguous alphabet, uniform-ish, typed loosely', () => {
    const seen = new Set<string>();
    for (let i = 0; i < 2000; i++) {
      const c = newTransferCode();
      expect(c).toHaveLength(CODE_LEN);
      for (const ch of c) { expect(CODE_ALPHABET).toContain(ch); seen.add(ch); }
    }
    expect(seen.size).toBe(CODE_ALPHABET.length);
    expect(normalizeCode(' k7m-4qx ')).toBe('K7M4QX');
    expect(normalizeCode('K7M4Q0')).toBeNull();   // 0 is not in the alphabet
    expect(normalizeCode('K7M4Q')).toBeNull();
    expect(normalizeCode(123456)).toBeNull();
  });
  test('adopt: right code adds the device, consumes the code; expired codes fail', async () => {
    let now = 0;
    const s = new MemoryStore(() => now);
    await claim(s, 'coby', A);
    const code = await issueCode(s, 'coby');
    expect(await adopt(s, 'coby', 'ZZZZZZ', B)).toBe('bad-code');
    expect(await adopt(s, 'other', code, B)).toBe('bad-code');      // a code is bound to its name
    expect(await adopt(s, 'coby', code, B)).toBe('ok');
    expect(await ownership(s, 'coby', B)).toBe('you');
    expect(await ownership(s, 'coby', A)).toBe('you');
    expect(await adopt(s, 'coby', code, 'cccccccccccccccccccccccccccccccc')).toBe('bad-code');
    const c2 = await issueCode(s, 'coby');
    now += 3601_000;
    expect(await adopt(s, 'coby', c2, 'cccccccccccccccccccccccccccccccc')).toBe('bad-code');
  });
});

describe('whitelists use own properties only', () => {
  test('prototype names are not tracks or cars', () => {
    for (const t of ['constructor', 'toString', '__proto__', 'hasOwnProperty']) {
      expect(parseBoardKey(`hotlap:${t}:probe_gt:abc`)).toBeNull();
      expect(parseBoardKey(`hotlap:laguna_seca:${t}:abc`)).toBeNull();
      expect(resolveTrackId(t)).toBe('laguna_seca');
      const v = validateSubmission({ mode: 'hotlap', track: t, car: t, physics: 'abc', name: 'x', input: 'pad' });
      expect(v.reasons).toContain('unknown track');
      expect(v.reasons).toContain('unknown car');
    }
  });
});
