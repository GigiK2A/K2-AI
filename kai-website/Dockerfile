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
# Paywall reale di default (produzione). =1 solo per demo/dev: salta il pagamento.
ARG NEXT_PUBLIC_KBOT_FREE_MODE="0"
# Paywall PIENO con pagamento simulato (demo): mostra prezzo + bottone, ma il
# "paga" non apre Stripe — marca paid e genera. =1 per la demo, 0 in produzione.
ARG NEXT_PUBLIC_KBOT_FAKE_PAYMENT="0"

ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY} \
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL} \
    NEXT_PUBLIC_KBOT_FREE_MODE=${NEXT_PUBLIC_KBOT_FREE_MODE} \
    NEXT_PUBLIC_KBOT_FAKE_PAYMENT=${NEXT_PUBLIC_KBOT_FAKE_PAYMENT}

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
    python3 python3-pip python3-venv ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

# Tailscale (userspace, non-root): se TS_AUTHKEY è impostata a runtime, la chat/8e
# raggiungono il modello LLM locale via tailnet invece del quick tunnel. Binari statici
# dall'immagine ufficiale; INERTI senza TS_AUTHKEY (vedi entrypoint.sh) → deploy invariato.
COPY --from=tailscale/tailscale:stable /usr/local/bin/tailscaled /usr/local/bin/tailscaled
COPY --from=tailscale/tailscale:stable /usr/local/bin/tailscale  /usr/local/bin/tailscale

# -------- §3c · Corpus Normattiva (normattiva.db, ~1.8GB FTS5) — fetch build-time --------
# POSIZIONE: subito dopo apt-get (curl c'è) e PRIMA delle COPY del codice → il layer (1.8GB)
# si CACHA e NON si ri-scarica a ogni commit (la COPY di app/, che cambia sempre,
# invaliderebbe tutto ciò che la segue, incluso questo fetch). DORMIENTE se la URL non è
# settata. NON-FATALE + bounded (--max-time): se il download non finisce entro il budget
# (URL throttled tipo pub-*.r2.dev, o deadline di build) il RUN NON fa fallire il build —
# normattiva resta dormiente (il resolver degrada onesto: available()=False, niente
# citazioni inventate) e tutto il resto (report, boost) deploya comunque. Il parziale viene
# rimosso per non lasciare un .db SQLite corrotto. Quando la URL diventa veloce (R2 custom
# domain / presigned), cambiare NORMATTIVA_DB_URL busta la cache e il download riparte.
ARG NORMATTIVA_DB_URL=""
RUN if [ -n "$NORMATTIVA_DB_URL" ]; then \
      mkdir -p /app/engine-8e && \
      echo "§3c: fetch normattiva.db (best-effort, non-fatale, max 8 min)…" && \
      { curl -fSL --max-time 480 "$NORMATTIVA_DB_URL" -o /app/engine-8e/normattiva.db \
        && ls -lh /app/engine-8e/normattiva.db ; } \
      || { echo "§3c: download non completato entro il budget → normattiva DORMIENTE"; \
           rm -f /app/engine-8e/normattiva.db ; } ; \
    else echo "§3c: NORMATTIVA_DB_URL non settato → normattiva DORMIENTE (resolver degrada onesto)"; fi

# -------- Install Python dependencies for kbot backend --------
COPY kbot/backend/requirements.txt /tmp/kbot-requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/kbot-requirements.txt

# -------- Copy Python backend source --------
COPY kbot/backend/app ./kbot-backend/app
COPY kbot/backend/Procfile ./kbot-backend/Procfile
# Compute layer: i package MCP vendorizzati di Luca (k2a_quant ecc., ~65MB). Servono
# al compute layer (/api/kbot/tools, check express) E al fallback MCP-stdio del quant
# (mcp_client lancia `python -m k2a_quant.server` dal vendored se manca l'entrypoint
# pip). Senza questa COPY erano assenti in prod → compute vuoto + quant/health 503.
COPY kbot/backend/vendor ./kbot-backend/vendor

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
# Pacchetti vendorizzati del motore 8e (k2a_quant/k2a_budget/elettrico/norme/strutturale):
# i binder deterministici (advisor/finance/§E budget/mep/agevolazioni) li importano a runtime
# via sys.path. Senza questa COPY → ModuleNotFoundError quando un boost prova a generare.
COPY k2a-8e/vendor ./engine-8e/vendor

# -------- Install Node runtime dependencies for server.js --------
COPY package*.json ./
RUN npm ci --omit=dev

# -------- Copy build artifacts and runtime sources --------
COPY --from=node-build /app/dist ./dist
COPY --from=node-build /app/kbot/.next/standalone ./kbot-standalone
COPY --from=node-build /app/kbot/.next/static ./kbot-standalone/.next/static
COPY --from=node-build /app/kbot/public ./kbot-standalone/public
COPY server.js ./server.js
COPY entrypoint.sh ./entrypoint.sh
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
    K2A_8E_OUT_DIR=/tmp/8e_out \
    NORMATTIVA_DB_PATH=/app/engine-8e/normattiva.db
# PRODUZIONE: paywall + entitlement firmato attivi di default.
# - K2A_8E_ENTITLEMENT_DEV NON è settato → l'8e è fail-closed: senza
#   K2A_ENTITLEMENT_SECRET RIFIUTA (nessun bypass silenzioso).
# - KBOT_FREE_MODE non settato (=0) → la generazione richiede pagamento.
# RICHIESTO in Railway env (backend E 8e, stesso valore): K2A_ENTITLEMENT_SECRET.
#
# DEMO "pagamento finto" (paywall PIENO, prezzo+bottone veri, NIENTE Stripe):
#   backend runtime env:  KBOT_FAKE_PAYMENT=1
#   frontend BUILD arg:   NEXT_PUBLIC_KBOT_FAKE_PAYMENT=1  (NEXT_PUBLIC_* = build-time)
#   + K2A_ENTITLEMENT_SECRET già presente (la generazione passa dall'entitlement vero).
#   La generazione vera del report consuma comunque crediti Anthropic.
# DEMO "tutto gratis senza prezzo": K2A_8E_ENTITLEMENT_DEV=true e KBOT_FREE_MODE=1.

# Run as a non-root user (node:20-slim ships with the "node" user, uid 1000).
# Tutto sotto /app è read-only a runtime (upload → Supabase storage + /tmp).
RUN chown -R node:node /app 2>/dev/null || true
USER node

EXPOSE 4173

CMD ["sh", "/app/entrypoint.sh"]
