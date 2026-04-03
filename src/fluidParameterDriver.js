import { displayUniforms, STEPS_PER_FRAME } from './fluidUniforms.js';
import { injectVortex, setStepsPerFrame } from './fluidRenderer.js';

// Speed envelope
let speedEnvelope = 0;

// Slow colour drift
let hueShift = 0;

let frameCount = 0;

export function fluidTick(audioState) {
  if (audioState && audioState.isBeat) {
    speedEnvelope = 1.0;

    // Inject at a shear boundary, perpendicular to it so each half
    // of the dipole lands in the opposite-coloured region
    const intensity = audioState.beatIntensity || 0.5;
    const strength = 15 + intensity * 25;
    const radius = 0.04;
    const boundaryY = Math.random() < 0.5 ? 0.25 : 0.75;
    const randomX = Math.random();
    // Perpendicular to the horizontal boundary = vertical (π/2), with slight randomness
    const angle = Math.PI / 2 + (Math.random() - 0.5) * 0.4;

    injectVortex(angle, strength, radius, randomX, boundaryY);

    hueShift += 0.008;
  }

  // Speed envelope: fast on beat, decay back
  speedEnvelope *= 0.95;
  setStepsPerFrame(Math.round(STEPS_PER_FRAME + speedEnvelope * 8));

  // Slow colour drift
  hueShift += 0.00008;
  displayUniforms.hueShift.value = hueShift % 1;

  frameCount++;
  if (frameCount % 60 === 0 && audioState) {
    console.log(`FLUID beat:${audioState.isBeat ? 'YES' : 'no'} speed:${STEPS_PER_FRAME + Math.round(speedEnvelope * 8)}`);
  }
}
