/**
 * Documento di lavoro (PEC, lettera, registro…) separato dalla conversazione.
 * Specchio di backend/app/lib/documento.py: il modello racchiude il documento fra <<<DOCUMENTO: titolo>>> e
 * <<<FINE DOCUMENTO>>>; il resto è conversazione. Il parser funziona anche sul testo PARZIALE di uno stream in corso.
 */
export type BloccoDocumento = { titolo: string; testo: string; completo: boolean };

const APERTURA = /<<<\s*DOCUMENTO(?:\s*:\s*([^>\n]{1,120}?))?\s*>>>/i;
const CHIUSURA = /<<<\s*FINE\s+DOCUMENTO\s*>>>/i;

/** Toglie in coda un marcatore ancora a metà («<<<DOCUM», «<<<FINE DOC»): non deve mai comparire a schermo. */
function senzaMarcatoreParziale(t: string): string {
  const i = t.lastIndexOf("<<");
  if (i >= 0 && t.indexOf(">>>", i) === -1) return t.slice(0, i);
  return t;
}

export function estraiDocumenti(testo: string): BloccoDocumento[] {
  const out: BloccoDocumento[] = [];
  let resto = testo || "";
  for (;;) {
    const a = APERTURA.exec(resto);
    if (!a) break;
    const dopo = resto.slice(a.index + a[0].length);
    const c = CHIUSURA.exec(dopo);
    const corpoGrezzo = c ? dopo.slice(0, c.index) : dopo;
    const corpo = (c ? corpoGrezzo : senzaMarcatoreParziale(corpoGrezzo)).replace(/^\n+/, "").trim();
    out.push({ titolo: (a[1] || "Documento").trim(), testo: corpo, completo: Boolean(c) });
    if (!c) break;
    resto = dopo.slice(c.index + c[0].length);
  }
  return out;
}

/** La conversazione: il testo senza i blocchi-documento (e senza il documento ancora aperto). */
export function fuoriDalDocumento(testo: string): string {
  let resto = testo || "";
  let out = "";
  for (;;) {
    const a = APERTURA.exec(resto);
    if (!a) {
      out += senzaMarcatoreParziale(resto);
      break;
    }
    out += resto.slice(0, a.index);
    const dopo = resto.slice(a.index + a[0].length);
    const c = CHIUSURA.exec(dopo);
    if (!c) break;
    resto = dopo.slice(c.index + c[0].length);
  }
  return out.replace(/\n{3,}/g, "\n\n").trim();
}

/** L'ultimo messaggio chiede di SCRIVERE un documento testuale? (stessa regola del backend: «report», «analisi»… restano ai report) */
const VERBI = "scrivi|scrivimi|redigi|redigimi|prepara|preparami|stendi|stendimi|compila|compilami|bozza|abbozza|stila|fammi|formula|genera|generami|crea|creami|produci|elabora";
const DOCUMENTI = "lettera|diffida|mail|e-?mail|pec|raccomandata|contratto|atto|comunicazione|messaggio|risposta|reclamo|contestazione|verbale|disdetta|recesso|preventivo|sollecito|informativa|testo|registro|documento|modulo|modello|nomina|delega|autocertificazione|dichiarazione|valutazione|notifica|segnalazione|procedura|policy|regolamento|istruzione operativa";
const RICHIESTA = new RegExp(`\\b(?:${VERBI})\\b[\\s\\S]{0,80}?\\b(?:${DOCUMENTI})\\b`, "i");
const REPORT = /\b(?:report|analisi|cruscotto|check-?up|bilancio|piano|pdf|excel|business plan)\b/i;

export function richiestaDocumento(ultimoUtente: string): boolean {
  const t = ultimoUtente || "";
  const m = RICHIESTA.exec(t);
  if (!m) return false;
  return !REPORT.test(t.slice(Math.max(0, m.index - 10), m.index + m[0].length + 40));
}

export type StatoDocumento = "preparazione" | "scrittura" | "verifica" | "pronto" | "errore";
