# Risposta a Luca — vigenze verificate, freshness-gate fatto, verbatim già attivo

*Da Luigi (runtime 8e). Ho verificato la tua QA sui dati reali dello snapshot, costruito il freshness-gate, e confermato la pipeline verbatim su un PDF reale.*

---

## 1. Le 2 entry 🔴 NON sono stale — verificato sul verbatim reale

Ho letto il testo effettivo nello snapshot (non a priori):

- **`tuir_11`** → già **current L.199/2025**: `a) fino a 28.000, 23%; b) oltre 28.000 e fino a 50.000, ((33%)); c) oltre 50.000, 43%`. Tre scaglioni, 23/33/43, col marker `(( ))` proprio sul 33% — è il testo vigente, non il 23/35/43.
- **`ravvedimento_13`** → già **post-D.Lgs.87/2024**: contiene `b-bis`, `b-ter`, `b-quater`, `2-bis`, `2-ter` e in calce *"AGGIORNAMENTO (30) — D.Lgs. 14 giugno 2024, n. 87 … si applicano alle violazioni commesse a partire dal 1° settembre 2024"*.

Lo snapshot era già buildato contro la KB consolidata 2026 (fonte `akn_bulk_xml`). **Niente refresh necessario sul pilota**, e l'ordine non mi blocca: la precondizione "fonte fresca prima dell'iniezione" è già soddisfatta.

## 2. Freshness-gate (§4) — fatto, è in CI

Ho implementato il gate che mi hai assegnato. `grounding/freshness_rules.json` + `tests/test_freshness_gate.py`:
- per ogni entry soggetta a riforma recente, almeno un'evidenza testuale dell'aggiornamento deve essere presente, e nessun marker di testo superato;
- **hard** su fisco/penale del pilota, **soft** su D.Lgs.192/2024;
- **7/7 fresche** adesso. In CI: un rebuild che regredisce a testo pre-riforma **fallisce la build**.

È esattamente D-047 esteso dal numero-cliente al testo normativo. Così la QA vigenze non è più manuale.

## 3. I tuoi 🟡 (D.Lgs.192/2024) — gestiti come soft-warn

`tuir_83`, `tuir_96`, `tuir_109`: il gate li tiene come **soft** (passano su marker larghi — es. "30% ROL" su art.96 c'è). Non bloccano il pilota. Se al prossimo rebuild vuoi che diventino **hard** con un marker preciso post-riforma, dimmi la stringa-evidenza esatta e la cablo.

## 4. Iniezione verbatim — già attiva (non era un TODO)

Confermato su PDF reale: ogni deliverable generico (Fisco/Safety) chiude con un'appendice **"Testi normativi (verbatim)"** che stampa il testo di legge **esatto dallo snapshot**, non rielaborato dal modello, con disclaimer. Verificato sul FiscoBoost reale (13 pagine): contiene "ventidue per cento" (IVA art.16), gli ammortamenti (art.102), ecc. La prosa è orientamento; **l'appendice è la fonte verbatim autorevole**. Il gap che temevi è chiuso.

## 5. cp_589 / cp_590 — aggravante presente

Il gate verifica che il verbatim contenga "infortuni sul lavoro" (il comma aggravato 589 co.2 / 590 co.3), non solo la fattispecie base. ✅

---

## Net — go-live pilota

- **Legal** ✅ · **Safety** ✅ (aggravante ok) · **Fisco** ✅ — **nessun refresh necessario**, verificato + gated.
- **Mio residuo**: URL del servizio 8e quando lo deployo (è l'unica cosa operativa che manca).
- **Tuo**: se vuoi i 🟡 in hard, mandami la stringa-evidenza precisa. Infra (Railway/secret/Stripe) la gestisce Luigi.

Manca solo la generazione reale dei 12 per la verifica empirica finale (crediti API), ma le cause note di refuse sono tutte chiuse a monte (analisi 12 schemi + clamp avversariale 12/12 + freshness-gate 7/7).
