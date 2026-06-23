"""DCF — Discounted Cash Flow con terminal value (Gordon o exit multiple) e sensitivity."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class DcfInput(BaseModel):
    fcf: list[float] = Field(..., description="Free Cash Flow esplicito anno 1..N in EUR")
    wacc: float = Field(..., description="WACC, decimale es. 0.09")
    terminal_method: Literal["gordon", "exit_multiple"] = "gordon"
    g_perpetual: float = Field(0.02, description="g per Gordon, decimale")
    exit_multiple: float | None = Field(None, description="EV/EBITDA terminale (se exit_multiple)")
    terminal_ebitda: float | None = Field(None, description="EBITDA anno N+1 per exit multiple")
    net_debt: float = Field(0.0, description="PFN in EUR (sottratta da EV per ottenere Equity)")
    shares_outstanding: float | None = None


class DcfOutput(BaseModel):
    pv_explicit: float
    terminal_value: float
    pv_terminal: float
    enterprise_value: float
    equity_value: float
    value_per_share: float | None
    discount_factors: list[float]
    pv_fcf_by_year: list[float]
    trace: dict


def compute_dcf(inp: DcfInput) -> DcfOutput:
    N = len(inp.fcf)
    dfs = [(1 + inp.wacc) ** -(t + 1) for t in range(N)]
    pv_fcf = [cf * d for cf, d in zip(inp.fcf, dfs)]
    pv_explicit = sum(pv_fcf)

    if inp.terminal_method == "gordon":
        if inp.wacc <= inp.g_perpetual:
            raise ValueError("WACC deve essere > g per Gordon Growth.")
        tv = inp.fcf[-1] * (1 + inp.g_perpetual) / (inp.wacc - inp.g_perpetual)
        tv_formula = "FCF_N × (1+g) / (WACC - g)"
    else:
        if inp.exit_multiple is None or inp.terminal_ebitda is None:
            raise ValueError("exit_multiple e terminal_ebitda obbligatori.")
        tv = inp.exit_multiple * inp.terminal_ebitda
        tv_formula = "EV/EBITDA × EBITDA_N+1"

    pv_tv = tv * dfs[-1]
    ev = pv_explicit + pv_tv
    eq = ev - inp.net_debt
    vps = eq / inp.shares_outstanding if inp.shares_outstanding else None

    return DcfOutput(
        pv_explicit=round(pv_explicit, 2),
        terminal_value=round(tv, 2),
        pv_terminal=round(pv_tv, 2),
        enterprise_value=round(ev, 2),
        equity_value=round(eq, 2),
        value_per_share=round(vps, 4) if vps is not None else None,
        discount_factors=[round(d, 6) for d in dfs],
        pv_fcf_by_year=[round(p, 2) for p in pv_fcf],
        trace={
            "terminal_formula": tv_formula,
            "pv_terminal_pct_ev": round(pv_tv / ev * 100, 1) if ev else 0,
            "method": inp.terminal_method,
        },
    )


class SensitivityInput(BaseModel):
    base: DcfInput
    wacc_range: list[float] = Field(..., description="Lista WACC da testare")
    g_range: list[float] = Field(..., description="Lista g da testare (solo Gordon)")


def sensitivity_dcf(inp: SensitivityInput) -> dict:
    grid = []
    for w in inp.wacc_range:
        row = []
        for g in inp.g_range:
            mod = inp.base.model_copy(update={"wacc": w, "g_perpetual": g})
            try:
                row.append(round(compute_dcf(mod).equity_value, 2))
            except ValueError:
                row.append(None)
        grid.append(row)
    return {"wacc_axis": inp.wacc_range, "g_axis": inp.g_range, "equity_value_grid": grid}
