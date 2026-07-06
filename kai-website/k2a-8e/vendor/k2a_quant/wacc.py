"""WACC — Weighted Average Cost of Capital con beta lever/unlever (Hamada)."""
from __future__ import annotations
from pydantic import BaseModel, Field


class WaccInput(BaseModel):
    rf: float = Field(..., description="Risk-free rate (Bund 10Y, euro), decimale es. 0.0295 (cfr. country_data['italy'].rf_10y). NB: il rischio-paese va nell'ERP, NON nel rf — non usare il BTP qui (doppio conteggio del rischio-Italia).")
    erp: float = Field(..., description="Equity Risk Premium paese, decimale es. 0.055")
    beta_unlevered: float = Field(..., description="Beta unlevered di settore (Damodaran)")
    equity: float = Field(..., gt=0, description="Equity (E) in EUR")
    debt: float = Field(..., ge=0, description="Debt (D) in EUR")
    cost_of_debt_pretax: float = Field(..., description="Kd pre-tax, decimale")
    tax_rate: float = Field(0.279, description="Aliquota fiscale effettiva (IRES+IRAP eff.), coerente snapshot Italia")


class WaccOutput(BaseModel):
    beta_levered: float
    cost_of_equity: float
    cost_of_debt_aftertax: float
    weight_equity: float
    weight_debt: float
    wacc: float
    trace: dict


def compute_wacc(inp: WaccInput) -> WaccOutput:
    D_E = inp.debt / inp.equity if inp.equity else 0.0
    beta_l = inp.beta_unlevered * (1 + (1 - inp.tax_rate) * D_E)
    ke = inp.rf + beta_l * inp.erp
    kd_at = inp.cost_of_debt_pretax * (1 - inp.tax_rate)
    V = inp.equity + inp.debt
    we = inp.equity / V
    wd = inp.debt / V
    wacc = we * ke + wd * kd_at
    return WaccOutput(
        beta_levered=round(beta_l, 4),
        cost_of_equity=round(ke, 4),
        cost_of_debt_aftertax=round(kd_at, 4),
        weight_equity=round(we, 4),
        weight_debt=round(wd, 4),
        wacc=round(wacc, 4),
        trace={
            "formula_beta_l": "β_u × (1 + (1-t) × D/E)  [Hamada]",
            "formula_ke": "Rf + β_l × ERP  [CAPM]",
            "formula_wacc": "(E/V)·Ke + (D/V)·Kd·(1-t)",
            "D_over_E": round(D_E, 4),
        },
    )
