// Block gesture events (Chrome-specific)
['gesturestart', 'gesturechange', 'gestureend'].forEach(evt =>
  window.addEventListener(evt, e => e.preventDefault(), { passive: false })
);

// Block multi-touch that might cause swipe nav
['touchstart', 'touchmove', 'touchend'].forEach(evt =>
  window.addEventListener(evt, e => {
    if (e.touches.length > 1) e.preventDefault();
  }, { passive: false })
);

// Block back/forward with wheel gesture (e.g., macOS two-finger horizontal swipe)
window.addEventListener('wheel', e => {
  if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
    // Horizontal scroll likely means back/forward gesture
    e.preventDefault();
  }
}, { passive: false });
