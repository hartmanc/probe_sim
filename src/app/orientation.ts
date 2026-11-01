// Portrait or landscape, for the rotate overlay and the pause-on-portrait. The CSS media query alone is not trusted: Chrome
// on iOS reads (orientation: portrait) during the first load of a page held in landscape, which put the "Rotate your
// phone" overlay over the load box (owner, 1 Nov 2026). The decision is a class on <html> set from JS, only after a
// reading has held for HOLD_MS, so a transient wrong reading never shows the overlay.

export interface OrientationReading {
  /** screen.orientation.type, when the browser has it */
  orientationType?: string | null;
  /** window.orientation (deprecated, still the one old iOS gives): 0 or 180 portrait, 90 or -90 landscape */
  windowOrientation?: number | null;
  /** matchMedia('(orientation: portrait)').matches, when matchMedia exists */
  mqPortrait?: boolean | null;
  innerWidth: number;
  innerHeight: number;
}

/**
 * Portrait? Precedence: screen.orientation.type (portrait-primary / -secondary vs landscape-*), else window.orientation
 * (0 or 180 is portrait), else the media query, else the window's shape (taller than wide).
 */
export function portraitFrom(r: OrientationReading): boolean {
  const t = r.orientationType;
  if (typeof t === 'string' && /^(portrait|landscape)/.test(t)) return t.startsWith('portrait');
  const o = r.windowOrientation;
  if (typeof o === 'number' && Number.isFinite(o)) return Math.abs(o) % 180 === 0;
  if (typeof r.mqPortrait === 'boolean') return r.mqPortrait;
  return r.innerHeight > r.innerWidth;
}

export const HOLD_MS = 300;

const read = (): OrientationReading => ({
  orientationType: typeof screen !== 'undefined' ? screen.orientation?.type ?? null : null,
  windowOrientation: typeof (window as unknown as { orientation?: unknown }).orientation === 'number' ? (window as unknown as { orientation: number }).orientation : null,
  mqPortrait: window.matchMedia ? window.matchMedia('(orientation: portrait)').matches : null,
  innerWidth: window.innerWidth, innerHeight: window.innerHeight,
});

/** Keep html.portrait in step with the device, updated on orientationchange, resize and the media query; each change must hold HOLD_MS. */
export function installPortraitWatcher(): void {
  const html = document.documentElement;
  let timer: number | undefined;
  const check = () => {
    const now = portraitFrom(read());
    if (now === html.classList.contains('portrait')) { if (timer !== undefined) { clearTimeout(timer); timer = undefined; } return; }
    if (timer !== undefined) return;   // already waiting on this change
    timer = window.setTimeout(() => {
      timer = undefined;
      html.classList.toggle('portrait', portraitFrom(read()));   // the state after it held: re-read, never the stale one
    }, HOLD_MS);
  };
  window.addEventListener('orientationchange', check);
  window.addEventListener('resize', check);
  window.matchMedia?.('(orientation: portrait)').addEventListener?.('change', check);
  screen.orientation?.addEventListener?.('change', check);
  check();
}

/** The committed state (html.portrait). */
export const isPortrait = (): boolean => document.documentElement.classList.contains('portrait');
