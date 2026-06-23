"""Illuminamento — metodo lumen UNI EN 12464-1 (interni) / UNI 11248 (cantieri/esterni)."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


# UNI EN 12464-1: lux raccomandati per ambiente
LUX_REQUIRED = {
    "ufficio_lavoro": 500,
    "ufficio_riunione": 500,
    "ufficio_corridoio": 100,
    "industria_lavoro_generale": 300,
    "industria_lavoro_preciso": 750,
    "industria_lavoro_finissimo": 1500,
    "magazzino_movimento": 100,
    "magazzino_picking": 200,
    "ospedale_corsia": 100,
    "ospedale_sala_operatoria": 1000,
    "scuola_aula": 300,
    "scuola_disegno": 750,
    "cantiere_generale": 50,    # UNI 11248
    "cantiere_lavorazione": 200,
    "ricezione_TLC_apparati": 200,
    "abitazione_soggiorno": 100,
    "abitazione_cucina": 300,
    "abitazione_bagno": 200,
}


class IlluminamentoLumenInput(BaseModel):
    ambiente: str = Field(..., description="Es: ufficio_lavoro, cantiere_generale, ricezione_TLC_apparati")
    lux_richiesti: float | None = Field(None, description="Override lux richiesti (se ambiente non in tabella)")
    L_m: float = Field(..., gt=0, description="Lunghezza locale m")
    W_m: float = Field(..., gt=0, description="Larghezza locale m")
    H_m: float = Field(3.0, gt=0, description="Altezza locale m")
    h_lavoro_m: float = Field(0.8, gt=0, description="Altezza piano di lavoro m")
    h_sospensione_apparecchio_m: float = Field(0.2, ge=0, description="Sospensione apparecchio dal soffitto")
    fattore_riflessione_soffitto: float = Field(0.7, ge=0, le=1)
    fattore_riflessione_pareti: float = Field(0.5, ge=0, le=1)
    fattore_riflessione_pavimento: float = Field(0.2, ge=0, le=1)
    fattore_manutenzione: float = Field(0.8, gt=0, le=1, description="MF: pulizia (0.8 nuovo, 0.6 ambiente sporco)")
    flusso_apparecchio_lm: float = Field(..., gt=0, description="Flusso luminoso singolo apparecchio (lm)")
    potenza_apparecchio_W: float = Field(..., gt=0, description="Potenza singolo apparecchio (W)")


class IlluminamentoLumenOutput(BaseModel):
    lux_target: float
    area_m2: float
    indice_locale_K: float
    fattore_utilizzazione_U: float
    n_apparecchi_richiesti: int
    flusso_totale_lm: float
    densita_potenza_W_m2: float
    lux_effettivi_calcolati: float
    trace: dict


def calcola_illuminamento(inp: IlluminamentoLumenInput) -> IlluminamentoLumenOutput:
    lux_target = inp.lux_richiesti if inp.lux_richiesti else LUX_REQUIRED.get(inp.ambiente, 300)
    area = inp.L_m * inp.W_m
    # Altezza utile apparecchio sopra piano di lavoro
    h_util = inp.H_m - inp.h_lavoro_m - inp.h_sospensione_apparecchio_m
    # Indice del locale K
    K = (inp.L_m * inp.W_m) / (h_util * (inp.L_m + inp.W_m))
    # Fattore di utilizzazione U — interpolazione semplificata da tabelle UNI
    # K=0.6→U=0.35, K=1→U=0.45, K=2→U=0.6, K=3→U=0.7, K=5→U=0.78
    U_table = [(0.6, 0.35), (1.0, 0.45), (1.5, 0.55), (2.0, 0.60),
               (2.5, 0.65), (3.0, 0.70), (4.0, 0.75), (5.0, 0.78)]
    if K <= U_table[0][0]:
        U = U_table[0][1]
    elif K >= U_table[-1][0]:
        U = U_table[-1][1]
    else:
        for i in range(len(U_table) - 1):
            if U_table[i][0] <= K <= U_table[i + 1][0]:
                k0, u0 = U_table[i]
                k1, u1 = U_table[i + 1]
                U = u0 + (u1 - u0) * (K - k0) / (k1 - k0)
                break
    # Riflessione media ponderata (semplificata): correzione su U
    refl_avg = (inp.fattore_riflessione_soffitto + inp.fattore_riflessione_pareti + inp.fattore_riflessione_pavimento) / 3
    U *= (0.85 + 0.30 * refl_avg)  # fattore correttivo empirico
    U = min(U, 0.85)  # cap fisico

    # Flusso totale richiesto Φ = E × A / (U × MF)
    flusso_totale = lux_target * area / (U * inp.fattore_manutenzione)
    n_app = int(flusso_totale / inp.flusso_apparecchio_lm) + 1
    flusso_eff = n_app * inp.flusso_apparecchio_lm
    lux_effettivi = flusso_eff * U * inp.fattore_manutenzione / area
    densita_W = n_app * inp.potenza_apparecchio_W / area

    return IlluminamentoLumenOutput(
        lux_target=lux_target,
        area_m2=round(area, 2),
        indice_locale_K=round(K, 3),
        fattore_utilizzazione_U=round(U, 3),
        n_apparecchi_richiesti=n_app,
        flusso_totale_lm=round(flusso_totale, 0),
        densita_potenza_W_m2=round(densita_W, 2),
        lux_effettivi_calcolati=round(lux_effettivi, 1),
        trace={
            "norma": "UNI EN 12464-1 (interni) / UNI 11248 (esterni)",
            "formula": "n = E × A / (Φ_app × U × MF)",
            "K_indice_locale": "K = L·W / (h_util × (L+W))",
            "ambiente_lux_default": lux_target if inp.lux_richiesti is None else "override fornito",
        },
    )
