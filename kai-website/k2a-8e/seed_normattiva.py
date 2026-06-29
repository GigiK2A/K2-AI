"""Seed one-shot del corpus normattiva sul volume (/corpus).

Usa httpx (gia' dipendenza dell'8e), NON curl: python:3.12-slim non include curl.
Idempotente: skip se il file esiste gia'. Scarica in streaming su .part poi rename
atomico, cosi' app/normattiva.py (che apre il DB in immutable + controlla is_file())
non vede mai un file parziale. Eseguito in background da seed_and_run.sh.
"""
import os
import sys

import httpx

url = os.environ.get("NORMATTIVA_DB_URL")
dst = os.environ.get("NORMATTIVA_DB_PATH")
tok = os.environ.get("GH_TOKEN", "")

if not url or not dst:
    print("[seed] NORMATTIVA_DB_URL/PATH non settati - skip")
    sys.exit(0)
if os.path.exists(dst):
    print("[seed] normattiva.db gia' presente - skip")
    sys.exit(0)

headers = {"Accept": "application/octet-stream"}
if tok:
    headers["Authorization"] = "token " + tok

tmp = dst + ".part"
try:
    n = 0
    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
                n += len(chunk)
    os.replace(tmp, dst)
    print(f"[seed] normattiva.db pronto: {n} bytes")
except Exception as e:  # noqa: BLE001
    print(f"[seed] download FALLITO: {e}")
    try:
        os.remove(tmp)
    except OSError:
        pass
    sys.exit(1)
