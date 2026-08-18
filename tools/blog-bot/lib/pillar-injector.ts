/**
 * Sincronizza le sezioni "Dal blog" nelle pagine pillar (kai-website/src/suite-ai/*.html)
 * a partire dagli articoli presenti in kai-website/src/blog/.
 *
 * Perché esiste: la regola SEO del progetto richiede che ogni pillar linki i
 * propri articoli cluster (link bidirezionale pillar ↔ articolo). Gli articoli
 * linkano già il pillar padre; questo modulo chiude il cerchio dal lato pillar.
 *
 * Ogni articolo dichiara il pillar di appartenenza nel commento di testa:
 *   <!-- pillar: P01 | slug: agenti-ai-email-crm-pmi -->
 *
 * La sezione viene (ri)generata dentro i sentinel PILLAR_BLOG_AUTO_BEGIN/END.
 * Se i sentinel non esistono ancora, la sezione viene inserita prima della
 * CTA finale (section.section-center). Idempotente: rieseguire senza nuovi
 * articoli non produce diff.
 */
import { readdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

import { URL_TO_PILLAR } from "./pillar.js";

export interface PillarArticleRef {
  slug: string;
  pillarCode: string;
  title: string;
  description: string;
  publishedAtIso: string;
}

const BEGIN = "<!-- PILLAR_BLOG_AUTO_BEGIN";
const END = "<!-- PILLAR_BLOG_AUTO_END";
const BEGIN_LINE = `  <!-- PILLAR_BLOG_AUTO_BEGIN — sezione generata da tools/blog-bot, non modificare a mano -->`;
const END_LINE = `  <!-- PILLAR_BLOG_AUTO_END -->`;

// Max card per pillar: 6 cluster per pillar da piano editoriale.
const MAX_CARDS = 6;

function unescapeHtml(s: string): string {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatItalianDate(iso: string): string {
  const months = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
  ];
  const [y, m, d] = iso.split("-").map((n) => parseInt(n, 10)) as [
    number | undefined,
    number | undefined,
    number | undefined,
  ];
  // Data non conforme a YYYY-MM-DD: restituiamo l'ISO grezzo invece di
  // produrre "undefined undefined NaN" dentro una pagina pubblicata.
  const mese = m !== undefined ? months[m - 1] : undefined;
  if (y === undefined || d === undefined || mese === undefined) return iso;
  return `${d} ${mese} ${y}`;
}

/** Path della pagina pillar per codice (es. "P01" → "/suite-ai/agenti-email-crm.html"). */
function pillarPathsByCode(): Map<string, string> {
  const map = new Map<string, string>();
  for (const [path, info] of Object.entries(URL_TO_PILLAR)) {
    if (!path.startsWith("/suite-ai/")) continue;
    // Primo path vince: gli alias deprecati sono elencati dopo il canonico.
    if (!map.has(info.code)) map.set(info.code, path);
  }
  return map;
}

/** Estrae i metadati SEO-rilevanti da un file articolo. Ritorna null se non è un articolo del bot. */
export function parseArticle(html: string): PillarArticleRef | null {
  const header = html.match(/<!--\s*pillar:\s*(\S+)\s*\|\s*slug:\s*(\S+)\s*-->/);
  if (!header?.[1] || !header[2]) return null;

  const ogTitle = html.match(/<meta property="og:title" content="([^"]*)"/);
  const titleTag = html.match(/<title>([^<]*)<\/title>/);
  const rawTitle = ogTitle?.[1] ?? titleTag?.[1]?.replace(/\s*\|\s*K2-AI\s*$/, "") ?? "";
  const description = html.match(/<meta name="description" content="([^"]*)"/)?.[1] ?? "";
  const published = html.match(/"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"/)?.[1] ?? "1970-01-01";

  if (!rawTitle) return null;
  return {
    pillarCode: header[1],
    slug: header[2],
    title: unescapeHtml(rawTitle),
    description: unescapeHtml(description),
    publishedAtIso: published,
  };
}

/** Legge tutti gli articoli del blog raggruppati per codice pillar (newest first). */
export function collectArticlesByPillar(blogDir: string): Map<string, PillarArticleRef[]> {
  const byPillar = new Map<string, PillarArticleRef[]>();
  for (const fileName of readdirSync(blogDir)) {
    if (!fileName.endsWith(".html")) continue;
    if (fileName === "index.html") continue;
    if (fileName.startsWith("._") || fileName.startsWith("_")) continue;
    const article = parseArticle(readFileSync(join(blogDir, fileName), "utf-8"));
    if (!article) continue;
    const list = byPillar.get(article.pillarCode) ?? [];
    list.push(article);
    byPillar.set(article.pillarCode, list);
  }
  for (const list of byPillar.values()) {
    list.sort((a, b) => b.publishedAtIso.localeCompare(a.publishedAtIso));
  }
  return byPillar;
}

function buildSection(articles: PillarArticleRef[]): string {
  const cards = articles
    .slice(0, MAX_CARDS)
    .map(
      (a, i) => `      <a class="card reveal${i > 0 ? ` reveal-delay-${Math.min(i, 3)}` : ""}" href="/blog/${escapeHtml(a.slug)}" style="text-decoration:none;color:inherit;display:block;">
        <div class="card-number">${escapeHtml(formatItalianDate(a.publishedAtIso))}</div>
        <div class="card-title card-title-18">${escapeHtml(a.title)}</div>
        <p class="card-body">${escapeHtml(a.description)}</p>
      </a>`
    )
    .join("\n");

  return `  <hr class="hr-section">

  <section>
    <div class="section-label reveal"><span>Dal blog</span></div>
    <div class="grid-3">
${cards}
    </div>
  </section>
`;
}

/**
 * Inietta/aggiorna la sezione "Dal blog" in una pagina pillar.
 * Ritorna il nuovo HTML, o null se la pagina non è cambiata.
 */
export function injectPillarSection(html: string, articles: PillarArticleRef[]): string | null {
  const block = `${BEGIN_LINE}\n${buildSection(articles)}${END_LINE}`;

  const beginIdx = html.indexOf(BEGIN);
  const endIdx = html.indexOf(END);

  let next: string;
  if (beginIdx !== -1 && endIdx !== -1 && endIdx > beginIdx) {
    const beginLineStart = html.lastIndexOf("\n", beginIdx) + 1;
    const endLineEnd = html.indexOf("\n", endIdx);
    const endBoundary = endLineEnd === -1 ? html.length : html.indexOf("-->", endIdx) + 3;
    next = html.slice(0, beginLineStart) + block + html.slice(endBoundary);
  } else {
    // Primo inserimento: prima della CTA finale (hr + section.section-center),
    // fallback prima del footer.
    const ctaMarker = html.lastIndexOf('<section class="section-center">');
    if (ctaMarker !== -1) {
      // Includi l'<hr> che precede la CTA, se presente, così la sezione
      // "Dal blog" resta separata da FAQ e CTA da un hr ciascuna.
      const hrBefore = html.lastIndexOf('<hr class="hr-section">', ctaMarker);
      const insertAt = hrBefore !== -1
        ? html.lastIndexOf("\n", hrBefore) + 1
        : html.lastIndexOf("\n", ctaMarker) + 1;
      next = html.slice(0, insertAt) + block + "\n" + html.slice(insertAt);
    } else {
      const footerIdx = html.lastIndexOf("<footer>");
      if (footerIdx === -1) return null;
      const insertAt = html.lastIndexOf("\n", footerIdx) + 1;
      next = html.slice(0, insertAt) + block + "\n" + html.slice(insertAt);
    }
  }

  return next === html ? null : next;
}

/**
 * Sincronizza tutte le pagine pillar con gli articoli presenti nel blog.
 * Ritorna i nomi file (relativi a suiteDir) effettivamente modificati.
 */
export function syncPillarBlogSections(blogDir: string, suiteDir: string): string[] {
  const byPillar = collectArticlesByPillar(blogDir);
  const paths = pillarPathsByCode();
  const modified: string[] = [];

  for (const [code, articles] of byPillar) {
    const pillarPath = paths.get(code);
    if (!pillarPath) continue; // LAB, P00 e codici senza pagina suite-ai
    const fileName = pillarPath.replace("/suite-ai/", "");
    const filePath = join(suiteDir, fileName);
    if (!existsSync(filePath)) continue;

    const html = readFileSync(filePath, "utf-8");
    const next = injectPillarSection(html, articles);
    if (next) {
      writeFileSync(filePath, next, "utf-8");
      modified.push(fileName);
    }
  }

  return modified;
}
