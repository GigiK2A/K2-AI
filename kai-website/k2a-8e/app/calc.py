"""Calcolo deterministico dei formula-fact — stopgap integrità (FinanceBoost + HostBoost + Cruscotto).

Lo snapshot dichiara 20 formula-fact come `fonte: "calcolo-runtime"`, ma la pipeline
NON li calcolava: finivano come formula-stringa nel prompt e li calcolava Sonnet
(violazione del principio "i numeri solo da tool deterministici"). Su prodotti VENDUTI.

Questo modulo riporta deterministici (Python puro) i fact aritmetici (no assunzioni):
  • bilancio:    de, roe, ros, roi, ebitda_margin, current_ratio, quick_ratio, ccn   (ccc → n/d)
  • hospitality: revpar, adr, occupancy (KPI dichiarati dall'utente, passthrough)      [HostBoost]
  • controllo:   ctrl_ebitda, ctrl_cashflow, ctrl_churn, ctrl_scost                     [Cruscotto]

Restano FUORI `dcf` e `wacc` (assunzioni → k2a-mcp-quant + valida_assunzioni) e i fact
il cui dato non è nel form (`goppar`: manca GOP/notti; `ctrl_dso`: manca crediti) → n/d.
Dove il form non fornisce i dati → `non_disponibile` con motivo. MAI inventato.

Base: estensione di Luca (HostBoost+Cruscotto) RICONCILIATA da Luigi contro i form.json
REALI (i nomi/struttura assunti dalle formule-snapshot non combaciavano: HostBoost
fornisce i KPI già calcolati, non le componenti grezze; Cruscotto usa clienti_attivi).
Quando arriva k2a-mcp-quant, `resolve_formula_fact(key, form)` è il punto di swap.
"""
from __future__ import annotations

from typing import Any, Optional

# ───────────────────────── helper numerici ─────────────────────────

def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        # formato IT "1.234,56" → 1234.56; se è già decimale-punto ("6.04") non rompere
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _div(a: Any, b: Any) -> Optional[float]:
    a, b = _num(a), _num(b)
    if a is None or b is None or b == 0:
        return None
    return a / b


def _pct(x: Optional[float]) -> Optional[float]:
    return round(x * 100, 1) if x is not None else None


def _r2(x: Optional[float]) -> Optional[float]:
    return round(x, 2) if x is not None else None


def _r1(x: Optional[float]) -> Optional[float]:
    return round(x, 1) if x is not None else None


# ═══════════════════════ 1. FACT DI BILANCIO ═══════════════════════
# Calcolati dai `bilanci` del form (lista per anno), con serie pluriennale.

_BILANCIO_FORMULA: dict[str, str] = {
    "de": "D/E = debiti_finanziari / patrimonio_netto",
    "roe": "ROE % = utile_netto / patrimonio_netto",
    "ros": "ROS % = reddito_operativo / ricavi",
    "roi": "ROI % = reddito_operativo / totale_attivo (proxy capitale investito)",
    "ebitda_margin": "EBITDA margin % = EBITDA / ricavi",
    "current_ratio": "current_ratio = attivo_corrente / passivo_corrente",
    "quick_ratio": "quick_ratio = (attivo_corrente - rimanenze) / passivo_corrente",
    "ccn": "CCN = attivo_corrente - passivo_corrente",
    "ccc": "CCC = DSO + giorni_magazzino - DPO",
}
_BILANCIO_KEYS = set(_BILANCIO_FORMULA)


def _latest(bilanci: list) -> Optional[dict]:
    rows = [b for b in bilanci if isinstance(b, dict)]
    with_year = [b for b in rows if _num(b.get("anno")) is not None]
    if with_year:
        return max(with_year, key=lambda b: _num(b.get("anno")))
    return rows[-1] if rows else None


def _compute_bilancio(key: str, b: dict) -> tuple[Optional[float], list[str]]:
    g = b.get
    if key == "de":
        return _r2(_div(g("debiti_finanziari"), g("patrimonio_netto"))), ["debiti_finanziari", "patrimonio_netto"]
    if key == "roe":
        return _pct(_div(g("utile_netto"), g("patrimonio_netto"))), ["utile_netto", "patrimonio_netto"]
    if key == "ros":
        return _pct(_div(g("reddito_operativo"), g("ricavi"))), ["reddito_operativo", "ricavi"]
    if key == "roi":
        return _pct(_div(g("reddito_operativo"), g("totale_attivo"))), ["reddito_operativo", "totale_attivo"]
    if key == "ebitda_margin":
        return _pct(_div(g("ebitda"), g("ricavi"))), ["ebitda", "ricavi"]
    if key == "current_ratio":
        return _r2(_div(g("attivo_corrente"), g("passivo_corrente"))), ["attivo_corrente", "passivo_corrente"]
    if key == "quick_ratio":
        ac, rim = _num(g("attivo_corrente")), _num(g("rimanenze"))
        num = (ac - rim) if (ac is not None and rim is not None) else None
        return _r2(_div(num, g("passivo_corrente"))), ["attivo_corrente", "rimanenze", "passivo_corrente"]
    if key == "ccn":
        ac, pc = _num(g("attivo_corrente")), _num(g("passivo_corrente"))
        return (round(ac - pc, 2) if ac is not None and pc is not None else None), ["attivo_corrente", "passivo_corrente"]
    if key == "ccc":
        return None, ["dso", "giorni_magazzino", "dpo"]  # non derivabile dal form attuale
    return None, []


# ═══════════ 2. FACT "FLAT" (hospitality + controllo) ═══════════
# Aritmetica pura da campi del form (root o blocco annidato di 1° livello).

def _field(form: dict, name: str) -> Optional[float]:
    if name in form:
        v = _num(form.get(name))
        if v is not None:
            return v
    for val in form.values():
        if isinstance(val, dict) and name in val:
            v = _num(val.get(name))
            if v is not None:
                return v
    return None


# — hospitality (HostBoost) —
# RICONCILIATO: il form HostBoost fornisce i KPI GIÀ calcolati in kpi_attuali
# (occupancy_pct, adr_eur, revpar_eur). Non sono componenti da derivare → passthrough
# autoritativo: il valore è quello dichiarato dall'utente, l'LLM non lo ricalcola.
def _f_adr(form):       return _r2(_field(form, "adr_eur"))
def _f_revpar(form):    return _r2(_field(form, "revpar_eur"))
def _f_occupancy(form): return _r1(_field(form, "occupancy_pct"))
def _f_goppar(form):    # GOP/notti non nel form HostBoost → n/d (onesto)
    return _r2(_div(_field(form, "gross_operating_profit"), _field(form, "notti_disponibili")))


# — controllo (Cruscotto direzionale) —
def _f_ctrl_ebitda(form):
    a, b = _field(form, "fatturato"), _field(form, "costi_operativi")
    return round(a - b, 2) if a is not None and b is not None else None

def _f_ctrl_cashflow(form):
    a, b = _field(form, "incassi"), _field(form, "pagamenti")
    return round(a - b, 2) if a is not None and b is not None else None

def _f_ctrl_dso(form):
    # crediti_commerciali non è nel form Cruscotto → n/d (serve a Luca decidere
    # campo + giorni-periodo per un cruscotto mensile). Calcola se i dati ci sono.
    r = _div(_field(form, "crediti_commerciali"), _field(form, "fatturato"))
    giorni = _field(form, "giorni_periodo")
    return _r1(r * (giorni if giorni is not None else 30.0)) if r is not None else None

def _f_ctrl_churn(form):
    # RICONCILIATO: il form ha clienti_attivi (fine periodo) + nuovi_clienti + clienti_persi.
    # base iniziale ricostruita = attivi - nuovi + persi (standard). churn = persi / iniziali.
    persi, attivi, nuovi = _field(form, "clienti_persi"), _field(form, "clienti_attivi"), _field(form, "nuovi_clienti")
    if persi is None or attivi is None or nuovi is None:
        return None
    iniziali = attivi - nuovi + persi
    return _pct(persi / iniziali) if iniziali > 0 else None

def _f_ctrl_scost(form):
    # RICONCILIATO: scostamento ricavi vs budget (fatturato vs target_budget.fatturato_target).
    fatt, tgt = _field(form, "fatturato"), _field(form, "fatturato_target")
    if fatt is None or tgt is None or tgt == 0:
        return None
    return _pct((fatt - tgt) / tgt)


_FLAT_SPEC: dict[str, tuple[str, Any, list[str]]] = {
    # hospitality (HostBoost) — KPI dichiarati dall'utente (kpi_attuali), passthrough
    "revpar":    ("RevPAR € (KPI dichiarato dall'utente)",   _f_revpar,    ["revpar_eur"]),
    "adr":       ("ADR € (KPI dichiarato dall'utente)",      _f_adr,       ["adr_eur"]),
    "occupancy": ("Occupancy % (KPI dichiarato dall'utente)", _f_occupancy, ["occupancy_pct"]),
    "goppar":    ("GOPPAR = gross_operating_profit / notti_disponibili", _f_goppar, ["gross_operating_profit", "notti_disponibili"]),
    # controllo (Cruscotto direzionale)
    "ctrl_ebitda":   ("EBITDA = fatturato - costi_operativi",            _f_ctrl_ebitda,   ["fatturato", "costi_operativi"]),
    "ctrl_cashflow": ("cashflow_operativo = incassi - pagamenti",        _f_ctrl_cashflow, ["incassi", "pagamenti"]),
    "ctrl_dso":      ("DSO = crediti_commerciali / fatturato * giorni",  _f_ctrl_dso,      ["crediti_commerciali", "fatturato"]),
    "ctrl_churn":    ("churn % = clienti_persi / (clienti_attivi - nuovi_clienti + clienti_persi)", _f_ctrl_churn, ["clienti_persi", "clienti_attivi", "nuovi_clienti"]),
    "ctrl_scost":    ("scostamento ricavi % = (fatturato - fatturato_target) / fatturato_target",   _f_ctrl_scost, ["fatturato", "fatturato_target"]),
}
_FLAT_KEYS = set(_FLAT_SPEC)

HANDLED = _BILANCIO_KEYS | _FLAT_KEYS  # dcf/wacc NON qui: assunzioni → quant
_FORMULA = {**_BILANCIO_FORMULA, **{k: v[0] for k, v in _FLAT_SPEC.items()}}


# ───────────────────────── interfaccia pubblica ─────────────────────────

def _nd(formula: str, motivo: str) -> dict:
    return {"tipo": "non_disponibile", "valore": None, "formula": formula, "motivo": motivo}


def resolve_formula_fact(key: str, form: dict) -> Optional[dict]:
    """Ritorna un fact con valore CALCOLATO o `non_disponibile` (mai None per le chiavi
    HANDLED → niente fallback all'LLM). Per chiavi non gestite (dcf, wacc, …) ritorna
    None: il chiamante usa la formula-stringa / il quant."""
    if key not in HANDLED:
        return None

    if key in _BILANCIO_KEYS:
        formula = _BILANCIO_FORMULA[key]
        bilanci = form.get("bilanci")
        if not isinstance(bilanci, list) or not bilanci:
            return _nd(formula, "nessun bilancio strutturato fornito")
        b = _latest(bilanci) or {}
        val, campi = _compute_bilancio(key, b)
        if val is None:
            mancanti = [c for c in campi if _num(b.get(c)) is None]
            return _nd(formula, f"dati non forniti dal form: {', '.join(mancanti) if mancanti else ', '.join(campi)}")
        fact = {"tipo": "valore_calcolato", "valore": val, "formula": formula,
                "anno": b.get("anno"), "fonte": "calcolo-runtime"}
        serie = {}
        for bb in bilanci:
            if isinstance(bb, dict) and bb.get("anno") is not None:
                vv, _ = _compute_bilancio(key, bb)
                if vv is not None:
                    serie[str(bb.get("anno"))] = vv
        if len(serie) > 1:
            fact["serie"] = serie
        return fact

    formula, fn, campi = _FLAT_SPEC[key]
    val = fn(form)
    if val is None:
        mancanti = [c for c in campi if _field(form, c) is None]
        return _nd(formula, f"dati non forniti dal form: {', '.join(mancanti) if mancanti else ', '.join(campi)}")
    return {"tipo": "valore_calcolato", "valore": val, "formula": formula, "fonte": "calcolo-runtime"}
