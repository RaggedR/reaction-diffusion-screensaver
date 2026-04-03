/**
 * Semi-Lagrangian advection + explicit viscous diffusion.
 * 1. Compute velocity from streamfunction: u = dpsi/dy, v = -dpsi/dx
 * 2. Trace particle backward: pos_back = pos - dt * velocity
 * 3. Sample vorticity at back-traced position (bilinear via LinearFilter)
 * 4. Add viscous diffusion: nu * nabla^2 omega
 */
precision highp float;
uniform sampler2D tOmega;
uniform sampler2D tPsi;
uniform vec2 resolution;
uniform float nu, dt;
varying vec2 vUv;

void main() {
  vec2 tx = 1.0 / resolution;
  float dx = tx.x;

  // Velocity from streamfunction via central differences
  float pE = texture2D(tPsi, vUv + vec2( tx.x, 0.0)).r;
  float pW = texture2D(tPsi, vUv + vec2(-tx.x, 0.0)).r;
  float pN = texture2D(tPsi, vUv + vec2(0.0,  tx.y)).r;
  float pS = texture2D(tPsi, vUv + vec2(0.0, -tx.y)).r;

  float u = (pN - pS) / (2.0 * dx);
  float v = -(pE - pW) / (2.0 * dx);

  // Semi-Lagrangian backtrace (periodic via RepeatWrapping)
  vec2 backPos = vUv - dt * vec2(u, v);
  float omegaAdv = texture2D(tOmega, backPos).r;

  // Explicit viscous diffusion
  float oC = texture2D(tOmega, vUv).r;
  float oE = texture2D(tOmega, vUv + vec2( tx.x, 0.0)).r;
  float oW = texture2D(tOmega, vUv + vec2(-tx.x, 0.0)).r;
  float oN = texture2D(tOmega, vUv + vec2(0.0,  tx.y)).r;
  float oS = texture2D(tOmega, vUv + vec2(0.0, -tx.y)).r;
  float laplacian = (oE + oW + oN + oS - 4.0 * oC) / (dx * dx);

  float omegaNew = omegaAdv + dt * nu * laplacian;
  omegaNew = clamp(omegaNew, -200.0, 200.0);

  gl_FragColor = vec4(omegaNew, 0.0, 0.0, 1.0);
}
