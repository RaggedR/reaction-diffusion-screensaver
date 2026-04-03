import * as THREE from 'three';

import simulationFragShader from './shaders/simulationFrag.glsl';
import simulationVertShader from './shaders/simulationVert.glsl';
import displayFragShader from './shaders/displayFrag.glsl';
import displayVertShader from './shaders/displayVert.glsl';
import passthroughVertShader from './shaders/passthroughVert.glsl';
import passthroughFragShader from './shaders/passthroughFrag.glsl';

import { simulationUniforms, displayUniforms, passthroughUniforms } from './uniforms.js';

export const simulationMaterial = new THREE.ShaderMaterial({
  uniforms: simulationUniforms,
  vertexShader: simulationVertShader,
  fragmentShader: simulationFragShader,
});
simulationMaterial.blending = THREE.NoBlending;

export const displayMaterial = new THREE.ShaderMaterial({
  uniforms: displayUniforms,
  vertexShader: displayVertShader,
  fragmentShader: displayFragShader,
});
displayMaterial.blending = THREE.NoBlending;

export const passthroughMaterial = new THREE.ShaderMaterial({
  uniforms: passthroughUniforms,
  vertexShader: passthroughVertShader,
  fragmentShader: passthroughFragShader,
});
passthroughMaterial.blending = THREE.NoBlending;
