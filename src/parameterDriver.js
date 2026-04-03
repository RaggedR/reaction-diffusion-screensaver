import { simulationUniforms, displayUniforms, MAX_RIPPLES } from './uniforms.js';
import { setPingPongSteps, getSimDimensions } from './renderer.js';

// Fixed maze parameters
const MAZE_F = 0.029;
const MAZE_K = 0.057;

// Speed envelope
let speedEnvelope = 0;

// Concurrent ripples — each expands independently
let ripples = [];

// Slow colour drift
let hueCenter = 0.45;

let frameCount = 0;

export function tick(audioState) {
  const { width, height } = getSimDimensions();
  const minDim = Math.min(width, height);
  const diagonal = Math.sqrt(width * width + height * height);

  if (audioState && audioState.isBeat) {
    speedEnvelope = 1.0;

    // Wave reaches edge in ~3 seconds
    const waveSpeed = diagonal / 180;

    if (ripples.length >= MAX_RIPPLES) ripples.shift();

    ripples.push({
      clearRadius: 3,
      waveRadius: 3,
      maxClear: minDim * 0.12,
      maxWave: diagonal,
      clearSpeed: 1.5,
      waveSpeed: waveSpeed
    });

    hueCenter += 0.008;
  }

  // === Expand all ripples and upload to uniforms ===
  const pos = simulationUniforms.ripplePos.value;
  const cl = simulationUniforms.rippleClear.value;
  const wv = simulationUniforms.rippleWave.value;

  for (let i = 0; i < MAX_RIPPLES; i++) {
    if (i < ripples.length) {
      const r = ripples[i];
      r.clearRadius = Math.min(r.clearRadius + r.clearSpeed, r.maxClear);
      r.waveRadius = Math.min(r.waveRadius + r.waveSpeed, r.maxWave);

      pos[i].set(0.5, 0.5);
      cl[i] = r.clearRadius;
      wv[i] = r.waveRadius;
    } else {
      pos[i].set(-1, -1);
      cl[i] = 0;
      wv[i] = 0;
    }
  }

  // Remove finished ripples
  ripples = ripples.filter(r => r.waveRadius < r.maxWave * 0.99);

  // === Simulation ===
  speedEnvelope *= 0.95;
  const steps = Math.round(30 + speedEnvelope * 70);
  simulationUniforms.f.value = MAZE_F;
  simulationUniforms.k.value = MAZE_K;
  simulationUniforms.dA.value = 0.2097;
  simulationUniforms.dB.value = 0.105;
  simulationUniforms.timestep.value = 1.0;
  simulationUniforms.bias.value.set(0, 0);
  setPingPongSteps(steps);

  // === Colour ===
  hueCenter += 0.00008;
  if (hueCenter > 1) hueCenter -= 1;
  displayUniforms.hslTo.value.set(hueCenter - 0.12, hueCenter + 0.12);
  displayUniforms.hslSaturation.value = 0.45;
  displayUniforms.hslLuminosity.value = 0.50;

  frameCount++;
}

export function getPathT() {
  return 0.33;
}
