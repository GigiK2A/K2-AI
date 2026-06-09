-- 006 — Layer crediti + abbonamenti K-BOT (modello: catalogo_documenti.json)
-- Free 0€/0cr · Pro 49€/50cr/-10% · Business 149€/200cr/-20% · 1cr=1€ · inattività 12 mesi
-- I crediti pagano i Check express (Consumo). I Boost restano a prezzo (mai crediti).
-- Additivo e reversibile. RLS: l'utente vede solo i propri dati; scrittura via service_role/RPC.

-- ---------- Abbonamenti ----------
create table if not exists public.kbot_subscriptions (
  user_id                uuid primary key references auth.users(id) on delete cascade,
  plan                   text not null default 'free' check (plan in ('free','pro','business')),
  status                 text not null default 'active' check (status in ('active','past_due','canceled')),
  stripe_customer_id     text,
  stripe_subscription_id text,
  current_period_end     timestamptz,
  updated_at             timestamptz not null default now(),
  created_at             timestamptz not null default now()
);
alter table public.kbot_subscriptions enable row level security;
drop policy if exists kbot_subscriptions_sel_own on public.kbot_subscriptions;
create policy kbot_subscriptions_sel_own on public.kbot_subscriptions
  for select using (auth.uid() = user_id);

-- ---------- Ledger crediti (append-only) ----------
-- delta>0 = accredito (grant mensile / pacchetto); delta<0 = consumo.
-- expires_at: crediti piano scadono (es. 30gg), pacchetti extra 365gg, null = mai.
create table if not exists public.kbot_credit_ledger (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  delta       integer not null,
  reason      text not null,                 -- monthly_grant | package | consume | refund | expire
  ref         text,                          -- service_id, package id, stripe id...
  expires_at  timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists kbot_credit_ledger_user_idx on public.kbot_credit_ledger(user_id, created_at);
alter table public.kbot_credit_ledger enable row level security;
drop policy if exists kbot_credit_ledger_sel_own on public.kbot_credit_ledger;
create policy kbot_credit_ledger_sel_own on public.kbot_credit_ledger
  for select using (auth.uid() = user_id);

-- ---------- Saldo crediti (esclude scaduti) ----------
create or replace function public.kbot_credit_balance(p_user uuid)
returns integer
language sql stable security definer set search_path = public, pg_temp
as $$
  select coalesce(sum(delta),0)::int
  from public.kbot_credit_ledger
  where user_id = p_user and (expires_at is null or expires_at > now());
$$;

-- ---------- Consumo atomico (race-safe) ----------
-- Ritorna il nuovo saldo; solleva se insufficiente.
create or replace function public.kbot_consume_credits(
  p_user uuid, p_amount int, p_reason text default 'consume', p_ref text default null)
returns integer
language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_bal int;
begin
  if p_amount <= 0 then raise exception 'amount must be positive'; end if;
  -- blocca le righe dell'utente per evitare doppio-spend concorrente
  perform 1 from public.kbot_credit_ledger where user_id = p_user for update;
  v_bal := public.kbot_credit_balance(p_user);
  if v_bal < p_amount then
    raise exception 'insufficient_credits: have % need %', v_bal, p_amount using errcode = 'P0001';
  end if;
  insert into public.kbot_credit_ledger(user_id, delta, reason, ref)
    values (p_user, -p_amount, p_reason, p_ref);
  return v_bal - p_amount;
end;
$$;

-- ---------- Accredito (grant mensile / pacchetto) ----------
create or replace function public.kbot_grant_credits(
  p_user uuid, p_amount int, p_reason text, p_ref text default null, p_expires timestamptz default null)
returns integer
language plpgsql security definer set search_path = public, pg_temp
as $$
begin
  if p_amount <= 0 then raise exception 'amount must be positive'; end if;
  insert into public.kbot_credit_ledger(user_id, delta, reason, ref, expires_at)
    values (p_user, p_amount, p_reason, p_ref, p_expires);
  return public.kbot_credit_balance(p_user);
end;
$$;

-- Permessi: solo service_role esegue le funzioni di scrittura (mai anon/authenticated via REST)
revoke execute on function public.kbot_consume_credits(uuid,int,text,text) from public, anon, authenticated;
revoke execute on function public.kbot_grant_credits(uuid,int,text,text,timestamptz) from public, anon, authenticated;
grant execute on function public.kbot_consume_credits(uuid,int,text,text) to service_role;
grant execute on function public.kbot_grant_credits(uuid,int,text,text,timestamptz) to service_role;
-- balance: leggibile dall'utente sui propri crediti
revoke execute on function public.kbot_credit_balance(uuid) from public, anon;
grant execute on function public.kbot_credit_balance(uuid) to authenticated, service_role;
