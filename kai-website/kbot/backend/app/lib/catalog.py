"""Catalog loader — fonte unica prezzi/servizi/percorsi lato K-BOT.

Legge `app/data/catalog.json` (interim editato a mano; target: generato da
k2a-catalogo via CI — vedi docs/interfaccia-kbot-8e.md §2).

L'interfaccia di queste funzioni è il contratto su cui si appoggiano
`services.py`, gli endpoint di checkout/upsell e il client 8e. NON cambiare le
firme senza aggiornare i call site.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    from ..settings import CATALOG_PATH  # type: ignore
except Exception:  # pragma: no cover - fallback se settings non importabile
    CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog.json"

log = logging.getLogger(__name__)

_EMPTY: dict = {
    "version": "0",
    "servizi": [],
    "percorsi": [],
    "abbonamenti": [],
    "mapping_tag_to_servizi": {},
}


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    try:
        return json.loads(Path(CATALOG_PATH).read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("Catalog load failed (%s): %s", CATALOG_PATH, exc)
        return dict(_EMPTY)


def invalidate() -> None:
    """Svuota la cache (chiamare dopo un redeploy che aggiorna catalog.json)."""
    load_catalog.cache_clear()


def catalog_version() -> str:
    return str(load_catalog().get("version", "0"))


def engine_expectations() -> dict:
    return dict(load_catalog().get("engine") or {})


# ---- Servizi -------------------------------------------------------------

def lista_servizi(tipo: Optional[str] = None) -> list[dict]:
    servizi = load_catalog().get("servizi", [])
    if tipo is None:
        return list(servizi)
    return [s for s in servizi if s.get("tipo") == tipo]


def get_servizio(servizio_id: Optional[str]) -> Optional[dict]:
    if not servizio_id:
        return None
    return next((s for s in load_catalog().get("servizi", []) if s["id"] == servizio_id), None)


def genera_via(servizio_id: str) -> Optional[str]:
    s = get_servizio(servizio_id)
    return s.get("genera_via") if s else None


def is_8e_generabile(servizio_id: str) -> bool:
    """True se il servizio si genera via 8e (ha blueprint). False per high-touch."""
    s = get_servizio(servizio_id)
    return bool(s and s.get("genera_via") == "8e" and s.get("blueprint_id"))


def blueprint_id(servizio_id: str) -> Optional[str]:
    s = get_servizio(servizio_id)
    return s.get("blueprint_id") if s else None


# ---- Prezzi --------------------------------------------------------------

def prezzo_eur(servizio_id: str) -> int:
    s = get_servizio(servizio_id)
    return int(s.get("prezzo_eur", 0)) if s else 0


def prezzo_per_piano(servizio_id: str, piano: Optional[str]) -> int:
    """Prezzo scontato per piano abbonamento (L3). Senza piano = prezzo pieno."""
    base = prezzo_eur(servizio_id)
    if not piano:
        return base
    abbonamenti = {a["id"]: a for a in load_catalog().get("abbonamenti", [])}
    sconto = int(abbonamenti.get(piano, {}).get("sconto_tappa_pct", 0))
    return int(round(base * (100 - sconto) / 100))


# ---- Percorsi ------------------------------------------------------------

def lista_percorsi() -> list[dict]:
    return list(load_catalog().get("percorsi", []))


def get_percorso(percorso_id: Optional[str]) -> Optional[dict]:
    if not percorso_id:
        return None
    return next((p for p in load_catalog().get("percorsi", []) if p["id"] == percorso_id), None)


def scheda_percorso(percorso_id: str) -> Optional[dict]:
    """Percorso + tappe risolte (con prezzi) + destinazione + totale tappe."""
    p = get_percorso(percorso_id)
    if not p:
        return None
    tappe = [get_servizio(t) for t in p.get("tappe_id_ordinate", [])]
    tappe = [t for t in tappe if t is not None]
    return {
        **p,
        "destinazione": get_servizio(p.get("destinazione_id")),
        "tappe": tappe,
        "prezzo_tappe_totale": sum(int(t.get("prezzo_eur", 0)) for t in tappe),
    }


# ---- Mapping tag pillar SEO → servizi (scenario C) -----------------------

def servizio_per_tag(tag: str, kind: str = "boost_primario") -> Optional[dict]:
    """Dato un tag P01-P20, ritorna il servizio mappato (check | boost_primario)."""
    mapping = load_catalog().get("mapping_tag_to_servizi", {}).get(tag, {})
    return get_servizio(mapping.get(kind))


def check_per_tag(tag: str) -> Optional[dict]:
    return servizio_per_tag(tag, kind="check")


def boost_per_tag(tag: str) -> Optional[dict]:
    return servizio_per_tag(tag, kind="boost_primario")
