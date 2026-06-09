"""Yield curve bootstrap da par yields + swap pricing IRS."""
from __future__ import annotations
import numpy as np
from pydantic import BaseModel, Field


class BootstrapInput(BaseModel):
    maturities: list[float] = Field(..., description="Scadenze in anni, ordinate crescente")
    par_yields: list[float] = Field(..., description="Par yield (cedola annuale) decimale, stessa lunghezza")
    frequency: int = Field(1, description="Compounding/anno per i par bond (1 o 2)")


class BootstrapOutput(BaseModel):
    maturities: list[float]
    spot_rates: list[float]
    discount_factors: list[float]
    forward_rates_1y: list[float]
    trace: dict


def bootstrap_curve(inp: BootstrapInput) -> BootstrapOutput:
    if len(inp.maturities) != len(inp.par_yields):
        raise ValueError("maturities e par_yields devono avere stessa lunghezza")
    f = inp.frequency
    Ts = list(inp.maturities)
    ys = list(inp.par_yields)
    DFs = []
    spots = []

    for i, (T, y) in enumerate(zip(Ts, ys)):
        n = int(round(T * f))
        cpn = y / f
        # Somma DF sui periodi precedenti (interpolazione lineare semplice per scadenze intermedie)
        # v0.1: assume scadenze multiple di 1/f e crescenti
        prev_pv = 0.0
        for j in range(1, n):
            tj = j / f
            # interpolazione lineare su DF su Ts noti
            if tj in [round(t, 8) for t in Ts[:i + 1]]:
                idx = [round(t, 8) for t in Ts].index(round(tj, 8))
                df_j = DFs[idx]
            else:
                # interpolazione lineare su DF tra Ts noti
                known_T = [0.0] + Ts[:i]
                known_DF = [1.0] + DFs
                df_j = float(np.interp(tj, known_T, known_DF))
            prev_pv += cpn * df_j
        df_T = (1 - prev_pv) / (1 + cpn)
        DFs.append(df_T)
        spot = (df_T ** (-1 / (T * f)) - 1) * f
        spots.append(spot)

    # Forward 1Y: f(t,t+1) = DF(t)/DF(t+1) − 1, su scadenze intere
    fwd = []
    for i in range(1, len(Ts)):
        if Ts[i] - Ts[i - 1] > 0:
            r_f = (DFs[i - 1] / DFs[i]) ** (1 / (Ts[i] - Ts[i - 1])) - 1
            fwd.append(round(r_f, 6))

    return BootstrapOutput(
        maturities=Ts,
        spot_rates=[round(s, 6) for s in spots],
        discount_factors=[round(d, 6) for d in DFs],
        forward_rates_1y=fwd,
        trace={"compounding": f"discrete x{f}/y", "interpolation": "linear on DF"},
    )


class SwapInput(BaseModel):
    notional: float = Field(..., gt=0)
    fixed_rate: float = Field(..., description="Tasso fisso pagato, decimale")
    maturities: list[float] = Field(..., description="Pagamenti in anni")
    discount_factors: list[float] = Field(..., description="DF risk-free su maturities (da bootstrap)")
    forward_rates: list[float] = Field(..., description="Forward rates floating su ciascun periodo")
    receive_fixed: bool = Field(True, description="True: receive fixed pay floating")


class SwapOutput(BaseModel):
    npv: float
    par_swap_rate: float
    pv_fixed_leg: float
    pv_float_leg: float
    trace: dict


def price_swap(inp: SwapInput) -> SwapOutput:
    if not (len(inp.maturities) == len(inp.discount_factors) == len(inp.forward_rates)):
        raise ValueError("maturities, DF, forward_rates devono avere stessa lunghezza")
    # accrual periods
    dts = [inp.maturities[0]] + [inp.maturities[i] - inp.maturities[i - 1] for i in range(1, len(inp.maturities))]
    pv_fixed = sum(inp.fixed_rate * dt * df for dt, df in zip(dts, inp.discount_factors)) * inp.notional
    pv_float = sum(fwd * dt * df for fwd, dt, df in zip(inp.forward_rates, dts, inp.discount_factors)) * inp.notional
    npv = (pv_float - pv_fixed) if inp.receive_fixed is False else (pv_fixed - pv_float)
    par = pv_float / sum(dt * df for dt, df in zip(dts, inp.discount_factors)) / inp.notional
    return SwapOutput(
        npv=round(npv, 2),
        par_swap_rate=round(par, 6),
        pv_fixed_leg=round(pv_fixed, 2),
        pv_float_leg=round(pv_float, 2),
        trace={"side": "receive_fixed" if inp.receive_fixed else "pay_fixed",
               "definition_par": "fixed rate che azzera NPV"},
    )
