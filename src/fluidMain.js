/**
 * Fluid Screen Saver — Music-reactive Navier-Stokes
 */

import { setupFluidRenderer, initSimulation, runFluidStep, renderFluidToScreen } from './fluidRenderer.js';
import { fluidTick } from './fluidParameterDriver.js';
import { startAudio, isAudioActive, getRawLevel, getBassEnergy } from './audio.js';
import { setupScreensaver } from './screensaver.js';

let isRunning = false;

// --- Level normalization (same as main.js) ---
let noiseFloor = 0;
let signalPeak = 0.001;
let framesSinceStart = 0;

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

// --- Tempo detection + beat locking (same as main.js) ---
const LISTEN_DURATION_MS = 5000;
let listening = true;
let listenStartTime = 0;

let bassHistory = [];
const BASS_HISTORY_SIZE = 10;
let onsetTimes = [];
let lastOnsetTime = 0;

let locked = false;
let beatPeriodMs = 500;
let bpm = 120;
let nextBeatTime = 0;
let lastBeatTimeLock = 0;
let beatCount = 0;
const PHASE_CORRECTION = 0.15;

function detectOnset(bass) {
  bassHistory.push(bass);
  if (bassHistory.length > BASS_HISTORY_SIZE) bassHistory.shift();
  const avg = bassHistory.reduce((a, b) => a + b, 0) / bassHistory.length;
  const now = performance.now();
  return bass > avg * 1.4 && bass > 0.01 && (now - lastOnsetTime) > 150;
}

function listenForTempo(bass) {
  const now = performance.now();
  if (listenStartTime === 0) listenStartTime = now;

  if (detectOnset(bass)) {
    onsetTimes.push(now);
    lastOnsetTime = now;
  }

  if (now - listenStartTime < LISTEN_DURATION_MS) return;

  const intervals = [];
  for (let i = 1; i < onsetTimes.length; i++) {
    intervals.push(onsetTimes[i] - onsetTimes[i - 1]);
  }

  if (intervals.length < 3) {
    listenStartTime = now - LISTEN_DURATION_MS / 2;
    onsetTimes = onsetTimes.slice(-5);
    return;
  }

  const sorted = [...intervals].sort((a, b) => a - b);
  beatPeriodMs = sorted[Math.floor(sorted.length / 2)];
  bpm = 60000 / beatPeriodMs;

  if (bpm > 155) {
    beatPeriodMs *= 2;
    bpm /= 2;
  }

  locked = true;
  listening = false;
  nextBeatTime = now;
  lastBeatTimeLock = now;
  console.log(`LOCKED: ${bpm.toFixed(0)} BPM (period ${beatPeriodMs.toFixed(0)}ms)`);
}

function tickBeat(bass) {
  const now = performance.now();
  let isBeat = false;

  if (now >= nextBeatTime) {
    isBeat = true;
    beatCount++;
    lastBeatTimeLock = nextBeatTime;
    nextBeatTime += beatPeriodMs;
    if (nextBeatTime < now) nextBeatTime = now + beatPeriodMs;
  }

  if (detectOnset(bass)) {
    lastOnsetTime = now;
    const error = now - lastBeatTimeLock;
    if (error < beatPeriodMs * 0.5) {
      nextBeatTime += error * PHASE_CORRECTION;
    } else if (beatPeriodMs - error < beatPeriodMs * 0.5) {
      nextBeatTime -= (beatPeriodMs - error) * PHASE_CORRECTION;
    }
  }

  return isBeat;
}

// --- Debug meter ---
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

// --- Main loop ---

async function start() {
  const overlay = document.getElementById('start-overlay');
  if (overlay) overlay.classList.add('hidden');
  document.body.style.cursor = 'none';

  setupFluidRenderer();
  initSimulation();
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
    if (listening) listenForTempo(bass);
    else if (locked) isBeat = tickBeat(bass);

    audioState = {
      rms: level,
      bassEnergy: bass,
      isBeat,
      beatIntensity: isBeat ? Math.min(1, bass / 0.3) : 0
    };

    if (meterEl) {
      const fill = document.getElementById('meter-fill');
      fill.style.width = (bass * 500) + '%';
      fill.style.background = isBeat ? '#ff0' : '#0f0';
      if (meterTextEl) {
        const status = listening
          ? `listening... ${((performance.now() - listenStartTime) / 1000).toFixed(1)}s`
          : `${bpm.toFixed(0)} BPM — locked`;
        meterTextEl.textContent = `${status} | bass:${bass.toFixed(3)} beats:${beatCount}`;
      }
    }
  }

  fluidTick(audioState);
  runFluidStep();
  renderFluidToScreen();

  requestAnimationFrame(update);
}

document.getElementById('start-overlay').addEventListener('click', () => {
  if (!isRunning) start();
});
