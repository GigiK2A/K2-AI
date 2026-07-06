"""Supabase Storage helpers."""
from __future__ import annotations

import logging
from typing import Optional

from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)


def upload_bytes(*, bucket: str, path: str, content: bytes,
                 content_type: str = "application/octet-stream") -> str:
    """Upload arbitrary bytes; ensure bucket exists; return public URL.

    C3: `upsert=true` sovrascrive se il path collide. La collisione cross-cliente
    è mitigata a monte rendendo il path univoco per sessione + suffisso casuale
    (vedi generate_pdf._make_friendly_filename). FOLLOW-UP infra (NON codice):
    rendere questo bucket PRIVATO e servire i report via signed URL a tempo, così
    un path pubblico indovinato non basta più a scaricare un report altrui.
    """
    client = get_admin_client()
    storage = client.storage

    # Ensure bucket exists (idempotent).
    try:
        buckets = storage.list_buckets()
        names = {b.name if hasattr(b, "name") else b.get("name") for b in buckets}
        if bucket not in names:
            storage.create_bucket(bucket, options={"public": True})
            log.info("Created Supabase bucket: %s", bucket)
    except Exception as exc:  # noqa: BLE001
        log.warning("Bucket bootstrap warning: %s", exc)

    storage.from_(bucket).upload(
        path,
        content,
        {"content-type": content_type, "upsert": "true"},
    )
    return storage.from_(bucket).get_public_url(path)


def upload_pdf(*, bucket: str, path: str, content: bytes) -> str:
    """Upload PDF bytes; ensure bucket exists; return public URL."""
    return upload_bytes(bucket=bucket, path=path, content=content,
                        content_type="application/pdf")


def download_bytes(*, bucket: str, path: str) -> Optional[bytes]:
    """Scarica i byte di un oggetto dallo Storage. Ritorna None se assente/errore.

    C4 — serve a rileggere la copia DUREVOLE del deliverable (PDF/JSON persistiti
    su Storage appena renderizzati) quando il job in-memory dell'8e è andato perso
    a un restart: il download continua a funzionare dalla copia durevole."""
    try:
        client = get_admin_client()
        return client.storage.from_(bucket).download(path)
    except Exception:
        log.warning("download_bytes fallito bucket=%s path=%s", bucket, path, exc_info=True)
        return None
