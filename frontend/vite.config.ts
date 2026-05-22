import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

function normalizeWindowsDrive(path: string): string {
  return path.replace(/^([A-Z]):/, (_, drive: string) => `${drive.toLowerCase()}:`);
}

export default defineConfig({
  root: normalizeWindowsDrive(fileURLToPath(new URL('.', import.meta.url))),
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});

