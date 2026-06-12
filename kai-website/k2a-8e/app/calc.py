"""Calcolo deterministico degli indici di bilancio — stopgap integrità FinanceBoost.

Lo snapshot dichiara questi indici come `fonte: "calcolo-runtime"`, ma la pipeline
NON li calcolava: finivano come formula-stringa nel prompt e li calcolava Sonnet
(violazione del principio "i numeri solo da tool deterministici"). Qui i numeri
tornano deterministici (Python puro). Dove il form non fornisce i dati, l'indice è
marcato `non_disponibile` con motivo — mai inventato.

Quando arriva `k2a-mcp-quant` (Luca), questo modulo è sostituibile da una chiamata
all'MCP: stesso principio, stessa interfaccia di fatto (key → valore + formula).
"""
from __future__ import annotations

from typing import Any, Optional

# Indici gestiti deterministicamente. Gli altri formula-fact (revpar, dcf, wacc,
# ctrl_*, ...) restano stringa: appartengono ad altri boost o richiedono assunzioni
# (DCF/WACC → li gestirà il quant con valida_assunzioni).
_FORMULA: dict[str, str] = {
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
HANDLED = set(_FORMULA)


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.replace(".", "").replace(",", ".")) if v.strip() else None
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


def _latest(bilanci: list) -> Optional[dict]:
    rows = [b for b in bilanci if isinstance(b, dict)]
    with_year = [b for b in rows if _num(b.get("anno")) is not None]
    if with_year:
        return max(with_year, key=lambda b: _num(b.get("anno")))
    return rows[-1] if rows else None


def _compute(key: str, b: dict) -> tuple[Optional[float], list[str]]:
    """Ritorna (valore, campi_richiesti). valore=None se un campo manca."""
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
        # Non derivabile dal form attuale (mancano crediti/debiti commerciali, magazzino, giorni).
        return None, ["dso", "giorni_magazzino", "dpo"]
    return None, []


def resolve_formula_fact(key: str, form: dict) -> Optional[dict]:
    """Per i formula-fact finanziari: ritorna un fact con valore CALCOLATO o
    `non_disponibile` (mai None per le chiavi HANDLED → niente fallback all'LLM).
    Per chiavi non gestite ritorna None (il chiamante usa la formula-stringa)."""
    if key not in HANDLED:
        return None
    formula = _FORMULA[key]
    bilanci = form.get("bilanci")
    if not isinstance(bilanci, list) or not bilanci:
        return {"tipo": "non_disponibile", "valore": None, "formula": formula,
                "motivo": "nessun bilancio strutturato fornito"}
    b = _latest(bilanci) or {}
    val, campi = _compute(key, b)
    if val is None:
        mancanti = [c for c in campi if _num(b.get(c)) is None]
        return {"tipo": "non_disponibile", "valore": None, "formula": formula,
                "motivo": f"dati non forniti dal form: {', '.join(mancanti) if mancanti else ', '.join(campi)}"}
    fact = {"tipo": "valore_calcolato", "valore": val, "formula": formula,
            "anno": b.get("anno"), "fonte": "calcolo-runtime"}
    serie: dict[str, float] = {}
    for bb in bilanci:
        if isinstance(bb, dict) and bb.get("anno") is not None:
            vv, _ = _compute(key, bb)
            if vv is not None:
                serie[str(bb.get("anno"))] = vv
    if len(serie) > 1:
        fact["serie"] = serie
    return fact
