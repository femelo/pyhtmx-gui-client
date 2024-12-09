htmx.on(
    "htmx:load",
    function(event) { htmx.process(event.detail.elt); },
);

