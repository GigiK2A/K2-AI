"""Lazy-init Supabase service-role client.

Service-role bypasses RLS by design — this client must NEVER be exposed to the
browser. Frontend talks to FastAPI; FastAPI talks to Supabase with this key.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.settings import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY."
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_supabase_or_none() -> Optional[Client]:
    """Variant that returns None instead of raising — useful for /health."""
    try:
        return get_supabase()
    except RuntimeError:
        return None
