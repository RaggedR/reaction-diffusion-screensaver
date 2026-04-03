/**
 * Audio — mic input with FFT-based bass energy detection.
 *
 * Uses Web Audio AnalyserNode for:
 * - Time-domain RMS (overall level, for meter)
 * - Frequency-domain bass energy (bins ~23-210 Hz, for beat detection)
 */

let audioContext = null;
let source = null;  // Keep reference to prevent GC
let analyser = null;
let isActive = false;

// Buffers
let timeDomainBuffer = null;  // For RMS
let frequencyBuffer = null;   // For bass energy

// FFT config — 2048-point at 48kHz gives ~23 Hz per bin
// Bass bins: 1-9 covers ~23-210 Hz (kick drum, bass guitar)
const BASS_BIN_START = 1;
const BASS_BIN_END = 9;

export async function startAudio() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new (window.AudioContext || window.webkitAudioContext)();

    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    const sampleRate = audioContext.sampleRate;
    console.log('AudioContext:', audioContext.state, 'sampleRate:', sampleRate);

    source = audioContext.createMediaStreamSource(stream);

    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.4;
    source.connect(analyser);

    timeDomainBuffer = new Uint8Array(analyser.fftSize);
    frequencyBuffer = new Uint8Array(analyser.frequencyBinCount);

    const binHz = sampleRate / analyser.fftSize;
    console.log(`FFT: ${analyser.frequencyBinCount} bins, ${binHz.toFixed(1)} Hz/bin`);
    console.log(`Bass range: bins ${BASS_BIN_START}-${BASS_BIN_END} = ${(BASS_BIN_START * binHz).toFixed(0)}-${(BASS_BIN_END * binHz).toFixed(0)} Hz`);

    const tracks = stream.getAudioTracks();
    console.log('Mic:', tracks[0]?.label);

    isActive = true;
    return true;
  } catch (err) {
    console.warn('Audio not available:', err.message);
    isActive = false;
    return false;
  }
}

/**
 * Overall RMS level (time-domain). For the meter and general level.
 */
export function getRawLevel() {
  if (!analyser || !timeDomainBuffer) return 0;
  analyser.getByteTimeDomainData(timeDomainBuffer);
  let sum = 0;
  for (let i = 0; i < timeDomainBuffer.length; i++) {
    const s = (timeDomainBuffer[i] - 128) / 128;
    sum += s * s;
  }
  return Math.sqrt(sum / timeDomainBuffer.length);
}

/**
 * Bass energy from FFT (frequency-domain).
 * Returns the average magnitude of bins in the ~23-210 Hz range.
 * Kick drums, bass drops, and low thumps live here.
 */
export function getBassEnergy() {
  if (!analyser || !frequencyBuffer) return 0;
  analyser.getByteFrequencyData(frequencyBuffer);
  let sum = 0;
  for (let i = BASS_BIN_START; i <= BASS_BIN_END; i++) {
    sum += frequencyBuffer[i];
  }
  return sum / ((BASS_BIN_END - BASS_BIN_START + 1) * 255);  // Normalize to 0-1
}

export function isAudioActive() {
  return isActive;
}
