# Per Luca — tutto ciò che serve dal tuo lato per mettere K-BOT in produzione

*Da Luigi (runtime 8e). Documento unico e completo: cosa è già fatto, cosa resta a te, cosa confermare. Verificato sui dati reali dello snapshot/catalogo nel repo (`kai-website/k2a-8e/`).*

---

## 0. Dove siamo

Il motore 8e genera report consulenziali profondi (8-12 pagine) con citazioni di legge **verbatim** dallo snapshot. Codice completo e testato offline (clamp avversariale 12/12, freshness-gate, integrazione kbot↔8e 8/8). I deliverable reali confermati finora: **LegalBoost + FiscoBoost** (PDF veri).

Per andare in produzione su tutto il catalogo serve chiudere il **grounding/dati** dal tuo lato. La **struttura** è già consegnata (vedi §1): non è da rifare.

---

## 1. STRUTTURA — già consegnata da te, presente nel repo ✅

Sincronizzata dai tuoi repo il 2026-06-07. **Niente da fare qui**, solo per tua consapevolezza:

- **Catalogo** `catalog/catalog.json` v1.0.0 — 81 servizi, 15 generabili da 8e, prezzi presenti (19€ → 2500€).
- **12 blueprint** (`blueprints/<skill>/blueprint.json`) — struttura di ogni report.
- **12 form** (`form.json`) — input richiesti all'utente.
- **12 output-schema** (`output-schema.json`) — forma del deliverable.
- **Snapshot grounding** `grounding/grounding-snapshot.json` — i fatti (coverage 55/57).

---

## 2. GROUNDING / DATI — cosa resta a te (6 punti)

### ✅ Già pronti e verificati — nessuna azione (4 boost)
- **LegalBoost** (3 art. verbatim) · **FiscoBoost** (8 art., già current: IRPEF 23/33/43 L.199/2025, ravvedimento post-D.Lgs.87/2024) · **SafetyBoost** (4 art. penali, aggravante infortuni presente) · **MEPBoost** (D.M.37/2008 art.5/6/7/15, stabile).
- Tutti coperti dal freshness-gate in CI.

### 🟡 Da completare

**(1) BuildBoost — QA Salva-Casa via MCP**
Chiavi `dpr380_3 / 10 / 22 / 24` (DPR 380/2001 art. 3/10/22/24). Il verbatim NON ha marker della riforma D.L.69/2024; art. 3 e 24 sono toccati dal Salva-Casa 2024 → **verifica/rinfresca contro la KB**. (Il gate li tiene già flaggati soft.)

**(2) Quattro dataset BENCHMARK vuoti** (`valore` assente oggi):
| chiave | boost | dato |
|---|---|---|
| `revpar_zona` | Host | RevPAR medio zona/categoria |
| `keyword_dataset` | Web/SEO | volumi keyword di settore |
| `multipli_ev` | Advisor | multipli EV/EBITDA di settore |
| `benchmark_settore` | Finance | indici/benchmark di settore |
Senza questi, quei 4 boost generano **senza confronto reale**. Servono i dataset.

**(3) AgevolazioniBoost — decisione + dati**
Ha **0 fatti**: è time-bound (iperammortamento 2026, Sabatini, de minimis). Approccio D-047 (numeri da fonte datata con freshness-gate, non congelati nello snapshot) + fonte dei numeri. È il più scoperto oggi.

**(4) Snapshot canonico + date CONSOLIDATED**
Tu segnali Fisco stale, ma nel committato è già current → forse hai una **copia più vecchia**. Mandami `snapshot_version` + `generated_at` del tuo per riconciliare **prima** di qualsiasi refresh. Dove possibile, includi la data `CONSOLIDATED/AAAAMMGG` per entry (così il gate confronta le date oltre ai marker testuali).

**(5) Stabilizzare il subprocess MCP**
Si pianta dopo alcune chiamate. Serve stabile per la QA Build e ogni estensione. (Non tocca il runtime: in esercizio l'8e risolve dallo snapshot statico, non dall'MCP.)

**(6) Confermare le formule dei calc-boost**
Finance (9 formule), Control (5), Advisor (2) hanno formule deterministiche nello snapshot. Confermami che sono **validate**. Strategy ha solo input (framework, model-only): confermi che è voluto.

---

## 3. DA CONFERMARE — 2 firme

**(A) Prezzi definitivi.** Il catalogo è v1.0.0. Confermi che i prezzi sono quelli **finali di lancio**? Servono per creare i price_id Stripe.

**(B) Disclaimer legali per boost** (D-034/D-036). Confermi che il testo di responsabilità nei deliverable è quello **approvato**.

---

## 4. NET — la tua parte completa per la produzione

| # | Cosa | Stato |
|---|---|---|
| Struttura | catalogo, 12 blueprint/form/schema | ✅ già consegnata |
| Grounding pilota | Legal, Fisco, Safety, MEP | ✅ verificati |
| 1 | QA Build (Salva-Casa) | 🟡 |
| 2 | 4 dataset benchmark | 🟡 |
| 3 | Agevolazioni (decisione+dati) | 🟡 |
| 4 | snapshot canonico + date | 🟡 |
| 5 | MCP stabile | 🟡 |
| 6 | conferma formule calc | 🟡 |
| A | prezzi finali | conferma |
| B | disclaimer approvati | conferma |

**Consegnati 1-6 + A-B → snapshot completo 57/57 e verificato → si genera tutto il catalogo, production-ready al primo colpo.**

## 5. Scorciatoia consigliata
Il **pilota Legal + Fisco + Safety è già 100% pronto adesso** (struttura ✅ + grounding ✅). Si può andare live a 3 boost con pochissimi crediti, e completare 1-6 / A-B in parallelo — senza aspettare tutto.

## 6. Cosa NON è tuo (lo gestisce Luigi)
- Deploy 8e su Railway + URL · secret `K2A_ENTITLEMENT_SECRET` · creazione price_id su Stripe · iniezione verbatim (già attiva) · freshness-gate (già in CI) · determinismo motore.

---

### Formato risposta utile
1. Snapshot: `snapshot_version` + `generated_at` del tuo (per riconciliare §2.4).
2. Per i 6 punti: cosa chiudi subito, cosa serve MCP, cosa è decisione.
3. Conferme A/B (prezzi, disclaimer).
4. Scegliamo: pilota-3 subito, o aspettare tutto-12.
