/**
 * Brand voice validator: banned terms + AI-typical phrases.
 * Esegue sul body markdown/text (extracted), case-insensitive.
 */
import * as cheerio from "cheerio";

const BANNED_TERMS = [
  // CLAUDE.md ban list (termini v1)
  "advisor finanziari pmi",
  "diagnosi strategica",
  "advisorboost",
  "strategyboost",
  "advisor pmi",
  // Buzzword K2-AI brand voice
  "trasformazione digitale",
  "rivoluzionario",
  "all'avanguardia",
  "cutting-edge",
  "cutting edge",
  "nell'era digitale",
  "nell'era dell'ai",
  "innovativo",
  "innovativa",
  "all'avanguardia",
];

const AI_TYPICAL = [
  "in conclusione",
  "è importante notare",
  "vale la pena di",
  "nel mondo di oggi",
  "non è più sufficiente",
  "in un'epoca in cui",
  "nel panorama attuale",
  "scenario complesso",
  "dinamiche di mercato",
  "stakeholder",
  "leverage",
  "unlock il potenziale",
  "delivery di valore",
];

export interface VoiceCheckResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
}

export function validateVoice(fullHtml: string, keywordPrimaria: string): VoiceCheckResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  const $ = cheerio.load(fullHtml);
  const text = $("article, main").text() || $("body").text();
  const lower = text.toLowerCase();

  for (const term of BANNED_TERMS) {
    if (lower.includes(term)) {
      errors.push(`banned term: "${term}"`);
    }
  }
  for (const term of AI_TYPICAL) {
    if (lower.includes(term)) {
      errors.push(`AI-typical phrase: "${term}"`);
    }
  }

  // Avg sentence length
  const sentences = text
    .replace(/\s+/g, " ")
    .split(/[.!?]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  const words = sentences.flatMap((s) => s.split(" ").filter(Boolean));
  const avg = words.length / Math.max(sentences.length, 1);
  if (avg > 28) {
    warnings.push(`avg sentence length ${avg.toFixed(1)} > 28 words`);
  }

  // Keyword stuffing: 0.4%-2.5%
  if (keywordPrimaria) {
    const kw = keywordPrimaria.toLowerCase();
    const matches = lower.split(kw).length - 1;
    const density = matches / Math.max(words.length, 1);
    if (density < 0.003) {
      warnings.push(`keyword "${kw}" density ${(density * 100).toFixed(2)}% < 0.3% (too low)`);
    }
    if (density > 0.025) {
      errors.push(`keyword "${kw}" density ${(density * 100).toFixed(2)}% > 2.5% (stuffing)`);
    }
  }

  return { ok: errors.length === 0, errors, warnings };
}
