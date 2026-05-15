#!/usr/bin/env bash
# backup-supabase.sh — pg_dump Supabase Postgres to local or S3-compatible storage.
#
# Required env (one of):
#   SUPABASE_DB_URL='postgresql://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres'
# or:
#   SUPABASE_PROJECT_REF=<ref>
#   SUPABASE_DB_PASSWORD=<pwd>
#
# Optional env:
#   BACKUP_TARGET=local           # local | s3 (default local)
#   BACKUP_DIR=./backups          # for local target
#   S3_BUCKET=...                 # for s3 target
#   S3_ENDPOINT=...               # e.g. https://<accountid>.r2.cloudflarestorage.com
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
#
# Rotation: keeps 14 daily + 8 weekly (Sunday) + 6 monthly (1st of month) copies.
#
# Exits 0 on success. Structured JSON log on stdout.

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────
BACKUP_TARGET="${BACKUP_TARGET:-local}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TS=$(date -u +%Y%m%dT%H%M%SZ)
DATE_ONLY=$(date -u +%Y-%m-%d)
DOW=$(date -u +%u)         # 1..7, 7=Sun
DOM=$(date -u +%d)         # 01..31

log() {
  # log <status> <message> [extra_json]
  local status="$1"; shift
  local msg="$1"; shift
  local extra="${1:-}"
  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if [[ -n "$extra" ]]; then
    printf '{"ts":"%s","script":"backup-supabase","status":"%s","msg":"%s",%s}\n' \
      "$ts" "$status" "$msg" "$extra"
  else
    printf '{"ts":"%s","script":"backup-supabase","status":"%s","msg":"%s"}\n' \
      "$ts" "$status" "$msg"
  fi
}

trap 'log error "unexpected failure on line $LINENO"' ERR

# ── Resolve DB URL ────────────────────────────────────────────────────────
if [[ -z "${SUPABASE_DB_URL:-}" ]]; then
  if [[ -z "${SUPABASE_PROJECT_REF:-}" || -z "${SUPABASE_DB_PASSWORD:-}" ]]; then
    log error "missing SUPABASE_DB_URL or (SUPABASE_PROJECT_REF + SUPABASE_DB_PASSWORD)"
    exit 1
  fi
  SUPABASE_DB_URL="postgresql://postgres:${SUPABASE_DB_PASSWORD}@db.${SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
fi

command -v pg_dump >/dev/null 2>&1 || { log error "pg_dump not installed"; exit 1; }
command -v gzip    >/dev/null 2>&1 || { log error "gzip not installed";   exit 1; }

# ── Dump ──────────────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"
OUT_FILE="$BACKUP_DIR/supabase-${TS}.sql.gz"

log info "starting pg_dump" "\"target\":\"$BACKUP_TARGET\",\"file\":\"$(basename "$OUT_FILE")\""

if ! pg_dump --no-owner --no-privileges --clean --if-exists \
     "$SUPABASE_DB_URL" 2>/tmp/pgdump.err | gzip -9 > "$OUT_FILE"; then
  log error "pg_dump failed" "\"detail\":\"$(tr -d '\n\"' </tmp/pgdump.err | head -c 200)\""
  rm -f "$OUT_FILE"
  exit 1
fi

SIZE=$(wc -c < "$OUT_FILE" | tr -d ' ')
if (( SIZE < 1024 )); then
  log error "dump suspiciously small" "\"size\":$SIZE"
  exit 1
fi

# ── Upload (if S3) ────────────────────────────────────────────────────────
if [[ "$BACKUP_TARGET" == "s3" ]]; then
  command -v aws >/dev/null 2>&1 || { log error "aws cli not installed"; exit 1; }
  [[ -z "${S3_BUCKET:-}" ]] && { log error "S3_BUCKET not set"; exit 1; }

  s3_args=(s3 cp "$OUT_FILE" "s3://${S3_BUCKET}/supabase/$(basename "$OUT_FILE")")
  [[ -n "${S3_ENDPOINT:-}" ]] && s3_args=(--endpoint-url "$S3_ENDPOINT" "${s3_args[@]}")

  if ! aws "${s3_args[@]}" >/dev/null 2>/tmp/awsput.err; then
    log error "s3 upload failed" "\"detail\":\"$(tr -d '\n\"' </tmp/awsput.err | head -c 200)\""
    exit 1
  fi
fi

# ── Tag for rotation ──────────────────────────────────────────────────────
# Symlink so weekly/monthly retention is decoupled from filename.
ln -sf "$(basename "$OUT_FILE")" "$BACKUP_DIR/daily-${DATE_ONLY}.sql.gz"
if [[ "$DOW" == "7" ]]; then
  ln -sf "$(basename "$OUT_FILE")" "$BACKUP_DIR/weekly-${DATE_ONLY}.sql.gz"
fi
if [[ "$DOM" == "01" ]]; then
  ln -sf "$(basename "$OUT_FILE")" "$BACKUP_DIR/monthly-${DATE_ONLY}.sql.gz"
fi

# ── Rotation ──────────────────────────────────────────────────────────────
# Delete daily-* older than 14d, weekly-* older than 56d, monthly-* older than 186d.
# Use mtime as proxy (created during this run = fresh).
rotate() {
  local pattern="$1" days="$2"
  find "$BACKUP_DIR" -maxdepth 1 -name "$pattern" -type l -mtime "+${days}" -print0 2>/dev/null |
    while IFS= read -r -d '' link; do
      target=$(readlink "$link" || true)
      rm -f "$link"
      # remove the underlying dump only if no other symlink references it
      if [[ -n "$target" ]]; then
        if ! find "$BACKUP_DIR" -maxdepth 1 -type l -lname "$target" -print -quit | grep -q .; then
          rm -f "$BACKUP_DIR/$target"
        fi
      fi
    done
}

rotate 'daily-*.sql.gz'   14
rotate 'weekly-*.sql.gz'  56
rotate 'monthly-*.sql.gz' 186

# Garbage-collect orphan dumps (no symlink) older than 14d as defense-in-depth.
find "$BACKUP_DIR" -maxdepth 1 -name 'supabase-*.sql.gz' -type f -mtime +14 -print0 2>/dev/null |
  while IFS= read -r -d '' f; do
    base=$(basename "$f")
    if ! find "$BACKUP_DIR" -maxdepth 1 -type l -lname "$base" -print -quit | grep -q .; then
      rm -f "$f"
    fi
  done

log ok "backup complete" "\"size\":${SIZE},\"target\":\"$BACKUP_TARGET\",\"file\":\"$(basename "$OUT_FILE")\""
