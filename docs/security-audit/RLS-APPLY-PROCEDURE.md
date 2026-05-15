# RLS Apply Procedure — K2-AI Supabase

Status: **manual apply required** (Supabase CLI is installed but not authenticated in this environment).

## Migrations to apply

| Project       | File                                                            | Purpose                                                       |
| ------------- | --------------------------------------------------------------- | ------------------------------------------------------------- |
| ai-board      | `ai-board/db/migrations/005_enable_rls.sql`                     | Enable RLS + deny-all on every ai-board table (C-2)           |
| kai-website   | `kai-website/supabase/migrations/006_enable_rls_kbot.sql`       | Enable RLS + deny-all on `kbot_sessions`, `kbot_conversions`, `newsletter_subscribers`, `newsletter_issues` |

Both Supabase projects use the **service-role key** server-side. Service role bypasses RLS by design, so backend code keeps working unchanged. RLS is the safety net for the `anon` / `authenticated` API keys.

## Option A — apply via Supabase Dashboard (recommended, no auth setup)

1. Open Supabase dashboard → select project.
2. **SQL Editor** → **New query**.
3. Paste the full content of the migration file (above).
4. Run.
5. Go to **Database → Tables**: every listed table should now show the small shield icon = RLS on.
6. Run the verification query below.

Repeat for the second project (kai-website Supabase, if it is a separate project — confirm with Luca before running).

## Option B — apply via CLI (requires interactive `supabase login`)

```bash
# one-time, opens browser:
supabase login

# from ai-board/:
cd ai-board
supabase link --project-ref <PROJECT_REF>
supabase db push   # applies any unapplied migrations in db/migrations/

# from kai-website/:
cd ../kai-website
supabase link --project-ref <PROJECT_REF>
supabase db push
```

## Verification query

Run this in the SQL editor (or via `psql`) **after applying**. It must return one row per protected table, all with `rowsecurity = t`.

```sql
-- 1. RLS enabled on every protected table
select
  schemaname,
  tablename,
  rowsecurity as rls_on,
  forcerowsecurity as force_rls
from pg_tables
where schemaname = 'public'
  and tablename in (
    -- ai-board
    'tasks','agent_logs','agent_logs_archive','approvals','pipeline_leads',
    'shared_memory','projects','project_phases','project_tasks',
    'project_documents','project_agent_links','board_users','board_sessions',
    -- kai-website
    'kbot_sessions','kbot_conversions','newsletter_subscribers','newsletter_issues'
  )
order by tablename;

-- 2. deny-all policies are present
select tablename, policyname, roles, cmd, permissive
from pg_policies
where schemaname='public'
  and policyname like 'deny_anon_all_%'
order by tablename;

-- 3. attempt as anon (should return 0 rows for every table)
set role anon;
select count(*) as anon_can_see_tasks from public.tasks;          -- expect: 0 or permission denied
select count(*) as anon_can_see_kbot from public.kbot_sessions;   -- expect: 0 or permission denied
reset role;
```

If any table is missing from result 1, the migration did not run — re-paste the SQL. If `rls_on` is `f`, the `alter table ... enable row level security` failed silently (likely table doesn't exist yet — create it first via earlier migrations).

## Verification script (CI-friendly)

`scripts/verify-rls.sh` (added in this commit) runs the same checks via `psql` against a Supabase connection string. Usage:

```bash
SUPABASE_DB_URL='postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres' \
  ./scripts/verify-rls.sh
```

Exit code 0 means every protected table has RLS on. Non-zero means a violation was found — see stderr for the list.

## Rollback

```sql
-- per table:
alter table public.<tbl> disable row level security;
drop policy if exists deny_anon_all_<tbl> on public.<tbl>;
```

Do not roll back unless you're actively debugging a client that needs anon access — RLS is the difference between "leaked anon key = read-only metadata" and "leaked anon key = full DB dump".
