"""Fama-French 3/5 factor regression — alpha, factor loadings, t-stat."""
from __future__ import annotations
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field
from .regression import OLSInput, compute_ols


class FactorInput(BaseModel):
    asset_returns: list[float] = Field(..., description="Rendimenti asset (excess se subtract_rf=False)")
    risk_free: list[float] | None = Field(None, description="Serie Rf (stessa lunghezza)")
    mkt_excess: list[float] = Field(..., description="Mkt-Rf (excess market return)")
    smb: list[float] = Field(..., description="Small Minus Big")
    hml: list[float] = Field(..., description="High Minus Low")
    rmw: list[float] | None = Field(None, description="Robust Minus Weak (5-factor)")
    cma: list[float] | None = Field(None, description="Conservative Minus Aggressive (5-factor)")
    model: Literal["ff3", "ff5"] = "ff3"
    subtract_rf: bool = True


class FactorOutput(BaseModel):
    alpha: float
    alpha_tstat: float
    alpha_pvalue: float
    loadings: dict[str, dict]
    r_squared: float
    adj_r_squared: float
    n_obs: int
    trace: dict


def compute_factor(inp: FactorInput) -> FactorOutput:
    y = np.array(inp.asset_returns, dtype=float)
    if inp.subtract_rf:
        if inp.risk_free is None or len(inp.risk_free) != len(y):
            raise ValueError("subtract_rf=True richiede risk_free di pari lunghezza")
        y = y - np.array(inp.risk_free, dtype=float)

    X_cols = [inp.mkt_excess, inp.smb, inp.hml]
    names = ["mkt_excess", "smb", "hml"]
    if inp.model == "ff5":
        if inp.rmw is None or inp.cma is None:
            raise ValueError("ff5 richiede rmw e cma")
        X_cols += [inp.rmw, inp.cma]
        names += ["rmw", "cma"]

    X = np.array(X_cols, dtype=float).T.tolist()
    ols = compute_ols(OLSInput(y=y.tolist(), X=X, feature_names=names, add_intercept=True))
    a = ols.coefficients[0]
    loads = {c.name: {"beta": c.coef, "t": c.t_stat, "p": c.p_value} for c in ols.coefficients[1:]}
    return FactorOutput(
        alpha=a.coef, alpha_tstat=a.t_stat, alpha_pvalue=a.p_value,
        loadings=loads, r_squared=ols.r_squared, adj_r_squared=ols.adj_r_squared,
        n_obs=ols.n_obs,
        trace={"model": inp.model, "y_is_excess": True, "interpretation_alpha": "Jensen's alpha (per periodo)"},
    )
