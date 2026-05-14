"""Supabase Storage helpers."""
from __future__ import annotations

import logging
from typing import Optional

from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)


def upload_pdf(*, bucket: str, path: str, content: bytes) -> str:
    """Upload PDF bytes; ensure bucket exists; return public URL."""
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
        {"content-type": "application/pdf", "upsert": "true"},
    )
    return storage.from_(bucket).get_public_url(path)
