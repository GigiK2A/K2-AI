"""Serve the AIOS cockpit on http://localhost:8800 over the Supabase-backed kernel.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python serve_cockpit.py
"""
import os

import uvicorn

from aios.kernel import Kernel
from aios.api.app import create_app

kernel = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                   os.environ["AIOS_SUPABASE_SERVICE_KEY"])
app = create_app(kernel)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)
