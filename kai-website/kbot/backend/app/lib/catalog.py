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
import re
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


# Boost NON ancora vendibili in pipeline: i numeri di valutazione (EV/DCF/WACC)
# li produrrebbe l'LLM, non un calcolo deterministico (debito #1). AdvisorBoost
# torna vendibile quando arriva il motore quant (k2a-mcp-quant + percorso
# agentico con valida_assunzioni). Vedi docs/handoff-luca-poc-agent-sdk-*.
_NON_VENDIBILI = {"checkup_advisor"}


def is_vendibile(servizio_id: str) -> bool:
    """False per i boost gated (valutazione da LLM) o marcati vendibile=false a catalogo."""
    s = get_servizio(servizio_id)
    if not s:
        return False
    if servizio_id in _NON_VENDIBILI:
        return False
    return s.get("vendibile") is not False


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


# ---- Selettore di catalogo: conversazione → Boost 8e ---------------------
# Mappa keyword → servizio_id (tutti 8e-generabili). Primo match vince. I domini
# specifici (legale, fiscale, edilizia, energia, sicurezza...) PRIMA dei generici
# (controllo, marketing, strategia), così "due diligence M&A" non finisce su
# StrategyBoost. È il routing deterministico che trasforma il K-BOT in un
# selettore del catalogo di Luca: a fine conversazione propone il deliverable.
_BOOST_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("due diligence", "m&a", "fusione", "acquisizione di azienda", "acquisizione aziendale",
      "acquisizione societaria", "acquisto di azienda", "cessione d'azienda", "cessione di ramo",
      "cessione di quote"), "checkup_legale_dd"),
    (("contratt", "nda", "clausol", "contract review", "review legale"), "checkup_legale_review"),
    (("legale", "avvocat", "causa", "contenzioso", "parere legale", "diffida"), "primo_parere_legale"),
    (("fiscal", "iva", "tribut", "tasse", "imposte", "f24", "dichiarazione dei redditi"), "checkup_fiscale"),
    (("agevolazion", "bando", "contribut", "incentiv", "sabatini", "credito d'imposta", "finanza agevolata"), "checkup_agevolazioni"),
    (("edilizi", "permesso di costruire", "scia", "cila", "urbanistic", "titolo edilizio"), "checkup_edilizia"),
    (("energ", "efficientamento", "ege", "diagnosi energetica", "fotovoltaic", "impianti termici"), "checkup_energia"),
    (("sicurezz", "dvr", "antincendio", "81/08", "rspp", "infortun"), "checkup_sicurezza_safetyboost"),
    (("hotel", "ricettiv", "ristorant", "hospitality", "struttura ricettiva", "albergo", "b&b"), "checkup_hospitality"),
    (("seo", "sito web", "posizionamento organico", "keyword", "traffico organico", "reputazione online", "sentiment"), "checkup_seo"),
    (("bilanci", "finanziar", "cash flow", "liquidità", "bancabil", "margini", "solvibil", "rating", "investiment", "roi", "payback"), "checkup_finanziario"),
    (("controllo di gestione", "kpi", "cruscotto", "reporting direzionale", "monitoraggio"), "checkup_controllo"),
    (("marketing", "brand", "awareness", "notorietà", "visibilità", "campagn", "funnel", "social",
      "lead generation", "acquisizione clienti", "studio di mercato", "competitor", "benchmark",
      "comunicazione", "pubblicità", "advertising"), "checkup_marketing"),
    # NB: ex checkup_advisor, ma AdvisorBoost fallisce la validazione (schema
    # numerico stringente) → instrado su ControlBoost finché non è irrobustito.
    # AdvisorBoost resta scegliibile a mano dal selettore del pannello.
    (("strateg", "crescita", "business plan", "piano industriale", "fattibilità", "espansione"), "checkup_controllo"),
]

# Default quando nessuna keyword combacia: ControlBoost (cruscotto direzionale),
# generico e robusto. NB: ex checkup_advisor, ma AdvisorBoost ha lo schema più
# stringente (12 sezioni, campi numerici obbligatori) e fallisce la validazione
# più spesso → non adatto come fallback finché non viene irrobustito.
_BOOST_DEFAULT = "checkup_controllo"


def suggest_boost(summary: Optional[dict]) -> Optional[dict]:
    """Dal riepilogo conversazione → il Boost 8e più adatto (selettore catalogo).

    Deterministico (keyword match, primo vince) con default generico. Ritorna il
    servizio dict se 8e-generabile, altrimenti il primo Boost generabile a
    catalogo, altrimenti None. Mai solleva: il routing non deve bloccare la chat.
    """
    summary = summary or {}

    def _match(text: str) -> Optional[str]:
        # Match a CONFINE DI PAROLA (\b a inizio keyword), non per sottostringa: evita
        # falsi positivi tipo "nda" dentro "aziendale" → LegalBoost su un bilancio.
        for keys, sid in _BOOST_KEYWORDS:
            if any(re.search(r"\b" + re.escape(k), text) for k in keys):
                return sid
        return None

    # PASS 1 — l'INTENTO esplicito (reportType/deliverableType) vince sui termini
    # INCIDENTALI che compaiono in objective/scope/notes: il SETTORE del cliente
    # ("edilizia") o frasi come "acquisizione clienti" NON devono dirottare un
    # report di marketing su BuildBoost o LegalBoost DD. (bug reale giu 2026)
    intent = " ".join(str(summary.get(k) or "") for k in ("reportType", "deliverableType")).lower()
    chosen = _match(intent)
    # PASS 2 — fallback sull'intero riepilogo se l'intento non è già instradabile.
    if not chosen:
        full = " ".join(
            str(summary.get(k) or "")
            for k in ("reportType", "deliverableType", "objective", "businessType", "scope", "notes")
        ).lower()
        chosen = _match(full)
    chosen = chosen or _BOOST_DEFAULT
    if not is_8e_generabile(chosen):
        chosen = next(
            (s["id"] for s in load_catalog().get("servizi", []) if is_8e_generabile(s["id"])),
            None,
        )
    return get_servizio(chosen)
