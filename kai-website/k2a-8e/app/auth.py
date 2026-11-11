"""Bearer auth backend-to-backend. Supporta 2 chiavi per rotazione (G6) + il bearer
interno di default come fallback robusto.

NB (test 31, 11/11/2026): il commento storico diceva «l'8e non è pubblico». In produzione `k2-ai-8e` HA un dominio pubblico
(`*.up.railway.app`) e `_INTERNAL_DEFAULT` (scritto nel codice) apriva `/v1/catalog`, `/v1/render`, `/v1/norme/verify` e la lettura di
un job a chiunque conoscesse il repository. Con `K2A_8E_REJECT_DEFAULT=1` il valore predefinito NON è più accettato (neanche se è
quello configurato in `K2A_8E_API_KEY`): ci vuole una chiave vera, uguale su 8e e backend. Spento di default: attivarlo SOLO dopo aver
impostato la stessa chiave nuova su entrambi i servizi (sequenza in docs/test-31-piano-operativo-2026-11.md), altrimenti il motore cade.
"""
from __future__ import annotations

import hmac
import logging
import os

from fastapi import Header, HTTPException

from .settings import API_KEY, API_KEY_NEXT

log = logging.getLogger(__name__)
_INTERNAL_DEFAULT = "k2a-8e-internal-loopback"


def _rifiuta_default() -> bool:
    return os.environ.get("K2A_8E_REJECT_DEFAULT", "") == "1"


def chiavi_valide() -> set:
    chiavi = {k for k in (API_KEY, API_KEY_NEXT) if k}
    if _rifiuta_default():
        chiavi.discard(_INTERNAL_DEFAULT)
    else:
        chiavi.add(_INTERNAL_DEFAULT)
    return chiavi


def avvisa_se_chiave_predefinita() -> None:
    """Una riga di log all'avvio se il servizio accetta ancora la chiave predefinita (non va nell'/health pubblico)."""
    if _INTERNAL_DEFAULT in chiavi_valide():
        log.warning("8e: la chiave predefinita del codice è ancora accettata (K2A_8E_REJECT_DEFAULT non attivo)")


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.split(" ", 1)[1].strip()
    if not any(hmac.compare_digest(token.encode(), k.encode()) for k in chiavi_valide()):      # tempo costante
        raise HTTPException(status_code=403, detail="bad key")
