"""Logistic regression via Newton-Raphson IRLS."""
from __future__ import annotations
import numpy as np
from pydantic import BaseModel, Field
from scipy import stats


class LogitInput(BaseModel):
    y: list[int] = Field(..., description="0/1 binary outcome")
    X: list[list[float]] = Field(..., description="Regressori (n × k) senza intercetta")
    feature_names: list[str] | None = None
    add_intercept: bool = True
    max_iter: int = 50
    tol: float = 1e-7


class LogitCoeff(BaseModel):
    name: str
    coef: float
    odds_ratio: float
    std_err: float
    z_stat: float
    p_value: float


class LogitOutput(BaseModel):
    coefficients: list[LogitCoeff]
    log_likelihood: float
    null_log_likelihood: float
    pseudo_r2_mcfadden: float
    aic: float
    n_obs: int
    converged: bool
    iterations: int
    trace: dict


def _sig(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))


def fit_logit(inp: LogitInput) -> LogitOutput:
    y = np.array(inp.y, dtype=float)
    if not set(np.unique(y).tolist()).issubset({0.0, 1.0}):
        raise ValueError("y deve essere binaria 0/1")
    X = np.array(inp.X, dtype=float)
    names = list(inp.feature_names) if inp.feature_names else [f"x{i+1}" for i in range(X.shape[1])]
    if inp.add_intercept:
        X = np.column_stack([np.ones(len(y)), X])
        names = ["intercept"] + names
    n, k = X.shape
    beta = np.zeros(k)
    converged = False
    for it in range(inp.max_iter):
        p = _sig(X @ beta)
        W = p * (1 - p)
        # gradient & Hessian
        grad = X.T @ (y - p)
        # Fisher information (positive-definite): I = X' W X. Newton: β += I^-1 @ grad
        I = (X.T * W) @ X
        try:
            step = np.linalg.solve(I, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(I) @ grad
        beta_new = beta + step
        if np.max(np.abs(beta_new - beta)) < inp.tol:
            beta = beta_new
            converged = True
            break
        beta = beta_new

    p = _sig(X @ beta)
    ll = float(np.sum(y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))))
    p0 = y.mean()
    ll0 = n * (p0 * np.log(p0) + (1 - p0) * np.log(1 - p0)) if 0 < p0 < 1 else 0
    pr2 = 1 - ll / ll0 if ll0 != 0 else 0
    W = p * (1 - p)
    cov = np.linalg.pinv((X.T * W) @ X)
    se = np.sqrt(np.diag(cov))
    coeffs = []
    for i, name in enumerate(names):
        b, s = float(beta[i]), float(se[i])
        z = b / s if s > 0 else 0
        pv = 2 * (1 - stats.norm.cdf(abs(z)))
        coeffs.append(LogitCoeff(
            name=name, coef=round(b, 6), odds_ratio=round(float(np.exp(b)), 6),
            std_err=round(s, 6), z_stat=round(z, 4), p_value=round(pv, 6),
        ))
    aic = 2 * k - 2 * ll
    return LogitOutput(
        coefficients=coeffs,
        log_likelihood=round(ll, 4),
        null_log_likelihood=round(float(ll0), 4),
        pseudo_r2_mcfadden=round(float(pr2), 6),
        aic=round(aic, 4),
        n_obs=n,
        converged=converged,
        iterations=it + 1,
        trace={"method": "Newton-Raphson IRLS",
               "interpretation": "exp(β) = odds ratio per unit increase"},
    )
