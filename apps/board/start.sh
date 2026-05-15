#!/bin/sh
# Boot the FastAPI backend (internal) and the Next.js standalone server (public).
# Next.js runs as PID 1 — it must terminate to end the container. We forward
# SIGTERM/SIGINT to uvicorn so Railway shutdowns stop cleanly.
set -e

: "${PORT:=3000}"

# Start FastAPI in background, bound to loopback only.
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning &
API_PID=$!

# Give uvicorn a moment to bind before Next.js starts proxying to it.
sleep 2

cleanup() {
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT

# Next.js standalone server (foreground).
cd /app/web
exec node server.js
