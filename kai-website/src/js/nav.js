const path = window.location.pathname;

const SUITE_AI_PILLARS = [
  { href: '/suite-ai/agenti-email-crm',                label: 'Agenti email e CRM' },
  { href: '/suite-ai/automazioni-amministrative',       label: 'Automazioni amministrative' },
  { href: '/suite-ai/ai-legale-contratti',             label: 'AI legale e contratti' },
  { href: '/suite-ai/ai-ingegneria-progettazione',     label: 'AI ingegneria e progettazione' },
  { href: '/suite-ai/microapp-documenti-tecnici',      label: 'Microapp documenti tecnici' },
  { href: '/suite-ai/ai-customer-service-ticket',      label: 'AI customer service' },
  { href: '/suite-ai/rag-knowledge-base',              label: 'RAG e knowledge base' },
  { href: '/suite-ai/ai-compliance-audit',             label: 'AI compliance e audit' },
  { href: '/suite-ai/ai-controllo-gestione-reporting', label: 'AI controllo di gestione' },
  { href: '/suite-ai/integrazione-gestionali-erp',     label: 'Integrazione gestionali ERP' },
];

// Active link based on current page
document.querySelectorAll('.nav-links a, .nav-overlay a').forEach(link => {
  const href = link.getAttribute('href');
  const isHome = (href === '/' || href === '/index') && (path === '/' || path === '/index' || path === '');
  const isMatch = href !== '/' && href !== '/index' && path.includes(href.replace('.html', ''));
  if (isHome || isMatch) link.classList.add('active');
});

// Suite AI dropdown — desktop
const navLinks = document.querySelector('.nav-links');
if (navLinks) {
  const suiteItem = [...navLinks.querySelectorAll('li')].find(
    li => li.querySelector('a')?.getAttribute('href') === '/suite-ai'
  );
  if (suiteItem) {
    suiteItem.classList.add('nav-has-dropdown');
    if (path.startsWith('/suite-ai/')) suiteItem.querySelector('a').classList.add('active');
    const menu = document.createElement('ul');
    menu.className = 'nav-dropdown-menu';
    SUITE_AI_PILLARS.forEach(({ href, label }) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = href;
      a.textContent = label;
      if (path === href) a.classList.add('active');
      li.appendChild(a);
      menu.appendChild(li);
    });
    suiteItem.appendChild(menu);
  }
}

// Suite AI submenu — mobile overlay
const overlay = document.querySelector('.nav-overlay');
if (overlay) {
  const suiteLink = overlay.querySelector('a[href="/suite-ai"]');
  if (suiteLink) {
    const sub = document.createElement('div');
    sub.className = 'nav-overlay-submenu';
    SUITE_AI_PILLARS.forEach(({ href, label }) => {
      const a = document.createElement('a');
      a.href = href;
      a.textContent = label;
      if (path === href) a.classList.add('active');
      sub.appendChild(a);
    });
    suiteLink.insertAdjacentElement('afterend', sub);
  }
}

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
