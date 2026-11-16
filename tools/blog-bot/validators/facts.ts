/**
 * Facts validator.
 *
 * Regola: una cifra con unità (percentuale, ore, minuti, giorni, €, "N persone"…)
 * si può scrivere solo se compare nel brief (`allowedFacts`: i testi del brief,
 * non elenchi di numeri). Un range ("8-12 ore"), un'approssimazione ("circa
 * 60%") o un esempio non rendono accettabile una cifra non fornita.
 * Una cifra non consentita è un ERRORE: blocca la pubblicazione.
 *
 * Consentiti senza essere nel brief: anni, riferimenti normativi e numeri senza
 * unità (D.Lgs. 81/08, ISO 9001, NTC 2018, Transizione 5.0), il tempo
 * di consegna del prototipo «14 giorni», la risposta «24 ore» (lavorative) e il
 * tempo di lettura calcolato dal template («7 min lettura»).
 */
import * as cheerio from "cheerio";

export interface FactsCheckResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
}

// Decisioni di marca: valgono per ogni articolo.
const ALWAYS_ALLOWED = ["14 giorni", "24 ore"];

// numero (anche range) + unità. Il lookbehind evita di prendere pezzi di
// codici o di numeri più lunghi ("81/08", "1.5", "2026-11").
const QUANTITY =
  /(?<![\w.,/-])(\d+(?:[.,]\d+)?)(?:\s?[-–]\s?(\d+(?:[.,]\d+)?))?\s?(%|€|euro|k\s?€|ore|ora|h|minuti|minuto|min|secondi|secondo|sec|giorni|giorno|gg|settimane|settimana|sett|mesi|mese|volte|×|persone|dipendenti|clienti|fatture|ticket|contratti|email|documenti|cantieri|sopralluoghi|collaboratori|professionisti|tecnici)(?![\p{L}\d])/giu;

const UNIT_GROUP: Record<string, string> = {
  "%": "%",
  "€": "€", euro: "€", "k€": "k€",
  ore: "h", ora: "h", h: "h",
  minuti: "min", minuto: "min", min: "min",
  secondi: "s", secondo: "s", sec: "s",
  giorni: "g", giorno: "g", gg: "g",
  settimane: "sett", settimana: "sett", sett: "sett",
  mesi: "mesi", mese: "mesi",
  volte: "x", "×": "x",
};

function normalizeUnit(raw: string): string {
  const u = raw.toLowerCase().replace(/\s+/g, "");
  return UNIT_GROUP[u] ?? u;
}

function norm(n: string): string {
  return n.replace(",", ".");
}

/** Chiavi normalizzate delle quantità presenti in un testo. */
export function quantityKeys(text: string): { key: string; raw: string }[] {
  const out: { key: string; raw: string }[] = [];
  for (const m of text.matchAll(QUANTITY)) {
    const after = text.slice((m.index ?? 0) + m[0].length, (m.index ?? 0) + m[0].length + 12);
    // «7 min lettura» è il tempo di lettura del template, non un claim.
    const unit = normalizeUnit(m[3] ?? "");
    if (unit === "min" && /^\s*(di\s+)?lettura/i.test(after)) continue;
    const n1 = norm(m[1] ?? "");
    const range = m[2] ? `${n1}-${norm(m[2])}` : n1;
    out.push({ key: `${range}${unit}`, raw: m[0].trim() });
  }
  return out;
}

const SPECIFIC_LARGE = /\b\d{4,}\b/g;

export function validateFacts(fullHtml: string, allowedFacts: string[] = []): FactsCheckResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const $ = cheerio.load(fullHtml);
  const text = $("main, article").first().text() || $("body").text();

  const allowed = new Set<string>();
  for (const src of [...ALWAYS_ALLOWED, ...allowedFacts]) {
    for (const { key } of quantityKeys(src)) allowed.add(key);
  }

  const seen = new Set<string>();
  for (const { key, raw } of quantityKeys(text)) {
    if (allowed.has(key) || seen.has(key)) continue;
    seen.add(key);
    errors.push(
      `cifra non fornita dal brief: "${raw}" (percentuali, tempi, importi e dimensioni si scrivono solo se sono nel brief; riscrivi in modo qualitativo)`
    );
  }

  for (const m of text.matchAll(SPECIFIC_LARGE)) {
    const v = m[0];
    if (/^(19|20)\d{2}$/.test(v)) continue; // anni
    warnings.push(`numero grande "${v}": controlla che sia nel brief`);
  }

  return { ok: errors.length === 0, errors, warnings };
}
