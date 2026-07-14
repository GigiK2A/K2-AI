#!/usr/bin/env sh
# Entrypoint del sito K2-AI su Railway. Avvia server.js (frontend + backend K-BOT
# python + motore 8e bundled). Se TS_AUTHKEY è impostata, collega il container alla
# tailnet (Tailscale userspace, non-root) così le chiamate al MODELLO LLM locale
# (ANTHROPIC_BASE_URL su IP 100.x del PC) passano via tailnet invece del quick tunnel
# Cloudflare (effimero, rate-limited). Il proxy HTTP :1055 vale SOLO per gli host NON
# in NO_PROXY: i servizi pubblici (Supabase/Stripe/OpenAI/Resend/PostHog/GitHub/API
# Anthropic) restano DIRETTI; solo l'endpoint LLM sull'IP tailnet passa dal proxy.
# Un fallimento di Tailscale NON blocca l'avvio. Senza TS_AUTHKEY: identico a prima.
if [ -n "${TS_AUTHKEY:-}" ]; then
  echo "[entrypoint] Tailscale: avvio tailscaled (userspace)…"
  mkdir -p /tmp/tailscale
  tailscaled --tun=userspace-networking \
             --outbound-http-proxy-listen=localhost:1055 \
             --socket=/tmp/tailscale/tailscaled.sock \
             --statedir=/tmp/tailscale >/tmp/tailscale/tailscaled.log 2>&1 &
  for _ in $(seq 1 20); do [ -S /tmp/tailscale/tailscaled.sock ] && break; sleep 1; done
  if tailscale --socket=/tmp/tailscale/tailscaled.sock up \
       --authkey="${TS_AUTHKEY}" \
       --hostname="${TS_HOSTNAME:-k2-website}" \
       --accept-routes; then
    # Solo l'IP tailnet del modello passa dal proxy; tutto il resto DIRETTO.
    _np="localhost,127.0.0.1,::1,.supabase.co,api.openai.com,.openai.com,api.stripe.com,.stripe.com,api.resend.com,.resend.com,.posthog.com,i.posthog.com,eu.i.posthog.com,github.com,.githubusercontent.com,api.anthropic.com"
    export HTTP_PROXY="http://localhost:1055" HTTPS_PROXY="http://localhost:1055" ALL_PROXY="http://localhost:1055"
    export http_proxy="http://localhost:1055" https_proxy="http://localhost:1055" all_proxy="http://localhost:1055"
    export NO_PROXY="$_np" no_proxy="$_np"
    echo "[entrypoint] Tailscale connesso (${TS_HOSTNAME:-k2-website}); LLM locale via tailnet, servizi pubblici diretti"
  else
    echo "[entrypoint] ATTENZIONE: Tailscale non connesso — avvio comunque (LLM via configurazione esistente)"
  fi
fi
exec node server.js
