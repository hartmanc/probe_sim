// The Start-menu title censor (owner, 27 Oct 2026): the team is "#619 The Anal Probe", the header reads "The ▒▒▒▒
// Probe Simulator". The censored word is drawn as a small pixel mosaic on a canvas (12 x 4 cells, scaled up with
// image-rendering: pixelated and a slight blur), so the word is not in the DOM as text, cannot be selected or
// copied, and screen readers skip it (aria-hidden; the heading carries aria-label "The Probe Simulator").
//
// The mosaic is seeded from the word but carries no letter shapes, so it is illegible at any zoom. The greys sit
// mid-range so the bar reads on the dark menu and would on a light one.
//
// Future release (owner): an "are you over 18?" easter egg reveals the word. The hook is revealCensor(): call it
// with the element censoredBlock() returned (or any ancestor of it). Unused for now.

/** The word behind the bar. Not shown anywhere as text until revealCensor() runs. */
const WORD = ['A', 'n', 'a', 'l'].join('');

export const CENSOR_COLS = 12;
export const CENSOR_ROWS = 4;
/** The heading's accessible name while the word is censored. */
export const TITLE_ACCESSIBLE_NAME = 'The Probe Simulator';

/** Grey levels (0-255) for each cell of the mosaic, row-major; deterministic per word. Pure, for tests. */
export function censorLevels(cols = CENSOR_COLS, rows = CENSOR_ROWS, seed = WORD): number[] {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  const out: number[] = [];
  for (let i = 0; i < cols * rows; i++) {
    h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909);
    h >>>= 0;
    out.push(100 + (h % 6) * 22); // 100..210, six steps
  }
  return out;
}

/** The censor bar: a canvas mosaic, aria-hidden, not selectable. Sized in em so it keeps the title's metrics. */
export function censoredBlock(doc: Document = document): HTMLElement {
  const c = doc.createElement('canvas');
  c.className = 'censor';
  c.width = CENSOR_COLS;
  c.height = CENSOR_ROWS;
  c.setAttribute('aria-hidden', 'true');
  c.setAttribute('role', 'presentation');
  c.dataset.censored = 'true';
  const g = c.getContext?.('2d') ?? null;
  if (g) {
    const lv = censorLevels();
    lv.forEach((v, i) => {
      g.fillStyle = `rgb(${v},${v},${v + 8})`;
      g.fillRect(i % CENSOR_COLS, Math.floor(i / CENSOR_COLS), 1, 1);
    });
  }
  return c;
}

/** The title's children: "The " + censor bar + " Probe Simulator". Give the heading aria-label TITLE_ACCESSIBLE_NAME. */
export function censoredTitleNodes(doc: Document = document): Node[] {
  return [doc.createTextNode('The '), censoredBlock(doc), doc.createTextNode(' Probe Simulator')];
}

/** HOOK for the future "are you over 18?" easter egg: swap the censor bar for the plain word. Unused for now. */
export function revealCensor(root: ParentNode): boolean {
  const bar = (root as Element).matches?.('[data-censored]') ? (root as Element) : root.querySelector('[data-censored]');
  if (!bar) return false;
  const doc = bar.ownerDocument;
  const span = doc.createElement('span');
  span.className = 'censor-revealed';
  span.textContent = WORD;
  bar.replaceWith(span);
  const h = span.closest('[aria-label]');
  if (h) h.removeAttribute('aria-label'); // the visible text now reads "The Anal Probe Simulator"
  return true;
}
