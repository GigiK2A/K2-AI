"""Iperammortamento 2026 / Transizione 5.0 — beni strumentali 4.0.

FRESHNESS-GATE per anno d'investimento:
- investimenti dal 1/1/2026 → IPERAMMORTAMENTO (L. 199/2025): maggiorazione del costo
  deducibile (+180/100/50% per scaglione di importo), beneficio = risparmio IRES/IRPEF
  DILUITO sull'ammortamento. NON un credito d'imposta, NON fasce di risparmio energetico.
- investimenti 1/1/2024–31/12/2025 → Transizione 5.0 (credito d'imposta per fasce di
  risparmio energetico), regime ABROGATO dal 2026 — calcolo storico/code-residue.

Decreto attuativo MIMIT-MEF non ancora definitivo → `decreto_attuativo: da_confermare`.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "transizione_5_0.json").read_text())
_IPER = _DATA["iperammortamento_2026"]
_STOR = _DATA["transizione_5_0_storico"]


class Transizione50Input(BaseModel):
    investimento_eur: float = Field(
        ..., gt=0,
        description="Importo del progetto ammissibile (beni nuovi 4.0 interconnessi, "
                    "Allegati IV/V L.199/2025 per il 2026).")
    anno_investimento: int = Field(
        2026, ge=2024, le=2028,
        description="Anno in cui il bene è realizzato/entra in funzione (art.109 TUIR). "
                    "≥2026 → iperammortamento; ≤2025 → credito Transizione 5.0 storico.")
    aliquota_imposta_pct: float = Field(
        24, gt=0, le=50,
        description="Aliquota IRES (24% default) o IRPEF marginale per stimare il "
                    "risparmio d'imposta dell'iperammortamento.")
    riduzione_consumi_pct: float | None = Field(
        None, gt=0,
        description="[SOLO regime storico ≤2025] Risparmio energetico %. Ignorato dal "
                    "2026 (premio energetico eliminato).")
    ambito: Literal["struttura", "processo"] = Field(
        "struttura", description="[SOLO regime storico ≤2025] Base del risparmio energetico.")


class Transizione50Output(BaseModel):
    regime: str
    ammissibile: bool
    investimento_eur: float
    investimento_agevolabile_eur: float
    eccedenza_oltre_tetto_eur: float
    dettaglio_scaglioni: list[dict]
    # Iperammortamento 2026
    maggiorazione_deducibile_eur: float | None = None
    risparmio_imposta_stimato_eur: float | None = None
    aliquota_imposta_pct: float | None = None
    # Transizione 5.0 storico
    fascia: str | None = None
    aliquote_per_scaglione_pct: list[float] | None = None
    credito_imposta_eur: float | None = None
    aliquota_media_effettiva_pct: float | None = None
    # Comune
    decreto_attuativo: str
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def _iperammortamento(inp: Transizione50Input) -> Transizione50Output:
    avvertenze = [
        "IPERAMMORTAMENTO (L. 199/2025): NON un credito d'imposta ma una MAGGIORAZIONE "
        "deducibile → beneficio = risparmio IRES/IRPEF DILUITO sull'ammortamento del bene "
        "(non cassa immediata). Richiede capienza fiscale.",
        "NESSUNA fascia di risparmio energetico: il premio energetico è stato ELIMINATO in "
        "sede parlamentare. La maggiorazione dipende SOLO dallo scaglione di importo.",
        "decreto_attuativo MIMIT-MEF non ancora definitivo: parametri operativi (perizia, "
        "interconnessione, comunicazioni GSE) DA CONFERMARE; stima su norma primaria.",
    ]
    if inp.riduzione_consumi_pct is not None:
        avvertenze.append(
            "Input 'riduzione_consumi_pct' IGNORATO nel regime 2026 (premio energetico abolito).")

    inv = inp.investimento_eur
    dettaglio: list[dict] = []
    magg_totale = 0.0
    agevolabile = 0.0
    for sc in _IPER["scaglioni_maggiorazione"]:
        da = float(sc["da"])
        a = float(sc["a"]) if sc["a"] is not None else float("inf")
        quota = max(0.0, min(inv, a) - da)
        if quota <= 0:
            continue
        m_pct = float(sc["maggiorazione_pct"])
        magg = quota * m_pct / 100.0
        magg_totale += magg
        if m_pct > 0:
            agevolabile += quota
        dettaglio.append({
            "scaglione": sc["label"],
            "quota_investimento_eur": round(quota, 2),
            "maggiorazione_pct": m_pct,
            "maggiorazione_deducibile_eur": round(magg, 2),
        })
    eccedenza = max(0.0, inv - 20000000.0)
    if eccedenza > 0:
        avvertenze.append(
            f"Quota oltre 20 M€ ({eccedenza:.0f}€): nessuna maggiorazione su quella parte.")

    risparmio = magg_totale * inp.aliquota_imposta_pct / 100.0
    return Transizione50Output(
        regime="iperammortamento_2026",
        ammissibile=True,
        investimento_eur=inv,
        investimento_agevolabile_eur=round(agevolabile, 2),
        eccedenza_oltre_tetto_eur=round(eccedenza, 2),
        dettaglio_scaglioni=dettaglio,
        maggiorazione_deducibile_eur=round(magg_totale, 2),
        risparmio_imposta_stimato_eur=round(risparmio, 2),
        aliquota_imposta_pct=inp.aliquota_imposta_pct,
        decreto_attuativo=_DATA["decreto_attuativo"],
        avvertenze=avvertenze,
        riferimento_normativo=_IPER["norma"],
        trace={
            "fonte_dati": _DATA["_fonte"],
            "data_validita_dati": _DATA["_data_validita"],
            "regime": "iperammortamento_2026",
            "finestra": _IPER["finestra"],
            "natura": _IPER["natura"],
            "premio_energetico": _IPER["premio_energetico"],
            "beneficio_diluito": True,
        },
    )


def _seleziona_fascia(ambito: str, riduzione_pct: float) -> dict | None:
    for f in _STOR["fasce_riduzione"][ambito]:
        lo, hi = f["min_pct"], f["max_pct"]
        if riduzione_pct >= lo and (hi is None or riduzione_pct < hi):
            return f
    return None


def _transizione_storico(inp: Transizione50Input) -> Transizione50Output:
    avvertenze = [
        "REGIME STORICO Transizione 5.0 (DL 19/2024 art.38), ABROGATO per investimenti dal "
        "1/1/2026. Valido solo per investimenti 2024-2025. Code residue: credito in F24 in "
        "5 quote 2026-2030, comunicazione di completamento entro 28/02/2026.",
    ]
    if inp.riduzione_consumi_pct is None:
        avvertenze.append("Regime storico richiede 'riduzione_consumi_pct': non fornito → non calcolabile.")
        return Transizione50Output(
            regime="transizione_5_0_storico", ammissibile=False, investimento_eur=inp.investimento_eur,
            investimento_agevolabile_eur=0.0, eccedenza_oltre_tetto_eur=0.0, dettaglio_scaglioni=[],
            decreto_attuativo="n/a", avvertenze=avvertenze, riferimento_normativo=_STOR["_fonte"],
            trace={"regime": "storico", "anno": inp.anno_investimento})

    soglia_min = _STOR["soglie_minime_accesso"][f"{inp.ambito}_pct"]
    if inp.riduzione_consumi_pct < soglia_min:
        avvertenze.append(f"NON AMMISSIBILE: risparmio {inp.riduzione_consumi_pct:.2f}% < soglia {soglia_min}%.")
        return Transizione50Output(
            regime="transizione_5_0_storico", ammissibile=False, investimento_eur=inp.investimento_eur,
            investimento_agevolabile_eur=0.0, eccedenza_oltre_tetto_eur=0.0, dettaglio_scaglioni=[],
            credito_imposta_eur=0.0, decreto_attuativo="n/a", avvertenze=avvertenze,
            riferimento_normativo=_STOR["_fonte"], trace={"soglia_minima_pct": soglia_min})

    fascia = _seleziona_fascia(inp.ambito, inp.riduzione_consumi_pct)
    aliquote = fascia["aliquote_per_scaglione"]
    tetto = float(_STOR["tetto_massimo_progetto_eur"])
    agevolabile = min(inp.investimento_eur, tetto)
    eccedenza = max(0.0, inp.investimento_eur - tetto)
    dettaglio, credito = [], 0.0
    for i, sc in enumerate(_STOR["scaglioni_investimento_eur"]):
        quota = max(0.0, min(agevolabile, float(sc["a"])) - float(sc["da"]))
        if quota <= 0:
            continue
        aliq = float(aliquote[i])
        contributo = quota * aliq / 100.0
        credito += contributo
        dettaglio.append({"scaglione": sc["label"], "quota_investimento_eur": round(quota, 2),
                          "aliquota_pct": aliq, "credito_eur": round(contributo, 2)})
    return Transizione50Output(
        regime="transizione_5_0_storico", ammissibile=True, investimento_eur=inp.investimento_eur,
        investimento_agevolabile_eur=round(agevolabile, 2), eccedenza_oltre_tetto_eur=round(eccedenza, 2),
        dettaglio_scaglioni=dettaglio, fascia=fascia["label"],
        aliquote_per_scaglione_pct=[float(x) for x in aliquote], credito_imposta_eur=round(credito, 2),
        aliquota_media_effettiva_pct=round(credito / agevolabile * 100.0, 2) if agevolabile else None,
        decreto_attuativo="n/a", avvertenze=avvertenze, riferimento_normativo=_STOR["_fonte"],
        trace={"regime": "storico", "ambito": inp.ambito, "anno": inp.anno_investimento})


def transizione_5_0(inp: Transizione50Input) -> Transizione50Output:
    """Freshness-gate: ≥2026 → iperammortamento; ≤2025 → credito T5.0 storico (abrogato)."""
    if inp.anno_investimento >= 2026:
        return _iperammortamento(inp)
    return _transizione_storico(inp)
