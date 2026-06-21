"""Game theory: Nash equilibrium in 2-player normal-form games (pure + mixed 2×2)."""
from __future__ import annotations
import numpy as np
from pydantic import BaseModel, Field


class NashInput(BaseModel):
    payoffs_player1: list[list[float]] = Field(..., description="Matrice payoff giocatore 1 (m×n)")
    payoffs_player2: list[list[float]] = Field(..., description="Matrice payoff giocatore 2 (m×n)")


class PureEquilibrium(BaseModel):
    row: int
    col: int
    payoff1: float
    payoff2: float


class MixedEquilibrium(BaseModel):
    strategy_player1: list[float]
    strategy_player2: list[float]
    expected_payoff1: float
    expected_payoff2: float


class NashOutput(BaseModel):
    pure_equilibria: list[PureEquilibrium]
    mixed_equilibrium: MixedEquilibrium | None
    dominant_strategies_p1: list[int]
    dominant_strategies_p2: list[int]
    trace: dict


def solve_nash(inp: NashInput) -> NashOutput:
    A = np.array(inp.payoffs_player1, dtype=float)
    B = np.array(inp.payoffs_player2, dtype=float)
    if A.shape != B.shape:
        raise ValueError(f"Shape mismatch: A={A.shape}, B={B.shape}")
    m, n = A.shape

    # Pure NE: per ogni cella, è il massimo della colonna per riga (A) E massimo della riga per colonna (B)
    pure = []
    for i in range(m):
        for j in range(n):
            if A[i, j] == A[:, j].max() and B[i, j] == B[i, :].max():
                pure.append(PureEquilibrium(
                    row=i, col=j,
                    payoff1=float(A[i, j]), payoff2=float(B[i, j]),
                ))

    # Strategie dominanti (strettamente)
    dom1 = [i for i in range(m) if all(
        all(A[i, j] > A[k, j] for k in range(m) if k != i) for j in range(n)
    )]
    dom2 = [j for j in range(n) if all(
        all(B[i, j] > B[i, k] for k in range(n) if k != j) for i in range(m)
    )]

    # Mixed NE solo per 2x2 (closed-form)
    mixed = None
    if m == 2 and n == 2:
        # p = prob giocatore 1 sceglie riga 0; q = prob giocatore 2 sceglie colonna 0
        # Indifferenza P2: B[0,0]*p + B[1,0]*(1-p) = B[0,1]*p + B[1,1]*(1-p)
        num_p = B[1, 1] - B[1, 0]
        den_p = B[0, 0] - B[0, 1] - B[1, 0] + B[1, 1]
        # Indifferenza P1: A[0,0]*q + A[0,1]*(1-q) = A[1,0]*q + A[1,1]*(1-q)
        num_q = A[1, 1] - A[0, 1]
        den_q = A[0, 0] - A[0, 1] - A[1, 0] + A[1, 1]
        if abs(den_p) > 1e-12 and abs(den_q) > 1e-12:
            p = num_p / den_p
            q = num_q / den_q
            if 0 < p < 1 and 0 < q < 1:
                ep1 = p * q * A[0, 0] + p * (1 - q) * A[0, 1] + (1 - p) * q * A[1, 0] + (1 - p) * (1 - q) * A[1, 1]
                ep2 = p * q * B[0, 0] + p * (1 - q) * B[0, 1] + (1 - p) * q * B[1, 0] + (1 - p) * (1 - q) * B[1, 1]
                mixed = MixedEquilibrium(
                    strategy_player1=[round(p, 6), round(1 - p, 6)],
                    strategy_player2=[round(q, 6), round(1 - q, 6)],
                    expected_payoff1=round(float(ep1), 6),
                    expected_payoff2=round(float(ep2), 6),
                )

    return NashOutput(
        pure_equilibria=pure,
        mixed_equilibrium=mixed,
        dominant_strategies_p1=dom1,
        dominant_strategies_p2=dom2,
        trace={
            "shape": f"{m}x{n}",
            "n_pure_NE": len(pure),
            "mixed_NE_method": "closed-form 2x2 indifference" if m == n == 2 else "not_computed",
        },
    )


class AuctionInput(BaseModel):
    auction_type: str = Field(..., description="first_price | second_price | english | dutch")
    private_value: float = Field(..., gt=0, description="Valutazione del bidder")
    n_bidders: int = Field(..., ge=2)
    value_distribution: str = Field("uniform", description="Per first_price: uniform [0, v_max]")
    v_max: float = Field(..., gt=0, description="Upper bound supporto valori")
    risk_neutral: bool = True


class AuctionOutput(BaseModel):
    optimal_bid: float
    expected_surplus: float
    win_probability: float
    trace: dict


def optimal_bid(inp: AuctionInput) -> AuctionOutput:
    v = inp.private_value
    N = inp.n_bidders
    if inp.auction_type in ("second_price", "english"):
        # Strategia dominante: bid = valore
        bid = v
        # Vince se altri N-1 hanno valore < v
        if inp.value_distribution == "uniform":
            win_p = (v / inp.v_max) ** (N - 1)
            # Surplus atteso: integrale dato il pricing al secondo prezzo
            exp_surplus = (v - v * (N - 1) / N) * win_p if v <= inp.v_max else 0
        else:
            win_p, exp_surplus = float("nan"), float("nan")
        trace_extra = "Strategia dominante: bidda il proprio valore"
    elif inp.auction_type in ("first_price", "dutch"):
        # Equilibrio simmetrico bidder neutrali, valore uniforme [0, v_max]: b(v) = v(N-1)/N
        if inp.value_distribution == "uniform" and inp.risk_neutral:
            bid = v * (N - 1) / N
            win_p = (v / inp.v_max) ** (N - 1)
            exp_surplus = (v - bid) * win_p
            trace_extra = "Equilibrio BNE simmetrico: b(v) = v(N-1)/N [uniforme, risk-neutral]"
        else:
            raise ValueError("Solo uniform + risk_neutral supportato v0.1")
    else:
        raise ValueError(f"auction_type non supportato: {inp.auction_type}")

    return AuctionOutput(
        optimal_bid=round(float(bid), 6),
        expected_surplus=round(float(exp_surplus), 6),
        win_probability=round(float(win_p), 6),
        trace={"auction_type": inp.auction_type, "N": N, "rule": trace_extra},
    )
