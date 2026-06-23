"""Metriche hospitality — KPI di revenue management alberghiero (USALI).

Calcola in modo deterministico i KPI chiave di una struttura ricettiva:
occupazione, ADR, RevPAR, TRevPAR, GOP/GOPPAR e l'occupazione di break-even.
Servizio SETTORIALE (settore: turismo_ricettivita).
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

_DATA = json.loads((Path(__file__).parent / "data" / "hospitality_benchmark.json").read_text())


class HospitalityInput(BaseModel):
    camere: int = Field(..., gt=0, description="Numero di camere disponibili (fisiche).")
    giorni: int = Field(..., gt=0, description="Giorni del periodo analizzato.")
    camere_vendute: int | None = Field(
        default=None, ge=0, description="Camere-notte vendute nel periodo. In alternativa fornire tasso_occupazione_pct.")
    tasso_occupazione_pct: float | None = Field(
        default=None, gt=0, le=100, description="Tasso di occupazione (%) se non si forniscono le camere vendute.")
    ricavi_camere_eur: float = Field(..., gt=0, description="Ricavi camere (room revenue) del periodo.")
    ricavi_totali_eur: float | None = Field(
        default=None, gt=0, description="Ricavi totali (camere + F&B + extra) per TRevPAR e GOP.")
    costi_operativi_eur: float | None = Field(
        default=None, ge=0, description="Costi operativi totali del periodo (per GOP/GOPPAR).")
    costi_fissi_eur: float | None = Field(
        default=None, ge=0, description="Costi fissi del periodo (per break-even occupancy).")
    costo_variabile_per_camera_eur: float = Field(
        0.0, ge=0, description="Costo variabile per camera occupata (pulizia, amenities, OTA fee).")

    @model_validator(mode="after")
    def _occ(self):
        if self.camere_vendute is None and self.tasso_occupazione_pct is None:
            raise ValueError("Fornire camere_vendute oppure tasso_occupazione_pct.")
        disponibili = self.camere * self.giorni
        if self.camere_vendute is not None and self.camere_vendute > disponibili:
            raise ValueError("camere_vendute non può superare camere×giorni disponibili.")
        return self


class KpiHosp(BaseModel):
    id: str
    label: str
    valore: float
    valutazione: str | None
    soglie: dict | None


class HospitalityOutput(BaseModel):
    camere_disponibili_notti: int
    camere_vendute: int
    occupazione_pct: float
    adr_eur: float
    revpar_eur: float
    trevpar_eur: float | None
    gop_eur: float | None
    goppar_eur: float | None
    gop_margin_pct: float | None
    ricavi_extra_camera_eur: float | None
    incidenza_extra_camera_pct: float | None
    break_even_occupazione_pct: float | None
    punteggio_0_100: float
    kpi: list[KpiHosp]
    raccomandazioni: list[str]
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


_PUNTI = {"ottimo": 100, "buono": 70, "attenzione": 40, "critico": 10}


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


def metriche_hospitality(inp: HospitalityInput) -> HospitalityOutput:
    avvertenze = [_DATA["_disclaimer"]]
    raccomandazioni: list[str] = []

    disponibili = inp.camere * inp.giorni
    if inp.camere_vendute is not None:
        vendute = inp.camere_vendute
    else:
        vendute = round(inp.tasso_occupazione_pct / 100 * disponibili)
    occ_pct = round(vendute / disponibili * 100, 2)

    adr = inp.ricavi_camere_eur / vendute if vendute else 0.0
    revpar = inp.ricavi_camere_eur / disponibili

    trevpar = gop = goppar = gop_margin = None
    if inp.ricavi_totali_eur is not None:
        trevpar = inp.ricavi_totali_eur / disponibili
        if inp.costi_operativi_eur is not None:
            gop = inp.ricavi_totali_eur - inp.costi_operativi_eur
            goppar = gop / disponibili
            gop_margin = gop / inp.ricavi_totali_eur * 100

    # Break-even occupancy: copertura costi fissi col margine di contribuzione per camera
    break_even = None
    if inp.costi_fissi_eur is not None:
        mc = adr - inp.costo_variabile_per_camera_eur
        if mc > 0:
            camere_be = inp.costi_fissi_eur / mc
            break_even = round(min(100.0, camere_be / disponibili * 100), 2)
            if break_even > occ_pct:
                raccomandazioni.append(
                    f"Occupazione break-even {break_even}% > occupazione attuale {occ_pct}%: "
                    "sotto la soglia di pareggio, agire su tariffe/costi o domanda.")
        else:
            avvertenze.append("Margine di contribuzione per camera ≤ 0: ADR non copre il costo "
                              "variabile, break-even non calcolabile.")

    s = _DATA["soglie"]
    kpi = [KpiHosp(id="occupazione_pct", label=s["occupazione_pct"]["label"], valore=occ_pct,
                   valutazione=_valuta(occ_pct, s["occupazione_pct"]), soglie=s["occupazione_pct"])]
    if gop_margin is not None:
        kpi.append(KpiHosp(id="gop_margin_pct", label=s["gop_margin_pct"]["label"],
                           valore=round(gop_margin, 2),
                           valutazione=_valuta(gop_margin, s["gop_margin_pct"]), soglie=s["gop_margin_pct"]))

    if _valuta(occ_pct, s["occupazione_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Occupazione {occ_pct}% sotto i livelli ottimali: "
                               "rivedere distribuzione, OTA mix e politiche tariffarie.")

    # Ricavi extra-camera (F&B, servizi, extra)
    ricavi_extra = incidenza_extra = None
    if inp.ricavi_totali_eur is not None:
        ricavi_extra = inp.ricavi_totali_eur - inp.ricavi_camere_eur
        incidenza_extra = ricavi_extra / inp.ricavi_totali_eur * 100 if inp.ricavi_totali_eur else None

    # Punteggio 0-100 deterministico (media dei KPI valutati, con penalità se sotto break-even)
    punti = [_PUNTI[k.valutazione] for k in kpi if k.valutazione in _PUNTI]
    punteggio = sum(punti) / len(punti) if punti else 0.0
    if break_even is not None and break_even > occ_pct:
        punteggio = max(0.0, punteggio - 20)  # sotto il pareggio: penalità

    return HospitalityOutput(
        camere_disponibili_notti=disponibili, camere_vendute=vendute, occupazione_pct=occ_pct,
        adr_eur=round(adr, 2), revpar_eur=round(revpar, 2),
        trevpar_eur=round(trevpar, 2) if trevpar is not None else None,
        gop_eur=round(gop, 2) if gop is not None else None,
        goppar_eur=round(goppar, 2) if goppar is not None else None,
        gop_margin_pct=round(gop_margin, 2) if gop_margin is not None else None,
        ricavi_extra_camera_eur=round(ricavi_extra, 2) if ricavi_extra is not None else None,
        incidenza_extra_camera_pct=round(incidenza_extra, 2) if incidenza_extra is not None else None,
        break_even_occupazione_pct=break_even,
        punteggio_0_100=round(punteggio, 1),
        kpi=kpi, raccomandazioni=raccomandazioni, avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "USALI: occ=vendute/disponibili; ADR=room_rev/vendute; RevPAR=room_rev/disponibili; GOPPAR=GOP/disponibili",
               "camere_vendute_fonte": "input" if inp.camere_vendute is not None else "da tasso_occupazione"},
    )
