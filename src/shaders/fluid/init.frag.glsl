/**
 * Kelvin-Helmholtz initial condition.
 * Double shear layer at y=0.25 and y=0.75 with sinusoidal perturbation.
 * Two counter-signed layers ensure zero net circulation (required for periodic Poisson).
 */
precision highp float;
uniform vec2 resolution;
uniform float vShear, delta, aPert, kPert;
varying vec2 vUv;

float sech2(float x) {
  float ex = exp(clamp(x, -20.0, 20.0));
  float ch = (ex + 1.0 / ex) * 0.5;
  return 1.0 / (ch * ch);
}

void main() {
  float x = vUv.x;
  float y = vUv.y;

  float layer1 = sech2((y - 0.25) / delta);
  float layer2 = sech2((y - 0.75) / delta);

  float pert = 1.0 + aPert * sin(6.283185307 * kPert * x);

  float omega = -(vShear / delta) * (layer1 - layer2) * pert;

  gl_FragColor = vec4(omega, 0.0, 0.0, 1.0);
}
