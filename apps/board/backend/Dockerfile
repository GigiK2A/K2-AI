FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps kept minimal — supabase-py is pure-python; bcrypt ships wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app

# Non-root user
RUN useradd --create-home --uid 1001 board && chown -R board:board /app
USER board

EXPOSE 8000

# Railway hits the platform-level healthcheck (railway.toml), but keep one
# here too so `docker run` reports liveness correctly.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,os,sys; \
url=f\"http://127.0.0.1:{os.environ.get('PORT','8000')}/health\"; \
sys.exit(0 if urllib.request.urlopen(url, timeout=3).status==200 else 1)" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
