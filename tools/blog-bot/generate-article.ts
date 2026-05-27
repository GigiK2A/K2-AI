/**
 * Orchestrator: pesca riga sheet → genera articolo Claude → valida → pubblica.
 *
 * Esecuzione:
 *   tsx generate-article.ts            (genera + valida + pubblica)
 *   tsx generate-article.ts --dry-run  (genera + valida, NON pubblica)
 *
 * Env vars richieste:
 *   - ANTHROPIC_API_KEY
 *   - GOOGLE_SHEETS_CREDENTIALS (JSON service account)
 *   - GOOGLE_SHEET_ID
 *   - TELEGRAM_BOT_TOKEN (opzionale ma raccomandato)
 *   - TELEGRAM_CHAT_ID (opzionale)
 */
import { writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { SheetClient, type SheetRow } from "./lib/sheet-client.js";

// Mapping URL → codice pillar (per metadata + section-label).
// Le righe "Laboratorio" puntano a /laboratorio invece di un pillar.
const URL_TO_PILLAR: Record<string, { code: string; label: string }> = {
  "/suite-ai/agenti-email-crm.html": { code: "P01", label: "Agenti email & CRM" },
  "/suite-ai/automazioni-amministrative.html": { code: "P02", label: "Automazioni amministrative" },
  "/suite-ai/ai-legale-contratti.html": { code: "P03", label: "AI legale & contratti" },
  "/suite-ai/ai-ingegneria-progettazione.html": { code: "P04", label: "AI ingegneria & progettazione" },
  "/suite-ai/microapp-documenti-tecnici.html": { code: "P05", label: "Microapp documenti tecnici" },
  "/suite-ai/ai-customer-service-ticket.html": { code: "P06", label: "AI customer service & ticket" },
  "/suite-ai/rag-knowledge-base.html": { code: "P07", label: "RAG knowledge base" },
  "/suite-ai/ai-compliance-audit.html": { code: "P08", label: "AI compliance & audit" },
  "/suite-ai/ai-controllo-gestione-reporting.html": { code: "P09", label: "AI controllo di gestione" },
  "/suite-ai/integrazione-gestionali-erp.html": { code: "P10", label: "Integrazione gestionali & ERP" },
  "/suite-ai/ai-marketing-contenuti.html": { code: "P11", label: "AI marketing & contenuti" },
  "/suite-ai/analisi-strategica-pmi.html": { code: "P12", label: "Analisi strategica PMI" },
  "/suite-ai/diagnosi-strategica-pmi.html": { code: "P12", label: "Analisi strategica PMI" },
  "/suite-ai/agevolazioni-finanza-agevolata.html": { code: "P13", label: "Agevolazioni & finanza agevolata" },
  "/suite-ai/ai-edilizia-appalti-pubblici.html": { code: "P14", label: "AI edilizia & appalti pubblici" },
  "/suite-ai/ai-hr-recruiting.html": { code: "P15", label: "AI HR & recruiting" },
  "/suite-ai/ai-real-estate-tokenizzazione.html": { code: "P16", label: "AI real estate & tokenizzazione" },
  "/suite-ai/ai-data-analytics-bi.html": { code: "P17", label: "AI data analytics & BI" },
  "/suite-ai/ai-ux-design-system.html": { code: "P18", label: "AI UX & design system" },
  "/suite-ai/ai-efficienza-energetica.html": { code: "P19", label: "AI efficienza energetica" },
  "/suite-ai/ai-hospitality-revenue.html": { code: "P20", label: "AI hospitality & revenue" },
  "/laboratorio": { code: "LAB", label: "Laboratorio" },
};

function resolvePillarFromUrl(url: string): { code: string; label: string; url: string } {
  const map = URL_TO_PILLAR[url];
  if (map) return { code: map.code, label: map.label, url };
  return { code: "P00", label: "Suite AI", url: "/suite-ai.html" };
}
import { createClient, generateDraft, reviseArticle } from "./lib/claude.js";
import { renderArticleHtml } from "./lib/template.js";
import { injectSitemapEntry } from "./lib/sitemap.js";
import { injectIndexCard } from "./lib/index-injector.js";
import { createOpenAIClient, generateArticleImages, type GeneratedImages } from "./lib/images.js";
import { commitAndPush } from "./lib/git.js";
import { notify } from "./lib/notify.js";
import { validateSeo } from "./validators/seo.js";
import { validateVoice } from "./validators/voice.js";
import { validateTeaser } from "./validators/teaser.js";
import { validateFacts } from "./validators/facts.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, "..", "..");
const BLOG_DIR = join(REPO_ROOT, "kai-website", "src", "blog");
const BLOG_INDEX_PATH = join(BLOG_DIR, "index.html");
const BLOG_IMG_DIR = join(BLOG_DIR, "img");
const SITEMAP_PATH = join(REPO_ROOT, "kai-website", "src", "public", "sitemap.xml");
const DRAFTS_REJECTED = join(__dirname, "drafts-rejected");

// Mapping pillar derivato dall'URL: vedi URL_TO_PILLAR sopra.

async function main() {
  const dryRun = process.argv.includes("--dry-run");

  // Source of truth è schedule.json nel repo (vedi lib/sheet-client.ts).
  // Nessuna Google API necessaria.
  const sheet = new SheetClient();

  const row = await sheet.pickNextForBlog();
  if (!row) {
    await notify("📭 *Blog bot*: nessuna riga `da usare` con blog non pubblicato. Coda vuota.");
    console.log("nothing to publish");
    return;
  }
  console.log(`[pick] row ${row.rowIndex}: ${row.servizio}`);

  const pillar = resolvePillarFromUrl(row.url);
  const anthropic = createClient();

  console.log("[draft] calling Claude Sonnet...");
  let pieces = await generateDraft(anthropic, {
    servizio: row.servizio,
    problema: row.descrizione,
    risultato_kpi: row.risultati_kpi,
    agevolazione: row.agevolazione,
    pillar_padre: pillar.code,
    pillar_url: pillar.url,
  });
  console.log(`[draft] H1: "${pieces.meta.title_h1}" | slug: ${pieces.meta.slug}`);

  console.log("[revise] calling Claude Haiku...");
  pieces = await reviseArticle(anthropic, pieces);

  // Image gen via OpenAI gpt-image-1. Se OPENAI_API_KEY manca o le scene
  // non sono nel META, l'articolo viene pubblicato senza immagini (warning).
  let images: GeneratedImages | null = null;
  if (process.env.OPENAI_API_KEY && pieces.meta.image_scenes) {
    try {
      const openai = createOpenAIClient();
      images = await generateArticleImages(
        openai,
        pieces.meta.image_scenes,
        pieces.meta.slug,
        BLOG_IMG_DIR
      );
      console.log(`[images] generated: ${images.cover}, ${images.inline1}, ${images.inline2}`);
    } catch (e) {
      console.error(`[images] generation failed: ${(e as Error).message}`);
      await notify(`⚠️ *Blog bot*: image gen fallito per ${pieces.meta.slug}. Articolo pubblicato senza immagini.\n\`\`\`\n${(e as Error).message}\n\`\`\``);
    }
  } else {
    const reason = !process.env.OPENAI_API_KEY ? "OPENAI_API_KEY missing" : "image_scenes missing in META";
    console.log(`[images] skipped: ${reason}`);
  }

  // Build full HTML
  const publishedAtIso = new Date().toISOString().slice(0, 10);
  const fullHtml = renderArticleHtml({
    meta: pieces.meta,
    bodyHtml: pieces.bodyHtml,
    pillarPadre: pillar.code,
    pillarUrl: pillar.url,
    pillarLabel: pillar.label,
    coverUrl: images?.cover,
    inline1Url: images?.inline1,
    inline2Url: images?.inline2,
    publishedAtIso,
    related: [
      {
        href: pillar.url,
        kicker: "Pillar",
        title: `Pacchetto completo ${pillar.label}`,
        body: `L'offerta K2-AI sulla categoria: cosa fa, come si integra, tempi e modalità.`,
      },
      {
        href: "/app",
        kicker: "Strumento",
        title: "K-BOT — diagnosi gratis in 5 minuti",
        body: "Descrivi il tuo caso. K-BOT dice se vale custom o se basta uno strumento standard.",
      },
      {
        href: "/contatti.html",
        kicker: "Persone",
        title: "Parla con noi",
        body: "Se preferisci una call diretta, scrivici. Rispondiamo in 24 ore con una lettura onesta.",
      },
    ],
  });

  // Validators
  console.log("[validate] seo + voice + facts + teaser...");
  // Keyword normalization: schedule.json usa " & " (es. "Agenti AI Email & CRM"),
  // ma l'articolo scrive naturale "agenti AI email e CRM". Convertiamo per
  // permettere il match in densità.
  const keywordPrimaria = row.servizio.toLowerCase().replace(/\s+&\s+/g, " e ");
  const seoRes = validateSeo(fullHtml);
  const voiceRes = validateVoice(fullHtml, keywordPrimaria);
  const factsRes = validateFacts(fullHtml, []);
  const teaserRes = await validateTeaser(fullHtml, anthropic);

  const allErrors = [
    ...seoRes.errors.map((e) => `[seo] ${e}`),
    ...voiceRes.errors.map((e) => `[voice] ${e}`),
    ...teaserRes.errors.map((e) => `[teaser] ${e}`),
    ...factsRes.errors.map((e) => `[facts] ${e}`),
  ];
  const allWarnings = [
    ...seoRes.warnings.map((w) => `[seo] ${w}`),
    ...voiceRes.warnings.map((w) => `[voice] ${w}`),
    ...teaserRes.warnings.map((w) => `[teaser] ${w}`),
    ...factsRes.warnings.map((w) => `[facts] ${w}`),
  ];

  if (allWarnings.length) {
    console.log("[validate] warnings:");
    for (const w of allWarnings) console.log("  - " + w);
  }
  if (allErrors.length) {
    console.error("[validate] FAIL:");
    for (const e of allErrors) console.error("  - " + e);

    if (!existsSync(DRAFTS_REJECTED)) mkdirSync(DRAFTS_REJECTED, { recursive: true });
    const rejectedPath = join(DRAFTS_REJECTED, `${pieces.meta.slug}-${publishedAtIso}.html`);
    writeFileSync(rejectedPath, fullHtml, "utf-8");
    await notify(
      `❌ *Blog bot*: articolo rifiutato dai validator (${allErrors.length} errori).\n` +
        `Riga: ${row.servizio}\n` +
        `Slug: \`${pieces.meta.slug}\`\n` +
        `Errori (primi 5):\n` +
        allErrors.slice(0, 5).map((e) => `• ${e}`).join("\n") +
        `\n\nBozza salvata in \`tools/blog-bot/drafts-rejected/\`. Sheet non aggiornata.`
    );
    process.exit(1);
  }
  console.log("[validate] OK");

  if (dryRun) {
    const outPath = join(__dirname, "dry-run-output", `${pieces.meta.slug}.html`);
    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, fullHtml, "utf-8");
    console.log(`[dry-run] articolo NON pubblicato. Salvato in ${outPath}`);
    return;
  }

  // Write article
  if (!existsSync(BLOG_DIR)) mkdirSync(BLOG_DIR, { recursive: true });
  const articlePath = join(BLOG_DIR, `${pieces.meta.slug}.html`);
  writeFileSync(articlePath, fullHtml, "utf-8");
  console.log(`[write] ${articlePath}`);

  // Update sitemap
  injectSitemapEntry(SITEMAP_PATH, pieces.meta.slug, publishedAtIso);
  console.log(`[sitemap] entry added for ${pieces.meta.slug}`);

  // Update blog index card
  injectIndexCard(BLOG_INDEX_PATH, {
    slug: pieces.meta.slug,
    title: pieces.meta.title_h1,
    description: pieces.meta.meta_description,
    category: row.categoria || pillar.label,
    publishedAtIso,
  });
  console.log(`[index] card prepended for ${pieces.meta.slug}`);

  // Git commit + push
  const articleRel = `kai-website/src/blog/${pieces.meta.slug}.html`;
  const indexRel = `kai-website/src/blog/index.html`;
  const sitemapRel = `kai-website/src/public/sitemap.xml`;
  const imageRels = images
    ? [
        `kai-website/src/blog/img/${images.cover}`,
        `kai-website/src/blog/img/${images.inline1}`,
        `kai-website/src/blog/img/${images.inline2}`,
      ]
    : [];
  const msg = `feat(blog): publish "${pieces.meta.title_h1}"\n\nAuto-generated by blog-bot from sheet row ${row.rowIndex} (${row.servizio}).\nPillar: ${pillar.code}\nSlug: ${pieces.meta.slug}\n\nCo-Authored-By: k2-blog-bot <blog-bot@k2-ai.it>`;
  commitAndPush([articleRel, indexRel, sitemapRel, ...imageRels], msg, REPO_ROOT);
  console.log("[git] pushed");

  // Mark sheet
  const blogUrl = `/blog/${pieces.meta.slug}`;
  await sheet.markBlogPublished(row.rowIndex, pieces.meta.slug, publishedAtIso, blogUrl);
  console.log(`[sheet] row ${row.rowIndex} marked: blog_url=${blogUrl}`);

  // Notify
  await notify(
    `✅ *Blog bot*: articolo pubblicato.\n` +
      `📝 ${pieces.meta.title_h1}\n` +
      `🔗 https://www.k2-ai.it${blogUrl}\n` +
      `📌 Riga sheet ${row.rowIndex} — ${row.servizio}\n\n` +
      `n8n IG userà questa riga giovedì 18:00 con link al blog.`
  );
}

main().catch(async (e) => {
  console.error("[fatal]", e);
  await notify(`💥 *Blog bot CRASH*\n\`\`\`\n${(e as Error).message}\n\`\`\``);
  process.exit(1);
});
