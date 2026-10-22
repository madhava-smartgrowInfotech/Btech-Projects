// FinSight AI — minimal frontend helpers.
document.addEventListener("DOMContentLoaded", () => {
  // Highlight active nav link
  const path = window.location.pathname;
  document.querySelectorAll(".nav a").forEach((a) => {
    if (a.getAttribute("href") === path) {
      a.style.color = "#2563eb";
    }
  });
});
