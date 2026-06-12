"""Tool extra v0.4 — punching shear EC2 + antenna rotation HPBW."""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep


# ---------------------------------------------------------------------------
# check_punching_shear — EC2 §6.4
# ---------------------------------------------------------------------------

class CheckPunchingShearInput(BaseModel):
    """Punzonamento plinto su pilastro centrato (semplificato).

    EC2 §6.4: v_Ed = N_Ed/(u_1·d) ; v_Rd,c = C_Rd,c·k·(100·ρ_l·f_ck)^(1/3)
    u_1 = perimetro a 2d dal bordo del pilastro
    """
    N_Ed_kN: float = Field(..., description="Forza punzonante netta")
    lato_pilastro_x_mm: float = Field(..., gt=0, description="Lato pilastro/baggiolo direzione x")
    lato_pilastro_y_mm: float = Field(..., gt=0)
    altezza_utile_d_mm: float = Field(..., gt=0, description="d altezza utile della soletta/plinto")
    fck_MPa: float = Field(20.0)
    rho_l_armatura: float = Field(
        0.005, ge=0.001, le=0.02,
        description="Rapporto armatura tesa medio (default 0.5%)"
    )
    gamma_C: float = Field(1.5)


class CheckPunchingShearOutput(CalcResult):
    u_1_mm: float | None = None
    k_size_effect: float | None = None
    v_Ed_MPa: float | None = None
    v_Rd_c_MPa: float | None = None
    eta: float | None = None
    verifica_ok: bool = False


def check_punching_shear(inp: CheckPunchingShearInput) -> CheckPunchingShearOutput:
    out = CheckPunchingShearOutput(tool="check_punching_shear", inputs_hash=compute_inputs_hash(inp))
    d = inp.altezza_utile_d_mm
    # u_1 perimetro a 2d dal bordo del pilastro (rettangolo arrotondato)
    u_1 = 2 * (inp.lato_pilastro_x_mm + inp.lato_pilastro_y_mm) + 2 * math.pi * 2 * d
    # k size effect (≤ 2.0)
    k = min(1.0 + math.sqrt(200.0 / d), 2.0)
    rho = min(inp.rho_l_armatura, 0.02)
    # v_Rd,c — EC2 eq. 6.47
    C_Rd_c = 0.18 / inp.gamma_C
    v_Rd_c = C_Rd_c * k * (100 * rho * inp.fck_MPa) ** (1.0/3.0)  # MPa
    # v_min minimum (EC2 §6.4.4(1))
    v_min = 0.035 * (k ** 1.5) * math.sqrt(inp.fck_MPa)
    v_Rd_c = max(v_Rd_c, v_min)

    v_Ed = inp.N_Ed_kN * 1000.0 / (u_1 * d)  # MPa
    eta = v_Ed / v_Rd_c if v_Rd_c > 0 else float("inf")

    out.u_1_mm = u_1
    out.k_size_effect = k
    out.v_Ed_MPa = v_Ed
    out.v_Rd_c_MPa = v_Rd_c
    out.eta = eta
    out.verifica_ok = eta <= 1.0

    out.trace.append(TraceStep(
        label="punzonamento",
        formula="v_Ed = N_Ed/(u_1·d) ; v_Rd,c = (0.18/γ_C)·k·(100·ρ·f_ck)^(1/3) ≥ v_min",
        substitution=(
            f"u_1={u_1:.0f} mm, k={k:.3f}, ρ={rho:.4f} → "
            f"v_Ed={v_Ed:.3f}, v_Rd,c={v_Rd_c:.3f} MPa → η={eta:.3f}"
        ),
        value=eta, unit="-",
        norm_ref="EN 1992-1-1 §6.4 (Punching shear)",
    ))
    out.primary_value = eta
    return out


# ---------------------------------------------------------------------------
# check_antenna_rotation — rotazione SLE vs HPBW
# ---------------------------------------------------------------------------

class CheckAntennaRotationInput(BaseModel):
    """Confronta rotazione SLE alla quota dell'antenna con HPBW (Half Power
    Beam Width). Se la rotazione supera HPBW/2 − margine, il fascio "scappa"
    dal target → degrado servizio.
    """
    rotazione_quota_antenna_gradi: float = Field(
        ..., ge=0, description="Rotazione SLE alla quota dell'antenna (output check_sls_deflection)"
    )
    HPBW_orizzontale_gradi: float = Field(
        65.0, gt=0,
        description="HPBW antenna pannello tipico 65°; parabola 1°-3°",
    )
    HPBW_verticale_gradi: float = Field(
        7.0, gt=0,
        description="HPBW verticale antenna pannello tipico 7°"
    )
    margine_riserva_gradi: float = Field(
        2.0, ge=0,
        description="Margine cautelativo (puntamento, tolleranze costruttive). Default 2°"
    )
    direzione_critica: str = Field(
        "verticale",
        description="'verticale' o 'orizzontale' — verticale è il caso più stringente per pali"
    )


class CheckAntennaRotationOutput(CalcResult):
    HPBW_critico_gradi: float | None = None
    limite_rotazione_gradi: float | None = None
    eta: float | None = None
    verifica_ok: bool = False


def check_antenna_rotation(inp: CheckAntennaRotationInput) -> CheckAntennaRotationOutput:
    out = CheckAntennaRotationOutput(tool="check_antenna_rotation", inputs_hash=compute_inputs_hash(inp))
    HPBW = inp.HPBW_verticale_gradi if inp.direzione_critica == "verticale" else inp.HPBW_orizzontale_gradi
    limite = HPBW / 2.0 - inp.margine_riserva_gradi
    eta = inp.rotazione_quota_antenna_gradi / limite if limite > 0 else float("inf")
    out.HPBW_critico_gradi = HPBW
    out.limite_rotazione_gradi = limite
    out.eta = eta
    out.verifica_ok = eta <= 1.0
    out.trace.append(TraceStep(
        label="rotazione antenna",
        formula="limite = HPBW_critico/2 − margine ; η = rotazione/limite",
        substitution=(
            f"HPBW_{inp.direzione_critica}={HPBW}°, margine={inp.margine_riserva_gradi}° → "
            f"limite={limite}° ; rotazione={inp.rotazione_quota_antenna_gradi}° → η={eta:.3f}"
        ),
        value=eta, unit="-",
        norm_ref="Criterio operatore (iliad/Cellnex) + datasheet HPBW antenna",
    ))
    out.primary_value = eta
    return out
