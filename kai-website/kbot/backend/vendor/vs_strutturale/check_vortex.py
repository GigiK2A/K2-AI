"""Verifica vortex shedding — CNR-DT 207/2008 §3.3 + EN 1993-3-1 Annex B.

Per pali snelli circolari (rapporto H/D > 8) il distacco alternato dei vortici
dietro al palo può causare oscillazioni trasversali in risonanza con i modi
propri della struttura. Cellnex CNP_TS21_002 lo prescrive obbligatorio.

Metodo (semplificato):
  v_cr,i = D · n_i / St                      velocità critica per modo i
  St = numero di Strouhal (≈0.18 per circolare in regime sub-critico)
  D = diametro medio rappresentativo
  n_i = frequenza propria modo i (Hz)

Confronto con velocità di progetto:
  v_m(L) = velocità media al riferimento (es. quota 0.6·H)
  Se v_cr ∈ [0.5·v_m, 1.25·v_m] → risonanza POSSIBILE → analisi amplitude
  Altrimenti → fenomeno trascurabile

Numero di Reynolds:
  Re = v_cr · D / ν,   ν ≈ 1.5e-5 m²/s aria
  Regime: subcritico Re<3e5, transcritico 3e5<Re<3e6, supercritico Re>3e6.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash


from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep

NU_ARIA = 1.5e-5  # viscosità cinematica aria [m²/s]


class CheckVortexInput(BaseModel):
    D_medio_m: float = Field(..., gt=0, description="Diametro medio rappresentativo")
    altezza_m: float = Field(..., gt=0, description="Altezza palo H")
    frequenze_proprie_Hz: list[float] = Field(
        ..., min_length=1, description="Frequenze proprie modi flessionali ortogonali al vento"
    )
    v_m_progetto_ms: float = Field(
        ...,
        description=(
            "Velocità media vento al riferimento (es. NTC §3.3 v_m(0.6·H) o quota top). "
            "Per pali TLC tipicamente 25-30 m/s."
        ),
    )
    St: float = Field(0.18, ge=0.1, le=0.25, description="Numero di Strouhal (default circolare)")
    massa_per_m_kg: float = Field(..., gt=0, description="m per unità di lunghezza")
    smorzamento_strutturale: float = Field(
        0.012, ge=0.001, le=0.05,
        description="δ_s (logaritmico) ≈ 0.012 acciaio pali, 0.030 c.a.",
    )
    rho_aria_kg_m3: float = 1.25


class CheckVortexOutput(CalcResult):
    v_cr_per_modo_ms: list[float] = Field(default_factory=list)
    Re_per_modo: list[float] = Field(default_factory=list)
    risonanza_possibile: list[bool] = Field(default_factory=list)
    n_modi_critici: int = 0
    Sc: float | None = None
    rischio: str = "BASSO"
    verifica_ok: bool = False


def check_vortex_shedding(inp: CheckVortexInput) -> CheckVortexOutput:
    out = CheckVortexOutput(tool="check_vortex_shedding", inputs_hash=compute_inputs_hash(inp))

    # Numero di Scruton: misura risposta del sistema (basso → amplitude grande)
    # Sc = 2 · m · δ_s / (ρ · D²)
    Sc = 2.0 * inp.massa_per_m_kg * inp.smorzamento_strutturale / (
        inp.rho_aria_kg_m3 * inp.D_medio_m * inp.D_medio_m
    )
    out.Sc = Sc

    out.trace.append(TraceStep(
        label="Scruton",
        formula="Sc = 2·m·δ_s/(ρ·D²)",
        substitution=(
            f"m={inp.massa_per_m_kg} kg/m, δ_s={inp.smorzamento_strutturale}, "
            f"D={inp.D_medio_m}m → Sc={Sc:.2f}"
        ),
        value=Sc, unit="-",
        norm_ref="CNR-DT 207/2008 §3.3.6 — Numero di Scruton",
    ))

    v_critiche = []
    Re_list = []
    risonanze = []
    n_critici = 0
    for n_i in inp.frequenze_proprie_Hz:
        v_cr = inp.D_medio_m * n_i / inp.St
        Re = v_cr * inp.D_medio_m / NU_ARIA
        v_critiche.append(v_cr)
        Re_list.append(Re)
        # Risonanza possibile se v_cr ∈ [0.5·v_m, 1.25·v_m]
        ris = (0.5 * inp.v_m_progetto_ms) <= v_cr <= (1.25 * inp.v_m_progetto_ms)
        risonanze.append(ris)
        if ris:
            n_critici += 1

    out.v_cr_per_modo_ms = v_critiche
    out.Re_per_modo = Re_list
    out.risonanza_possibile = risonanze
    out.n_modi_critici = n_critici

    # Valutazione rischio (EN 1993-3-1 Annex B + CNR-DT 207 §3.3.7)
    # Sc ≥ 30 → fenomeno trascurabile, Sc < 8 → critico, intermedio → da analizzare
    if n_critici == 0:
        out.rischio = "TRASCURABILE"
        out.verifica_ok = True
    elif Sc >= 30:
        out.rischio = "BASSO (Sc≥30, amplitude limitata)"
        out.verifica_ok = True
    elif Sc >= 8:
        out.rischio = "MEDIO (Sc 8-30, calcolo amplitude raccomandato)"
        out.verifica_ok = False  # va verificato con calcolo amplitude
    else:
        out.rischio = "ELEVATO (Sc<8, vibrazioni significative)"
        out.verifica_ok = False

    out.trace.append(TraceStep(
        label="vortex shedding",
        formula="v_cr,i = D·n_i/St ; risonanza se v_cr ∈ [0.5·v_m, 1.25·v_m]",
        substitution=(
            f"St={inp.St}, v_m={inp.v_m_progetto_ms} m/s → "
            f"{n_critici}/{len(v_critiche)} modi a rischio risonanza"
        ),
        value=float(n_critici), unit="modi_critici",
        norm_ref="CNR-DT 207/2008 §3.3.3 + EN 1993-3-1 Annex B",
    ))

    out.primary_value = float(n_critici)
    out.primary_unit = "modi_critici"
    return out
