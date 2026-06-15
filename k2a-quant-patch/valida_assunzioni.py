"""valida_assunzioni — il recinto del giudizio (spec Luca §1.8, criterio #1).

Le assunzioni forward (FCF, g, costo debito, rettifiche) restano giudizio
dell'agente, MA passano da check deterministici contro gli storici del cliente e i
range di settore dello snapshot. Esito per il gate Stop del K-BOT:
  OK   → via libera
  WARN → consegna SOLO se il deliverable motiva ogni check in WARN
  FAIL → blocco, l'agente rivede le assunzioni

Il check più importante (Luca): un'azienda a margine basso/negativo che proietta
FCF da margine alto → la traiettoria margini è incoerente → WARN/FAIL.
"""
from __future__ import annotations

from typing import Optional

from .calc_result import calc_result
from . import snapshot as snap


def _cagr(series: list) -> Optional[float]:
    s = [float(x) for x in (series or []) if isinstance(x, (int, float))]
    if len(s) < 2 or s[0] <= 0:
        return None
    return (s[-1] / s[0]) ** (1 / (len(s) - 1)) - 1


def _last(series: list) -> Optional[float]:
    s = [x for x in (series or []) if isinstance(x, (int, float))]
    return float(s[-1]) if s else None


def valida_assunzioni(
    storici: dict,
    assunzioni: dict,
    settore: str,
    snapshot: dict,
    *,
    patrimonio_netto_eur: Optional[float] = None,
) -> dict:
    inputs = {"settore": settore, "assunzioni": assunzioni}
    asof = snap.snapshot_as_of(snapshot)
    g_lo, g_hi = snap.g_range(snapshot, settore)
    banda = snap.banda_cagr(snapshot, settore)
    rf_pct = snap.country(snapshot).get("rf_10y", 0.0385) * 100
    checks: list[dict] = []

    # 1) CAGR FCF previsti vs CAGR storico ricavi ± banda di settore
    cagr_fcf = _cagr(assunzioni.get("fcf_previsti_eur", []))
    cagr_ric = _cagr(storici.get("ricavi_eur", []))
    if cagr_fcf is not None and cagr_ric is not None:
        soglia = cagr_ric + banda / 100
        checks.append({"check": "cagr_fcf_vs_storico",
                       "esito": "OK" if cagr_fcf <= soglia else "WARN",
                       "valore": round(cagr_fcf, 3), "soglia_max": round(soglia, 3),
                       "nota": f"CAGR FCF previsto {cagr_fcf:.1%} vs storico ricavi {cagr_ric:.1%} + banda {banda}%"})

    # 2) traiettoria margini: margine FCF implicito vs margine EBITDA storico
    ric_last = _last(storici.get("ricavi_eur", []))
    eb_last = _last(storici.get("ebitda_eur", []))
    fcf_first = (assunzioni.get("fcf_previsti_eur") or [None])[0]
    if ric_last and eb_last is not None and isinstance(fcf_first, (int, float)):
        margine_storico = eb_last / ric_last
        margine_implicito = fcf_first / ric_last
        gap = margine_implicito - margine_storico
        checks.append({"check": "traiettoria_margini",
                       "esito": "OK" if gap <= banda / 100 else "FAIL",
                       "valore": round(margine_implicito, 3), "margine_storico": round(margine_storico, 3),
                       "nota": f"margine FCF implicito {margine_implicito:.1%} vs storico EBITDA {margine_storico:.1%}"})

    # 3) g perpetuo dentro il range di settore (rifiuto, non warning)
    g = assunzioni.get("g_perpetuo_pct")
    if g is not None:
        checks.append({"check": "g_perpetuo_in_range",
                       "esito": "OK" if g_lo <= g <= g_hi else "FAIL",
                       "valore": g, "range": [g_lo, g_hi]})

    # 4) costo debito dentro banda risk-free + spread plausibile (max +8pp)
    kd = assunzioni.get("costo_debito_pct")
    if kd is not None:
        lo, hi = round(rf_pct, 2), round(rf_pct + 8, 2)
        checks.append({"check": "costo_debito_plausibile",
                       "esito": "OK" if lo <= kd <= hi else "WARN",
                       "valore": kd, "banda": [lo, hi]})

    # 5) rettifiche patrimoniali vs soglia 50% PN
    rett = assunzioni.get("rettifiche_totale_eur")
    if rett is not None and patrimonio_netto_eur:
        soglia = 0.5 * abs(patrimonio_netto_eur)
        checks.append({"check": "rettifiche_vs_50pct_pn",
                       "esito": "OK" if abs(rett) <= soglia else "WARN",
                       "valore": rett, "soglia": round(soglia, 2)})

    esiti = [c["esito"] for c in checks]
    globale = "FAIL" if "FAIL" in esiti else ("WARN" if "WARN" in esiti else "OK")
    outputs = {"esito_globale": globale, "checks": checks}
    return calc_result("valida_assunzioni", inputs, outputs, snapshot_as_of=asof)
