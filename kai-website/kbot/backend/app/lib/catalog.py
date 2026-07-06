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


# Cache manuale: memoizza SOLO una lettura VALIDA. Con @lru_cache un fallimento
# transitorio a startup (I/O race) memoizzava _EMPTY per tutta la vita del processo
# → routing default e PREZZI A 0 per sempre. Ora il ramo d'errore ritorna il fallback
# SENZA cacharlo: una lettura successiva può ancora avere successo.
_CATALOG_CACHE: Optional[dict] = None


def load_catalog() -> dict:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE
    try:
        data = json.loads(Path(CATALOG_PATH).read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("Catalog load failed (%s): %s", CATALOG_PATH, exc)
        return dict(_EMPTY)  # NON cachato → riprova alla prossima chiamata
    _CATALOG_CACHE = data
    return _CATALOG_CACHE


def invalidate() -> None:
    """Svuota la cache (chiamare dopo un redeploy che aggiorna catalog.json)."""
    global _CATALOG_CACHE
    _CATALOG_CACHE = None


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


# Lo sconto abbonato sui Boost vive in billing.prezzo_boost_scontato(base, plan)
# (-10% Pro / -20% Business), usato da api/checkout.py: è l'UNICO path corretto.
# Qui c'era prezzo_per_piano(): dead code (zero chiamanti) che leggeva `abbonamenti`
# vuoti e `sconto_tappa_pct` → ritornava SEMPRE il prezzo pieno anche per Pro/Business.
# Rimosso per non lasciare una mina sul prezzo. Se servirà uno sconto-per-tappa sui
# PERCORSI, va costruito ex-novo su billing + dati `abbonamenti` reali + test.


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
# Negazione prima di una keyword: 'non ho bilancio', 'senza fatturato', 'non ho nessun
# tipo di documento tipo il bilancio' → NON è intento per quel boost. Cerchiamo un
# marcatore di negazione nelle ULTIME ~6 PAROLE INTERE prima della keyword (non su uno
# slice a caratteri fissi, che era cieco oltre ~3 token o quando tagliava le parole).
# Vedi _NEGATION_MARKERS e _negated_before in suggest_boost.
_NEGATION_MARKERS = frozenset((
    "non", "senza", "niente", "nessun", "nessuna", "nessuno", "nessun'",
    "né", "nè", "mai", "privo", "priva", "manca", "mancano", "mancante",
    "manco", "assenza", "assente", "sprovvisto", "sprovvista", "no",
))
_NEG_WINDOW_WORDS = 6  # quante parole intere guardare a ritroso dalla keyword

# Apostrofi curvi → dritto: le keyword (es. "credito d'imposta", "cessione d'azienda")
# usano l'apostrofo ASCII; un testo utente con '’'/'‘' non combaciava con re.escape.
_APOSTROPHES = {"’": "'", "‘": "'", "ʼ": "'", "´": "'", "`": "'"}


def _normalize_text(text: str) -> str:
    """Minuscolo + apostrofi curvi normalizzati a ASCII: rende il match keyword
    tollerante alla forma tipografica dell'apostrofo."""
    text = (text or "").lower()
    for src, dst in _APOSTROPHES.items():
        if src in text:
            text = text.replace(src, dst)
    return text


def _negated_before(text: str, kw_start: int) -> bool:
    """True se un marcatore di negazione compare nelle ultime ~6 parole INTERE prima
    della keyword. Lavora su parole, non su uno slice a caratteri fissi: coglie
    'non ho nessun tipo di documento tipo il bilancio' (negazione lontana dalla keyword)."""
    before_words = text[:kw_start].split()[-_NEG_WINDOW_WORDS:]
    for w in before_words:
        # strip punteggiatura ai bordi ('non,' → 'non'); tiene l'apostrofo interno.
        token = w.strip(".,;:!?()[]\"'«»").lower()
        if token in _NEGATION_MARKERS:
            return True
    return False

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
    # "roi" rimosso come keyword singola: falsi positivi su contesti marketing ("ROI campagna")
    # dirottavano un'analisi marketing su FinanceBoost. Il finanziario resta coperto dalle
    # keyword forti (bilanci/cash flow/margini/bancabilità/…). "investiment" tenuto: nel
    # dubbio un investimento è più finanziario che marketing, e ha co-keyword forti a fianco.
    (("bilanci", "finanziar", "cash flow", "liquidità", "bancabil", "margini", "solvibil", "rating", "investiment", "payback"), "checkup_finanziario"),
    (("controllo di gestione", "kpi", "cruscotto", "reporting direzionale", "monitoraggio"), "checkup_controllo"),
    (("marketing", "brand", "awareness", "notorietà", "visibilità", "campagn", "funnel", "social",
      "lead generation", "acquisizione clienti", "studio di mercato", "competitor", "benchmark",
      "comunicazione", "pubblicità", "advertising"), "checkup_marketing"),
    # Strategia/crescita → StrategyBoost (checkup_marketing = "Strategia e crescita"):
    # è il suo scope esatto (posizionamento competitivo, canali di crescita, entry
    # mercati). Prima puntava a ControlBoost (workaround di quando qui c'era
    # checkup_advisor, che falliva la validazione) → una diagnosi strategica finiva
    # sul "cruscotto direzionale" e il form chiedeva mese/costi_operativi = vicolo
    # cieco. AdvisorBoost resta scegliibile a mano dal selettore del pannello.
    (("strateg", "crescita", "business plan", "piano industriale", "fattibilità", "espansione"), "checkup_marketing"),
]

# Default quando nessuna keyword combacia: ControlBoost (cruscotto direzionale),
# generico e robusto. NB: ex checkup_advisor, ma AdvisorBoost ha lo schema più
# stringente (12 sezioni, campi numerici obbligatori) e fallisce la validazione
# più spesso → non adatto come fallback finché non viene irrobustito.
_BOOST_DEFAULT = "checkup_controllo"


def suggest_boost(summary: Optional[dict], explicit_only: bool = False,
                  user_text: Optional[str] = None) -> Optional[dict]:
    """Dal riepilogo conversazione → il Boost 8e più adatto (selettore catalogo).

    Deterministico (keyword match, primo vince) con default generico. Ritorna il
    servizio dict se 8e-generabile, altrimenti il primo Boost generabile a
    catalogo, altrimenti None. Mai solleva: il routing non deve bloccare la chat.

    `user_text` (opzionale): il testo dei messaggi UTENTE. Entra in PASS 1 DAVANTI a
    reportType/deliverableType: se l'LLM ha messo in reportType il contenuto del SITO
    analizzato (es. "analisi bilancio" su uno studio commercialista) mentre l'utente ha
    chiesto "parere SEO", deve vincere la richiesta dell'utente. Con user_text=None il
    comportamento è identico a prima (backward-compatible).
    """
    summary = summary or {}

    def _match(text: str) -> Optional[str]:
        # SCORE-BASED (allineato a infer_service_id_from_session, che fa girare le SKILL):
        # conta le occorrenze di keyword per gruppo e vince il PIÙ menzionato → l'INTENTO
        # (es. "marketing"/"seo", citati più volte) batte il SETTORE incidentale (es.
        # "edilizia" nominato di sfuggita), che con il vecchio first-match-per-ordine dirottava
        # un'analisi marketing su BuildBoost. A PARITÀ vince il primo gruppo (ordine-dominio).
        # \b a inizio keyword: niente match parziali ("nda" dentro "aziendale").
        # NEGAZIONE: una keyword preceduta da 'non/senza/né/niente/nessun' entro ~3 parole NON
        # è intento — 'non ho bilancio né fatturato' NON deve instradare a FinanceBoost (l'utente
        # dice che quei dati NON ce li ha). Senza questo, un «senza dati» finiva su FinanceBoost.
        best_sid, best_score = None, 0
        for keys, sid in _BOOST_KEYWORDS:
            score = 0
            for k in keys:
                for mt in re.finditer(r"\b" + re.escape(k), text):
                    if not _negated_before(text, mt.start()):
                        score += 1
            if score > best_score:
                best_sid, best_score = sid, score
        return best_sid

    # PASS 1 — l'INTENTO esplicito (testo utente + reportType/deliverableType) vince sui
    # termini INCIDENTALI in objective/scope/notes: il SETTORE del cliente ("edilizia") o
    # frasi come "acquisizione clienti" NON devono dirottare un report di marketing su
    # BuildBoost o LegalBoost DD. Il testo utente è davanti: l'arbitro resta l'ordine dei
    # gruppi keyword (domini specifici prima), così "parere SEO" batte "analisi bilancio".
    intent = _normalize_text(str(user_text or "") + " "
              + " ".join(str(summary.get(k) or "") for k in ("reportType", "deliverableType")))
    chosen = _match(intent)
    # PASS 2 — fallback sull'intero riepilogo se l'intento non è già instradabile.
    if not chosen:
        full = _normalize_text(" ".join(
            str(summary.get(k) or "")
            for k in ("reportType", "deliverableType", "objective", "businessType", "scope", "notes")
        ))
        if user_text:
            full = _normalize_text(str(user_text)) + " " + full
        chosen = _match(full)
    if not chosen and explicit_only:
        return None          # nessun match esplicito → il chiamante tiene il boost corrente
    chosen = chosen or _BOOST_DEFAULT
    if not is_8e_generabile(chosen):
        chosen = next(
            (s["id"] for s in load_catalog().get("servizi", []) if is_8e_generabile(s["id"])),
            None,
        )
    return get_servizio(chosen)
