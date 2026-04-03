# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A music-reactive screen saver built on Gray-Scott reaction-diffusion. Maze patterns grow from seeds, and beats in the music trigger expanding ripples of reconfiguration across the screen. Colours drift slowly through the spectrum.

## Architecture

```
Microphone → Web Audio API (FFT) → Bass energy → Tempo detection → Beat clock
                                                                      ↓
                                                        Expanding ripple rings
                                                                      ↓
                                              Gray-Scott simulation (GLSL shader)
                                                                      ↓
                                              HSL colour mapping → Screen
```

## Key Files

- `src/main.js` — Entry point, audio pipeline, tempo detection, beat locking
- `src/parameterDriver.js` — Maps beats to ripple uniforms, manages concurrent ripples
- `src/audio.js` — Mic input, FFT bass energy extraction
- `src/renderer.js` — Three.js ping-pong rendering, simulation step loop
- `src/shaders/simulationFrag.glsl` — Gray-Scott equations + ripple perturbation
- `src/shaders/displayFrag.glsl` — HSL colour mapping (9 rendering styles)
- `src/uniforms.js` — All shader uniform declarations
- `src/presetPath.js` — Catmull-Rom spline through 24 (f,k) presets

## Commands

```bash
npm run dev      # Start dev server (Vite)
npm run build    # Production build
npm run preview  # Preview production build
```

## Critical Constraints (from LESSONS.md)

- **Timestep > 1.2 causes numerical explosion** — explicit Euler stability limit
- **ANY perturbation to running simulation can destroy it** — the ripple shader carefully clears a thin ring, not a filled circle
- **f/k changes kill patterns** — the interesting region is a thin crescent in parameter space
- **Don't resize render targets** — it wipes simulation state. CSS scales instead.
- **Pixel ratio must be 1** — devicePixelRatio makes circles too small on Retina
- **Renderer clears ripple uniforms after iteration 0** — perturbation applies ONCE per frame, not 60×

## How the Ripples Work

1. Beat detected → new ripple added to array (up to 8 concurrent)
2. Each frame: clear ring expands slowly (1.5 px/frame), wave ring expands fast (~12 px/frame)
3. Shader applies perturbation at the wavefront: thin ring adds B chemical → maze reconfigures
4. Clear ring wipes a small zone at center and plants a seed → new maze grows outward
5. Renderer clears all ripple uniforms after the first ping-pong iteration to prevent 60× application

## Audio Pipeline

1. Mic → AnalyserNode (FFT size 2048)
2. `getBassEnergy()` — averages FFT bins 1-9 (~23-210 Hz)
3. `getRawLevel()` — time-domain RMS for the meter
4. Tempo detection: 5-second listening phase, collects bass onsets, computes median interval
5. Beat clock: fires on schedule with phase correction toward real onsets
6. If BPM > 155, auto-halves to every other beat
