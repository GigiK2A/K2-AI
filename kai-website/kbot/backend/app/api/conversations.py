"""CRUD su kbot_conversations — history sidebar persistente per utenti loggati.

Anon non ha persistenza: il frontend mantiene la lista in memoria/local
state. Tutte le rotte richiedono JWT Supabase valido.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import conversations_index, sessions
from ..lib.auth import AuthUser, require_user
from ..lib.supabase_admin import get_admin_client

router = APIRouter()
log = logging.getLogger(__name__)

TABLE = "kbot_conversations"


def _is_missing_table_error(exc: Exception) -> bool:
    """Detect Postgrest PGRST205 (schema cache miss) — tabella non esistente."""
    msg = str(exc).lower()
    return "pgrst205" in msg or "schema cache" in msg or "could not find the table" in msg


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CreateConversationBody(BaseModel):
    title: Optional[str] = None
    mode: Optional[str] = "report"
    kbot_session_id: Optional[str] = Field(default=None, alias="kbotSessionId")

    class Config:
        populate_by_name = True


class UpdateConversationBody(BaseModel):
    title: Optional[str] = None
    kbot_session_id: Optional[str] = Field(default=None, alias="kbotSessionId")

    class Config:
        populate_by_name = True


def _public(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "title": row.get("title") or "Nuova conversazione",
        "mode": row.get("mode") or "report",
        "kbotSessionId": row.get("kbot_session_id"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
    }


def _check_owner(row: dict, user: AuthUser) -> None:
    if not row or row.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="not found")


@router.get("/conversations")
def list_conversations(user: AuthUser = Depends(require_user)) -> dict:
    client = get_admin_client()
    # Recupero delle sessioni orfane PRIMA di leggere: una chat esistente in kbot_sessions
    # ma senza riga qui era invisibile in cronologia (visibile solo in dashboard, che legge
    # /sessions). Best-effort: se fallisce, si prosegue con la lista che c'è.
    try:
        conversations_index.backfill_orphan_sessions(
            user.id, sessions.list_user_sessions(user.id, limit=100))
    except Exception:
        log.warning("recupero sessioni orfane fallito (fail-open)", exc_info=True)
    try:
        res = (
            client.table(TABLE)
            .select("*")
            .eq("user_id", user.id)
            .is_("deleted_at", "null")
            # Ordinamento per ULTIMA ATTIVITÀ, non per creazione: una conversazione ripresa
            # oggi deve stare in cima. `updated_at` viene toccato a ogni turno di chat
            # (lib/conversations_index.touch_by_session).
            .order("updated_at", desc=True)
            .limit(100)
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            log.warning("kbot_conversations table missing — returning empty list (run migration 007)")
            return {"conversations": []}
        raise
    return {"conversations": [_public(r) for r in (res.data or [])]}


@router.post("/conversations")
def create_conversation(
    body: CreateConversationBody,
    user: AuthUser = Depends(require_user),
) -> dict:
    row = {
        "user_id": user.id,
        "title": (body.title or "Nuova conversazione")[:120],
        "mode": "lead" if (body.mode or "").lower() == "lead" else "report",
    }
    if body.kbot_session_id:
        row["kbot_session_id"] = body.kbot_session_id
    client = get_admin_client()
    res = client.table(TABLE).insert(row).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="insert failed")
    return {"conversation": _public(res.data[0])}


@router.patch("/conversations/{conv_id}")
def update_conversation(
    conv_id: str,
    body: UpdateConversationBody,
    user: AuthUser = Depends(require_user),
) -> dict:
    client = get_admin_client()
    existing = (
        client.table(TABLE).select("*").eq("id", conv_id).limit(1).execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="not found")
    _check_owner(existing.data[0], user)

    patch: dict = {"updated_at": _now_iso()}
    if body.title is not None:
        patch["title"] = body.title.strip()[:120] or "Nuova conversazione"
    if body.kbot_session_id is not None:
        patch["kbot_session_id"] = body.kbot_session_id
    res = client.table(TABLE).update(patch).eq("id", conv_id).execute()
    return {"conversation": _public(res.data[0])}


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str, user: AuthUser = Depends(require_user)
) -> dict:
    client = get_admin_client()
    existing = (
        client.table(TABLE).select("*").eq("id", conv_id).limit(1).execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="not found")
    _check_owner(existing.data[0], user)
    # Soft delete.
    client.table(TABLE).update(
        {"deleted_at": _now_iso(), "updated_at": _now_iso()}
    ).eq("id", conv_id).execute()
    return {"ok": True}
