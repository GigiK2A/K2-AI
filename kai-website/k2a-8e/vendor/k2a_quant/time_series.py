"""Time series — ARIMA fit/forecast + GARCH(1,1) volatility forecast."""
from __future__ import annotations
import numpy as np
from typing import Literal
from pydantic import BaseModel, Field
from scipy.optimize import minimize


class ARIMAInput(BaseModel):
    series: list[float] = Field(..., min_length=20)
    p: int = Field(1, ge=0, le=5)
    d: int = Field(0, ge=0, le=2)
    q: int = Field(0, ge=0, le=5)
    n_forecast: int = Field(5, ge=1, le=50)


class ARIMAOutput(BaseModel):
    ar_coefs: list[float]
    ma_coefs: list[float]
    intercept: float
    sigma2: float
    aic: float
    forecast: list[float]
    forecast_se: list[float]
    trace: dict


def _diff(x: np.ndarray, d: int) -> np.ndarray:
    for _ in range(d):
        x = np.diff(x)
    return x


def _undiff(forecast_diff: np.ndarray, last_levels: list[float], d: int) -> np.ndarray:
    out = forecast_diff.copy()
    for _ in range(d):
        last = last_levels.pop()
        out = np.cumsum(out) + last
    return out


def fit_arima(inp: ARIMAInput) -> ARIMAOutput:
    y = np.array(inp.series, dtype=float)
    last_levels = [y[-1]] if inp.d >= 1 else []
    if inp.d >= 2:
        last_levels.append(np.diff(y)[-1])
    x = _diff(y, inp.d)
    n = len(x)
    p, q = inp.p, inp.q

    def nll(theta):
        c = theta[0]
        phi = theta[1:1 + p]
        psi = theta[1 + p:1 + p + q]
        s2 = max(theta[-1], 1e-10)
        eps = np.zeros(n)
        for t in range(n):
            ar_part = sum(phi[i] * x[t - i - 1] for i in range(p) if t - i - 1 >= 0)
            ma_part = sum(psi[i] * eps[t - i - 1] for i in range(q) if t - i - 1 >= 0)
            eps[t] = x[t] - c - ar_part - ma_part
        return 0.5 * n * np.log(2 * np.pi * s2) + 0.5 * np.sum(eps ** 2) / s2

    n_params = 1 + p + q + 1
    theta0 = np.concatenate([[x.mean()], np.zeros(p + q), [np.var(x)]])
    res = minimize(nll, theta0, method="Nelder-Mead", options={"maxiter": 5000, "xatol": 1e-6})
    th = res.x
    c, phi, psi, s2 = th[0], th[1:1 + p].tolist(), th[1 + p:1 + p + q].tolist(), max(th[-1], 1e-10)
    aic = 2 * n_params + 2 * res.fun

    # Forecast ricorsivo (innovazioni future = 0)
    x_ext = list(x)
    eps_hist = np.zeros(n)
    # ricalcola eps con parametri finali
    for t in range(n):
        ar_part = sum(phi[i] * x[t - i - 1] for i in range(p) if t - i - 1 >= 0)
        ma_part = sum(psi[i] * eps_hist[t - i - 1] for i in range(q) if t - i - 1 >= 0)
        eps_hist[t] = x[t] - c - ar_part - ma_part

    eps_ext = list(eps_hist)
    fc = []
    for _ in range(inp.n_forecast):
        ar_part = sum(phi[i] * x_ext[-i - 1] for i in range(p))
        ma_part = sum(psi[i] * eps_ext[-i - 1] for i in range(q))
        fhat = c + ar_part + ma_part
        x_ext.append(fhat)
        eps_ext.append(0.0)
        fc.append(fhat)

    fc_arr = np.array(fc)
    if inp.d > 0:
        fc_arr = _undiff(fc_arr, last_levels[:], inp.d)
    se = [np.sqrt(s2 * (h + 1)) for h in range(inp.n_forecast)]  # approssimazione

    return ARIMAOutput(
        ar_coefs=[round(v, 6) for v in phi],
        ma_coefs=[round(v, 6) for v in psi],
        intercept=round(float(c), 6),
        sigma2=round(float(s2), 8),
        aic=round(float(aic), 4),
        forecast=[round(float(v), 6) for v in fc_arr],
        forecast_se=[round(v, 6) for v in se],
        trace={"order": f"({p},{inp.d},{q})", "n_obs_diff": n,
               "estimator": "MLE Gaussian via Nelder-Mead"},
    )


class GARCHInput(BaseModel):
    returns: list[float] = Field(..., min_length=50)
    n_forecast: int = Field(10, ge=1, le=100)


class GARCHOutput(BaseModel):
    omega: float
    alpha: float
    beta: float
    persistence: float
    long_run_variance: float
    conditional_variance_last: float
    forecast_variance: list[float]
    forecast_volatility: list[float]
    aic: float
    trace: dict


def fit_garch11(inp: GARCHInput) -> GARCHOutput:
    r = np.array(inp.returns, dtype=float)
    r = r - r.mean()
    n = len(r)

    def nll(theta):
        omega, alpha, beta = theta
        if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 0.999:
            return 1e10
        s2 = np.zeros(n)
        s2[0] = r.var()
        for t in range(1, n):
            s2[t] = omega + alpha * r[t - 1] ** 2 + beta * s2[t - 1]
        return 0.5 * np.sum(np.log(s2) + r ** 2 / s2)

    res = minimize(nll, [r.var() * 0.1, 0.08, 0.9], method="Nelder-Mead",
                   options={"maxiter": 5000, "xatol": 1e-8})
    omega, alpha, beta = res.x
    persistence = alpha + beta
    lr_var = omega / (1 - persistence) if persistence < 1 else float("inf")

    # condizionale finale
    s2 = np.zeros(n)
    s2[0] = r.var()
    for t in range(1, n):
        s2[t] = omega + alpha * r[t - 1] ** 2 + beta * s2[t - 1]

    fc = []
    s2_h = s2[-1]
    for h in range(inp.n_forecast):
        s2_h = omega + (alpha + beta) * s2_h
        fc.append(s2_h)

    aic = 2 * 3 + 2 * res.fun
    return GARCHOutput(
        omega=round(float(omega), 10),
        alpha=round(float(alpha), 6),
        beta=round(float(beta), 6),
        persistence=round(float(persistence), 6),
        long_run_variance=round(float(lr_var), 10) if lr_var != float("inf") else -1.0,
        conditional_variance_last=round(float(s2[-1]), 10),
        forecast_variance=[round(float(v), 10) for v in fc],
        forecast_volatility=[round(float(np.sqrt(v)), 8) for v in fc],
        aic=round(float(aic), 4),
        trace={"model": "GARCH(1,1) Gaussian", "stationary": persistence < 1},
    )
