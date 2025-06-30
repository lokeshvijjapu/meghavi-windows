// 1. Prevent multi-touch (pinch/swipe) only if it's a pinch
['touchstart', 'touchmove', 'touchend'].forEach(evt =>
  document.addEventListener(evt, e => {
    if (e.touches.length > 1) e.preventDefault(); // only block multi-touch
  }, { passive: false })
);

// 2. Block Chrome-specific gesture events for pinch
['gesturestart', 'gesturechange', 'gestureend'].forEach(evt =>
  document.addEventListener(evt, e => e.preventDefault(), { passive: false })
);

// 3. Block right-click context menu
window.addEventListener('contextmenu', e => e.preventDefault(), true);

// 4. Prevent touchpad pinch-zoom via Ctrl + wheel
window.addEventListener('wheel', e => {
  if (e.ctrlKey) e.preventDefault();
}, { passive: false });
