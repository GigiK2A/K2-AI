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

if (hamburger && overlay) {
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    overlay.classList.toggle('open');
    document.body.classList.toggle('nav-open', overlay.classList.contains('open'));
  });

  overlay.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      overlay.classList.remove('open');
      document.body.classList.remove('nav-open');
    });
  });
}
