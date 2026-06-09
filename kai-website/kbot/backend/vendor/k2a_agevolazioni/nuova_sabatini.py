"""Nuova Sabatini — contributo in conto impianti (L. 98/2013 art.2).

Il contributo è pari alla somma delle quote interessi di un piano di
ammortamento a rata costante (francese) calcolato su un finanziamento
quinquennale (10 rate semestrali) a un tasso convenzionale di riferimento,
diverso tra investimenti ordinari e investimenti 4.0/green.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "nuova_sabatini.json").read_text())


class NuovaSabatiniInput(BaseModel):
    finanziamento_eur: float = Field(
        ..., gt=0,
        description="Importo del finanziamento/leasing per beni strumentali.")
    tipologia: Literal["ordinario", "industria_4_0", "green"] = Field(
        "ordinario",
        description="Determina il tasso convenzionale: ordinario 2,75% / "
                    "industria 4.0 e green 3,575%.")


class NuovaSabatiniOutput(BaseModel):
    ammissibile: bool
    tipologia: str
    tasso_riferimento_annuo_pct: float
    finanziamento_eur: float
    durata_anni: int
    n_rate: int
    rata_semestrale_eur: float
    contributo_totale_eur: float
    contributo_su_finanziamento_pct: float
    piano_ammortamento: list[dict]
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def nuova_sabatini(inp: NuovaSabatiniInput) -> NuovaSabatiniOutput:
    avvertenze: list[str] = []
    if _DATA.get("_da_validare"):
        avvertenze.append(
            "Tassi convenzionali Sabatini marcati _DA_VALIDARE: verificare la "
            "circolare MIMIT vigente prima dell'uso ufficiale."
        )

    lim = _DATA["limiti_finanziamento_eur"]
    ammissibile = lim["minimo"] <= inp.finanziamento_eur <= lim["massimo"]
    if not ammissibile:
        avvertenze.append(
            f"ATTENZIONE: finanziamento {inp.finanziamento_eur:.0f}€ fuori dai limiti "
            f"ammissibili [{lim['minimo']:.0f}€ ; {lim['massimo']:.0f}€]. "
            f"Il contributo è comunque calcolato a titolo indicativo."
        )

    tasso_annuo = float(_DATA["tassi_riferimento_annui_pct"][inp.tipologia])
    durata = int(_DATA["piano"]["durata_anni"])
    rate_anno = int(_DATA["piano"]["rate_per_anno"])
    n = int(_DATA["piano"]["n_rate"])

    i = tasso_annuo / 100.0 / rate_anno  # tasso periodale (semestrale)
    P = inp.finanziamento_eur

    # Rata costante (ammortamento francese)
    rata = P * i / (1 - (1 + i) ** (-n))

    # Piano: somma quote interessi = contributo
    piano: list[dict] = []
    debito = P
    contributo = 0.0
    for k in range(1, n + 1):
        interessi = debito * i
        capitale = rata - interessi
        debito_fine = debito - capitale
        contributo += interessi
        piano.append({
            "rata_n": k,
            "quota_interessi_eur": round(interessi, 2),
            "quota_capitale_eur": round(capitale, 2),
            "debito_residuo_eur": round(max(debito_fine, 0.0), 2),
        })
        debito = debito_fine

    contributo_pct = round(contributo / P * 100.0, 4)

    avvertenze.append(
        "La Nuova Sabatini è erogata in regime de minimis (verificare plafond con "
        "de_minimis_plafond) e richiede investimento avviato dopo la domanda."
    )

    return NuovaSabatiniOutput(
        ammissibile=ammissibile,
        tipologia=inp.tipologia,
        tasso_riferimento_annuo_pct=tasso_annuo,
        finanziamento_eur=P,
        durata_anni=durata,
        n_rate=n,
        rata_semestrale_eur=round(rata, 2),
        contributo_totale_eur=round(contributo, 2),
        contributo_su_finanziamento_pct=contributo_pct,
        piano_ammortamento=piano,
        avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={
            "fonte_dati": _DATA["_fonte"],
            "data_validita_dati": _DATA["_data_validita"],
            "tasso_periodale": round(i, 6),
            "metodo": "somma quote interessi ammortamento francese, 5 anni, rate semestrali",
        },
    )
