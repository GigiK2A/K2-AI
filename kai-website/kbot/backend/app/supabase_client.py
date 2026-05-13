from __future__ import annotations

import os
from datetime import datetime, timezone

from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY mancante")
        _client = create_client(url, key)
    return _client


def get_conversation_memory_db(clerk_user_id: str, conversation_id: str, limit: int = 40) -> list[dict]:
    try:
        client = _get_client()
        result = (
            client.table("conversations")
            .select("role, content, context_files, ts")
            .eq("clerk_user_id", clerk_user_id)
            .eq("conversation_id", conversation_id)
            .order("ts", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def append_conversation_memory_db(
    clerk_user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    context_files: list[str],
) -> None:
    try:
        client = _get_client()
        client.table("conversations").insert({
            "clerk_user_id": clerk_user_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content[:12000],
            "context_files": context_files,
            "ts": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass
