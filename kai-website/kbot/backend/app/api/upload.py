"""POST /api/kbot/upload — base64 file payloads → Supabase Storage + text extraction."""
from __future__ import annotations

import anthropic as _anthropic
import base64
import binascii
import logging
import re
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.analytics import track_server
from ..lib.auth import AuthUser, optional_user
from ..lib.limiter import limiter
from ..lib.supabase_admin import get_admin_client
from ..settings import STORAGE_UPLOADS_BUCKET

router = APIRouter()
log = logging.getLogger(__name__)

MAX_BYTES = 20 * 1024 * 1024  # 20 MB per file (bilanci/relazioni finanziarie PDF arrivano spesso a 10-15 MB)
TEXT_LIMIT = 40_000
PDF_LIMIT = 120_000  # bilanci/relazioni 50-200 pagine: serve testo abbondante


class FilePayload(BaseModel):
    name: str
    type: Optional[str] = ""
    size: Optional[int] = 0
    base64: str


class UploadBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    files: List[FilePayload]

    class Config:
        populate_by_name = True


_CLEAN_RE = re.compile(r"[^A-Za-z0-9._-]+")
_VISION_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

_BUCKET_READY = False


def _ensure_bucket(client) -> None:
    """Create the uploads bucket on first call. Idempotent, cached after success."""
    global _BUCKET_READY
    if _BUCKET_READY:
        return
    try:
        existing = client.storage.list_buckets()
        names = {b.name if hasattr(b, "name") else b.get("name") for b in existing}
        if STORAGE_UPLOADS_BUCKET not in names:
            client.storage.create_bucket(
                STORAGE_UPLOADS_BUCKET,
                options={"public": True},
            )
            log.info("created supabase storage bucket %s", STORAGE_UPLOADS_BUCKET)
        _BUCKET_READY = True
    except Exception as exc:
        msg = str(exc).lower()
        if "already exists" in msg or "duplicate" in msg or "23505" in msg:
            _BUCKET_READY = True
            return
        log.exception("ensure_bucket failed for %s", STORAGE_UPLOADS_BUCKET)
        # Don't raise — let the actual upload attempt surface a clearer error.


def _clean_filename(name: str) -> str:
    return _CLEAN_RE.sub("_", name).strip("._") or "file"


def _analyze_image_vision(data: bytes, mime: str, name: str) -> str:
    """Call Claude Vision to describe the image. Returns description string."""
    from ..settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

    b64 = base64.b64encode(data).decode("utf-8")
    client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f'Analizza questa immagine "{name}" e descrivi in dettaglio: '
                            "testo visibile, struttura e layout, elementi chiave (titoli, CTA, grafici, form, tabelle). "
                            "Sii preciso e completo. Rispondi in italiano."
                        ),
                    },
                ],
            }
        ],
        timeout=60.0,
    )
    return response.content[0].text.strip() if response.content else ""


def _decode_b64(payload: str) -> bytes:
    # Accept "data:...;base64,..." prefix.
    stripped = payload.lstrip()
    if stripped.startswith("data:"):
        if "," in stripped:
            payload = stripped.split(",", 1)[1]
        else:
            # data: prefix senza virgola: payload malformato, NON tentare decode
            raise HTTPException(status_code=400, detail="invalid data-URI payload")
    try:
        return base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid base64: {exc}") from exc


def _extract_text(content: bytes, name: str, mime: str) -> tuple[str, str, str]:
    """Return (extracted_text, extracted_summary, method)."""
    lower = name.lower()
    is_pdf = mime == "application/pdf" or lower.endswith(".pdf")
    is_text = mime.startswith("text/") or lower.endswith((".txt", ".md", ".csv", ".json", ".xml"))

    if is_text:
        try:
            text = content.decode("utf-8", errors="replace")[:TEXT_LIMIT]
            return text, "", "text-decode"
        except Exception:
            pass

    if is_pdf:
        try:
            import pdfplumber  # lazy import

            from io import BytesIO

            with pdfplumber.open(BytesIO(content)) as pdf:
                pages = []
                for page in pdf.pages[:120]:
                    txt = page.extract_text() or ""
                    if txt.strip():
                        pages.append(txt)
                text = "\n\n".join(pages)[:PDF_LIMIT]
                if len(text.strip()) >= 120:
                    return text, "", "pdf-parse"
        except Exception as exc:
            log.warning("pdf-parse failed for %s: %s", name, exc)

    if mime in _VISION_MIMES or any(name.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        try:
            description = _analyze_image_vision(content, mime or "image/jpeg", name)
            if description:
                return "", description, "claude-vision"
        except Exception as exc:
            log.warning("vision analysis failed for %s: %s", name, exc)

    return "", "Nessun testo estraibile dal file.", "none"


@router.post("/upload")
@limiter.limit("10/minute")
def upload(
    request: Request,
    body: UploadBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    client = get_admin_client()
    _ensure_bucket(client)
    storage = client.storage.from_(STORAGE_UPLOADS_BUCKET)

    saved = []
    for f in body.files:
        data = _decode_b64(f.base64)
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=413, detail=f"{f.name}: exceeds 20 MB")

        clean = _clean_filename(f.name)
        path = f"{body.sessionId}/{int(time.time() * 1000)}-{clean}"
        try:
            storage.upload(
                path,
                data,
                {"content-type": f.type or "application/octet-stream", "upsert": "true"},
            )
        except Exception:
            log.exception("storage upload failed")
            raise HTTPException(status_code=500, detail="Upload non riuscito. Riprova.")

        public_url = storage.get_public_url(path)
        extracted_text, extracted_summary, method = _extract_text(data, f.name, f.type or "")

        saved.append(
            {
                "name": f.name,
                "type": f.type or "",
                "size": len(data),
                "path": path,
                "publicUrl": public_url,
                "extractedText": extracted_text,
                "extractedSummary": extracted_summary,
                "extractionMethod": method,
            }
        )
        track_server(
            distinct_id=body.sessionId,
            event="file_uploaded",
            properties={
                "extraction_method": method,
                "mime": f.type or "",
                "size_bytes": len(data),
            },
        )

    collected = dict(session.get("collected_data") or {})
    current_files = list(collected.get("uploaded_files") or [])
    current_files.extend(saved)
    collected["uploaded_files"] = current_files

    sessions.update_session(body.sessionId, {"collected_data": collected})
    return {"files": saved}
