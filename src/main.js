/**
 * Screen Saver — Music-reactive reaction-diffusion
 */

import * as THREE from 'three';
import { setupRenderer, runSimulationStep, renderToScreen } from './renderer.js';
import { drawFirstFrame } from './firstFrame.js';
import { tick } from './parameterDriver.js';
import { simulationUniforms, displayUniforms } from './uniforms.js';
import { startAudio, isAudioActive, getRawLevel, getBassEnergy } from './audio.js';
import { setupScreensaver } from './screensaver.js';

const clock = new THREE.Clock();
let isRunning = false;

// Level normalization
let noiseFloor = 0;
let signalPeak = 0.001;
let framesSinceStart = 0;

// === Tempo detection + beat locking ===
const LISTEN_DURATION_MS = 5000;  // Listen for 5 seconds to find tempo
let listening = true;
let listenStartTime = 0;

// Onset detection during listening phase
let bassHistory = [];
const BASS_HISTORY_SIZE = 10;
let onsetTimes = [];         // Timestamps of detected bass onsets
let lastOnsetTime = 0;

// Locked beat state
let locked = false;
let beatPeriodMs = 500;      // Detected beat period (ms)
let bpm = 120;
let nextBeatTime = 0;
let lastBeatTime = 0;
let beatCount = 0;

// Phase correction: nudge toward real onsets
const PHASE_CORRECTION = 0.15;  // How much to adjust toward detected onsets

// Debug UI
let meterEl, meterTextEl;

function createMeter() {
  meterEl = document.createElement('div');
  meterEl.style.cssText = 'position:fixed;bottom:20px;left:20px;width:400px;z-index:100;font:14px monospace;color:#aaa;background:rgba(0,0,0,0.6);padding:10px;border-radius:8px';
  const barOuter = document.createElement('div');
  barOuter.style.cssText = 'height:12px;background:#222;border-radius:6px;overflow:hidden;margin-bottom:6px';
  const barInner = document.createElement('div');
  barInner.id = 'meter-fill';
  barInner.style.cssText = 'height:100%;width:0%;background:#0f0;transition:width 0.05s';
  barOuter.appendChild(barInner);
  meterTextEl = document.createElement('div');
  meterEl.appendChild(barOuter);
  meterEl.appendChild(meterTextEl);
  document.body.appendChild(meterEl);

}

function normalize(raw) {
  framesSinceStart++;
  if (framesSinceStart > 60) {
    if (raw < noiseFloor || noiseFloor === 0) {
      noiseFloor += (raw - noiseFloor) * 0.05;
    } else {
      noiseFloor += (raw - noiseFloor) * 0.0005;
    }
  }
  if (raw > signalPeak) signalPeak = raw;
  else signalPeak *= 0.999;

  const floor = noiseFloor * 1.2;
  const range = Math.max(signalPeak - floor, 0.005);
  return Math.min(1, Math.max(0, raw - floor) / range);
}

/**
 * Detect a bass onset (spike in bass energy above recent average).
 */
function detectOnset(bass) {
  bassHistory.push(bass);
  if (bassHistory.length > BASS_HISTORY_SIZE) bassHistory.shift();

  const avg = bassHistory.reduce((a, b) => a + b, 0) / bassHistory.length;
  const now = performance.now();

  return bass > avg * 1.4
    && bass > 0.01
    && (now - lastOnsetTime) > 150;  // Debounce
}

/**
 * Listening phase: collect onset timestamps, then compute tempo.
 */
function listenForTempo(bass) {
  const now = performance.now();

  if (listenStartTime === 0) listenStartTime = now;

  if (detectOnset(bass)) {
    onsetTimes.push(now);
    lastOnsetTime = now;
    console.log(`ONSET #${onsetTimes.length} bass:${bass.toFixed(4)}`);
  }

  // Log bass levels every second during listening
  if (Math.floor((now - listenStartTime) / 1000) > Math.floor((now - listenStartTime - 16) / 1000)) {
    const avg = bassHistory.length > 0 ? (bassHistory.reduce((a, b) => a + b, 0) / bassHistory.length) : 0;
    console.log(`LISTENING bass:${bass.toFixed(4)} avg:${avg.toFixed(4)} onsets:${onsetTimes.length}`);
  }

  // Done listening?
  if (now - listenStartTime < LISTEN_DURATION_MS) return;

  // Compute inter-onset intervals
  const intervals = [];
  for (let i = 1; i < onsetTimes.length; i++) {
    intervals.push(onsetTimes[i] - onsetTimes[i - 1]);
  }

  if (intervals.length < 3) {
    // Not enough onsets — keep listening
    listenStartTime = now - LISTEN_DURATION_MS / 2;
    onsetTimes = onsetTimes.slice(-5);
    console.log('Not enough beats detected, listening more...');
    return;
  }

  // Find the median interval (robust to outliers)
  const sorted = [...intervals].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];

  beatPeriodMs = median;
  bpm = 60000 / beatPeriodMs;

  // If too fast (> 155 BPM), pulse every other beat
  if (bpm > 155) {
    beatPeriodMs *= 2;
    bpm /= 2;
    console.log(`Tempo too fast, halving to ${bpm.toFixed(0)} BPM`);
  }

  // Lock!
  locked = true;
  listening = false;
  nextBeatTime = now;
  lastBeatTime = now;

  console.log(
    `LOCKED: ${bpm.toFixed(0)} BPM (period ${beatPeriodMs.toFixed(0)}ms) ` +
    `from ${intervals.length} intervals`
  );
}

/**
 * Locked phase: fire beats on schedule, nudge phase toward real onsets.
 */
function tickBeat(bass) {
  const now = performance.now();
  let isBeat = false;

  // Fire if we've reached the next predicted beat time
  if (now >= nextBeatTime) {
    isBeat = true;
    beatCount++;
    lastBeatTime = nextBeatTime;
    nextBeatTime += beatPeriodMs;

    // If we've fallen behind (e.g. tab was backgrounded), catch up
    if (nextBeatTime < now) {
      nextBeatTime = now + beatPeriodMs;
    }
  }

  // Phase correction: if we detect a real onset near the predicted time,
  // nudge toward it to stay in sync with the music
  if (detectOnset(bass)) {
    lastOnsetTime = now;
    const error = now - lastBeatTime;

    // Only correct if onset is within half a beat of the predicted time
    if (error < beatPeriodMs * 0.5) {
      nextBeatTime += error * PHASE_CORRECTION;
    } else if (beatPeriodMs - error < beatPeriodMs * 0.5) {
      nextBeatTime -= (beatPeriodMs - error) * PHASE_CORRECTION;
    }
  }

  return isBeat;
}

async function start() {
  const overlay = document.getElementById('start-overlay');
  if (overlay) overlay.classList.add('hidden');
  document.body.style.cursor = 'none';

  setupRenderer();
  drawFirstFrame();
  createMeter();

  isRunning = true;
  update();

  setupScreensaver(() => { isRunning = false; });

  const audioOk = await startAudio();
  if (!audioOk && meterTextEl) {
    meterTextEl.textContent = 'No mic — autonomous mode';
  }
}

function update() {
  if (!isRunning) return;

  let audioState = null;

  if (isAudioActive()) {
    const raw = getRawLevel();
    const level = normalize(raw);
    const bass = getBassEnergy();

    let isBeat = false;

    if (listening) {
      listenForTempo(bass);
    } else if (locked) {
      isBeat = tickBeat(bass);
    }

    audioState = {
      rms: level,
      bassEnergy: bass,
      isBeat,
      beatIntensity: isBeat ? Math.min(1, bass / 0.3) : 0
    };

    // Update meter
    if (meterEl) {
      const fill = document.getElementById('meter-fill');
      fill.style.width = (bass * 500) + '%';  // Bass energy scaled for visibility
      fill.style.background = isBeat ? '#ff0' : '#0f0';
      if (meterTextEl) {
        const status = listening ? `listening... ${((performance.now() - listenStartTime) / 1000).toFixed(1)}s` :
          `${bpm.toFixed(0)} BPM — locked`;
        meterTextEl.textContent = `${status} | bass:${bass.toFixed(3)} beats:${beatCount}`;
      }
    }
  }

  tick(audioState);
  runSimulationStep();
  renderToScreen(clock);

  requestAnimationFrame(update);
}

document.getElementById('start-overlay').addEventListener('click', () => {
  if (!isRunning) start();
});
