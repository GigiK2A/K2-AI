# Checklist Luca — "tutto pronto" PRIMA di spendere crediti

Obiettivo: quando generiamo i report veri, escono giusti **al primo colpo** su tutti e 12, zero crediti sprecati. Sotto, esatto stato per boost (scan reale dello snapshot, coverage 55/57) e cosa manca DA TE.

## ✅ Pronti e verificati — nessuna azione (4)
- **LegalBoost** — 3 articoli verbatim, freshness-gate OK.
- **FiscoBoost** — 8 articoli verbatim, già current (tuir_11=23/33/43, ravvedimento post-D.Lgs.87/2024), gate OK.
- **SafetyBoost** — 4 articoli penali, aggravante infortuni presente, gate OK.
- **MEPBoost** — D.M.37/2008 art.5/6/7/15, stabile, gate OK.

## 🟡 Serve azione DA TE (per estendere oltre il pilota)

**1. BuildBoost — QA Salva-Casa (MCP)**
Le 4 chiavi `dpr380_3 / 10 / 22 / 24` (DPR 380/2001 art. 3/10/22/24) non hanno marker della riforma D.L.69/2024. Art. 3 e 24 sono toccati dal Salva-Casa → verifica/rinfresca il verbatim contro la KB. (Gate li tiene già flaggati soft.)

**2. Quattro dataset BENCHMARK vuoti** (oggi `valore` assente):
| chiave | boost | cosa serve |
|---|---|---|
| `revpar_zona` | Host | RevPAR medio di zona/categoria |
| `keyword_dataset` | Web/SEO | volumi keyword di settore |
| `multipli_ev` | Advisor | multipli EV/EBITDA di settore |
| `benchmark_settore` | Finance | indici/benchmark di settore |
→ Senza questi, quei 4 boost generano ma **senza confronto/benchmark reale**. Servono i dataset (tu o una fonte dati).

**3. AgevolazioniBoost — decisione + dati**
Ha **0 fatti**: è time-bound (iperammortamento 2026, Sabatini, de minimis). Va deciso l'approccio (D-047: numeri da fonte datata con freshness-gate, non snapshot) e fornita la fonte dei numeri. **Oggi è il più scoperto.**

**4. Snapshot canonico + date CONSOLIDATED**
Riconciliamo quale snapshot è quello buono (tu dici Fisco stale, nel committato è già current → forse hai una copia vecchia). Mandami `snapshot_version` + `generated_at` del tuo. E, dove possibile, la data `CONSOLIDATED/AAAAMMGG` per entry, così il gate confronta le date oltre ai marker.

**5. Stabilizzare il subprocess MCP**
Si pianta dopo alcune chiamate. Serve stabile per fare la QA Build e qualsiasi estensione.

## 🔵 Formule (calc boosts) — confermare validità
Finance (9 formule), Control (5), Advisor (2) hanno le formule nello snapshot. Confermami che sono **validate** (sono determinismo, non LLM). Strategy ha solo input (framework, model-only): confermi che è voluto.

---

## Riepilogo: cosa serve da te per avere TUTTO
1. QA/refresh **Build** (Salva-Casa, via MCP)
2. **4 dataset benchmark** (revpar_zona, keyword_dataset, multipli_ev, benchmark_settore)
3. **Agevolazioni**: decisione + fonte dati time-bound
4. **Snapshot canonico** riconciliato (+ date consolidamento)
5. **MCP stabile**
6. Conferma **formule** calc + Strategy model-only

Consegnati questi 6 → snapshot completo e verificato (57/57) → **allora** spendiamo i crediti e generiamo tutti e 12 production-ready.

## Nota onesta
"Avere tutto da Luca" elimina i giri a vuoto, ma la generazione reale costa comunque crediti: è l'unica prova empirica che i documenti escono bene. La checklist serve a renderla l'**ultima** generazione, non una di scoperta.

**Scorciatoia possibile**: il pilota **Legal+Fisco+Safety è già 100% pronto adesso** (punti ✅). Si potrebbe verificare quello con pochissimi crediti, andare live a 3 boost, e completare i punti 🟡 in parallelo — senza aspettare tutti e 6.
