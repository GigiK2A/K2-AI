#!/usr/bin/env sh
# Avvio 8e + seed one-shot dei corpora sul volume (/corpus): normattiva + norme_tecniche.
# Il download gira in BACKGROUND: uvicorn parte subito (healthcheck /health ok), e i
# resolver rilevano il .db appena pronto (is_file()/open on-demand). Idempotente.
if [ -n "$NORMATTIVA_DB_URL" ] || [ -n "$NORME_DB_URL" ]; then
  echo "[seed] avvio download corpora in background (python/httpx)"
  python3 seed_corpus.py &
fi

# Tailscale (userspace): se TS_AUTHKEY è impostata, collega il container alla tailnet
# così le chiamate al modello raggiungono l'endpoint Anthropic-compatibile LOCALE
# (Ollama + shim) sul PC via IP privato 100.x — senza il cap ~100s del quick tunnel
# Cloudflare. Il proxy HTTP su :1055 viene passato SOLO al client Anthropic
# (K2A_8E_LLM_PROXY, vedi app/llm.py) → le altre uscite (OpenAI web search, storage)
# restano dirette. Un fallimento di Tailscale NON blocca l'avvio (fail-safe).
# Senza TS_AUTHKEY: comportamento IDENTICO a prima (dev locale, Claude reale).
if [ -n "${TS_AUTHKEY:-}" ]; then
  echo "[entrypoint] Tailscale: avvio tailscaled (userspace)…"
  mkdir -p /tmp/tailscale
  # userspace-networking = niente root/TUN (compatibile coi container Railway).
  # Socket e stato in /tmp (scrivibili da utente non-root). Proxy HTTP su :1055.
  tailscaled --tun=userspace-networking \
             --outbound-http-proxy-listen=localhost:1055 \
             --socket=/tmp/tailscale/tailscaled.sock \
             --statedir=/tmp/tailscale >/tmp/tailscale/tailscaled.log 2>&1 &
  # attende che il daemon crei il socket (max ~20s)
  for _ in $(seq 1 20); do [ -S /tmp/tailscale/tailscaled.sock ] && break; sleep 1; done
  if tailscale --socket=/tmp/tailscale/tailscaled.sock up \
       --authkey="${TS_AUTHKEY}" \
       --hostname="${TS_HOSTNAME:-k2-8e}" \
       --accept-routes; then
    echo "[entrypoint] Tailscale connesso come ${TS_HOSTNAME:-k2-8e}"
    # instrada SOLO le chiamate LLM attraverso la tailnet (vedi _anthropic_client)
    export K2A_8E_LLM_PROXY="${K2A_8E_LLM_PROXY:-http://localhost:1055}"
  else
    echo "[entrypoint] ATTENZIONE: Tailscale non connesso — avvio comunque (modello locale irraggiungibile finché la tailnet non è su)"
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8800}"
