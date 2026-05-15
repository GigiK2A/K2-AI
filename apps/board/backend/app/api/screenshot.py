"""POST /screenshot — render HTML to PNG via Playwright headless Chromium.

Auth: `X-API-Key` header must equal SCREENSHOT_API_KEY env. If env is empty,
endpoint returns 503 (disabled).

Body:
  {
    "html": "<html>...</html>",
    "width":  1080,  // optional, default 1080
    "height": 1350   // optional, default 1350
  }

Response: image/png binary.
"""
from __future__ import annotations

import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.settings import get_settings

router = APIRouter(prefix="/api/screenshot", tags=["screenshot"])
log = logging.getLogger(__name__)

# Bounds — keep memory/time predictable.
MIN_DIM = 64
MAX_DIM = 4096
MAX_HTML_BYTES = 1_000_000  # 1 MB
NAVIGATION_TIMEOUT_MS = 15_000


class ScreenshotRequest(BaseModel):
    html: str = Field(..., min_length=1)
    width: int = Field(default=1080, ge=MIN_DIM, le=MAX_DIM)
    height: int = Field(default=1350, ge=MIN_DIM, le=MAX_DIM)


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


@router.get("/health")
async def screenshot_health(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> dict:
    """Readiness probe — verifies Playwright + Chromium are usable.

    Returns 200 only if API key valid AND Chromium can be launched.
    """
    _check_auth(x_api_key)
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
        return {"status": "ok"}
    except Exception as exc:
        log.exception("screenshot health check failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chromium not available: {exc}",
        )


@router.post("")
async def screenshot(
    body: ScreenshotRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Response:
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

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
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

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-Image-Width": str(body.width),
            "X-Image-Height": str(body.height),
        },
    )
