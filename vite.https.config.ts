// `npm run dev:https`: the same dev server over HTTPS on port 5174 (self-signed certificate from
// @vitejs/plugin-basic-ssl), so iOS Safari treats the LAN origin as a secure context and allows tilt
// steering (DeviceOrientationEvent.requestPermission). Kept separate from vite.config.ts so the plain
// http server on 5173 is untouched. See src/app/NOTES-phone.md.
import { defineConfig, mergeConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import base from './vite.config';

export default mergeConfig(base, defineConfig({
  plugins: [basicSsl({ name: 'probe-sim-dev', domains: ['localhost', '192.168.1.125', '*.local'] })],
  server: { port: 5174, strictPort: true, host: true },
}));
