import * as THREE from 'three';

export const SIM_SIZE = 128;
export const JACOBI_ITERS = 40;
export const STEPS_PER_FRAME = 16;
export const WARMUP_ITERS = 500;

export const DEFAULTS = {
  nu: 0.001,
  dt: 0.005,
  vShear: 2.0,
  delta: 0.05,
  aPert: 0.1,
  kPert: 4.0
};

export const initUniforms = {
  resolution: { value: new THREE.Vector2(SIM_SIZE, SIM_SIZE) },
  vShear: { value: DEFAULTS.vShear },
  delta: { value: DEFAULTS.delta },
  aPert: { value: DEFAULTS.aPert },
  kPert: { value: DEFAULTS.kPert }
};

export const jacobiUniforms = {
  tOmega: { value: null },
  tPsi: { value: null },
  resolution: { value: new THREE.Vector2(SIM_SIZE, SIM_SIZE) }
};

export const advectUniforms = {
  tOmega: { value: null },
  tPsi: { value: null },
  resolution: { value: new THREE.Vector2(SIM_SIZE, SIM_SIZE) },
  nu: { value: DEFAULTS.nu },
  dt: { value: DEFAULTS.dt }
};

export const injectUniforms = {
  tOmega: { value: null },
  resolution: { value: new THREE.Vector2(SIM_SIZE, SIM_SIZE) },
  injectCenter: { value: new THREE.Vector2(0.5, 0.5) },
  injectAngle: { value: 0.0 },
  injectStrength: { value: 0.0 },
  injectRadius: { value: 0.03 },
  injectActive: { value: 0.0 }
};

export const displayUniforms = {
  tOmega: { value: null },
  omegaMax: { value: 0.5 * DEFAULTS.vShear / DEFAULTS.delta },
  colormap: { value: 0 },
  hueShift: { value: 0.0 }
};
