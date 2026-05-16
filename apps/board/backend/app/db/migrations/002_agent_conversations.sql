-- Sprint 9A — Giuseppina agent conversations.
--
-- Stores chat history for the in-board Claude agent. Single-user board for
-- now (Luigi), but we keep the table user-agnostic so future multi-user is
-- a column add. RLS denies all anon access; service-role bypasses RLS.
--
-- VERIFY AFTER APPLYING:
--   select tablename, rowsecurity
--   from pg_tables
--   where schemaname = 'public' and tablename = 'board_agent_conversations';
--   → rowsecurity must be `t`.

begin;

create table if not exists board_agent_conversations (
    id uuid primary key default gen_random_uuid(),
    title text,
    messages jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists ix_agent_conv_updated
    on board_agent_conversations (updated_at desc);

alter table board_agent_conversations enable row level security;
alter table board_agent_conversations force row level security;

drop policy if exists deny_anon_all_board_agent_conversations
    on board_agent_conversations;
create policy deny_anon_all_board_agent_conversations
    on board_agent_conversations
    as restrictive for all
    to anon
    using (false)
    with check (false);

revoke all on board_agent_conversations from anon;

-- updated_at auto-bump (reuse trigger function from 001_initial_board.sql)
drop trigger if exists set_updated_at on public.board_agent_conversations;
create trigger set_updated_at
    before update on public.board_agent_conversations
    for each row execute function public.set_updated_at();

commit;
