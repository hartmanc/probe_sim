import { defineConfig } from 'vite';

// base './' so the built site works from any path (GitHub Pages project site).
export default defineConfig({
  base: './',
  server: { port: 5173, host: true },
  build: { target: 'es2022', sourcemap: true, chunkSizeWarningLimit: 2000 },
});
