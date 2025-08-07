// Disable right-click menu
document.addEventListener('contextmenu', function(e) {
  e.preventDefault();
}, true);

// Prevent text selection
document.addEventListener('selectstart', function(e) {
  e.preventDefault();
}, true);

// Suppress touch/hold behavior (not usually needed on Windows, but safe to include)
document.addEventListener('touchstart', function(e) {
  if (e.touches && e.touches.length > 1) {
    e.preventDefault();
  }
}, { passive: false });
