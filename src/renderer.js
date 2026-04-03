import * as THREE from 'three';
import { simulationUniforms, displayUniforms } from './uniforms.js';
import { simulationMaterial, displayMaterial } from './materials.js';

let camera, scene, mesh, renderer;
let renderTargets = [];
let pingPongSteps = 60; // Variable — audio controls this

// Track simulation dimensions (logical, not physical)
let simWidth, simHeight;

export function setupRenderer() {
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  scene = new THREE.Scene();

  mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(2, 2),
    displayMaterial
  );
  scene.add(mesh);

  renderer = new THREE.WebGLRenderer({ preserveDrawingBuffer: false });
  // Use pixel ratio 1 for simulation — the CSS scales to fill screen.
  // This avoids Retina doubling the simulation grid (which halves visual pattern size
  // and wastes GPU on 4× the pixels).
  renderer.setPixelRatio(1);
  renderer.setSize(window.innerWidth, window.innerHeight);

  document.body.appendChild(renderer.domElement);

  renderer.domElement.style.position = 'fixed';
  renderer.domElement.style.top = '0';
  renderer.domElement.style.left = '0';
  renderer.domElement.style.width = '100vw';
  renderer.domElement.style.height = '100vh';

  simWidth = window.innerWidth;
  simHeight = window.innerHeight;

  setupRenderTargets();

  // DON'T re-create render targets on resize — it wipes the simulation state.
  // The CSS scaling handles visual resizing; the simulation grid stays fixed.

  return { camera, scene, mesh, renderer, renderTargets };
}

function setupRenderTargets() {
  renderTargets.length = 0;

  for (let i = 0; i < 2; i++) {
    renderTargets.push(new THREE.WebGLRenderTarget(simWidth, simHeight, {
      minFilter: THREE.NearestFilter,
      magFilter: THREE.NearestFilter,
      format: THREE.RGBAFormat,
      type: THREE.FloatType
    }));
  }

  simulationUniforms.resolution.value.set(simWidth, simHeight);
}

let currentRenderTargetIndex = 0;

export function runSimulationStep() {
  mesh.material = simulationMaterial;

  for (let i = 0; i < pingPongSteps; i++) {
    const nextIndex = currentRenderTargetIndex === 0 ? 1 : 0;

    simulationUniforms.previousIterationTexture.value = renderTargets[currentRenderTargetIndex].texture;
    renderer.setRenderTarget(renderTargets[nextIndex]);
    renderer.render(scene, camera);

    // Clear all ripples after first iteration — perturbation applies ONCE, not 60×
    if (i === 0) {
      const pos = simulationUniforms.ripplePos.value;
      const cl = simulationUniforms.rippleClear.value;
      const wv = simulationUniforms.rippleWave.value;
      for (let j = 0; j < pos.length; j++) {
        pos[j].set(-1, -1);
        cl[j] = 0;
        wv[j] = 0;
      }
    }

    simulationUniforms.previousIterationTexture.value = renderTargets[nextIndex].texture;
    displayUniforms.textureToDisplay.value = renderTargets[nextIndex].texture;
    displayUniforms.previousIterationTexture.value = renderTargets[currentRenderTargetIndex].texture;

    currentRenderTargetIndex = nextIndex;
  }
}

export function renderToScreen(clock) {
  displayUniforms.time.value = clock.getElapsedTime();
  mesh.material = displayMaterial;
  renderer.setRenderTarget(null);
  renderer.render(scene, camera);
}

export function getSimDimensions() {
  return { width: simWidth, height: simHeight };
}

export function setPingPongSteps(n) {
  pingPongSteps = Math.max(10, Math.min(120, Math.round(n)));
}

export function getRendererState() {
  return { camera, scene, mesh, renderer, renderTargets };
}

/**
 * Read the B chemical value at a pixel position.
 * Used to measure maze front propagation speed.
 */
export function readPixelB(x, y) {
  const buffer = new Float32Array(4);
  const px = Math.round(Math.max(0, Math.min(x, simWidth - 1)));
  const py = Math.round(Math.max(0, Math.min(y, simHeight - 1)));
  renderer.readRenderTargetPixels(renderTargets[currentRenderTargetIndex], px, py, 1, 1, buffer);
  return buffer[1];  // Green channel = chemical B
}
