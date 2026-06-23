"""LBO model — IRR sponsor, MOIC, debt paydown schedule."""
from __future__ import annotations
from pydantic import BaseModel, Field
from scipy.optimize import brentq


class LBOInput(BaseModel):
    entry_ebitda: float = Field(..., gt=0)
    entry_multiple: float = Field(..., gt=0, description="EV/EBITDA entry")
    debt_pct: float = Field(0.6, ge=0, lt=1, description="LTV iniziale")
    interest_rate: float = Field(..., description="Costo del debito, decimale")
    tax_rate: float = Field(0.25, ge=0, lt=1)
    ebitda_growth: float = Field(..., description="CAGR EBITDA periodo, decimale")
    exit_multiple: float = Field(..., gt=0)
    holding_period: int = Field(5, ge=1, le=10)
    capex_pct_revenue: float = Field(0.03, description="Approssimazione: CapEx ≈ Δ EBITDA proxy")
    cash_sweep: float = Field(1.0, ge=0, le=1.0, description="% FCF dedicato a rimborso debito")
    minimum_cash: float = Field(0.0, ge=0)


class LBOYear(BaseModel):
    year: int
    ebitda: float
    interest: float
    taxes: float
    fcf_for_debt: float
    debt_repayment: float
    debt_eop: float


class LBOOutput(BaseModel):
    entry_ev: float
    entry_equity: float
    entry_debt: float
    exit_ev: float
    exit_debt: float
    exit_equity: float
    sponsor_irr: float
    moic: float
    schedule: list[LBOYear]
    trace: dict


def compute_lbo(inp: LBOInput) -> LBOOutput:
    ev0 = inp.entry_ebitda * inp.entry_multiple
    debt0 = ev0 * inp.debt_pct
    eq0 = ev0 - debt0

    schedule = []
    debt = debt0
    ebitda = inp.entry_ebitda
    for t in range(1, inp.holding_period + 1):
        ebitda = ebitda * (1 + inp.ebitda_growth)
        interest = debt * inp.interest_rate
        # Semplificazione: D&A ≈ CapEx → EBIT ≈ EBITDA − D&A; usiamo proxy EBITDA - interest = pretax
        pretax = ebitda - interest
        taxes = max(pretax, 0) * inp.tax_rate
        # FCF ≈ EBITDA - interest - taxes - capex (capex ≈ capex_pct × ebitda come proxy)
        capex = inp.capex_pct_revenue * ebitda
        fcf = ebitda - interest - taxes - capex
        repay = min(max(fcf * inp.cash_sweep - inp.minimum_cash, 0), debt)
        debt = max(debt - repay, 0)
        schedule.append(LBOYear(
            year=t, ebitda=round(ebitda, 2), interest=round(interest, 2),
            taxes=round(taxes, 2), fcf_for_debt=round(fcf, 2),
            debt_repayment=round(repay, 2), debt_eop=round(debt, 2),
        ))

    exit_ev = ebitda * inp.exit_multiple
    exit_eq = exit_ev - debt
    moic = exit_eq / eq0 if eq0 > 0 else 0.0

    # IRR: eq0 invested → exit_eq dopo N anni (no dividendi interim per v0.1)
    if exit_eq <= 0 or eq0 <= 0:
        irr = -1.0
    else:
        irr = (exit_eq / eq0) ** (1 / inp.holding_period) - 1

    return LBOOutput(
        entry_ev=round(ev0, 2), entry_equity=round(eq0, 2), entry_debt=round(debt0, 2),
        exit_ev=round(exit_ev, 2), exit_debt=round(debt, 2), exit_equity=round(exit_eq, 2),
        sponsor_irr=round(irr, 4), moic=round(moic, 3),
        schedule=schedule,
        trace={
            "fcf_proxy": "EBITDA − interest − taxes − capex_pct×EBITDA",
            "exit_eq_formula": "exit_EBITDA × exit_multiple − debt_eop_N",
            "irr_simplification": "no interim distributions",
        },
    )
