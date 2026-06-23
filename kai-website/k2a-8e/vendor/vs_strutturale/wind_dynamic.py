"""Fattore CsCd dinamico — EN 1991-1-4 Annex B Procedure 1.

Per pali TLC snelli, il c_d statico = 1.0 è cautelativo verso il basso (errato a
sfavore della verifica). EN 1991-1-4 Annex B Procedure 1 calcola il vero
CsCd in funzione di:
  - turbolenza I_v(z_s)
  - fattore di sfondo B² (dimensioni struttura vs scala di turbolenza)
  - fattore risonante R² (frequenza propria vs spettro di Davenport)
  - smorzamento totale δ
  - fattore di picco k_p

Formula (eq. B.2):
  CsCd = (1 + 2·k_p·I_v(z_s)·√(B² + R²)) / (1 + 7·I_v(z_s))

Per pali TLC tipici (H=20-30m, n_1=1.5-2.5 Hz):
  CsCd attesi 1.05 - 1.20
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep


# Costanti EN 1991-1-4
L_T = 300.0    # m — scala di turbolenza al riferimento z_t=200m
Z_T = 200.0    # m — altezza riferimento
T_OBS = 600.0  # s — durata raffica
K_L_DEFAULT = 1.0
C_O_DEFAULT = 1.0


class WindDynamicFactorInput(BaseModel):
    altezza_riferimento_z_s_m: float = Field(
        ..., gt=0,
        description="z_s = riferimento (EN 1991-1-4 §6.3.1.2): tipicamente 0.6·H per cantilever"
    )
    velocita_media_z_s_ms: float = Field(
        ..., gt=0,
        description="v_m(z_s) = velocità media a z_s. Es: v_m = v_b · c_r(z_s)"
    )
    altezza_struttura_m: float = Field(..., gt=0)
    larghezza_struttura_m: float = Field(..., gt=0, description="b = larghezza al vento (D palo)")
    frequenza_propria_n1_Hz: float = Field(
        ..., gt=0,
        description="n_1 = freq. fondamentale flessionale ortogonale al vento"
    )
    z_0_m: float = Field(
        0.05,
        description="z_0 = lunghezza di rugosità (cat. esposizione II=0.05)"
    )
    smorzamento_totale_log: float = Field(
        0.05,
        ge=0.005, le=0.20,
        description=(
            "δ totale = δ_s (struttura) + δ_a (aerodinamico) + δ_d (special). "
            "Acciaio pali tipico δ = 0.05 (5%)"
        ),
    )
    k_l: float = Field(K_L_DEFAULT, description="Fattore turbolenza (1.0 default)")
    c_o: float = Field(C_O_DEFAULT, description="Fattore orografia (1.0 in pianura)")


class WindDynamicFactorOutput(CalcResult):
    I_v_z_s: float | None = None
    L_z_s_m: float | None = None
    B_squared: float | None = None
    R_squared: float | None = None
    S_L: float | None = None
    n_aux_Hz: float | None = None
    k_p: float | None = None
    Cs_factor: float | None = None
    Cd_factor: float | None = None
    CsCd: float | None = None


def compute_wind_dynamic_factor(inp: WindDynamicFactorInput) -> WindDynamicFactorOutput:
    """CsCd EN 1991-1-4 Annex B (procedimento 1)."""
    out = WindDynamicFactorOutput(tool="wind_dynamic_factor", inputs_hash=compute_inputs_hash(inp))
    z_s = inp.altezza_riferimento_z_s_m
    v_m = inp.velocita_media_z_s_ms
    h = inp.altezza_struttura_m
    b = inp.larghezza_struttura_m

    # 1. Turbolenza I_v(z_s) (eq. 4.7)
    I_v = inp.k_l / (inp.c_o * math.log(z_s / inp.z_0_m))
    out.I_v_z_s = I_v

    # 2. Scala turbolenza L(z_s) (eq. B.1)
    alpha_L = 0.67 + 0.05 * math.log(inp.z_0_m)
    L_zs = L_T * (z_s / Z_T) ** alpha_L
    out.L_z_s_m = L_zs

    # 3. Fattore di sfondo B² (eq. B.3)
    B2 = 1.0 / (1.0 + 0.9 * ((b + h) / L_zs) ** 0.63)
    out.B_squared = B2

    # 4. Spettro non-dim. S_L (eq. B.2)
    f_L = inp.frequenza_propria_n1_Hz * L_zs / v_m
    S_L = 6.8 * f_L / ((1.0 + 10.2 * f_L) ** (5.0 / 3.0))
    out.S_L = S_L

    # 5. Aerodynamic admittance R_h, R_b (eq. B.7)
    def R_n(eta: float) -> float:
        if eta <= 0:
            return 1.0
        return (1.0 / eta) - (1.0 / (2.0 * eta * eta)) * (1.0 - math.exp(-2.0 * eta))

    eta_h = 4.6 * h / L_zs * f_L
    eta_b = 4.6 * b / L_zs * f_L
    R_h = R_n(eta_h)
    R_b = R_n(eta_b)

    # 6. Fattore risonante R² (eq. B.6)
    R2 = (math.pi ** 2 / (2.0 * inp.smorzamento_totale_log)) * S_L * R_h * R_b
    out.R_squared = R2

    # 7. Frequenza media v_aux (eq. B.5) e fattore di picco k_p (eq. B.4)
    n_aux = inp.frequenza_propria_n1_Hz * math.sqrt(R2 / (B2 + R2))
    out.n_aux_Hz = n_aux
    # k_p = max( sqrt(2·ln(ν·T)) + 0.6/sqrt(2·ln(ν·T)), 3 )
    arg = max(2.0 * math.log(n_aux * T_OBS), 1e-3)
    k_p = max(math.sqrt(arg) + 0.6 / math.sqrt(arg), 3.0)
    out.k_p = k_p

    # 8. Cs e Cd separati (eq. B.8-B.9)
    Cs = (1.0 + 7.0 * I_v * math.sqrt(B2)) / (1.0 + 7.0 * I_v)
    Cd = (1.0 + 2.0 * k_p * I_v * math.sqrt(B2 + R2)) / (1.0 + 7.0 * I_v * math.sqrt(B2))
    # CsCd combinato (eq. B.2)
    CsCd = (1.0 + 2.0 * k_p * I_v * math.sqrt(B2 + R2)) / (1.0 + 7.0 * I_v)
    out.Cs_factor = Cs
    out.Cd_factor = Cd
    out.CsCd = CsCd

    out.trace.append(TraceStep(
        label="parametri turbolenza",
        formula="I_v = k_l/(c_o·ln(z_s/z_0)) ; L(z_s) = L_t·(z_s/z_t)^α_L",
        substitution=f"z_s={z_s}m, z_0={inp.z_0_m}m → I_v={I_v:.4f}, L={L_zs:.1f}m",
        value=I_v, unit="-",
        norm_ref="EN 1991-1-4 §4.4 + Annex B eq. B.1",
    ))
    out.trace.append(TraceStep(
        label="fattori B² e R²",
        formula="B²=1/(1+0.9·((b+h)/L)^0.63) ; R²=(π²/(2δ))·S_L·R_h·R_b",
        substitution=(
            f"B²={B2:.4f}, S_L={S_L:.4f}, R_h={R_h:.3f}, R_b={R_b:.3f}, "
            f"δ={inp.smorzamento_totale_log} → R²={R2:.3f}"
        ),
        value=R2, unit="-",
        norm_ref="EN 1991-1-4 Annex B eq. B.3, B.5, B.6, B.7",
    ))
    out.trace.append(TraceStep(
        label="CsCd",
        formula="CsCd = (1 + 2·k_p·I_v·√(B²+R²)) / (1 + 7·I_v)",
        substitution=(
            f"k_p={k_p:.3f}, I_v={I_v:.4f}, √(B²+R²)={math.sqrt(B2+R2):.3f} → "
            f"Cs={Cs:.4f}, Cd={Cd:.4f}, CsCd={CsCd:.4f}"
        ),
        value=CsCd, unit="-",
        norm_ref="EN 1991-1-4 Annex B Procedure 1 eq. B.2/B.8/B.9",
    ))
    # Sanity rules (§12.13) — F12-W3
    if not (0.85 <= CsCd <= 2.5):
        out.warnings.append(
            f"CsCd={CsCd:.3f} fuori range atteso [0.85, 2.5]: verificare n_1, smorzamento e "
            "geometria (possibile input incoerente)."
        )
    if h > 50.0:
        out.out_of_scope = True
        out.out_of_scope_reason = (
            f"H={h}m oltre perimetro validato v1 (≤50m). EN 1991-1-4 Annex B Procedure 1 "
            "resta applicabile ma il risultato è fuori dal range di calibrazione goldens L2."
        )
        out.warnings.append(out.out_of_scope_reason)
    if inp.frequenza_propria_n1_Hz < 0.2:
        out.warnings.append(
            f"n_1={inp.frequenza_propria_n1_Hz} Hz molto bassa: struttura molto flessibile, "
            "contributo risonante R² dominante — verificare analisi modale."
        )

    out.primary_value = CsCd
    out.primary_unit = "-"
    return out
