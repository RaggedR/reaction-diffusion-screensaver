/**
 * Vortex dipole injection — adds two opposite-sign Gaussian vortices
 * at a random angle from center. Preserves zero net circulation.
 * Runs once per beat as a separate pass.
 */
precision highp float;
uniform sampler2D tOmega;
uniform vec2 resolution;
uniform vec2 injectCenter;
uniform float injectAngle;
uniform float injectStrength;
uniform float injectRadius;
uniform float injectActive;
varying vec2 vUv;

void main() {
  float omega = texture2D(tOmega, vUv).r;

  if (injectActive > 0.5) {
    vec2 dir = vec2(cos(injectAngle), sin(injectAngle));
    vec2 offset = dir * injectRadius * 1.5;

    vec2 p1 = injectCenter + offset;
    vec2 p2 = injectCenter - offset;

    float d1 = length(vUv - p1) / injectRadius;
    float d2 = length(vUv - p2) / injectRadius;

    float v1 =  injectStrength * exp(-d1 * d1);
    float v2 = -injectStrength * exp(-d2 * d2);

    omega += v1 + v2;
    omega = clamp(omega, -200.0, 200.0);
  }

  gl_FragColor = vec4(omega, 0.0, 0.0, 1.0);
}
