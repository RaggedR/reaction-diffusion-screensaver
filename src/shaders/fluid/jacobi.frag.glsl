/**
 * Jacobi iteration for Poisson equation: nabla^2 psi = -omega
 * psi_new = (psi_E + psi_W + psi_N + psi_S + dx^2 * omega) / 4
 */
precision highp float;
uniform sampler2D tOmega;
uniform sampler2D tPsi;
uniform vec2 resolution;
varying vec2 vUv;

void main() {
  vec2 tx = 1.0 / resolution;
  float dx = tx.x;

  float omega = texture2D(tOmega, vUv).r;

  float pE = texture2D(tPsi, vUv + vec2( tx.x, 0.0)).r;
  float pW = texture2D(tPsi, vUv + vec2(-tx.x, 0.0)).r;
  float pN = texture2D(tPsi, vUv + vec2(0.0,  tx.y)).r;
  float pS = texture2D(tPsi, vUv + vec2(0.0, -tx.y)).r;

  float psi = (pE + pW + pN + pS + dx * dx * omega) / 4.0;

  gl_FragColor = vec4(psi, 0.0, 0.0, 1.0);
}
