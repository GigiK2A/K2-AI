"""VaR ed Expected Shortfall — parametrico, storico, Monte Carlo."""
from __future__ import annotations
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field
from scipy.stats import norm


class VarInput(BaseModel):
    method: Literal["parametric", "historical", "monte_carlo"] = "parametric"
    confidence: float = Field(0.95, gt=0, lt=1, description="Es. 0.95 o 0.99")
    horizon_days: int = Field(1, ge=1)

    # parametric / monte_carlo
    portfolio_value: float | None = Field(None, description="EUR")
    mu_daily: float | None = Field(None, description="Rendimento medio giornaliero")
    sigma_daily: float | None = Field(None, description="Volatilità giornaliera")

    # historical
    returns: list[float] | None = Field(None, description="Serie rendimenti per historical")

    # monte_carlo
    n_simulations: int = Field(10000, ge=100)
    seed: int | None = 42


class VarOutput(BaseModel):
    var: float
    expected_shortfall: float
    var_pct: float
    es_pct: float
    method: str
    trace: dict


def compute_var(inp: VarInput) -> VarOutput:
    alpha = 1 - inp.confidence
    H = inp.horizon_days

    if inp.method == "parametric":
        if None in (inp.portfolio_value, inp.mu_daily, inp.sigma_daily):
            raise ValueError("parametric richiede portfolio_value, mu_daily, sigma_daily")
        z = norm.ppf(alpha)
        mu_H = inp.mu_daily * H
        sig_H = inp.sigma_daily * np.sqrt(H)
        var_ret = -(mu_H + z * sig_H)
        es_ret = -(mu_H - sig_H * norm.pdf(z) / alpha)
        var = var_ret * inp.portfolio_value
        es = es_ret * inp.portfolio_value
        trace = {"z": round(z, 4), "mu_H": round(mu_H, 6), "sigma_H": round(sig_H, 6)}

    elif inp.method == "historical":
        if not inp.returns or len(inp.returns) < 20:
            raise ValueError("historical richiede returns con ≥20 osservazioni")
        if inp.portfolio_value is None:
            raise ValueError("historical richiede portfolio_value")
        # Scale: assumiamo returns giornalieri, scaliamo con √H
        r = np.array(inp.returns)
        # Per H>1 si potrebbe bootstrappare; v0.1 usa scaling sqrt
        r_scaled = r * np.sqrt(H)
        q = np.quantile(r_scaled, alpha)
        var_ret = -q
        tail = r_scaled[r_scaled <= q]
        es_ret = -tail.mean() if len(tail) else var_ret
        var = var_ret * inp.portfolio_value
        es = es_ret * inp.portfolio_value
        trace = {"n_obs": len(r), "quantile": round(float(q), 6), "tail_size": int(len(tail))}

    else:  # monte_carlo
        if None in (inp.portfolio_value, inp.mu_daily, inp.sigma_daily):
            raise ValueError("monte_carlo richiede portfolio_value, mu_daily, sigma_daily")
        rng = np.random.default_rng(inp.seed)
        mu_H = inp.mu_daily * H
        sig_H = inp.sigma_daily * np.sqrt(H)
        sims = rng.normal(mu_H, sig_H, inp.n_simulations)
        q = np.quantile(sims, alpha)
        var_ret = -q
        tail = sims[sims <= q]
        es_ret = -tail.mean() if len(tail) else var_ret
        var = var_ret * inp.portfolio_value
        es = es_ret * inp.portfolio_value
        trace = {"n_sim": inp.n_simulations, "seed": inp.seed, "quantile": round(float(q), 6)}

    return VarOutput(
        var=round(float(var), 2),
        expected_shortfall=round(float(es), 2),
        var_pct=round(float(var_ret) * 100, 4),
        es_pct=round(float(es_ret) * 100, 4),
        method=inp.method,
        trace=trace,
    )
