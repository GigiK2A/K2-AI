// Citazioni documentali: il backend normalizza i marcatori `[[fonte|doc|pag|citazione|stato]]` scritti dal modello.
//   doc   = identificativo del documento nella pratica (lo assegna il backend, non il modello)
//   pag   = numero di pagina (0 se il formato non ha pagine)
//   stato = "ok" passaggio verificato nel testo del documento · "pag" solo pagina · assente = non ancora verificato (streaming)
export type Citazione = { doc: string; pag: number; quote: string; stato: "ok" | "pag" | "attesa" };

const RE = /\[\[fonte\|([^|\]]*)\|(\d*)\|([^\]]*?)(?:\|(ok|pag))?\]\]/g;

/** Sostituisce i marcatori con link `kbot-fonte:N` (risolti da Markdown.tsx) e toglie quelli ancora incompleti in streaming. */
export function preparaTesto(testo: string): { testo: string; citazioni: Citazione[] } {
  const citazioni: Citazione[] = [];
  let out = testo.replace(RE, (_m, doc: string, pag: string, quote: string, stato?: string) => {
    const n = Number(pag) || 0;
    citazioni.push({ doc: doc.trim(), pag: n, quote: quote.trim(), stato: (stato as "ok" | "pag") ?? "attesa" });
    return ` [${n ? `pag. ${n}` : "fonte"}](kbot-fonte:${citazioni.length - 1})`;
  });
  // marcatore non ancora chiuso alla fine del testo (token in arrivo): non va mostrato a pezzi
  out = out.replace(/\[\[fonte[^\]]*$/, "").replace(/\[\[?f?o?n?t?e?$/, "");
  // "(pag. N)" scritto a mano resta un riferimento semplice, non cliccabile
  out = out.replace(/\(pag\.\s*(\d+)\)/gi, (_m, n: string) => `[pag. ${n}](kbot-pag:${n})`);
  return { testo: out, citazioni };
}
