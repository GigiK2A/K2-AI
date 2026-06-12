"""Layer billing K-BOT — abbonamenti + crediti (logica PURA, no I/O).

Modello fonte: `catalogo_documenti.json` (k2a-mcp-agevolazioni) → sezioni
`abbonamenti` e `crediti`. Finché il `catalog.json` consumato non viene
rigenerato includendole, i valori vivono qui come COSTANTI allineate alla fonte;
`load_model()` preferisce il catalogo se le espone.

Regole di business (dalla fonte):
- Free: 0€, 0 cr, NON esegue servizi (solo account/vetrina/esempi).
- Pro: 49€/mese, 50 cr/mese, -10% sui Boost.
- Business: 149€/mese, 200 cr/mese, -20% sui Boost, 3 utenti.
- Credito: 1 cr = 1€. Inattività max 12 mesi.
- I CREDITI pagano i Check express (strato Consumo). I BOOST restano a prezzo,
  MAI a crediti (anti-cannibalizzazione).
- Pacchetti crediti: 49€→50, 199€→220 (consigliato), 499€→600.
"""
from __future__ import annotations

from typing import Optional

# --- modello costante allineato alla fonte (catalogo_documenti.json) ---------
# Fedele al catalogo sorgente di Luca (catalogo_documenti.json → abbonamenti.piani):
# label e feature INCLUDE comprese. La differenziazione non è solo nei crediti.
PIANI: dict[str, dict] = {
    "free": {"label": "Account gratuito", "prezzo_mese_eur": 0, "crediti_mese": 0,
             "sconto_boost_pct": 0, "utenti": 1, "servizi_eseguibili": False,
             "include": ["Registrazione", "Vetrina servizi", "Documenti di esempio (statici)"]},
    "pro": {"label": "Pro", "prezzo_mese_eur": 49, "crediti_mese": 50,
            "sconto_boost_pct": 10, "utenti": 1, "servizi_eseguibili": True,
            "include": ["Utility: memo→testo, calendario/Drive, traduttore", "50 crediti/mese",
                        "-10% sui Boost", "Area personale e storico"]},
    "business": {"label": "Studio", "prezzo_mese_eur": 149, "crediti_mese": 200,
                 "sconto_boost_pct": 20, "utenti": 3, "servizi_eseguibili": True,
                 "include": ["Tutto Pro", "200 crediti/mese", "3 utenti", "-20% sui Boost",
                             "Priorità di elaborazione"]},
}
VALORE_CREDITO_EUR = 1
INATTIVITA_MAX_MESI = 12
PACCHETTI_CREDITI = [
    {"prezzo_eur": 49,  "crediti": 50},
    {"prezzo_eur": 199, "crediti": 220, "consigliato": True},
    {"prezzo_eur": 499, "crediti": 600},
]
# Strati che si pagano a CREDITI (Consumo). Gli altri (servizio/tappa/...) a prezzo.
STRATI_A_CREDITI = {"consumo"}


def piano(plan_id: Optional[str]) -> dict:
    return PIANI.get((plan_id or "free").lower(), PIANI["free"])


def puo_eseguire_servizi(plan_id: Optional[str]) -> bool:
    return bool(piano(plan_id)["servizi_eseguibili"])


def sconto_boost_pct(plan_id: Optional[str]) -> int:
    return int(piano(plan_id)["sconto_boost_pct"])


def crediti_mensili(plan_id: Optional[str]) -> int:
    return int(piano(plan_id)["crediti_mese"])


def prezzo_boost_scontato(prezzo_base_eur: int, plan_id: Optional[str]) -> int:
    """Prezzo Boost con lo sconto dell'abbonato (arrotondato all'euro)."""
    sconto = sconto_boost_pct(plan_id)
    return int(round(prezzo_base_eur * (100 - sconto) / 100))


def costo_crediti(servizio: dict) -> Optional[int]:
    """Quanti crediti costa un servizio di strato Consumo; None se NON a crediti.

    I Boost (strato 'servizio') tornano None → vanno pagati a prezzo, mai crediti.
    """
    strato = servizio.get("strato")
    if strato not in STRATI_A_CREDITI:
        return None
    # costo esplicito o derivato dal prezzo (1 cr = 1€)
    if servizio.get("costo_crediti") is not None:
        return int(servizio["costo_crediti"])
    prezzo = servizio.get("prezzo_documento_eur") or servizio.get("prezzo_eur") or 0
    return int(round(prezzo / VALORE_CREDITO_EUR))


def pacchetto_crediti(prezzo_eur: int) -> Optional[dict]:
    return next((p for p in PACCHETTI_CREDITI if p["prezzo_eur"] == prezzo_eur), None)


def load_model(catalog: Optional[dict] = None) -> dict:
    """Modello effettivo: dal catalogo se espone abbonamenti/crediti, altrimenti
    dalle costanti. Ponte finché `catalog.json` non viene rigenerato dalla fonte."""
    if catalog:
        ab = (catalog.get("abbonamenti") or {})
        piani = ab.get("piani") if isinstance(ab, dict) else None
        cr = catalog.get("crediti")
        if piani and cr:
            return {"piani": piani, "crediti": cr, "fonte": "catalog.json"}
    return {"piani": PIANI, "crediti": {"valore_credito_eur": VALORE_CREDITO_EUR,
            "inattivita_max_mesi": INATTIVITA_MAX_MESI, "pacchetti": PACCHETTI_CREDITI},
            "fonte": "costanti (catalog non rigenerato)"}
