-- 005_enable_rls.sql
-- Source: ai-board-security-report.md C-2 (no RLS policies, service-role key bypasses everything).
--
-- Apply via:
--   supabase db push
-- or paste this whole file in Supabase SQL editor (Project → SQL → New query) and run.
--
-- Goal
--   1. Enable RLS on every table created by migrations 001–004.
--   2. Add an explicit DENY-ALL policy for the `anon` role on each table.
--      (Without an explicit policy, RLS already denies, but we make it explicit + auditable.)
--   3. Service-role key bypasses RLS by design (it's a Supabase platform behavior) — so
--      all current backend code that uses `get_service_client()` keeps working unchanged.
--   4. Where there is a future need for authenticated-user access from a client SDK using
--      the anon/publishable key + a Supabase Auth session, add narrower policies later.
--      For now NO client path uses anon — everything goes through server-side service key.
--
-- Verification after apply:
--   select schemaname, tablename, rowsecurity from pg_tables where schemaname='public';
--   → rowsecurity should be `t` for every row below.
--
--   select tablename, policyname, roles, cmd from pg_policies where schemaname='public';
--   → each table should have a `deny_anon_all_*` policy targeting {anon}.

begin;

-- ── Enable RLS on every known table ────────────────────────────────────────

alter table if exists public.tasks                enable row level security;
alter table if exists public.agent_logs           enable row level security;
alter table if exists public.agent_logs_archive   enable row level security;
alter table if exists public.approvals            enable row level security;
alter table if exists public.pipeline_leads       enable row level security;
alter table if exists public.shared_memory        enable row level security;
alter table if exists public.projects             enable row level security;
alter table if exists public.project_phases       enable row level security;
alter table if exists public.project_tasks        enable row level security;
alter table if exists public.project_documents    enable row level security;
alter table if exists public.project_agent_links  enable row level security;
alter table if exists public.board_users          enable row level security;
alter table if exists public.board_sessions       enable row level security;

-- Force RLS even for table owners (defense-in-depth — without this, the owning
-- Postgres role can still bypass policies via direct `psql`):

alter table if exists public.tasks                force row level security;
alter table if exists public.agent_logs           force row level security;
alter table if exists public.agent_logs_archive   force row level security;
alter table if exists public.approvals            force row level security;
alter table if exists public.pipeline_leads       force row level security;
alter table if exists public.shared_memory        force row level security;
alter table if exists public.projects             force row level security;
alter table if exists public.project_phases       force row level security;
alter table if exists public.project_tasks        force row level security;
alter table if exists public.project_documents    force row level security;
alter table if exists public.project_agent_links  force row level security;
alter table if exists public.board_users          force row level security;
alter table if exists public.board_sessions       force row level security;

-- ── Explicit deny-all policies for the `anon` role ─────────────────────────
-- The `anon` role is what Supabase uses when a client connects with the
-- publishable / anon API key without a JWT. We want zero access from there.
--
-- Note: with RLS enabled and NO permissive policy matching, access is already
-- denied. These restrictive policies make the intent explicit and survive any
-- accidental future `create policy ... for all to public using (true)`.

do $$
declare
    tbl text;
    tables text[] := array[
        'tasks',
        'agent_logs',
        'agent_logs_archive',
        'approvals',
        'pipeline_leads',
        'shared_memory',
        'projects',
        'project_phases',
        'project_tasks',
        'project_documents',
        'project_agent_links',
        'board_users',
        'board_sessions'
    ];
begin
    foreach tbl in array tables loop
        -- drop pre-existing policy with this name so the migration is idempotent
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

-- ── Revoke direct grants on `anon` for safety ─────────────────────────────
-- Supabase by default grants SELECT/INSERT/UPDATE/DELETE on public.* to the
-- `anon` and `authenticated` roles. RLS gates those grants, but revoking them
-- on tables that should never be touched by anon is a belt-and-braces step.

revoke all on public.tasks                from anon;
revoke all on public.agent_logs           from anon;
revoke all on public.agent_logs_archive   from anon;
revoke all on public.approvals            from anon;
revoke all on public.pipeline_leads       from anon;
revoke all on public.shared_memory        from anon;
revoke all on public.projects             from anon;
revoke all on public.project_phases       from anon;
revoke all on public.project_tasks        from anon;
revoke all on public.project_documents    from anon;
revoke all on public.project_agent_links  from anon;
revoke all on public.board_users          from anon;
revoke all on public.board_sessions       from anon;

commit;

-- Rollback (if needed):
--   alter table public.<each> disable row level security;
--   drop policy deny_anon_all_<each> on public.<each>;
