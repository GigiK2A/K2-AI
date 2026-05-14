"""Sessions data access layer.

Mirrors kai-website/lib/kbot/sessions.ts for the V2 flow.
Table: kbot_sessions (extended with user_id, see supabase migration).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .services import (
    DEFAULT_SERVICE_ID,
    VALID_SERVICE_IDS,
    normalize_service_id,
)
from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)

TABLE = "kbot_sessions"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_mode(value: Optional[str]) -> str:
    return "lead" if str(value or "").lower() == "lead" else "report"


def create_session(*, service_id: Optional[str], mode: Optional[str], user_id: Optional[str]) -> dict:
    sid = normalize_service_id(service_id) or DEFAULT_SERVICE_ID
    if sid not in VALID_SERVICE_IDS:
        sid = DEFAULT_SERVICE_ID
    resolved_mode = _coerce_mode(mode)

    row = {
        "step": 1,
        "status": "active",
        "path": "unknown",
        "messages": [],
        "collected_data": {
            "service_id": sid,
            "mode": resolved_mode,
            "extractedData": {},
        },
    }
    if user_id:
        row["user_id"] = user_id

    client = get_admin_client()
    res = client.table(TABLE).insert(row).execute()
    if not res.data:
        raise RuntimeError("failed to create session")
    return res.data[0]


def get_session(session_id: str) -> Optional[dict]:
    client = get_admin_client()
    res = client.table(TABLE).select("*").eq("id", session_id).limit(1).execute()
    if not res.data:
        return None
    return res.data[0]


def update_session(session_id: str, patch: Dict[str, Any]) -> dict:
    patch = {**patch, "updated_at": _now_iso()}
    client = get_admin_client()
    res = client.table(TABLE).update(patch).eq("id", session_id).execute()
    if not res.data:
        raise RuntimeError("session not found")
    return res.data[0]


def link_user_to_session(session_id: str, user_id: str) -> dict:
    return update_session(session_id, {"user_id": user_id})


def list_user_sessions(user_id: str, *, limit: int = 50) -> List[dict]:
    """Return the most recent sessions belonging to the given user."""
    client = get_admin_client()
    res = (
        client.table(TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def append_messages(session: dict, new_msgs: List[dict]) -> List[dict]:
    """Returns merged messages list. Deduplicates trivial repeats."""
    current = list(session.get("messages") or [])
    for m in new_msgs:
        role = m.get("role")
        content = str(m.get("content") or "")
        if role not in ("user", "assistant") or not content.strip():
            continue
        # Dedup: same role+content as previous tail.
        if current and current[-1].get("role") == role and current[-1].get("content") == content:
            continue
        entry = {"role": role, "content": content, "ts": m.get("ts") or _now_iso()}
        current.append(entry)
    return current


def merge_collected_data(session: dict, patch: Dict[str, Any]) -> Dict[str, Any]:
    base = dict(session.get("collected_data") or {})
    base.update({k: v for k, v in patch.items() if v is not None})
    return base


def public_session(session: dict) -> dict:
    """Strip internal fields before returning to client."""
    collected = session.get("collected_data") or {}
    return {
        "id": session.get("id"),
        "serviceId": collected.get("service_id"),
        "mode": collected.get("mode") or "report",
        "messages": session.get("messages") or [],
        "extractedData": collected.get("extractedData") or {},
        "summary": collected.get("summary"),
        "recommendedServiceId": collected.get("recommendedServiceId"),
        "recommendedServiceName": collected.get("recommendedServiceName"),
        "recommendedTier": collected.get("recommendedTier"),
        "status": session.get("status"),
        "pdfUrl": session.get("pdf_url"),
        "hasUser": bool(session.get("user_id")),
        "timestamps": {
            "createdAt": session.get("created_at"),
            "updatedAt": session.get("updated_at"),
        },
    }
