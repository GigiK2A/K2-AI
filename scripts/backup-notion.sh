#!/usr/bin/env bash
# backup-notion.sh — export Notion databases as JSON dump (queries via Notion API).
#
# Required env:
#   NOTION_TOKEN              # Internal integration secret (secret_...)
#
# Optional env:
#   NOTION_DATABASE_IDS       # comma-separated list of DB UUIDs to back up.
#                             # If empty, the script calls /v1/search and dumps
#                             # every database the integration has access to.
#   BACKUP_DIR=./backups/notion
#   BACKUP_TARGET=local       # local | s3
#   S3_BUCKET / S3_ENDPOINT / AWS_* — same as backup-supabase.sh
#
# Output: one JSON file per database + a metadata index, all gzipped together.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups/notion}"
BACKUP_TARGET="${BACKUP_TARGET:-local}"
TS=$(date -u +%Y%m%dT%H%M%SZ)
NOTION_VER="2022-06-28"

log() {
  local status="$1"; shift; local msg="$1"; shift; local extra="${1:-}"
  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if [[ -n "$extra" ]]; then
    printf '{"ts":"%s","script":"backup-notion","status":"%s","msg":"%s",%s}\n' "$ts" "$status" "$msg" "$extra"
  else
    printf '{"ts":"%s","script":"backup-notion","status":"%s","msg":"%s"}\n' "$ts" "$status" "$msg"
  fi
}

trap 'log error "unexpected failure on line $LINENO"' ERR

[[ -z "${NOTION_TOKEN:-}" ]] && { log error "NOTION_TOKEN env required"; exit 1; }
command -v curl >/dev/null 2>&1 || { log error "curl not installed"; exit 1; }
command -v jq   >/dev/null 2>&1 || { log error "jq not installed";   exit 1; }
command -v tar  >/dev/null 2>&1 || { log error "tar not installed";  exit 1; }

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

api() {
  # api <METHOD> <PATH> [JSON_BODY]
  local method="$1" path="$2" body="${3:-}"
  local args=( -sS -X "$method"
    -H "Authorization: Bearer $NOTION_TOKEN"
    -H "Notion-Version: $NOTION_VER"
    -H "Content-Type: application/json" )
  if [[ -n "$body" ]]; then args+=( -d "$body" ); fi
  curl "${args[@]}" "https://api.notion.com/v1${path}"
}

# ── Resolve DB list ───────────────────────────────────────────────────────
mkdir -p "$WORKDIR/dbs"
if [[ -n "${NOTION_DATABASE_IDS:-}" ]]; then
  IFS=',' read -r -a DBIDS <<< "$NOTION_DATABASE_IDS"
else
  search=$(api POST /search '{"filter":{"property":"object","value":"database"},"page_size":100}')
  mapfile -t DBIDS < <(echo "$search" | jq -r '.results[].id')
fi

if (( ${#DBIDS[@]} == 0 )); then
  log error "no databases found"; exit 1
fi

total=0
for db in "${DBIDS[@]}"; do
  [[ -z "$db" ]] && continue
  schema=$(api GET "/databases/$db")
  echo "$schema" > "$WORKDIR/dbs/${db}.schema.json"

  pages_file="$WORKDIR/dbs/${db}.pages.jsonl"
  : > "$pages_file"
  cursor=""
  while :; do
    body='{"page_size":100'
    [[ -n "$cursor" ]] && body="${body},\"start_cursor\":\"$cursor\""
    body="${body}}"
    resp=$(api POST "/databases/$db/query" "$body")
    echo "$resp" | jq -c '.results[]' >> "$pages_file" || true
    has_more=$(echo "$resp" | jq -r '.has_more // false')
    cursor=$(echo "$resp" | jq -r '.next_cursor // empty')
    [[ "$has_more" != "true" || -z "$cursor" ]] && break
  done
  count=$(wc -l < "$pages_file" | tr -d ' ')
  total=$((total + count))
done

# ── Index + archive ───────────────────────────────────────────────────────
jq -n --arg ts "$TS" --argjson count "$total" --argjson dbs "$(printf '%s\n' "${DBIDS[@]}" | jq -R . | jq -s .)" \
  '{ts:$ts, databases:$dbs, total_pages:$count}' > "$WORKDIR/index.json"

mkdir -p "$BACKUP_DIR"
OUT_FILE="$BACKUP_DIR/notion-${TS}.tar.gz"
tar -czf "$OUT_FILE" -C "$WORKDIR" .

SIZE=$(wc -c < "$OUT_FILE" | tr -d ' ')

# ── Upload (if S3) ────────────────────────────────────────────────────────
if [[ "$BACKUP_TARGET" == "s3" ]]; then
  command -v aws >/dev/null 2>&1 || { log error "aws cli not installed"; exit 1; }
  [[ -z "${S3_BUCKET:-}" ]] && { log error "S3_BUCKET not set"; exit 1; }
  s3_args=(s3 cp "$OUT_FILE" "s3://${S3_BUCKET}/notion/$(basename "$OUT_FILE")")
  [[ -n "${S3_ENDPOINT:-}" ]] && s3_args=(--endpoint-url "$S3_ENDPOINT" "${s3_args[@]}")
  aws "${s3_args[@]}" >/dev/null
fi

# ── Rotation: keep last 30 backups ────────────────────────────────────────
ls -1t "$BACKUP_DIR"/notion-*.tar.gz 2>/dev/null | tail -n +31 | xargs -r rm -f

log ok "notion backup complete" "\"size\":${SIZE},\"pages\":${total},\"dbs\":${#DBIDS[@]},\"file\":\"$(basename "$OUT_FILE")\""
