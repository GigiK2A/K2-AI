"""Application settings — loaded from environment via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")

    # Auth — single-user (Luigi) for now.
    board_username: str = Field(default="luigi", alias="BOARD_USERNAME")
    board_password_hash: str = Field(default="", alias="BOARD_PASSWORD_HASH")
    board_session_secret: str = Field(
        default="dev-only-not-secure-change-me-in-production-please-32b",
        alias="BOARD_SESSION_SECRET",
    )
    board_session_cookie_name: str = Field(default="k2board_session")
    board_session_max_age_seconds: int = Field(default=60 * 60 * 24 * 30)  # 30 days

    # CORS — comma-separated origin list in env.
    board_cors_origins: str = Field(
        default="https://board.k2-ai.it,http://localhost:3000,http://localhost:3001",
        alias="BOARD_CORS_ORIGINS",
    )

    # Optional integrations
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Stripe — webhook signature verification (Sprint 7).
    stripe_webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")

    # Screenshot service — Playwright headless Chromium endpoint.
    # If empty, /screenshot returns 503. Set to enable.
    screenshot_api_key: str = Field(default="", alias="SCREENSHOT_API_KEY")

    # Google Calendar — stubs for future sync (Sprint 9+).
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_refresh_token: str = Field(default="", alias="GOOGLE_REFRESH_TOKEN")

    # Sprint 9B/9C/9D — email delivery, daily brief, email triage.
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    board_owner_email: str = Field(
        default="rluigiluca@gmail.com", alias="BOARD_OWNER_EMAIL"
    )
    board_email_from: str = Field(
        default="noreply@k2-ai.it", alias="BOARD_EMAIL_FROM"
    )
    daily_brief_enabled: bool = Field(default=True, alias="DAILY_BRIEF_ENABLED")
    daily_brief_cron: str = Field(default="0 7 * * *", alias="DAILY_BRIEF_CRON")
    daily_brief_tz: str = Field(default="Europe/Rome", alias="DAILY_BRIEF_TZ")
    email_triage_enabled: bool = Field(default=False, alias="EMAIL_TRIAGE_ENABLED")
    email_triage_cron: str = Field(
        default="0 */2 * * *", alias="EMAIL_TRIAGE_CRON"
    )

    # Observability
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # "json" | "plain"
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server
    port: int = Field(default=8000, alias="PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.board_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
