# k2a-quant-patch — le pezze del gap per il tuo `k2a_quant`

> **Da:** Luigi · **A:** Luca · **Per:** chiudere il quant SENZA ricostruirlo.
> Drop-in da merge nel tuo package canonico `k2a_quant`. Test 12/12 contro il TUO snapshot reale.

## Il finding (importante — fermati prima di ri-sourcing)

Ho ispezionato `k2a_quant` (vendorizzato/deployato): **esiste già quasi tutto.**
- **WACC + CAPM** (Hamada relevering, `ke = rf + βL·ERP`) → `wacc.py`
- **DCF** (Gordon/exit, terminal value, EV, net-debt→equity) → `dcf.py`
- **Snapshot Damodaran gennaio 2026** → `data/industry_multiples.json`: **20 settori con `beta_unlevered` + multipli** (`ev_ebitda`/`ev_sales`/`pe`) e **`country_data[italy]` con `rf_10y` 3,85% / `erp` 7,1% / `tax` 27,9%**.
- MCP server + `lookup_multiples` / `lookup_country`.

**Quindi lo snapshot che stavi per sorgere (Damodaran + BTP) c'è già.** Non rifarlo: al massimo **verifica la freschezza** (è "indicativo gennaio 2026") e aggiungi i 3 campi sotto.

## Cosa contiene questa patch (il gap vero)

| File | Cosa aggiunge | Spec |
|---|---|---|
| `calc_result.py` | **Envelope CalcResult** (call_id, inputs_hash, snapshot_as_of, trace, warnings) | §1.0 |
| `capm.py` | `capm_cost_of_equity` — **assunzioni dallo snapshot** (beta+rf+erp+size per settore), l'agente non li passa più | §1.1 |
| `ev_multiples.py` | `ev_from_multiples` (EBITDA>0 → EV/EBITDA; ≤0 → EV/Ricavi) | §1.4 |
| `valida_assunzioni.py` | **il recinto del giudizio** (OK/WARN/FAIL): CAGR FCF vs storico, **traiettoria margini**, g-in-range, costo-debito, rettifiche | §1.8 |
| `dcf_guard.py` | **g-range hard-reject** sul tuo `compute_dcf` (g fuori range → errore, non warning) | §1.3 |
| `snapshot.py` | helper + i **3 campi mancanti** con default | §2 |

La matematica è la **tua** (riuso `wacc`/`dcf`/`lookups`): qui c'è solo l'instradamento-da-snapshot, l'envelope e il recinto.

## Cosa devi fare tu (poco)

1. **Merge** i file in `k2a_quant/` (cartella package). `dcf_guard` riceve `compute_dcf`/`DcfInput` per evitare import circolari.
2. **3 campi nello snapshot** (sono tua elaborazione, non Damodaran): per ogni settore `g_range_pct` e `banda_cagr_fcf_pct`; top-level `size_premium` per fascia (già in `snapshot.SIZE_PREMIUM` coi valori della tua §2 — spostali nello snapshot se preferisci) e un `as_of` esplicito.
3. **Mappatura ATECO → settore** dentro lo snapshot (la spec §2 la voleva lì): oggi i settori sono chiavi tipo `restaurant_hotel`; serve il dizionario ATECO→chiave così l'8e/agente passano il codice ATECO.
4. **Esponi** i nuovi tool nel tuo MCP server (`server.py`) accanto a calc_wacc/calc_dcf.
5. **Manutenzione** snapshot: owner tu, refresh annuale Damodaran + risk-free più spesso (decisione DEC1 confermata da Luigi: stale→blocco lato backend per i report venduti).

## Verifica fatta (test_quant_patch.py, 12/12, sul TUO snapshot)
- CAPM `restaurant_hotel`: ke **17,44%** (βU 0,88 → βL 1,72; rf 3,85% + βL·7,1% + size 1,4%).
- ev_from_multiples: 540k×12,8 = 6,912M; EBITDA≤0 → 3,6M×2,1 = 7,56M.
- valida_assunzioni: **margine storico −1,4% che proietta FCF da margine 14% → FAIL** (il check che volevi); g 5% fuori [0,5–2,0] → FAIL; assunzioni sane → OK.

## Come si aggancia (le due strade)
- **B-path (pipeline 8e FinanceBoost)**: dentro `calc.resolve_formula_fact(key, form)` per `dcf`/`wacc` chiami questi tool → valore + call_id nel fact. Una sola verità.
- **A-path (agente AdvisorBoost)**: sostituisci il mio `quant-lite` con questi → numeri veri + il recinto `valida_assunzioni` come hook PreToolUse ("DCF solo dopo valida_assunzioni").

Dimmi se merge tu o preparo io la PR sul tuo repo. Appena i 3 campi snapshot sono dentro, AdvisorBoost esce dal gate e dcf/wacc del FinanceBoost diventano deterministici.

Luigi
