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

ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY} \
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}

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

# Python 3 + WeasyPrint native deps (libpango/cairo/harfbuzz/gdk-pixbuf).
# Era chromium per Playwright; ora WeasyPrint sync, niente headless browser.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    ca-certificates fonts-liberation fonts-inter \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    libcairo2 libgdk-pixbuf-2.0-0 shared-mime-info \
  && rm -rf /var/lib/apt/lists/*

# -------- Install Python dependencies for kbot backend --------
COPY kbot/backend/requirements.txt /tmp/kbot-requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/kbot-requirements.txt

# -------- Copy Python backend source --------
COPY kbot/backend/app ./kbot-backend/app
COPY kbot/backend/Procfile ./kbot-backend/Procfile

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
    KBOT_PYTHON_BIN=/usr/bin/python3

# Run as a non-root user (node:20-slim ships with the "node" user, uid 1000).
# Tutto sotto /app è read-only a runtime (upload → Supabase storage + /tmp).
RUN chown -R node:node /app 2>/dev/null || true
USER node

EXPOSE 4173

CMD ["node", "server.js"]
