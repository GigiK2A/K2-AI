"""Generazione immagini con GPT Image (OpenAI Images API).

Eccezione al 'no OpenAI' approvata dall'owner (lug 2026): oltre alla web search del
K-BOT, OpenAI è usato QUI solo per generare immagini per i post. Tutto il resto resta
Claude. Ritorna base64 (poi caricata su Supabase Storage → URL pubblico per la pubblicazione).
Env: OPENAI_API_KEY, opz. OPENAI_IMAGE_MODEL (default gpt-image-1).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_ENDPOINT = "https://api.openai.com/v1/images/generations"


def generate_image(prompt: str, *, size: str = "1024x1024",
                   model: str | None = None) -> dict[str, Any]:
    """Genera un'immagine da un prompt testuale. Ritorna {'ok':True,'b64':...} (o 'url'),
    oppure {'ok':False,'errore':...}."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return {"ok": False, "errore": "OPENAI_API_KEY non configurato sul board"}
    if not prompt or not str(prompt).strip():
        return {"ok": False, "errore": "prompt vuoto"}
    mdl = model or os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
    body = json.dumps({"model": mdl, "prompt": str(prompt), "size": size,
                       "n": 1}).encode("utf-8")
    req = urllib.request.Request(_ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            msg = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            msg = f"HTTP {exc.code}"
        return {"ok": False, "errore": (msg or f"HTTP {exc.code}")[:220]}
    except Exception as exc:
        return {"ok": False, "errore": str(exc)[:200]}
    items = d.get("data") or []
    if not items:
        return {"ok": False, "errore": "nessuna immagine restituita"}
    it = items[0]
    if it.get("b64_json"):
        return {"ok": True, "b64": it["b64_json"]}
    if it.get("url"):
        return {"ok": True, "url": it["url"]}
    return {"ok": False, "errore": "formato risposta immagine inatteso"}
