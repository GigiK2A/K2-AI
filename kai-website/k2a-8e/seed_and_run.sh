#!/usr/bin/env sh
# Avvio 8e + seed one-shot del corpus normattiva sul volume (/corpus).
# Il download gira in BACKGROUND: uvicorn parte subito (healthcheck /health ok),
# e app/normattiva.py rileva il .db appena pronto (controlla is_file() per-richiesta).
# Idempotente: scarica solo se NORMATTIVA_DB_URL è settato e il file non esiste già.
if [ -n "$NORMATTIVA_DB_URL" ] && [ ! -f "$NORMATTIVA_DB_PATH" ]; then
  echo "[seed] avvio download normattiva.db in background (python/httpx)"
  python3 seed_normattiva.py &
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8800}"
