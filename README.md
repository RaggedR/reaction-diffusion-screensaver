# Music-Reactive Screen Savers & Mazes

Browser-based screen savers that respond to music, plus interactive maze generators.

**[Try Reaction-Diffusion](https://raggedr.github.io/reaction-diffusion-screensaver/)** | **[Try Fluid Dynamics](https://raggedr.github.io/reaction-diffusion-screensaver/fluid.html)** | **[Tree Surgery Maze](https://raggedr.github.io/reaction-diffusion-screensaver/mazes/interactive.html)** | **[Knotted Maze](https://raggedr.github.io/reaction-diffusion-screensaver/mazes/knotted.html)**
## Reaction-Diffusion

[Gray-Scott](https://groups.csail.mit.edu/mac/projects/amorphous/GrayScott/) maze patterns that reconfigure on the beat. Expanding ripple waves travel from the center of the screen, forcing the maze to reorganise as they pass through — a wavefront of destruction followed by regrowth. Colours drift slowly through greens, teals, blues, and purples.

## Fluid Dynamics

[Kelvin-Helmholtz](https://en.wikipedia.org/wiki/Kelvin%E2%80%93Helmholtz_instability) vortex patterns driven by 2D Navier-Stokes. Beats inject vortex dipoles at the shear boundaries, stirring the fluid and creating swirling jets. The physics naturally carries the energy outward — like a lava lamp that dances to music.

## Mazes

### Tree Surgery

Interactive maze built with Kruskal's algorithm on an expanded graph. Click any cell to sever its subtree and regrow it — the maze restructures in real time. Supports DFS, Wilson's, Kruskal's, and Prim's algorithms.

### Knotted Maze

Fullscreen animated screen saver. Generates a knotted maze using Kruskal's on an expanded graph where some cells become crossings (two independent strands passing through). Periodically performs tree surgery — pruning and regrowing subtrees to keep the maze evolving.

## Quick Start

```bash
npm install
npm run dev
```

- **Reaction-Diffusion**: `http://localhost:5173`
- **Fluid Dynamics**: `http://localhost:5173/fluid.html`
- **Tree Surgery Maze**: `http://localhost:5173/mazes/interactive.html`
- **Knotted Maze**: `http://localhost:5173/mazes/knotted.html`

Click to start the screen savers, then grant microphone access. They detect the tempo from bass energy and lock onto the beat.

## No Microphone?

The screen savers run autonomously without a mic — patterns evolve but don't respond to beats. The maze modes don't use audio.

## Tech Stack

- **Vite** — build tool
- **Three.js** — WebGL rendering (ping-pong framebuffers)
- **GLSL** — Gray-Scott reaction-diffusion + Navier-Stokes fluid dynamics
- **Web Audio API** — FFT bass energy extraction and tempo detection

## Based On

- Gray-Scott shaders adapted from [reaction-diffusion-playground](https://github.com/jasonwebb/reaction-diffusion-playground) by Jason Webb
- Fluid dynamics solver uses the vorticity-streamfunction formulation with Semi-Lagrangian advection and Jacobi Poisson solver
