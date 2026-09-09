const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
document.querySelector("#year").textContent = new Date().getFullYear();

const showcase = document.querySelector(".hero-showcase");
if (showcase && window.matchMedia("(pointer: fine)").matches) {
  window.addEventListener("pointermove", (event) => {
    const x = (event.clientX / window.innerWidth - 0.5) * 5;
    const y = (event.clientY / window.innerHeight - 0.5) * 5;
    showcase.style.setProperty("--shift-x", `${x}px`);
    showcase.style.setProperty("--shift-y", `${y}px`);
  });
}
