"""Environment-driven settings. Loaded once at import time."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# .env.local overrides shell env (developer file is source of truth).
# .env is a non-overriding default (lowest priority).
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / ".env.local", override=True)


def _env(name: str, *fallbacks: str, default: Optional[str] = None) -> Optional[str]:
    for key in (name, *fallbacks):
        value = os.environ.get(key)
        if value:  # empty strings treated as missing
            return value
    return default


ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = _env("ANTHROPIC_MODEL", "CLAUDE_MODEL", default="claude-haiku-4-5")
ANTHROPIC_PDF_MODEL = _env("ANTHROPIC_PDF_MODEL", default="claude-sonnet-4-5")
# Multi-call generation: spezza il JSON in 3 chiamate (exec_summary, body, conclusions)
# per evitare troncamento ultime sezioni con report lunghi. Default OFF — feature
# flag per safe rollout. Attivare con ANTHROPIC_PDF_MULTI_CALL=1.
ANTHROPIC_PDF_MULTI_CALL = (_env("ANTHROPIC_PDF_MULTI_CALL", default="0") or "0").lower() in ("1", "true", "yes")

SUPABASE_URL = _env("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = _env(
    "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_KEY"
)
SUPABASE_JWT_SECRET = _env("SUPABASE_JWT_SECRET")  # legacy HS256, optional fallback
SUPABASE_JWT_JWKS_URL = _env(
    "SUPABASE_JWT_JWKS_URL",
    default=(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else None),
)
SUPABASE_ANON_KEY = _env("NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_ANON_KEY")

STRIPE_SECRET_KEY = _env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = _env("STRIPE_WEBHOOK_SECRET")
STRIPE_API_VERSION = _env("STRIPE_API_VERSION", default="2024-12-18.acacia")
REPORT_PRICE_EUR_CENTS = int(_env("REPORT_PRICE_EUR_CENTS", default="1900") or "1900")

RESEND_API_KEY = _env("RESEND_API_KEY")
REPORT_FROM_EMAIL = _env("REPORT_FROM_EMAIL", default="K2-AI <noreply@k2-ai.it>")
KBOT_NOTIFY_EMAIL = _env("KBOT_NOTIFY_EMAIL")

FRONTEND_URL = _env("FRONTEND_URL", default="http://localhost:3000")
SITE_URL = _env("NEXT_PUBLIC_SITE_URL", "SITE_URL", default="https://www.k2-ai.it")
INTERNAL_API_KEY = _env("INTERNAL_API_KEY")

# Default to k2-ai.it production origins. Never default to "*" with credentials.
# Override via KBOT_CORS_ORIGINS env var (comma-separated) for dev/staging.
_DEFAULT_CORS = ",".join([
    "https://www.k2-ai.it",
    "https://k2-ai.it",
    "https://k-ai.it",
    "https://www.k-ai.it",
    FRONTEND_URL,  # dev only — usually http://localhost:3000
])
CORS_ORIGINS = [
    o.strip()
    for o in (_env("KBOT_CORS_ORIGINS", default=_DEFAULT_CORS) or _DEFAULT_CORS).split(",")
    if o.strip() and o.strip() != "*"  # explicit guard: never allow wildcard
]

# Skill loader looks here first (consolidated repo), then falls back to local copy.
SKILLS_DIR = Path(
    _env("KBOT_SKILLS_DIR", default=str(ROOT.parent.parent / "lib" / "skills"))
).resolve()

# Storage bucket names (Supabase Storage), shared with the site.
STORAGE_UPLOADS_BUCKET = _env("STORAGE_UPLOADS_BUCKET", default="kbot-uploads")
STORAGE_REPORTS_BUCKET = _env("STORAGE_REPORTS_BUCKET", default="kbot-reports")

# Catalog (fonte unica prezzi/servizi/percorsi). Interim: file committato in
# app/data/catalog.json. Target: generato da k2a-catalogo (vedi
# docs/interfaccia-kbot-8e.md §2). Override con KBOT_CATALOG_PATH.
CATALOG_PATH = Path(
    _env("KBOT_CATALOG_PATH", default=str(ROOT / "app" / "data" / "catalog.json"))
).resolve()

# Motore 8e (generazione deliverable). Vuoto in dev → si usa il MOCK locale
# (kbot/mock-8e). Vedi docs/interfaccia-kbot-8e.md.
ENGINE_8E_BASE_URL = _env("K2A_8E_BASE_URL", default="http://localhost:8800")
ENGINE_8E_API_KEY = _env("K2A_8E_API_KEY")  # Bearer backend-to-backend

# Prompt size limits, mirroring api/kbot/_shared.ts.
CHAT_SYSTEM_MAX_CHARS = int(_env("CHAT_SYSTEM_MAX_CHARS", default="26000") or "26000")
PDF_SYSTEM_MAX_CHARS = int(_env("PDF_SYSTEM_MAX_CHARS", default="55000") or "55000")
MAX_HISTORY_MESSAGES = int(_env("MAX_HISTORY_MESSAGES", default="12") or "12")
MAX_MESSAGE_CHARS = int(_env("MAX_MESSAGE_CHARS", default="900") or "900")

# PostHog Cloud EU (server-side). Empty → analytics disabled (no-op).
POSTHOG_API_KEY = _env("POSTHOG_API_KEY")
POSTHOG_HOST = _env("POSTHOG_HOST", default="https://eu.i.posthog.com")
