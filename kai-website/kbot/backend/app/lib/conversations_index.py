"""Indice delle conversazioni (`kbot_conversations`) — logica condivisa.

`kbot_conversations` è la riga di cronologia in sidebar; `kbot_sessions` è il contenuto.
Due tabelle, due fonti di verità, e questo modulo tiene allineate le due cose che
divergevano:

1. **updated_at.** Era toccato solo da un PATCH del frontend (rinomina o bind della
   sessione), quindi un turno di chat non lo muoveva: la cronologia restava ordinata per
   data di CREAZIONE e una conversazione vecchia ripresa oggi rimaneva in fondo alla lista.
2. **Sessioni orfane.** La dashboard legge `/sessions`, la chat legge `/conversations`.
   Una sessione nata anonima e poi rivendicata al login, o una `POST /conversations`
   fallita per un errore di rete, produce una conversazione che esiste nel DB ed è
   INVISIBILE in cronologia. Qui vengono recuperate e materializzate.

Tutto best-effort: un problema d'indice non deve mai rompere né la chat né la lista.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)

TABLE = "kbot_conversations"
_TITLE_MAX = 48
# Quante sessioni orfane materializzare per singola chiamata: un utente con storico lungo
# non deve trasformare l'apertura della chat in una migrazione.
_BACKFILL_LIMIT = 50
# Quante sessioni guardare a caccia di orfani. È una select di soli `id`, quindi il tetto
# serve solo a non far crescere la query senza limiti.
_SESSION_SCAN_LIMIT = 200
# Sotto questa soglia di messaggi non è una conversazione: è una sessione aperta e
# abbandonata (o creata da un tag pillar), e non merita una riga in cronologia.
_MIN_MESSAGES = 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_missing_table_error(exc: Exception) -> bool:
    """Postgrest PGRST205 (schema cache miss) — tabella non esistente."""
    msg = str(exc).lower()
    return "pgrst205" in msg or "schema cache" in msg or "could not find the table" in msg


def _is_duplicate_error(exc: Exception) -> bool:
    """Violazione di unicità (23505): la riga è già stata creata da una richiesta parallela."""
    msg = str(exc).lower()
    return "23505" in msg or "duplicate key" in msg or "already exists" in msg


def touch_by_session(session_id: Optional[str]) -> None:
    """Fa risalire in cronologia la conversazione legata a questa sessione."""
    if not session_id:
        return
    try:
        (get_admin_client().table(TABLE)
         .update({"updated_at": _now_iso()})
         .eq("kbot_session_id", session_id)
         .is_("deleted_at", "null")
         .execute())
    except Exception as exc:
        if is_missing_table_error(exc):
            return  # migration non applicata: la cronologia è già disattivata a monte
        log.warning("indice conversazioni: touch fallito (fail-open)", exc_info=True)


def derive_title(session: dict) -> str:
    """Titolo dal primo messaggio utente, come fa il frontend. '' se non deducibile."""
    for m in (session.get("messages") or []):
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        text = re.sub(r"\s+", " ", str(m.get("content") or "")).strip()
        if text:
            return text[:_TITLE_MAX]
    collected = session.get("collected_data") or {}
    label = str(collected.get("deliverable_label") or "").strip()
    return label[:_TITLE_MAX]


def backfill_orphan_sessions(user_id: str) -> int:
    """Crea le righe di cronologia mancanti per le sessioni dell'utente.

    Gira a ogni apertura della cronologia, quindi il caso NORMALE — nessun orfano — deve
    costare quasi nulla: prima si confrontano i soli `id` (due select magrissime), e solo
    per gli id davvero mancanti si leggono le righe intere. La prima versione passava qui
    l'output di `list_user_sessions`, che fa `select("*")`: trascinava il JSONB completo di
    `messages` e `collected_data` di 100 sessioni — testo estratto dei PDF compreso — a
    ogni apertura della sidebar, anche quando non c'era niente da recuperare.

    `created_at` viene copiato dalla sessione, così la conversazione recuperata si colloca
    al punto giusto della cronologia invece di apparire come nuovissima.
    """
    if not user_id:
        return 0
    client = get_admin_client()
    try:
        # 1. Solo gli id delle sessioni dell'utente (niente messages, niente collected_data).
        owned = (client.table("kbot_sessions")
                 .select("id")
                 .eq("user_id", user_id)
                 .order("created_at", desc=True)
                 .limit(_SESSION_SCAN_LIMIT)
                 .execute())
        # 2. Le sessioni già in cronologia. Si guardano ANCHE le conversazioni cancellate
        #    (soft-delete): una chat eliminata dall'utente non deve riapparire al reload.
        existing = (client.table(TABLE)
                    .select("kbot_session_id")
                    .eq("user_id", user_id)
                    .execute())
    except Exception as exc:
        if not is_missing_table_error(exc):
            log.warning("indice conversazioni: sonda per backfill fallita", exc_info=True)
        return 0

    linked = {r.get("kbot_session_id") for r in (existing.data or []) if r.get("kbot_session_id")}
    missing = [r["id"] for r in (owned.data or [])
               if r.get("id") and r["id"] not in linked][:_BACKFILL_LIMIT]
    if not missing:
        return 0  # caso normale: costo = due select di soli id

    try:
        # 3. Solo ora le righe intere, e solo quelle che servono davvero.
        full = (client.table("kbot_sessions")
                .select("id,created_at,updated_at,messages,collected_data")
                .in_("id", missing)
                .execute())
    except Exception:
        log.warning("indice conversazioni: lettura sessioni orfane fallita", exc_info=True)
        return 0

    created = 0
    for s in (full.data or []):
        if len(s.get("messages") or []) < _MIN_MESSAGES:
            continue  # sessione aperta e abbandonata: non merita una riga in cronologia
        collected = s.get("collected_data") or {}
        row = {
            "user_id": user_id,
            "title": derive_title(s) or "Conversazione recuperata",
            "mode": "lead" if str(collected.get("mode") or "").lower() == "lead" else "report",
            "kbot_session_id": s["id"],
            "created_at": s.get("created_at") or _now_iso(),
            "updated_at": s.get("updated_at") or s.get("created_at") or _now_iso(),
        }
        try:
            # Una riga per volta: con l'indice unico della migration 009 due richieste
            # concorrenti si scontrano su una singola riga invece di far abortire l'intero
            # batch, e il duplicato viene semplicemente ignorato.
            client.table(TABLE).insert(row).execute()
            created += 1
        except Exception as exc:
            if _is_duplicate_error(exc):
                continue
            log.warning("indice conversazioni: insert orfana fallito (fail-open)",
                        exc_info=True)
    if created:
        log.info("indice conversazioni: recuperate %d sessioni orfane (user=%s)",
                 created, user_id)
    return created
