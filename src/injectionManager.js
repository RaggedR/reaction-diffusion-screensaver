/**
 * Injection Manager — "drop" chemical B into the petri dish on each beat.
 *
 * Uses a canvas texture that the simulation shader reads.
 * Drops are big, bright circles that fade over ~10 frames.
 */

import * as THREE from 'three';
import { simulationUniforms } from './uniforms.js';
import { getSimDimensions } from './renderer.js';

let canvas, ctx;
let texture;
let width, height;
let dropCount = 0;

export function setupInjection() {
  const dims = getSimDimensions();
  width = dims.width;
  height = dims.height;

  canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  ctx = canvas.getContext('2d', { willReadFrequently: false });

  ctx.clearRect(0, 0, width, height);

  texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.NearestFilter;
  texture.magFilter = THREE.NearestFilter;

  simulationUniforms.injectionTexture.value = texture;
  simulationUniforms.injectionAmount.value = 0.5; // Strong injection
}

/**
 * Call once per frame. Fades existing drops and adds new ones on beats.
 */
export function updateInjection(audioState) {
  if (!ctx) return;

  // Fade existing drops
  ctx.globalCompositeOperation = 'destination-out';
  ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
  ctx.fillRect(0, 0, width, height);
  ctx.globalCompositeOperation = 'source-over';

  // On beat: drop 1-2 big splashes
  if (audioState && audioState.isBeat) {
    dropCount++;
    console.log(`DROP #${dropCount} intensity:${audioState.beatIntensity.toFixed(2)}`);

    const numDrops = 1 + Math.floor(Math.random() * 2);
    const minDim = Math.min(width, height);

    for (let i = 0; i < numDrops; i++) {
      // Random position, biased toward center
      const x = width * (0.5 + (Math.random() - 0.5) * 0.7);
      const y = height * (0.5 + (Math.random() - 0.5) * 0.7);

      // BIG radius — 5-15% of screen
      const radius = minDim * (0.05 + audioState.beatIntensity * 0.1);

      // Full brightness — no subtlety
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 1.0)';
      ctx.fill();
    }
  }

  texture.needsUpdate = true;
}

export function getDropCount() {
  return dropCount;
}
