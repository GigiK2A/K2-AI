"""g-range hard-reject sul DCF (spec Luca §1.3).

Il DCF esistente (k2a_quant/dcf.py, compute_dcf) accetta g_perpetual senza vincolo.
Qui un guard deterministico: se g è fuori dal g_range di settore → RIFIUTO (errore,
non warning), col range ammesso. Wrappa compute_dcf invariato quando g è valido.

Drop-in: importa compute_dcf/DcfInput dal package k2a_quant.
"""
from __future__ import annotations

from .calc_result import calc_result
from . import snapshot as snap


def dcf_enterprise_value_guarded(dcf_input: dict, settore: str, snapshot: dict, compute_dcf, DcfInput) -> dict:
    """compute_dcf / DcfInput sono passati dal package k2a_quant (no import circolare).
    dcf_input: dict conforme a DcfInput (fcf, wacc, g_perpetual, ...)."""
    inputs = {"settore": settore, "dcf_input": dcf_input}
    asof = snap.snapshot_as_of(snapshot)
    g_lo, g_hi = snap.g_range(snapshot, settore)
    g = dcf_input.get("g_perpetual")
    # g nello snapshot è in %, l'input DCF in decimale → confronto coerente
    g_pct = g * 100 if (g is not None and abs(g) < 1) else g
    if g_pct is not None and dcf_input.get("terminal_method", "gordon") == "gordon" and not (g_lo <= g_pct <= g_hi):
        return calc_result("dcf_enterprise_value", inputs, snapshot_as_of=asof,
                           errore={"code": "g_fuori_range", "g_pct": g_pct, "range_ammesso_pct": [g_lo, g_hi]})

    out = compute_dcf(DcfInput(**dcf_input))
    d = out.model_dump() if hasattr(out, "model_dump") else dict(out)
    warnings = []
    ev = d.get("enterprise_value") or 0
    pv_tv = d.get("pv_terminal") or 0
    if ev and pv_tv / ev > 0.75:
        warnings.append("peso_tv_alto")
    return calc_result("dcf_enterprise_value", inputs, d, snapshot_as_of=asof, warnings=warnings)
