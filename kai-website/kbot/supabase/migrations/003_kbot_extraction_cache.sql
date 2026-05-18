-- K-BOT extraction cache.
-- Caches the result of PDF/text/vision extraction keyed by sha256 of raw file
-- bytes. Saves 20-60s on re-uploads of the same document (very common when
-- the same bilancio is uploaded across multiple sessions).
--
-- TTL is informal: a separate Supabase scheduled job (or manual cron) can
-- prune rows with created_at < now() - interval '30 days'.
--
-- Apply with: psql ... -f migrations/20260518_kbot_extraction_cache.sql
create table if not exists public.kbot_extraction_cache (
    hash             text primary key,
    extracted_text   text,
    extracted_summary text,
    extraction_method text not null,
    pages_json       jsonb,
    bytes_size       bigint,
    mime             text,
    created_at       timestamptz not null default now()
);

create index if not exists kbot_extraction_cache_created_at_idx
    on public.kbot_extraction_cache (created_at);

-- Service-role only; never expose via PostgREST anon.
alter table public.kbot_extraction_cache enable row level security;
-- No policies = locked down. Only service_role bypasses RLS.

comment on table public.kbot_extraction_cache is
    'Hash-keyed cache of file extraction results. Used by app/api/upload.py.';
comment on column public.kbot_extraction_cache.hash is
    'sha256(raw bytes) of the uploaded file, hex string.';
