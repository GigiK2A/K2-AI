"""Metriche e-commerce — indicatori gestionali deterministici.

Calcola conversion rate, AOV, ricavo per sessione, margine di contribuzione netto
(al netto di COGS, spedizioni e commissioni), incidenza di spedizioni/commissioni,
tasso di reso e ROAS. Servizio SETTORIALE (settore: ecommerce_digitale).
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

_DATA = json.loads((Path(__file__).parent / "data" / "ecommerce_benchmark.json").read_text())


class EcommerceInput(BaseModel):
    sessioni: int = Field(..., gt=0, description="Sessioni/visite del periodo.")
    ordini: int = Field(..., gt=0, description="Ordini completati nel periodo.")
    ricavi_eur: float = Field(..., gt=0, description="Ricavi (fatturato) del periodo.")
    costo_venduto_eur: float = Field(..., ge=0, description="Costo del venduto (COGS).")
    costo_spedizioni_eur: float = Field(0.0, ge=0, description="Costo totale spedizioni a carico dello shop.")
    commissioni_eur: float = Field(0.0, ge=0, description="Commissioni marketplace/pagamenti totali.")
    resi: int | None = Field(default=None, ge=0, description="Numero di ordini resi (per tasso di reso).")
    valore_resi_eur: float | None = Field(default=None, ge=0, description="Valore dei resi; se assente stimato come resi×AOV.")
    spesa_marketing_eur: float | None = Field(default=None, ge=0, description="Spesa adv del periodo (per ROAS).")

    @model_validator(mode="after")
    def _coerenza(self):
        if self.ordini > self.sessioni:
            raise ValueError("Gli ordini non possono superare le sessioni.")
        if self.resi is not None and self.resi > self.ordini:
            raise ValueError("I resi non possono superare gli ordini.")
        return self


class KpiEcom(BaseModel):
    id: str
    label: str
    valore: float
    valutazione: str
    soglie: dict


class EcommerceOutput(BaseModel):
    conversion_rate_pct: float
    aov_eur: float
    ricavo_per_sessione_eur: float
    margine_lordo_pct: float
    margine_contribuzione_eur: float
    margine_contribuzione_pct: float
    margine_contribuzione_per_ordine_eur: float
    incidenza_spedizioni_pct: float
    incidenza_commissioni_pct: float
    tasso_reso_pct: float | None
    valore_resi_eur: float | None
    roas: float | None
    kpi: list[KpiEcom]
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


def metriche_ecommerce(inp: EcommerceInput) -> EcommerceOutput:
    avvertenze = [_DATA["_disclaimer"]]
    raccomandazioni: list[str] = []

    cr = inp.ordini / inp.sessioni * 100
    aov = inp.ricavi_eur / inp.ordini
    rps = inp.ricavi_eur / inp.sessioni

    margine_lordo = inp.ricavi_eur - inp.costo_venduto_eur
    margine_lordo_pct = margine_lordo / inp.ricavi_eur * 100

    mc = inp.ricavi_eur - inp.costo_venduto_eur - inp.costo_spedizioni_eur - inp.commissioni_eur
    mc_pct = mc / inp.ricavi_eur * 100
    mc_per_ordine = mc / inp.ordini

    inc_sped = inp.costo_spedizioni_eur / inp.ricavi_eur * 100
    inc_comm = inp.commissioni_eur / inp.ricavi_eur * 100

    tasso_reso = valore_resi = None
    if inp.resi is not None:
        tasso_reso = inp.resi / inp.ordini * 100
        valore_resi = inp.valore_resi_eur if inp.valore_resi_eur is not None else inp.resi * aov

    roas = None
    if inp.spesa_marketing_eur:
        roas = inp.ricavi_eur / inp.spesa_marketing_eur

    s = _DATA["soglie"]
    kpi = [
        KpiEcom(id="conversion_rate_pct", label=s["conversion_rate_pct"]["label"], valore=round(cr, 2),
                valutazione=_valuta(cr, s["conversion_rate_pct"]), soglie=s["conversion_rate_pct"]),
        KpiEcom(id="margine_contribuzione_pct", label=s["margine_contribuzione_pct"]["label"], valore=round(mc_pct, 2),
                valutazione=_valuta(mc_pct, s["margine_contribuzione_pct"]), soglie=s["margine_contribuzione_pct"]),
    ]
    if tasso_reso is not None:
        kpi.append(KpiEcom(id="tasso_reso_pct", label=s["tasso_reso_pct"]["label"], valore=round(tasso_reso, 2),
                           valutazione=_valuta(tasso_reso, s["tasso_reso_pct"]), soglie=s["tasso_reso_pct"]))

    if _valuta(cr, s["conversion_rate_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Conversion rate {cr:.2f}% basso: ottimizzare UX, pagina prodotto, "
                               "checkout e velocità del sito.")
    if mc_pct < s["margine_contribuzione_pct"]["attenzione"]:
        raccomandazioni.append(f"Margine di contribuzione {mc_pct:.1f}% eroso: agire su prezzo, "
                               "costo spedizioni e commissioni di canale.")
    if tasso_reso is not None and _valuta(tasso_reso, s["tasso_reso_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Tasso di reso {tasso_reso:.1f}% elevato: migliorare schede prodotto, "
                               "taglie/foto e gestione aspettative.")
    if inc_sped > 15:
        raccomandazioni.append(f"Incidenza spedizioni {inc_sped:.1f}% alta: rivedere corrieri, soglie "
                               "di spedizione gratuita e packaging.")

    return EcommerceOutput(
        conversion_rate_pct=round(cr, 2), aov_eur=round(aov, 2), ricavo_per_sessione_eur=round(rps, 2),
        margine_lordo_pct=round(margine_lordo_pct, 2),
        margine_contribuzione_eur=round(mc, 2), margine_contribuzione_pct=round(mc_pct, 2),
        margine_contribuzione_per_ordine_eur=round(mc_per_ordine, 2),
        incidenza_spedizioni_pct=round(inc_sped, 2), incidenza_commissioni_pct=round(inc_comm, 2),
        tasso_reso_pct=round(tasso_reso, 2) if tasso_reso is not None else None,
        valore_resi_eur=round(valore_resi, 2) if valore_resi is not None else None,
        roas=round(roas, 2) if roas is not None else None,
        kpi=kpi, raccomandazioni=raccomandazioni, avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "CR=ordini/sessioni; AOV=ricavi/ordini; MC=ricavi-COGS-spedizioni-commissioni",
               "valore_resi_fonte": "input" if inp.valore_resi_eur is not None else ("stima resi×AOV" if inp.resi else "n/d")},
    )
