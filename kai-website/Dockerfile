# =============================================================================
# K2-AI — Unified container (Vite site + Next.js kbot standalone + Python kbot
# backend + Playwright Chromium).
# Single Node entrypoint (server.js) supervises:
#   - the Next.js kbot standalone (child Node process on :4174)
#   - the FastAPI Python kbot backend (child uvicorn process on :8000)
# =============================================================================

# -------- Stage 1: build Vite (kai-website) + Next.js (kbot) --------
FROM node:20-slim AS node-build

WORKDIR /app

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
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install Python 3 + Chromium runtime libs for Playwright.
# `playwright install-deps chromium` would normally pull these, but doing it
# explicitly via apt keeps the image deterministic and avoids the host check.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcairo2 libcups2 \
    libdbus-1-3 libdrm2 libexpat1 libgbm1 libglib2.0-0 libnspr4 libnss3 \
    libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 \
    libxfixes3 libxkbcommon0 libxrandr2 wget xdg-utils \
  && rm -rf /var/lib/apt/lists/*

# -------- Install Python dependencies for kbot backend --------
COPY kbot/backend/requirements.txt /tmp/kbot-requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/kbot-requirements.txt \
  && playwright install chromium

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

EXPOSE 4173

CMD ["node", "server.js"]
