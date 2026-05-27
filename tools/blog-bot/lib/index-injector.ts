/**
 * Inietta una card articolo dentro `kai-website/src/blog/index.html`,
 * nel blocco delimitato dai sentinel BLOG_INDEX_AUTO_BEGIN / END.
 *
 * Idempotente: se esiste già una card con lo stesso data-slug, viene
 * aggiornata invece di duplicata. Nuove card vanno in cima (newest first).
 */
import { readFileSync, writeFileSync } from "node:fs";

export interface IndexCardInput {
  slug: string;            // es. "agenti-ai-email-crm-pmi"
  title: string;           // H1 articolo
  description: string;     // 1 frase, usata come case-card-desc
  category: string;        // es. "Email & CRM" (row.categoria)
  publishedAtIso: string;  // YYYY-MM-DD
}

const BEGIN = "<!-- BLOG_INDEX_AUTO_BEGIN";
const END = "<!-- BLOG_INDEX_AUTO_END";

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
  const parts = iso.split("-").map((n) => parseInt(n, 10));
  const [y, m, d] = parts as [number, number, number];
  return `${d} ${months[m - 1]} ${y}`;
}

function dataSectorFromCategory(category: string): string {
  return category
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function buildCard(input: IndexCardInput): string {
  const sector = dataSectorFromCategory(input.category);
  const date = formatItalianDate(input.publishedAtIso);
  return [
    `      <article class="case-card reveal" data-sector="${escapeHtml(sector)}" data-slug="${escapeHtml(input.slug)}">`,
    `        <div class="case-card-header">`,
    `          <div class="case-card-sector">${escapeHtml(input.category)} · ${escapeHtml(date)}</div>`,
    `          <h3 class="case-card-title">${escapeHtml(input.title)}</h3>`,
    `          <p class="case-card-desc">${escapeHtml(input.description)}</p>`,
    `          <a href="/blog/${escapeHtml(input.slug)}" class="case-card-cta">Leggi l'articolo →</a>`,
    `        </div>`,
    `      </article>`,
  ].join("\n");
}

export function injectIndexCard(indexPath: string, input: IndexCardInput): void {
  const html = readFileSync(indexPath, "utf-8");

  const beginIdx = html.indexOf(BEGIN);
  const endIdx = html.indexOf(END);
  if (beginIdx === -1 || endIdx === -1 || endIdx < beginIdx) {
    throw new Error(
      `index.html missing BLOG_INDEX_AUTO sentinels (${indexPath})`
    );
  }

  // Estendi a fine riga
  const beginLineEnd = html.indexOf("\n", beginIdx);
  const endLineStart = html.lastIndexOf("\n", endIdx);
  const before = html.slice(0, beginLineEnd + 1);
  const after = html.slice(endLineStart);
  const inner = html.slice(beginLineEnd + 1, endLineStart);

  // Split cards: ogni <article ...>...</article> a top-level
  const cardRegex = /<article\b[\s\S]*?<\/article>/g;
  const existing = inner.match(cardRegex) ?? [];

  // Filtra eventuale duplicato per slug
  const dedup = existing.filter(
    (c) => !c.includes(`data-slug="${input.slug}"`)
  );

  const newCard = buildCard(input);
  // Re-applica indent 6 spazi davanti a ogni card esistente (regex spogliata
  // dal trim della cattura iniziale).
  const reIndented = dedup.map((c) => (c.startsWith("      ") ? c : `      ${c}`));
  const merged = [newCard, ...reIndented].join("\n");

  const next = `${before}${merged}\n    ${after}`;
  writeFileSync(indexPath, next, "utf-8");
}
