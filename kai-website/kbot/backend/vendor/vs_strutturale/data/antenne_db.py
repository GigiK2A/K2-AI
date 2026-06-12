"""DB antenne TLC — seed manuale.

Modelli più frequenti su pali iliad/Cellnex/Inwit. Dati da datasheet costruttori
(Kathrein/CommScope/Huawei/ZTE) + arrotondamenti cautelativi per il calcolo strutturale.

Convenzioni:
- area_frontale_m2: area di riferimento c_p calcolo vento (h × w)
- C_d: coefficiente di forma dichiarato dal costruttore o 1.3 cautelativo
- peso_kg: peso secco incluso staffaggio standard

Espandibile a piacere. Fonte XLSX completa K2A pendente.
"""

from __future__ import annotations

from typing import TypedDict


class DatiAntenna(TypedDict):
    famiglia: str
    altezza_mm: int
    larghezza_mm: int
    profondita_mm: int
    area_frontale_m2: float
    C_d: float
    peso_kg: float
    bande: list[str]
    note: str


ANTENNE_DB: dict[str, DatiAntenna] = {
    # --- Kathrein (cl. macrocella) ---
    "Kathrein 80010622": {
        "famiglia": "Kathrein 800 Series", "altezza_mm": 2580, "larghezza_mm": 499,
        "profondita_mm": 158, "area_frontale_m2": 1.29, "C_d": 1.30, "peso_kg": 33.0,
        "bande": ["1800", "2100", "2600"], "note": "Macrocella triple-band classic",
    },
    "Kathrein 800-10973": {
        "famiglia": "Kathrein 800 Series", "altezza_mm": 1305, "larghezza_mm": 305,
        "profondita_mm": 145, "area_frontale_m2": 0.40, "C_d": 1.30, "peso_kg": 13.5,
        "bande": ["1800", "2100"], "note": "Compatta dual-band",
    },
    # --- CommScope (rebranded Andrew/Kathrein) ---
    "CommScope SBNHH-1D65B": {
        "famiglia": "CommScope SBNHH", "altezza_mm": 1996, "larghezza_mm": 309,
        "profondita_mm": 178, "area_frontale_m2": 0.62, "C_d": 1.30, "peso_kg": 22.0,
        "bande": ["1800", "2100", "2600"], "note": "Tribanda macrocella moderna",
    },
    "CommScope NHH-65C-R4": {
        "famiglia": "CommScope NHH", "altezza_mm": 1500, "larghezza_mm": 300,
        "profondita_mm": 165, "area_frontale_m2": 0.45, "C_d": 1.30, "peso_kg": 15.0,
        "bande": ["1800", "2100"], "note": "Compact macro",
    },
    # --- Huawei ---
    "Huawei AAU5613": {
        "famiglia": "Huawei AAU 5G", "altezza_mm": 860, "larghezza_mm": 395,
        "profondita_mm": 195, "area_frontale_m2": 0.34, "C_d": 1.30, "peso_kg": 35.0,
        "bande": ["3500-mMIMO"], "note": "Massive MIMO 64T64R 5G",
    },
    "Huawei AAU5639": {
        "famiglia": "Huawei AAU 5G", "altezza_mm": 980, "larghezza_mm": 510,
        "profondita_mm": 220, "area_frontale_m2": 0.50, "C_d": 1.30, "peso_kg": 45.0,
        "bande": ["3500-mMIMO"], "note": "Massive MIMO 5G più larga",
    },
    # --- ZTE ---
    "ZTE A9611": {
        "famiglia": "ZTE Massive MIMO", "altezza_mm": 875, "larghezza_mm": 400,
        "profondita_mm": 180, "area_frontale_m2": 0.35, "C_d": 1.30, "peso_kg": 28.0,
        "bande": ["3500-mMIMO"], "note": "5G NR Massive MIMO",
    },
    # --- Parabole / link microonde ---
    "Parabola 0.3m": {
        "famiglia": "Microwave dish 0.3m", "altezza_mm": 300, "larghezza_mm": 300,
        "profondita_mm": 200, "area_frontale_m2": 0.071, "C_d": 1.30, "peso_kg": 5.0,
        "bande": ["MW"], "note": "Microonde compatta",
    },
    "Parabola 0.6m": {
        "famiglia": "Microwave dish 0.6m", "altezza_mm": 600, "larghezza_mm": 600,
        "profondita_mm": 300, "area_frontale_m2": 0.283, "C_d": 1.30, "peso_kg": 12.0,
        "bande": ["MW"], "note": "Microonde standard",
    },
    "Parabola 1.2m": {
        "famiglia": "Microwave dish 1.2m", "altezza_mm": 1200, "larghezza_mm": 1200,
        "profondita_mm": 500, "area_frontale_m2": 1.131, "C_d": 1.30, "peso_kg": 30.0,
        "bande": ["MW"], "note": "Microonde grande, link lunga distanza",
    },
    # --- RRU / RRH ---
    "RRU Ericsson 4408": {
        "famiglia": "Ericsson Radio", "altezza_mm": 550, "larghezza_mm": 300,
        "profondita_mm": 160, "area_frontale_m2": 0.165, "C_d": 1.30, "peso_kg": 26.0,
        "bande": ["1800/2100/2600"], "note": "RRU multibanda",
    },
    "RRU Nokia AHFIB": {
        "famiglia": "Nokia Airscale", "altezza_mm": 460, "larghezza_mm": 260,
        "profondita_mm": 145, "area_frontale_m2": 0.12, "C_d": 1.30, "peso_kg": 23.0,
        "bande": ["1800/2100"], "note": "RRU compatta",
    },
}


def cerca_antenna(modello: str) -> DatiAntenna | None:
    """Lookup case-insensitive con normalizzazione spazi."""
    target = modello.strip().lower().replace(" ", "")
    for k, v in ANTENNE_DB.items():
        if k.lower().replace(" ", "") == target:
            return v
    return None


def lista_antenne() -> list[str]:
    return list(ANTENNE_DB.keys())
