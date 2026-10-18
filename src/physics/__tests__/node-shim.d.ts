// Minimal types for the two Node built-ins edge.test.ts uses (the project has no @types/node).
declare module 'node:fs' {
  export function readFileSync(path: string): Uint8Array;
  export function readFileSync(path: string, encoding: 'utf8'): string;
}
declare module 'node:url' {
  export function fileURLToPath(url: URL | string): string;
}
