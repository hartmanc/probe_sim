import { describe, expect, it } from 'vitest';
import { CENSOR_COLS, CENSOR_ROWS, TITLE_ACCESSIBLE_NAME, censorLevels, censoredBlock, censoredTitleNodes, revealCensor } from '../censor';

// vitest runs in node: a tiny element stand-in is enough for the builders
class FakeEl {
  className = ''; width = 0; height = 0; dataset: Record<string, string> = {}; attrs: Record<string, string> = {};
  children: unknown[] = []; textContent = ''; ownerDocument: FakeDoc; parent: FakeEl | null = null;
  constructor(public tag: string, doc: FakeDoc) { this.ownerDocument = doc; }
  setAttribute(k: string, v: string) { this.attrs[k] = v; }
  removeAttribute(k: string) { delete this.attrs[k]; }
  getContext() { return null; }
  matches(sel: string) { return sel === '[data-censored]' && this.dataset.censored === 'true'; }
  querySelector() { return null; }
  replaceWith(n: FakeEl) { this.replaced = n; }
  closest() { return null; }
  replaced?: FakeEl;
}
class FakeDoc {
  createElement(t: string) { return new FakeEl(t, this); }
  createTextNode(t: string) { return { text: t }; }
}
const doc = new FakeDoc() as unknown as Document;

describe('title censor', () => {
  it('has the accessible name without the word', () => {
    expect(TITLE_ACCESSIBLE_NAME).toBe('The Probe Simulator');
  });
  it('builds an aria-hidden canvas block between the visible words, with no text', () => {
    const nodes = censoredTitleNodes(doc) as unknown[];
    expect(nodes).toHaveLength(3);
    const bar = nodes[1] as FakeEl;
    expect(bar.tag).toBe('canvas');
    expect(bar.attrs['aria-hidden']).toBe('true');
    expect(bar.textContent).toBe('');
    expect(bar.width).toBe(CENSOR_COLS); expect(bar.height).toBe(CENSOR_ROWS);
    expect((nodes[0] as { text: string }).text + (nodes[2] as { text: string }).text).toBe('The  Probe Simulator');
  });
  it('mosaic is deterministic, varied and carries no letter shapes (many distinct mid greys)', () => {
    const a = censorLevels(), b = censorLevels();
    expect(a).toEqual(b);
    expect(a).toHaveLength(CENSOR_COLS * CENSOR_ROWS);
    expect(new Set(a).size).toBeGreaterThan(3);
    expect(Math.min(...a)).toBeGreaterThanOrEqual(100); expect(Math.max(...a)).toBeLessThanOrEqual(210);
  });
  it('revealCensor (the future 18+ hook) swaps the block for the plain word', () => {
    const bar = censoredBlock(doc) as unknown as FakeEl;
    expect(revealCensor(bar as unknown as ParentNode)).toBe(true);
    expect(bar.replaced?.textContent).toBe('Anal');
  });
});
