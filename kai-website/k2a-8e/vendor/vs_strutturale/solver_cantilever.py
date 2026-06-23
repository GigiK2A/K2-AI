"""Solver sollecitazioni — palo a mensola (incastro al piede, libero in testa).

Schema statico: asta verticale incastrata in z=0, libera in z=H.
Asse z verticale, verso l'alto. Forza vento orizzontale lungo +x (cautelativa).

Carichi gestiti:
  - q(z) vento DISTRIBUITO per tronco (carico per unità di lunghezza, kN/m, orizzontale)
  - F_h_i concentrate orizzontali (antenne) a quota z_i
  - F_v_i concentrate verticali (peso antenne) a quota z_i, ECCENTRICITÀ e_i possibile
  - peso proprio dei tronchi (kN/m verticale)

Output (per ciascuna sezione di verifica z_s):
  - N(z_s)  forza assiale di compressione (kN, positivo se comprime)
  - V(z_s)  taglio orizzontale (kN)
  - M(z_s)  momento flettente attorno all'asse y (kN·m)

Convenzione: sezione "tagliata", si considerano le forze SOPRA la sezione.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash


from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep


class Tronco(BaseModel):
    z_base_m: float
    z_top_m: float
    peso_kN_per_m: float = Field(0.0, description="Peso proprio per unità di lunghezza")


class CaricoDistribuito(BaseModel):
    z_base_m: float
    z_top_m: float
    q_orizz_kN_m: float = Field(..., description="Vento orizzontale per unità di lunghezza")


class CaricoConcentrato(BaseModel):
    z_m: float
    F_h_kN: float = 0.0
    F_v_kN: float = 0.0
    eccentricita_m: float = Field(0.0, description="Eccentricità di F_v rispetto all'asse palo")
    M_aggiuntivo_kNm: float = 0.0


class SolverInput(BaseModel):
    tronchi: list[Tronco]
    carichi_distribuiti: list[CaricoDistribuito] = Field(default_factory=list)
    carichi_concentrati: list[CaricoConcentrato] = Field(default_factory=list)
    sezioni_di_verifica_m: list[float] = Field(..., description="Quote z dove valutare N/V/M")


class SollecitazioniSezione(BaseModel):
    z_m: float
    N_kN: float
    V_kN: float
    M_kNm: float


class SolverOutput(CalcResult):
    sezioni: list[SollecitazioniSezione] = Field(default_factory=list)
    sezione_critica_M: SollecitazioniSezione | None = None


def _sollecitazioni_in_z(z_s: float, inp: SolverInput) -> tuple[float, float, float]:
    """Calcola (N, V, M) alla quota z_s sommando tutto ciò che sta SOPRA z_s."""
    N = 0.0
    V = 0.0
    M = 0.0

    # 1. Peso proprio tronchi (vertical → N), eccentricità nulla → no M aggiuntivo
    for t in inp.tronchi:
        if t.z_top_m <= z_s:
            continue  # tutto sotto la sezione, salta
        # Porzione di tronco SOPRA z_s
        z_b = max(t.z_base_m, z_s)
        z_t = t.z_top_m
        if z_t > z_b:
            L = z_t - z_b
            N += t.peso_kN_per_m * L

    # 2. Carichi distribuiti vento (orizzontali) → V e M
    for c in inp.carichi_distribuiti:
        if c.z_top_m <= z_s:
            continue
        z_b = max(c.z_base_m, z_s)
        z_t = c.z_top_m
        if z_t > z_b:
            L = z_t - z_b
            F = c.q_orizz_kN_m * L
            V += F
            # Braccio: distanza dal baricentro del tratto a z_s
            z_baric = 0.5 * (z_b + z_t)
            M += F * (z_baric - z_s)

    # 3. Carichi concentrati
    for cc in inp.carichi_concentrati:
        if cc.z_m <= z_s:
            continue
        N += cc.F_v_kN
        V += cc.F_h_kN
        # M: contributo F_h · braccio verticale + F_v · eccentricità + M_aggiuntivo
        M += cc.F_h_kN * (cc.z_m - z_s)
        M += cc.F_v_kN * cc.eccentricita_m
        M += cc.M_aggiuntivo_kNm

    return N, V, M


def solve_cantilever(inp: SolverInput) -> SolverOutput:
    """Risolve un palo a mensola e restituisce N, V, M per ogni sezione."""
    out = SolverOutput(tool="solver_cantilever", inputs_hash=compute_inputs_hash(inp))

    # Validazione geometrica
    if not inp.tronchi:
        raise ValueError("Almeno un tronco richiesto")
    z_max_struct = max(t.z_top_m for t in inp.tronchi)
    for z_s in inp.sezioni_di_verifica_m:
        if z_s < 0 or z_s > z_max_struct:
            out.warnings.append(
                f"Sezione z={z_s}m fuori dal range struttura [0, {z_max_struct}m]"
            )

    sezioni: list[SollecitazioniSezione] = []
    for z_s in inp.sezioni_di_verifica_m:
        N, V, M = _sollecitazioni_in_z(z_s, inp)
        sezioni.append(SollecitazioniSezione(z_m=z_s, N_kN=N, V_kN=V, M_kNm=M))

    out.sezioni = sezioni
    if sezioni:
        out.sezione_critica_M = max(sezioni, key=lambda s: abs(s.M_kNm))

    out.trace.append(TraceStep(
        label="solver mensola",
        formula=(
            "N(z) = Σ peso_proprio_sopra + Σ F_v_concentrate_sopra ; "
            "V(z) = Σ q·L_sopra + Σ F_h_concentrate_sopra ; "
            "M(z) = Σ q·L·braccio_baric + Σ F_h·(z_i−z) + Σ F_v·e + Σ M_locali"
        ),
        substitution=(
            f"{len(inp.tronchi)} tronchi, {len(inp.carichi_distribuiti)} carichi distrib, "
            f"{len(inp.carichi_concentrati)} concentrati, "
            f"{len(inp.sezioni_di_verifica_m)} sezioni di verifica"
        ),
        value=out.sezione_critica_M.M_kNm if out.sezione_critica_M else 0.0,
        unit="kN·m",
        norm_ref="Statica — equilibrio mensola, integrazione top-down",
    ))

    # Sanity rules (§12.13) — F12-W3. Valutate alla base z=0 (sollecitazioni massime
    # per mensola). NB: la regola M_base/(W_min·f_yk) richiede la geometria di sezione
    # (D, t) che questo tool NON possiede → appartiene a `check_tubular_resistance`.
    N0, V0, M0 = _sollecitazioni_in_z(0.0, inp)
    if N0 < -1e-6:
        out.warnings.append(
            f"N_base={N0:.2f} kN < 0 (trazione netta alla base): verificare pesi/carichi — "
            "un palo TLC autoportante è atteso in compressione alla base."
        )
    if abs(N0) > 1e-6 and abs(V0) / abs(N0) > 5.0:
        out.warnings.append(
            f"|V_base|/N_base = {abs(V0) / abs(N0):.1f} > 5: rapporto taglio/normale anomalo, "
            "verificare input carichi."
        )

    if out.sezione_critica_M:
        out.primary_value = out.sezione_critica_M.M_kNm
        out.primary_unit = "kN·m"

    return out
