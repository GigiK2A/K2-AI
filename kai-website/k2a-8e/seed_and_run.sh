#!/usr/bin/env sh
# Avvio 8e + seed one-shot dei corpora sul volume (/corpus): normattiva + norme_tecniche.
# Il download gira in BACKGROUND: uvicorn parte subito (healthcheck /health ok), e i
# resolver rilevano il .db appena pronto (is_file()/open on-demand). Idempotente.
if [ -n "$NORMATTIVA_DB_URL" ] || [ -n "$NORME_DB_URL" ]; then
  echo "[seed] avvio download corpora in background (python/httpx)"
  python3 seed_corpus.py &
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8800}"
