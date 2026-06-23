"""Verifica a fatica — EN 1993-1-9 §7 + §8.

Metodo: somma di Miner (cumulative damage).
Per ogni blocco (Δσ_i, n_i) calcola N_R(Δσ_i) e accumula D = Σ n_i/N_R,i ≤ 1.

Curva S-N standard EN 1993-1-9:
- pendenza m=3 sopra il limite di fatica costante Δσ_D (2·10⁶ cicli)
- pendenza m=5 tra Δσ_D e cut-off Δσ_L (10⁸ cicli)
- nessuna fatica sotto Δσ_L

Δσ_C = categoria del dettaglio (es. 71, 90, 125 MPa a 2·10⁶ cicli).
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash


from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep


class BloccoSpettro(BaseModel):
    delta_sigma_MPa: float = Field(..., ge=0)
    n_cicli: float = Field(..., ge=0)


class CheckFatigueInput(BaseModel):
    delta_sigma_C_MPa: float = Field(
        ...,
        description="Categoria del dettaglio EN 1993-1-9 Tab. 8.1 (es. 71, 80, 90, 125)",
    )
    spettro: list[BloccoSpettro] = Field(
        ..., description="Spettro di carico aleatorio: lista (Δσ_i, n_i)"
    )
    gamma_Mf: float = Field(
        1.35,
        description="Coefficiente parziale fatica EN 1993-1-9 Tab. 3.1 (1.00 – 1.35)",
    )
    gamma_Ff: float = Field(1.0, description="Coefficiente parziale azioni di fatica")


class CheckFatigueOutput(CalcResult):
    delta_sigma_D_MPa: float | None = None
    delta_sigma_L_MPa: float | None = None
    danneggiamento_D: float | None = None
    contributo_per_blocco: list[dict] = Field(default_factory=list)
    verifica_ok: bool = False


def _N_R(delta_sigma: float, delta_sigma_C: float, delta_sigma_D: float, delta_sigma_L: float) -> float:
    """Cicli a rottura per Δσ dato — curva trilineare EN 1993-1-9."""
    if delta_sigma <= delta_sigma_L:
        return float("inf")  # sotto cut-off, nessun danno
    if delta_sigma <= delta_sigma_D:
        # ramo m=5
        return 5e6 * (delta_sigma_D / delta_sigma) ** 5
    # ramo m=3
    return 2e6 * (delta_sigma_C / delta_sigma) ** 3


def check_fatigue(inp: CheckFatigueInput) -> CheckFatigueOutput:
    out = CheckFatigueOutput(tool="check_fatigue", inputs_hash=compute_inputs_hash(inp))

    # Limiti caratteristici (EN 1993-1-9 §7.1)
    delta_sigma_C = inp.delta_sigma_C_MPa
    delta_sigma_D = delta_sigma_C * (2.0 / 5.0) ** (1.0 / 3.0)   # ≈ 0.737·Δσ_C
    delta_sigma_L = delta_sigma_D * (5.0 / 100.0) ** (1.0 / 5.0)  # ≈ 0.549·Δσ_D
    out.delta_sigma_D_MPa = delta_sigma_D
    out.delta_sigma_L_MPa = delta_sigma_L

    out.trace.append(TraceStep(
        label="curva S-N",
        formula="Δσ_D = Δσ_C·(2/5)^(1/3) ; Δσ_L = Δσ_D·(5/100)^(1/5)",
        substitution=f"Δσ_C={delta_sigma_C} → Δσ_D={delta_sigma_D:.2f} MPa, Δσ_L={delta_sigma_L:.2f} MPa",
        value=delta_sigma_C, unit="MPa", norm_ref="EN 1993-1-9 §7 + Fig. 7.1",
    ))

    # Applico i coefficienti parziali: Δσ_i,Ed = γ_Ff·Δσ_i ; Δσ_C,Rd = Δσ_C/γ_Mf
    delta_sigma_C_d = delta_sigma_C / inp.gamma_Mf
    delta_sigma_D_d = delta_sigma_D / inp.gamma_Mf
    delta_sigma_L_d = delta_sigma_L / inp.gamma_Mf

    D = 0.0
    contributi = []
    for b in inp.spettro:
        d_sig = inp.gamma_Ff * b.delta_sigma_MPa
        N_R = _N_R(d_sig, delta_sigma_C_d, delta_sigma_D_d, delta_sigma_L_d)
        damage = b.n_cicli / N_R if N_R != float("inf") else 0.0
        D += damage
        contributi.append({
            "delta_sigma_Ed_MPa": d_sig,
            "n_cicli": b.n_cicli,
            "N_R_cicli": N_R,
            "damage": damage,
        })

    out.contributo_per_blocco = contributi
    out.danneggiamento_D = D
    out.verifica_ok = D <= 1.0

    out.trace.append(TraceStep(
        label="Miner",
        formula="D = Σ n_i / N_R,i ≤ 1.0",
        substitution=f"{len(inp.spettro)} blocchi → D = {D:.4f} "
                     f"{'OK' if out.verifica_ok else 'NON VERIFICATO'}",
        value=D, unit="-", norm_ref="EN 1993-1-9 §8.2 — eq. 8.2",
    ))

    # Sanity rules (§12.13) — F12-W3
    sum_n = sum(b.n_cicli for b in inp.spettro)
    delta_sigma_max = max((b.delta_sigma_MPa for b in inp.spettro), default=0.0)
    if sum_n <= 0:
        out.out_of_scope = True
        out.out_of_scope_reason = "spettro di fatica vuoto (Σn_i = 0): nessun ciclo da verificare."
        out.warnings.append(out.out_of_scope_reason)
    if D > 1.5:
        out.warnings.append(
            f"D={D:.2f} > 1.5: fatica NON VERIFICATA severa — rivedere dettaglio costruttivo, "
            "spessori o categoria Δσ_C."
        )
    if D < 0.01 and delta_sigma_max > delta_sigma_D:
        out.warnings.append(
            f"D={D:.4f} molto basso ma Δσ_max={delta_sigma_max:.0f} > Δσ_D={delta_sigma_D:.0f} MPa: "
            "verificare il numero di cicli n_i dello spettro."
        )
    if delta_sigma_max > 1.5 * delta_sigma_C:
        out.warnings.append(
            f"Δσ_max={delta_sigma_max:.0f} MPa > 1.5·Δσ_C={1.5 * delta_sigma_C:.0f}: tensione molto "
            "sopra la categoria — verificare validità EN 1993-1-9 (possibile regime LCF)."
        )

    out.primary_value = D
    out.primary_unit = "-"
    return out
