"""POST /api/screenshot — render HTML to PNG via Playwright, upload to Supabase Storage.

Auth: `X-API-Key` header must equal SCREENSHOT_API_KEY env. If env is empty,
endpoint returns 503 (disabled).

Body:
  {
    "html":   "<html>...</html>",
    "width":  1080,  // optional, default 1080
    "height": 1350   // optional, default 1350
  }

Response:
  { "url": "https://<project>.supabase.co/storage/v1/object/public/instagram-slides/slides/..." }

Files stored at: slides/{timestamp}_{uuid4()}.png in bucket `instagram-slides` (public).
"""
from __future__ import annotations

import logging
import secrets
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.db.client import get_supabase
from app.settings import get_settings

router = APIRouter(prefix="/api/screenshot", tags=["screenshot"])
log = logging.getLogger(__name__)

# Bounds — keep memory/time predictable.
MIN_DIM = 64
MAX_DIM = 4096
MAX_HTML_BYTES = 1_000_000  # 1 MB
NAVIGATION_TIMEOUT_MS = 15_000

STORAGE_BUCKET = "instagram-slides"
STORAGE_PREFIX = "slides"


class ScreenshotRequest(BaseModel):
    html: str = Field(..., min_length=1)
    width: int = Field(default=1080, ge=MIN_DIM, le=MAX_DIM)
    height: int = Field(default=1350, ge=MIN_DIM, le=MAX_DIM)


class ScreenshotResponse(BaseModel):
    url: str


def _check_auth(x_api_key: Optional[str]) -> None:
    settings = get_settings()
    expected = settings.screenshot_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Screenshot service disabled (SCREENSHOT_API_KEY not configured)",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _ensure_bucket_exists() -> None:
    """Create the storage bucket if missing. Idempotent."""
    client = get_supabase()
    try:
        existing = client.storage.list_buckets()
        names = {b.name if hasattr(b, "name") else b.get("name") for b in existing}
        if STORAGE_BUCKET in names:
            return
        client.storage.create_bucket(STORAGE_BUCKET, options={"public": True})
        log.info("created supabase storage bucket %s", STORAGE_BUCKET)
    except Exception as exc:
        # If the bucket already exists, create_bucket raises — that's fine.
        msg = str(exc).lower()
        if "already exists" in msg or "duplicate" in msg or "23505" in msg:
            return
        raise


@router.get("/health")
async def screenshot_health(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> dict:
    """Readiness probe — verifies Chromium boots AND Supabase storage reachable."""
    _check_auth(x_api_key)
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
    except Exception as exc:
        log.exception("chromium probe failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chromium not available: {exc}",
        )

    try:
        _ensure_bucket_exists()
    except Exception as exc:
        log.exception("supabase bucket probe failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase storage unreachable: {exc}",
        )

    return {"status": "ok", "storage_bucket": STORAGE_BUCKET}


@router.post("", response_model=ScreenshotResponse)
async def screenshot(
    body: ScreenshotRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> ScreenshotResponse:
    _check_auth(x_api_key)

    if len(body.html.encode("utf-8")) > MAX_HTML_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"HTML exceeds {MAX_HTML_BYTES} bytes",
        )

    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"playwright not installed: {exc}",
        )

    # 1) Render PNG with Playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                context = await browser.new_context(
                    viewport={"width": body.width, "height": body.height},
                    device_scale_factor=1,
                )
                page = await context.new_page()
                await page.set_content(
                    body.html,
                    wait_until="networkidle",
                    timeout=NAVIGATION_TIMEOUT_MS,
                )
                png_bytes = await page.screenshot(
                    type="png",
                    full_page=False,
                    omit_background=False,
                )
                await context.close()
            finally:
                await browser.close()
    except Exception as exc:
        log.exception("screenshot render failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Render failed: {exc}",
        )

    # 2) Upload to Supabase Storage
    try:
        _ensure_bucket_exists()
        client = get_supabase()
        filename = f"{STORAGE_PREFIX}/{int(time.time() * 1000)}_{uuid.uuid4().hex}.png"
        client.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=png_bytes,
            file_options={"content-type": "image/png", "upsert": "false"},
        )
        public = client.storage.from_(STORAGE_BUCKET).get_public_url(filename)
        # get_public_url returns URL; strip trailing '?' if SDK appends it.
        public_url = public.rstrip("?")
    except Exception as exc:
        log.exception("supabase upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase upload failed: {exc}",
        )

    return ScreenshotResponse(url=public_url)
