/**
 * Screensaver UX — fullscreen, cursor hiding, ESC to exit.
 */

let onExitCallback = null;
let isFullscreen = false;

export function setupScreensaver(onExit) {
  onExitCallback = onExit;

  // ESC shows the restart overlay (but doesn't kill the simulation)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      showOverlay();
    }
  });
}

export async function enterFullscreen() {
  try {
    await document.documentElement.requestFullscreen();
    isFullscreen = true;
  } catch {
    // Fullscreen not supported or denied — works fine windowed
  }
}

function showOverlay() {
  document.body.style.cursor = '';

  const overlay = document.getElementById('start-overlay');
  if (overlay) {
    overlay.textContent = 'Click to restart';
    overlay.classList.remove('hidden');
  }

  if (onExitCallback) onExitCallback();
}
