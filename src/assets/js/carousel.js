const carouselBg = document.getElementById("carousel-bg");
const carousel = document.querySelector(".carousel");
const carouselItems = document.querySelectorAll(".carousel-item");
const tabs = document.querySelectorAll(".tab");
const tabsContainer = document.getElementById("tabs-container");
const fullScreenImage = document.getElementById("full-screen-image");

let tabsVisibleTimeout;

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
  const index = Math.floor(scrollPosition / (totalWidth / carouselItems.length));

  tabs.forEach((tab, idx) => {
    tab.classList.remove('tab-active'); // Verwijder de actieve klasse van alle tabs
    if (idx === index) {
      tab.classList.add('tab-active'); // Voeg de actieve klasse toe aan de tab die overeenkomt met de scrollpositie
    }
  });
}

// Function to show tabs temporarily and adjust fullscreen image
function showTabs() {
  clearTimeout(tabsVisibleTimeout); // Reset de timeout voor het verbergen van tabs
  tabsContainer.classList.remove("opacity-0", "pointer-events-none"); // Verwijder de 'hidden' klassen van de tabs
  tabsContainer.classList.add("tabs-shown"); // Voeg de 'tabs-shown' klasse toe om ze zichtbaar te maken

  // Maak de full-screen afbeelding kleiner
  fullScreenImage.classList.add("small");

  tabsVisibleTimeout = setTimeout(() => {
    tabsContainer.classList.remove("tabs-shown"); // Verberg de tabs na 2 seconden
    tabsContainer.classList.add("opacity-0", "pointer-events-none");

    // Herstel de grootte van de full-screen afbeelding
    fullScreenImage.classList.remove("small");
  }, 2000); // De tabs verdwijnen na 2 seconden
}

// Show tabs on hover over the carousel
carousel.addEventListener("mouseover", () => {
  showTabs();
});

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
    const scrollTo = carouselItems[index].offsetLeft; // Scroll naar de juiste carousel item op basis van de tab index
    carousel.scrollTo({
      left: scrollTo,
      behavior: 'smooth' // Zorgt voor een soepele scrollanimatie
    });
  });
});

// Initial setup
updateBackgroundOnScroll();
updateTabs();
