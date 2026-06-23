"""Black-Scholes pricing europeo + greeks (Δ, Γ, Vega, Θ, ρ)."""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, Field
from scipy.stats import norm


class BlackScholesInput(BaseModel):
    spot: float = Field(..., gt=0, description="Prezzo sottostante S")
    strike: float = Field(..., gt=0, description="Strike K")
    time_to_expiry: float = Field(..., gt=0, description="T in anni (es. 0.5 = 6 mesi)")
    rate: float = Field(..., description="Risk-free continuo r, decimale")
    volatility: float = Field(..., gt=0, description="Volatilità annualizzata σ, decimale")
    dividend_yield: float = Field(0.0, description="Dividend yield continuo q")
    option_type: Literal["call", "put"] = "call"


class BlackScholesOutput(BaseModel):
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    d1: float
    d2: float
    trace: dict


def compute_black_scholes(inp: BlackScholesInput) -> BlackScholesOutput:
    S, K, T, r, sigma, q = inp.spot, inp.strike, inp.time_to_expiry, inp.rate, inp.volatility, inp.dividend_yield
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    Nd1, Nd2 = norm.cdf(d1), norm.cdf(d2)
    nd1 = norm.pdf(d1)
    disc_r = math.exp(-r * T)
    disc_q = math.exp(-q * T)

    if inp.option_type == "call":
        price = S * disc_q * Nd1 - K * disc_r * Nd2
        delta = disc_q * Nd1
        theta = (-(S * disc_q * nd1 * sigma) / (2 * sqrtT)
                 - r * K * disc_r * Nd2 + q * S * disc_q * Nd1)
        rho = K * T * disc_r * Nd2
    else:
        price = K * disc_r * norm.cdf(-d2) - S * disc_q * norm.cdf(-d1)
        delta = -disc_q * norm.cdf(-d1)
        theta = (-(S * disc_q * nd1 * sigma) / (2 * sqrtT)
                 + r * K * disc_r * norm.cdf(-d2) - q * S * disc_q * norm.cdf(-d1))
        rho = -K * T * disc_r * norm.cdf(-d2)

    gamma = disc_q * nd1 / (S * sigma * sqrtT)
    vega = S * disc_q * nd1 * sqrtT

    return BlackScholesOutput(
        price=round(price, 4),
        delta=round(delta, 4),
        gamma=round(gamma, 6),
        vega=round(vega / 100, 4),  # per 1% di vol change
        theta=round(theta / 365, 4),  # per giorno
        rho=round(rho / 100, 4),  # per 1% di rate change
        d1=round(d1, 4), d2=round(d2, 4),
        trace={
            "convention_vega": "per 1% di σ",
            "convention_theta": "per giorno (theta/365)",
            "convention_rho": "per 1% di r",
            "formula": "Black-Scholes-Merton 1973 con dividend yield q",
        },
    )
