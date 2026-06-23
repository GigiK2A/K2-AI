"""OLS regression con diagnostica (R², t-stat, p-value, VIF)."""
from __future__ import annotations
import numpy as np
from pydantic import BaseModel, Field
from scipy import stats


class OLSInput(BaseModel):
    y: list[float] = Field(..., min_length=3, description="Variabile dipendente")
    X: list[list[float]] = Field(..., description="Matrice regressori (n × k), senza intercetta")
    feature_names: list[str] | None = None
    add_intercept: bool = True


class OLSCoeff(BaseModel):
    name: str
    coef: float
    std_err: float
    t_stat: float
    p_value: float
    ci_low_95: float
    ci_high_95: float


class OLSOutput(BaseModel):
    coefficients: list[OLSCoeff]
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    f_pvalue: float
    residual_std_error: float
    n_obs: int
    df_residual: int
    vif: dict[str, float] | None
    trace: dict


def compute_ols(inp: OLSInput) -> OLSOutput:
    y = np.array(inp.y, dtype=float)
    X = np.array(inp.X, dtype=float)
    if X.ndim != 2 or X.shape[0] != len(y):
        raise ValueError(f"X shape {X.shape} non compatibile con y len {len(y)}")

    names = list(inp.feature_names) if inp.feature_names else [f"x{i+1}" for i in range(X.shape[1])]
    if inp.add_intercept:
        X = np.column_stack([np.ones(len(y)), X])
        names = ["intercept"] + names

    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    y_hat = X @ beta
    resid = y - y_hat
    rss = float(resid @ resid)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - rss / tss if tss > 0 else 0.0
    df_res = n - k
    adj_r2 = 1 - (1 - r2) * (n - 1) / df_res if df_res > 0 else 0.0
    sigma2 = rss / df_res if df_res > 0 else 0.0
    se = np.sqrt(np.diag(XtX_inv) * sigma2)

    coeffs = []
    for i, name in enumerate(names):
        b, s = float(beta[i]), float(se[i])
        t = b / s if s > 0 else 0.0
        p = 2 * (1 - stats.t.cdf(abs(t), df_res)) if df_res > 0 else 1.0
        tcrit = stats.t.ppf(0.975, df_res) if df_res > 0 else 0
        coeffs.append(OLSCoeff(
            name=name, coef=round(b, 6), std_err=round(s, 6),
            t_stat=round(t, 4), p_value=round(p, 6),
            ci_low_95=round(b - tcrit * s, 6), ci_high_95=round(b + tcrit * s, 6),
        ))

    # F-stat (overall): testa β_1..β_{k-1}=0 escludendo intercetta
    k_reg = k - 1 if inp.add_intercept else k
    if k_reg > 0 and df_res > 0 and tss > 0 and r2 < 1 - 1e-12:
        f_stat = (r2 / k_reg) / ((1 - r2) / df_res)
        f_p = 1 - stats.f.cdf(f_stat, k_reg, df_res)
    elif r2 >= 1 - 1e-12:
        f_stat, f_p = float("inf"), 0.0
    else:
        f_stat, f_p = 0.0, 1.0

    # VIF per ogni regressore (escl. intercetta)
    vif = None
    if inp.add_intercept and X.shape[1] > 2:
        vif = {}
        for j in range(1, X.shape[1]):
            others = np.delete(X, j, axis=1)
            xj = X[:, j]
            b_aux = np.linalg.pinv(others.T @ others) @ others.T @ xj
            r2_j = 1 - ((xj - others @ b_aux) ** 2).sum() / ((xj - xj.mean()) ** 2).sum()
            vif[names[j]] = round(1 / (1 - r2_j) if r2_j < 1 else float("inf"), 3)

    return OLSOutput(
        coefficients=coeffs,
        r_squared=round(r2, 6),
        adj_r_squared=round(adj_r2, 6),
        f_statistic=round(f_stat, 4),
        f_pvalue=round(f_p, 6),
        residual_std_error=round(float(np.sqrt(sigma2)), 6),
        n_obs=n,
        df_residual=df_res,
        vif=vif,
        trace={
            "method": "OLS closed-form pinv(X'X)X'y",
            "intercept_included": inp.add_intercept,
            "vif_warning_threshold": 5,
        },
    )
