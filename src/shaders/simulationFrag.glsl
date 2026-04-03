/**
 * Gray-Scott reaction-diffusion simulation
 * - Red channel = concentration of chemical A (0.0 - 1.0)
 * - Green channel = concentration of chemical B (0.0 - 1.0)
 */

uniform sampler2D previousIterationTexture;

uniform float f;
uniform float k;
uniform float dA;
uniform float dB;
uniform float timestep;

// Concurrent ripples
const int MAX_RIPPLES = 8;
uniform vec2 ripplePos[8];
uniform float rippleClear[8];
uniform float rippleWave[8];

uniform vec2 bias;
uniform vec2 resolution;

varying vec2 v_uvs[9];

vec3 weights[3];

void setWeights(int type) {
  if(type == 0) {
    weights[0] = vec3(0.05,  0.2,  0.05);
    weights[1] = vec3(0.2,  -1.0,  0.2);
    weights[2] = vec3(0.05,  0.2,  0.05);
  } else if(type == 1) {
    weights[0] = vec3(0.25,  0.5,  0.25);
    weights[1] = vec3(0.5,  -3.0,  0.5);
    weights[2] = vec3(0.25,  0.5,  0.25);
  } else if(type == 2) {
    weights[0] = vec3(0.0,  1.0,  0.0);
    weights[1] = vec3(1.0, -4.0,  1.0);
    weights[2] = vec3(0.0,  1.0,  0.0);
  }
}

vec2 getLaplacian(vec4 centerTexel) {
  setWeights(2);
  vec2 laplacian = centerTexel.xy * weights[1][1];

  laplacian += texture2D(previousIterationTexture, fract(v_uvs[1])).xy * (weights[0][1] + bias.y);
  laplacian += texture2D(previousIterationTexture, fract(v_uvs[2])).xy * (weights[1][2] + bias.x);
  laplacian += texture2D(previousIterationTexture, fract(v_uvs[3])).xy * (weights[2][1] - bias.y);
  laplacian += texture2D(previousIterationTexture, fract(v_uvs[4])).xy * (weights[1][0] - bias.x);

  laplacian += texture2D(previousIterationTexture, fract(v_uvs[5])).xy * weights[0][2];
  laplacian += texture2D(previousIterationTexture, fract(v_uvs[6])).xy * weights[2][2];
  laplacian += texture2D(previousIterationTexture, fract(v_uvs[7])).xy * weights[2][0];
  laplacian += texture2D(previousIterationTexture, fract(v_uvs[8])).xy * weights[0][0];

  return laplacian;
}

void main() {
  vec4 centerTexel = texture2D(previousIterationTexture, v_uvs[0]);
  float A = centerTexel[0];
  float B = centerTexel[1];

  // Gray-Scott equations
  vec2 laplacian = getLaplacian(centerTexel);
  float reactionTerm = A * B * B;

  float newA = A + ((dA * laplacian[0] - reactionTerm + f * (1.0 - A)) * timestep);
  float newB = B + ((dB * laplacian[1] + reactionTerm - (k + f) * B) * timestep);

  // Process all active ripples
  for (int i = 0; i < MAX_RIPPLES; i++) {
    if (ripplePos[i].x < 0.0) continue;

    vec2 pixelPos = ripplePos[i] * resolution;
    float dist = length(gl_FragCoord.xy - pixelPos);
    float cr = rippleClear[i];
    float wr = rippleWave[i];

    // === Inner: clear ring ===
    float ringWidth = max(cr * 0.15, 3.0);
    float innerEdge = cr - ringWidth;

    if (dist > innerEdge && dist < cr) {
      newA = 1.0;
      newB = 0.0;
    }

    // Seed at center (early frames only)
    float seedR = ringWidth * 0.6;
    if (dist < seedR && cr < ringWidth * 5.0) {
      float t = dist / seedR;
      newB = 0.5 * (1.0 - t * t);
    }

    // === Outer: perturbation wave ===
    if (wr > cr && dist > cr && dist < wr) {
      float waveWidth = max((wr - cr) * 0.15, 4.0);
      float waveFront = wr - waveWidth;

      if (dist > waveFront && dist < wr) {
        float t = (dist - waveFront) / waveWidth;
        float nudge = 0.12 * (1.0 - t);
        newB = min(newB + nudge, 0.9);
      }
    }
  }

  gl_FragColor = vec4(newA, newB, centerTexel.b, 1.0);
}
