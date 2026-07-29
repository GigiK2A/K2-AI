#!/usr/bin/env bash
# verify-rls.sh — verify Supabase RLS is enabled on protected tables.
#
# Usage:
#   SUPABASE_DB_URL='postgresql://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres' \
#     ./scripts/verify-rls.sh
#
# Exit code 0 if every protected table has rowsecurity=true.
# Exit code 1 on any violation (or missing psql / missing DB URL).

set -euo pipefail

if [[ -z "${SUPABASE_DB_URL:-}" ]]; then
  echo '{"status":"error","reason":"SUPABASE_DB_URL env var required"}' >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo '{"status":"error","reason":"psql not installed"}' >&2
  exit 1
fi

# Tables to check (union of board AIOS + kai-website). Le tabelle legacy del
# vecchio ai-board (tasks/agent_logs/approvals) esistono ancora e restano
# protette da RLS anche se non più scritte da nessuno.
PROTECTED_TABLES=(
  tasks agent_logs agent_logs_archive approvals pipeline_leads shared_memory
  projects project_phases project_tasks project_documents project_agent_links
  board_users board_sessions
  kbot_sessions kbot_conversions newsletter_subscribers newsletter_issues
)

IFS=',' read -r -a _ <<< ""
TABLE_LIST=$(printf "'%s'," "${PROTECTED_TABLES[@]}")
TABLE_LIST=${TABLE_LIST%,}

SQL=$(cat <<EOF
select tablename, rowsecurity::text
from pg_tables
where schemaname='public'
  and tablename in (${TABLE_LIST});
EOF
)

ROWS=$(psql "$SUPABASE_DB_URL" -At -F'|' -c "$SQL" 2>/dev/null || true)

if [[ -z "$ROWS" ]]; then
  echo '{"status":"error","reason":"no rows returned (connection/permission issue or no tables exist)"}' >&2
  exit 1
fi

violations=()
checked=0
while IFS='|' read -r tbl rls; do
  [[ -z "$tbl" ]] && continue
  checked=$((checked+1))
  if [[ "$rls" != "t" && "$rls" != "true" ]]; then
    violations+=("$tbl")
  fi
done <<< "$ROWS"

ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if (( ${#violations[@]} == 0 )); then
  printf '{"ts":"%s","status":"ok","tables_checked":%d}\n' "$ts" "$checked"
  exit 0
else
  printf '{"ts":"%s","status":"fail","tables_checked":%d,"violations":[' "$ts" "$checked"
  printf '"%s",' "${violations[@]}" | sed 's/,$//'
  printf ']}\n'
  exit 1
fi
