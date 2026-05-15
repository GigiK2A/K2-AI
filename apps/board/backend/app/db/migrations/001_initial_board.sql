-- 001_initial_board.sql
-- K2-Board Sprint 1 — initial schema.
-- Single source of truth: Supabase Postgres (Frankfurt).
-- Replaces the multi-store (Supabase + Notion) layout used by the old ai-board/.
--
-- Apply via Supabase dashboard SQL editor (Project → SQL → New query) OR `supabase db push`.
-- Idempotent: safe to re-run.
--
-- Verification:
--   select tablename, rowsecurity from pg_tables where schemaname='public'
--     and tablename in ('contacts','leads','tasks','approvals','memos','meetings','revenue_events');
--   → rowsecurity must be `t` for every row.
--
--   select tablename, policyname from pg_policies where schemaname='public';
--   → each table must have a `deny_anon_all_<table>` policy.

begin;

-- ── Extensions ─────────────────────────────────────────────────────────────

create extension if not exists pg_trgm;
create extension if not exists pgcrypto;  -- for gen_random_uuid()

-- ── Enums ──────────────────────────────────────────────────────────────────

do $$ begin
    create type lead_status as enum ('nuovo', 'contatto', 'proposta', 'chiuso_vinto', 'chiuso_perso');
exception when duplicate_object then null; end $$;

do $$ begin
    create type lead_source as enum ('k_bot', 'contact_form', 'newsletter', 'referral', 'outbound', 'other');
exception when duplicate_object then null; end $$;

do $$ begin
    create type task_priority as enum ('alta', 'media', 'bassa');
exception when duplicate_object then null; end $$;

do $$ begin
    create type task_status as enum ('todo', 'doing', 'done', 'cancelled');
exception when duplicate_object then null; end $$;

do $$ begin
    create type approval_kind as enum ('email', 'proposta', 'post', 'reply', 'altro');
exception when duplicate_object then null; end $$;

do $$ begin
    create type approval_status as enum ('pending', 'approved', 'rejected', 'edited_and_sent');
exception when duplicate_object then null; end $$;

-- ── Tables ─────────────────────────────────────────────────────────────────

-- contacts: anagrafica persone/aziende
create table if not exists contacts (
    id uuid primary key default gen_random_uuid(),
    company text,
    person_name text,
    email text,
    phone text,
    notes text,
    tags text[] not null default array[]::text[],
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create unique index if not exists ix_contacts_email_lower
    on contacts (lower(email)) where email is not null;

-- leads: pipeline commerciale
create table if not exists leads (
    id uuid primary key default gen_random_uuid(),
    contact_id uuid references contacts(id) on delete set null,
    title text not null,
    description text,
    status lead_status not null default 'nuovo',
    source lead_source not null default 'other',
    value_eur numeric(12,2),
    probability int default 50 check (probability between 0 and 100),
    next_action_at timestamptz,
    next_action_note text,
    kbot_session_id uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    closed_at timestamptz
);
create index if not exists ix_leads_status on leads (status);
create index if not exists ix_leads_next_action
    on leads (next_action_at)
    where next_action_at is not null and status not in ('chiuso_vinto', 'chiuso_perso');

-- tasks: todo Luigi (collegabili a lead o standalone)
create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    lead_id uuid references leads(id) on delete set null,
    title text not null,
    notes text,
    priority task_priority not null default 'media',
    status task_status not null default 'todo',
    due_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    position int not null default 0
);
create index if not exists ix_tasks_status_due on tasks (status, due_at);

-- approvals: draft generati da AI che Luigi approva
create table if not exists approvals (
    id uuid primary key default gen_random_uuid(),
    kind approval_kind not null,
    title text not null,
    body text not null,
    rationale text,
    lead_id uuid references leads(id) on delete set null,
    contact_id uuid references contacts(id) on delete set null,
    status approval_status not null default 'pending',
    decision_note text,
    created_at timestamptz not null default now(),
    decided_at timestamptz
);
create index if not exists ix_approvals_status on approvals (status, created_at desc);

-- memos: memoria persistente fact-based
create table if not exists memos (
    id uuid primary key default gen_random_uuid(),
    subject text not null,
    body text not null,
    tags text[] not null default array[]::text[],
    contact_id uuid references contacts(id) on delete set null,
    lead_id uuid references leads(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists ix_memos_subject_trgm on memos using gin (subject gin_trgm_ops);
create index if not exists ix_memos_tags on memos using gin (tags);

-- meetings: sync Google Calendar (read-mostly)
create table if not exists meetings (
    id uuid primary key default gen_random_uuid(),
    external_id text unique,
    title text not null,
    description text,
    starts_at timestamptz not null,
    ends_at timestamptz not null,
    location text,
    meet_link text,
    attendees jsonb not null default '[]'::jsonb,
    contact_id uuid references contacts(id) on delete set null,
    lead_id uuid references leads(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists ix_meetings_starts on meetings (starts_at);

-- revenue_events: sync Stripe (read-mostly)
create table if not exists revenue_events (
    id uuid primary key default gen_random_uuid(),
    external_id text unique not null,
    customer_email text,
    customer_id text,
    amount_cents int not null,
    currency text not null default 'eur',
    description text,
    status text not null,
    occurred_at timestamptz not null,
    lead_id uuid references leads(id) on delete set null,
    raw jsonb,
    created_at timestamptz not null default now()
);
create index if not exists ix_revenue_status_date on revenue_events (status, occurred_at desc);

-- ── RLS: enable + force + deny-all-anon (pattern from old 005_enable_rls.sql) ──

alter table contacts        enable row level security;
alter table leads           enable row level security;
alter table tasks           enable row level security;
alter table approvals       enable row level security;
alter table memos           enable row level security;
alter table meetings        enable row level security;
alter table revenue_events  enable row level security;

alter table contacts        force row level security;
alter table leads           force row level security;
alter table tasks           force row level security;
alter table approvals       force row level security;
alter table memos           force row level security;
alter table meetings        force row level security;
alter table revenue_events  force row level security;

do $$
declare
    tbl text;
    tables text[] := array[
        'contacts', 'leads', 'tasks', 'approvals',
        'memos', 'meetings', 'revenue_events'
    ];
begin
    foreach tbl in array tables loop
        execute format(
            'drop policy if exists %I on public.%I',
            'deny_anon_all_' || tbl, tbl
        );
        execute format(
            'create policy %I on public.%I as restrictive for all to anon using (false) with check (false)',
            'deny_anon_all_' || tbl, tbl
        );
    end loop;
end$$;

revoke all on public.contacts       from anon;
revoke all on public.leads          from anon;
revoke all on public.tasks          from anon;
revoke all on public.approvals      from anon;
revoke all on public.memos          from anon;
revoke all on public.meetings       from anon;
revoke all on public.revenue_events from anon;

-- ── updated_at auto-bump trigger ───────────────────────────────────────────

create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

do $$
declare
    tbl text;
    tables text[] := array['contacts', 'leads', 'tasks', 'memos', 'meetings'];
begin
    foreach tbl in array tables loop
        execute format('drop trigger if exists set_updated_at on public.%I', tbl);
        execute format(
            'create trigger set_updated_at before update on public.%I '
            'for each row execute function public.set_updated_at()',
            tbl
        );
    end loop;
end$$;

commit;
