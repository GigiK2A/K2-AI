"""
Sistema di livelli di rischio per le azioni Notion.

Tre livelli:
- READ           (L1): lettura libera, nessun gate
- WRITE_SIMPLE   (L2): scrittura a basso rischio, esecuzione con validazione standard
- WRITE_SENSITIVE (L3): scrittura sensibile, richiede conferma esplicita prima dell'esecuzione

Flusso L3:
1. Tool chiamata con parametri sensibili
2. action_guard intercetta → salva params in _PENDING_CONFIRMATIONS → ritorna summary "Confermi?"
3. Telegram handler intercetta "conferma" → esegue azione salvata
4. Telegram handler intercetta "annulla" → scarta azione, notifica
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from loguru import logger


class ActionRisk(Enum):
    READ = 1
    WRITE_SIMPLE = 2
    WRITE_SENSITIVE = 3


# ─── Mappa funzione → livello di rischio ────────────────────────────────────
ACTION_RISK_MAP: dict[str, ActionRisk] = {
    # L1 — Lettura
    "list_open_tasks": ActionRisk.READ,
    "list_pipeline_status": ActionRisk.READ,
    "list_clients": ActionRisk.READ,
    "search_client": ActionRisk.READ,
    # L2 — Scrittura semplice
    "add_lead_to_pipeline": ActionRisk.WRITE_SIMPLE,
    "create_board_task": ActionRisk.WRITE_SIMPLE,
    "save_to_memory": ActionRisk.WRITE_SIMPLE,
    "create_or_update_client": ActionRisk.WRITE_SIMPLE,
    "update_board_task": ActionRisk.WRITE_SIMPLE,
    "update_pipeline_lead": ActionRisk.WRITE_SIMPLE,
    # L3 — Scrittura sensibile (richiede conferma)
    # Attivare quando si aggiungono operazioni distruttive:
    # "delete_task": ActionRisk.WRITE_SENSITIVE,
    # "archive_client": ActionRisk.WRITE_SENSITIVE,
    # "delete_pipeline_lead": ActionRisk.WRITE_SENSITIVE,
}

# ─── Criteri che promuovono L2 a L3 a runtime ───────────────────────────────
# Tuple: (nome_funzione, nome_param, valori_sensibili)
SENSITIVE_PARAM_OVERRIDES: list[tuple[str, str, set[str]]] = [
    # Spostare pipeline a stato finale = decisione irreversibile
    ("update_pipeline_lead", "status", {"won", "lost"}),
    # Chiudere un task = irreversibile operativamente
    ("update_board_task", "status", {"done", "rejected"}),
]


def get_action_risk(func_name: str, kwargs: dict[str, Any] | None = None) -> ActionRisk:
    """
    Ritorna il livello di rischio per una funzione.
    Se i parametri passati corrispondono a override sensibili, ritorna WRITE_SENSITIVE.
    """
    base = ACTION_RISK_MAP.get(func_name, ActionRisk.WRITE_SIMPLE)
    if base == ActionRisk.WRITE_SENSITIVE:
        return base
    if kwargs:
        for fn_name, param, sensitive_vals in SENSITIVE_PARAM_OVERRIDES:
            if fn_name == func_name:
                val = str(kwargs.get(param, "")).lower()
                if val in sensitive_vals:
                    return ActionRisk.WRITE_SENSITIVE
    return base


# ─── Store conferme pendenti per chat ────────────────────────────────────────
# Key: chat_id (str), Value: dict con func_name, kwargs, summary, created_at
_PENDING_CONFIRMATIONS: dict[str, dict[str, Any]] = {}

# TTL conferme pendenti in secondi (10 minuti)
CONFIRMATION_TTL_SECONDS = 600


def store_pending_confirmation(
    chat_id: str | int,
    func_name: str,
    kwargs: dict[str, Any],
    summary: str,
) -> None:
    """Salva un'azione sensibile in attesa di conferma."""
    key = str(chat_id)
    record = {
        "func_name": func_name,
        "kwargs": kwargs,
        "summary": summary,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _PENDING_CONFIRMATIONS[key] = record
    logger.info(f"[action_guard] Azione L3 in attesa di conferma per chat {key}: {func_name}")
    # Persistenza opzionale Supabase
    _persist_confirmation_to_supabase(key, record)


def pop_pending_confirmation(chat_id: str | int) -> dict[str, Any] | None:
    """Rimuove e ritorna l'azione pendente per questo chat_id."""
    key = str(chat_id)
    record = _PENDING_CONFIRMATIONS.pop(key, None)

    # Fallback Supabase se non in memoria (es. dopo restart)
    if record is None:
        record = _load_confirmation_from_supabase(key)

    if record is None:
        return None

    # Controlla TTL
    try:
        created = datetime.fromisoformat(record["created_at"])
        age = (datetime.now(UTC) - created).total_seconds()
        if age > CONFIRMATION_TTL_SECONDS:
            logger.warning(f"[action_guard] Conferma scaduta per chat {key} (età: {age:.0f}s)")
            _delete_confirmation_from_supabase(key)
            return None
    except Exception:
        pass  # Created_at malformato — procedi comunque

    _delete_confirmation_from_supabase(key)
    return record


def has_pending_confirmation(chat_id: str | int) -> bool:
    """True se esiste un'azione pendente non scaduta per questo chat_id."""
    key = str(chat_id)
    record = _PENDING_CONFIRMATIONS.get(key)
    if not record:
        return False
    created = datetime.fromisoformat(record["created_at"])
    age = (datetime.now(UTC) - created).total_seconds()
    if age > CONFIRMATION_TTL_SECONDS:
        _PENDING_CONFIRMATIONS.pop(key, None)
        return False
    return True


def cancel_pending_confirmation(chat_id: str | int) -> bool:
    """Annulla azione pendente. Ritorna True se c'era qualcosa da annullare."""
    key = str(chat_id)
    existed = key in _PENDING_CONFIRMATIONS
    _PENDING_CONFIRMATIONS.pop(key, None)
    if existed:
        logger.info(f"[action_guard] Azione pendente annullata per chat {key}")
    return existed


# ─── Persistenza Supabase per pending confirmations ─────────────────────────
# Tabella `pending_confirmations` opzionale su Supabase.
# Se non esiste, le conferme pendenti si perdono al restart (accettabile).

def _persist_confirmation_to_supabase(chat_id: str, record: dict[str, Any]) -> None:
    try:
        import json
        from db.client import get_service_client
        client = get_service_client()
        client.table("pending_confirmations").upsert({
            "chat_id": chat_id,
            "func_name": record["func_name"],
            "kwargs": json.dumps(record["kwargs"], ensure_ascii=False, default=str),
            "summary": record.get("summary", ""),
            "created_at": record["created_at"],
        }).execute()
    except Exception as exc:
        logger.debug(f"[action_guard] Persistenza Supabase non disponibile: {exc}")


def _load_confirmation_from_supabase(chat_id: str) -> dict[str, Any] | None:
    try:
        import json
        from db.client import get_service_client
        client = get_service_client()
        resp = (
            client.table("pending_confirmations")
            .select("*")
            .eq("chat_id", chat_id)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            return None
        row = rows[0]
        kwargs = row.get("kwargs", "{}")
        if isinstance(kwargs, str):
            try:
                kwargs = json.loads(kwargs)
            except Exception:
                kwargs = {}
        return {
            "func_name": row.get("func_name", ""),
            "kwargs": kwargs,
            "summary": row.get("summary", ""),
            "created_at": row.get("created_at", datetime.now(UTC).isoformat()),
        }
    except Exception as exc:
        logger.debug(f"[action_guard] Load Supabase non disponibile: {exc}")
        return None


def _delete_confirmation_from_supabase(chat_id: str) -> None:
    try:
        from db.client import get_service_client
        client = get_service_client()
        client.table("pending_confirmations").delete().eq("chat_id", chat_id).execute()
    except Exception as exc:
        logger.debug(f"[action_guard] Delete Supabase non disponibile: {exc}")


def build_confirmation_prompt(func_name: str, kwargs: dict[str, Any]) -> str:
    """
    Costruisce un messaggio di conferma human-readable per operazioni L3.
    """
    descriptions: dict[str, Callable[[dict], str]] = {
        "update_pipeline_lead": lambda kw: (
            f"Stai per segnare il lead '{kw.get('name_or_id', '?')}' come "
            f"**{kw.get('status', '?')}**. Questa azione cambia lo stato finale del lead."
        ),
        "update_board_task": lambda kw: (
            f"Stai per portare il task al stato **{kw.get('status', '?')}**. "
            f"Questa azione chiude o blocca il task."
        ),
    }
    fn = descriptions.get(func_name)
    if fn:
        desc = fn(kwargs)
    else:
        desc = f"Stai per eseguire '{func_name}' con parametri sensibili."

    return (
        f"⚠️ **Azione sensibile — conferma richiesta**\n\n"
        f"{desc}\n\n"
        f"Rispondi **conferma** per procedere, oppure **annulla** per scartare."
    )
