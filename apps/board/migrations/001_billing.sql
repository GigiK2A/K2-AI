-- AIOS · Primitiva #1 (Paperclip): metering costi LLM + budget con hard-stop.
--
-- Lo schema dell'AIOS è provisionato out-of-band direttamente su Supabase (non ci
-- sono migration applicate da codice). Questo file è la fonte di verità delle
-- tabelle di billing: applicalo una volta nel SQL editor di Supabase.
--
-- Nessuna di queste tabelle è scrivibile dagli agenti: sono nella BLOCKED list
-- dell'attuatore. Le scrive solo il CostMeter di sistema (billing.py).

-- Ledger append-only: una riga per chiamata LLM, con token e costo stimato.
create table if not exists public.aios_cost_ledger (
    id            bigint generated always as identity primary key,
    ts            timestamptz not null default now(),
    actor         text not null,               -- es. finance_agent, marketing_agent, system
    period        text not null,               -- 'YYYY-MM' (UTC)
    model         text not null,
    input_tokens  integer not null default 0,
    output_tokens integer not null default 0,
    cost_eur      numeric(12,6) not null default 0
);
create index if not exists aios_cost_ledger_actor_period_idx
    on public.aios_cost_ledger (actor, period);
create index if not exists aios_cost_ledger_ts_idx
    on public.aios_cost_ledger (ts desc);

-- Running-state: spesa aggregata per (agente, mese) — letta O(1) dal gate hard-stop.
-- Stesso pattern di aios_policy_state.
create table if not exists public.aios_budget_state (
    actor      text not null,
    period     text not null,                  -- 'YYYY-MM'
    spent_eur  numeric(12,6) not null default 0,
    updated_at timestamptz not null default now(),
    primary key (actor, period)
);

-- Config dei tetti mensili per agente (opzionale: in alternativa si usa
-- l'env AIOS_AGENT_BUDGETS / AIOS_DEFAULT_AGENT_BUDGET_EUR).
create table if not exists public.aios_agent_budgets (
    actor            text primary key,
    monthly_cap_eur  numeric(12,2) not null,
    active           boolean not null default true,
    updated_at       timestamptz not null default now()
);
