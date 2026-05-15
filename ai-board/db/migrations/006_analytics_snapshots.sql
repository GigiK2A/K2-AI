-- 006_analytics_snapshots.sql
--
-- Stores hourly rollups computed by `agents/scheduler_tasks/posthog_sync.py`
-- from PostHog Cloud EU. The dashboard at /analytics reads the most recent
-- row from this table — never PostHog directly — so the page stays fast and
-- works even if PostHog is unreachable.
--
-- Apply via:
--   supabase db push
-- or paste in Supabase SQL editor and run.
--
-- After apply, verify:
--   select schemaname, tablename, rowsecurity from pg_tables
--     where schemaname='public' and tablename='analytics_snapshots';
--   → rowsecurity should be `t`.

create table if not exists analytics_snapshots (
    id           uuid primary key default gen_random_uuid(),
    ts           timestamptz not null default now(),
    -- Map of P01..P20 → click count in the rollup window.
    profile_stats jsonb not null default '{}'::jsonb,
    -- K-BOT funnel counts + conversion rates.
    kbot_funnel   jsonb not null default '{}'::jsonb,
    events_processed integer not null default 0,
    created_at   timestamptz not null default now()
);

create index if not exists idx_analytics_snapshots_ts
  on analytics_snapshots (ts desc);

-- RLS — mirror migrations/005: enable + deny-all for anon. The board uses
-- the service-role key (bypasses RLS) so the scheduler/dashboard keep working.
alter table analytics_snapshots enable row level security;

drop policy if exists analytics_snapshots_anon_deny on analytics_snapshots;
create policy analytics_snapshots_anon_deny
  on analytics_snapshots
  as restrictive
  for all
  to anon
  using (false)
  with check (false);
