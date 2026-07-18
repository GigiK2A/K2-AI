-- AIOS · Primitiva #4 (Paperclip): heartbeat per-agente.
--
-- Persistenza del last-run per dominio, così un riavvio del loop di autonomia non
-- rifà ripartire tutti gli agenti in blocco. Scritta SOLO dal loop (BLOCKED per gli agenti).
-- Opt-in: attiva il ritmo per-agente impostando AIOS_HEARTBEATS nell'env.

create table if not exists public.aios_heartbeats (
    actor            text primary key,
    interval_seconds integer not null default 86400,
    last_run_epoch   double precision,               -- epoch dell'ultimo run (per lo scheduler)
    last_run_at      timestamptz,
    updated_at       timestamptz not null default now()
);

alter table public.aios_heartbeats enable row level security;
