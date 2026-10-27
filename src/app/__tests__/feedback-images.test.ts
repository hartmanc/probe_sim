// The report's picture parts that need no canvas: paste extraction, the 3-picture cap, the size gates, the encoder loop.
import { describe, expect, test } from 'vitest';
import {
  MAX_BODY_BYTES, MAX_PICTURE_BYTES, TARGET_BYTES, bodyProblem, buildFeedback, fitSize, imagesFromClipboard, pictureSizeProblem, preparePicture, takePictures,
  type JpegEncoder,
} from '../feedback';

const file = (name: string, type: string) => new File(['x'], name, { type });
const item = (kind: string, type: string, f: File | null) => ({ kind, type, getAsFile: () => f });

describe('pasted images', () => {
  test('takes image files from clipboardData items, ignores text and non-images', () => {
    const a = file('a.png', 'image/png'), b = file('b.jpg', 'image/jpeg');
    const got = imagesFromClipboard({ items: [item('string', 'text/plain', null), item('file', 'image/png', a), item('file', 'application/pdf', file('c.pdf', 'application/pdf')), item('file', 'image/jpeg', b), item('file', 'image/gif', null)] });
    expect(got).toEqual([a, b]);
  });
  test('falls back to files; null and empty give nothing', () => {
    const a = file('a.webp', 'image/webp');
    expect(imagesFromClipboard({ files: [a, file('t.txt', 'text/plain')] })).toEqual([a]);
    expect(imagesFromClipboard(null)).toEqual([]);
    expect(imagesFromClipboard({ items: [] })).toEqual([]);
  });
});

describe('the 3-picture cap', () => {
  test('room for the rest, the surplus is counted', () => {
    expect(takePictures(0, [1, 2])).toEqual({ take: [1, 2], dropped: 0 });
    expect(takePictures(2, [1, 2, 3])).toEqual({ take: [1], dropped: 2 });
    expect(takePictures(3, [1])).toEqual({ take: [], dropped: 1 });
  });
});

describe('size gates', () => {
  test('a picture over 900 KB is refused, 900 KB passes', () => {
    expect(pictureSizeProblem(MAX_PICTURE_BYTES)).toBeNull();
    expect(pictureSizeProblem(MAX_PICTURE_BYTES + 1)).toMatch(/too big/);
  });
  test('the body over 2.5 MB is refused with a message, counting bytes not characters', () => {
    expect(bodyProblem('x'.repeat(1000))).toBeNull();
    expect(bodyProblem('x'.repeat(MAX_BODY_BYTES + 1))).toMatch(/too large/);
    expect(bodyProblem('é'.repeat(MAX_BODY_BYTES / 2 + 1))).toMatch(/too large/);
  });
  test('downscale keeps the aspect, caps the longest side at 1600, never enlarges', () => {
    expect(fitSize(4000, 3000)).toEqual({ w: 1600, h: 1200 });
    expect(fitSize(800, 600)).toEqual({ w: 800, h: 600 });
  });
});

describe('preparePicture (encoder injected)', () => {
  test('first try is 1600 px at 0.85; lands under target and stops', async () => {
    const calls: [number, number][] = [];
    const enc: JpegEncoder = async (_f, side, q) => { calls.push([side, q]); return { bytes: TARGET_BYTES - 1, data: 'QUJD' }; };
    const r = await preparePicture(file('My Shot (1).PNG', 'image/png'), enc);
    expect(calls).toEqual([[1600, 0.85]]);
    expect(r).toMatchObject({ ok: true, pic: { type: 'image/jpeg', data: 'QUJD', name: 'My_Shot_1_.jpg' } });
  });
  test('retries smaller when over 600 KB, accepts up to 900 KB, refuses beyond', async () => {
    const sizes = [700, 650, 880, 880].map((k) => k * 1024);
    let i = 0;
    const enc: JpegEncoder = async () => ({ bytes: sizes[i++], data: 'QQ==' });
    const ok = await preparePicture(file('a.jpg', 'image/jpeg'), enc);
    expect(ok.ok).toBe(true);
    expect(i).toBe(4);
    const huge: JpegEncoder = async () => ({ bytes: MAX_PICTURE_BYTES + 5000, data: 'QQ==' });
    expect(await preparePicture(file('big.jpg', 'image/jpeg'), huge)).toMatchObject({ ok: false, reason: expect.stringContaining('too big') });
    const boom: JpegEncoder = async () => { throw new Error('decode'); };
    expect(await preparePicture(file('x.heic', 'image/heic'), boom)).toMatchObject({ ok: false });
  });
  test('the payload carries at most 3 images and omits the key when none', () => {
    const base = { kind: 'bug' as const, description: 'd', version: '1', sha: '', track: 't', device: 'desktop', ua: '', screen: '', error: null, name: null, secret: undefined };
    const pic = { name: 'a.jpg', type: 'image/jpeg' as const, data: 'QQ==' };
    expect(buildFeedback(base).images).toBeUndefined();
    expect(buildFeedback({ ...base, images: [pic, pic, pic, pic] }).images).toHaveLength(3);
  });
});
