# Risposta a Luca — calc.py esteso: committato, ma riconciliato ai form reali

Ciao Luca,

committato io (commit `bb53af7` sul ramo 8e). Test verdi, suite 8e (deep/smoke/all-boosts) ok, numeri veri iniettati su HostBoost e Cruscotto. **Ma prima di committare ho dovuto riconciliare**, perché — come temevi — il problema non erano solo i nomi: era la **struttura** dei form. Se avessi committato com'era, su due prodotti venduti i fact tornavano tutti `non_disponibile` (regressione: Sonnet almeno li scriveva). Ecco cosa ho cambiato in `_FLAT_SPEC`, la logica è la tua.

## HostBoost — il form dà i KPI GIÀ calcolati, non le componenti

Il `form.json` di `flusso-hostboost-ricettive` **non ha** `ricavi_camere`/`notti_vendute`/`notti_disponibili`. Ha `kpi_attuali.{occupancy_pct, adr_eur, revpar_eur}`: l'utente inserisce **direttamente** i KPI. Quindi:
- `adr`, `revpar`, `occupancy` → **passthrough autoritativo** del valore dichiarato (deterministico: l'LLM non lo ricalcola). Non li derivo da ADR×occupancy perché il form me li dà.
- `goppar` → `non_disponibile` (GOP e notti non sono nel form).

## Cruscotto — riconciliato ai campi reali

Il `form.json` di `cruscotto-direzionale` ha: `fatturato, costi_operativi, incassi, pagamenti, clienti_attivi, nuovi_clienti, clienti_persi, target_budget.{fatturato_target, ebitda_target}`.
- `ctrl_ebitda` = fatturato − costi_operativi ✓ (combaciava)
- `ctrl_cashflow` = incassi − pagamenti ✓ (combaciava)
- `ctrl_churn` → il form ha `clienti_attivi` (fine periodo), non `clienti_attivi_iniziali`. **Ricostruito**: base iniziale = `clienti_attivi − nuovi_clienti + clienti_persi`, churn = persi/iniziali. ⟵ **assunzione da confermare**
- `ctrl_scost` → generico "valore/target" non deducibile. **Mappato** su scostamento ricavi = (fatturato − fatturato_target)/fatturato_target. ⟵ **assunzione da confermare** (o vuoi ebitda vs ebitda_target? o entrambi?)
- `ctrl_dso` → `non_disponibile`: manca `crediti_commerciali` nel form. Per attivarlo serve la tua decisione su (a) aggiungere il campo crediti e (b) i giorni-periodo per un cruscotto **mensile** (DSO con 365 sarebbe sbagliato). L'ho lasciato n/d apposta, non l'ho indovinato.

## Le 2 decisioni che sono tue (semantica prodotto)

1. **churn**: la base è `clienti_attivi − nuovi + persi`? O `clienti_attivi` è già l'inizio-periodo (allora churn = persi/clienti_attivi)?
2. **ctrl_scost**: scostamento su fatturato (come ora), su EBITDA, o un fact per metrica?

Dimmi e cambio una riga. Se invece per Host/Cruscotto i campi vanno raccolti diversamente (es. aggiungere `crediti_commerciali`, `gross_operating_profit`, `notti_disponibili` ai form per coprire goppar/dso), li aggiungo ai `form.json` come ho fatto per FinanceBoost (e l'autofill li estrae).

## AZIONE 2 e 3

- **AZIONE 2 (batch varianza):** pronto. Ho i 4 casi in-target + `run_batch.py`. Lancio i 3 mancanti + N run dello stesso caso e ti mando il `batch_summary` (stabilità orchestrazione). Ti confermo quando.
- **AZIONE 3 (FinanceBoost A/B):** A adesso — `calc.py` È il calcolo-runtime, esteso. B a regime: dentro `resolve_formula_fact(key, form)` chiami il quant e valore+call_id entrano nel fact. Una sola verità.

Grazie per il _num IT-format: tenuto (replace solo se c'è la virgola). Bel catch sul finding di sistema — ora il principio è ristabilito su **tutti** i venduti ad aritmetica pura, non solo i bilanci.

Luigi
