"""Impianto di terra — CEI 64-12 (Sunde) + CEI 64-8 sez.411."""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, Field


class DispersoreTerraInput(BaseModel):
    tipo: Literal["picchetto_verticale", "corda_orizzontale", "anello", "piastra"] = "picchetto_verticale"
    resistivita_suolo_ohm_m: float = 100.0
    lunghezza_m: float = Field(..., gt=0)
    diametro_mm: float = 20.0
    profondita_m: float = 0.7
    area_piastra_m2: float | None = None
    n_picchetti_paralleli: int = 1
    fattore_riduzione_parallelo: float = 0.65
    formula_corda: Literal["Tagg", "IEEE81"] = Field(
        default="Tagg",
        description=(
            "Formula per resistenza di corda interrata orizzontale (caso "
            "tipo='corda_orizzontale'). Ignorato per altri tipi. "
            "'Tagg': R = (ρ/πL)·[ln(2L²/(d·h)) − 1]. Formulazione "
            "anglosassone semplificata (Tagg 1964), più conservativa. "
            "Default per asseverazione prudenziale. "
            "'IEEE81': R = (ρ/πL)·[ln(2L/√(d·h/2)) − 1]. Da IEEE Std "
            "81-2012 Appendice B, con profondità equivalente √(d·h/2). "
            "Restituisce valori inferiori (~50%) per cavi sottili. "
            "Usare con motivazione esplicita nel PE. "
            "Entrambe le formule sono ortodosse in letterature diverse."
        ),
    )


class DispersoreTerraOutput(BaseModel):
    Re_singolo_ohm: float
    Re_totale_ohm: float
    formula_usata: str
    trace: dict


def dispersore_terra(inp: DispersoreTerraInput) -> DispersoreTerraOutput:
    rho, L, d, h = inp.resistivita_suolo_ohm_m, inp.lunghezza_m, inp.diametro_mm / 1000, inp.profondita_m
    if inp.tipo == "picchetto_verticale":
        Re = (rho / (2 * math.pi * L)) * (math.log(4 * L / d) - 1)
        f = "Re = (ρ/2πL)·(ln(4L/d)-1) [Sunde]"
    elif inp.tipo == "corda_orizzontale":
        if inp.formula_corda == "IEEE81":
            Re = (rho / (math.pi * L)) * (math.log(2 * L / math.sqrt(d * h / 2)) - 1)
            f = "IEEE 81-2012 App.B: Re = (ρ/πL)·[ln(2L/√(d·h/2)) − 1]"
        else:  # "Tagg" default conservativo
            Re = (rho / (math.pi * L)) * (math.log(2 * L ** 2 / (d * h)) - 1)
            f = "Tagg 1964 (conservativo): Re = (ρ/πL)·[ln(2L²/(d·h)) − 1]"
    elif inp.tipo == "anello":
        D = L / math.pi
        Re = (rho / (math.pi ** 2 * D)) * math.log(2 * math.pi * D / d)
        f = "Re ≈ (ρ/π²D)·ln(2πD/d)"
    elif inp.tipo == "piastra":
        if inp.area_piastra_m2 is None:
            raise ValueError("piastra: serve area_piastra_m2")
        Re = rho / (4 * math.sqrt(inp.area_piastra_m2 / math.pi))
        f = "Re = ρ/(4√(A/π))"
    else:
        raise ValueError(f"tipo: {inp.tipo}")
    Re_tot = Re / (inp.n_picchetti_paralleli * inp.fattore_riduzione_parallelo) if inp.n_picchetti_paralleli > 1 else Re
    return DispersoreTerraOutput(
        Re_singolo_ohm=round(Re, 3), Re_totale_ohm=round(Re_tot, 3), formula_usata=f,
        trace={"norma": "CEI 64-12 + IEEE Std 80", "rho_ohm_m": rho},
    )


class VerificaTerraInput(BaseModel):
    sistema: Literal["TT", "TN-S", "TN-C", "TN-C-S"] = "TT"
    RA_ohm: float | None = None
    Idn_RCD_mA: float = 30.0
    U_limite_V: float = 50.0
    Zs_ohm: float | None = None
    Ia_A: float | None = None
    U0_V: float = 230.0


class VerificaTerraOutput(BaseModel):
    sistema: str
    verifica_ok: bool
    criterio: str
    valore_calcolato: float
    valore_limite: float
    margine: float
    trace: dict


def verifica_terra(inp: VerificaTerraInput) -> VerificaTerraOutput:
    if inp.sistema == "TT":
        if inp.RA_ohm is None: raise ValueError("TT: serve RA_ohm")
        v = inp.RA_ohm * (inp.Idn_RCD_mA / 1000)
        return VerificaTerraOutput(
            sistema="TT", verifica_ok=v <= inp.U_limite_V,
            criterio=f"RA·Idn ≤ {inp.U_limite_V}V", valore_calcolato=round(v, 3),
            valore_limite=inp.U_limite_V, margine=round(inp.U_limite_V - v, 3),
            trace={"norma": "CEI 64-8 art.411.3.2.2"},
        )
    if inp.Zs_ohm is None or inp.Ia_A is None: raise ValueError("TN: servono Zs, Ia")
    v = inp.Zs_ohm * inp.Ia_A
    return VerificaTerraOutput(
        sistema=inp.sistema, verifica_ok=v <= inp.U0_V,
        criterio=f"Zs·Ia ≤ U0 ({inp.U0_V}V)", valore_calcolato=round(v, 3),
        valore_limite=inp.U0_V, margine=round(inp.U0_V - v, 3),
        trace={"norma": "CEI 64-8 art.411.4.4"},
    )
