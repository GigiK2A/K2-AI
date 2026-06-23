"""Tabella zone vento NTC 2018 §3.3.2 — Tab. 3.3.I.

Parametri: v_b,0 [m/s], a_0 [m s.l.m.], k_s [-] (coefficiente quota).

Fonte: NTC 2018 D.M. 17 gennaio 2018 — Tabella 3.3.I.
"""

from __future__ import annotations

from typing import TypedDict


class ZonaVentoData(TypedDict):
    descrizione: str
    v_b0_ms: float  # velocità base di riferimento al livello del mare [m/s]
    a_0_m: float  # quota di riferimento [m]
    k_s: float  # coefficiente di altitudine [-]


# Tabella 3.3.I — NTC 2018
NTC_ZONE_VENTO: dict[int, ZonaVentoData] = {
    1: {
        "descrizione": "Valle d'Aosta, Piemonte, Lombardia, Trentino Alto Adige, Veneto, Friuli "
                       "Venezia Giulia (escl. provincia Trieste)",
        "v_b0_ms": 25.0,
        "a_0_m": 1000.0,
        "k_s": 0.40,
    },
    2: {
        "descrizione": "Emilia Romagna",
        "v_b0_ms": 25.0,
        "a_0_m": 750.0,
        "k_s": 0.45,
    },
    3: {
        "descrizione": "Toscana, Marche, Umbria, Lazio, Abruzzo, Molise, Campania, Puglia, "
                       "Basilicata, Calabria (escl. provincia Reggio Calabria)",
        "v_b0_ms": 27.0,
        "a_0_m": 500.0,
        "k_s": 0.37,
    },
    4: {
        "descrizione": "Sicilia, provincia Reggio Calabria",
        "v_b0_ms": 28.0,
        "a_0_m": 500.0,
        "k_s": 0.36,
    },
    5: {
        "descrizione": "Sardegna (zona orientale a est della retta congiungente Capo Teulada-"
                       "Capo Comino)",
        "v_b0_ms": 28.0,
        "a_0_m": 750.0,
        "k_s": 0.40,
    },
    6: {
        "descrizione": "Sardegna (zona occidentale a ovest della retta congiungente Capo Teulada-"
                       "Capo Comino)",
        "v_b0_ms": 28.0,
        "a_0_m": 500.0,
        "k_s": 0.36,
    },
    7: {
        "descrizione": "Liguria",
        "v_b0_ms": 28.0,
        "a_0_m": 1000.0,
        "k_s": 0.54,
    },
    8: {
        "descrizione": "Provincia di Trieste",
        "v_b0_ms": 30.0,
        "a_0_m": 1500.0,
        "k_s": 0.50,
    },
    9: {
        "descrizione": "Isole (escluse Sicilia e Sardegna) e mare aperto",
        "v_b0_ms": 31.0,
        "a_0_m": 500.0,
        "k_s": 0.32,
    },
}


# Tabella 3.3.II — Categoria esposizione NTC 2018.
# Convenzione classi rugosità NTC (NB: A = molto rugoso urbano, D = aperto/mare):
#   A → aree urbane metropolitane (alta rugosità)
#   B → aree urbane non A, industriali, suburbane
#   C → aree con vegetazione bassa, ostacoli isolati
#   D → assenza di ostacoli (mare aperto, campi)
# Quindi: rugosità↑ ⇒ categoria↓ (più protezione, minore esposizione).
#
# Tabella derivata da Tab. 3.3.II + validata contro fixtures reali:
#   - Pomezia (zona 3, D, 10km) → II
#   - Pedaso  (zona 3, D, 0.5km) → II
#   - Aldini  (zona 2, B, 85km) → IV
#
# Format: (zona, classe_rug, fascia_distanza_costa) -> categoria
# fascia: "0-2km" | "2-10km" | "10-30km" | ">30km" | "isola"

NTC_CAT_ESPOSIZIONE: dict[tuple[int, str, str], str] = {
    # --- Zone 1 (Nord-Ovest / Triveneto, Po) ---
    (1, "A", "0-2km"): "IV", (1, "A", "2-10km"): "IV", (1, "A", "10-30km"): "IV", (1, "A", ">30km"): "V",
    (1, "B", "0-2km"): "III", (1, "B", "2-10km"): "IV", (1, "B", "10-30km"): "IV", (1, "B", ">30km"): "IV",
    (1, "C", "0-2km"): "II", (1, "C", "2-10km"): "III", (1, "C", "10-30km"): "III", (1, "C", ">30km"): "III",
    (1, "D", "0-2km"): "I", (1, "D", "2-10km"): "II", (1, "D", "10-30km"): "II", (1, "D", ">30km"): "II",
    # --- Zone 2 (Emilia Romagna) ---
    (2, "A", "0-2km"): "IV", (2, "A", "2-10km"): "IV", (2, "A", "10-30km"): "IV", (2, "A", ">30km"): "V",
    (2, "B", "0-2km"): "III", (2, "B", "2-10km"): "IV", (2, "B", "10-30km"): "IV", (2, "B", ">30km"): "IV",
    (2, "C", "0-2km"): "II", (2, "C", "2-10km"): "III", (2, "C", "10-30km"): "III", (2, "C", ">30km"): "III",
    (2, "D", "0-2km"): "I", (2, "D", "2-10km"): "II", (2, "D", "10-30km"): "II", (2, "D", ">30km"): "II",
    # --- Zone 3 (Centro-Sud peninsulare) ---
    (3, "A", "0-2km"): "IV", (3, "A", "2-10km"): "IV", (3, "A", "10-30km"): "IV", (3, "A", ">30km"): "V",
    (3, "B", "0-2km"): "III", (3, "B", "2-10km"): "IV", (3, "B", "10-30km"): "IV", (3, "B", ">30km"): "IV",
    (3, "C", "0-2km"): "II", (3, "C", "2-10km"): "III", (3, "C", "10-30km"): "III", (3, "C", ">30km"): "III",
    (3, "D", "0-2km"): "II", (3, "D", "2-10km"): "II", (3, "D", "10-30km"): "II", (3, "D", ">30km"): "II",
}


# Tabella 3.3.III — Parametri categoria esposizione: k_r, z_0, z_min
NTC_PARAMETRI_CAT_ESPOSIZIONE: dict[str, dict[str, float]] = {
    "I":   {"k_r": 0.17, "z_0_m": 0.01, "z_min_m": 2.0},
    "II":  {"k_r": 0.19, "z_0_m": 0.05, "z_min_m": 4.0},
    "III": {"k_r": 0.20, "z_0_m": 0.10, "z_min_m": 5.0},
    "IV":  {"k_r": 0.22, "z_0_m": 0.30, "z_min_m": 8.0},
    "V":   {"k_r": 0.23, "z_0_m": 0.70, "z_min_m": 12.0},
}
