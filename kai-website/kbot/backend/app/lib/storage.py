"""Supabase Storage helpers."""
from __future__ import annotations

import logging
from typing import Optional

from ..settings import SUPABASE_URL
from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)

# Report emailati: il link firmato resta valido 7 giorni. Il PDF e' comunque
# allegato alla mail, quindi anche a link scaduto l'utente ha il documento.
REPORT_URL_TTL = 7 * 24 * 3600


def _extract_signed_url(resp) -> str:
    """Estrae l'URL firmato dalla risposta di create_signed_url.

    supabase-py ha cambiato la forma della risposta tra versioni (dict con
    'signedURL' / 'signedUrl' / 'signed_url', oppure oggetto con attributo, e in
    alcune versioni un path relativo). Gestiamo tutti i casi e assolutizziamo.
    """
    url = None
    if isinstance(resp, dict):
        url = resp.get("signedURL") or resp.get("signedUrl") or resp.get("signed_url")
    else:
        url = getattr(resp, "signed_url", None) or getattr(resp, "signedURL", None)
    if not url:
        raise RuntimeError(f"create_signed_url: risposta inattesa: {resp!r}")
    if url.startswith("/"):
        url = (SUPABASE_URL or "").rstrip("/") + url
    return url


def signed_url(*, bucket: str, path: str, expires_in: int) -> str:
    """Genera un signed URL a scadenza per un oggetto gia' presente nello Storage.

    Funziona sia su bucket pubblici che privati: e' quindi sicuro passare al
    signed URL nel codice PRIMA di rendere privati i bucket lato Supabase, senza
    rompere i link esistenti."""
    client = get_admin_client()
    return _extract_signed_url(
        client.storage.from_(bucket).create_signed_url(path, expires_in)
    )


def upload_bytes(*, bucket: str, path: str, content: bytes,
                 content_type: str = "application/octet-stream",
                 expires_in: int = REPORT_URL_TTL) -> str:
    """Upload arbitrary bytes; ensure bucket exists; return a time-limited signed URL.

    C3: `upsert=true` sovrascrive se il path collide. La collisione cross-cliente
    e' mitigata a monte rendendo il path univoco per sessione + suffisso casuale
    (vedi generate_pdf._make_friendly_filename).

    SICUREZZA: il bucket viene creato PRIVATO e l'accesso e' servito via signed URL
    a scadenza, cosi' un path indovinato non basta piu' a scaricare un report
    altrui. NB infra (NON codice): i bucket gia' esistenti in prod vanno resi
    privati manualmente lato Supabase — questo codice non li modifica.
    """
    client = get_admin_client()
    storage = client.storage

    # Ensure bucket exists (idempotent).
    try:
        buckets = storage.list_buckets()
        names = {b.name if hasattr(b, "name") else b.get("name") for b in buckets}
        if bucket not in names:
            storage.create_bucket(bucket, options={"public": False})
            log.info("Created Supabase bucket (private): %s", bucket)
    except Exception as exc:  # noqa: BLE001
        log.warning("Bucket bootstrap warning: %s", exc)

    storage.from_(bucket).upload(
        path,
        content,
        {"content-type": content_type, "upsert": "true"},
    )
    return signed_url(bucket=bucket, path=path, expires_in=expires_in)


def upload_pdf(*, bucket: str, path: str, content: bytes,
               expires_in: int = REPORT_URL_TTL) -> str:
    """Upload PDF bytes; ensure bucket exists; return a time-limited signed URL."""
    return upload_bytes(bucket=bucket, path=path, content=content,
                        content_type="application/pdf", expires_in=expires_in)


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
