/**
 * Inietta una nuova <url> nella sitemap.xml prima del blocco </urlset>.
 * Idempotente: se l'URL c'è già, non fa nulla.
 */
import { readFileSync, writeFileSync } from "node:fs";

export function injectSitemapEntry(
  sitemapPath: string,
  slug: string,
  lastmodIso: string
): boolean {
  const xml = readFileSync(sitemapPath, "utf-8");
  const loc = `https://www.k2-ai.it/blog/${slug}`;
  if (xml.includes(`<loc>${loc}</loc>`)) return false;

  const entry = `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmodIso}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
`;
  const updated = xml.replace("</urlset>", `${entry}</urlset>`);
  writeFileSync(sitemapPath, updated, "utf-8");
  return true;
}
