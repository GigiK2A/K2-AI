"""Metriche ristorazione — indicatori gestionali deterministici.

Calcola food cost, beverage cost, prime cost, incidenza del personale,
scontrino medio, margine di contribuzione per coperto e break-even coperti.
Servizio SETTORIALE (settore: ristorazione_food).
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

_DATA = json.loads((Path(__file__).parent / "data" / "ristorazione_benchmark.json").read_text())


class RistorazioneInput(BaseModel):
    ricavi_totali_eur: float = Field(..., gt=0, description="Ricavi totali del periodo.")
    ricavi_food_eur: float | None = Field(default=None, ge=0, description="Ricavi food (se distinti); altrimenti food cost calcolato sui ricavi totali.")
    ricavi_beverage_eur: float | None = Field(default=None, ge=0, description="Ricavi beverage (se distinti).")
    costo_food_eur: float = Field(..., ge=0, description="Costo materie prime food (acquisti food).")
    costo_beverage_eur: float = Field(0.0, ge=0, description="Costo materie prime beverage.")
    costo_personale_eur: float = Field(..., ge=0, description="Costo del personale del periodo.")
    coperti: int = Field(..., gt=0, description="Numero di coperti serviti nel periodo.")
    giorni: int | None = Field(default=None, gt=0, description="Giorni di apertura (per break-even coperti/giorno).")
    costi_fissi_eur: float | None = Field(default=None, ge=0, description="Costi fissi del periodo (per break-even).")

    @model_validator(mode="after")
    def _coerenza(self):
        if self.ricavi_food_eur is not None and self.ricavi_food_eur > self.ricavi_totali_eur + 1:
            raise ValueError("ricavi_food non può superare i ricavi_totali.")
        return self


class KpiRist(BaseModel):
    id: str
    label: str
    valore: float
    valutazione: str
    soglie: dict


class RistorazioneOutput(BaseModel):
    scontrino_medio_eur: float
    food_cost_pct: float
    beverage_cost_pct: float | None
    prime_cost_pct: float
    incidenza_personale_pct: float
    margine_contribuzione_per_coperto_eur: float
    break_even_coperti: float | None
    break_even_coperti_giorno: float | None
    kpi: list[KpiRist]
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


def metriche_ristorazione(inp: RistorazioneInput) -> RistorazioneOutput:
    avvertenze = [_DATA["_disclaimer"]]
    raccomandazioni: list[str] = []

    base_food = inp.ricavi_food_eur if inp.ricavi_food_eur else inp.ricavi_totali_eur
    food_cost = inp.costo_food_eur / base_food * 100

    beverage_cost = None
    if inp.ricavi_beverage_eur:
        beverage_cost = inp.costo_beverage_eur / inp.ricavi_beverage_eur * 100

    prime_cost = (inp.costo_food_eur + inp.costo_beverage_eur + inp.costo_personale_eur) / inp.ricavi_totali_eur * 100
    incidenza_personale = inp.costo_personale_eur / inp.ricavi_totali_eur * 100
    scontrino = inp.ricavi_totali_eur / inp.coperti

    # Margine di contribuzione per coperto: ricavi - costi variabili (food+beverage)
    mc_coperto = (inp.ricavi_totali_eur - inp.costo_food_eur - inp.costo_beverage_eur) / inp.coperti

    break_even = break_even_giorno = None
    if inp.costi_fissi_eur is not None:
        # Includiamo il personale tra i costi da coprire col margine di contribuzione "industriale"
        if mc_coperto > 0:
            break_even = round((inp.costi_fissi_eur + inp.costo_personale_eur) / mc_coperto, 1)
            if inp.giorni:
                break_even_giorno = round(break_even / inp.giorni, 1)
            if break_even > inp.coperti:
                raccomandazioni.append(
                    f"Break-even {break_even:.0f} coperti > coperti attuali {inp.coperti}: "
                    "sotto la soglia di pareggio, agire su scontrino medio/costi.")
        else:
            avvertenze.append("Margine di contribuzione per coperto ≤ 0: i costi variabili "
                              "superano il ricavo medio, break-even non calcolabile.")

    s = _DATA["soglie"]
    kpi = [
        KpiRist(id="food_cost_pct", label=s["food_cost_pct"]["label"], valore=round(food_cost, 2),
                valutazione=_valuta(food_cost, s["food_cost_pct"]), soglie=s["food_cost_pct"]),
        KpiRist(id="prime_cost_pct", label=s["prime_cost_pct"]["label"], valore=round(prime_cost, 2),
                valutazione=_valuta(prime_cost, s["prime_cost_pct"]), soglie=s["prime_cost_pct"]),
        KpiRist(id="incidenza_personale_pct", label=s["incidenza_personale_pct"]["label"], valore=round(incidenza_personale, 2),
                valutazione=_valuta(incidenza_personale, s["incidenza_personale_pct"]), soglie=s["incidenza_personale_pct"]),
    ]

    if _valuta(food_cost, s["food_cost_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Food cost {food_cost:.1f}% elevato: rivedere ricette, porzionatura, "
                               "fornitori e sprechi.")
    if _valuta(prime_cost, s["prime_cost_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Prime cost {prime_cost:.1f}% oltre soglia: agire su food cost e/o "
                               "produttività del personale.")

    return RistorazioneOutput(
        scontrino_medio_eur=round(scontrino, 2),
        food_cost_pct=round(food_cost, 2),
        beverage_cost_pct=round(beverage_cost, 2) if beverage_cost is not None else None,
        prime_cost_pct=round(prime_cost, 2),
        incidenza_personale_pct=round(incidenza_personale, 2),
        margine_contribuzione_per_coperto_eur=round(mc_coperto, 2),
        break_even_coperti=break_even,
        break_even_coperti_giorno=break_even_giorno,
        kpi=kpi, raccomandazioni=raccomandazioni, avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "food_cost=costo_food/ricavi_food; prime_cost=(food+bev+labor)/ricavi; MC_coperto=(ricavi-food-bev)/coperti",
               "base_food_cost": "ricavi_food" if inp.ricavi_food_eur else "ricavi_totali"},
    )
