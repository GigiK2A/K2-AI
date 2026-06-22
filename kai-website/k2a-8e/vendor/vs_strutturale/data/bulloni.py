"""Caratteristiche bulloni — UNI EN ISO 898-1, EN 1993-1-8.

A_s = area resistente (tensile stress area) — UNI EN ISO 898-1 Tab.
A   = area nominale dello stelo (per taglio in zona non filettata)
"""

from __future__ import annotations


# Area resistente A_s [mm²] e nominale A [mm²]
BULLONI_AREE: dict[str, dict[str, float]] = {
    "M10": {"A_s": 58.0,  "A": 78.5,   "d": 10.0},
    "M12": {"A_s": 84.3,  "A": 113.1,  "d": 12.0},
    "M14": {"A_s": 115.0, "A": 153.9,  "d": 14.0},
    "M16": {"A_s": 157.0, "A": 201.1,  "d": 16.0},
    "M18": {"A_s": 192.0, "A": 254.5,  "d": 18.0},
    "M20": {"A_s": 245.0, "A": 314.2,  "d": 20.0},
    "M22": {"A_s": 303.0, "A": 380.1,  "d": 22.0},
    "M24": {"A_s": 353.0, "A": 452.4,  "d": 24.0},
    "M27": {"A_s": 459.0, "A": 572.6,  "d": 27.0},
    "M30": {"A_s": 561.0, "A": 706.9,  "d": 30.0},
    "M36": {"A_s": 817.0, "A": 1017.9, "d": 36.0},
}

# Classi resistenza UNI EN ISO 898-1
# f_yb [MPa], f_ub [MPa]
CLASSI_BULLONI: dict[str, dict[str, float]] = {
    "4.6":  {"f_yb": 240,  "f_ub": 400},
    "4.8":  {"f_yb": 320,  "f_ub": 400},
    "5.6":  {"f_yb": 300,  "f_ub": 500},
    "5.8":  {"f_yb": 400,  "f_ub": 500},
    "6.8":  {"f_yb": 480,  "f_ub": 600},
    "8.8":  {"f_yb": 640,  "f_ub": 800},
    "10.9": {"f_yb": 900,  "f_ub": 1000},
    "12.9": {"f_yb": 1080, "f_ub": 1200},
}


def alpha_v(classe: str) -> float:
    """α_v per resistenza a taglio EN 1993-1-8 Tab. 3.4."""
    if classe in ("4.6", "5.6", "8.8"):
        return 0.6
    return 0.5  # 4.8, 5.8, 6.8, 10.9, 12.9
