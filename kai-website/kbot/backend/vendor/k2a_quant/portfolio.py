"""Markowitz mean-variance optimization — min-variance, tangency, frontiera efficiente."""
from __future__ import annotations
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field


class MarkowitzInput(BaseModel):
    expected_returns: list[float] = Field(..., description="μ_i annualizzati, decimale")
    cov_matrix: list[list[float]] = Field(..., description="Matrice covarianza Σ (n×n) annualizzata")
    risk_free: float = Field(0.0, description="Rf per tangency / Sharpe")
    allow_short: bool = Field(True, description="Se False, pesi >=0 (richiede scipy)")
    objective: Literal["min_variance", "tangency", "frontier"] = "tangency"
    n_frontier_points: int = 20


class PortfolioMetrics(BaseModel):
    weights: list[float]
    expected_return: float
    volatility: float
    sharpe: float


class MarkowitzOutput(BaseModel):
    min_variance: PortfolioMetrics
    tangency: PortfolioMetrics | None
    frontier: list[PortfolioMetrics] | None
    trace: dict


def _metrics(w: np.ndarray, mu: np.ndarray, S: np.ndarray, rf: float) -> PortfolioMetrics:
    er = float(w @ mu)
    var = float(w @ S @ w)
    vol = float(np.sqrt(max(var, 0.0)))
    sh = (er - rf) / vol if vol > 0 else 0.0
    return PortfolioMetrics(
        weights=[round(x, 6) for x in w.tolist()],
        expected_return=round(er, 6),
        volatility=round(vol, 6),
        sharpe=round(sh, 4),
    )


def _min_variance_closed(S: np.ndarray) -> np.ndarray:
    n = S.shape[0]
    ones = np.ones(n)
    inv = np.linalg.pinv(S)
    return (inv @ ones) / (ones @ inv @ ones)


def _tangency_closed(mu: np.ndarray, S: np.ndarray, rf: float) -> np.ndarray:
    inv = np.linalg.pinv(S)
    excess = mu - rf
    raw = inv @ excess
    return raw / raw.sum()


def compute_markowitz(inp: MarkowitzInput) -> MarkowitzOutput:
    mu = np.array(inp.expected_returns, dtype=float)
    S = np.array(inp.cov_matrix, dtype=float)
    n = len(mu)
    if S.shape != (n, n):
        raise ValueError(f"Cov matrix shape {S.shape} != ({n},{n})")

    if not inp.allow_short:
        try:
            from scipy.optimize import minimize
        except ImportError:
            raise ValueError("scipy required per no-short")

        cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bnds = [(0.0, 1.0)] * n
        x0 = np.ones(n) / n
        mv = minimize(lambda w: w @ S @ w, x0, constraints=cons, bounds=bnds).x
        tan = minimize(
            lambda w: -(w @ mu - inp.risk_free) / np.sqrt(max(w @ S @ w, 1e-12)),
            x0, constraints=cons, bounds=bnds,
        ).x
    else:
        mv = _min_variance_closed(S)
        tan = _tangency_closed(mu, S, inp.risk_free)

    mv_metrics = _metrics(mv, mu, S, inp.risk_free)
    tan_metrics = _metrics(tan, mu, S, inp.risk_free)

    frontier = None
    if inp.objective == "frontier":
        target_returns = np.linspace(mu.min(), mu.max(), inp.n_frontier_points)
        ones = np.ones(n)
        inv = np.linalg.pinv(S)
        A = ones @ inv @ ones
        B = ones @ inv @ mu
        C = mu @ inv @ mu
        D = A * C - B * B
        frontier = []
        for tr in target_returns:
            lam = (C - tr * B) / D
            gam = (tr * A - B) / D
            w = inv @ (lam * ones + gam * mu)
            frontier.append(_metrics(w, mu, S, inp.risk_free))

    return MarkowitzOutput(
        min_variance=mv_metrics,
        tangency=tan_metrics,
        frontier=frontier,
        trace={
            "method": "closed-form" if inp.allow_short else "scipy SLSQP no-short",
            "n_assets": n,
            "risk_free": inp.risk_free,
        },
    )
