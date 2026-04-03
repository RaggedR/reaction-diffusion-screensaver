/**
 * Vorticity → colour via diverging colormap with hue rotation.
 */
precision highp float;
uniform sampler2D tOmega;
uniform float omegaMax;
uniform int colormap;
uniform float hueShift;
varying vec2 vUv;

// Cyan-Orange (dark background)
vec3 cyanOrange(float t) {
  vec3 neg = vec3(0.10, 0.55, 0.85);
  vec3 zero = vec3(0.03, 0.03, 0.08);
  vec3 pos = vec3(0.90, 0.40, 0.10);
  return t < 0.0 ? mix(zero, neg, sqrt(-t)) : mix(zero, pos, sqrt(t));
}

// Cool-Warm (Moreland diverging)
vec3 coolWarm(float t) {
  vec3 neg = vec3(0.23, 0.30, 0.75);
  vec3 zero = vec3(0.87, 0.87, 0.87);
  vec3 pos = vec3(0.71, 0.02, 0.15);
  float a = abs(t);
  return t < 0.0 ? mix(zero, neg, a) : mix(zero, pos, a);
}

// Inferno-style (sequential, absolute value)
vec3 inferno(float t) {
  float a = clamp(abs(t), 0.0, 1.0);
  vec3 c0 = vec3(0.001, 0.001, 0.014);
  vec3 c1 = vec3(0.107, 0.564, 3.933);
  vec3 c2 = vec3(11.602, -3.973, -15.942);
  vec3 c3 = vec3(-41.704, 17.436, 44.354);
  vec3 c4 = vec3(77.163, -33.402, -81.807);
  vec3 c5 = vec3(-73.683, 32.626, 73.210);
  vec3 c6 = vec3(27.163, -12.584, -23.070);
  return clamp(c0+a*(c1+a*(c2+a*(c3+a*(c4+a*(c5+a*c6))))), 0.0, 1.0);
}

// RGB ↔ HSV conversion for hue rotation
vec3 rgb2hsv(vec3 c) {
  vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
  vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
  vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
  float d = q.x - min(q.w, q.y);
  float e = 1.0e-10;
  return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
  float omega = texture2D(tOmega, vUv).r;
  float t = clamp(omega / omegaMax, -1.0, 1.0);

  vec3 color;
  if (colormap == 0) color = cyanOrange(t);
  else if (colormap == 1) color = coolWarm(t);
  else color = inferno(t);

  // Hue rotation for slow colour drift
  if (hueShift > 0.001) {
    vec3 hsv = rgb2hsv(color);
    hsv.x = fract(hsv.x + hueShift);
    color = hsv2rgb(hsv);
  }

  gl_FragColor = vec4(color, 1.0);
}
