#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBSITE_DIR="$ROOT_DIR/kai-website"
SKIP_BUILD="${1:-}"

cd "$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "git non trovato nel PATH." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm non trovato nel PATH." >&2
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
  echo "Deploy bloccato: passa a 'main' prima di pubblicare il sito." >&2
  exit 1
fi

if [[ -n "$(git status --short)" ]]; then
  echo "Deploy bloccato: ci sono modifiche non committate o file non tracciati." >&2
  git status --short
  exit 1
fi

if [[ "$SKIP_BUILD" != "--skip-build" ]]; then
  echo "Eseguo la build locale di verifica..."
  (cd "$WEBSITE_DIR" && npm run build)
fi

echo "Pubblico via GitHub: push di main su origin."
git push origin main

cat <<'EOF'

Push completato.

Per il servizio Railway `k2-ai-website` usare il deploy Git-backed da `main`.
Evitare `railway up` su questo servizio: può fallire in modo intermittente
durante la risoluzione del root directory dello snapshot.
EOF
