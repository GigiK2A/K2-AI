"""Bond pricing — YTM, duration di Macaulay e modificata, convexity."""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq
from pydantic import BaseModel, Field


class BondInput(BaseModel):
    face_value: float = Field(1000.0, gt=0)
    coupon_rate: float = Field(..., description="Cedola annua, decimale (es. 0.04)")
    years_to_maturity: float = Field(..., gt=0)
    frequency: int = Field(2, description="Pagamenti/anno (1, 2, 4, 12)")
    # Specifica UNO tra price o ytm:
    price: float | None = Field(None, description="Prezzo dirty → calcola YTM")
    ytm: float | None = Field(None, description="YTM annualizzato → calcola prezzo")


class BondOutput(BaseModel):
    price: float
    ytm: float
    macaulay_duration: float
    modified_duration: float
    convexity: float
    dv01: float
    cash_flows: list[dict]
    trace: dict


def _cash_flows(face: float, c: float, T: float, f: int) -> tuple[np.ndarray, np.ndarray]:
    n = int(round(T * f))
    times = np.array([(i + 1) / f for i in range(n)])
    cpn = face * c / f
    cfs = np.full(n, cpn)
    cfs[-1] += face
    return times, cfs


def _price_from_ytm(face: float, c: float, T: float, f: int, y: float) -> float:
    times, cfs = _cash_flows(face, c, T, f)
    return float(np.sum(cfs / (1 + y / f) ** (times * f)))


def compute_bond(inp: BondInput) -> BondOutput:
    if (inp.price is None) == (inp.ytm is None):
        raise ValueError("Specifica esattamente UNO tra price e ytm")

    times, cfs = _cash_flows(inp.face_value, inp.coupon_rate, inp.years_to_maturity, inp.frequency)

    if inp.ytm is not None:
        y = inp.ytm
        P = _price_from_ytm(inp.face_value, inp.coupon_rate, inp.years_to_maturity, inp.frequency, y)
    else:
        target = inp.price
        f = lambda yy: _price_from_ytm(inp.face_value, inp.coupon_rate, inp.years_to_maturity, inp.frequency, yy) - target
        y = brentq(f, -0.5, 2.0)
        P = target

    # Macaulay duration: Σ (t × PV(CF_t)) / P
    pv = cfs / (1 + y / inp.frequency) ** (times * inp.frequency)
    mac = float(np.sum(times * pv) / P)
    mod = mac / (1 + y / inp.frequency)

    # Convexity: Σ (t² + t/f) × PV(CF_t) / P / (1+y/f)²  → forma semplificata
    convex = float(np.sum(times * (times + 1 / inp.frequency) * pv) / (P * (1 + y / inp.frequency) ** 2))

    dv01 = mod * P * 0.0001

    return BondOutput(
        price=round(P, 4),
        ytm=round(y, 6),
        macaulay_duration=round(mac, 4),
        modified_duration=round(mod, 4),
        convexity=round(convex, 4),
        dv01=round(dv01, 4),
        cash_flows=[{"t": round(float(t), 4), "cf": round(float(cf), 2)} for t, cf in zip(times, cfs)],
        trace={
            "frequency": inp.frequency,
            "n_periods": len(times),
            "dv01_definition": "ModDur × P × 0.0001 (1 bp parallel shift)",
        },
    )
