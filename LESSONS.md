# Lessons Learned

## Gray-Scott Simulation
- **Timestep > 1.2 causes numerical explosion** — explicit Euler stability limit is dt × dA ≈ 0.25
- **Too much initial chemical B floods the domain** — use 1 small circle (7% of screen), not 4-6 large ones
- **ANY perturbation to running simulation destroys it** — even +0.001 B applied for 1 iteration. The ping-pong loop runs 60 iterations per frame, so any uniform active during the loop gets applied 60×
- **f/k changes kill patterns** — the interesting region is a thin crescent; even ±0.003 can push into dead zones
- **Bias > 0.15 degrades maze structure** — destroys the Turing instability that creates intricate patterns
- **Maze patterns don't physically move** — they're connected static structures. Only spots/solitons respond to bias. User chose beautiful mazes over movement.
- **Changing iteration count per frame is imperceptible** — patterns evolve too slowly per-step for 30 vs 120 steps/frame to be visible
- **Pixel ratio 1 for simulation** — using devicePixelRatio makes circles too small on Retina and wastes GPU
- **Don't resize render targets** — it wipes simulation state. Let CSS scale.

## Audio Pipeline
- **Meyda features (rms, spectralFlux, etc.) come back as zero** despite mic being connected. Raw Web Audio AnalyserNode works. Use `getRawLevel()` as fallback.
- **`getByteFrequencyData` is useless for voice** — voice occupies ~5 of 128 frequency bins, averaging all bins dilutes the signal 25×. Use `getByteTimeDomainData` + RMS instead — measures amplitude regardless of frequency distribution.
- **Auto-normalization is essential** — mic levels vary wildly (0.001-0.1). Track observed max and normalize to 0-1.
- **Source node must be kept at module level** — if GC'd, the stream stops.
- The green meter bar confirms audio is flowing.

## Color Dancing
- **Direct level→uniform mapping doesn't feel like "dancing"** — it's just bright/dim with no rhythmic quality
- **Beat response is essential** — each beat must visibly shift hue (4-12% of color wheel), creating a color "kick" effect
- **Envelopes create the "pump" feel** — fast attack (~3 frames), slow decay (~25 frames) for luminosity. Without this, level changes feel mechanical
- **Hue range width should breathe with bass** — narrow (monochromatic) when quiet, wide (rainbow) when bassy
- **Hue rotation speed should track overall level** — louder = faster cycling
- Use `console.log` with prefix `DANCE` to verify all values in the chain

## Current State
- Maze patterns (f=0.029, k=0.057) with expanding ripples from center on each beat
- FFT bass energy (23-210 Hz) for beat detection, with tempo locking (~5s calibration)
- 8 concurrent ripple slots — clear ring (growth speed) + perturbation wave (reaches edge in ~3s)
- Slow hue drift through colour wheel, no audio-driven colour modulation
- Meyda removed from pipeline — only raw Web Audio AnalyserNode used

## Architecture
- Vite + Three.js + Meyda + GLSL shaders
- Ping-pong rendering: 60 iterations per frame at timestep 1.0
- Simulation is autonomous — audio only drives display shader (hue/saturation/luminosity)
