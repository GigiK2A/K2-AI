"""Modelli Pydantic per input budget."""
from __future__ import annotations

from pydantic import BaseModel, Field, PositiveFloat, NonNegativeFloat, PositiveInt, field_validator


class BilancioBase(BaseModel):
    ricavi_eur_anno_base: PositiveFloat
    costi_variabili_eur_anno_base: NonNegativeFloat
    costi_fissi_eur_anno_base: NonNegativeFloat
    ammortamenti_eur_anno_base: NonNegativeFloat = 0
    oneri_finanziari_eur_anno_base: NonNegativeFloat = 0


class AssunzioniProiezione(BaseModel):
    crescita_ricavi_pct_anno: float = 2.0  # default inflazione ISTAT 2026
    stagionalita_mensile_12: list[float] = Field(default_factory=lambda: [1.0] * 12)
    elasticita_costi_variabili_su_ricavi: float = 1.0
    crescita_costi_fissi_pct_anno: float = 2.0
    capex_eur_anno: NonNegativeFloat = 0
    vita_utile_capex_anni: PositiveInt = 5
    wc_giorni: int = 0  # delta WC; 0 = neutrale

    @field_validator("stagionalita_mensile_12")
    @classmethod
    def _check_stag(cls, v: list[float]) -> list[float]:
        if len(v) != 12:
            raise ValueError("stagionalita_mensile_12 deve avere 12 elementi")
        if any(x < 0 for x in v):
            raise ValueError("stagionalita_mensile_12 non puo' avere valori negativi")
        if sum(v) <= 0:
            raise ValueError("stagionalita_mensile_12 deve avere somma > 0")
        return v
