import test from "node:test";
import assert from "node:assert/strict";

import { parseArticle, injectPillarSection, type PillarArticleRef } from "./pillar-injector.js";

const ARTICLE_HTML = `<!DOCTYPE html>
<!-- pillar: P01 | slug: agenti-ai-email-crm-pmi -->
<html lang="it">
<head>
  <title>Agenti AI Email &amp; CRM per PMI | K2-AI</title>
  <meta name="description" content="Il commerciale perde ore a smistare email.">
  <meta property="og:title" content="Agenti AI Email &amp; CRM per PMI">
  <script type="application/ld+json">{"@type":"Article","datePublished":"2026-05-27"}</script>
</head>
<body></body>
</html>`;

const PILLAR_HTML = `<!DOCTYPE html>
<html lang="it">
<body>
  <section>
    <div class="section-label reveal"><span>FAQ</span></div>
  </section>

  <hr class="hr-section">

  <section class="section-center">
    <a href="/contatti.html?pkg=P01" class="btn btn-primary">Richiedi una proposta →</a>
  </section>

  <footer>
  </footer>
</body>
</html>`;

const REFS: PillarArticleRef[] = [
  {
    slug: "articolo-vecchio",
    pillarCode: "P01",
    title: "Articolo vecchio",
    description: "Descrizione vecchia.",
    publishedAtIso: "2026-05-27",
  },
  {
    slug: "articolo-nuovo",
    pillarCode: "P01",
    title: "Articolo nuovo & bello",
    description: "Descrizione nuova.",
    publishedAtIso: "2026-06-10",
  },
];

test("parseArticle: estrae pillar, slug, titolo (unescaped), descrizione e data", () => {
  const a = parseArticle(ARTICLE_HTML);
  assert.ok(a);
  assert.equal(a.pillarCode, "P01");
  assert.equal(a.slug, "agenti-ai-email-crm-pmi");
  assert.equal(a.title, "Agenti AI Email & CRM per PMI");
  assert.equal(a.description, "Il commerciale perde ore a smistare email.");
  assert.equal(a.publishedAtIso, "2026-05-27");
});

test("parseArticle: html senza commento pillar → null", () => {
  assert.equal(parseArticle("<html><head><title>x</title></head></html>"), null);
});

test("injectPillarSection: primo inserimento prima della CTA finale", () => {
  const next = injectPillarSection(PILLAR_HTML, REFS);
  assert.ok(next);
  assert.ok(next.includes("PILLAR_BLOG_AUTO_BEGIN"));
  assert.ok(next.includes('href="/blog/articolo-vecchio"'));
  assert.ok(next.includes("Articolo nuovo &amp; bello"));
  // La sezione deve stare PRIMA della CTA
  assert.ok(next.indexOf("PILLAR_BLOG_AUTO_END") < next.indexOf('section-center'));
});

test("injectPillarSection: idempotente — seconda iniezione identica non produce diff", () => {
  const first = injectPillarSection(PILLAR_HTML, REFS)!;
  assert.equal(injectPillarSection(first, REFS), null);
});

test("injectPillarSection: articolo aggiunto rimpiazza il blocco tra i sentinel", () => {
  const first = injectPillarSection(PILLAR_HTML, REFS)!;
  const more = [
    ...REFS,
    {
      slug: "terzo-articolo",
      pillarCode: "P01",
      title: "Terzo articolo",
      description: "Desc.",
      publishedAtIso: "2026-07-01",
    },
  ];
  const second = injectPillarSection(first, more)!;
  assert.ok(second.includes('href="/blog/terzo-articolo"'));
  // un solo blocco sentinel
  assert.equal(second.split("PILLAR_BLOG_AUTO_BEGIN").length, 2);
  assert.equal(second.split("PILLAR_BLOG_AUTO_END").length, 2);
});
