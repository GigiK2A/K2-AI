#!/usr/bin/env bash
# Genera i segreti per la produzione (entitlement + API key 8e).
# Settare gli STESSI valori su K-BOT backend e 8e (env Railway).
set -euo pipefail

echo "# === Segreti K2A 8e (settare su Railway, IDENTICI sui due servizi) ==="
echo "K2A_ENTITLEMENT_SECRET=$(openssl rand -base64 48 | tr -d '\n')"
echo "K2A_8E_API_KEY=$(openssl rand -hex 32)"
echo
echo "# 8e (env): K2A_ENTITLEMENT_SECRET, K2A_8E_API_KEY, ANTHROPIC_API_KEY"
echo "# K-BOT backend (env): K2A_ENTITLEMENT_SECRET (stesso), K2A_8E_API_KEY (stesso),"
echo "#                      K2A_8E_BASE_URL=https://<8e-railway-url>"
