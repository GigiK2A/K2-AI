document.documentElement.classList.add('js-scroll');
const revealEls = document.querySelectorAll('.reveal');

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.05, rootMargin: '0px 0px 0px 0px' });

  revealEls.forEach(el => observer.observe(el));
} else {
  revealEls.forEach(el => el.classList.add('visible'));
}

// Rete di sicurezza: dopo 2,5 s rende visibili solo gli elementi già nella
// finestra (o senza dimensioni, es. dentro contenitori nascosti) che
// l'observer non ha segnato. Quelli più in basso restano osservati e
// compaiono quando ci si arriva con lo scroll.
setTimeout(() => {
  const limit = window.innerHeight * 1.1;
  revealEls.forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.height === 0 || r.top < limit) el.classList.add('visible');
  });
}, 2500);

const root = document.documentElement;
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
let scrollFrame = null;

function updateNeuralNetworkMotion() {
  scrollFrame = null;

  if (reducedMotionQuery.matches) {
    root.style.setProperty('--neural-shift-y', '0px');
    root.style.setProperty('--neural-shift-y-slow', '0px');
    root.style.setProperty('--neural-scale', '1');
    return;
  }

  const scrollY = window.scrollY || window.pageYOffset || 0;
  const shiftY = Math.min(scrollY * 0.11, 420);
  const shiftYSlow = Math.min(scrollY * 0.055, 220);
  const scale = 1 + Math.min(scrollY, 2200) * 0.00003;

  root.style.setProperty('--neural-shift-y', `${shiftY.toFixed(2)}px`);
  root.style.setProperty('--neural-shift-y-slow', `${shiftYSlow.toFixed(2)}px`);
  root.style.setProperty('--neural-scale', scale.toFixed(4));
}

function requestNeuralUpdate() {
  if (scrollFrame !== null) return;
  scrollFrame = window.requestAnimationFrame(updateNeuralNetworkMotion);
}

window.addEventListener('scroll', requestNeuralUpdate, { passive: true });
window.addEventListener('resize', requestNeuralUpdate, { passive: true });
if (typeof reducedMotionQuery.addEventListener === 'function') {
  reducedMotionQuery.addEventListener('change', requestNeuralUpdate);
} else if (typeof reducedMotionQuery.addListener === 'function') {
  reducedMotionQuery.addListener(requestNeuralUpdate);
}
requestNeuralUpdate();
