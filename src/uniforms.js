import * as THREE from 'three';

const DEFAULTS = {
  f: 0.054,
  k: 0.062,
  dA: 0.2097,
  dB: 0.105,
  timestep: 1.0
};

const MAX_RIPPLES = 8;
const ripplePos = [];
const rippleClear = [];
const rippleWave = [];
for (let i = 0; i < MAX_RIPPLES; i++) {
  ripplePos.push(new THREE.Vector2(-1, -1));
  rippleClear.push(0);
  rippleWave.push(0);
}

export const simulationUniforms = {
  previousIterationTexture: { value: null },
  resolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
  ripplePos: { value: ripplePos },
  rippleClear: { value: rippleClear },
  rippleWave: { value: rippleWave },
  bias: { value: new THREE.Vector2(0.0, 0.0) },
  f: { value: DEFAULTS.f },
  k: { value: DEFAULTS.k },
  dA: { value: DEFAULTS.dA },
  dB: { value: DEFAULTS.dB },
  timestep: { value: DEFAULTS.timestep }
};

export const displayUniforms = {
  textureToDisplay: { value: null },
  previousIterationTexture: { value: null },
  time: { value: 0 },
  renderingStyle: { value: 0 },

  colorStop1: { value: new THREE.Vector4(0, 0, 0, 0) },
  colorStop2: { value: new THREE.Vector4(0, 1, 0, 0.2) },
  colorStop3: { value: new THREE.Vector4(1, 1, 0, 0.21) },
  colorStop4: { value: new THREE.Vector4(1, 0, 0, 0.4) },
  colorStop5: { value: new THREE.Vector4(0.39, 0, 0, 0.6) },

  hslFrom: { value: new THREE.Vector2(0.0, 1.0) },
  hslTo: { value: new THREE.Vector2(0.21, 0.85) },
  hslSaturation: { value: 0.7 },
  hslLuminosity: { value: 0.7 }
};

export const passthroughUniforms = {
  textureToDisplay: { value: null }
};

export { DEFAULTS, MAX_RIPPLES };
