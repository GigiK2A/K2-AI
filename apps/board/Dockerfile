# syntax=docker/dockerfile:1.7
# Unified K2-Board image: Next.js standalone (frontend) + FastAPI (backend)
# running side-by-side in one container. Frontend on $PORT (public),
# FastAPI on internal 127.0.0.1:8000 (proxied by Next.js rewrites).

# ---------- Stage 1: install Node deps ----------
FROM node:20-alpine AS web-deps
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci || npm install

# ---------- Stage 2: build Next.js standalone ----------
FROM node:20-alpine AS web-build
WORKDIR /web
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=web-deps /web/node_modules ./node_modules
COPY web/ ./
RUN npm run build

# ---------- Stage 3: runtime (Python + Node) ----------
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    INTERNAL_API_URL=http://127.0.0.1:8000

# System deps: ca-certs (TLS), curl (healthcheck), Node 20 (for Next.js server.js)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y --auto-remove gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python / FastAPI ---
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt
COPY backend/app /app/backend/app

# --- Next.js standalone build ---
# The standalone output bundles node_modules + a server.js at its root.
COPY --from=web-build /web/.next/standalone /app/web
COPY --from=web-build /web/.next/static /app/web/.next/static
COPY --from=web-build /web/public /app/web/public

# --- Entrypoint ---
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Non-root user
RUN useradd --create-home --uid 1001 app && chown -R app:app /app
USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-3000}/health" >/dev/null || exit 1

CMD ["/app/start.sh"]
