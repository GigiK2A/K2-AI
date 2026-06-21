"""NPV / IRR / MIRR / Payback standalone."""
from __future__ import annotations
import numpy as np
from pydantic import BaseModel, Field
from scipy.optimize import brentq


class NpvIrrInput(BaseModel):
    cash_flows: list[float] = Field(..., min_length=2, description="CF_0, CF_1, ..., CF_N (t=0 di solito negativo)")
    discount_rate: float = Field(..., description="Per NPV, decimale")
    reinvest_rate: float | None = Field(None, description="Per MIRR; se None usa discount_rate")
    finance_rate: float | None = Field(None, description="Per MIRR sui flussi negativi")


class NpvIrrOutput(BaseModel):
    npv: float
    irr: float | None
    mirr: float | None
    payback_period: float | None
    discounted_payback: float | None
    profitability_index: float | None
    trace: dict


def _npv(rate: float, cfs: list[float]) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cfs))


def compute_npv_irr(inp: NpvIrrInput) -> NpvIrrOutput:
    cfs = inp.cash_flows
    n = len(cfs)
    npv = _npv(inp.discount_rate, cfs)

    # IRR via brentq
    irr = None
    try:
        # cerca cambio di segno
        irr = brentq(lambda r: _npv(r, cfs), -0.99, 10.0)
    except Exception:
        irr = None

    # MIRR
    rr = inp.reinvest_rate if inp.reinvest_rate is not None else inp.discount_rate
    fr = inp.finance_rate if inp.finance_rate is not None else inp.discount_rate
    pos = [cf if cf > 0 else 0.0 for cf in cfs]
    neg = [cf if cf < 0 else 0.0 for cf in cfs]
    fv_pos = sum(cf * (1 + rr) ** (n - 1 - t) for t, cf in enumerate(pos))
    pv_neg = sum(cf / (1 + fr) ** t for t, cf in enumerate(neg))
    mirr = None
    if pv_neg < 0 and fv_pos > 0:
        mirr = (fv_pos / -pv_neg) ** (1 / (n - 1)) - 1

    # Payback semplice e scontato
    cum, payback = 0.0, None
    for t, cf in enumerate(cfs):
        cum += cf
        if cum >= 0 and payback is None:
            # interpola
            prev = cum - cf
            payback = (t - 1) + (-prev / cf) if cf != 0 else float(t)
            break

    cum_d, dpayback = 0.0, None
    for t, cf in enumerate(cfs):
        pv = cf / (1 + inp.discount_rate) ** t
        cum_d += pv
        if cum_d >= 0 and dpayback is None:
            prev = cum_d - pv
            dpayback = (t - 1) + (-prev / pv) if pv != 0 else float(t)
            break

    # Profitability Index = PV(inflows) / |CF_0|
    pi = None
    if cfs[0] < 0:
        pv_in = sum(cf / (1 + inp.discount_rate) ** t for t, cf in enumerate(cfs) if t > 0 and cf > 0)
        pi = pv_in / -cfs[0]

    return NpvIrrOutput(
        npv=round(npv, 4),
        irr=round(irr, 6) if irr is not None else None,
        mirr=round(mirr, 6) if mirr is not None else None,
        payback_period=round(payback, 4) if payback is not None else None,
        discounted_payback=round(dpayback, 4) if dpayback is not None else None,
        profitability_index=round(pi, 4) if pi is not None else None,
        trace={"n_flows": n, "decision_rule": "Accept if NPV>0 and IRR>discount_rate"},
    )
