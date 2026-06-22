"""Instabilità locale CHS classe 4 — area efficace A_eff (F12-W4 Stage 2).

Per sezioni tubolari circolari snelle (classe 4, d/t > 90ε²) calcola l'area efficace
ridotta secondo l'approccio semplificato EC3: si riduce l'area in modo che la snellezza
efficace rientri nel limite di classe 3.

    ρ = 1                          se d/t ≤ 90ε²   (classe ≤ 3)
    ρ = √(90ε² / (d/t))            se d/t > 90ε²   (classe 4)
    A_eff = ρ · A

ε = √(235/fy). A = π/4·(D² − (D−2t)²) (sezione anulare).

NB metodologico (F12-W4): per CHS classe 4 EN 1993-1-1 rimanda a EN 1993-1-6 (shell
buckling), già implementato in `check_tubular_stability` (χ_shell). Questo tool fornisce
l'**A_eff semplificata** complementare (utile per verifiche di resistenza a sezione).

ANCHOR K2A (foglio 14_Verifica_stabilit.md): K2A usa A_eff = 2·A/π ≈ 0.637·A come fattore
COSTANTE su TUTTE le sezioni (anche classe ≤ 3), NON una riduzione dipendente dalla
snellezza. È una convenzione legacy K2A divergente da EC3 — vedi decision log L4. Il tool
espone `method` per riprodurre la convenzione K2A quando richiesto.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckLocalBucklingInput(BaseModel):
    D_ext_mm: float = Field(..., gt=0, description="Diametro esterno")
    t_mm: float = Field(..., gt=0, description="Spessore parete")
    fy_MPa: float = Field(355.0, gt=0)
    method: Literal["EC3", "K2A"] = Field(
        "EC3",
        description="EC3 = ρ=√(90ε²/(d/t)) per classe 4; K2A = 2/π·A costante (convenzione legacy K2A foglio 14)",
    )


class CheckLocalBucklingOutput(CalcResult):
    classe: int | None = None
    d_over_t: float | None = None
    epsilon: float | None = None
    limite_classe3: float | None = None
    rho: float | None = None
    A_gross_cm2: float | None = None
    A_eff_cm2: float | None = None
    A_eff_ratio: float | None = None


def check_tubular_local_buckling(inp: CheckLocalBucklingInput) -> CheckLocalBucklingOutput:
    out = CheckLocalBucklingOutput(tool="check_tubular_local_buckling", inputs_hash=compute_inputs_hash(inp))
    D, t = inp.D_ext_mm, inp.t_mm
    eps2 = 235.0 / inp.fy_MPa
    eps = math.sqrt(eps2)
    d_over_t = D / t
    lim3 = 90.0 * eps2
    # area anulare (mm² → cm²)
    A = math.pi / 4.0 * (D**2 - (D - 2.0 * t) ** 2) / 100.0

    classe = 1 if d_over_t <= 50 * eps2 else 2 if d_over_t <= 70 * eps2 else 3 if d_over_t <= lim3 else 4

    if inp.method == "K2A":
        rho = 2.0 / math.pi  # convenzione K2A: A_eff = 2A/π costante
        norm = "Convenzione K2A (foglio 14): A_eff = 2·A/π ≈ 0.637·A (costante, non dipendente da classe)"
    else:  # EC3
        rho = 1.0 if d_over_t <= lim3 else math.sqrt(lim3 / d_over_t)
        norm = "EN 1993-1-1 §6.2.2.5 (approccio A_eff semplificato classe 4 CHS) + §5.5 Tab.5.2"

    A_eff = rho * A

    out.classe = classe
    out.d_over_t = d_over_t
    out.epsilon = eps
    out.limite_classe3 = lim3
    out.rho = rho
    out.A_gross_cm2 = A
    out.A_eff_cm2 = A_eff
    out.A_eff_ratio = rho

    out.trace.append(TraceStep(
        label="A_eff classe 4",
        formula="ρ = 1 se d/t≤90ε² ; ρ = √(90ε²/(d/t)) se classe 4 ; A_eff = ρ·A",
        substitution=(
            f"D={D} t={t} fy={inp.fy_MPa} → d/t={d_over_t:.1f}, 90ε²={lim3:.1f}, classe {classe} "
            f"→ ρ={rho:.4f}, A={A:.2f}cm², A_eff={A_eff:.2f}cm²"
        ),
        value=rho, unit="-", norm_ref=norm,
    ))

    # Sanity rules (§12.13) — F12-W4
    if rho > 1.0 + 1e-9:
        out.out_of_scope = True
        out.out_of_scope_reason = f"ρ={rho:.3f} > 1 non fisico"
        out.warnings.append(out.out_of_scope_reason)
    if inp.method == "EC3" and d_over_t <= lim3:
        out.warnings.append(
            f"d/t={d_over_t:.1f} ≤ 90ε²={lim3:.1f}: sezione classe ≤ 3, ρ=1 (tool fuori scope, "
            "A_eff = A; usare solo per classe 4)."
        )
    if rho < 0.5:
        out.warnings.append(
            f"ρ={rho:.3f} < 0.5: sezione molto snella, riduzione locale severa — considerare "
            "maggiore spessore o verifica shell buckling EN 1993-1-6 (check_tubular_stability)."
        )
    if not (235.0 <= inp.fy_MPa <= 460.0):
        out.warnings.append(f"fy={inp.fy_MPa} fuori [235,460]: ε calibrata su S235-S460.")

    out.primary_value = A_eff
    out.primary_unit = "cm²"
    return out
