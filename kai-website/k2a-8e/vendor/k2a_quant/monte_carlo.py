"""Monte Carlo simulator generico per finanza/decision analysis."""
from __future__ import annotations
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field


class MCVariable(BaseModel):
    name: str
    distribution: Literal["normal", "lognormal", "uniform", "triangular", "beta", "discrete"]
    params: dict = Field(..., description="es. normal: {mu, sigma}; uniform: {low, high}; triangular: {low, mode, high}")


class MonteCarloInput(BaseModel):
    variables: list[MCVariable]
    expression: str = Field(..., description="Espressione Python con nomi variabili. Es: 'revenue * margin - fixed_costs'")
    n_simulations: int = Field(10000, ge=100, le=1_000_000)
    seed: int | None = 42
    percentiles: list[float] = Field(default_factory=lambda: [5, 25, 50, 75, 95])


class MonteCarloOutput(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    percentiles: dict[str, float]
    prob_negative: float
    prob_above_zero: float
    n_simulations: int
    trace: dict


_ALLOWED = {"abs", "min", "max", "round", "log", "exp", "sqrt", "sum"}


def _sample(var: MCVariable, n: int, rng: np.random.Generator) -> np.ndarray:
    p = var.params
    d = var.distribution
    if d == "normal":
        return rng.normal(p["mu"], p["sigma"], n)
    if d == "lognormal":
        return rng.lognormal(p["mu"], p["sigma"], n)
    if d == "uniform":
        return rng.uniform(p["low"], p["high"], n)
    if d == "triangular":
        return rng.triangular(p["low"], p["mode"], p["high"], n)
    if d == "beta":
        return rng.beta(p["alpha"], p["beta"], n)
    if d == "discrete":
        values = p["values"]
        probs = p.get("probs")
        return rng.choice(values, n, p=probs)
    raise ValueError(f"Distribuzione non supportata: {d}")


def simulate(inp: MonteCarloInput) -> MonteCarloOutput:
    rng = np.random.default_rng(inp.seed)
    samples = {v.name: _sample(v, inp.n_simulations, rng) for v in inp.variables}

    # Compilazione sicura: namespace ristretto
    import math
    safe_globals = {"__builtins__": {}, "np": np, **{k: getattr(math, k, getattr(np, k, None)) for k in _ALLOWED}}
    try:
        result = eval(inp.expression, safe_globals, samples)
    except Exception as e:
        raise ValueError(f"Errore nell'espressione: {e}")

    result = np.asarray(result, dtype=float)
    pct = {f"p{int(q)}": round(float(np.percentile(result, q)), 6) for q in inp.percentiles}
    return MonteCarloOutput(
        mean=round(float(result.mean()), 6),
        std=round(float(result.std()), 6),
        min=round(float(result.min()), 6),
        max=round(float(result.max()), 6),
        percentiles=pct,
        prob_negative=round(float((result < 0).mean()), 6),
        prob_above_zero=round(float((result > 0).mean()), 6),
        n_simulations=inp.n_simulations,
        trace={"expression": inp.expression,
               "variables": [v.name for v in inp.variables],
               "rng_seed": inp.seed},
    )
