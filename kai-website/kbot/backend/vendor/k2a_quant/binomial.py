"""Cox-Ross-Rubinstein binomial tree — opzioni europee e americane (call/put)."""
from __future__ import annotations
import math
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field


class BinomialInput(BaseModel):
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    time_to_expiry: float = Field(..., gt=0)
    rate: float
    volatility: float = Field(..., gt=0)
    dividend_yield: float = 0.0
    n_steps: int = Field(200, ge=10, le=2000)
    option_type: Literal["call", "put"] = "call"
    exercise: Literal["european", "american"] = "american"


class BinomialOutput(BaseModel):
    price: float
    early_exercise_premium: float
    n_steps: int
    trace: dict


def compute_binomial(inp: BinomialInput) -> BinomialOutput:
    S, K, T, r, sig, q, N = (inp.spot, inp.strike, inp.time_to_expiry,
                              inp.rate, inp.volatility, inp.dividend_yield, inp.n_steps)
    dt = T / N
    u = math.exp(sig * math.sqrt(dt))
    d = 1 / u
    p = (math.exp((r - q) * dt) - d) / (u - d)
    disc = math.exp(-r * dt)
    if not (0 < p < 1):
        raise ValueError(f"Probabilità rischio-neutrale fuori (0,1): p={p:.4f}. Riduci dt o vol.")

    # Prezzi a scadenza
    j = np.arange(N + 1)
    ST = S * (u ** (N - j)) * (d ** j)
    if inp.option_type == "call":
        V = np.maximum(ST - K, 0.0)
    else:
        V = np.maximum(K - ST, 0.0)

    # Backward induction
    for step in range(N - 1, -1, -1):
        j = np.arange(step + 1)
        St = S * (u ** (step - j)) * (d ** j)
        V = disc * (p * V[:-1] + (1 - p) * V[1:])
        if inp.exercise == "american":
            intrinsic = (St - K) if inp.option_type == "call" else (K - St)
            V = np.maximum(V, intrinsic)

    price = float(V[0])

    # Premium = americana − europea (per confronto)
    if inp.exercise == "american":
        eu_inp = inp.model_copy(update={"exercise": "european"})
        eu_price = compute_binomial(eu_inp).price
        premium = price - eu_price
    else:
        premium = 0.0

    return BinomialOutput(
        price=round(price, 4),
        early_exercise_premium=round(premium, 4),
        n_steps=N,
        trace={"u": round(u, 6), "d": round(d, 6), "p_risk_neutral": round(p, 6), "model": "CRR"},
    )
