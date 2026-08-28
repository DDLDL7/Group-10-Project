// Small, dependency-free UI-liveliness touches for ClinicCare-Lite.
// Nothing here changes what data is shown, only how it animates in --
// if JS fails to load, every page still shows the correct final values
// (rendered server-side by Jinja) with no animation, which is fine.

document.addEventListener('DOMContentLoaded', () => {
  // Count up any element with data-countup="<final number>" from 0.
  document.querySelectorAll('[data-countup]').forEach((el) => {
    const target = parseFloat(el.dataset.countup);
    if (Number.isNaN(target)) return;

    const duration = 800;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      el.textContent = Math.round(target * eased);
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = target;
      }
    }
    requestAnimationFrame(tick);
  });

  // Stagger card entrances slightly so a row of stat cards doesn't all
  // pop in at once.
  document.querySelectorAll('.row.g-3 > div, .row.g-2 > div').forEach((el, i) => {
    el.style.animationDelay = `${Math.min(i * 40, 240)}ms`;
  });

  // Auto-scroll chat/message panels to the latest message.
  document.querySelectorAll('.chat-scroll').forEach((panel) => {
    panel.scrollTop = panel.scrollHeight;
  });
});
