#!/usr/bin/env sh
# Entrypoint del board su Railway.
# Se TS_AUTHKEY è impostata → collega il container alla tailnet (Tailscale userspace,
# senza privilegi/TUN) così può raggiungere l'Ollama sul GB10 su IP privato 100.x.
# Se NON è impostata → parte l'app e basta: comportamento IDENTICO a prima (safe).
# Un fallimento di Tailscale NON blocca l'app: parte comunque (se il backend è 'local'
# le chiamate LLM degradano finché la tailnet non è su — opzione A).

if [ -n "${TS_AUTHKEY:-}" ]; then
  echo "[entrypoint] Tailscale: avvio tailscaled (userspace)…"
  mkdir -p /tmp/tailscale
  # userspace-networking = niente root/TUN (compatibile coi container Railway).
  # Socket e stato in /tmp: scrivibili dall'utente non-root (il default /run/tailscale NO).
  # Proxy HTTP su :1055 che instrada verso la tailnet → AIOS_LOCAL_PROXY.
  tailscaled --tun=userspace-networking \
             --socks5-server=localhost:1055 \
             --outbound-http-proxy-listen=localhost:1055 \
             --socket=/tmp/tailscale/tailscaled.sock \
             --statedir=/tmp/tailscale >/tmp/tailscale/tailscaled.log 2>&1 &
  # attende che il daemon crei il socket (max ~20s)
  for _ in $(seq 1 20); do [ -S /tmp/tailscale/tailscaled.sock ] && break; sleep 1; done
  if tailscale --socket=/tmp/tailscale/tailscaled.sock up \
       --authkey="${TS_AUTHKEY}" \
       --hostname="${TS_HOSTNAME:-k2-board}" \
       --accept-routes; then
    echo "[entrypoint] Tailscale connesso come ${TS_HOSTNAME:-k2-board}"
  else
    echo "[entrypoint] ATTENZIONE: Tailscale non connesso — l'app parte comunque"
  fi
fi

exec python serve_cockpit.py
