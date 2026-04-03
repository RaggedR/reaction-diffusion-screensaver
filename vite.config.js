import { resolve } from 'path';
import { defineConfig } from 'vite';
import glsl from 'vite-plugin-glsl';

export default defineConfig({
  base: '/reaction-diffusion-screensaver/',
  plugins: [glsl()],
  server: {
    port: 5173,
    open: true
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        fluid: resolve(__dirname, 'fluid.html'),
      }
    }
  }
});
