"""Serve the K2-AI AIOS cockpit on http://localhost:8800 over the full platform
(kernel + sensors + knowledge + multi-domain agents). Cockpit shows only what the
agents read/produce; nothing hardcoded.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY, AIOS_IG_TOKEN, ANTHROPIC_API_KEY.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python serve_cockpit.py
"""
import os

import uvicorn

from aios.platform import build_platform
from aios.api.app import create_app

platform = build_platform()
app = create_app(platform.kernel, platform=platform)

if __name__ == "__main__":
    # Locale: 127.0.0.1:8800. Deploy: imposta PORT (Railway) e AIOS_HOST=0.0.0.0
    # (mettere dietro reverse proxy HTTPS e impostare AIOS_API_TOKEN).
    host = os.environ.get("AIOS_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("AIOS_PORT", "8800")))
    uvicorn.run(app, host=host, port=port)
