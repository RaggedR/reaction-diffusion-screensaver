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
        mazeInteractive: resolve(__dirname, 'mazes/interactive.html'),
        mazeKnotted: resolve(__dirname, 'mazes/knotted.html'),
        mazeCeltic: resolve(__dirname, 'mazes/celtic.html'),
      }
    }
  }
});
