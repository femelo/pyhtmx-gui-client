
// Process newly added elements to DOM
htmx.on(
    'htmx:load',
    function(event) { htmx.process(event.detail.elt); },
);

// Helper function
let dom_ready = (callback) => {
    document.readyState === 'interactive' || document.readyState === 'complete'
        ? callback()
        : document.addEventListener('DOMContentLoaded', callback);
};


// Function to set animation before swapping the element in
function set_animation(event) {
    const classes_match = /(?<=class=")[^\"\=]*(?=")/.exec(event.detail.data);
    if (classes_match != null) {
        const classes_list = classes_match[0].split(' ');
        const match = classes_list.filter(
            (c) => c.includes("fade-in"),
        ).pop();
        if (match != null) {
            console.log(`Setting --swap-animation = ${match}`)
            document.documentElement.style.setProperty(
                "--swap-animation",
                match,
            );
        } else {
            // console.log("Unsetting --swap-animation");
            document.documentElement.style.removeProperty(
                "--swap-animation",
            );
        }
    }
};


dom_ready(() => {
    // Display body when DOM is loaded
    document.body.style.visibility = 'visible';
    const session_element = document.getElementById("session-id");
    if (session_element != null) {
        const session_id = session_element.textContent;
        console.log(`Session opened: ${session_id}`);
    }
    document.body.addEventListener(
        'htmx:sseBeforeMessage',
        set_animation,
    );
});
