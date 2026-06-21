"""Metriche retail / commercio al dettaglio — indicatori gestionali deterministici.

Calcola margine commerciale, markup, rotazione di magazzino, giorni di giacenza,
GMROI, ricavo per mq, sell-through, scontrino medio e break-even.
Servizio SETTORIALE (settore: commercio_dettaglio).
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field


_DATA = json.loads((Path(__file__).parent / "data" / "retail_benchmark.json").read_text())


class RetailInput(BaseModel):
    ricavi_eur: float = Field(..., gt=0, description="Ricavi di vendita del periodo.")
    costo_venduto_eur: float = Field(..., gt=0, description="Costo del venduto (COGS) del periodo.")
    giacenza_media_eur: float | None = Field(
        default=None, gt=0, description="Giacenza media di magazzino a costo (per rotazione/GMROI).")
    mq_vendita: float | None = Field(default=None, gt=0, description="Superficie di vendita in mq (per ricavo/mq).")
    n_scontrini: int | None = Field(default=None, gt=0, description="Numero di scontrini/transazioni (per scontrino medio).")
    unita_vendute: int | None = Field(default=None, ge=0, description="Unità vendute (per sell-through).")
    unita_ricevute: int | None = Field(default=None, gt=0, description="Unità ricevute/acquistate (per sell-through).")
    costi_fissi_eur: float | None = Field(default=None, ge=0, description="Costi fissi del periodo (per break-even ricavi).")
    giorni: int = Field(365, gt=0, description="Giorni del periodo (per annualizzare la rotazione). Default 365.")


class KpiRetail(BaseModel):
    id: str
    label: str
    valore: float
    valutazione: str
    soglie: dict


class RetailOutput(BaseModel):
    margine_commerciale_pct: float
    markup_pct: float
    rotazione_magazzino: float | None
    giorni_giacenza: float | None
    gmroi: float | None
    ricavo_per_mq_eur: float | None
    scontrino_medio_eur: float | None
    sell_through_pct: float | None
    break_even_ricavi_eur: float | None
    kpi: list[KpiRetail]
    raccomandazioni: list[str]
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def _valuta(v: float, s: dict) -> str:
    if s["direzione"] == "alto_meglio":
        if v >= s["ottimo"]: return "ottimo"
        if v >= s["buono"]: return "buono"
        if v >= s["attenzione"]: return "attenzione"
        return "critico"
    if v <= s["ottimo"]: return "ottimo"
    if v <= s["buono"]: return "buono"
    if v <= s["attenzione"]: return "attenzione"
    return "critico"


def metriche_retail(inp: RetailInput) -> RetailOutput:
    avvertenze = [_DATA["_disclaimer"]]
    raccomandazioni: list[str] = []

    margine_lordo = inp.ricavi_eur - inp.costo_venduto_eur
    margine_pct = margine_lordo / inp.ricavi_eur * 100
    markup_pct = margine_lordo / inp.costo_venduto_eur * 100

    rotazione = giorni_giac = gmroi = None
    if inp.giacenza_media_eur:
        rotazione_periodo = inp.costo_venduto_eur / inp.giacenza_media_eur
        # annualizza la rotazione in base ai giorni del periodo
        rotazione = rotazione_periodo * (365 / inp.giorni)
        giorni_giac = 365 / rotazione if rotazione else None
        gmroi = margine_lordo / inp.giacenza_media_eur

    ricavo_mq = inp.ricavi_eur / inp.mq_vendita if inp.mq_vendita else None
    scontrino = inp.ricavi_eur / inp.n_scontrini if inp.n_scontrini else None
    sell_through = None
    if inp.unita_vendute is not None and inp.unita_ricevute:
        sell_through = inp.unita_vendute / inp.unita_ricevute * 100

    break_even = None
    if inp.costi_fissi_eur is not None:
        mc_ratio = margine_pct / 100
        if mc_ratio > 0:
            break_even = round(inp.costi_fissi_eur / mc_ratio, 2)
            if break_even > inp.ricavi_eur:
                raccomandazioni.append(
                    f"Ricavi di break-even {break_even:.0f}€ > ricavi attuali {inp.ricavi_eur:.0f}€: "
                    "sotto la soglia di pareggio, agire su margine/volumi/costi fissi.")

    s = _DATA["soglie"]
    kpi = [KpiRetail(id="margine_commerciale_pct", label=s["margine_commerciale_pct"]["label"],
                     valore=round(margine_pct, 2), valutazione=_valuta(margine_pct, s["margine_commerciale_pct"]),
                     soglie=s["margine_commerciale_pct"])]
    if rotazione is not None:
        kpi.append(KpiRetail(id="rotazione_magazzino", label=s["rotazione_magazzino"]["label"],
                             valore=round(rotazione, 2), valutazione=_valuta(rotazione, s["rotazione_magazzino"]),
                             soglie=s["rotazione_magazzino"]))
    if gmroi is not None:
        kpi.append(KpiRetail(id="gmroi", label=s["gmroi"]["label"], valore=round(gmroi, 2),
                             valutazione=_valuta(gmroi, s["gmroi"]), soglie=s["gmroi"]))

    if _valuta(margine_pct, s["margine_commerciale_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Margine commerciale {margine_pct:.1f}% basso: rivedere pricing, "
                               "mix di prodotto e condizioni di acquisto.")
    if rotazione is not None and _valuta(rotazione, s["rotazione_magazzino"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Rotazione magazzino {rotazione:.1f}x bassa: capitale immobilizzato "
                               "in stock, ridurre giacenze lente e gestire i resi.")

    return RetailOutput(
        margine_commerciale_pct=round(margine_pct, 2), markup_pct=round(markup_pct, 2),
        rotazione_magazzino=round(rotazione, 2) if rotazione is not None else None,
        giorni_giacenza=round(giorni_giac, 1) if giorni_giac is not None else None,
        gmroi=round(gmroi, 2) if gmroi is not None else None,
        ricavo_per_mq_eur=round(ricavo_mq, 2) if ricavo_mq is not None else None,
        scontrino_medio_eur=round(scontrino, 2) if scontrino is not None else None,
        sell_through_pct=round(sell_through, 2) if sell_through is not None else None,
        break_even_ricavi_eur=break_even,
        kpi=kpi, raccomandazioni=raccomandazioni, avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "margine=(ricavi-cogs)/ricavi; rotazione=cogs/giacenza×(365/giorni); GMROI=margine_lordo/giacenza",
               "rotazione_annualizzata": rotazione is not None},
    )
