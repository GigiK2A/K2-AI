# K2-AI — Backup & Restore Procedure

Owner: Luca (rluigiluca@gmail.com).
Last review: 2026-05-15.

## What gets backed up

| Source                          | Tool                          | Frequency                | Off-site target            |
| ------------------------------- | ----------------------------- | ------------------------ | -------------------------- |
| Supabase Postgres (ai-board)    | `scripts/backup-supabase.sh`  | daily 03:00 UTC          | Cloudflare R2 / S3         |
| Supabase Postgres (kai-website) | `scripts/backup-supabase.sh`  | daily 03:00 UTC          | Cloudflare R2 / S3         |
| Notion workspace                | `scripts/backup-notion.sh`    | daily 04:00 UTC          | Cloudflare R2 / S3         |
| Supabase Storage buckets        | manual `supabase storage cp`  | weekly (Sunday)          | Cloudflare R2 / S3         |
| Code                            | GitHub                        | continuous (every push)  | GitHub default             |
| Stripe data                     | Stripe Dashboard exports      | not needed (Stripe is SoR) | n/a                      |

> **RPO target**: 24h. **RTO target**: 4h.
> This is appropriate for a PMI-targeted SaaS at our scale. Anything tighter would
> require multi-region active-active and is not in scope.

## Storage layout

Recommended off-site target: **Cloudflare R2** (no egress fees, S3-compatible API).
Fallback: AWS S3 in `eu-central-1` (Frankfurt) to keep EU residency.

Bucket structure:

```
s3://k2ai-backups/
├── supabase/        ← supabase-YYYYMMDDTHHMMSSZ.sql.gz
└── notion/          ← notion-YYYYMMDDTHHMMSSZ.tar.gz
```

Set object-level retention / versioning at the bucket level so a compromised
backup script cannot wipe history.

## Retention

`backup-supabase.sh` maintains, automatically:

- **14 daily** snapshots
- **8 weekly** snapshots (every Sunday)
- **6 monthly** snapshots (1st of month)

`backup-notion.sh` keeps last 30 backups (Notion data is comparatively small).

## Schedule (cron)

Add to a stable host (Railway cron job, GitHub Action, or your laptop):

```cron
# Supabase (ai-board)
0 3 * * *  cd /path/to/K-AI && \
  SUPABASE_DB_URL=$AIBOARD_DB_URL BACKUP_TARGET=s3 \
  S3_BUCKET=k2ai-backups S3_ENDPOINT=$R2_ENDPOINT \
  ./scripts/backup-supabase.sh >> ./logs/backup.log 2>&1

# Supabase (kai-website)
15 3 * * * cd /path/to/K-AI && \
  SUPABASE_DB_URL=$KAIWEBSITE_DB_URL BACKUP_TARGET=s3 \
  S3_BUCKET=k2ai-backups S3_ENDPOINT=$R2_ENDPOINT \
  ./scripts/backup-supabase.sh >> ./logs/backup.log 2>&1

# Notion
0 4 * * *  cd /path/to/K-AI && \
  NOTION_TOKEN=$NOTION_TOKEN BACKUP_TARGET=s3 \
  S3_BUCKET=k2ai-backups S3_ENDPOINT=$R2_ENDPOINT \
  ./scripts/backup-notion.sh >> ./logs/backup.log 2>&1
```

For Railway, use the `cron` plugin or a separate "backup" service with `command = scripts/backup-supabase.sh` and `schedule = "0 3 * * *"`.

## Restore — Supabase Postgres

1. Download the desired snapshot:
   ```bash
   aws s3 cp s3://k2ai-backups/supabase/supabase-YYYYMMDDTHHMMSSZ.sql.gz . \
     --endpoint-url $R2_ENDPOINT
   gunzip supabase-*.sql.gz
   ```
2. Restore against a **fresh** Supabase project (do NOT restore over production
   without staging first):
   ```bash
   psql 'postgresql://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres' \
     < supabase-YYYYMMDDTHHMMSSZ.sql
   ```
   The `--clean --if-exists` flags in the dump script mean the restore drops
   existing objects before recreating them — only do this on a target you
   intend to overwrite.
3. Re-apply RLS migrations (`005_enable_rls.sql`, `006_enable_rls_kbot.sql`).
4. Update app env vars to point at the new project.

## Restore — Notion

Notion has no native bulk-import. Restore is a recovery archive, not a
re-applicable migration:

1. Download the tar.gz, extract.
2. For each `*.pages.jsonl`, write a small script that calls
   `POST /v1/pages` for each row, re-creating pages in a fresh database with
   the schema from `*.schema.json`.
3. For an emergency partial recovery, the JSON is human-readable — `jq` it.

## Quarterly restore test

Every quarter (Mar / Jun / Sep / Dec), Luca runs the **restore drill**:

1. Spin up a free-tier Supabase project (`k2ai-restore-drill`).
2. Restore the latest Supabase backup against it.
3. Run `scripts/verify-rls.sh` against the restored DB.
4. Manually check a sample query (`select count(*) from kbot_sessions;`).
5. Tear down the drill project.
6. Note pass/fail in `docs/security-audit/RESTORE-DRILLS.md`.

A restore that has never been tested is a 50/50 coin flip. Test it.

## Local dry run

```bash
# Default target = local, dumps into ./backups/
SUPABASE_DB_URL='postgresql://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres' \
  ./scripts/backup-supabase.sh
```

Verify the output JSON line has `"status":"ok"` and inspect the file:

```bash
ls -la backups/
gunzip -c backups/supabase-*.sql.gz | head -50
```
