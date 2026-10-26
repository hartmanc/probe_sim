// WebGL 2 checks (three.js r186 needs it): the start-up test and the messages for a browser without it or a lost context.

export const NO_WEBGL2_MESSAGE = 'This game needs WebGL 2, which this browser does not offer or has turned off. It runs in a current Chrome, Edge, Firefox or Safari (15 or newer) on a computer, Safari on an iPhone or iPad (iOS 15 or newer) and Chrome on Android. If your browser is current, check that hardware acceleration (graphics acceleration) is switched on in its settings.';

export const CONTEXT_LOST_MESSAGE = 'The graphics stopped: the browser took the GPU back (a driver reset, or a phone running short of memory). Reload to continue.';

/** True when a canvas can make a WebGL 2 context (the probe context is released at once). */
export function webgl2Available(doc: Pick<Document, 'createElement'> = document): boolean {
  try {
    const c = doc.createElement('canvas') as HTMLCanvasElement;
    const gl = c.getContext('webgl2');
    if (!gl) return false;
    gl.getExtension('WEBGL_lose_context')?.loseContext();
    return true;
  } catch { return false; }
}
