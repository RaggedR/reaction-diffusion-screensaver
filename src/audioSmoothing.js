/**
 * Audio Smoothing — EMA smoothing, beat detection, and feature normalization.
 *
 * Raw Meyda features are noisy and variable. This module:
 * - Applies exponential moving averages for smooth parameter control
 * - Normalizes features to 0-1 based on adaptive min/max
 * - Detects beats via spectral flux threshold over moving average
 */

// Smoothed state
const state = {
  rms: 0,
  energy: 0,
  centroid: 0.5,
  flux: 0,
  flatness: 0,
  bassEnergy: 0,
  trebleEnergy: 0,
  isBeat: false,
  beatIntensity: 0,
  silence: true
};

// Beat detection state
const BEAT_HISTORY_SIZE = 15;
const BEAT_THRESHOLD = 1.2;    // Flux must exceed this × moving average (lowered for sensitivity)
const MIN_BEAT_GAP_MS = 150;    // Minimum ms between beats
let fluxHistory = [];
let lastBeatTime = 0;

// Silence detection
let silenceTimer = 0;
const SILENCE_THRESHOLD = 0.002;
const SILENCE_DELAY_MS = 2000;

// Adaptive normalization for spectral centroid (range varies by content)
let centroidMin = 50;
let centroidMax = 200;
const ADAPT_RATE = 0.001; // Slow adaptation for stable normalization

// EMA smoothing factors (higher = more responsive, lower = smoother)
// Cranked up for immediate response — we can smooth later once it works
const ALPHA = {
  rms: 0.5,
  energy: 0.5,
  centroid: 0.3,
  flux: 0.6,
  flatness: 0.3,
  bass: 0.5,
  treble: 0.4
};

function ema(current, target, alpha) {
  return current + alpha * (target - current);
}

function clamp01(v) {
  return Math.max(0, Math.min(1, v));
}

/**
 * Process raw Meyda features into smoothed, normalized audio state.
 * Call once per frame.
 */
export function processFeatures(features) {
  if (!features) return state;

  const now = performance.now();

  // --- RMS (already 0-1) ---
  state.rms = state.rms + ALPHA.rms * (features.rms - state.rms);

  // --- Energy (normalize from 0-512 range to 0-1) ---
  const normEnergy = clamp01(features.energy / 200);
  state.energy = state.energy + ALPHA.energy * (normEnergy - state.energy);

  // --- Spectral Centroid (adaptive normalization) ---
  const rawCentroid = features.spectralCentroid || 0;
  // Slowly adapt the observed range
  centroidMin = centroidMin + ADAPT_RATE * (rawCentroid - centroidMin);
  centroidMax = centroidMax + ADAPT_RATE * (rawCentroid - centroidMax);
  // Expand range if needed
  if (rawCentroid < centroidMin) centroidMin = rawCentroid;
  if (rawCentroid > centroidMax) centroidMax = rawCentroid;
  const range = Math.max(centroidMax - centroidMin, 10);
  const normCentroid = clamp01((rawCentroid - centroidMin) / range);
  state.centroid = state.centroid + ALPHA.centroid * (normCentroid - state.centroid);

  // --- Spectral Flatness (already 0-1) ---
  state.flatness = state.flatness + ALPHA.flatness * ((features.spectralFlatness || 0) - state.flatness);

  // --- Spectral Flux (for beat detection) ---
  const rawFlux = features.spectralFlux || 0;
  state.flux = state.flux + ALPHA.flux * (rawFlux - state.flux);

  // --- Loudness bark bands → bass and treble energy ---
  // Meyda loudness: .specific in v5, .bark in some versions
  const barkBands = features.loudness && (features.loudness.specific || features.loudness.bark);
  if (barkBands) {
    const bark = barkBands;

    // Bass: bark bands 0-5 (roughly 0-500 Hz)
    let bass = 0;
    for (let i = 0; i < Math.min(6, bark.length); i++) bass += bark[i];
    bass = clamp01(bass / 20);
    state.bassEnergy = state.bassEnergy + ALPHA.bass * (bass - state.bassEnergy);

    // Treble: bark bands 18-23 (roughly 7-15 kHz)
    let treble = 0;
    for (let i = 18; i < Math.min(24, bark.length); i++) treble += bark[i];
    treble = clamp01(treble / 5);
    state.trebleEnergy = state.trebleEnergy + ALPHA.treble * (treble - state.trebleEnergy);
  }

  // --- Beat detection via spectral flux ---
  fluxHistory.push(rawFlux);
  if (fluxHistory.length > BEAT_HISTORY_SIZE) fluxHistory.shift();

  const avgFlux = fluxHistory.reduce((a, b) => a + b, 0) / fluxHistory.length;
  const isBeat = rawFlux > avgFlux * BEAT_THRESHOLD && (now - lastBeatTime) > MIN_BEAT_GAP_MS;

  if (isBeat) {
    lastBeatTime = now;
    state.isBeat = true;
    state.beatIntensity = clamp01((rawFlux - avgFlux) / (avgFlux + 0.001));
  } else {
    state.isBeat = false;
    state.beatIntensity *= 0.85; // Decay
  }

  // --- Silence detection ---
  if (state.rms < SILENCE_THRESHOLD) {
    silenceTimer += 16; // ~1 frame at 60fps
    state.silence = silenceTimer > SILENCE_DELAY_MS;
  } else {
    silenceTimer = 0;
    state.silence = false;
  }

  return state;
}

export function getAudioState() {
  return state;
}
