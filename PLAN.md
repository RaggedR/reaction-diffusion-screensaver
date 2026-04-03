# Music-Reactive Reaction-Diffusion Screen Saver

## Context
Robin wants a screen saver that "dances" to music using Belousov-Zhabotinsky / Turing patterns. We have a production-quality Gray-Scott reaction-diffusion playground at `~/git/reaction-diffusion-playground/` (Three.js + WebGL + GLSL shaders). We'll extract its GPU core, add Meyda for real-time microphone audio analysis, and map audio features to simulation parameters.

## Architecture

```
Microphone → Web Audio API → Meyda (86 Hz)
                                ↓
                    AudioSmoothing (EMA + beat detection)
                                ↓
                    ParameterDriver (audio → uniforms)
                                ↓
              ┌─────────────────┼──────────────────┐
              ↓                 ↓                  ↓
        f, k, dA, dB     injectionTexture     hsl colors
        timestep, bias    (beat splashes)      luminosity
              ↓                 ↓                  ↓
        simulationFrag.glsl ←──┘          displayFrag.glsl
              ↓                                    ↓
        Ping-pong (60 iters/frame)          Color mapping
              ↓                                    ↓
              └────────────── Screen ──────────────┘
```

## Tech Stack
- **Vite** + `vite-plugin-glsl` (replaces Webpack 4)
- **Three.js** (modern, r160+; use `PlaneGeometry`, drop uniform `type` fields)
- **Meyda** (MIT, npm) for audio feature extraction
- GLSL shaders adapted from existing playground

## Project Structure
```
~/screen-saver/
  index.html                 -- Fullscreen, click-to-start overlay
  package.json               -- vite, three, meyda, vite-plugin-glsl
  vite.config.js
  src/
    main.js                  -- Entry: init, render loop
    renderer.js              -- Three.js setup, ping-pong buffers
    audio.js                 -- Meyda mic analyzer
    audioSmoothing.js        -- EMA smoothing, beat detection, normalization
    parameterDriver.js       -- Audio features → uniform mappings
    presetPath.js            -- Catmull-Rom spline through 25 (f,k) presets
    injectionManager.js      -- Canvas-based beat splash texture
    uniforms.js              -- All uniform declarations
    materials.js             -- ShaderMaterial constructors
    firstFrame.js            -- Seed initial circles
    screensaver.js           -- Fullscreen, cursor hide, ESC exit
    shaders/
      simulationFrag.glsl    -- Gray-Scott + injection texture (modified)
      simulationVert.glsl    -- Laplacian stencil (unchanged)
      displayFrag.glsl       -- 9 color modes (unchanged)
      displayVert.glsl       -- Passthrough (unchanged)
      passthroughFrag.glsl   -- Passthrough (unchanged)
      passthroughVert.glsl   -- Passthrough (unchanged)
```

## Audio → Parameter Mapping

| Audio Feature | → Uniform | Effect |
|---|---|---|
| spectralCentroid (0-1) | Path position `t` velocity | Bright sounds advance toward complex patterns |
| bassEnergy (bark 0-5) | `f` perturbation ±0.004 | Bass shifts feed rate |
| spectralFlatness (0-1) | `k` perturbation ±0.002 | Noisy sounds shift kill rate |
| rms (0-1) | `dB` + 0.05 | Louder = more fluid patterns |
| energy (0-1) | `timestep` + 0.3 | Louder = faster simulation |
| centroid (0-1) | `bias.x` ±0.15 | Frequency brightness → directional flow |
| flatness (0-1) | `bias.y` ±0.1 | Noise/tone → vertical flow |
| trebleEnergy (bark 18-23) | `hslTo` range width | Treble widens hue range |
| rms | `hslSaturation` 0.5-0.9 | Louder = more saturated |
| beat detected | injection splashes + timestep spike + luminosity flash | Multi-layered beat response |

## Preset Path Strategy (Option C)
The (f,k) parameter space is mostly dead zones. We define a **spline path** through the 25 known-good presets ordered by visual complexity (Waves → Spots → Worms → Mazes → Chaos → Bubbles). Audio controls position along this 1D path + small perturbations. Guarantees visual interest at all times.

## Shader Modification (minimal)
Only `simulationFrag.glsl` changes — add `injectionTexture` uniform for beat splashes:
```glsl
uniform sampler2D injectionTexture;
uniform float injectionAmount;
// In main(): read injection.r, add to B chemical output
```
Remove `mousePosition`/`brushRadius` (no mouse in screensaver). Display shader unchanged.

## Build Order

### Phase 1: Static renderer (no audio)
1. Init project (npm, vite, three, vite-plugin-glsl)
2. Copy & adapt shaders, uniforms, materials, renderer, firstFrame
3. Create render loop with ping-pong
4. **Verify**: `npx vite dev` → patterns grow from circle

### Phase 2: Autonomous drift
5. Create presetPath.js with Catmull-Rom spline
6. Create parameterDriver.js with time-only drift
7. **Verify**: Patterns slowly transition through types over ~5 min

### Phase 3: Audio input
8. Create audio.js (Meyda + mic)
9. Create audioSmoothing.js (EMA, beat detection)
10. Add click-to-start overlay for permissions
11. **Verify**: Console-log features, verify beat detection

### Phase 4: Audio → parameters
12. Wire all audio mappings into parameterDriver.js
13. **Verify**: Play music → patterns visibly respond

### Phase 5: Beat response
14. Create injectionManager.js (canvas texture)
15. Wire injection into simulation shader
16. Add timestep spike + luminosity flash
17. **Verify**: Beats trigger visible pattern blooms

### Phase 6: Screensaver polish
18. Fullscreen, cursor hide, ESC exit, permission-denied fallback
19. **Verify**: Full experience end-to-end

### Phase 7: Tuning
20. Test with various music genres, adjust mapping constants
21. Color palette cycling, rendering style variety

## Key Source Files (to copy/adapt from)
- `~/git/reaction-diffusion-playground/glsl/*.glsl` — All 6 shaders
- `~/git/reaction-diffusion-playground/entry.js` — Render loop pattern
- `~/git/reaction-diffusion-playground/js/uniforms.js` — Uniform structure
- `~/git/reaction-diffusion-playground/js/parameterPresets.js` — 25 (f,k) pairs
- `~/git/reaction-diffusion-playground/js/renderTargets.js` — Ping-pong setup
- `~/git/reaction-diffusion-playground/js/parameterMetadata.js` — Safe ranges

## Confidence
- Phase 1-2 (renderer): 90% — proven shaders, minor adaptations
- Phase 3 (audio): 80% — well-documented API, browser permission fiddliness
- Phase 4-5 (mapping): 70% first-pass — mapping constants will need tuning
- Phase 7 (tuning): iterative creative work, hard to predict
