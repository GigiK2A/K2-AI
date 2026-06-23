"""Riduzione resistenza shell EN 1993-1-6 per sezioni circolari cave classe 4.

Approccio standard pali TLC poligonali/circolari snelli (d/t > 90·ε²).
Quando la sezione è classe 4 secondo EN 1993-1-1, le resistenze N_pl,Rd e M_pl,Rd
vanno ridotte per imbozzamento locale del guscio (shell buckling).

Formulazione: EN 1993-1-6 §8.5 + §D.1 (Annex D — Express formulae for shell
buckling stress design).

Per cilindro lungo sotto compressione meridiana:
  σ_x,Rcr = 0.605 · E · C_x · t / r          (eq. D.4)  con C_x = 1 (lungo)
  λ̄_x   = √(f_yk / σ_x,Rcr)                  (slenderness shell)

Curva di buckling (eq. 8.16-8.18):
  χ = 1                                       se λ̄ ≤ λ̄_0
  χ = 1 − β · ((λ̄ − λ̄_0)/(λ̄_p − λ̄_0))^η    se λ̄_0 < λ̄ < λ̄_p
  χ = α / λ̄²                                  se λ̄ ≥ λ̄_p

Parametri standard per CHS (EN 1993-1-6 Tab. D.1):
  λ̄_0 = 0.20 ; β = 0.60 ; η = 1.0 ; λ̄_p = √(α / (1 − β))

α dipende dalla classe di qualità di fabbricazione (EN 1993-1-6 Tab. D.2):
  Class A — Excellent  :  α = 0.83
  Class B — High        :  α = 0.62  ← default pali TLC saldati standard
  Class C — Normal      :  α = 0.42

NB: pali poligonali sono approssimabili a CHS equivalente, ma con
fattore di riduzione lieve aggiuntivo (-5 / -10%) per le saldature longitudinali.
"""

from __future__ import annotations

import math
from typing import Literal

E_ACCIAIO_MPa = 210_000.0

# Parametri α_x per classe di qualità — EN 1993-1-6 Tab. D.2
ALPHA_X_QUALITY: dict[str, float] = {
    "A": 0.83,
    "B": 0.62,
    "C": 0.42,
}
LAMBDA_0 = 0.20
BETA = 0.60
ETA = 1.0


def chi_shell_circular(
    D_mm: float, t_mm: float, fy_MPa: float,
    quality: Literal["A", "B", "C"] = "B",
    additional_imperfection: float = 1.0,
    is_poligonale: bool = False,
) -> dict:
    """Coefficiente di riduzione χ per CHS / palo poligonale in compressione assiale.

    Parameters
    ----------
    D_mm : float
        Diametro medio (D − t) della sezione tubolare (o diametro equivalente poligonale)
    t_mm : float
        Spessore
    fy_MPa : float
        Tensione di snervamento caratteristica
    quality : "A"|"B"|"C"
        Classe di qualità EN 1993-1-6
    additional_imperfection : float
        Penalizzazione aggiuntiva per geometria non perfetta
    is_poligonale : bool
        Se True, applica riduzione α × 0.85 (EN 1993-3-1 Annex A — pali poligonali
        saldati longitudinalmente sono +imperfetti di CHS laminato a caldo).

    Returns
    -------
    dict con: sigma_x_Rcr, lambda_bar_x, lambda_bar_p, chi, alpha_x_used,
              regime, riduzione_poligonale_applicata
    """
    if quality not in ALPHA_X_QUALITY:
        raise ValueError(f"quality must be A/B/C, got '{quality}'")
    r = (D_mm - t_mm) / 2.0   # raggio medio
    # Tensione critica elastica (cilindro lungo, C_x = 1)
    sigma_x_Rcr = 0.605 * E_ACCIAIO_MPa * t_mm / r * additional_imperfection
    lambda_bar_x = math.sqrt(fy_MPa / sigma_x_Rcr)
    alpha_x_base = ALPHA_X_QUALITY[quality]
    # Penalizzazione poligonale (EN 1993-3-1 Annex A — saldature longitudinali)
    poligonale_factor = 0.85 if is_poligonale else 1.0
    alpha_x = alpha_x_base * poligonale_factor
    lambda_bar_p = math.sqrt(alpha_x / (1.0 - BETA))

    if lambda_bar_x <= LAMBDA_0:
        chi = 1.0
        regime = "plateau"
    elif lambda_bar_x < lambda_bar_p:
        chi = 1.0 - BETA * ((lambda_bar_x - LAMBDA_0) / (lambda_bar_p - LAMBDA_0)) ** ETA
        regime = "elasto_plastico"
    else:
        chi = alpha_x / (lambda_bar_x ** 2)
        regime = "elastico_puro"

    return {
        "sigma_x_Rcr_MPa": sigma_x_Rcr,
        "lambda_bar_x": lambda_bar_x,
        "lambda_bar_p": lambda_bar_p,
        "alpha_x": alpha_x,
        "alpha_x_base": alpha_x_base,
        "poligonale_factor": poligonale_factor,
        "chi": chi,
        "regime": regime,
    }


def chi_shell_bending(
    D_mm: float, t_mm: float, fy_MPa: float,
    quality: Literal["A", "B", "C"] = "B",
    additional_imperfection: float = 1.0,
) -> dict:
    """Riduzione per flessione — applico stesso χ assiale (cautelativo).

    EN 1993-1-6 §8.5.2(7) permette di usare χ_x in compressione per la verifica
    a flessione, con l'ulteriore vantaggio che la sollecitazione massima copre
    solo una porzione della circonferenza (meno critica). In pratica si usa
    σ_x_eq = σ_M (gradient elevato) → stessa formulazione cautelativa.
    """
    return chi_shell_circular(D_mm, t_mm, fy_MPa, quality, additional_imperfection)
