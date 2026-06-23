"""Hypothesis testing: t-test (one/two sample, paired), χ² indipendenza, F-test, ANOVA one-way."""
from __future__ import annotations
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field
from scipy import stats


class TTestInput(BaseModel):
    test: Literal["one_sample", "two_sample", "paired", "welch"] = "two_sample"
    sample1: list[float] = Field(..., min_length=2)
    sample2: list[float] | None = None
    mu0: float = Field(0.0, description="Solo one_sample")
    alpha: float = Field(0.05, gt=0, lt=1)
    alternative: Literal["two-sided", "greater", "less"] = "two-sided"


class TestOutput(BaseModel):
    statistic: float
    p_value: float
    df: float
    confidence_interval: list[float] | None
    reject_h0: bool
    effect_size: float | None
    trace: dict


def t_test(inp: TTestInput) -> TestOutput:
    s1 = np.array(inp.sample1, dtype=float)
    alt = inp.alternative
    if inp.test == "one_sample":
        t, p = stats.ttest_1samp(s1, inp.mu0, alternative=alt)
        df = len(s1) - 1
        se = s1.std(ddof=1) / np.sqrt(len(s1))
        tcrit = stats.t.ppf(1 - inp.alpha / 2, df)
        ci = [float(s1.mean() - tcrit * se), float(s1.mean() + tcrit * se)]
        d = (s1.mean() - inp.mu0) / s1.std(ddof=1)  # Cohen's d one-sample
    else:
        if inp.sample2 is None:
            raise ValueError(f"{inp.test} richiede sample2")
        s2 = np.array(inp.sample2, dtype=float)
        if inp.test == "paired":
            if len(s1) != len(s2):
                raise ValueError("paired: campioni di pari lunghezza")
            t, p = stats.ttest_rel(s1, s2, alternative=alt)
            diff = s1 - s2
            df = len(diff) - 1
            se = diff.std(ddof=1) / np.sqrt(len(diff))
            tcrit = stats.t.ppf(1 - inp.alpha / 2, df)
            ci = [float(diff.mean() - tcrit * se), float(diff.mean() + tcrit * se)]
            d = diff.mean() / diff.std(ddof=1)
        elif inp.test == "welch":
            t, p = stats.ttest_ind(s1, s2, equal_var=False, alternative=alt)
            # df Welch-Satterthwaite
            v1, v2 = s1.var(ddof=1), s2.var(ddof=1)
            n1, n2 = len(s1), len(s2)
            df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
            ci = None
            pooled = np.sqrt((v1 + v2) / 2)
            d = (s1.mean() - s2.mean()) / pooled if pooled > 0 else 0
        else:  # two_sample equal var
            t, p = stats.ttest_ind(s1, s2, equal_var=True, alternative=alt)
            df = len(s1) + len(s2) - 2
            pooled = np.sqrt(((len(s1) - 1) * s1.var(ddof=1) + (len(s2) - 1) * s2.var(ddof=1)) / df)
            d = (s1.mean() - s2.mean()) / pooled if pooled > 0 else 0
            ci = None
    return TestOutput(
        statistic=round(float(t), 6), p_value=round(float(p), 8),
        df=round(float(df), 4),
        confidence_interval=[round(c, 6) for c in ci] if ci else None,
        reject_h0=bool(p < inp.alpha),
        effect_size=round(float(d), 4),
        trace={"test": inp.test, "alternative": alt, "alpha": inp.alpha,
               "effect_size_type": "Cohen's d"},
    )


class ChiSquareInput(BaseModel):
    contingency_table: list[list[float]] = Field(..., description="Tabella di contingenza r×c")
    alpha: float = 0.05


def chi_square(inp: ChiSquareInput) -> TestOutput:
    table = np.array(inp.contingency_table)
    chi2, p, df, exp = stats.chi2_contingency(table)
    # Cramer's V
    n = table.sum()
    k = min(table.shape) - 1
    v = np.sqrt(chi2 / (n * k)) if n * k > 0 else 0
    return TestOutput(
        statistic=round(float(chi2), 6), p_value=round(float(p), 8),
        df=float(df), confidence_interval=None,
        reject_h0=bool(p < inp.alpha),
        effect_size=round(float(v), 4),
        trace={"test": "chi2_independence", "effect_size_type": "Cramer's V",
               "expected_min": round(float(exp.min()), 4)},
    )


class AnovaInput(BaseModel):
    groups: list[list[float]] = Field(..., min_length=2)
    alpha: float = 0.05


def anova_oneway(inp: AnovaInput) -> TestOutput:
    arrays = [np.array(g, dtype=float) for g in inp.groups]
    F, p = stats.f_oneway(*arrays)
    k = len(arrays)
    N = sum(len(a) for a in arrays)
    df_b = k - 1
    df_w = N - k
    # Eta-squared
    grand = np.concatenate(arrays).mean()
    ss_b = sum(len(a) * (a.mean() - grand) ** 2 for a in arrays)
    ss_t = sum(((a - grand) ** 2).sum() for a in arrays)
    eta2 = ss_b / ss_t if ss_t > 0 else 0
    return TestOutput(
        statistic=round(float(F), 6), p_value=round(float(p), 8),
        df=float(df_w), confidence_interval=None,
        reject_h0=bool(p < inp.alpha),
        effect_size=round(float(eta2), 4),
        trace={"test": "anova_oneway", "k_groups": k, "N": N,
               "df_between": df_b, "df_within": df_w,
               "effect_size_type": "eta-squared"},
    )
