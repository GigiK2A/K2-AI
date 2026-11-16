import { test } from "node:test";
import assert from "node:assert/strict";
import { validateFacts, quantityKeys } from "../validators/facts.js";

const page = (body: string) => `<html><body><main><article><p>${body}</p></article></main></body></html>`;
const errs = (body: string, brief: string[] = []) => validateFacts(page(body), brief).errors;

test("facts: una percentuale non fornita dal brief è un errore (blocca)", () => {
  const r = validateFacts(page("Un agente gestisce il 70% dei messaggi."), []);
  assert.equal(r.ok, false);
  assert.equal(r.errors.length, 1);
  assert.match(r.errors[0] ?? "", /70%/);
});

test("facts: range, 'circa' e decimali non rendono lecita una cifra non fornita", () => {
  assert.equal(errs("Circa il 60-70% dei casi.").length, 1);
  assert.equal(errs("Servono 8–12 ore a settimana.").length, 1);
  assert.equal(errs("Il 73,4% delle aziende.").length, 1);
  assert.equal(errs("Fino a 5 minuti per ticket.").length, 1);
});

test("facts: tempi, importi e dimensioni inventati sono errori", () => {
  assert.equal(errs("Uno studio con 8 dipendenti, 40 contratti al mese.").length, 2);
  assert.equal(errs("Il ROI arriva in 6 mesi, con 1.500 € di canone.").length, 2);
  assert.equal(errs("Da 90 minuti a 4 minuti.").length, 2);
});

test("facts: una cifra presente nel brief è consentita, anche con altra grafia dell'unità", () => {
  assert.deepEqual(errs("Recuperate 12 ore a settimana.", ["Ore recuperate: 12h/sett"]), []);
  assert.deepEqual(errs("Circa il 70% delle email.", ["Email gestite senza intervento umano: ~70%"]), []);
  assert.deepEqual(errs("Da 3 a 1 passaggi.", ["Passaggi: da 3 a 1"]), []);
});

test("facts: una cifra del brief non autorizza un'altra cifra", () => {
  assert.equal(errs("Il 80% e il 70%.", ["KPI: ~70%"]).length, 1);
});

test("facts: sono sempre consentiti 14 giorni, 24 ore, anni, norme e tempo di lettura", () => {
  const body = "Il primo prototipo è pronto in 14 giorni. Rispondiamo in 24 ore. Nel 2026 il D.Lgs. 81/08, la ISO 9001, le NTC 2018 e la Transizione 5.0 valgono. 7 min lettura.";
  assert.deepEqual(errs(body), []);
});

test("facts: un numero grande che non è un anno resta un avviso, non un errore", () => {
  const r = validateFacts(page("Il codice 123456 compare nel testo, e nel 2024 anche."), []);
  assert.equal(r.ok, true);
  assert.equal(r.warnings.length, 1);
  assert.match(r.warnings[0] ?? "", /123456/);
});

test("facts: quantityKeys normalizza unità e range", () => {
  const k = quantityKeys("12h/sett e 8–12 ore e 3 minuti").map((x) => x.key);
  assert.ok(k.includes("12h"));
  assert.ok(k.includes("8-12h"));
  assert.ok(k.includes("3min"));
});

test("facts: scenario senza cifre passa", () => {
  const body = "Uno scenario tipico: un team passa molte ore a leggere contratti. Con il sistema il tempo di lettura si riduce.";
  assert.deepEqual(errs(body), []);
});
