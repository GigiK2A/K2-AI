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
import { createClient, generateDraft, reviseArticle } from "./lib/claude.js";
import { renderArticleHtml } from "./lib/template.js";
import { injectSitemapEntry } from "./lib/sitemap.js";
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
const SITEMAP_PATH = join(REPO_ROOT, "kai-website", "src", "public", "sitemap.xml");
const DRAFTS_REJECTED = join(__dirname, "drafts-rejected");

const PILLAR_LABEL_MAP: Record<string, { label: string; url: string }> = {
  P01: { label: "Agenti email & CRM", url: "/suite-ai/agenti-email-crm.html" },
  P02: { label: "Automazioni amministrative", url: "/suite-ai/automazioni-amministrative.html" },
  P03: { label: "AI legale & contratti", url: "/suite-ai/ai-legale-contratti.html" },
  P04: { label: "AI ingegneria & progettazione", url: "/suite-ai/ai-ingegneria-progettazione.html" },
  P05: { label: "Microapp documenti tecnici", url: "/suite-ai/microapp-documenti-tecnici.html" },
  P06: { label: "AI customer service & ticket", url: "/suite-ai/ai-customer-service-ticket.html" },
  P07: { label: "RAG knowledge base", url: "/suite-ai/rag-knowledge-base.html" },
  P08: { label: "AI compliance & audit", url: "/suite-ai/ai-compliance-audit.html" },
  P09: { label: "AI controllo di gestione", url: "/suite-ai/ai-controllo-gestione-reporting.html" },
  P10: { label: "Integrazione gestionali & ERP", url: "/suite-ai/integrazione-gestionali-erp.html" },
  P11: { label: "AI marketing & contenuti", url: "/suite-ai/ai-marketing-contenuti.html" },
  P12: { label: "Analisi strategica PMI", url: "/suite-ai/analisi-strategica-pmi.html" },
  P13: { label: "Agevolazioni & finanza agevolata", url: "/suite-ai/agevolazioni-finanza-agevolata.html" },
  P14: { label: "AI edilizia & appalti pubblici", url: "/suite-ai/ai-edilizia-appalti-pubblici.html" },
  P15: { label: "AI HR & recruiting", url: "/suite-ai/ai-hr-recruiting.html" },
  P16: { label: "AI real estate & tokenizzazione", url: "/suite-ai/ai-real-estate-tokenizzazione.html" },
  P17: { label: "AI data analytics & BI", url: "/suite-ai/ai-data-analytics-bi.html" },
  P18: { label: "AI UX & design system", url: "/suite-ai/ai-ux-design-system.html" },
  P19: { label: "AI efficienza energetica", url: "/suite-ai/ai-efficienza-energetica.html" },
  P20: { label: "AI hospitality & revenue", url: "/suite-ai/ai-hospitality-revenue.html" },
};

function resolvePillar(row: SheetRow): { code: string; label: string; url: string } {
  const code = (row.pillarPadre || "").toUpperCase().trim();
  const map = PILLAR_LABEL_MAP[code];
  if (!map) {
    // fallback: punta alla landing suite-ai
    return { code: code || "P00", label: "Suite AI", url: "/suite-ai.html" };
  }
  return { code, label: map.label, url: row.pillarUrl || map.url };
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");

  const sheetId = process.env.GOOGLE_SHEET_ID;
  if (!sheetId) throw new Error("GOOGLE_SHEET_ID env var missing");
  const sheet = new SheetClient(sheetId);

  const row = await sheet.pickNextForBlog();
  if (!row) {
    await notify("📭 *Blog bot*: nessuna riga `da usare` con blog non pubblicato. Coda vuota.");
    console.log("nothing to publish");
    return;
  }
  console.log(`[pick] row ${row.rowIndex}: ${row.servizio}`);

  const pillar = resolvePillar(row);
  const anthropic = createClient();

  console.log("[draft] calling Claude Sonnet...");
  let pieces = await generateDraft(anthropic, {
    servizio: row.servizio,
    problema: row.problema,
    risultato_kpi: row.risultatoKpi,
    agevolazione: row.agevolazione,
    pillar_padre: pillar.code,
    pillar_url: pillar.url,
  });
  console.log(`[draft] H1: "${pieces.meta.title_h1}" | slug: ${pieces.meta.slug}`);

  console.log("[revise] calling Claude Haiku...");
  pieces = await reviseArticle(anthropic, pieces);

  // Build full HTML
  const publishedAtIso = new Date().toISOString().slice(0, 10);
  const fullHtml = renderArticleHtml({
    meta: pieces.meta,
    bodyHtml: pieces.bodyHtml,
    pillarPadre: pillar.code,
    pillarUrl: pillar.url,
    pillarLabel: pillar.label,
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
  const keywordPrimaria = row.servizio.toLowerCase();
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

  // Git commit + push
  const articleRel = `kai-website/src/blog/${pieces.meta.slug}.html`;
  const sitemapRel = `kai-website/src/public/sitemap.xml`;
  const msg = `feat(blog): publish "${pieces.meta.title_h1}"\n\nAuto-generated by blog-bot from sheet row ${row.rowIndex} (${row.servizio}).\nPillar: ${pillar.code}\nSlug: ${pieces.meta.slug}\n\nCo-Authored-By: k2-blog-bot <blog-bot@k2-ai.it>`;
  commitAndPush([articleRel, sitemapRel], msg, REPO_ROOT);
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
