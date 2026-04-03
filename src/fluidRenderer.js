import * as THREE from 'three';
import { SIM_SIZE, JACOBI_ITERS, STEPS_PER_FRAME, WARMUP_ITERS,
         initUniforms, jacobiUniforms, advectUniforms, injectUniforms, displayUniforms } from './fluidUniforms.js';
import { initMaterial, jacobiMaterial, advectMaterial, injectMaterial, fluidDisplayMaterial } from './fluidMaterials.js';

let camera, scene, mesh, renderer;

// 4 render targets: omega[2] for vorticity, psi[2] for streamfunction
let omega = [];
let psi = [];
let curOmega = 0;
let curPsi = 0;

let stepsPerFrame = STEPS_PER_FRAME;

function makeRT(filter) {
  return new THREE.WebGLRenderTarget(SIM_SIZE, SIM_SIZE, {
    wrapS: THREE.RepeatWrapping,
    wrapT: THREE.RepeatWrapping,
    minFilter: filter,
    magFilter: filter,
    type: THREE.FloatType,
    format: THREE.RGBAFormat,
    depthBuffer: false,
    stencilBuffer: false
  });
}

export function setupFluidRenderer() {
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  scene = new THREE.Scene();
  mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
  scene.add(mesh);

  renderer = new THREE.WebGLRenderer({ preserveDrawingBuffer: false });
  renderer.setPixelRatio(1);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x000000, 1);
  document.body.appendChild(renderer.domElement);

  renderer.domElement.style.position = 'fixed';
  renderer.domElement.style.top = '0';
  renderer.domElement.style.left = '0';
  renderer.domElement.style.width = '100vw';
  renderer.domElement.style.height = '100vh';

  // omega: LinearFilter for bilinear interpolation in Semi-Lagrangian backtrace
  omega = [makeRT(THREE.LinearFilter), makeRT(THREE.LinearFilter)];
  // psi: NearestFilter (sampled at exact grid points)
  psi = [makeRT(THREE.NearestFilter), makeRT(THREE.NearestFilter)];
}

export function initSimulation() {
  // Render KH initial condition to omega[0]
  mesh.material = initMaterial;
  renderer.setRenderTarget(omega[0]);
  renderer.render(scene, camera);

  // Clear the rest
  renderer.setRenderTarget(omega[1]);
  renderer.clear();
  renderer.setRenderTarget(psi[0]);
  renderer.clear();
  renderer.setRenderTarget(psi[1]);
  renderer.clear();

  curOmega = 0;
  curPsi = 0;

  // Warm-up: 500 Jacobi iterations to build the background streamfunction
  mesh.material = jacobiMaterial;
  jacobiUniforms.tOmega.value = omega[0].texture;
  for (let j = 0; j < WARMUP_ITERS; j++) {
    jacobiUniforms.tPsi.value = psi[curPsi].texture;
    const nextPsi = 1 - curPsi;
    renderer.setRenderTarget(psi[nextPsi]);
    renderer.render(scene, camera);
    curPsi = nextPsi;
  }
}

function step() {
  // Phase 1: Poisson solve (Jacobi iterations)
  mesh.material = jacobiMaterial;
  jacobiUniforms.tOmega.value = omega[curOmega].texture;
  for (let j = 0; j < JACOBI_ITERS; j++) {
    jacobiUniforms.tPsi.value = psi[curPsi].texture;
    const nextPsi = 1 - curPsi;
    renderer.setRenderTarget(psi[nextPsi]);
    renderer.render(scene, camera);
    curPsi = nextPsi;
  }

  // Phase 2: Semi-Lagrangian advection + diffusion
  mesh.material = advectMaterial;
  advectUniforms.tOmega.value = omega[curOmega].texture;
  advectUniforms.tPsi.value = psi[curPsi].texture;
  const nextOmega = 1 - curOmega;
  renderer.setRenderTarget(omega[nextOmega]);
  renderer.render(scene, camera);
  curOmega = nextOmega;
}

export function runFluidStep() {
  for (let i = 0; i < stepsPerFrame; i++) {
    step();
  }
}

/**
 * Inject a vortex dipole into the vorticity field.
 * Runs once per beat as a separate shader pass.
 */
export function injectVortex(angle, strength, radius, x = 0.5, y = 0.5) {
  injectUniforms.tOmega.value = omega[curOmega].texture;
  injectUniforms.injectCenter.value.set(x, y);
  injectUniforms.injectAngle.value = angle;
  injectUniforms.injectStrength.value = strength;
  injectUniforms.injectRadius.value = radius;
  injectUniforms.injectActive.value = 1.0;

  mesh.material = injectMaterial;
  const nextOmega = 1 - curOmega;
  renderer.setRenderTarget(omega[nextOmega]);
  renderer.render(scene, camera);
  curOmega = nextOmega;

  // Deactivate injection
  injectUniforms.injectActive.value = 0.0;
}

export function renderFluidToScreen() {
  displayUniforms.tOmega.value = omega[curOmega].texture;
  mesh.material = fluidDisplayMaterial;
  renderer.setRenderTarget(null);
  renderer.render(scene, camera);
}

export function setStepsPerFrame(n) {
  stepsPerFrame = Math.max(1, Math.min(30, Math.round(n)));
}
