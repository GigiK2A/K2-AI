# Handoff Luigi → Luca — schema fatti snapshot, entry LegalBoost, contratto resolve()

*Risposta ai 3 file che il tuo Claude ha chiesto a "Luigi". + 1 correzione importante.*

---

## ⚠️ Correzione prima di tutto: Fisco e Safety SONO GIÀ groundati

Verificato sullo snapshot reale in `kai-website/k2a-8e/grounding/grounding-snapshot.json` (57 entries, **coverage 55/57**, gli unici 2 gap sono `benchmark`):

- **FiscoBoost** (`flusso-fiscoboost-pmi`) — 8 chiavi normative **già presenti e verbatim**:
  `iva_16` (1727 char, fonte `akn_bulk_xml`), `iva_19`, `ravvedimento_13`, `tuir_83`, `tuir_96`, `tuir_102` (4821 char), `tuir_109`, `tuir_11`. Più `in_regime` (input).
- **SafetyBoost** (`flusso-safetyboost-studio`) — 4 chiavi penali **già presenti e verbatim**:
  `cp_437`, `cp_451`, `cp_589` (testo reale, `override_locale`, status "VIGENTE confermato 2026-06-04"), `cp_590`. Più `in_cantiere` (input).

**Conseguenza:** il pilota Legal+Fisco+Safety è **già groundato a snapshot**. Il tuo Claude offre di "produrre i fact-file verbatim per Fisco e Safety": in gran parte **è già fatto**. Quello che serve da te su questi non è grounding nuovo, ma **QA di aggiornamento** (le vigenze sono "consolidato KB normattiva" / "2026-06-04": confermare che reggono).

## Il vero gap è CODICE, lato nostro (Luigi), non grounding

I fatti normativi vengono **risolti** correttamente per tutti i boost (lo dimostra `resolve()` che solleverebbe `unresolvable_placeholder` se mancassero — e non succede). Ma:

- **LegalBoost** (voci-shape) inietta le citazioni in modo **deterministico** via `assemble_legalboost` → il `riferimento` nel deliverable è verbatim dallo snapshot. ✅
- **Fisco/Safety** passano dal generatore **generico** (`generate_deliverable_deep`): i fatti verbatim sono nel prompt (`_facts_block`) e il modello è istruito a usarli, ma **l'iniezione verbatim della citazione nell'output NON è forzata** come in LegalBoost. → è qui che una norma può "driftare". 

Questo è il fix di liability vero, ed **è mio (Luigi)**: portare nel path generico la stessa garanzia di LegalBoost (citazioni dallo `citazioni` risolto, non dalla prosa del modello). Lo segno come prossimo lavoro di codice.

---

## I 3 file che hai chiesto

### 1. Una entry LegalBoost reale (struttura da replicare 1:1)

Chiave `cc_1341` in `entries`:
```json
{
  "tipo": "normativo",
  "testo": "# Art. 1341 Codice Civile — Condizioni generali di contratto\n\nLe condizioni generali di contratto predisposte da uno dei contraenti sono efficaci nei confronti dell'altro, se al momento della conclusione del contratto questi le ha conosciute o avrebbe dovuto conoscerle usando l'ordinaria diligenza...",
  "fonte": "override_locale",
  "fonte_url": "https://www.brocardi.it/codice-civile/.../art1341.html",
  "vigenza": "Aggiornato al 29/01/2026 (fonte)",
  "status": "VIGENTE (confermato 2026-06-04 via Brocardi)"
}
```

### 2. Schema dei fatti (`grounding-snapshot.json`)

Top-level: `{ snapshot_version, generated_at, boosts, entries, coverage }`.

`entries` = mappa **chiave-placeholder → fatto**. Il campo `tipo` fa da discriminante:

| `tipo` | campi usati da resolve() | note |
|---|---|---|
| `normativo` | `testo` (verbatim, **prima riga = "# Art. X — Titolo"**), `fonte`, `fonte_url`, `vigenza`, `status` | la prima riga del `testo` è la fonte del `riferimento` leggibile |
| `formula` | `formula` | stringa formula deterministica |
| `input` | `campo_form` | valore preso dal form a runtime, non dallo snapshot |
| `benchmark` | `valore`, `status` | **non bloccante**: se assente → confronto omesso (gap ammesso) |

`coverage` = `{ declared, resolved, gaps:[{key, boost, tipo, motivo}] }`. **Regola CI già attiva**: ammessi solo gap di tipo `benchmark`; un gap `normativo` irrisolto fa fallire la build.

`fonte` ammette almeno: `akn_bulk_xml` (Normattiva bulk reale), `override_locale` (store override per shell HTML), più `fonte_url` per il link umano.

### 3. Come `resolve()` consuma i fatti (`app/pipeline.py`)

```
resolve(skill, form):
  snap    = assets.load_snapshot()
  keys    = assets.placeholders_for(skill)     # elenco CHIUSO di chiavi per quel boost
  for k in keys:
     e = snap["entries"][k]                     # assente → Refuse("unresolvable_placeholder")
     se tipo=="normativo": fact = {valore:testo, fonte, vigenza, riferimento=prima_riga}
                           + citazione {campo:k, riferimento, fonte, fonte_url, vigenza, status}
     ...
  return facts, citazioni
```

Punti chiave per te:
- Il mapping è **per chiave-placeholder**, non per "Art. X". Le chiavi del fact-set di un boost = `placeholders_for(skill)` (il tuo `build_snapshot.py` / manifest le definisce: oggi 57 chiavi / 11 boost).
- **Per groundare/estendere un boost basta**: (a) aggiungere la chiave alla lista del boost nel manifest, (b) mettere la entry verbatim in `entries` con lo schema sopra. `resolve()` la prende automaticamente.
- Le **citazioni** che finiscono nel deliverable escono da `resolve()` (lista `citazioni`), già pronte: `riferimento` + `fonte` + `vigenza` + `status`.

---

## Net: chi fa cosa adesso

- **Luca**: NON rigroundare Fisco/Safety (fatto) — solo **QA vigenze**. Riavviare MCP Normattiva serve solo per estendere fact-set *futuri* o per un 4° boost. Pilota confermabile **subito**. Infra (secret Railway, Stripe price) resta tua.
- **Luigi (io)**: (a) URL 8e quando deployato; (b) **fix codice**: iniezione verbatim delle citazioni nel path generico (Fisco/Safety) come già in LegalBoost — è il vero chiusura-liability.
- **Economics**: ok, ma il tuo punto su **backpressure/coda** è corretto e tocca il mio fan-out parallelo (oggi senza tetto globale). Lo segno come hardening pre-scaling (non pre-pilota).
