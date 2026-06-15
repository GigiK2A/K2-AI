"""Endpoint HTML→PNG per n8n (slide Instagram). Contratto FISSO:
  POST /api/screenshot   header X-API-Key: <SCREENSHOT_API_KEY>
  body  {html, width, height}  ->  {"url": "https://api.k2-ai.it/shots/<uuid>.png"}

Render con Playwright Chromium headless: il browser parte UNA volta allo startup e
viene riusato. Il PNG finisce in una cartella servita pubblicamente su /shots (la
scarica Meta/Instagram senza auth). Niente chiave nel codice: solo da env.
"""
from __future__ import annotations

import os
import secrets
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Cartella pubblica per i PNG (ephemeral va bene: servono pochi minuti).
SHOTS_DIR = Path(os.environ.get("AIOS_SHOTS_DIR", "/tmp/aios_shots"))
SHOTS_DIR.mkdir(parents=True, exist_ok=True)
# Base URL pubblica (i workflow puntano ad api.k2-ai.it). Override via env per il locale.
_BASE = os.environ.get("SCREENSHOT_BASE_URL", "https://api.k2-ai.it").rstrip("/")
_TTL_S = int(os.environ.get("AIOS_SHOTS_TTL_S", "1800"))   # cleanup differito (~30 min)


class ShotBody(BaseModel):
    html: str
    width: int = 1080
    height: int = 1350


def _require_screenshot_key(request: Request) -> None:
    key = os.environ.get("SCREENSHOT_API_KEY", "")
    got = request.headers.get("x-api-key", "")
    if not (key and got and secrets.compare_digest(got, key)):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _cleanup_old() -> None:
    """Rimuove i PNG più vecchi di TTL (cleanup differito, mai immediato)."""
    cutoff = time.time() - _TTL_S
    try:
        for f in SHOTS_DIR.glob("*.png"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except OSError:
                pass
    except OSError:
        pass


def add_screenshot(app: FastAPI) -> None:
    """Monta /shots (statico pubblico) + l'endpoint /api/screenshot sull'app esistente."""
    app.mount("/shots", StaticFiles(directory=str(SHOTS_DIR)), name="shots")
    state: dict = {"pw": None, "browser": None}

    @app.on_event("startup")
    async def _start_browser() -> None:
        # Browser unico, riusato fra le richieste. Se Playwright/Chromium non c'è
        # (es. ambiente locale/CI) l'endpoint risponde 503, il resto dell'app è ok.
        try:
            from playwright.async_api import async_playwright
            state["pw"] = await async_playwright().start()
            state["browser"] = await state["pw"].chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        except Exception:
            state["browser"] = None

    @app.on_event("shutdown")
    async def _stop_browser() -> None:
        try:
            if state["browser"]:
                await state["browser"].close()
            if state["pw"]:
                await state["pw"].stop()
        except Exception:
            pass

    @app.post("/api/screenshot")
    async def screenshot(body: ShotBody, _=Depends(_require_screenshot_key)) -> dict:
        browser = state["browser"]
        if browser is None:
            raise HTTPException(status_code=503, detail="renderer non disponibile")
        w = max(1, min(int(body.width or 1080), 4000))
        h = max(1, min(int(body.height or 1350), 6000))
        page = await browser.new_page(viewport={"width": w, "height": h},
                                      device_scale_factor=2)
        try:
            page.set_default_timeout(60000)
            # networkidle = aspetta che font/immagini remote abbiano finito di caricare
            await page.set_content(body.html, wait_until="networkidle", timeout=60000)
            try:
                await page.evaluate("() => (document.fonts && document.fonts.ready) || true")
            except Exception:
                pass
            await page.wait_for_timeout(350)   # margine per render/fonts
            name = f"{uuid.uuid4().hex}.png"
            await page.screenshot(path=str(SHOTS_DIR / name), type="png",
                                  clip={"x": 0, "y": 0, "width": w, "height": h})
        finally:
            try:
                await page.close()
            except Exception:
                pass
        _cleanup_old()   # differito: cancella solo i vecchi, non questo
        return {"url": f"{_BASE}/shots/{name}"}
