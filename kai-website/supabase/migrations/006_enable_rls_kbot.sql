-- 006_enable_rls_kbot.sql
-- Source: kai-website-security-report.md / RLS-APPLY-PROCEDURE.md
--
-- Enable Row Level Security + deny-all on every kai-website public table.
-- All backend access uses SUPABASE_SERVICE_KEY which bypasses RLS by design,
-- so this migration does NOT break any current code path.
-- The anon / publishable key (NEXT_PUBLIC_SUPABASE_ANON_KEY) is never used to
-- read/write these tables today — but if it leaks (e.g. via a bundled SDK
-- snippet), this migration ensures it cannot read user PII or session data.
--
-- Verify after apply with:
--   select tablename, rowsecurity from pg_tables where schemaname='public';
--   → rowsecurity = t for every row.

begin;

-- ── Enable + force RLS ─────────────────────────────────────────────────────

alter table if exists public.kbot_sessions          enable row level security;
alter table if exists public.kbot_conversions       enable row level security;
alter table if exists public.newsletter_subscribers enable row level security;
alter table if exists public.newsletter_issues      enable row level security;

alter table if exists public.kbot_sessions          force row level security;
alter table if exists public.kbot_conversions       force row level security;
alter table if exists public.newsletter_subscribers force row level security;
alter table if exists public.newsletter_issues      force row level security;

-- ── Explicit deny-all for the `anon` role ──────────────────────────────────

do $$
declare
    tbl text;
    tables text[] := array[
        'kbot_sessions',
        'kbot_conversions',
        'newsletter_subscribers',
        'newsletter_issues'
    ];
begin
    foreach tbl in array tables loop
        execute format(
            'drop policy if exists %I on public.%I',
            'deny_anon_all_' || tbl,
            tbl
        );
        execute format(
            'create policy %I on public.%I as restrictive for all to anon using (false) with check (false)',
            'deny_anon_all_' || tbl,
            tbl
        );
    end loop;
end$$;

-- ── Revoke direct grants ───────────────────────────────────────────────────

revoke all on public.kbot_sessions          from anon;
revoke all on public.kbot_conversions       from anon;
revoke all on public.newsletter_subscribers from anon;
revoke all on public.newsletter_issues      from anon;

commit;

-- Rollback:
--   alter table public.<tbl> disable row level security;
--   drop policy deny_anon_all_<tbl> on public.<tbl>;
