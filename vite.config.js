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
        penrose: resolve(__dirname, 'penrose.html'),
        penroseRandom: resolve(__dirname, 'penrose-random.html'),
        notPenrose: resolve(__dirname, 'not-penrose.html'),
        penroseDeflation: resolve(__dirname, 'penrose-deflation.html'),
        kiteDecomposition: resolve(__dirname, 'kite-decomposition.html'),
        randomSubstitution: resolve(__dirname, 'random-substitution.html'),
        randomSubstitutionScreensaver: resolve(__dirname, 'random-substitution-screensaver.html'),
        pentagrid: resolve(__dirname, 'pentagrid.html'),
      }
    }
  }
});
