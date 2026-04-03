# Music-Reactive Screen Savers

Two browser-based screen savers that respond to music through your microphone.

**[Try Reaction-Diffusion](https://raggedr.github.io/reaction-diffusion-screensaver/)** | **[Try Fluid Dynamics](https://raggedr.github.io/reaction-diffusion-screensaver/fluid.html)**

## Reaction-Diffusion

[Gray-Scott](https://groups.csail.mit.edu/mac/projects/amorphous/GrayScott/) maze patterns that reconfigure on the beat. Expanding ripple waves travel from the center of the screen, forcing the maze to reorganise as they pass through — a wavefront of destruction followed by regrowth. Colours drift slowly through greens, teals, blues, and purples.

## Fluid Dynamics

[Kelvin-Helmholtz](https://en.wikipedia.org/wiki/Kelvin%E2%80%93Helmholtz_instability) vortex patterns driven by 2D Navier-Stokes. Beats inject vortex dipoles at the shear boundaries, stirring the fluid and creating swirling jets. The physics naturally carries the energy outward — like a lava lamp that dances to music.

## Quick Start

```bash
npm install
npm run dev
```

- **Reaction-Diffusion**: `http://localhost:5173`
- **Fluid Dynamics**: `http://localhost:5173/fluid.html`

Click to start, then grant microphone access. The screen savers detect the tempo from bass energy and lock onto the beat.

## No Microphone?

Both modes run autonomously without a mic — patterns evolve but don't respond to beats.

## Tech Stack

- **Vite** — build tool
- **Three.js** — WebGL rendering (ping-pong framebuffers)
- **GLSL** — Gray-Scott reaction-diffusion + Navier-Stokes fluid dynamics
- **Web Audio API** — FFT bass energy extraction and tempo detection

## Based On

- Gray-Scott shaders adapted from [reaction-diffusion-playground](https://github.com/jasonwebb/reaction-diffusion-playground) by Jason Webb
- Fluid dynamics solver uses the vorticity-streamfunction formulation with Semi-Lagrangian advection and Jacobi Poisson solver
