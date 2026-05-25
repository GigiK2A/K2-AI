/**
 * Facts validator (best-effort).
 * Estrae numeri citati e li confronta con un whitelist; numeri puntuali
 * non in whitelist generano warning (non blocking nella prima versione,
 * Luigi può rivedere). Range vaghi (es. "3-5") sono sempre ammessi.
 */
import * as cheerio from "cheerio";

export interface FactsCheckResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
}

// Pattern per numeri puntuali sospetti (es. "73,4%", "1.247 ore")
// Range "3-5" e percentuali "circa 60-70%" sono OK.
const SPECIFIC_PERCENT = /(?<![\d-,.])\d{1,2}[,.]\d{1,2}\s?%/g;
const SPECIFIC_LARGE = /\b\d{4,}\b/g;

export function validateFacts(fullHtml: string, allowedFacts: string[] = []): FactsCheckResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const $ = cheerio.load(fullHtml);
  const text = $("article, main").text() || $("body").text();

  const allowed = new Set(allowedFacts.map((s) => s.trim()));

  for (const match of text.matchAll(SPECIFIC_PERCENT)) {
    const m = match[0].trim();
    if (!allowed.has(m)) {
      warnings.push(`specific percent "${m}" not in facts-allowed.yaml`);
    }
  }
  for (const match of text.matchAll(SPECIFIC_LARGE)) {
    const m = match[0].trim();
    // Anni ammessi
    if (/^20\d{2}$/.test(m)) continue;
    // Numeri tipo "1500-2000" ok (sono range)
    if (!allowed.has(m)) {
      warnings.push(`large specific number "${m}" not in facts-allowed.yaml`);
    }
  }

  return { ok: true, errors, warnings };
}
