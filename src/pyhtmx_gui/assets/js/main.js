
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

// Function to set animation before swapping the element in
function set_animation(event) {
    // Get the classes of the element
    const classes_match = /(?<=class=")[^\"\=]*(?=")/.exec(event.detail.data);
    let classes_list = [];
    let match = [];
    if (classes_match != null) {
        classes_list = classes_match[0].split(' ');
        match = classes_list.filter(
            (c) => c.includes("speech-period") || c.includes("utterance-period"),
        ).pop();
        if (match != null) {
            if (match.includes("speech-period")) {
                const value = match.split('-').pop();
                console.log(`Setting --speech-period = ${value}s`)
                document.documentElement.style.setProperty(
                    "--speech-period",
                    `${value}s`,
                );
            } else {
                const value = match.split('-').pop();
                console.log(`Setting --utterance-period = ${value}s`)
                document.documentElement.style.setProperty(
                    "--utterance-period",
                    `${value}s`,
                );
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
    const attributes = Array.from(node.getAttributeNames()).filter(
        (attr) => !attr.startsWith("hx-") && !attr.startsWith("sse")
    );
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
