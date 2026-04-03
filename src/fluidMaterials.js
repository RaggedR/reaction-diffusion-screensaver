import * as THREE from 'three';

import vertShader from './shaders/fluid/passthrough.vert.glsl';
import initFragShader from './shaders/fluid/init.frag.glsl';
import jacobiFragShader from './shaders/fluid/jacobi.frag.glsl';
import advectFragShader from './shaders/fluid/advect.frag.glsl';
import injectFragShader from './shaders/fluid/inject.frag.glsl';
import displayFragShader from './shaders/fluid/display.frag.glsl';

import { initUniforms, jacobiUniforms, advectUniforms, injectUniforms, displayUniforms } from './fluidUniforms.js';

function makeMat(uniforms, fragmentShader) {
  const mat = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: vertShader,
    fragmentShader
  });
  mat.blending = THREE.NoBlending;
  return mat;
}

export const initMaterial = makeMat(initUniforms, initFragShader);
export const jacobiMaterial = makeMat(jacobiUniforms, jacobiFragShader);
export const advectMaterial = makeMat(advectUniforms, advectFragShader);
export const injectMaterial = makeMat(injectUniforms, injectFragShader);
export const fluidDisplayMaterial = makeMat(displayUniforms, displayFragShader);
