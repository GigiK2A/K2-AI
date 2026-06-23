"""Accesso allo snapshot quant + i 3 campi mancanti (spec Luca §2).

Lo snapshot Damodaran ESISTE già in k2a_quant/data/industry_multiples.json
(20 settori con beta_unlevered + multipli, country_data con rf/erp/tax). Mancano
solo, per `valida_assunzioni` e il size premium del CAPM:
  - g_range_pct        per settore (banda g perpetuo ammessa)
  - banda_cagr_fcf_pct per settore (tolleranza CAGR FCF vs storico)
  - size_premium       per fascia di fatturato (top-level)
  - as_of              esplicito (oggi è solo in _source come testo)

Questi VALORI sono elaborazione di Luca (non Damodaran). Qui forniamo:
  - default ragionevoli (dalla spec §2) usati se il settore non ha override
  - helper per leggere lo snapshot in modo uniforme
"""
from __future__ import annotations

from typing import Any

# Default dalla spec §2 (Luca tara per settore). g in %, banda in punti %.
DEFAULT_G_RANGE_PCT = [0.5, 2.0]
DEFAULT_BANDA_CAGR_FCF_PCT = 8.0
SIZE_PREMIUM = [
    ("ricavi_0_1M", 1_000_000, 0.025),
    ("ricavi_1_10M", 10_000_000, 0.014),
    ("ricavi_10_50M", 50_000_000, 0.008),
    ("ricavi_oltre_50M", float("inf"), 0.005),
]


def snapshot_as_of(snapshot: dict) -> Any:
    return snapshot.get("as_of") or snapshot.get("_source")


def sector(snapshot: dict, settore: str) -> dict | None:
    secs = snapshot.get("sectors") or {}
    sec = secs.get(settore)
    # Risoluzione alias dichiarata nel sector (es. retail_online → retail_general).
    # Limite di sicurezza: max 3 salti per evitare loop.
    for _ in range(3):
        if not sec:
            return None
        alias = sec.get("_alias_a")
        if not alias:
            return sec
        sec = secs.get(alias)
    return sec


def country(snapshot: dict, paese: str = "italy") -> dict:
    return (snapshot.get("country_data") or {}).get(paese, {})


def g_range(snapshot: dict, settore: str) -> list:
    sec = sector(snapshot, settore) or {}
    return sec.get("g_range_pct") or DEFAULT_G_RANGE_PCT


def banda_cagr(snapshot: dict, settore: str) -> float:
    sec = sector(snapshot, settore) or {}
    return float(sec.get("banda_cagr_fcf_pct", DEFAULT_BANDA_CAGR_FCF_PCT))


def size_premium(fatturato_eur: float) -> tuple[str, float]:
    for nome, cap, prem in SIZE_PREMIUM:
        if fatturato_eur <= cap:
            return nome, prem
    return SIZE_PREMIUM[-1][0], SIZE_PREMIUM[-1][2]
