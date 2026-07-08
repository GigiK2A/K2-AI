"""Seed one-shot dei corpora SQLite sul volume (/corpus) — normattiva + norme_tecniche.

Usa httpx (gia' dipendenza), NON curl (assente in python:3.12-slim). Per ogni coppia
(<URL>, <PATH>) configurata via env: scarica in streaming su .part poi rename atomico,
solo se il file non esiste gia' (idempotente). Eseguito in BACKGROUND da seed_and_run.sh
cosi' uvicorn parte subito (healthcheck ok) mentre i .db scendono; i resolver
(app/normattiva.py, vendor norme) controllano is_file()/aprono il DB on-demand.

Env per coppia: NORMATTIVA_DB_URL→NORMATTIVA_DB_PATH, NORME_DB_URL→NORME_DB_PATH.
Auth repo privato: GH_TOKEN (header Authorization: token ...).
"""
import os
import sys

import httpx

PAIRS = [
    ("NORMATTIVA_DB_URL", "NORMATTIVA_DB_PATH"),
    ("NORME_DB_URL", "NORME_DB_PATH"),
]
tok = os.environ.get("GH_TOKEN", "")
base_headers = {"Accept": "application/octet-stream"}
if tok and tok != "disabled-after-seed":
    base_headers["Authorization"] = "token " + tok

rc = 0
for url_env, path_env in PAIRS:
    url = os.environ.get(url_env)
    dst = os.environ.get(path_env)
    if not url or not dst:
        continue
    if os.path.exists(dst):
        # FORCE-REFRESH (8 lug 2026): il file c'e' gia', ma se l'asset e' stato RIPUBBLICATO
        # (corpus aggiornato) la dimensione remota differisce da quella locale → ri-scarico.
        # Cosi' aggiornare il corpus in prod = ri-caricare l'asset del release (nessun
        # bisogno di cancellare a mano il file sul volume). Se la HEAD fallisce o le
        # dimensioni coincidono → skip (idempotente, comportamento storico).
        local_size = os.path.getsize(dst)
        remote_size = 0
        try:
            h = httpx.head(url, headers=base_headers, follow_redirects=True, timeout=30)
            remote_size = int(h.headers.get("content-length") or 0)
        except Exception as e:  # noqa: BLE001
            print(f"[seed] {path_env} HEAD fallita ({e}) — mantengo il file presente, skip")
        if not remote_size or remote_size == local_size:
            print(f"[seed] {path_env} gia' presente e allineato ({local_size} b) — skip")
            continue
        print(f"[seed] {path_env} disallineato (locale {local_size} vs remoto {remote_size}) — ri-scarico")
    tmp = dst + ".part"
    try:
        n = 0
        with httpx.stream("GET", url, headers=base_headers, follow_redirects=True, timeout=None) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_bytes(1 << 20):
                    f.write(chunk)
                    n += len(chunk)
        os.replace(tmp, dst)
        print(f"[seed] {path_env} pronto: {n} bytes")
    except Exception as e:  # noqa: BLE001
        print(f"[seed] {path_env} download FALLITO: {e}")
        try:
            os.remove(tmp)
        except OSError:
            pass
        rc = 1

sys.exit(rc)
