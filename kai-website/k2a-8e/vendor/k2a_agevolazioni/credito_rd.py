"""Credito R&S, Innovazione tecnologica e Design (L. 160/2019 commi 198-209).

Credito d'imposta = min(spese ammissibili ; massimale) x aliquota,
differenziato per tipologia di attività.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "credito_rd.json").read_text())


class CreditoRDInput(BaseModel):
    spese_ammissibili_eur: float = Field(
        ..., gt=0,
        description="Spese ammissibili al netto delle altre sovvenzioni ricevute "
                    "sulle stesse spese (base di calcolo del credito).")
    tipologia: Literal[
        "ricerca_sviluppo", "innovazione_tecnologica",
        "innovazione_4_0_green", "design"
    ] = Field(..., description="Tipologia di attività agevolata.")


class CreditoRDOutput(BaseModel):
    tipologia: str
    descrizione: str
    aliquota_pct: float
    massimale_eur: float
    spese_ammissibili_eur: float
    base_agevolabile_eur: float
    spese_oltre_massimale_eur: float
    credito_imposta_eur: float
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def credito_rd_innovazione(inp: CreditoRDInput) -> CreditoRDOutput:
    avvertenze: list[str] = []
    if _DATA.get("_da_validare"):
        avvertenze.append(
            "Aliquote/massimali credito R&S marcati _DA_VALIDARE (a regime 2024-2025): "
            "verificare l'annualità di competenza su MIMIT/Agenzia Entrate."
        )

    node = _DATA["tipologie"][inp.tipologia]
    if node.get("_da_validare"):
        avvertenze.append(
            f"Tipologia '{inp.tipologia}': aliquota {node['aliquota_pct']}% è un "
            f"PLACEHOLDER variato negli anni ({node.get('note', '')}). Verificare annualità."
        )

    aliquota = float(node["aliquota_pct"])
    massimale = float(node["massimale_eur"])
    base = min(inp.spese_ammissibili_eur, massimale)
    oltre = max(0.0, inp.spese_ammissibili_eur - massimale)
    if oltre > 0:
        avvertenze.append(
            f"Spese {inp.spese_ammissibili_eur:.0f}€ oltre il massimale {massimale:.0f}€: "
            f"l'eccedenza di {oltre:.0f}€ non genera credito."
        )

    credito = base * aliquota / 100.0

    avvertenze.append(
        "Credito R&S: richiede certificazione contabile e relazione tecnica "
        "asseverata. Regime non de minimis; verificare cumulabilità sulle stesse spese."
    )

    return CreditoRDOutput(
        tipologia=inp.tipologia,
        descrizione=node["label"],
        aliquota_pct=aliquota,
        massimale_eur=massimale,
        spese_ammissibili_eur=inp.spese_ammissibili_eur,
        base_agevolabile_eur=round(base, 2),
        spese_oltre_massimale_eur=round(oltre, 2),
        credito_imposta_eur=round(credito, 2),
        avvertenze=avvertenze,
        riferimento_normativo=f"{_DATA['_fonte']} — {node.get('comma', '')}",
        trace={
            "fonte_dati": _DATA["_fonte"],
            "data_validita_dati": _DATA["_data_validita"],
            "metodo": "min(spese; massimale) x aliquota",
        },
    )
