"""Pre-flight consulenziale: decide se una generazione di report è LEGITTIMA.

Traduce a CODICE il principio della review 'calo ordini': il report è una
CONSEGUENZA della diagnosi e della volontà dell'utente, NON un automatismo guidato
dal completamento dei campi. Modulo PURO (nessun I/O) → testabile in isolamento.

Regole (dalla checklist della review):
  1. Se l'utente ha chiesto di continuare la consulenza (`report_hold`) → SEMPRE bloccato.
  2. Con consenso esplicito (l'utente ha chiesto/accettato il report) → consentito: la
     valutazione se generare la fa l'utente, il gate non gli si mette contro. (L'HOLD resta
     vincolante: è il "no" esplicito, che vince anche sul click.)
  3. Senza consenso esplicito, la diagnosi deve essere SOLIDA (confidenza alta / fase
     'pronto') e non devono restare ipotesi decisive aperte né dati critici mancanti,
     altrimenti → bloccato con 'continua la consulenza'.
  4. Il dominio instradato non deve essere spurio (routeConfidence): sotto soglia, senza
     consenso esplicito, non si genera.
"""
from __future__ import annotations

from typing import Optional


def _open_hypotheses(diag: dict) -> list:
    return [i for i in (diag.get("ipotesi") or [])
            if isinstance(i, dict) and str(i.get("s") or "aperta").strip().lower() == "aperta"]


def evaluate(collected: Optional[dict], servizio_id: Optional[str] = None,
             user_requested: bool = False) -> dict:
    """Ritorna {'allowed': bool, 'reason': str, 'checks': dict}.

    `user_requested`: True quando la generazione parte da un'azione ESPLICITA dell'utente
    (click sulla CTA, procedi, ripresa post-pagamento). Un consenso esplicito supera il gate
    diagnostico ma MAI l'HOLD.
    """
    collected = collected or {}
    diag = collected.get("diagnosi") or {}
    route = collected.get("route_confidence") or {}
    conf = str(diag.get("confidenza") or "").strip().lower()
    fase = str(diag.get("fase") or "").strip().lower()
    open_hyps = _open_hypotheses(diag)

    checks = {
        "report_hold": bool(collected.get("report_hold")),
        "user_consent": bool(user_requested or collected.get("analysis_ready")),
        "confidenza": conf or None,
        "fase": fase or None,
        "open_hypotheses": len(open_hyps),
        "missing_datum": bool(diag.get("manca")),
        # routeConfidence ignoto (nessuna telemetria ancora) → non penalizzare: default True.
        "route_confident": bool(route.get("confident", True)),
        "route_top": route.get("top"),
        "servizio_id": servizio_id,
    }

    # 1. HOLD → blocco duro, sempre. È la volontà esplicita dell'utente.
    if checks["report_hold"]:
        return {"allowed": False, "reason": "hold_utente", "checks": checks}

    # 2. Consenso esplicito → consentito (l'HOLD sopra ha già la precedenza).
    if checks["user_consent"]:
        return {"allowed": True, "reason": "consenso_utente", "checks": checks}

    # 3. Senza consenso: serve una diagnosi solida.
    diag_solid = conf == "alta" or fase == "pronto"
    still_investigating = bool(open_hyps) or checks["missing_datum"]
    if not diag_solid and still_investigating:
        return {"allowed": False, "reason": "diagnosi_non_conclusa", "checks": checks}
    if not diag_solid:
        return {"allowed": False, "reason": "confidenza_insufficiente", "checks": checks}

    # 4. Dominio instradato non confidente → non generare (fallback = consulenza in chat).
    if not checks["route_confident"]:
        return {"allowed": False, "reason": "routing_non_confidente", "checks": checks}

    return {"allowed": True, "reason": "diagnosi_solida", "checks": checks}


def can_generate_report(collected: Optional[dict], servizio_id: Optional[str] = None,
                        user_requested: bool = False) -> bool:
    """Scorciatoia booleana su :func:`evaluate`."""
    return bool(evaluate(collected, servizio_id, user_requested).get("allowed"))
