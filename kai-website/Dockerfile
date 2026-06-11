# =============================================================================
# K2-AI — Unified container (Vite site + Next.js kbot standalone + Python kbot
# backend + WeasyPrint PDF rendering).
# Single Node entrypoint (server.js) supervises:
#   - the Next.js kbot standalone (child Node process on :4174)
#   - the FastAPI Python kbot backend (child uvicorn process on :8000)
# =============================================================================

# -------- Stage 1: build Vite (kai-website) + Next.js (kbot) --------
FROM node:20-slim AS node-build

WORKDIR /app

# Build args: Next.js bakes NEXT_PUBLIC_* into the client bundle at build
# time, so Railway env vars must be forwarded as ARG/ENV here.
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_API_BASE_URL=""
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=""
ARG NEXT_PUBLIC_SITE_URL="https://www.k2-ai.it"
# K-BOT ufficiale: genera via motore 8e senza paywall (default ON nell'immagine).
ARG NEXT_PUBLIC_KBOT_FREE_MODE="1"

ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY} \
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL} \
    NEXT_PUBLIC_KBOT_FREE_MODE=${NEXT_PUBLIC_KBOT_FREE_MODE}

# Build kai-website (Vite)
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Build kbot Next.js (output: standalone)
WORKDIR /app/kbot
RUN npm ci
RUN npm run build


# -------- Stage 2: runtime image — Debian-based to fit Node + Python + Chromium --------
FROM node:20-slim

WORKDIR /app

ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Python 3 only — ReportLab è pure-python con font Helvetica builtin.
# Niente più Chromium (Playwright) né libpango (WeasyPrint) → immagine
# docker più piccola, cold start più rapido, zero apt-get dipendenze
# native per il PDF rendering.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# -------- Install Python dependencies for kbot backend --------
COPY kbot/backend/requirements.txt /tmp/kbot-requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/kbot-requirements.txt

# -------- Copy Python backend source --------
COPY kbot/backend/app ./kbot-backend/app
COPY kbot/backend/Procfile ./kbot-backend/Procfile

# -------- Install Python deps + source for the 8e engine (motore deliverable) --------
# Gira come co-processo in questo stesso container (loopback :8800). Le deps sono
# in gran parte già soddisfatte dal backend kbot; pip salta quelle presenti.
COPY k2a-8e/requirements.txt /tmp/engine-8e-requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/engine-8e-requirements.txt
# Struttura preservata (8e risolve ROOT = __file__.parent.parent):
COPY k2a-8e/app ./engine-8e/app
COPY k2a-8e/blueprints ./engine-8e/blueprints
COPY k2a-8e/catalog ./engine-8e/catalog
COPY k2a-8e/grounding ./engine-8e/grounding
COPY k2a-8e/k2a_validation ./engine-8e/k2a_validation
COPY k2a-8e/assets ./engine-8e/assets

# -------- Install Node runtime dependencies for server.js --------
COPY package*.json ./
RUN npm ci --omit=dev

# -------- Copy build artifacts and runtime sources --------
COPY --from=node-build /app/dist ./dist
COPY --from=node-build /app/kbot/.next/standalone ./kbot-standalone
COPY --from=node-build /app/kbot/.next/static ./kbot-standalone/.next/static
COPY --from=node-build /app/kbot/public ./kbot-standalone/public
COPY server.js ./server.js
COPY lib ./lib

# Skills directory: the Python backend reads from KBOT_SKILLS_DIR which defaults
# to ../../lib/skills relative to the backend root. Expose via env to be safe.
ENV KBOT_SKILLS_DIR=/app/lib/skills \
    KBOT_PYTHON_DIR=/app/kbot-backend \
    KBOT_PYTHON_PORT=8000 \
    KBOT_PYTHON_BIN=/usr/bin/python3 \
    ENGINE_8E_DIR=/app/engine-8e \
    ENGINE_8E_PORT=8800 \
    K2A_8E_BASE_URL=http://127.0.0.1:8800 \
    K2A_8E_API_KEY=k2a-8e-internal-loopback \
    K2A_8E_ENTITLEMENT_DEV=true \
    K2A_8E_OUT_DIR=/tmp/8e_out \
    KBOT_FREE_MODE=1

# Run as a non-root user (node:20-slim ships with the "node" user, uid 1000).
# Tutto sotto /app è read-only a runtime (upload → Supabase storage + /tmp).
RUN chown -R node:node /app 2>/dev/null || true
USER node

EXPOSE 4173

CMD ["node", "server.js"]
