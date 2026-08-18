/**
 * Risoluzione pillar a partire dall'URL della riga schedule.json.
 *
 * schedule.json contiene URL ASSOLUTI (es. "https://www.k2-ai.it/suite-ai/...")
 * mentre la mappa è indicizzata per PATH (es. "/suite-ai/..."). Per questo
 * normalizziamo sempre a pathname prima del lookup: senza normalizzazione
 * nessuna chiave matcha e ogni articolo cade nel fallback P00.
 */

export interface PillarInfo {
  code: string;
  label: string;
}

export interface ResolvedPillar {
  code: string;
  label: string;
  /** Path relativo del pillar, usato come href negli internal link. */
  url: string;
}

// Mapping PATH → codice pillar (per metadata + section-label).
// Le righe "Laboratorio" puntano a /laboratorio invece di un pillar.
export const URL_TO_PILLAR: Record<string, PillarInfo> = {
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

/**
 * Normalizza un URL (assoluto o già-path) al solo pathname.
 * "https://www.k2-ai.it/suite-ai/x.html" → "/suite-ai/x.html"
 * "/laboratorio"                          → "/laboratorio"
 * Eventuale trailing slash viene rimosso (eccetto la root).
 */
export function toPath(url: string): string {
  let path: string;
  try {
    // URL assoluto con schema → estrai pathname.
    path = new URL(url).pathname;
  } catch {
    // Già un path relativo (new URL senza base lancia).
    path = url.startsWith("/") ? url : `/${url}`;
  }
  if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);
  return path;
}

export function resolvePillarFromUrl(url: string): ResolvedPillar {
  const path = toPath(url);
  const map = URL_TO_PILLAR[path];
  // href SENZA estensione .html: è l'URL canonico servito in prod; la
  // variante .html risponde con un 301 che negli internal link va evitato.
  if (map) return { code: map.code, label: map.label, url: path.replace(/\.html$/, "") };
  return { code: "P00", label: "Suite AI", url: "/suite-ai" };
}
