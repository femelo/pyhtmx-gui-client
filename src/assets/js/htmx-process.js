htmx.on(
    "htmx:load",
    function(event) { htmx.process(event.detail.elt); },
);

// Helper function
let dom_ready = (callback) => {
    document.readyState === 'interactive' || document.readyState === 'complete'
      ? callback()
      : document.addEventListener('DOMContentLoaded', callback);
  };
  
  dom_ready(() => {
    // Display body when DOM is loaded
    document.body.style.visibility = 'visible';
  });
  