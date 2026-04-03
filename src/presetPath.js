/**
 * Preset Path — a smooth spline through known-good (f,k) parameter space.
 *
 * The Gray-Scott parameter space is mostly dead zones. Only a thin crescent
 * produces interesting patterns. This module defines a tour through 24 known-good
 * presets, ordered by visual complexity, and provides Catmull-Rom interpolation
 * so any t in [0,1] gives a visually interesting (f,k,dA,dB) point.
 */

// Presets ordered by visual complexity (simple → complex → chaotic → bubbles)
// Based on Robert Munafo's Gray-Scott Explorer: https://mrob.com/pub/comp/xmorphia/
const PRESETS = [
  { name: 'Waves',                  f: 0.014, k: 0.045 },
  { name: 'Moving spots',           f: 0.014, k: 0.054 },
  { name: 'Spots and loops',        f: 0.018, k: 0.051 },
  { name: 'Warring microbes',       f: 0.022, k: 0.059 },
  { name: 'Pulsating solitons',     f: 0.025, k: 0.060 },
  { name: 'Chaos',                  f: 0.026, k: 0.051 },
  { name: 'Mazes with some chaos',  f: 0.026, k: 0.055 },
  { name: 'Mazes',                  f: 0.029, k: 0.057 },
  { name: 'Super-resonant mazes',   f: 0.030, k: 0.0565 },
  { name: 'Self-replicating spots', f: 0.030, k: 0.063 },
  { name: 'Spots and worms',        f: 0.034, k: 0.0618 },
  { name: 'Chaos with negatons',    f: 0.0353, k: 0.0566 },
  { name: 'Fingerprints',           f: 0.037, k: 0.060 },
  { name: 'Chaos to Turing',        f: 0.039, k: 0.058 },
  { name: 'Turing patterns',        f: 0.042, k: 0.059 },
  { name: 'Negatons',               f: 0.046, k: 0.0594 },
  { name: 'Worms join into maze',   f: 0.046, k: 0.063 },
  { name: 'Worms',                  f: 0.058, k: 0.065 },
  { name: 'The U-Skate World',      f: 0.062, k: 0.0609 },
  { name: 'Stable solitons',        f: 0.074, k: 0.064 },
  { name: 'Worms and loops',        f: 0.082, k: 0.060 },
  { name: 'Precritical bubbles',    f: 0.082, k: 0.059 },
  { name: 'Negative bubbles',       f: 0.098, k: 0.0555 },
  { name: 'Positive bubbles',       f: 0.098, k: 0.057 },
];

const N = PRESETS.length;

/**
 * Catmull-Rom interpolation between four values.
 * tension = 0.5 gives standard Catmull-Rom.
 */
function catmullRom(p0, p1, p2, p3, t) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (
    (2.0 * p1) +
    (-p0 + p2) * t +
    (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
    (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
  );
}

/**
 * Get a point on the preset path at position t (0 to 1, wrapping).
 * Returns { f, k, dA, dB, name } with Catmull-Rom interpolated values.
 */
export function getPresetPoint(t) {
  // Wrap t to [0, 1)
  t = ((t % 1) + 1) % 1;

  const segment = t * N;
  const i = Math.floor(segment);
  const frac = segment - i;

  // Get 4 control points with wrapping
  const p0 = PRESETS[((i - 1) % N + N) % N];
  const p1 = PRESETS[i % N];
  const p2 = PRESETS[(i + 1) % N];
  const p3 = PRESETS[(i + 2) % N];

  return {
    f: catmullRom(p0.f, p1.f, p2.f, p3.f, frac),
    k: catmullRom(p0.k, p1.k, p2.k, p3.k, frac),
    dA: 0.2097,
    dB: 0.105,
    name: p1.name
  };
}

export { PRESETS };
