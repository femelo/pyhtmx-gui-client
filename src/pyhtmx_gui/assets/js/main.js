
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

const status_elements = ["speech", "utterance", "spinner"];

// TODO: avoid duplication of code
// Function to show tabs temporarily and adjust fullscreen image
function show_tabs() {
    const bottom_container = document.getElementById("bottom-container");
    const full_screen_image = document.getElementById("full-screen-image");
    if (bottom_container != null && full_screen_image != null) {
        // Remove the ‘hidden’ classes from the tabs
        bottom_container.classList.remove("tabs-hidden");
        // Add the ‘tabs-shown’ class to make them visible
        bottom_container.classList.add("tabs-shown");

        // Make the full-screen image smaller
        full_screen_image.classList.add("small");
    }
}

function hide_tabs() {
    const utterance_input = document.getElementById("utterance-input");
    const bottom_container = document.getElementById("bottom-container");
    const full_screen_image = document.getElementById("full-screen-image");
    if (utterance_input !== document.activeElement && bottom_container != null && full_screen_image != null) {
        bottom_container.classList.remove("tabs-shown"); // Hide the tabs after 2 seconds
        bottom_container.classList.add("tabs-hidden");

        // Resize the full-screen image
        full_screen_image.classList.remove("small");
    }
}


// Function to set animation before swapping the element in
function set_animation(event) {
    // Get the classes of the element
    const classes_match = /(?<=class=")[^\"\=]*(?=")/.exec(event.detail.data);
    let classes_list = [];
    let match = [];
    if (classes_match != null) {
        classes_list = classes_match[0].split(' ');
        match = classes_list.filter(
            (c) => c.includes("speech-period") || c.includes("utterance-period") || c.includes("no-text"),
        ).pop();
        if (match != null) {
            if (match.includes("speech-period")) {
                const value = match.split('-').pop();
                console.log(`Setting --speech-period = ${value}s`)
                document.documentElement.style.setProperty(
                    "--speech-period",
                    `${value}s`,
                );
                show_tabs();
            } else if (match.includes("utterance-period")) {
                const value = match.split('-').pop();
                console.log(`Setting --utterance-period = ${value}s`)
                document.documentElement.style.setProperty(
                    "--utterance-period",
                    `${value}s`,
                );
                show_tabs();
            } else {
                hide_tabs();
            }
        }
    }

    // Verify whether a transition should be applied
    const swap_spec = event.target.getAttribute("hx-swap");
    if (swap_spec == null) {
        console.log("Target not set for transition.");
        return;
    }
    match = /(?<=transition:)(true|false)/.exec(swap_spec);
    let should_transition = (match != null) && (match[0] === "true");
    if (!should_transition) {
        console.log("Target not set for transition.");
        return;
    }

    /* Default transition */
    if ((event.target.id == null) || !(status_elements.includes(event.target.id))) {
        document.documentElement.style.setProperty(
            "--swap-animation",
            "fade-in",
        );
    } else {
        document.documentElement.style.setProperty(
            "--swap-animation",
            "none",
        );
    }

    // If there is a transition
    if (classes_list != []) {
        match = classes_list.filter(
            (c) => c.includes("fade-in") || c.includes("swipe-in"),
        ).pop();
        if (match != null) {
            console.log(`Setting --swap-animation = ${match}`)
            document.documentElement.style.setProperty(
                "--swap-animation",
                match,
            );
        } else {
            const swap_animation = document.documentElement.style.getPropertyValue("--swap-animation");
            console.log(`--swap-animation = ${swap_animation}`);
            if ((swap_animation != null) && (swap_animation != "") && (swap_animation !== "fade-in")) {
                console.log("Unsetting --swap-animation");
                document.documentElement.style.removeProperty(
                    "--swap-animation",
                );
            }
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


function objectify_node(node) {
    let attributes = [];
    if (node.getAttributeNames) {
        attributes = Array.from(node.getAttributeNames()).filter(
            (attr) => !attr.startsWith("hx-") && !attr.startsWith("sse")
        );
    }
    const node_object = Object.fromEntries(
        attributes.map((attr) => [attr, node.getAttribute(attr)])
    );
    if ("value" in node) {
        node_object["value"] = node.value;
    }
    return node_object;
}


function stringify_event(e) {
    const obj = {};
    for (let k in e) {
      obj[k] = e[k];
    }
    return JSON.stringify(obj, (k, v) => {
        if (v instanceof Node) return objectify_node(v);
        if (v instanceof Window) return 'Window';
        return v;
    }, ' ');
}
