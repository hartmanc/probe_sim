// The last uncaught error of the page (window `error` / `unhandledrejection`), kept for the report button
// (feedback.ts), so a player's bug report carries what actually broke. Installed first thing in index.ts.

let last: string | null = null;

/** Message + the top of the stack, at most 1500 characters. */
export function describeError(e: unknown): string {
  const err = e as { name?: unknown; message?: unknown; stack?: unknown } | null;
  let s: string;
  if (err && typeof err === 'object' && typeof err.stack === 'string') s = err.stack.includes(String(err.message ?? '')) ? err.stack : `${err.name}: ${err.message}\n${err.stack}`;
  else if (err && typeof err === 'object' && 'message' in err) s = `${String(err.name ?? 'Error')}: ${String(err.message)}`;
  else s = String(e);
  return s.split('\n').slice(0, 8).join('\n').slice(0, 1500);
}

export function recordError(e: unknown, where?: string): void {
  last = `${where ? `${where}: ` : ''}${describeError(e)} (at ${new Date().toISOString()})`;
}

export const lastError = (): string | null => last;

let installed = false;
export function installErrorCapture(target: Pick<Window, 'addEventListener'> = window): void {
  if (installed) return;
  installed = true;
  target.addEventListener('error', (ev: Event) => {
    const e = ev as ErrorEvent;
    recordError(e.error ?? `${e.message} (${e.filename}:${e.lineno}:${e.colno})`, 'error');
  });
  target.addEventListener('unhandledrejection', (ev: Event) => recordError((ev as PromiseRejectionEvent).reason, 'unhandled rejection'));
}
