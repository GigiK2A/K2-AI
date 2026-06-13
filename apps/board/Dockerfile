# syntax=docker/dockerfile:1.7
# K2-AI AIOS — cockpit (FastAPI/uvicorn) + autonomia. Sostituisce il vecchio K2-Board.
# Servizio Railway "k2-board": Root Directory = apps/board, builder = Dockerfile.
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AIOS_HOST=0.0.0.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dipendenze esplicite (no build del pacchetto): l'app gira da /app/src via
# PYTHONPATH, così i file dati — cockpit.html, skills SKILL.md — restano leggibili
# da disco senza configurare package-data. (Tenere allineato a pyproject.toml.)
RUN pip install "psycopg[binary]>=3.1" "anthropic>=0.40" "fastapi>=0.110" "uvicorn>=0.29"
COPY src ./src
# Entrypoint + runner (worker autonomia opzionale via AIOS_AUTONOMY=1)
COPY serve_cockpit.py autonomy_loop.py scheduler.py telegram_bot.py ./
ENV PYTHONPATH=/app/src

RUN useradd --create-home --uid 1001 app && chown -R app:app /app
USER app

EXPOSE 8800

# Railway inietta $PORT; serve_cockpit ci fa il bind. /health è pubblico (no auth).
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8800}/health" >/dev/null || exit 1

CMD ["python", "serve_cockpit.py"]
