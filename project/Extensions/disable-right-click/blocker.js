window.addEventListener('contextmenu', function(e) {
  debugger;
  console.log('Right-click attempt detected');
  e.preventDefault();
}, true);

