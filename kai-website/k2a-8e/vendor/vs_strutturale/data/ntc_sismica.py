"""Parametri sismica NTC 2018 §3.2 — Tab. 3.2.II, 3.2.III, 3.2.IV.

NB: ag, F0, Tc* per il sito specifico vengono normalmente da interpolazione del
reticolo INGV (Allegato B NTC). In v1 si passano come INPUT espliciti — la lookup
geografica sarà aggiunta in v1.1 con DB sismico per comune o coordinate.
"""

from __future__ import annotations

from typing import Literal, TypedDict

CategoriaSottosuolo = Literal["A", "B", "C", "D", "E"]
CategoriaTopografica = Literal["T1", "T2", "T3", "T4"]
StatoLimite = Literal["SLO", "SLD", "SLV", "SLC"]


class ParametriSottosuolo(TypedDict):
    """Parametri amplificazione stratigrafica NTC Tab. 3.2.IV."""
    Ss_min: float
    Ss_max: float
    Cc_formula: str
    Cc_coeff: tuple[float, float]  # (a, b) in Cc = a · (Tc*)^b


# NTC Tab. 3.2.IV — coefficienti per S_S e C_C
# S_S limitato tra Ss_min e Ss_max in funzione di ag·F0/g (formule §3.2.3.2.1)
NTC_PARAMETRI_SOTTOSUOLO: dict[str, ParametriSottosuolo] = {
    "A": {"Ss_min": 1.00, "Ss_max": 1.00, "Cc_formula": "1.00",            "Cc_coeff": (1.00, 0.00)},
    "B": {"Ss_min": 1.00, "Ss_max": 1.20, "Cc_formula": "1.10·(Tc*)^-0.20", "Cc_coeff": (1.10, -0.20)},
    "C": {"Ss_min": 1.00, "Ss_max": 1.50, "Cc_formula": "1.05·(Tc*)^-0.33", "Cc_coeff": (1.05, -0.33)},
    "D": {"Ss_min": 0.90, "Ss_max": 1.80, "Cc_formula": "1.25·(Tc*)^-0.50", "Cc_coeff": (1.25, -0.50)},
    "E": {"Ss_min": 1.00, "Ss_max": 1.60, "Cc_formula": "1.15·(Tc*)^-0.40", "Cc_coeff": (1.15, -0.40)},
}


# NTC Tab. 3.2.V — coefficiente amplificazione topografica S_T
NTC_TOPOGRAFICO: dict[str, float] = {
    "T1": 1.0,  # Superficie pianeggiante, pendii e rilievi isolati con i ≤ 15°
    "T2": 1.2,  # Pendii con inclinazione media i > 15°
    "T3": 1.2,  # Rilievi con larghezza in cresta molto > base, 15° < i ≤ 30°
    "T4": 1.4,  # Rilievi con larghezza in cresta molto > base, i > 30°
}


# Coefficienti S_S formula NTC eq. 3.2.5 — espressi come (a, b, c) in
# S_S = a − b · F0 · ag/g, vincolato a [Ss_min, Ss_max]
NTC_SS_FORMULA: dict[str, tuple[float, float]] = {
    "A": (1.00, 0.00),
    "B": (1.40, 0.40),
    "C": (1.70, 0.60),
    "D": (2.40, 1.50),
    "E": (2.00, 1.10),
}
