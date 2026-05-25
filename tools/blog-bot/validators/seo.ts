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
  else if (title.length < 40 || title.length > 70) {
    warnings.push(`title length ${title.length} out of 40-70 range`);
  }

  // Meta description
  const desc = $('meta[name="description"]').attr("content")?.trim() ?? "";
  if (!desc) errors.push("missing <meta name=description>");
  else if (desc.length < 130 || desc.length > 160) {
    warnings.push(`meta description length ${desc.length} out of 130-160`);
  }

  // Canonical
  if (!$('link[rel="canonical"]').attr("href")) {
    errors.push("missing canonical link");
  }

  // H1: exactly one
  const h1count = $("h1").length;
  if (h1count !== 1) errors.push(`expected 1 <h1>, got ${h1count}`);

  // At least 4 H2
  const h2count = $("h2").length;
  if (h2count < 4) errors.push(`expected >=4 <h2>, got ${h2count}`);

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
  if (!hrefs.some((h) => h === "/app" || h.startsWith("/app?") || h === "/contatti.html")) {
    errors.push("missing CTA link to /app or /contatti.html");
  }

  // Body word count (between 1200 and 2500)
  const body = $("article, main, section").text().replace(/\s+/g, " ").trim();
  const wc = body.split(" ").length;
  if (wc < 1200) errors.push(`word count ${wc} below 1200`);
  if (wc > 2500) warnings.push(`word count ${wc} above 2500`);

  return { ok: errors.length === 0, errors, warnings };
}
