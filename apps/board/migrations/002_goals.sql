-- AIOS · Primitiva #3 (Paperclip): goal ancestry — obiettivi con gerarchia.
--
-- "Context flows from the task up through the project and company goals."
-- Applicare una volta nel SQL editor di Supabase (schema out-of-band).
--
-- A differenza delle tabelle di billing, aios_goals è in ALLOWLIST: gli obiettivi
-- si creano/aggiornano col normale flusso propose→approva (li propone CEO/direttore).

-- Albero degli obiettivi: mission → strategico → progetto (self-FK parent_goal_id).
create table if not exists public.aios_goals (
    id             bigint generated always as identity primary key,
    title          text not null,
    description    text,
    parent_goal_id bigint references public.aios_goals(id) on delete set null,
    status         text not null default 'active',   -- active | done | paused
    priority       integer not null default 3,        -- 1 = più alta
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);
create index if not exists aios_goals_status_priority_idx
    on public.aios_goals (status, priority);
create index if not exists aios_goals_parent_idx
    on public.aios_goals (parent_goal_id);

-- Link ascendente opzionale: un task interno può tracciare l'obiettivo che serve.
alter table public.board_tasks
    add column if not exists goal_id bigint references public.aios_goals(id) on delete set null;
