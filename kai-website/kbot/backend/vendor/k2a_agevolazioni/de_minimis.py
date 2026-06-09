"""De minimis — plafond residuo su finestra mobile 3 anni (Reg. UE 2023/2831).

Reg. UE 2023/2831 art.3 §2: il massimale si applica su qualsiasi periodo di
3 anni (finestra mobile rolling day-by-day), NON più sull'esercizio finanziario
corrente + 2 precedenti (regola del previgente Reg. 1407/2013).
"""
from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_SOGLIE = json.loads((Path(__file__).parent / "data" / "de_minimis_soglie.json").read_text())


class AiutoDeMinimis(BaseModel):
    importo_eur: float = Field(..., gt=0, description="Importo aiuto concesso (ESL — equivalente sovvenzione lordo)")
    data_concessione: date = Field(..., description="Data di concessione dell'aiuto (formato YYYY-MM-DD)")
    descrizione: str = Field("", description="Riferimento aiuto (bando, atto), opzionale")


class DeMinimisPlafondInput(BaseModel):
    aiuti_ricevuti: list[AiutoDeMinimis] = Field(
        default_factory=list,
        description="Aiuti de minimis già concessi all'impresa (impresa unica).")
    settore: Literal["generale", "sieg", "agricoltura_primaria", "pesca_acquacoltura"] = Field(
        "generale", description="Settore che determina il massimale applicabile.")
    data_riferimento: date | None = Field(
        default=None,
        description="Data rispetto a cui calcolare la finestra mobile di 3 anni. "
                    "Default: oggi. Per simulare un nuovo aiuto futuro, impostare la "
                    "data prevista di concessione.")
    nuovo_aiuto_eur: float | None = Field(
        default=None, gt=0,
        description="Importo di un nuovo aiuto da verificare. Se fornito, controlla "
                    "se è capiente entro il plafond residuo.")


class DeMinimisPlafondOutput(BaseModel):
    settore: str
    massimale_eur: float
    finestra_inizio: date
    finestra_fine: date
    usato_nella_finestra_eur: float
    plafond_residuo_eur: float
    aiuti_dentro_finestra: list[dict]
    aiuti_fuori_finestra: list[dict]
    prossima_liberazione: dict | None
    nuovo_aiuto_capiente: bool | None
    nuovo_aiuto_msg: str | None
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def de_minimis_plafond(inp: DeMinimisPlafondInput) -> DeMinimisPlafondOutput:
    avvertenze: list[str] = []

    soglia_node = _SOGLIE["soglie_eur"][inp.settore]
    massimale = float(soglia_node["massimale"])
    if soglia_node.get("_da_validare"):
        avvertenze.append(
            f"Massimale settore '{inp.settore}' = {massimale:.0f}€ è un PLACEHOLDER "
            f"da validare ({soglia_node.get('regolamento', '')}). "
            f"Verificare su EUR-Lex / portale RNA prima dell'uso ufficiale."
        )

    data_rif = inp.data_riferimento or date.today()
    # Finestra mobile 3 anni: [data_rif - 3 anni + 1 giorno ; data_rif]
    # (qualsiasi periodo di 3 anni — Reg. 2023/2831 art.3 §2)
    finestra_inizio = data_rif - timedelta(days=3 * 365)
    finestra_fine = data_rif

    dentro: list[dict] = []
    fuori: list[dict] = []
    usato = 0.0
    for a in inp.aiuti_ricevuti:
        rec = {
            "importo_eur": a.importo_eur,
            "data_concessione": a.data_concessione.isoformat(),
            "descrizione": a.descrizione,
        }
        if finestra_inizio <= a.data_concessione <= finestra_fine:
            usato += a.importo_eur
            dentro.append(rec)
        else:
            fuori.append(rec)

    residuo = massimale - usato

    # Prossima liberazione: quando il più vecchio aiuto DENTRO la finestra ne esce
    prossima = None
    if dentro:
        aiuto_piu_vecchio = min(
            inp.aiuti_ricevuti,
            key=lambda a: a.data_concessione,
        ) if dentro else None
        # consideriamo solo gli aiuti effettivamente dentro
        dentro_date = [
            a for a in inp.aiuti_ricevuti
            if finestra_inizio <= a.data_concessione <= finestra_fine
        ]
        if dentro_date:
            piu_vecchio = min(dentro_date, key=lambda a: a.data_concessione)
            data_uscita = piu_vecchio.data_concessione + timedelta(days=3 * 365)
            prossima = {
                "data": data_uscita.isoformat(),
                "importo_liberato_eur": piu_vecchio.importo_eur,
                "descrizione": piu_vecchio.descrizione,
                "nota": "Data oltre la quale l'aiuto più vecchio esce dalla finestra "
                        "mobile di 3 anni, liberando plafond.",
            }

    # Verifica nuovo aiuto
    nuovo_capiente = None
    nuovo_msg = None
    if inp.nuovo_aiuto_eur is not None:
        nuovo_capiente = inp.nuovo_aiuto_eur <= residuo
        if nuovo_capiente:
            nuovo_msg = (
                f"OK: nuovo aiuto {inp.nuovo_aiuto_eur:.0f}€ capiente "
                f"(residuo {residuo:.0f}€). Plafond dopo concessione: "
                f"{residuo - inp.nuovo_aiuto_eur:.0f}€."
            )
        else:
            ecc = inp.nuovo_aiuto_eur - residuo
            nuovo_msg = (
                f"KO: nuovo aiuto {inp.nuovo_aiuto_eur:.0f}€ supera il residuo "
                f"{residuo:.0f}€ di {ecc:.0f}€. Lo sforamento anche di 1€ rende "
                f"l'intero aiuto non concedibile in de minimis (no frazionamento)."
            )

    if residuo < 0:
        avvertenze.append(
            f"ATTENZIONE: aiuti già concessi nella finestra ({usato:.0f}€) superano "
            f"il massimale ({massimale:.0f}€). Verificare correttezza dati / impresa unica."
        )

    avvertenze.append(
        "Il calcolo assume il perimetro 'impresa unica' (Reg. 2023/2831 art.2 §2): "
        "includere gli aiuti di tutte le imprese collegate/controllate."
    )

    return DeMinimisPlafondOutput(
        settore=inp.settore,
        massimale_eur=massimale,
        finestra_inizio=finestra_inizio,
        finestra_fine=finestra_fine,
        usato_nella_finestra_eur=round(usato, 2),
        plafond_residuo_eur=round(residuo, 2),
        aiuti_dentro_finestra=dentro,
        aiuti_fuori_finestra=fuori,
        prossima_liberazione=prossima,
        nuovo_aiuto_capiente=nuovo_capiente,
        nuovo_aiuto_msg=nuovo_msg,
        avvertenze=avvertenze,
        riferimento_normativo=soglia_node.get("regolamento", "Reg. UE 2023/2831"),
        trace={
            "fonte_dati": _SOGLIE["_fonte"],
            "data_validita_dati": _SOGLIE["_data_validita"],
            "metodo_finestra": "periodo mobile 3 anni (rolling) — Reg. 2023/2831 art.3 §2",
            "data_riferimento": data_rif.isoformat(),
            "n_aiuti_totali": len(inp.aiuti_ricevuti),
            "n_dentro_finestra": len(dentro),
        },
    )
