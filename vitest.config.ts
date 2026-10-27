// The normal suite (`npm test`, `npx vitest run`) excludes the end-to-end test; `npm run test:e2e` sets E2E=1 to include
// it (it starts its own throwaway redis-server, docs/scoreboard.md "E2E"). Everything else comes from vite.config.ts.
import { configDefaults, defineConfig } from 'vitest/config';
import { mergeConfig } from 'vite';
import viteConfig from './vite.config.ts';

export default mergeConfig(viteConfig, defineConfig({
  test: { exclude: [...configDefaults.exclude, ...(process.env.E2E ? [] : ['**/e2e.*.test.ts'])] },
}));
