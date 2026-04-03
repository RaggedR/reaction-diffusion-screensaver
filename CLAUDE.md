# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Two music-reactive screen savers sharing the same audio pipeline:

1. **Reaction-Diffusion** (`index.html`) — Gray-Scott maze patterns with beat-triggered expanding ripples
2. **Fluid Dynamics** (`fluid.html`) — Kelvin-Helmholtz vortices with beat-triggered vortex dipole injection

## Architecture

```
Microphone → Web Audio API (FFT) → Bass energy → Tempo detection → Beat clock
                                                                      ↓
                                                              ┌───────┴───────┐
                                                              ↓               ↓
                                                    Reaction-Diffusion    Fluid Dynamics
                                                    (ripple rings)        (vortex dipoles)
                                                              ↓               ↓
                                                    Gray-Scott GLSL     Navier-Stokes GLSL
                                                              ↓               ↓
                                                         HSL mapping    Diverging colormap
                                                              ↓               ↓
                                                              └───── Screen ──┘
```

## Key Files

### Shared
- `src/audio.js` — Mic input, FFT bass energy extraction (bins 1-9, 23-210 Hz)
- `src/screensaver.js` — Fullscreen, cursor hide, ESC exit

### Reaction-Diffusion Mode
- `index.html` → `src/main.js` — Entry, audio, beat detection, render loop
- `src/parameterDriver.js` — Beat → ripple uniforms (8 concurrent)
- `src/renderer.js` — Ping-pong rendering (2 render targets)
- `src/uniforms.js`, `src/materials.js`
- `src/shaders/simulationFrag.glsl` — Gray-Scott equations + ripple perturbation
- `src/shaders/displayFrag.glsl` — HSL colour mapping

### Fluid Dynamics Mode
- `fluid.html` → `src/fluidMain.js` — Entry, audio, beat detection, render loop
- `src/fluidParameterDriver.js` — Beat → vortex dipole injection at shear boundaries
- `src/fluidRenderer.js` — 4 render targets (omega[2] + psi[2]), Jacobi Poisson solver
- `src/fluidUniforms.js`, `src/fluidMaterials.js`
- `src/shaders/fluid/advect.frag.glsl` — Semi-Lagrangian advection + viscous diffusion
- `src/shaders/fluid/jacobi.frag.glsl` — Poisson iteration for streamfunction
- `src/shaders/fluid/inject.frag.glsl` — Vortex dipole injection
- `src/shaders/fluid/display.frag.glsl` — Diverging colormaps (cyan-orange, cool-warm, inferno)

## Commands

```bash
npm run dev      # Start dev server (Vite)
npm run build    # Production build (both entry points)
npm run preview  # Preview production build
```

## Critical Constraints

### Reaction-Diffusion
- **Timestep > 1.2 causes numerical explosion** — explicit Euler stability limit
- **ANY perturbation can destroy the simulation** — ripple shader clears a thin ring, not a filled circle
- **f/k changes kill patterns** — the interesting region is a thin crescent in parameter space
- **Don't resize render targets** — wipes simulation state
- **Renderer clears ripple uniforms after iteration 0** — perturbation applies ONCE per frame, not 60×

### Fluid Dynamics
- **Jacobi solver needs 500 warm-up iterations** at SIM_SIZE=128 (cold-start convergence is slow)
- **SIM_SIZE=256 requires ~5000 warm-up** — Jacobi convergence scales as cos(2π/N)^iters
- **Stick to SIM_SIZE=128** — proven stable, 256 causes convergence failures
- **Vortex injection must preserve zero net circulation** — dipole design (±Gaussian) satisfies this
- **Inject at shear boundaries (y=0.25, y=0.75)** — perpendicular orientation for maximum mixing

## Audio Pipeline (shared)

1. Mic → AnalyserNode (FFT size 2048)
2. `getBassEnergy()` — averages FFT bins 1-9 (~23-210 Hz)
3. `getRawLevel()` — time-domain RMS for the meter
4. Tempo detection: 5-second listening phase, collects bass onsets, computes median interval
5. Beat clock: fires on schedule with phase correction toward real onsets
6. If BPM > 155, auto-halves to every other beat
