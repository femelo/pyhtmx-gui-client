/* The following wrapping is considered a best practice to isolate
  the context for variables, especially when the script will be
  loaded/unloaded dynamically, which would lead to variables
  redefinition if left in a global context.
*/
(() => {
    const carouselBg = document.getElementById("carousel-bg");
    const carousel = document.querySelector(".carousel");
    const carouselItems = document.querySelectorAll(".carousel-item");
    const tabs = document.querySelectorAll(".tab");
    const tabsContainer = document.getElementById("tabs-container");
    const fullScreenImage = document.getElementById("full-screen-image");

    let selectedTab = 0;
    const inactivityTimeout = 2000; // ms
    let tabsVisibleTimeout;


    // Helper function to debounce events
    function debounce(func, timeout = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }


    // Function to calculate the dynamic gradient based on scroll position
    function calculateDynamicGradient(scrollRatio) {
        const startColor = [59, 130, 246]; // Blue
        const endColor = [255, 182, 193]; // Light pink
        const r = startColor[0] + (endColor[0] - startColor[0]) * scrollRatio;
        const g = startColor[1] + (endColor[1] - startColor[1]) * scrollRatio;
        const b = startColor[2] + (endColor[2] - startColor[2]) * scrollRatio;
        return `linear-gradient(to right, rgb(${r}, ${g}, ${b}), rgb(255, 182, 193))`;
    }

    // Function to update background gradient
    function updateBackgroundOnScroll() {
        const scrollPosition = carousel.scrollLeft;
        const totalWidth = carousel.scrollWidth - carousel.offsetWidth;
        const scrollRatio = scrollPosition / totalWidth;
        carouselBg.style.background = calculateDynamicGradient(scrollRatio);
    }

    // Function to update the active tabs based on the scroll position
    function updateTabs() {
        const scrollPosition = carousel.scrollLeft;
        const totalWidth = carousel.scrollWidth - carousel.offsetWidth;
        selectedTab = Math.min(
            Math.floor(scrollPosition / (totalWidth / carouselItems.length)),
            tabs.length - 1,
        );
        tabs.forEach((tab, idx) => {
            // Remove the active class from all tabs
            tab.classList.remove('tab-active');
            if (idx === selectedTab) {
                // Add the active class to the tab
                // corresponding to the scroll position
                tab.classList.add('tab-active');
            }
        });
    }

    // Function to show tabs temporarily and adjust fullscreen image
    function showTabs() {
        // Remove the ‘hidden’ classes from the tabs
        tabsContainer.classList.remove("tabs-hidden");
        // Add the ‘tabs-shown’ class to make them visible
        tabsContainer.classList.add("tabs-shown");

        // Make the full-screen image smaller
        fullScreenImage.classList.add("small");
    }

    function hideTabs() {
        tabsContainer.classList.remove("tabs-shown"); // Hide the tabs after 2 seconds
        tabsContainer.classList.add("tabs-hidden");

        // Resize the full-screen image
        fullScreenImage.classList.remove("small");
    }

    // Show tabs on hover over the carousel
    function handleMouseover(event) {
        clearTimeout(tabsVisibleTimeout);
        event.preventDefault();
        showTabs();
        tabsVisibleTimeout = setTimeout(hideTabs, inactivityTimeout);
    }

    function handleMouseout(event) {
        clearTimeout(tabsVisibleTimeout);
        event.preventDefault();
        hideTabs();
    }

    let isScrolling = false;
    
    function handleKeyup(event) {
        clearTimeout(tabsVisibleTimeout);
        event.preventDefault();
    
        if (isScrolling) return; // Prevent a new scroll from starting during an active scroll
    
        let index;
        if (event.code === "ArrowRight") {
            index = Math.min(selectedTab + 1, tabs.length - 1);
        } else if (event.code === "ArrowLeft") {
            index = Math.max(selectedTab - 1, 0);
        }
    
        if (carouselItems[index]) {
            isScrolling = true; // Mark that a scroll is in progress
            const scrollTo = carouselItems[index].offsetLeft;
            carousel.scrollTo({
                left: scrollTo,
                behavior: 'smooth' // Ensure smooth scrolling animation
            });
    
            setTimeout(() => { isScrolling = false; }, 500); // Wait for the animation to finish
            tabsVisibleTimeout = setTimeout(hideTabs, inactivityTimeout);
        }
    }

    const debouncedHandleMouseover = debounce(handleMouseover, 10);
    const debouncedHandleMouseout = debounce(handleMouseout, 10);
    const debouncedHandleKeyup = debounce(handleKeyup, 25);

    document.addEventListener("mouseover", debouncedHandleMouseover);
    document.addEventListener("mouseout", debouncedHandleMouseout);
    document.addEventListener("keyup", debouncedHandleKeyup);

    // Listen for scroll events to update the background, active tab, and show tabs
    carousel.addEventListener("scroll", () => {
        updateBackgroundOnScroll();
        updateTabs();
        showTabs();
    });

    // Click event for tabs to smoothly scroll to the selected carousel item
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', (event) => {
            event.preventDefault();
           // Scroll to the appropriate carousel item based on the tab index
            const scrollTo = carouselItems[index].offsetLeft;
            carousel.scrollTo({
                left: scrollTo,
               // Ensures smooth scrolling animation
                behavior: 'smooth'
            });
        });
    });

    // Initial setup
    updateBackgroundOnScroll();
    updateTabs();
})();
