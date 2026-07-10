#!/usr/bin/env sh
# Entrypoint del board su Railway.
# Se TS_AUTHKEY è impostata → collega il container alla tailnet (Tailscale userspace,
# senza privilegi/TUN) così può raggiungere l'Ollama sul GB10 su IP privato 100.x.
# Se NON è impostata → parte l'app e basta: comportamento IDENTICO a prima (safe).
set -e

if [ -n "${TS_AUTHKEY:-}" ]; then
  echo "[entrypoint] Tailscale: avvio tailscaled (userspace)…"
  # userspace-networking = niente root/TUN (compatibile con i container Railway).
  # Espone un proxy HTTP su :1055 che instrada verso la tailnet → AIOS_LOCAL_PROXY.
  tailscaled --tun=userspace-networking \
             --socks5-server=localhost:1055 \
             --outbound-http-proxy-listen=localhost:1055 \
             --statedir=/tmp/tailscale &
  # attende che il socket sia pronto
  for _ in $(seq 1 15); do [ -S /tmp/tailscale/tailscaled.sock ] && break; sleep 1; done
  tailscale --socket=/tmp/tailscale/tailscaled.sock up \
            --authkey="${TS_AUTHKEY}" \
            --hostname="${TS_HOSTNAME:-k2-board}" \
            --accept-routes
  echo "[entrypoint] Tailscale connesso come ${TS_HOSTNAME:-k2-board}"
fi

exec python serve_cockpit.py
