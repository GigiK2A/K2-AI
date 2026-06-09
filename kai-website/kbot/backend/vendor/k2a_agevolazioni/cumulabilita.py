"""Cumulabilità e finanziabilità complessiva di più agevolazioni sui medesimi costi.

Verifica:
  - intensità totale ≤ 100% del costo (divieto di doppio finanziamento, PNRR art.9);
  - incompatibilità note tra misure (es. Transizione 5.0 vs 4.0 / ZES);
  - importo massimo ancora finanziabile residuo entro il costo.
"""
from __future__ import annotations
import json
from itertools import combinations
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "cumulabilita.json").read_text())

_MISURE = Literal[
    "transizione_5_0", "transizione_4_0", "credito_rd",
    "nuova_sabatini", "credito_zes", "fondo_perduto", "altro",
]


class Agevolazione(BaseModel):
    misura: _MISURE = Field(..., description="Identificativo della misura agevolativa.")
    importo_eur: float = Field(..., gt=0, description="Importo dell'agevolazione (credito/contributo).")
    descrizione: str = Field("", description="Riferimento (bando/decreto), opzionale.")


class CumulabilitaInput(BaseModel):
    costo_investimento_eur: float = Field(
        ..., gt=0, description="Costo dell'investimento sui medesimi costi agevolati.")
    agevolazioni: list[Agevolazione] = Field(
        ..., min_length=1, description="Agevolazioni che si intende cumulare sugli stessi costi.")


class CumulabilitaOutput(BaseModel):
    costo_investimento_eur: float
    totale_agevolazioni_eur: float
    intensita_totale_pct: float
    intensita_massima_pct: float
    supera_intensita_massima: bool
    importo_residuo_finanziabile_eur: float
    incompatibilita_rilevate: list[dict]
    cumulo_ammesso: bool
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def cumulabilita_e_finanziabile(inp: CumulabilitaInput) -> CumulabilitaOutput:
    avvertenze: list[str] = []
    if _DATA.get("_da_validare"):
        avvertenze.append(
            "Regole di cumulo marcate _DA_VALIDARE e semplificate: verificare sempre "
            "il decreto della singola misura e le FAQ ufficiali sui costi agevolati."
        )

    totale = sum(a.importo_eur for a in inp.agevolazioni)
    intensita = round(totale / inp.costo_investimento_eur * 100.0, 2)
    int_max = float(_DATA["intensita_massima_pct"])
    supera = intensita > int_max
    residuo = round(max(0.0, inp.costo_investimento_eur - totale), 2)

    if supera:
        avvertenze.append(
            f"INTENSITÀ {intensita:.2f}% > {int_max:.0f}%: la somma delle agevolazioni "
            f"({totale:.0f}€) supera il costo ({inp.costo_investimento_eur:.0f}€). "
            f"Configura doppio finanziamento — non ammesso."
        )

    # Incompatibilità tra coppie di misure presenti
    misure_presenti = {a.misura for a in inp.agevolazioni}
    incompat: list[dict] = []
    for regola in _DATA["incompatibilita"]:
        coppia = set(regola["misure"])
        if coppia.issubset(misure_presenti):
            incompat.append({
                "misure": regola["misure"],
                "tipo": regola["tipo"],
                "nota": regola["nota"],
            })
            avvertenze.append(f"INCOMPATIBILITÀ: {regola['nota']}")

    cumulo_ammesso = (not supera) and (len(incompat) == 0)

    return CumulabilitaOutput(
        costo_investimento_eur=inp.costo_investimento_eur,
        totale_agevolazioni_eur=round(totale, 2),
        intensita_totale_pct=intensita,
        intensita_massima_pct=int_max,
        supera_intensita_massima=supera,
        importo_residuo_finanziabile_eur=residuo,
        incompatibilita_rilevate=incompat,
        cumulo_ammesso=cumulo_ammesso,
        avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={
            "fonte_dati": _DATA["_fonte"],
            "data_validita_dati": _DATA["_data_validita"],
            "n_agevolazioni": len(inp.agevolazioni),
            "misure": sorted(misure_presenti),
        },
    )
