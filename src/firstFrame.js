import * as THREE from 'three';
import { displayUniforms, passthroughUniforms } from './uniforms.js';
import { displayMaterial, passthroughMaterial } from './materials.js';
import { getRendererState, getSimDimensions } from './renderer.js';

/**
 * Seed the simulation with a small circle of chemical B.
 *
 * Key insight: too much initial B floods the domain and collapses
 * the system to a uniform steady state. We want just enough B to
 * trigger the Turing instability — a single circle covering ~2-5%
 * of the area, matching the original reaction-diffusion-playground.
 */
export function drawFirstFrame() {
  const { renderer, scene, camera, mesh, renderTargets } = getRendererState();
  const { width, height } = getSimDimensions();

  const bufferCanvas = document.querySelector('#buffer-canvas');
  bufferCanvas.width = width;
  bufferCanvas.height = height;
  const ctx = bufferCanvas.getContext('2d');

  // Fill with white (chemical A = 1.0, chemical B = 0.0)
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, width, height);

  // Draw a single centered circle — the classic seed
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.07; // ~7% of screen

  ctx.fillStyle = '#000';
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
  ctx.fill();

  // Add 2 small off-center circles for asymmetry
  ctx.beginPath();
  ctx.arc(centerX - width * 0.15, centerY + height * 0.1, radius * 0.4, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.arc(centerX + width * 0.2, centerY - height * 0.15, radius * 0.3, 0, Math.PI * 2);
  ctx.fill();

  // Convert canvas pixels to float texture data
  const pixels = ctx.getImageData(0, 0, width, height).data;
  const data = new Float32Array(pixels.length);

  for (let i = 0; i < data.length; i += 4) {
    data[i] = 1.0;                                     // A = 1.0 everywhere
    data[i + 1] = pixels[i + 1] === 0 ? 0.5 : 0.0;   // B = 0.5 where black
    data[i + 2] = 0.0;
    data[i + 3] = 0.0;
  }

  const texture = new THREE.DataTexture(data, width, height, THREE.RGBAFormat, THREE.FloatType);
  texture.flipY = true;
  texture.needsUpdate = true;

  passthroughUniforms.textureToDisplay.value = texture;
  mesh.material = passthroughMaterial;

  for (let i = 0; i < 2; i++) {
    renderer.setRenderTarget(renderTargets[i]);
    renderer.render(scene, camera);
  }

  displayUniforms.textureToDisplay.value = renderTargets[0].texture;
  displayUniforms.previousIterationTexture.value = renderTargets[0].texture;
  mesh.material = displayMaterial;

  renderer.setRenderTarget(null);
  renderer.render(scene, camera);
}
