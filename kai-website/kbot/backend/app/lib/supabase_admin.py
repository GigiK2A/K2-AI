"""Supabase admin client (service-role). Singleton."""
from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from ..settings import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Missing Supabase env: NEXT_PUBLIC_SUPABASE_URL / SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY are required."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
