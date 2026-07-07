"""Upload di un'immagine su Supabase Storage (bucket pubblico) → URL pubblico.

Serve alla pubblicazione IG: Meta preleva l'immagine da un URL PUBBLICO, quindi
un'immagine allegata in chat (base64) va prima caricata qui. Nome file = hash del
contenuto (deterministico, niente duplicati). Env: AIOS_SUPABASE_URL + SERVICE_KEY.
"""
from __future__ import annotations

import base64
import hashlib
import os
import urllib.error
import urllib.request

BUCKET = "ig-media"


def _ext(name: str, media_type: str) -> str:
    n = (name or "").lower()
    for e in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if n.endswith(e):
            return e
    return {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
            "image/gif": ".gif"}.get((media_type or "").lower(), ".jpg")


def upload_public(name: str, media_type: str, data_b64: str,
                  bucket: str = BUCKET) -> dict:
    """Carica l'immagine e ritorna {'ok':True,'url':...} pubblico, o {'ok':False,'errore'}."""
    base = os.environ.get("AIOS_SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("AIOS_SUPABASE_SERVICE_KEY", "")
    if not base or not key:
        return {"ok": False, "errore": "Supabase non configurato"}
    try:
        raw = base64.b64decode(data_b64 or "")
    except Exception:
        return {"ok": False, "errore": "immagine non valida (base64)"}
    if not raw:
        return {"ok": False, "errore": "immagine vuota"}
    path = hashlib.sha1(raw).hexdigest()[:16] + _ext(name, media_type)
    req = urllib.request.Request(
        f"{base}/storage/v1/object/{bucket}/{path}", data=raw, method="POST",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": media_type or "application/octet-stream",
                 "x-upsert": "true"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            r.read()
    except urllib.error.HTTPError as exc:
        try:
            return {"ok": False, "errore": exc.read().decode("utf-8", "replace")[:200]}
        except Exception:
            return {"ok": False, "errore": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"ok": False, "errore": str(exc)[:200]}
    return {"ok": True, "url": f"{base}/storage/v1/object/public/{bucket}/{path}"}
