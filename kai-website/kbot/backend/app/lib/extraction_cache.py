"""Hash-keyed cache for PDF/text/vision extraction results.

The same bilancio PDF often gets uploaded across multiple K-BOT sessions —
extracting it again costs 20-60s (and, for OCR, a non-trivial number of
Claude Vision tokens). We key by sha256 of the raw bytes so trivial filename
changes still hit the cache.

All operations are best-effort: a Supabase outage MUST NOT block uploads.
Cache misses simply fall through to the live extractor.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional, Tuple

log = logging.getLogger(__name__)

TABLE = "kbot_extraction_cache"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def lookup(hash_hex: str) -> Optional[dict]:
    """Return cached row dict or None. Never raises."""
    try:
        from .supabase_admin import get_admin_client

        client = get_admin_client()
        resp = client.table(TABLE).select("*").eq("hash", hash_hex).limit(1).execute()
        rows = getattr(resp, "data", None) or []
        if rows:
            return rows[0]
    except Exception as exc:  # pragma: no cover — defensive
        log.warning("extraction_cache lookup failed: %s", exc)
    return None


def store(
    hash_hex: str,
    *,
    extracted_text: str,
    extracted_summary: str,
    extraction_method: str,
    pages: Optional[list[dict]],
    bytes_size: int,
    mime: str,
) -> None:
    """Insert (or upsert) a cache row. Never raises."""
    try:
        from .supabase_admin import get_admin_client

        client = get_admin_client()
        row = {
            "hash": hash_hex,
            "extracted_text": extracted_text or "",
            "extracted_summary": extracted_summary or "",
            "extraction_method": extraction_method,
            "pages_json": pages or [],
            "bytes_size": int(bytes_size),
            "mime": mime or "",
        }
        # Use insert; on conflict the unique pk will reject — that's fine
        # (another concurrent upload wrote first; we keep the existing row).
        try:
            client.table(TABLE).insert(row).execute()
        except Exception:
            # Likely duplicate-key on parallel upload of the same file. Ignore.
            pass
    except Exception as exc:  # pragma: no cover — defensive
        log.warning("extraction_cache store failed: %s", exc)


def unpack(row: dict) -> Tuple[str, str, str, list[dict]]:
    """Convert a cache row back into the _extract_text tuple shape."""
    pages = row.get("pages_json") or []
    if not isinstance(pages, list):
        pages = []
    return (
        row.get("extracted_text") or "",
        row.get("extracted_summary") or "",
        row.get("extraction_method") or "none",
        pages,
    )
