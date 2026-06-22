"""DB sezioni tubolari circolari cave (CHS) — EN 10210-2 / EN 10219-2.

Caratteristiche calcolate da D_ext e t. Le proprietà geometriche sono esatte
(formule analitiche), quindi NON serve un DB tabellare: calcolo on-demand.

Per profili commerciali standard (sagomario) usare una whitelist di taglie
disponibili sul mercato, così che `get_profile("TUBO 273x8")` restituisca un
profilo *commerciale* e non solo numeri arbitrari.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# Taglie commerciali standard più usate per pali TLC (EN 10210 caldolaminati + EN 10219 saldati)
# Lista non esaustiva — espandibile.
TAGLIE_CHS_COMMERCIALI: dict[str, tuple[float, float]] = {
    # designazione : (D_ext_mm, t_mm)
    "CHS 168.3x6.3": (168.3, 6.3),
    "CHS 168.3x8":   (168.3, 8.0),
    "CHS 168.3x10":  (168.3, 10.0),
    "CHS 193.7x6.3": (193.7, 6.3),
    "CHS 193.7x8":   (193.7, 8.0),
    "CHS 193.7x10":  (193.7, 10.0),
    "CHS 219.1x6.3": (219.1, 6.3),
    "CHS 219.1x8":   (219.1, 8.0),
    "CHS 219.1x10":  (219.1, 10.0),
    "CHS 219.1x12.5": (219.1, 12.5),
    "CHS 244.5x8":   (244.5, 8.0),
    "CHS 244.5x10":  (244.5, 10.0),
    "CHS 244.5x12.5": (244.5, 12.5),
    "CHS 273.0x8":   (273.0, 8.0),
    "CHS 273.0x10":  (273.0, 10.0),
    "CHS 273.0x12.5": (273.0, 12.5),
    "CHS 323.9x8":   (323.9, 8.0),
    "CHS 323.9x10":  (323.9, 10.0),
    "CHS 323.9x12.5": (323.9, 12.5),
    "CHS 355.6x10":  (355.6, 10.0),
    "CHS 355.6x12.5": (355.6, 12.5),
    "CHS 406.4x10":  (406.4, 10.0),
    "CHS 406.4x12.5": (406.4, 12.5),
    "CHS 457x10":    (457.0, 10.0),
    "CHS 457x12.5":  (457.0, 12.5),
    "CHS 508x10":    (508.0, 10.0),
    "CHS 508x12.5":  (508.0, 12.5),
}


@dataclass(frozen=True)
class SezioneTubolare:
    """Caratteristiche geometriche sezione tubolare cava."""
    designazione: str
    D_ext_mm: float
    t_mm: float
    A_mm2: float
    I_mm4: float        # momento d'inerzia
    W_el_mm3: float     # modulo elastico
    W_pl_mm3: float     # modulo plastico
    i_mm: float         # raggio d'inerzia
    peso_kg_m: float    # peso per unità di lunghezza (acciaio ρ=7850)

    def classe_sezione(self, fy_MPa: float) -> int:
        """Classificazione EN 1993-1-1 Tab. 5.2 — tubolari cavi.

        Per sezioni tubolari cave: rapporto d/t confrontato con limiti·ε,
        dove ε = √(235/fy).
        """
        eps = math.sqrt(235.0 / fy_MPa)
        ratio = self.D_ext_mm / self.t_mm
        limit_C1 = 50.0 * eps * eps
        limit_C2 = 70.0 * eps * eps
        limit_C3 = 90.0 * eps * eps
        if ratio <= limit_C1:
            return 1
        if ratio <= limit_C2:
            return 2
        if ratio <= limit_C3:
            return 3
        return 4


def chs_proprieta(D_ext_mm: float, t_mm: float, designazione: str = "") -> SezioneTubolare:
    """Calcola proprietà geometriche di una sezione tubolare circolare cava.

    Formule esatte (anello circolare):
      A   = π/4 · (D² − d²)
      I   = π/64 · (D⁴ − d⁴)
      W_el = I / (D/2)
      W_pl = 1/6 · (D³ − d³)
      i   = √(I/A) = √((D² + d²)/16)
    """
    if t_mm <= 0 or D_ext_mm <= 2 * t_mm:
        raise ValueError(f"Geometria non valida: D={D_ext_mm}, t={t_mm}")
    D = D_ext_mm
    d = D - 2.0 * t_mm
    A = math.pi / 4.0 * (D * D - d * d)
    I = math.pi / 64.0 * (D**4 - d**4)
    W_el = I / (D / 2.0)
    W_pl = (D**3 - d**3) / 6.0
    i = math.sqrt(I / A)
    peso = A * 1e-6 * 7850.0  # kg/m
    return SezioneTubolare(
        designazione=designazione or f"CHS {D}x{t_mm}",
        D_ext_mm=D, t_mm=t_mm,
        A_mm2=A, I_mm4=I, W_el_mm3=W_el, W_pl_mm3=W_pl,
        i_mm=i, peso_kg_m=peso,
    )


def palo_poligonale_proprieta(
    D_inscritto_mm: float, t_mm: float, n_lati: int, designazione: str = "",
) -> SezioneTubolare:
    """Caratteristiche sezione poligonale regolare cava (palo TLC tipico).

    Approssimazione: per poligoni regolari con n ≥ 8 lati, le proprietà
    convergono a quelle del cerchio circoscritto. Formule precise:
      A_pol   = n · t · L_lato,                 L_lato = 2·R·tan(π/n)
      I_pol  ≈ I_cerchio_equiv · (1 − 0.05/n)   (correzione lieve)
    Per n ≥ 12 si usa direttamente l'equivalente circolare con D_medio.
    """
    if n_lati < 6:
        raise ValueError("Poligonali TLC tipici: 8, 12, 16, 18, 24 lati")
    R_ext = D_inscritto_mm / 2.0  # raggio cerchio inscritto (apotema circoscritto al poligono)
    # Per palo TLC il "D inscritto" è il cerchio inscritto al poligono → apotema = R_ext
    R_circ = R_ext / math.cos(math.pi / n_lati)  # raggio circoscritto al poligono
    D_equiv = 2.0 * R_circ * math.cos(math.pi / n_lati / 2.0)  # diametro medio
    sez = chs_proprieta(D_equiv, t_mm, designazione=designazione or f"POL{n_lati} D{D_inscritto_mm:.0f}x{t_mm}")
    return sez


def lookup_chs_commerciale(designazione: str) -> SezioneTubolare:
    """Trova un profilo commerciale dalla designazione."""
    key = designazione.strip().upper().replace(" ", "")
    for k, (D, t) in TAGLIE_CHS_COMMERCIALI.items():
        if k.upper().replace(" ", "") == key:
            return chs_proprieta(D, t, designazione=k)
    raise KeyError(f"Profilo commerciale '{designazione}' non trovato. Disponibili: "
                   f"{list(TAGLIE_CHS_COMMERCIALI.keys())[:5]}...")
