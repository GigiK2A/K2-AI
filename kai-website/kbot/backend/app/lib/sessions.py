"""Sessions data access layer.

Mirrors kai-website/lib/kbot/sessions.ts for the V2 flow.
Table: kbot_sessions (extended with user_id, see supabase migration).
"""
from __future__ import annotations

import logging
import secrets
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


def _normalize_tag(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().upper()
    import re
    return v if re.fullmatch(r"P[0-9]{2}", v) else None


def create_session(
    *, service_id: Optional[str], mode: Optional[str], user_id: Optional[str],
    tag_pillar: Optional[str] = None,
) -> dict:
    # Service-id NOT defaulted: prevents biasing the LLM toward one specific
    # analysis type (was: P12 'AI Consulenza Strategica' → made K-BOT start
    # every cold conversation as a strategic/financial diagnosis even when
    # user wanted SEO/marketing/feasibility). User picks explicitly OR
    # K-BOT asks first what kind of report.
    sid = normalize_service_id(service_id)
    if sid is not None and sid not in VALID_SERVICE_IDS:
        sid = None
    resolved_mode = _coerce_mode(mode)

    collected_data: dict = {"mode": resolved_mode, "extractedData": {}}
    if sid:
        collected_data["service_id"] = sid

    # Scenario C: tag pillar SEO dal sito → contesto + boost suggerito (catalog).
    tag = _normalize_tag(tag_pillar)
    if tag:
        collected_data["tag_pillar"] = tag
        try:
            from . import catalog
            boost = catalog.boost_per_tag(tag)
            if boost:
                collected_data["boost_suggerito"] = boost["id"]
                collected_data["boost_suggerito_label"] = boost.get("label")
        except Exception:
            pass  # mai bloccare la creazione sessione per il catalogo

    row = {
        "step": 1,
        "status": "active",
        "path": "unknown",
        "messages": [],
        "collected_data": collected_data,
    }
    if user_id:
        row["user_id"] = user_id
    else:
        # Anonymous session: issue a single-use link token so only the browser
        # that originally created the session can later claim it (H-6).
        row["link_token"] = secrets.token_urlsafe(32)

    client = get_admin_client()
    res = client.table(TABLE).insert(row).execute()
    if not res.data:
        raise RuntimeError("failed to create session")
    return res.data[0]


def claim_session_with_token(
    session_id: str, user_id: str, link_token: str
) -> Optional[dict]:
    """Atomically claim an anonymous session, verifying the link token.

    Returns the updated row on success, None if the session doesn't exist,
    is already owned, or the token doesn't match.
    """
    row = get_session(session_id)
    if not row:
        return None
    if row.get("user_id"):
        # Already linked — caller must check ownership separately.
        return row if row.get("user_id") == user_id else None
    stored = row.get("link_token") or ""
    if not stored or not link_token:
        return None
    if not secrets.compare_digest(str(stored), str(link_token)):
        return None
    # Burn the token on use so it can't be replayed.
    return update_session(session_id, {"user_id": user_id, "link_token": None})


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
        "tagPillar": collected.get("tag_pillar"),
        "boostSuggerito": collected.get("boost_suggerito"),
        "boostSuggeritoLabel": collected.get("boost_suggerito_label"),
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
