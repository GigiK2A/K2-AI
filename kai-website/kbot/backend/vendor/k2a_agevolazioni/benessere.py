"""Metriche benessere/estetica — indicatori gestionali dei servizi alla persona.

Calcola tasso di utilizzo della capacità (poltrone/cabine), scontrino medio,
ricavo per ora-operatore, incidenza del personale, retail mix, tasso di ritorno
clienti e break-even. Servizio SETTORIALE (settore: benessere_estetica).
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

_DATA = json.loads((Path(__file__).parent / "data" / "benessere_benchmark.json").read_text())


class BenessereInput(BaseModel):
    ricavi_totali_eur: float = Field(..., gt=0, description="Ricavi totali del periodo.")
    ricavi_prodotti_eur: float = Field(0.0, ge=0, description="Ricavi da vendita prodotti (per retail mix).")
    n_clienti: int = Field(..., gt=0, description="Numero di clienti/trattamenti serviti nel periodo.")
    ore_disponibili: float | None = Field(default=None, gt=0, description="Ore-operatore disponibili (capacità).")
    ore_erogate: float | None = Field(default=None, ge=0, description="Ore di servizio effettivamente erogate.")
    costo_personale_eur: float = Field(..., ge=0, description="Costo del personale del periodo.")
    clienti_di_ritorno: int | None = Field(default=None, ge=0, description="Clienti già visti in precedenza (per retention).")
    costi_fissi_eur: float | None = Field(default=None, ge=0, description="Costi fissi del periodo (per break-even clienti).")

    @model_validator(mode="after")
    def _coerenza(self):
        if self.ore_erogate is not None and self.ore_disponibili is not None and self.ore_erogate > self.ore_disponibili + 0.01:
            raise ValueError("ore_erogate non possono superare ore_disponibili.")
        if self.clienti_di_ritorno is not None and self.clienti_di_ritorno > self.n_clienti:
            raise ValueError("clienti_di_ritorno non possono superare n_clienti.")
        if self.ricavi_prodotti_eur > self.ricavi_totali_eur + 0.01:
            raise ValueError("ricavi_prodotti non possono superare i ricavi_totali.")
        return self


class KpiBen(BaseModel):
    id: str
    label: str
    valore: float
    valutazione: str
    soglie: dict


class BenessereOutput(BaseModel):
    scontrino_medio_eur: float
    tasso_utilizzo_pct: float | None
    ricavo_per_ora_operatore_eur: float | None
    incidenza_personale_pct: float
    retail_mix_pct: float
    retention_pct: float | None
    margine_contribuzione_per_cliente_eur: float
    break_even_clienti: float | None
    kpi: list[KpiBen]
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


def metriche_benessere(inp: BenessereInput) -> BenessereOutput:
    avvertenze = [_DATA["_disclaimer"]]
    raccomandazioni: list[str] = []

    scontrino = inp.ricavi_totali_eur / inp.n_clienti
    incidenza_personale = inp.costo_personale_eur / inp.ricavi_totali_eur * 100
    retail_mix = inp.ricavi_prodotti_eur / inp.ricavi_totali_eur * 100

    tasso_utilizzo = ricavo_ora = None
    if inp.ore_disponibili:
        if inp.ore_erogate is not None:
            tasso_utilizzo = inp.ore_erogate / inp.ore_disponibili * 100
        ore_base = inp.ore_erogate if inp.ore_erogate else inp.ore_disponibili
        if ore_base:
            ricavo_ora = inp.ricavi_totali_eur / ore_base

    retention = None
    if inp.clienti_di_ritorno is not None:
        retention = inp.clienti_di_ritorno / inp.n_clienti * 100

    # Margine di contribuzione per cliente: ricavi - costo personale (variabile dominante nei servizi)
    mc_cliente = (inp.ricavi_totali_eur - inp.costo_personale_eur) / inp.n_clienti

    break_even = None
    if inp.costi_fissi_eur is not None and mc_cliente > 0:
        break_even = round(inp.costi_fissi_eur / mc_cliente, 1)
        if break_even > inp.n_clienti:
            raccomandazioni.append(
                f"Break-even {break_even:.0f} clienti > clienti attuali {inp.n_clienti}: "
                "sotto pareggio, agire su scontrino, utilizzo e costi fissi.")

    s = _DATA["soglie"]
    kpi: list[KpiBen] = []
    if tasso_utilizzo is not None:
        kpi.append(KpiBen(id="tasso_utilizzo_pct", label=s["tasso_utilizzo_pct"]["label"],
                          valore=round(tasso_utilizzo, 2), valutazione=_valuta(tasso_utilizzo, s["tasso_utilizzo_pct"]),
                          soglie=s["tasso_utilizzo_pct"]))
    kpi.append(KpiBen(id="incidenza_personale_pct", label=s["incidenza_personale_pct"]["label"],
                      valore=round(incidenza_personale, 2), valutazione=_valuta(incidenza_personale, s["incidenza_personale_pct"]),
                      soglie=s["incidenza_personale_pct"]))
    if retention is not None:
        kpi.append(KpiBen(id="retention_pct", label=s["retention_pct"]["label"],
                          valore=round(retention, 2), valutazione=_valuta(retention, s["retention_pct"]),
                          soglie=s["retention_pct"]))

    if tasso_utilizzo is not None and _valuta(tasso_utilizzo, s["tasso_utilizzo_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Utilizzo capacità {tasso_utilizzo:.1f}% basso: ottimizzare agenda, "
                               "promemoria appuntamenti e riempimento fasce vuote.")
    if retention is not None and _valuta(retention, s["retention_pct"]) in ("attenzione", "critico"):
        raccomandazioni.append(f"Retention {retention:.1f}% bassa: introdurre richiami, abbonamenti "
                               "e programmi fedeltà.")
    if retail_mix < 5:
        raccomandazioni.append(f"Retail mix {retail_mix:.1f}% basso: la vendita di prodotti è un margine "
                               "facile, formare il personale al cross-sell.")

    return BenessereOutput(
        scontrino_medio_eur=round(scontrino, 2),
        tasso_utilizzo_pct=round(tasso_utilizzo, 2) if tasso_utilizzo is not None else None,
        ricavo_per_ora_operatore_eur=round(ricavo_ora, 2) if ricavo_ora is not None else None,
        incidenza_personale_pct=round(incidenza_personale, 2),
        retail_mix_pct=round(retail_mix, 2),
        retention_pct=round(retention, 2) if retention is not None else None,
        margine_contribuzione_per_cliente_eur=round(mc_cliente, 2),
        break_even_clienti=break_even,
        kpi=kpi, raccomandazioni=raccomandazioni, avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "utilizzo=ore_erogate/ore_disponibili; scontrino=ricavi/clienti; MC_cliente=(ricavi-personale)/clienti",
               "retention_calcolata": retention is not None},
    )
