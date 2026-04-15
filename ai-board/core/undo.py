"""
Sistema di undo minimo per azioni Notion.

Permette di annullare l'ultima azione eseguita per le operazioni più comuni:
- Creazione entità (task, lead, cliente) → undo = archivia la pagina Notion
- Aggiornamento campi → undo = ripristina valori precedenti

Stack per sessione (chat_id). Persiste in-memory durante il processo.
Non sopravvive ai restart — è una protezione tattica, non un backup.

Operazioni supportate:
- create_task      → undo: archivia pagina
- create_lead      → undo: archivia pagina
- create_client    → undo: archivia pagina
- update_task      → undo: ripristina status/notes precedenti
- update_lead      → undo: ripristina status/next_action/notes precedenti

Uso via Telegram:
- /undo → annulla ultima azione
- "annulla ultima" → stessa cosa
"""
from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any

from loguru import logger

# Max undo records per sessione
_MAX_UNDO_DEPTH = 5

# Stack per sessione: dict[session_id, deque[UndoRecord]]
_UNDO_STACKS: dict[str, deque[dict[str, Any]]] = {}

# TTL undo records in secondi (30 minuti)
UNDO_TTL_SECONDS = 1800


def push_undo(
    session_id: str | int,
    action_type: str,        # "create" | "update"
    entity_type: str,        # "task" | "lead" | "client" | "memory"
    entity_id: str,          # Notion page_id
    entity_name: str,        # Nome leggibile
    pre_state: dict[str, Any] | None = None,  # Stato prima della modifica (None per create)
    action_description: str = "",
) -> None:
    """
    Aggiunge un record undo allo stack della sessione.
    Chiamare PRIMA di eseguire l'operazione write (con pre_state catturato).
    """
    key = str(session_id)
    if key not in _UNDO_STACKS:
        _UNDO_STACKS[key] = deque(maxlen=_MAX_UNDO_DEPTH)

    record = {
        "action_type": action_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "pre_state": pre_state,
        "action_description": action_description,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _UNDO_STACKS[key].append(record)
    logger.debug(
        f"[undo] Push: {action_type} {entity_type} '{entity_name}' "
        f"(session: {key}, stack size: {len(_UNDO_STACKS[key])})"
    )
    # Persistenza opzionale Supabase
    _persist_undo_to_supabase(key, record)


def pop_undo(session_id: str | int) -> dict[str, Any] | None:
    """
    Rimuove e ritorna il record più recente dallo stack.
    Ritorna None se stack vuoto o record scaduto.
    """
    key = str(session_id)
    stack = _UNDO_STACKS.get(key)
    if not stack:
        return None

    record = stack.pop()
    created = datetime.fromisoformat(record["created_at"])
    age = (datetime.now(UTC) - created).total_seconds()
    if age > UNDO_TTL_SECONDS:
        logger.warning(f"[undo] Record scaduto per session {key} (età: {age:.0f}s)")
        return None

    return record


def peek_undo(session_id: str | int) -> dict[str, Any] | None:
    """Ritorna il record più recente senza rimuoverlo (per preview)."""
    key = str(session_id)
    stack = _UNDO_STACKS.get(key)
    if not stack:
        return None
    record = stack[-1]
    created = datetime.fromisoformat(record["created_at"])
    age = (datetime.now(UTC) - created).total_seconds()
    if age > UNDO_TTL_SECONDS:
        return None
    return record


def has_undo(session_id: str | int) -> bool:
    """True se esiste almeno un'azione annullabile."""
    return peek_undo(session_id) is not None


def execute_undo(record: dict[str, Any]) -> str:
    """
    Esegue il rollback di un'azione registrata.

    Per 'create': archivia la pagina Notion (soft delete reversibile).
    Per 'update': ripristina i campi allo stato precedente.

    Ritorna messaggio human-readable del risultato.
    """
    from core import notion_board

    if not notion_board.notion_enabled():
        return "Undo non disponibile: Notion non abilitato."

    action_type = record.get("action_type")
    entity_type = record.get("entity_type")
    entity_id = record.get("entity_id")
    entity_name = record.get("entity_name", "?")

    if not entity_id:
        return "Undo non eseguibile: ID entità mancante nel record."

    try:
        if action_type == "create":
            return _undo_create(entity_id, entity_type, entity_name)
        elif action_type == "update":
            return _undo_update(entity_id, entity_type, entity_name, record.get("pre_state") or {})
        else:
            return f"Tipo azione '{action_type}' non supportato per undo."
    except Exception as exc:
        logger.error(f"[undo] Errore esecuzione undo per {entity_type} '{entity_name}': {exc}")
        return f"Errore durante l'undo di '{entity_name}': {exc}"


def _undo_create(entity_id: str, entity_type: str, entity_name: str) -> str:
    """Archivia una pagina Notion (undo creazione)."""
    from core import notion_board
    notion_board.archive_page(entity_id)
    logger.info(f"[undo] Archiviata pagina Notion: {entity_type} '{entity_name}' ({entity_id})")
    return f"Annullato: {entity_type} '{entity_name}' archiviato in Notion."


def _undo_update(entity_id: str, entity_type: str, entity_name: str, pre_state: dict) -> str:
    """Ripristina campi allo stato precedente (undo aggiornamento)."""
    from core import notion_board

    if not pre_state:
        return f"Undo non disponibile: nessuno stato precedente salvato per '{entity_name}'."

    # Ripristina proprietà via PATCH diretto
    props: dict = {}

    if entity_type == "task":
        if "status" in pre_state:
            notion_status = notion_board.TASK_STATUS_TO_NOTION.get(pre_state["status"], pre_state["status"])
            props["Stato"] = notion_board._select(notion_status)
        if "notes" in pre_state:
            props["Output"] = notion_board._rich_text(pre_state["notes"])

    elif entity_type == "lead":
        if "status" in pre_state:
            notion_status = notion_board.PIPELINE_STATUS_TO_NOTION.get(pre_state["status"], pre_state["status"])
            props["Stato"] = notion_board._select(notion_status)
        if "next_action" in pre_state:
            props["Prossima azione"] = notion_board._rich_text(pre_state["next_action"])
        if "notes" in pre_state:
            props["Note"] = notion_board._rich_text(pre_state["notes"])

    if not props:
        return f"Undo parziale: nessun campo da ripristinare nel record per '{entity_name}'."

    notion_board._request("PATCH", f"/pages/{entity_id}", json={"properties": props})
    logger.info(f"[undo] Ripristinato stato precedente: {entity_type} '{entity_name}' ({entity_id})")
    fields_restored = ", ".join(pre_state.keys())
    return f"Ripristinato: {entity_type} '{entity_name}' riportato allo stato precedente ({fields_restored})."


# ─── Persistenza Supabase (fallback opzionale) ──────────────────────────────
# La tabella `undo_stack` su Supabase è opzionale.
# Se non esiste, l'undo funziona solo in-memory (si azzera al restart).
# Se esiste, sopravvive ai restart del processo.

def _persist_undo_to_supabase(session_id: str, record: dict[str, Any]) -> None:
    """Salva record undo su Supabase per persistenza cross-restart."""
    try:
        from db.client import get_service_client
        import json
        client = get_service_client()
        client.table("undo_stack").upsert({
            "session_id": str(session_id),
            "action_type": record["action_type"],
            "entity_type": record["entity_type"],
            "entity_id": record["entity_id"],
            "entity_name": record["entity_name"],
            "pre_state": json.dumps(record.get("pre_state") or {}, ensure_ascii=False),
            "action_description": record.get("action_description", ""),
            "created_at": record["created_at"],
        }).execute()
    except Exception as exc:
        logger.debug(f"[undo] Persistenza Supabase non disponibile (non critico): {exc}")


def _load_undo_from_supabase(session_id: str) -> list[dict[str, Any]]:
    """Carica undo stack da Supabase per questo session_id (dopo restart)."""
    try:
        import json
        from db.client import get_service_client
        client = get_service_client()
        resp = (
            client.table("undo_stack")
            .select("*")
            .eq("session_id", str(session_id))
            .order("created_at", desc=False)
            .limit(_MAX_UNDO_DEPTH)
            .execute()
        )
        records = []
        for row in (resp.data or []):
            pre_state = row.get("pre_state")
            if isinstance(pre_state, str):
                try:
                    pre_state = json.loads(pre_state)
                except Exception:
                    pre_state = {}
            records.append({
                "action_type": row.get("action_type", ""),
                "entity_type": row.get("entity_type", ""),
                "entity_id": row.get("entity_id", ""),
                "entity_name": row.get("entity_name", ""),
                "pre_state": pre_state,
                "action_description": row.get("action_description", ""),
                "created_at": row.get("created_at", ""),
            })
        return records
    except Exception as exc:
        logger.debug(f"[undo] Load da Supabase non disponibile: {exc}")
        return []


def _delete_undo_from_supabase(session_id: str, entity_id: str) -> None:
    """Rimuove record undo da Supabase dopo esecuzione."""
    try:
        from db.client import get_service_client
        client = get_service_client()
        client.table("undo_stack").delete().eq("session_id", str(session_id)).eq("entity_id", entity_id).execute()
    except Exception as exc:
        logger.debug(f"[undo] Delete Supabase non disponibile: {exc}")


def load_session_from_supabase(session_id: str) -> None:
    """
    Carica lo stack undo da Supabase per questa sessione (se non già in memoria).
    Da chiamare all'avvio della sessione Telegram per recuperare undo post-restart.
    """
    key = str(session_id)
    if key in _UNDO_STACKS and _UNDO_STACKS[key]:
        return  # Già in memoria, non sovrascrivere

    records = _load_undo_from_supabase(session_id)
    if records:
        _UNDO_STACKS[key] = deque(records, maxlen=_MAX_UNDO_DEPTH)
        logger.debug(f"[undo] Recuperati {len(records)} record da Supabase per session {key}")


def describe_undo(record: dict[str, Any]) -> str:
    """Descrizione human-readable di cosa verrebbe annullato."""
    action_type = record.get("action_type", "?")
    entity_type = record.get("entity_type", "?")
    entity_name = record.get("entity_name", "?")
    action_desc = record.get("action_description", "")

    if action_type == "create":
        return f"Creazione {entity_type} '{entity_name}'"
    elif action_type == "update":
        pre = record.get("pre_state", {})
        if pre:
            fields = ", ".join(pre.keys())
            return f"Modifica {entity_type} '{entity_name}' (campi: {fields})"
        return f"Modifica {entity_type} '{entity_name}'"
    return action_desc or f"{action_type} su {entity_type} '{entity_name}'"
