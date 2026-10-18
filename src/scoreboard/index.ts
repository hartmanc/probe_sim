// Scoreboard public API (docs/scoreboard.md). Pure TS, safe to import from the browser.
export * from './config';
export * from './types';
export { physicsVersion, cyrb53, canonicalJson } from './hash';
export { HotlapSim, canonicalReset, defaultRefGhost, type SimAssets, type RawInput, type HotlapSimOptions, type SceneryLike, type GhostsLike } from './sim';
export { checkTrace, replayTrace, verifyHotlap, type ReplayResult, type HotlapVerdict } from './replay';
export { normalizeName, nameKey, boardKey, parseBoardKey, lowerIsBetter, validateSubmission } from './validate';
