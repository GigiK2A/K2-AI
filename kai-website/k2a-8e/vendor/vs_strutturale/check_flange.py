"""Verifica flangia circolare bullonata — EN 1993-1-8 + formule Roark/T-stub.

Schema: palo CHS (o poligonale) saldato a flangia anulare, ancorata da n bulloni
disposti su circonferenza concentrica. Sollecitazioni N_Ed (compr.+), M_Ed, V_Ed.

Verifiche (3 fronti):
  1. Bulloni — trazione massima T_Ed,max (da N+M) vs F_t,Rd
  2. Bulloni — taglio per bullone V_Ed,b vs F_v,Rd
  3. Bulloni — combinata trazione+taglio (EN 1993-1-8 Tab. 3.4 eq. 6.1)
  4. Flangia — flessione locale (modello semplificato: mensola tra palo e bullone)

Flessione flangia — due metodi (metodo_flangia):
- "mensola" (default, cautelativo): flangia NON irrigidita, striscia di larghezza p (passo
  bulloni in circonferenza), W=p·t²/6, M_Sd=T·a. Sovrastima η per flange con nervature.
- "roark" (K2A foglio 17, richiede n_costole): piastra-tra-costole, σ=β·q·b²/t² con β3 da
  Warren Young pag.513. Realistico per flange irrigidite. Vedi decision_log/W5_check_flange_roark.md.

Limitazioni v1 (esplicitate):
- T-stub completo con prying NON implementato.
- Verifica per modo 3 (rottura bullone) sempre attiva; modo 1-2 (snervamento flangia) trattato
  con verifica flessione (mensola o Roark).
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math
from typing import Literal

from pydantic import BaseModel, Field

from .data.bulloni import BULLONI_AREE, CLASSI_BULLONI, alpha_v
from .schemas import CalcResult, TraceStep

# Tabella β Roark (Warren Young, "Roark's Formulas for Stress and Strain" pag.513),
# riprodotta dal foglio K2A 17_Flangie_Roark (righe 41-44). Modello: piastra tra due nervature
# (costole) caricata dai bulloni. Si usa β3 (riga "più cautelativa"). σ_max = β·q·b²/t².
# Verificata contro i casi numerici del foglio (a/b=1.192→β=0.727 D55; a/b=2.734→β=1.872 D42).
ROARK_AB = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
ROARK_BETA3 = [0.031, 0.126, 0.286, 0.511, 1.073, 1.568, 1.982]


def _roark_beta3(ab: float) -> float:
    """Interpolazione lineare di β3 sul rapporto di forma a/b (clamp agli estremi tabella)."""
    if ab <= ROARK_AB[0]:
        return ROARK_BETA3[0]
    if ab >= ROARK_AB[-1]:
        return ROARK_BETA3[-1]
    for i in range(len(ROARK_AB) - 1):
        x0, x1 = ROARK_AB[i], ROARK_AB[i + 1]
        if x0 <= ab <= x1:
            y0, y1 = ROARK_BETA3[i], ROARK_BETA3[i + 1]
            return y0 + (ab - x0) / (x1 - x0) * (y1 - y0)
    return ROARK_BETA3[-1]


class CheckFlangeInput(BaseModel):
    # Geometria palo
    D_palo_ext_mm: float = Field(..., description="Diametro esterno palo CHS al collegamento")
    # Geometria flangia
    D_flangia_ext_mm: float
    D_flangia_int_mm: float = Field(..., description="Tipicamente = D_palo_ext_mm")
    t_flangia_mm: float
    fy_flangia_MPa: float = 275.0
    gamma_M0: float = 1.05
    # Bulloni
    n_bulloni: int = Field(..., ge=3)
    D_cerchio_bulloni_mm: float = Field(..., description="Diametro circonferenza centri bulloni")
    designazione_bullone: str = Field(..., description="es. 'M24'")
    classe_bulloni: str = Field(..., description="es. '8.8', '10.9'")
    taglio_in_filettato: bool = Field(True, description="Se False, taglio in zona stelo (A invece di A_s)")
    gamma_M2: float = 1.25
    # Sollecitazioni di progetto
    N_Ed_kN: float = Field(0.0, description="Forza assiale, + compressione")
    M_Ed_kNm: float = 0.0
    V_Ed_kN: float = 0.0
    modalita_cautelativa: bool = Field(
        False,
        description="Se True: M_Ed × 1.10 imperfezioni + fattore vortex applicabile",
    )
    fattore_amplificazione_M_vortex: float = Field(1.0, ge=1.0, le=1.5)
    # Flessione flangia — metodo (F12-W4 W5)
    metodo_flangia: Literal["mensola", "roark"] = Field(
        "mensola",
        description=(
            "'mensola' (default, cautelativo, flangia NON irrigidita) | 'roark' (piastra tra "
            "nervature, K2A foglio 17 — richiede n_costole). Vedi K2A_VS_EN_DIVERGENCE_FINDING.md"
        ),
    )
    n_costole: int | None = Field(
        None, ge=2,
        description="Numero nervature/costole irrigidenti (richiesto se metodo_flangia='roark')",
    )


class CheckFlangeOutput(CalcResult):
    F_t_Rd_kN: float | None = None
    F_v_Rd_kN: float | None = None
    T_Ed_max_kN: float | None = None
    V_Ed_per_bullone_kN: float | None = None
    eta_trazione_bullone: float | None = None
    eta_taglio_bullone: float | None = None
    eta_combinata_bullone: float | None = None
    M_Rd_flangia_kNm_per_bullone: float | None = None
    eta_flessione_flangia: float | None = None
    # Roark (metodo_flangia='roark')
    beta_roark: float | None = None
    sigma_max_roark_MPa: float | None = None
    eta_globale: float | None = None
    verifica_ok: bool = False


def check_flange(inp: CheckFlangeInput) -> CheckFlangeOutput:
    out = CheckFlangeOutput(tool="check_flange", inputs_hash=compute_inputs_hash(inp))

    if inp.designazione_bullone not in BULLONI_AREE:
        raise ValueError(f"Bullone non in DB: {inp.designazione_bullone}")
    if inp.classe_bulloni not in CLASSI_BULLONI:
        raise ValueError(f"Classe non in DB: {inp.classe_bulloni}")

    bd = BULLONI_AREE[inp.designazione_bullone]
    cls = CLASSI_BULLONI[inp.classe_bulloni]
    A_s = bd["A_s"]
    A_nom = bd["A"]
    A_shear = A_s if inp.taglio_in_filettato else A_nom
    f_ub = cls["f_ub"]
    av = alpha_v(inp.classe_bulloni)
    n = inp.n_bulloni
    r = inp.D_cerchio_bulloni_mm / 2.0

    out.trace.append(TraceStep(
        label="bulloni",
        formula="F_t,Rd = k_2·f_ub·A_s/γ_M2 ; F_v,Rd = α_v·f_ub·A/γ_M2",
        substitution=(
            f"{n}× {inp.designazione_bullone} cl {inp.classe_bulloni}, "
            f"A_s={A_s}, f_ub={f_ub}, α_v={av}"
        ),
        value=A_s, unit="mm²", norm_ref="EN 1993-1-8 Tab. 3.4",
    ))

    # F_t,Rd, F_v,Rd per bullone
    F_t_Rd = 0.9 * f_ub * A_s / inp.gamma_M2 / 1000.0   # kN
    F_v_Rd = av * f_ub * A_shear / inp.gamma_M2 / 1000.0
    out.F_t_Rd_kN = F_t_Rd
    out.F_v_Rd_kN = F_v_Rd

    # Sollecitazione massima per bullone (modello rigido, neutral axis al centro)
    # N comprime → riduce T; M genera T_max = 2·M / (n·r)
    # Distribuzione: F_bull(θ) = N/n + (2M/(n·r))·cos(θ) (segno positivo = trazione)
    # Per la verifica si prende il bullone più sollecitato a trazione:
    # T_Ed_max = max(0, 2·M_Ed/(n·r) − N_Ed/n)
    # NB: N_Ed positivo = compressione → riduce trazione (segno meno).
    # Modalità cautelativa: amplifica M_Ed
    M_Ed_used_kNm = inp.M_Ed_kNm * inp.fattore_amplificazione_M_vortex
    if inp.modalita_cautelativa:
        M_Ed_used_kNm *= 1.10
    M_Ed_Nmm = M_Ed_used_kNm * 1.0e6
    N_Ed_N = inp.N_Ed_kN * 1.0e3
    T_per_M = 2.0 * M_Ed_Nmm / (n * r)   # N per bullone all'angolo 0
    N_per_bull = N_Ed_N / n              # compressione media (positiva)
    T_Ed_max = max(0.0, T_per_M - N_per_bull) / 1.0e3  # kN
    out.T_Ed_max_kN = T_Ed_max

    out.trace.append(TraceStep(
        label="T_Ed,max",
        formula="T_max = max(0, 2·M_Ed/(n·r) − N_Ed/n)",
        substitution=(
            f"= max(0, 2·{inp.M_Ed_kNm}·1e6/({n}·{r}) − {inp.N_Ed_kN}·1e3/{n}) = "
            f"{T_Ed_max:.2f} kN"
        ),
        value=T_Ed_max, unit="kN",
        norm_ref="Distribuzione neutral-axis al centro flangia (modello rigido)",
    ))

    # V per bullone (uniforme)
    V_per_bull = abs(inp.V_Ed_kN) / n
    out.V_Ed_per_bullone_kN = V_per_bull

    # η bullone
    eta_T = T_Ed_max / F_t_Rd
    eta_V = V_per_bull / F_v_Rd
    eta_comb = V_per_bull / F_v_Rd + T_Ed_max / (1.4 * F_t_Rd)
    out.eta_trazione_bullone = eta_T
    out.eta_taglio_bullone = eta_V
    out.eta_combinata_bullone = eta_comb

    out.trace.append(TraceStep(
        label="η bullone",
        formula="η_T = T_Ed/F_t,Rd ; η_V = V_Ed/F_v,Rd ; η_comb = V_Ed/F_v,Rd + T_Ed/(1.4·F_t,Rd)",
        substitution=(
            f"F_t,Rd={F_t_Rd:.2f} kN, F_v,Rd={F_v_Rd:.2f} kN → "
            f"η_T={eta_T:.3f}, η_V={eta_V:.3f}, η_comb={eta_comb:.3f}"
        ),
        value=eta_comb, unit="-", norm_ref="EN 1993-1-8 Tab. 3.4 eq. 6.1",
    ))

    # Flessione flangia — modello mensola anulare semplificato
    # Striscia di larghezza p = π·D_cerchio / n
    # Mensola lunga a = (D_cerchio − D_palo)/2 (distanza radiale bullone-saldatura)
    # M_Sd_flangia = T_Ed,max · a (momento al lembo interno per ciascun bullone)
    # W_strip = (p · t²) / 6
    # M_Rd_strip = W_strip · fy / γ_M0
    p = math.pi * inp.D_cerchio_bulloni_mm / n
    a = (inp.D_cerchio_bulloni_mm - inp.D_palo_ext_mm) / 2.0  # mm
    t = inp.t_flangia_mm
    if a <= 0:
        out.warnings.append("D_cerchio_bulloni ≤ D_palo: bulloni all'interno del palo, modello non applicabile.")
        a = max(a, 1.0)
    W_strip = p * t * t / 6.0   # mm³
    M_Rd = W_strip * inp.fy_flangia_MPa / inp.gamma_M0 / 1.0e6   # kN·m
    M_Sd = T_Ed_max * a / 1000.0   # kN·m (T in kN, a in mm → /1000)
    out.M_Rd_flangia_kNm_per_bullone = M_Rd
    eta_fl = M_Sd / M_Rd if M_Rd > 0 else float("inf")
    out.eta_flessione_flangia = eta_fl

    out.trace.append(TraceStep(
        label="flangia (mensola)",
        formula="p=π·D_b/n ; a=(D_b−D_palo)/2 ; W=p·t²/6 ; M_Rd=W·fy/γ_M0 ; M_Sd=T·a",
        substitution=(
            f"p={p:.1f} mm, a={a:.1f} mm, t={t} mm → "
            f"M_Rd={M_Rd:.3f} kN·m/bull, M_Sd={M_Sd:.3f} kN·m/bull, η={eta_fl:.3f}"
        ),
        value=eta_fl, unit="-",
        norm_ref="Modello mensola circolare semplificato (cautelativo; T-stub completo in v2)",
    ))

    # Metodo Roark (piastra tra nervature, K2A foglio 17) — opt-in, sovrascrive eta_fl
    if inp.metodo_flangia == "roark":
        if not inp.n_costole or inp.n_costole < 2:
            raise ValueError("metodo_flangia='roark' richiede n_costole >= 2")
        Nc = inp.n_costole
        a_roark = math.pi * inp.D_cerchio_bulloni_mm / Nc   # larghezza media piastra tra costole
        b_roark = (inp.D_flangia_ext_mm - inp.D_palo_ext_mm) / 2.0  # profondità radiale piastra
        ab = a_roark / b_roark if b_roark > 0 else float("inf")
        beta = _roark_beta3(ab)
        Ac = a_roark * b_roark   # mm²
        # Carico distribuito equivalente: trazione bulloni nel segmento tra due costole / Ac
        n_per_segmento = n / Nc
        F_segmento_N = T_Ed_max * 1.0e3 * n_per_segmento   # N (T_Ed_max in kN)
        q = F_segmento_N / Ac if Ac > 0 else 0.0           # MPa
        sigma_max = beta * q * b_roark * b_roark / (t * t)  # MPa
        sigma_d = inp.fy_flangia_MPa / inp.gamma_M0
        eta_fl = sigma_max / sigma_d if sigma_d > 0 else float("inf")
        out.eta_flessione_flangia = eta_fl
        out.beta_roark = beta
        out.sigma_max_roark_MPa = sigma_max
        out.trace.append(TraceStep(
            label="flangia (Roark, tra costole)",
            formula="a=π·D_b/Nc ; b=(D_flangia−D_palo)/2 ; β=β3(a/b) ; q=T·(n/Nc)/(a·b) ; σ=β·q·b²/t² ; η=σ/(fy/γ_M0)",
            substitution=(
                f"Nc={Nc}, a={a_roark:.1f}, b={b_roark:.1f}, a/b={ab:.3f}, β={beta:.3f}, "
                f"q={q:.3f} MPa → σ={sigma_max:.1f} MPa, σ_d={sigma_d:.1f} → η={eta_fl:.3f}"
            ),
            value=eta_fl, unit="-",
            norm_ref="Roark/Warren Young pag.513 (K2A foglio 17) — piastra tra nervature",
        ))

    eta_glob = max(eta_T, eta_V, eta_comb, eta_fl)
    out.eta_globale = eta_glob
    out.verifica_ok = eta_glob <= 1.0

    out.trace.append(TraceStep(
        label="η globale flangia",
        formula="η = max(η_T, η_V, η_comb, η_flessione_flangia)",
        substitution=f"= {eta_glob:.3f} {'OK' if out.verifica_ok else 'NON VERIFICATO'}",
        value=eta_glob, unit="-",
        norm_ref="EN 1993-1-8 + cautela flangia",
    ))

    # Sanity rules (§12.13) — F12-W4
    if not (235.0 <= inp.fy_flangia_MPa <= 460.0):
        out.warnings.append(
            f"fy_flangia={inp.fy_flangia_MPa} MPa fuori [235,460]: acciai non standard."
        )
    if eta_fl >= max(eta_T, eta_V, eta_comb) and eta_fl > 1.0:
        out.warnings.append(
            f"Collasso flangia (flessione, η={eta_fl:.2f}) governa e > 1: flangia sottodimensionata — "
            "aumentare spessore o aggiungere nervature."
        )
    if eta_fl > 1.5 and inp.metodo_flangia == "mensola":
        out.warnings.append(
            "Modello a mensola NON irrigidito (cautelativo). Per flange CON nervature usare il "
            "metodo Roark a piastra tra costole (metodo_flangia='roark' + n_costole, K2A foglio "
            "17): il presente modello sovrastima η. Vedi K2A_VS_EN_DIVERGENCE_FINDING.md."
        )
    if eta_fl > 1.0 and inp.metodo_flangia == "roark":
        out.warnings.append(
            f"Metodo Roark: η flangia={eta_fl:.2f} > 1 anche con {inp.n_costole} costole — "
            "aumentare spessore, numero costole o ridurre il passo bulloni."
        )

    out.primary_value = eta_glob
    out.primary_unit = "-"
    return out
