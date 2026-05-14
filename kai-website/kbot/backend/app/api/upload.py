"""POST /api/kbot/upload — base64 file payloads → Supabase Storage + text extraction."""
from __future__ import annotations

import base64
import logging
import re
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..lib.supabase_admin import get_admin_client
from ..settings import STORAGE_UPLOADS_BUCKET

router = APIRouter()
log = logging.getLogger(__name__)

MAX_BYTES = 3 * 1024 * 1024  # 3 MB per file, mirroring site limit
TEXT_LIMIT = 12_000
PDF_LIMIT = 30_000


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


def _clean_filename(name: str) -> str:
    return _CLEAN_RE.sub("_", name).strip("._") or "file"


def _decode_b64(payload: str) -> bytes:
    # Accept "data:...;base64,..." prefix.
    if "," in payload and payload.lstrip().startswith("data:"):
        payload = payload.split(",", 1)[1]
    return base64.b64decode(payload, validate=False)


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
                for page in pdf.pages[:30]:
                    txt = page.extract_text() or ""
                    if txt.strip():
                        pages.append(txt)
                text = "\n\n".join(pages)[:PDF_LIMIT]
                if len(text.strip()) >= 120:
                    return text, "", "pdf-parse"
        except Exception as exc:
            log.warning("pdf-parse failed for %s: %s", name, exc)

    return "", "Nessun testo estraibile dal file.", "none"


@router.post("/upload")
def upload(body: UploadBody, user: Optional[AuthUser] = Depends(optional_user)):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    client = get_admin_client()
    storage = client.storage.from_(STORAGE_UPLOADS_BUCKET)

    saved = []
    for f in body.files:
        data = _decode_b64(f.base64)
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=413, detail=f"{f.name}: exceeds 3 MB")

        clean = _clean_filename(f.name)
        path = f"{body.sessionId}/{int(time.time() * 1000)}-{clean}"
        try:
            storage.upload(
                path,
                data,
                {"content-type": f.type or "application/octet-stream", "upsert": "true"},
            )
        except Exception as exc:
            log.exception("storage upload failed")
            raise HTTPException(status_code=500, detail=f"upload failed: {exc}")

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

    collected = dict(session.get("collected_data") or {})
    current_files = list(collected.get("uploaded_files") or [])
    current_files.extend(saved)
    collected["uploaded_files"] = current_files

    sessions.update_session(body.sessionId, {"collected_data": collected})
    return {"files": saved}
