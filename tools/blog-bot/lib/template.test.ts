import { test } from "node:test";
import assert from "node:assert/strict";
import * as cheerio from "cheerio";

import { renderArticleHtml, type TemplateInput } from "./template.js";
import { validateSeo } from "../validators/seo.js";

const SECTION = (n: number) =>
  `<section><h2 class="display-sm">Titolo della sezione numero ${n} dell'articolo.</h2><p>${"parola ".repeat(40)}</p></section>`;
const BODY = [1, 2, 3, 4, 5].map(SECTION).join('<hr class="hr-section">');

function sample(over: Partial<TemplateInput> = {}): TemplateInput {
  return {
    meta: {
      title_h1: "Agenti AI per email e CRM nelle PMI: come funzionano",
      title_tag: "Agenti AI email e CRM per PMI | K2-AI",
      meta_description:
        "Un agente AI smista le email, prepara le bozze e aggiorna il CRM. Scopri cosa cambia per una PMI e quando conviene costruirlo su misura davvero.",
      lede: "Il problema.",
      slug: "agenti-ai-prova",
      faq_questions: [
        { q: "Domanda uno?", a: "Risposta uno." },
        { q: "Domanda due?", a: "Risposta due." },
        { q: "Domanda tre?", a: "Risposta tre." },
      ],
      image_alts: {
        cover: "Due colleghi davanti a un portatile in un ufficio",
        inline1: "Portatile con un elenco di email in arrivo",
        inline2: "Monitor con una bacheca di schede in colonne",
      },
    },
    bodyHtml: BODY,
    pillarPadre: "P01",
    pillarUrl: "/suite-ai/agenti-email-crm",
    pillarLabel: "Agenti email & CRM",
    coverUrl: "agenti-ai-prova-cover.webp",
    inline1Url: "agenti-ai-prova-inline-1.webp",
    inline2Url: "agenti-ai-prova-inline-2.webp",
    coverSize: { width: 1280, height: 853 },
    inlineSize: { width: 1024, height: 1024 },
    ogImageFile: "agenti-ai-prova.jpg",
    publishedAtIso: "2026-11-13",
    related: [
      { href: "/suite-ai/agenti-email-crm", kicker: "Pillar", title: "Pacchetto", body: "Corpo." },
    ],
    ...over,
  };
}

test("template: canonical, og:url e JSON-LD senza .html", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  assert.equal($('link[rel="canonical"]').attr("href"), "https://www.k2-ai.it/blog/agenti-ai-prova");
  assert.equal($('meta[property="og:url"]').attr("content"), "https://www.k2-ai.it/blog/agenti-ai-prova");
  for (const el of $('script[type="application/ld+json"]').toArray()) {
    assert.ok(!/\.html/.test($(el).text()), "JSON-LD con .html");
  }
});

test("template: link interni senza .html", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  const bad = $("a").toArray().map((a) => $(a).attr("href") ?? "").filter((h) => /\.html($|[?#])/.test(h));
  assert.deepEqual(bad, []);
});

test("template: og:image, twitter:image e JSON-LD puntano allo stesso JPG in /blog/og/", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  const og = $('meta[property="og:image"]').attr("content");
  assert.equal(og, "https://www.k2-ai.it/blog/og/agenti-ai-prova.jpg");
  assert.equal($('meta[name="twitter:image"]').attr("content"), og);
  assert.equal($('meta[property="og:image:width"]').attr("content"), "1200");
  assert.equal($('meta[property="og:image:height"]').attr("content"), "630");
  const article = JSON.parse($('script[type="application/ld+json"]').first().text());
  assert.equal(article.image, og);
  assert.ok(!/\/blog\/img\//.test(og ?? ""));
});

test("template: senza JPG (ImageMagick assente) ripiega su og-home, un file che esiste", () => {
  const $ = cheerio.load(renderArticleHtml(sample({ ogImageFile: null })));
  assert.equal($('meta[property="og:image"]').attr("content"), "https://www.k2-ai.it/assets/og-home.png");
  assert.equal($('meta[name="twitter:image"]').attr("content"), "https://www.k2-ai.it/assets/og-home.png");
});

test("template: immagini con width/height, alt descrittivo, lazy tranne la cover", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  const imgs = $("img.blog-cover-full").toArray();
  assert.equal(imgs.length, 3);
  const [cover, in1, in2] = imgs.map((i) => $(i)) as [cheerio.Cheerio<any>, cheerio.Cheerio<any>, cheerio.Cheerio<any>];
  assert.equal(cover.attr("src"), "./img/agenti-ai-prova-cover.webp");
  assert.equal(cover.attr("width"), "1280");
  assert.equal(cover.attr("height"), "853");
  assert.equal(cover.attr("loading"), "eager");
  assert.equal(cover.attr("fetchpriority"), "high");
  assert.equal(cover.attr("alt"), "Due colleghi davanti a un portatile in un ufficio");
  for (const im of [in1, in2]) {
    assert.equal(im.attr("loading"), "lazy");
    assert.equal(im.attr("width"), "1024");
    assert.equal(im.attr("height"), "1024");
    assert.ok((im.attr("alt") ?? "").length > 10);
  }
  assert.equal(in1.attr("alt"), "Portatile con un elenco di email in arrivo");
});

test("template: senza image_alts l'alt ripiega sul titolo (mai vuoto)", () => {
  const input = sample();
  input.meta.image_alts = undefined;
  const $ = cheerio.load(renderArticleHtml(input));
  for (const el of $("img.blog-cover-full").toArray()) assert.ok(($(el).attr("alt") ?? "").trim().length > 0);
});

test("template: un solo <main> tra menu e footer", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  assert.equal($("main").length, 1);
  assert.equal($("main").parent().is("body"), true);
  assert.equal($("main").prev().is(".nav-overlay"), true);
  assert.equal($("main").next().is("footer"), true);
  assert.equal($("main h1").length, 1);
});

test("template: preload dei font solo WOFF2", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  const hrefs = $('link[rel="preload"]').toArray().map((l) => $(l).attr("href"));
  assert.ok(hrefs.includes("/fonts/dm-sans-400.woff2"));
  assert.ok(hrefs.every((h) => !h?.endsWith(".ttf")));
});

test("template: CTA con titolo descrittivo (30-70 caratteri)", () => {
  const $ = cheerio.load(renderArticleHtml(sample()));
  const t = $("h2.center-cta-title-sm").text().trim();
  assert.ok(t.length >= 30 && t.length <= 70, t);
});

test("validator SEO: non segnala i difetti corretti sul sito", () => {
  const r = validateSeo(renderArticleHtml(sample()));
  const joined = r.errors.join(" | ");
  for (const re of [/\.html/, /og:image/, /twitter:image/, /width\/height/, /without alt/, /\.ttf/]) {
    assert.ok(!re.test(joined), `errore inatteso ${re}: ${joined}`);
  }
});

test("validator SEO: boccia og:image sotto /blog/img/, link .html e canonical .html", () => {
  let html = renderArticleHtml(sample());
  html = html.replace("https://www.k2-ai.it/blog/og/agenti-ai-prova.jpg", "https://www.k2-ai.it/blog/img/x-cover.png");
  html = html.replace('href="/metodo"', 'href="/metodo.html"');
  html = html.replace('rel="canonical" href="https://www.k2-ai.it/blog/agenti-ai-prova"', 'rel="canonical" href="https://www.k2-ai.it/blog/agenti-ai-prova.html"');
  const joined = validateSeo(html).errors.join(" | ");
  assert.match(joined, /og:image under \/blog\/img\//);
  assert.match(joined, /internal links with \.html/);
  assert.match(joined, /canonical with \.html/);
});
