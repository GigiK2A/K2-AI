"""Verifica SLE — freccia in testa di palo a mensola.

Schema: cantilever a sezioni variabili (tronchi), incastro al piede.
Calcolo numerico per integrazione doppia: δ(z) = ∫₀ᶻ ∫₀ˢ M(τ)/(E·I(τ)) dτ ds.

Carichi: stessi del solver_cantilever (q distribuiti, F concentrati, peso).
NB: NON applica γ — usare combinazioni SLE (rara/frequente/q.permanente) a monte.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash


from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep
from .solver_cantilever import (
    CaricoConcentrato,
    CaricoDistribuito,
    SolverInput,
    Tronco,
    _sollecitazioni_in_z,
)

E_ACCIAIO_MPa = 210000.0


class TroncoConSezione(BaseModel):
    z_base_m: float
    z_top_m: float
    I_mm4: float = Field(..., description="Momento d'inerzia alla base del tronco (z_base)")
    I_top_mm4: float | None = Field(
        None,
        description=(
            "Momento d'inerzia in testa al tronco (z_top). Se fornito → interpolazione "
            "LINEARE I(z) per palo rastremato. Se None → I costante = I_mm4."
        ),
    )


class CheckSlsInput(BaseModel):
    tronchi: list[TroncoConSezione]
    carichi_distribuiti: list[CaricoDistribuito] = Field(default_factory=list)
    carichi_concentrati: list[CaricoConcentrato] = Field(default_factory=list)
    H_totale_m: float = Field(..., description="Quota in testa palo dove valutare la freccia")
    n_passi_integrazione: int = Field(200, ge=20, le=2000)
    limite_freccia_relativo: float = Field(
        1.0 / 100.0,
        description="δ_lim / H. Default 1/100 per pali TLC (criterio iliad/Cellnex usuale)",
    )
    rotazione_max_primi: float | None = Field(
        None,
        description=(
            "Criterio LG committenza: rotazione max in testa palo [primi]. "
            "Es. iliad/Cellnex = 30' (0.5°). Se fornito → verifica η_rotazione."
        ),
    )


class CheckSlsOutput(CalcResult):
    freccia_in_testa_mm: float | None = None
    freccia_limite_mm: float | None = None
    rotazione_in_testa_gradi: float | None = None
    rotazione_in_testa_primi: float | None = None
    rotazione_limite_primi: float | None = None
    eta: float | None = None
    eta_rotazione: float | None = None
    verifica_ok: bool = False


def _I_at_z(z: float, tronchi: list[TroncoConSezione]) -> float:
    """I(z) — costante per tronco se I_top_mm4 None, altrimenti interpolazione lineare."""
    for t in tronchi:
        if t.z_base_m <= z <= t.z_top_m:
            if t.I_top_mm4 is None:
                return t.I_mm4
            # interpolazione lineare base→top
            L = t.z_top_m - t.z_base_m
            if L <= 0:
                return t.I_mm4
            xi = (z - t.z_base_m) / L
            return t.I_mm4 * (1.0 - xi) + t.I_top_mm4 * xi
    # fuori dal range: bordo più vicino
    if z > tronchi[-1].z_top_m:
        return tronchi[-1].I_top_mm4 or tronchi[-1].I_mm4
    return tronchi[0].I_mm4


def check_sls_deflection(inp: CheckSlsInput) -> CheckSlsOutput:
    out = CheckSlsOutput(tool="check_sls_deflection", inputs_hash=compute_inputs_hash(inp))

    H = inp.H_totale_m
    if H <= 0:
        raise ValueError("H_totale_m deve essere > 0.")
    if not inp.tronchi:
        raise ValueError("tronchi vuoto: geometria non definita.")
    n = inp.n_passi_integrazione
    dz = H / n

    # Costruisco un SolverInput "minimale" per riusare _sollecitazioni_in_z
    solver_inp = SolverInput(
        tronchi=[Tronco(z_base_m=t.z_base_m, z_top_m=t.z_top_m) for t in inp.tronchi],
        carichi_distribuiti=inp.carichi_distribuiti,
        carichi_concentrati=inp.carichi_concentrati,
        sezioni_di_verifica_m=[0.0],  # placeholder
    )

    # Curvatura κ(z) = M(z) / (E·I(z))
    # M(z) in kN·m, I in mm⁴, E in MPa = N/mm² → unità coerenti:
    # κ = M·1e6 [N·mm] / (E [N/mm²] · I [mm⁴]) = 1/mm
    # Doppia integrazione: θ(z) = ∫κdz, δ(z) = ∫θdz, con δ(0)=0, θ(0)=0
    # Integrazione trapezoidale.
    z_vals = [i * dz for i in range(n + 1)]
    kappa = []
    for z in z_vals:
        _, _, M_kNm = _sollecitazioni_in_z(z, solver_inp)
        I = _I_at_z(z, inp.tronchi)
        # κ in 1/mm con z in mm
        kappa.append(M_kNm * 1.0e6 / (E_ACCIAIO_MPa * I))  # 1/mm

    # θ(z): integrale di κ
    theta = [0.0] * (n + 1)
    for i in range(1, n + 1):
        theta[i] = theta[i - 1] + 0.5 * (kappa[i] + kappa[i - 1]) * (dz * 1000.0)  # dz in mm

    # δ(z): integrale di θ
    delta = [0.0] * (n + 1)
    for i in range(1, n + 1):
        delta[i] = delta[i - 1] + 0.5 * (theta[i] + theta[i - 1]) * (dz * 1000.0)

    delta_top_mm = delta[-1]
    delta_lim_mm = inp.limite_freccia_relativo * H * 1000.0
    eta = abs(delta_top_mm) / delta_lim_mm if delta_lim_mm > 0 else float("inf")

    # Rotazione in testa = θ(H) ottenuta dall'integrale di κ
    import math as _math
    theta_top_rad = abs(theta[-1])
    theta_top_deg = _math.degrees(theta_top_rad)
    theta_top_primi = theta_top_deg * 60.0

    out.freccia_in_testa_mm = delta_top_mm
    out.freccia_limite_mm = delta_lim_mm
    out.rotazione_in_testa_gradi = theta_top_deg
    out.rotazione_in_testa_primi = theta_top_primi
    out.eta = eta

    verifica_rotaz_ok = True
    if inp.rotazione_max_primi is not None:
        out.rotazione_limite_primi = inp.rotazione_max_primi
        out.eta_rotazione = theta_top_primi / inp.rotazione_max_primi
        verifica_rotaz_ok = out.eta_rotazione <= 1.0

    out.verifica_ok = (eta <= 1.0) and verifica_rotaz_ok

    out.trace.append(TraceStep(
        label="freccia in testa",
        formula="δ(H) = ∫₀ᴴ ∫₀ˢ M(τ)/(E·I(τ)) dτ ds  (integrazione trapezoidale)",
        substitution=(
            f"H={H}m, n_passi={n}, δ_top={delta_top_mm:.2f} mm, "
            f"δ_lim={delta_lim_mm:.2f} mm (H/{1.0/inp.limite_freccia_relativo:.0f})"
        ),
        value=delta_top_mm, unit="mm",
        norm_ref="NTC 2018 §4.2.4.2 — Stati limite di esercizio",
    ))
    out.trace.append(TraceStep(
        label="η SLE",
        formula="η = |δ_top| / δ_lim",
        substitution=f"= {eta:.3f} {'OK' if out.verifica_ok else 'NON VERIFICATO'}",
        value=eta, unit="-",
        norm_ref="Criterio progettuale K2A/iliad: H/100 per pali TLC",
    ))

    # Sanity rules (§12.13) — F12-W6 Stage 4
    if abs(delta_top_mm) > H * 1000.0 / 10.0:
        out.warnings.append(
            f"δ_top={delta_top_mm:.0f} mm > H/10: deflessione fisicamente eccessiva, "
            "verificare geometria/carichi (palo troppo snello o q sovrastimato)."
        )
    if delta_lim_mm > 0 and eta > 5.0:
        out.warnings.append(
            f"η={eta:.1f} > 5: verifica SLE fortemente NON soddisfatta — ridimensionare "
            "(sezione/tronchi) o rivalutare il limite δ adottato."
        )

    out.primary_value = eta
    out.primary_unit = "-"
    return out
