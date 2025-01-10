
// Process newly added elements to DOM
htmx.on(
    'htmx:load',
    function(event) { htmx.process(event.detail.elt); },
);

// Root element
const root_div = document.getElementById("root");

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
        const fade_in = classes_list.filter(
            (c) => c.includes("fade-in"),
        ).pop();
        const next = classes_list.filter(
            (c) => c.includes("next"),
        ).pop();
        const previous = classes_list.filter(
            (c) => c.includes("previous"),
        ).pop();
        if (fade_in != null) {
            console.log(`Setting --swap-animation = ${fade_in}`)
            document.documentElement.style.setProperty(
                "--swap-animation",
                fade_in,
            );
        } else if (next != null) {
            console.log("Setting --swap-animation = swipe-in-from-right")
            document.documentElement.style.setProperty(
                "--swap-animation",
                "swipe-in-from-right",
            );
            root_div.firstElementChild.classList.add("swipe-out-to-left");
        } else if (previous != null) {
            console.log("Setting --swap-animation = swipe-in-from-left")
            document.documentElement.style.setProperty(
                "--swap-animation",
                "swipe-in-from-left",
            );
            root_div.firstElementChild.classList.add("swipe-out-to-right");
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
