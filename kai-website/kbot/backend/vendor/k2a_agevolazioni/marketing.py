"""Metriche di marketing — unit economics deterministiche.

Calcola CAC, LTV, rapporto LTV/CAC, payback del CAC, ROAS, ROI e break-even
a partire dai dati di spesa/acquisizione/margine. Confronta con benchmark di
prassi e produce un giudizio sintetico.
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

_DATA = json.loads((Path(__file__).parent / "data" / "marketing_benchmark.json").read_text())


class MarketingInput(BaseModel):
    spesa_marketing_eur: float = Field(..., gt=0, description="Spesa totale di marketing/acquisizione nel periodo.")
    nuovi_clienti: int = Field(..., gt=0, description="Nuovi clienti acquisiti nel periodo.")
    margine_mensile_per_cliente_eur: float = Field(
        ..., gt=0, description="Margine lordo mensile medio per cliente.")
    vita_media_mesi: float | None = Field(
        default=None, gt=0, description="Vita media del cliente in mesi. In alternativa fornire churn_mensile_pct.")
    churn_mensile_pct: float | None = Field(
        default=None, gt=0, description="Tasso di abbandono mensile (%). Vita media = 1/churn.")
    # ROAS / ROI opzionali
    ricavi_da_campagna_eur: float | None = Field(default=None, ge=0, description="Ricavi attribuiti alla campagna (per ROAS/ROI).")
    # Break-even opzionale
    costi_fissi_eur: float | None = Field(default=None, ge=0, description="Costi fissi del periodo (per break-even in numero clienti).")

    @model_validator(mode="after")
    def _vita(self):
        if self.vita_media_mesi is None and self.churn_mensile_pct is None:
            raise ValueError("Fornire vita_media_mesi oppure churn_mensile_pct.")
        return self


class MetricaOut(BaseModel):
    id: str
    label: str
    valore: float
    valutazione: str | None
    soglie: dict | None


class MarketingOutput(BaseModel):
    cac_eur: float
    ltv_eur: float
    ltv_cac: float
    payback_mesi: float
    roas: float | None
    roi_pct: float | None
    break_even_clienti: float | None
    vita_media_mesi: float
    metriche: list[MetricaOut]
    giudizio_sintetico: str
    raccomandazioni: list[str]
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def _valuta(valore: float, s: dict) -> str:
    if s["direzione"] == "alto_meglio":
        if valore >= s["ottimo"]: return "ottimo"
        if valore >= s["buono"]: return "buono"
        if valore >= s["attenzione"]: return "attenzione"
        return "critico"
    else:
        if valore <= s["ottimo"]: return "ottimo"
        if valore <= s["buono"]: return "buono"
        if valore <= s["attenzione"]: return "attenzione"
        return "critico"


def metriche_marketing(inp: MarketingInput) -> MarketingOutput:
    avvertenze = [_DATA["_disclaimer"]]
    raccomandazioni: list[str] = []

    vita = inp.vita_media_mesi if inp.vita_media_mesi is not None else 100.0 / inp.churn_mensile_pct
    cac = inp.spesa_marketing_eur / inp.nuovi_clienti
    ltv = inp.margine_mensile_per_cliente_eur * vita
    ltv_cac = ltv / cac if cac else 0.0
    payback = cac / inp.margine_mensile_per_cliente_eur

    roas = roi = None
    if inp.ricavi_da_campagna_eur is not None:
        roas = round(inp.ricavi_da_campagna_eur / inp.spesa_marketing_eur, 2)
        roi = round((inp.ricavi_da_campagna_eur - inp.spesa_marketing_eur) / inp.spesa_marketing_eur * 100, 1)

    break_even = None
    if inp.costi_fissi_eur is not None:
        break_even = round(inp.costi_fissi_eur / inp.margine_mensile_per_cliente_eur, 1)

    s = _DATA["soglie"]
    metriche = [
        MetricaOut(id="ltv_cac", label=s["ltv_cac"]["label"], valore=round(ltv_cac, 2),
                   valutazione=_valuta(ltv_cac, s["ltv_cac"]), soglie=s["ltv_cac"]),
        MetricaOut(id="payback_mesi", label=s["payback_mesi"]["label"], valore=round(payback, 1),
                   valutazione=_valuta(payback, s["payback_mesi"]), soglie=s["payback_mesi"]),
    ]
    if roas is not None:
        metriche.append(MetricaOut(id="roas", label=s["roas"]["label"], valore=roas,
                                   valutazione=_valuta(roas, s["roas"]), soglie=s["roas"]))

    # Raccomandazioni
    if ltv_cac < s["ltv_cac"]["attenzione"]:
        raccomandazioni.append(f"LTV/CAC = {ltv_cac:.2f} < 1: stai spendendo per acquisire più del valore generato. Rivedere canali e CAC.")
    elif ltv_cac < s["ltv_cac"]["ottimo"]:
        raccomandazioni.append(f"LTV/CAC = {ltv_cac:.2f}: sotto il benchmark 3x. Aumentare LTV (retention/upsell) o ridurre CAC.")
    if payback > s["payback_mesi"]["attenzione"]:
        raccomandazioni.append(f"Payback {payback:.0f} mesi elevato: capitale immobilizzato a lungo, attenzione alla cassa.")

    # Giudizio sintetico
    val_ltvcac = _valuta(ltv_cac, s["ltv_cac"])
    giudizio = f"LTV/CAC {ltv_cac:.2f} ({val_ltvcac}), payback {payback:.0f} mesi"

    return MarketingOutput(
        cac_eur=round(cac, 2), ltv_eur=round(ltv, 2), ltv_cac=round(ltv_cac, 2),
        payback_mesi=round(payback, 1), roas=roas, roi_pct=roi,
        break_even_clienti=break_even, vita_media_mesi=round(vita, 1),
        metriche=metriche, giudizio_sintetico=giudizio, raccomandazioni=raccomandazioni,
        avvertenze=avvertenze, riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "CAC=spesa/clienti; LTV=margine_mensile*vita_media; payback=CAC/margine_mensile",
               "vita_media_fonte": "input" if inp.vita_media_mesi is not None else "1/churn"},
    )
