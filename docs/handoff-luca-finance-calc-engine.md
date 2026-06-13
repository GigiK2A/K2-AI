# Handoff a Luca — motore di calcolo deterministico FinanceBoost (+ il cambiamento)

> **Da:** Luigi · **A:** Luca (+ il suo Claude) · **Data:** 2026-06-13
> **Cosa:** il motore 8e calcolava i numeri finanziari del FinanceBoost (venduto) con l'LLM. Ho messo uno **stopgap deterministico** (`app/calc.py`) e ti consegno **il cambiamento e il motore**, perché il 8e è tuo: o lo adotti così, o ci costruisci `k2a-mcp-quant` sopra con lo stesso contratto. L'importante è non avere due verità che divergono.
>
> In repo: commit `3d0b557`. File: `kai-website/k2a-8e/app/calc.py`, wiring in `app/pipeline.py` + `app/llm.py`, form esteso in `blueprints/flusso-financeboost-pmi/form.json`, test `tests/test_calc.py`.

---

## 1. Il finding (perché il cambiamento)

Lo snapshot dichiara gli indici come `"fonte": "calcolo-runtime"`:

```json
"de":  {"tipo": "formula", "formula": "D/E = debiti_finanziari / patrimonio_netto", "fonte": "calcolo-runtime"},
"roe": {"tipo": "formula", "formula": "ROE = utile_netto / patrimonio_netto",      "fonte": "calcolo-runtime"},
"wacc":{"tipo": "formula", "formula": "WACC = E/V*Ke + D/V*Kd*(1-t)",               "fonte": "calcolo-runtime"}
```

Ma `pipeline.resolve()` (branch `formula`) salvava **solo la stringa**:

```python
elif tipo == "formula":
    facts[k] = {"valore": e.get("formula"), "tipo": "formula"}   # ← formula-testo, mai calcolata
```

E `llm._facts_block` la passava a Sonnet come testo → **l'aritmetica la faceva il modello.** Zero `eval`/`sympy` in tutto il 8e: il `calcolo-runtime` dichiarato non esisteva. Su un report venduto = numeri non deterministici, non riproducibili, non difendibili.

## 2. Il motore (`app/calc.py`) — cosa fa

Implementa il `calcolo-runtime` che lo snapshot già prometteva. Pura aritmetica Python, niente LLM. Interfaccia:

```python
calc.resolve_formula_fact(key: str, form: dict) -> dict | None
```

- Ritorna un fact `{"tipo": "valore_calcolato", "valore": <num>, "formula": ..., "anno": ..., "serie": {...}}` quando i dati ci sono.
- Ritorna `{"tipo": "non_disponibile", "valore": None, "motivo": "..."}` quando il form non basta — **mai un numero inventato**.
- Ritorna `None` per le chiavi che non gestisce (revpar/dcf/wacc/ctrl_*) → il chiamante usa il fallback formula-stringa.

**Indici coperti (deterministici, dai `bilanci` del form):**
`de`, `roe`, `ros`, `roi`, `ebitda_margin`, `current_ratio`, `quick_ratio`, `ccn` + serie pluriennale per il trend.

**Verifica su Juventus:** `D/E = 6,04` (242,8M/40,2M) ora da Python — prima lo scriveva Sonnet.

## 3. Come si aggancia (le 2 modifiche)

**`pipeline.resolve()`** — il branch formula ora calcola:

```python
elif tipo == "formula":
    computed = calc.resolve_formula_fact(k, form)
    facts[k] = computed if computed is not None else {"valore": e.get("formula"), "tipo": "formula"}
```

**`llm._facts_block()`** — i valori calcolati diventano autoritativi, i mancanti non si inventano:

```
- [de] CALCOLATO (anno 2024): 6.04  [D/E = ...]  · serie: {'2023': 8.07, '2024': 6.04}
- [ccc] NON DISPONIBILE — dati non forniti dal form: dso (NON inventare)
```
con una riga di regole in testa al blocco: *"i CALCOLATO sono autoritativi, riportali verbatim; i NON DISPONIBILE non vanno inventati."*

## 4. Il contratto per il tuo `k2a-mcp-quant` (qui ti aggganci)

`calc.resolve_formula_fact(key, form)` **è il punto di sostituzione**. Quando il tuo MCP è pronto, quella chiamata diventa una chiamata al quant: stessa firma di fatto (key + dati → valore + formula + provenienza). I tuoi 8 tool (spec v0.1) mappano 1:1:

| fact-key (snapshot) | tuo tool quant |
|---|---|
| de, roe, ros, roi, ebitda_margin, current/quick, ccn | `indici_bilancio_ccii` (esteso) |
| dcf | `dcf_enterprise_value` (+ `valida_assunzioni` per FCF/g) |
| wacc | `wacc` (+ `capm_cost_of_equity`) |

Il tuo envelope `CalcResult` (`call_id`/`inputs_hash`/`trace`) sostituisce il mio fact: più ricco, stesso ruolo. Il `valore` finisce nel fact, il `call_id` nella provenienza.

## 5. Cosa NON copre (tocca al tuo quant)

- **`ccc`**: il form non ha DSO/giorni-magazzino/DPO → resta `non_disponibile` (onesto). Se lo vuoi, serve estendere il form con crediti/debiti commerciali + magazzino.
- **`dcf`, `wacc`, valutazione (EV)**: hanno bisogno di **assunzioni** (FCF forward, Ke via CAPM, g-range) → li lascio fuori apposta: sono il territorio del tuo quant + `valida_assunzioni`. `calc.py` non finge di calcolarli.

## 6. Form esteso (cosa l'autofill ora estrae)

Ho aggiunto ai `bilanci` del form: `reddito_operativo` (EBIT), `attivo_corrente`, `passivo_corrente`, `rimanenze` → così `ros/roi/current/quick/ccn` diventano deterministici quando l'autofill li trova nel bilancio caricato. Dove mancano → `non_disponibile`, mai stimati.

## 7. La domanda per te

Il 8e è tuo. Due strade, scegli:
- **A)** Adotti `calc.py` così com'è come `calcolo-runtime` (stopgap) e poi lo sostituisci col quant quando è pronto.
- **B)** Lo butti e fai consumare **direttamente il tuo `k2a-mcp-quant`** dalla pipeline (anche per FinanceBoost, non solo Advisor) — preferibile a regime, è il single-source che volevi.

In entrambi i casi il principio è ristabilito **adesso** sul venduto: i numeri di bilancio non escono più da Sonnet. Dimmi quale strada e se vuoi che lasci `calc.py` o lo rimuovo quando arriva il tuo MCP.

Allego: `calc.py`, `test_calc.py`, `form.json`, gli estratti di `pipeline.py`/`llm.py`, le entries `formula` dello snapshot.
