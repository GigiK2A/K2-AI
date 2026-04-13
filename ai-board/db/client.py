from functools import lru_cache

from loguru import logger
from supabase import Client, create_client

from core.config import settings, supabase_configured


@lru_cache()
def get_client() -> Client:
    if not supabase_configured():
        raise RuntimeError("Supabase non configurato. In modalità Notion-only, evita i percorsi legacy che lo richiedono.")
    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client connesso")
        return client
    except Exception as exc:
        logger.error(f"Errore connessione Supabase: {exc}")
        raise


@lru_cache()
def get_service_client() -> Client:
    if not supabase_configured():
        raise RuntimeError("Supabase non configurato. In modalità Notion-only, evita i percorsi legacy che lo richiedono.")
    try:
        client = create_client(settings.supabase_url, settings.supabase_service_key)
        logger.info("Supabase service client connesso")
        return client
    except Exception as exc:
        logger.error(f"Errore connessione Supabase service: {exc}")
        raise
