-- Sprint 9C — Email triage stub provider.
--
-- Holds inbound emails staged manually (or imported via Gmail) until
-- Giuseppina has classified them. Service-role only; anon blocked.
--
-- VERIFY AFTER APPLYING:
--   select tablename, rowsecurity from pg_tables
--     where schemaname = 'public' and tablename = 'board_inbox_pending';
--   → rowsecurity must be `t`.

begin;

create table if not exists board_inbox_pending (
    id uuid primary key default gen_random_uuid(),
    from_email text not null,
    from_name text,
    subject text not null,
    body text not null,
    received_at timestamptz not null default now(),
    triaged_at timestamptz,
    triage_result jsonb,
    created_at timestamptz not null default now()
);

create index if not exists ix_inbox_pending_received
    on board_inbox_pending (received_at desc);
create index if not exists ix_inbox_pending_untriaged
    on board_inbox_pending (triaged_at)
    where triaged_at is null;

alter table board_inbox_pending enable row level security;
alter table board_inbox_pending force row level security;

drop policy if exists deny_anon_all_board_inbox_pending on board_inbox_pending;
create policy deny_anon_all_board_inbox_pending
    on board_inbox_pending
    for all
    to anon
    using (false)
    with check (false);

commit;
