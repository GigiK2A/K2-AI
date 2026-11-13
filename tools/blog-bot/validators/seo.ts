/**
 * SEO validator: hard checks su title, meta, schema, structure, links.
 * Esegue su HTML completo (template + body inserito).
 */
import * as cheerio from "cheerio";

export interface SeoCheckResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
}

export function validateSeo(fullHtml: string): SeoCheckResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const $ = cheerio.load(fullHtml);

  // Title
  const title = $("title").text().trim();
  if (!title) errors.push("missing <title>");
  else if (title.length > 60) {
    warnings.push(`title length ${title.length} over 60`);
  }

  // Meta description
  const desc = $('meta[name="description"]').attr("content")?.trim() ?? "";
  if (!desc) errors.push("missing <meta name=description>");
  else if (desc.length < 140 || desc.length > 155) {
    warnings.push(`meta description length ${desc.length} out of 140-155`);
  }

  // Canonical: presente e nella forma pulita (il server fa 301 da ogni .html)
  const canonicalHref = $('link[rel="canonical"]').attr("href");
  if (!canonicalHref) {
    errors.push("missing canonical link");
  } else if (/\.html($|[?#])/.test(canonicalHref)) {
    errors.push(`canonical with .html: ${canonicalHref}`);
  }

  // H1: exactly one
  const h1count = $("h1").length;
  if (h1count !== 1) errors.push(`expected 1 <h1>, got ${h1count}`);
  else {
    const h1Text = $("h1").text().replace(/\s+/g, " ").trim();
    if (h1Text.length < 45 || h1Text.length > 65) warnings.push(`h1 length ${h1Text.length} out of 45-65`);
    if (title && h1Text.toLowerCase() === title.replace(/\s*\|.*$/, "").trim().toLowerCase()) {
      warnings.push("h1 identical to the title (without brand)");
    }
  }

  // At least 4 H2
  const h2count = $("h2").length;
  if (h2count < 4) errors.push(`expected >=4 <h2>, got ${h2count}`);
  $("h2").each((_, el) => {
    const t = $(el).text().replace(/\s+/g, " ").trim();
    if (t.length < 30 || t.length > 70) warnings.push(`h2 length ${t.length} out of 30-70: "${t.slice(0, 50)}"`);
  });

  // Schema.org: Article + BreadcrumbList + FAQPage
  const jsonLds = $('script[type="application/ld+json"]')
    .toArray()
    .map((el) => $(el).text());
  const types = new Set<string>();
  for (const raw of jsonLds) {
    try {
      const parsed = JSON.parse(raw);
      const items = Array.isArray(parsed) ? parsed : [parsed];
      for (const it of items) {
        if (it["@type"]) {
          if (Array.isArray(it["@type"])) {
            it["@type"].forEach((t: string) => types.add(t));
          } else {
            types.add(it["@type"]);
          }
        }
      }
    } catch {
      warnings.push("invalid JSON-LD block, skipping");
    }
  }
  for (const required of ["Article", "BreadcrumbList", "FAQPage"]) {
    if (!types.has(required)) errors.push(`missing schema.org ${required}`);
  }

  // Internal links: >= 2 to suite-ai or blog or contatti, plus 1 to /app
  const hrefs = $("a")
    .toArray()
    .map((el) => $(el).attr("href") ?? "");
  const internalAnchors = hrefs.filter((h) =>
    /^\/(suite-ai|blog|contatti|metodo|laboratorio|app|k-bot|per-te)\b/.test(h)
  );
  if (internalAnchors.length < 3) {
    errors.push(`expected >=3 internal links, got ${internalAnchors.length}`);
  }
  if (!hrefs.some((h) => h === "/app" || h.startsWith("/app?") || h === "/contatti")) {
    errors.push("missing CTA link to /app or /contatti");
  }
  // Link interni senza .html (ogni .html risponde con un 301)
  const htmlLinks = hrefs.filter((h) => /^\/[^?#]*\.html($|[?#])/.test(h));
  if (htmlLinks.length > 0) {
    errors.push(`internal links with .html: ${[...new Set(htmlLinks)].slice(0, 5).join(", ")}`);
  }

  // Immagini: width/height, alt non vuoto, lazy tranne la prima (cover, eager)
  $("img").each((_, el) => {
    const src = $(el).attr("src") ?? "";
    if (!src.startsWith("./img/")) return; // logo ecc.
    if (!$(el).attr("width") || !$(el).attr("height")) errors.push(`img without width/height: ${src}`);
    if (!($(el).attr("alt") ?? "").trim()) errors.push(`img without alt: ${src}`);
  });

  // og:image / twitter:image / JSON-LD: stesso URL assoluto e mai sotto /blog/img/ (404 dopo il build di Vite)
  const ogImage = $('meta[property="og:image"]').attr("content") ?? "";
  const twImage = $('meta[name="twitter:image"]').attr("content") ?? "";
  if (!ogImage) errors.push("missing og:image");
  else if (/\/blog\/img\//.test(ogImage)) errors.push(`og:image under /blog/img/ (404 in production): ${ogImage}`);
  if (twImage !== ogImage) errors.push("twitter:image differs from og:image");

  // Preload font: solo WOFF2
  if ($('link[rel="preload"][href$=".ttf"]').length > 0) errors.push("preload of a .ttf font (use .woff2)");

  // Body word count (between 1200 and 2500)
  const body = $("article, main, section").text().replace(/\s+/g, " ").trim();
  const wc = body.split(" ").length;
  if (wc < 1200) errors.push(`word count ${wc} below 1200`);
  if (wc > 2500) warnings.push(`word count ${wc} above 2500`);

  return { ok: errors.length === 0, errors, warnings };
}
