const path = window.location.pathname;

// Active link based on current page
document.querySelectorAll('.nav-links a, .nav-overlay a').forEach(link => {
  const href = link.getAttribute('href');
  const isHome = (href === '/' || href === '/index.html') && (path === '/' || path === '/index.html' || path === '');
  const isMatch = href !== '/' && href !== '/index.html' && path.includes(href.replace('.html', ''));
  if (isHome || isMatch) link.classList.add('active');
});

// Hamburger toggle
const hamburger = document.querySelector('.nav-hamburger');
const overlay = document.querySelector('.nav-overlay');

function openMenu() {
  hamburger?.classList.add('open');
  overlay?.classList.add('open');
  hamburger?.setAttribute('aria-expanded', 'true');
  document.documentElement.classList.add('nav-open');
  document.body.classList.add('nav-open');
}

function closeMenu() {
  hamburger?.classList.remove('open');
  overlay?.classList.remove('open');
  hamburger?.setAttribute('aria-expanded', 'false');
  document.documentElement.classList.remove('nav-open');
  document.body.classList.remove('nav-open');
}

function toggleMenu() {
  if (!overlay || !hamburger) return;
  if (overlay.classList.contains('open')) {
    closeMenu();
    return;
  }
  openMenu();
}

if (hamburger && overlay) {
  hamburger.setAttribute('aria-expanded', 'false');
  hamburger.setAttribute('aria-controls', 'mobile-nav-overlay');
  overlay.id = 'mobile-nav-overlay';

  // Add close button inside overlay
  const closeBtn = document.createElement('button');
  closeBtn.className = 'nav-overlay-close';
  closeBtn.setAttribute('aria-label', 'Chiudi menu');
  closeBtn.textContent = '×';
  overlay.prepend(closeBtn);
  closeBtn.addEventListener('click', closeMenu);

  hamburger.addEventListener('click', toggleMenu);

  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeMenu();
  });

  overlay.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  // Close on Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeMenu();
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) closeMenu();
  });
}
