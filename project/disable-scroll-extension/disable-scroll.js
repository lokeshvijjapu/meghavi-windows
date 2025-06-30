// Disable scroll via CSS
const style = document.createElement('style');
style.textContent = `
  html, body {
    overflow: hidden !important;
    position: fixed !important;
    width: 100% !important;
    height: 100% !important;
    touch-action: none !important; /* Important for touch screens */
  }
`;
document.documentElement.appendChild(style);

// Prevent scrolling via mouse wheel
window.addEventListener('wheel', e => e.preventDefault(), { passive: false });

// Prevent keyboard scroll
window.addEventListener('keydown', e => {
  const keys = ['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '];
  if (keys.includes(e.key)) e.preventDefault();
}, true);

// Prevent touch scroll (touchscreen)
['touchstart', 'touchmove', 'touchend'].forEach(evt =>
  window.addEventListener(evt, e => e.preventDefault(), { passive: false })
);
