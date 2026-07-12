/**
 * Inietta il body articolo + meta dentro il template HTML K2-AI.
 * Il template è strutturalmente identico a una pillar page (page-header,
 * hr-section, section, ecc.) — vedi kai-website/src/blog/<articolo>.html
 * per riferimento.
 */
import type { ArticlePieces } from "./claude.js";

export interface RelatedLink {
  href: string;
  kicker: string;
  title: string;
  body: string;
}

export interface TemplateInput {
  meta: ArticlePieces["meta"];
  bodyHtml: string;            // le 5 sezioni 01-05 + FAQ generate da Claude
  pillarPadre: string;         // es. "P01"
  pillarUrl: string;           // es. "/suite-ai/agenti-email-crm" (canonico, senza .html)
  pillarLabel: string;         // es. "Agenti email & CRM"
  coverUrl?: string;           // path immagine cover (es. "slug-cover.png")
  inline1Url?: string;         // path immagine inline tra sezione 02 e 03
  inline2Url?: string;         // path immagine inline tra sezione 04 e 05
  publishedAtIso: string;      // YYYY-MM-DD
  related: RelatedLink[];      // 3 card "continua a leggere"
}

function injectInlineImages(
  bodyHtml: string,
  meta: ArticlePieces["meta"],
  inline1?: string,
  inline2?: string
): string {
  if (!inline1 && !inline2) return bodyHtml;
  const HR = '<hr class="hr-section">';
  const parts = bodyHtml.split(HR);
  // Body atteso: 5 sezioni 01-05 + FAQ con hr in mezzo. Split tipico produce
  // 5 o 6 parti (FAQ può essere separato da hr o no). Vogliamo:
  // - immagine PRIMA di parts[2] (tra sezione 02 e 03)
  // - immagine PRIMA di parts[4] (tra sezione 04 e 05)
  // Serve almeno 5 parti per avere indici 2 e 4 validi.
  if (parts.length < 5) return bodyHtml;

  const imgBlock = (src: string, alt: string) =>
    `\n  <section>\n    <img class="blog-cover-full reveal" src="./img/${src}" alt="${alt}" loading="lazy">\n  </section>\n`;

  const out: string[] = [];
  for (let i = 0; i < parts.length; i++) {
    if (i > 0) out.push(HR);
    if (i === 2 && inline1) out.push(imgBlock(inline1, `${meta.title_h1} — dettaglio del problema`));
    if (i === 4 && inline2) out.push(imgBlock(inline2, `${meta.title_h1} — dettaglio della soluzione`));
    out.push(parts[i] ?? "");
  }
  return out.join("");
}

export function renderArticleHtml(input: TemplateInput): string {
  const {
    meta,
    bodyHtml: rawBodyHtml,
    pillarPadre,
    pillarUrl,
    pillarLabel,
    coverUrl,
    inline1Url,
    inline2Url,
    publishedAtIso,
    related,
  } = input;

  const bodyHtml = injectInlineImages(rawBodyHtml, meta, inline1Url, inline2Url);

  const canonical = `https://www.k2-ai.it/blog/${meta.slug}`;
  const ogImage = coverUrl
    ? `https://www.k2-ai.it/blog/img/${coverUrl}`
    : "https://www.k2-ai.it/assets/og-home.png";

  const articleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: meta.title_h1,
    description: meta.meta_description,
    datePublished: publishedAtIso,
    dateModified: publishedAtIso,
    author: { "@type": "Organization", name: "K2-AI", url: "https://www.k2-ai.it/" },
    publisher: {
      "@type": "Organization",
      name: "K2-AI",
      logo: { "@type": "ImageObject", url: "https://www.k2-ai.it/logo-nav.png" },
    },
    mainEntityOfPage: { "@type": "WebPage", "@id": canonical },
    image: ogImage,
  };

  const breadcrumb = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://www.k2-ai.it/" },
      { "@type": "ListItem", position: 2, name: "Blog", item: "https://www.k2-ai.it/blog" },
      { "@type": "ListItem", position: 3, name: meta.title_h1, item: canonical },
    ],
  };

  const faq = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: meta.faq_questions.map((q) => ({
      "@type": "Question",
      name: q.q,
      acceptedAnswer: { "@type": "Answer", text: q.a },
    })),
  };

  const formattedDate = new Date(publishedAtIso).toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const coverSection = coverUrl
    ? `
  <section>
    <img class="blog-cover-full reveal" src="./img/${coverUrl}" alt="${escapeAttr(meta.title_h1)}" loading="eager">
  </section>

  <hr class="hr-section">
`
    : "";

  const relatedCards = related
    .map(
      (r, i) => `
      <a class="card reveal ${i > 0 ? `reveal-delay-${i}` : ""}" href="${r.href}" style="text-decoration:none;color:inherit;display:block;">
        <div class="card-number">${escapeHtml(r.kicker)}</div>
        <div class="card-title card-title-18">${escapeHtml(r.title)}</div>
        <p class="card-body">${escapeHtml(r.body)}</p>
      </a>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<!-- pillar: ${pillarPadre} | slug: ${meta.slug} -->
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>${escapeHtml(meta.title_tag)}</title>
  <meta name="description" content="${escapeAttr(meta.meta_description)}">
  <!-- nosemgrep: html.security.audit.missing-integrity.missing-integrity -- canonical link is metadata, not a loaded resource; SRI does not apply -->
  <link rel="canonical" href="${canonical}">
  <link rel="icon" type="image/png" href="/favicon.png">
  <link rel="preload" href="/fonts/clash-display-700.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/fonts/dm-sans-400.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="apple-touch-icon" href="/favicon.png">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="K2-AI">
  <meta property="og:locale" content="it_IT">
  <meta property="og:title" content="${escapeAttr(meta.title_h1)}">
  <meta property="og:description" content="${escapeAttr(meta.meta_description)}">
  <meta property="og:url" content="${canonical}">
  <meta property="og:image" content="${ogImage}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="../css/base.css">
  <link rel="stylesheet" href="../css/nav.css">
  <link rel="stylesheet" href="../css/components.css">
  <link rel="stylesheet" href="../css/pages.css">
  <link rel="stylesheet" href="../css/k2-immersive.css">
  <link rel="stylesheet" href="../css/blog.css">
  <script type="application/ld+json">${JSON.stringify(articleSchema)}</script>
  <script type="application/ld+json">${JSON.stringify(breadcrumb)}</script>
  <script type="application/ld+json">${JSON.stringify(faq)}</script>
</head>
<body class="cases-page">

  <nav id="navbar">
    <div class="nav-inner">
      <a href="/" class="nav-logo" aria-label="K2-AI">
        <img src="../logo-nav-compact.png?v=20260429" width="220" height="113" alt="K2-AI">
      </a>
      <ul class="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="/metodo.html">Metodo</a></li>
        <li><a href="/laboratorio.html">Laboratorio</a></li>
        <li><a href="/k-bot">K-BOT</a></li>
        <li><a href="/per-te">Per te</a></li>
        <li><a href="/suite-ai.html">Suite AI</a></li>
        <li><a href="/blog">Blog</a></li>
        <li><a href="/contatti.html">Contatti</a></li>
      </ul>
      <a href="/app" class="nav-cta">Apri K-BOT →</a>
      <button class="nav-hamburger" aria-label="Menu">
        <span></span><span></span>
      </button>
    </div>
  </nav>

  <div class="nav-overlay">
    <a href="/">Home</a>
    <a href="/metodo.html">Metodo</a>
    <a href="/laboratorio.html">Laboratorio</a>
    <a href="/k-bot">K-BOT</a>
    <a href="/per-te">Per te</a>
    <a href="/suite-ai.html">Suite AI</a>
    <a href="/blog">Blog</a>
    <a href="/contatti.html">Contatti</a>
  </div>

  <section class="page-header">
    <p class="hero-eyebrow reveal">Blog · ${escapeHtml(pillarLabel)}</p>
    <h1 class="display-xl reveal reveal-delay-1">${escapeHtml(meta.title_h1)}</h1>
    <p class="reveal reveal-delay-2 page-copy-16">
      ${escapeHtml(meta.lede)}
    </p>
    <p class="blog-meta reveal reveal-delay-3" style="margin-top:32px;">
      <span>${formattedDate}</span>
      <span class="dot"></span>
      <span>7 min lettura</span>
      <span class="dot"></span>
      <span><a href="${pillarUrl}">${escapeHtml(pillarPadre)}</a></span>
    </p>
  </section>

  <hr class="hr-section">
${coverSection}
${bodyHtml}

  <hr class="hr-section">

  <section class="section-center">
    <p class="mono reveal center-cta-label">Prossimo passo</p>
    <h2 class="display-md reveal reveal-delay-1 center-cta-title-sm">Vuoi capire il tuo caso?</h2>
    <p class="reveal reveal-delay-2 center-cta-copy">
      Apri K-BOT e in 5 minuti ti diciamo se questa categoria di soluzione fa al caso della tua PMI, oppure se basta uno strumento off-the-shelf. Gratuito.
    </p>
    <div class="reveal reveal-delay-3">
      <a href="/app" class="btn btn-primary">Apri K-BOT →</a>
    </div>
  </section>

  <hr class="hr-section">

  <section>
    <div class="section-label reveal"><span>Continua a leggere</span></div>
    <div class="grid-3">
${relatedCards}
    </div>
  </section>

  <footer>
    <div class="footer-inner footer-inner-legal">
      <span class="footer-logo"><img src="../logo-nav-compact.png?v=20260429" width="220" height="113" alt="K2-AI" loading="lazy"></span>
      <ul class="footer-links">
        <li><a href="/metodo.html">Metodo</a></li>
        <li><a href="/laboratorio.html">Laboratorio</a></li>
        <li><a href="/k-bot">K-BOT</a></li>
        <li><a href="/per-te">Per te</a></li>
        <li><a href="/suite-ai.html">Suite AI</a></li>
        <li><a href="/blog">Blog</a></li>
        <li><a href="/contatti.html">Contatti</a></li>
      </ul>
      <ul class="footer-legal-links">
        <li><a href="/privacy.html">Privacy</a></li>
        <li><a href="/cookie.html">Cookie</a></li>
        <li><a href="/note-legali.html">Note legali</a></li>
      </ul>
      <span class="footer-copy">© 2026 K2-AI</span>
    </div>
  </footer>

  <script type="module" src="../js/scroll.js"></script>
  <script type="module" src="../js/k2-immersive.js"></script>
  <script type="module" src="../js/nav.js"></script>
  <script type="module" src="../js/analytics.js"></script>
</body>
</html>
`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
function escapeAttr(s: string): string {
  return escapeHtml(s);
}
