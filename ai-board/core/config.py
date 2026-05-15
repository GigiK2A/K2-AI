from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM — Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, description="Chiave API Anthropic")
    default_anthropic_model: str = Field(default="claude-sonnet-4-6")

    # LLM — OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="Chiave API OpenAI")
    default_openai_model: str = Field(default="gpt-4o")
    default_openai_mini_model: str = Field(default="gpt-4o-mini")
    tavily_api_key: Optional[str] = Field(default=None)

    # Supabase (opzionale in modalità Notion-only)
    supabase_url: Optional[str] = Field(default=None, description="URL progetto Supabase")
    supabase_key: Optional[str] = Field(default=None, description="Chiave anon Supabase")
    supabase_service_key: Optional[str] = Field(default=None, description="Chiave service role Supabase")

    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, description="Token bot Telegram")
    telegram_chat_id: Optional[str] = Field(default=None, description="Chat ID del fondatore")
    telegram_mode: str = Field(default="polling")
    telegram_webhook_url: Optional[str] = Field(default=None)
    telegram_webhook_secret: Optional[str] = Field(
        default=None,
        description="Token segreto passato a setWebhook e validato nell'header X-Telegram-Bot-Api-Secret-Token. Obbligatorio quando telegram_mode='webhook'.",
    )

    # App
    app_env: str = Field(default="development")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="DEBUG")
    app_allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
        description="Origini abilitate per le richieste dal sito pubblico, separate da virgole. NON includere IP LAN in default; estendere via env in deploy.",
    )
    board_auth_enabled: bool = Field(default=False)
    board_username: str = Field(default="admin")
    board_password: Optional[str] = Field(default=None)
    board_auth_realm: str = Field(default="AI Board")
    board_session_hours: int = Field(default=12)
    reports_site_url: str = Field(default="http://127.0.0.1:4173")
    board_data_backend: str = Field(default="notion")
    notion_token: Optional[str] = Field(default=None)
    notion_page_id: Optional[str] = Field(default=None)
    notion_version: str = Field(default="2022-06-28")

    # Email — Resend (primario) o SMTP (fallback)
    resend_api_key: Optional[str] = Field(default=None, description="Chiave API Resend")
    email_from: str = Field(default="K2-AI <noreply@k2-ai.it>", description="Mittente email (nome + indirizzo)")
    email_reply_to: Optional[str] = Field(default=None, description="Reply-to per le conferme (es. info@k2-ai.it)")
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_tls: bool = Field(default=True)

    # PostHog (Cloud EU) — read-only ingestion via Personal API key.
    # Empty → ingest job is a no-op.
    posthog_personal_api_key: Optional[str] = Field(default=None)
    posthog_project_id: Optional[str] = Field(default=None)
    posthog_host: str = Field(default="https://eu.i.posthog.com")
    scheduler_posthog_sync_cron: str = Field(default="0 * * * *")  # every hour

    # Scheduler
    scheduler_weekly_plan_cron: str = Field(default="0 8 * * 1")
    scheduler_daily_brief_cron: str = Field(default="0 8 * * *")
    scheduler_task_reminder_cron: str = Field(default="0 8 * * *")
    scheduler_kpi_update_cron: str = Field(default="0 18 * * *")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env.notion", ".env.notion"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def get_allowed_origins() -> list[str]:
    return [origin.strip() for origin in settings.app_allowed_origins.split(",") if origin.strip()]


def supabase_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_key and settings.supabase_service_key)
