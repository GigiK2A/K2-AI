"""Aderenza e lunghezza di ancoraggio barre c.a. — EC2 §8.4 + NTC §4.1.6.1.4.

Tensione di aderenza ultima (EC2 §8.4.2 eq. 8.2):
  f_bd = 2.25 · η_1 · η_2 · f_ctd
    η_1 = 1.0 (aderenza buona) | 0.7 (aderenza scarsa)
    η_2 = 1.0 (Φ ≤ 32 mm) | (132 − Φ)/100 (Φ > 32)
    f_ctd = α_ct · f_ctk,0.05 / γ_c = 0.7·f_ctm/γ_c ,  f_ctm = 0.30·f_ck^(2/3)

Lunghezza di ancoraggio base (EC2 §8.4.3 eq. 8.3):
  l_b,rqd = (Φ/4) · (σ_sd / f_bd)
Lunghezza di progetto (EC2 §8.4.4 eq. 8.4):
  l_bd = α_1·α_2·α_3·α_4·α_5 · l_b,rqd ≥ l_b,min
  l_b,min = max(0.3·l_b,rqd, 10·Φ, 100 mm)  (ancoraggi tesi)

Anchor K2A DIRETTO: foglio `30_Calcolo_fbd.md` implementa la stessa f_bd (barre "a.m" = ribbed,
con 0.83·R_ck = f_ck cilindrico). Per barre lisce K2A usa 0.36·√f_ck/γ_c (vecchia formulazione).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckRcBondInput(BaseModel):
    phi_mm: float = Field(..., gt=0, description="Diametro barra")
    f_ck_MPa: float = Field(25.0, gt=0, le=50)
    sigma_sd_MPa: float = Field(..., gt=0, description="Tensione barra da ancorare (≤ f_yd)")
    aderenza: Literal["buona", "scarsa"] = "buona"
    tipo_barra: Literal["nervata", "liscia"] = "nervata"
    alpha_prod: float = Field(
        1.0, gt=0, le=1.0,
        description="Prodotto α_1·α_2·α_3·α_4·α_5 (EC2 §8.4.4; 0.7 tipico con ganci/staffe)",
    )
    l_disponibile_mm: float | None = Field(None, description="Lunghezza disponibile (per verifica)")
    gamma_c: float = Field(1.5, gt=0)


class CheckRcBondOutput(CalcResult):
    f_ctm_MPa: float | None = None
    f_bd_MPa: float | None = None
    l_b_rqd_mm: float | None = None
    l_bd_mm: float | None = None
    l_b_min_mm: float | None = None
    eta: float | None = None
    verifica_ok: bool = True


def check_rc_bond(inp: CheckRcBondInput) -> CheckRcBondOutput:
    out = CheckRcBondOutput(tool="check_rc_bond", inputs_hash=compute_inputs_hash(inp))

    f_ctm = 0.30 * inp.f_ck_MPa ** (2.0 / 3.0)
    f_ctk = 0.7 * f_ctm
    f_ctd = f_ctk / inp.gamma_c
    out.f_ctm_MPa = f_ctm

    eta_1 = 1.0 if inp.aderenza == "buona" else 0.7
    eta_2 = 1.0 if inp.phi_mm <= 32 else (132.0 - inp.phi_mm) / 100.0

    if inp.tipo_barra == "nervata":
        f_bd = 2.25 * eta_1 * eta_2 * f_ctd
        ref_fbd = "EC2 §8.4.2 eq.8.2 (= K2A foglio 30 'a.m')"
    else:  # liscia — formulazione storica K2A foglio 30
        import math
        f_bd = 0.36 * math.sqrt(inp.f_ck_MPa) / inp.gamma_c * eta_1
        ref_fbd = "barre lisce: 0.36·√f_ck/γ_c (K2A foglio 30 'Liscie')"
    out.f_bd_MPa = f_bd

    l_b_rqd = (inp.phi_mm / 4.0) * (inp.sigma_sd_MPa / f_bd)
    l_bd = inp.alpha_prod * l_b_rqd
    l_b_min = max(0.3 * l_b_rqd, 10.0 * inp.phi_mm, 100.0)
    l_bd = max(l_bd, l_b_min)
    out.l_b_rqd_mm = l_b_rqd
    out.l_bd_mm = l_bd
    out.l_b_min_mm = l_b_min

    out.trace.append(TraceStep(
        label="f_bd",
        formula="f_bd = 2.25·η_1·η_2·f_ctd ; f_ctd = 0.7·f_ctm/γ_c",
        substitution=f"η_1={eta_1}, η_2={eta_2:.3f}, f_ctm={f_ctm:.2f}, f_ctd={f_ctd:.3f} → f_bd={f_bd:.3f} MPa",
        value=f_bd, unit="MPa", norm_ref=ref_fbd,
    ))
    out.trace.append(TraceStep(
        label="l_bd",
        formula="l_b,rqd=(Φ/4)·(σ_sd/f_bd) ; l_bd=α·l_b,rqd ≥ l_b,min=max(0.3·l_b,rqd,10Φ,100)",
        substitution=f"l_b,rqd={l_b_rqd:.0f}mm, α={inp.alpha_prod}, l_b,min={l_b_min:.0f}mm → l_bd={l_bd:.0f}mm",
        value=l_bd, unit="mm", norm_ref="EC2 §8.4.3-4 + NTC §4.1.6.1.4",
    ))

    if inp.l_disponibile_mm is not None:
        out.eta = l_bd / inp.l_disponibile_mm
        out.verifica_ok = out.eta <= 1.0
        out.trace.append(TraceStep(
            label="verifica ancoraggio",
            formula="η = l_bd / l_disponibile",
            substitution=f"l_disp={inp.l_disponibile_mm}mm → η={out.eta:.3f} {'OK' if out.verifica_ok else 'NV'}",
            value=out.eta, unit="-", norm_ref="EC2 §8.4.4",
        ))

    # Sanity rules (§12.13)
    if inp.sigma_sd_MPa > 450.0 / 1.15 + 1.0:
        out.warnings.append(
            f"σ_sd={inp.sigma_sd_MPa} MPa > f_yd (B450C≈391): verificare che non superi lo snervamento."
        )
    if out.l_bd_mm == l_b_min and inp.alpha_prod * l_b_rqd < l_b_min:
        out.warnings.append(f"l_bd governato dal minimo l_b,min={l_b_min:.0f}mm (ancoraggio corto).")
    if inp.l_disponibile_mm is not None and out.eta and out.eta > 1.0:
        out.warnings.append(
            f"l_bd={l_bd:.0f}mm > disponibile {inp.l_disponibile_mm}mm: ancoraggio insufficiente, "
            "prevedere ganci/uncini o aumentare la lunghezza."
        )

    out.primary_value = l_bd
    out.primary_unit = "mm"
    return out
