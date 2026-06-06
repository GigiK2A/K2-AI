# Dump per Luca — popolamento contratto boost→snapshot

**Da**: Luigi (estratto da `catalog.json` + snapshot reali, handoff v2.27).
**Risponde a**: `boost-snapshot-contract-SKELETON.md` §4 (i 2 dump richiesti) + correzioni di forma.

---

## DUMP 1 — I 12 boost autoritativi (dal `catalog.json`)

15 `service_id` con `genera_via:8e` → **deduplicati per blueprint = 12 boost**.
(LegalBoost ha 4 service_id commerciali che puntano allo stesso blueprint.)

| # | skill_emittente | blueprint_id | service_id commerciali (prezzo) |
|---|---|---|---|
| 1 | `cruscotto-direzionale` | `cruscotto-direzionale.boost` | checkup_controllo (1499) → **ControlBoost** |
| 2 | `flusso-advisorboost-pmi` | `flusso-advisorboost-pmi.boost` | checkup_advisor (2499) |
| 3 | `flusso-agevolazioni-pmi` | `flusso-agevolazioni-pmi.boost` | checkup_agevolazioni (1999) |
| 4 | `flusso-buildboost-studio` | `flusso-buildboost-studio.boost` | checkup_edilizia (2499) |
| 5 | `flusso-financeboost-pmi` | `flusso-financeboost-pmi.boost` | checkup_finanziario (2500) |
| 6 | `flusso-fiscoboost-pmi` | `flusso-fiscoboost-pmi.boost` | checkup_fiscale (1999) |
| 7 | `flusso-hostboost-ricettive` | `flusso-hostboost-ricettive.boost` | checkup_hospitality (690) |
| 8 | `flusso-legalboost-pmi` | `flusso-legalboost-pmi.boost` | primo_parere_legale (490), checkup_legale_triage (1499), checkup_legale_review (1999), checkup_legale_dd (2499) |
| 9 | `flusso-mepboost-studio` | `flusso-mepboost-studio.boost` | checkup_energia (1999) → **MEPBoost** |
| 10 | `flusso-safetyboost-studio` | `flusso-safetyboost-studio.boost` | checkup_sicurezza_safetyboost (1999) |
| 11 | `flusso-strategyboost-pmi` | `flusso-strategyboost-pmi.boost` | checkup_marketing (1800) → **StrategyBoost** |
| 12 | `flusso-webboost-pmi` | `flusso-webboost-pmi.boost` | checkup_seo (1500) → **WebBoost** |

### Riconciliazione vs i tuoi 13 candidati (§3 scheletro)
- **FUORI** (non nel catalog portale, D-035 engineering interno): `StructBoost`, `TLCBoost`, `VerifyBoost` → rimuovere dalla mappa.
- **MANCAVA** nel tuo stub ma È nel catalog: **`FiscoBoost`** (`flusso-fiscoboost-pmi`).
- `ControlBoost <da confermare>` → **skill = `cruscotto-direzionale`** (blueprint `cruscotto-direzionale.boost`).
- Risultato: 13 − 3 (Struct/TLC/Verify) + Fisco = **12** ✓ (+ LegalBoost già nel tuo esempio).

---

## DUMP 2 — Chiavi LegalBoost (esatte, dal resolver/snapshot)

```
cc_1341 · cc_1342 · dlgs231_25septies
```

⚠️ **Correzione di forma importante** (il tuo scheletro assume 3 chiavi
`norma_testo`/`norma_vigenza`/`norma_fonte` per UN articolo). La realtà è diversa:
**LegalBoost consuma 3 chiavi = 3 ARTICOLI**, e ogni entry è UN oggetto che
**già contiene** testo+fonte+vigenza+status. Granularità = **per-articolo**, non
per-campo.

Shape reale di una entry snapshot:
```json
"cc_1341": {
  "tipo": "normativo",
  "testo": "<verbatim art. 1341 c.c.>",
  "fonte": "override_locale",
  "fonte_url": "https://www.brocardi.it/.../art1341.html",
  "vigenza": "Aggiornato al 29/01/2026 (fonte)",
  "status": "VIGENTE (confermato 2026-06-04 via Brocardi)"
}
```
Le 3 chiavi LegalBoost: tutte `tipo:normativo`, `fonte:override_locale`,
`status: VIGENTE confermato 2026-06-04` → **gate pre-vendita CHIUSO** (vendibile),
coerente con la tua nota §2.

---

## Correzioni al vocabolario del contratto (allinealo allo snapshot reale)

Lo snapshot usa **4 `tipo`** (non quelli dello scheletro):

| `tipo` reale | n | resolver/fonte reale | tuo equivalente scheletro |
|---|---|---|---|
| `normativo` | 23 | `override_locale` (11) / `akn_bulk_xml` (12) | `norma_verbatim` |
| `formula` | 20 | `calcolo-runtime` | `numero_deterministico` |
| `input` | 10 | `form.json` | (input form) |
| `benchmark` | 4 | vari (vedi gaps) | `benchmark` |

Note:
- `fonte` reali da aggiungere agli enum del contratto: **`override_locale`**,
  **`akn_bulk_xml`** (non solo `normattiva`/`override_norme`).
- `formula` → il numero è **calcolato a runtime** sui dati del form (non da MCP
  live): coerente con ADR-028 (il numero non è "a memoria del modello", è una
  formula deterministica), ma il resolver è `calcolo-runtime`, non `mcp:<tool>`.
  Valuta se adeguare l'invariante.

---

## BONUS — Tutte le 57 chiavi snapshot (per assegnarle ai 12 boost)

Mancando ancora il manifest placeholder→boost (`build_snapshot.py` non era nello
zip), ecco le chiavi che puoi distribuire tra i boost.

**normativo (23)** — legale/fiscale/edilizia/sicurezza:
`cc_1341, cc_1342, cp_437, cp_451, cp_589, cp_590, dlgs231_25septies, dm37_5, dm37_6, dm37_7, dm37_15, dpr380_3, dpr380_10, dpr380_22, dpr380_24, iva_16, iva_19, ravvedimento_13, tuir_11, tuir_83, tuir_96, tuir_102, tuir_109`

**formula (20)** — indici/metriche `calcolo-runtime`:
`adr, ccc, ccn, ctrl_cashflow, ctrl_churn, ctrl_dso, ctrl_ebitda, ctrl_scost, current_ratio, dcf, de, ebitda_margin, goppar, occupancy, quick_ratio, revpar, roe, roi, ros, wacc`

**input (10)** — dal form: `in_bilanci, in_cantiere, in_competitor, in_edificio, in_intervento, in_mese, in_regime, in_settore, in_struttura, in_url`

**benchmark (4)** — già taggati per boost in `coverage.gaps` (status `da_strutturare`):
- `benchmark_settore` → flusso-financeboost-pmi
- `multipli_ev` → flusso-advisorboost-pmi (`k2a-quant/lookup_multiples`)
- `revpar_zona` → flusso-hostboost-ricettive (`k2a-catalogo/metriche_hospitality`)
- `keyword_dataset` → flusso-webboost-pmi (provider SEO esterno)

---

## Cosa serve ancora a Luigi (per chiudere il resto)

Il dump sopra ti basta per popolare il contratto. Per il runtime serve poi
**l'assegnazione chiave→boost** delle 53 chiavi non-benchmark (oggi nota solo per
LegalBoost). Il modo più pulito: il `build_snapshot.py` reale con la sua
`manifest()` (placeholder→boost) — quella è la fonte. Quando me la passi,
sostituisco il mio `boost_placeholders.json` interim e sblocco gli 11 boost.

*Generato da Luigi dai file reali del repo. Numeri verificabili: `catalog/catalog.json`, `grounding/grounding-snapshot.json`, `grounding/boost_placeholders.json` in `kai-website/k2a-8e/`.*
