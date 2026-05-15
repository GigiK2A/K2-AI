"""Shared FastAPI dependencies (re-exports for ergonomics)."""
from __future__ import annotations

from app.auth import CurrentUser, get_current_user, require_auth  # noqa: F401
from app.db.client import get_supabase  # noqa: F401
from app.settings import get_settings  # noqa: F401
