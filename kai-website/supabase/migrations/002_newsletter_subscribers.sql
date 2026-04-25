-- Newsletter subscribers table
create table if not exists public.newsletter_subscribers (
  id           uuid primary key default gen_random_uuid(),
  email        text not null unique,
  name         text,
  confirmed    boolean not null default false,
  confirm_token text unique,
  is_active    boolean not null default true,
  newsletter_ai boolean not null default true,
  source       text not null default 'website',
  confirmed_at timestamptz,
  unsubscribed_at timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- Safe upgrades if the table already existed before these workflow fields.
alter table public.newsletter_subscribers
  add column if not exists is_active boolean not null default true,
  add column if not exists newsletter_ai boolean not null default true,
  add column if not exists unsubscribed_at timestamptz;

-- Index for fast token lookup on confirm
create index if not exists idx_newsletter_confirm_token
  on public.newsletter_subscribers (confirm_token)
  where confirm_token is not null;

-- Index for n8n queries: only confirmed subscribers
create index if not exists idx_newsletter_confirmed
  on public.newsletter_subscribers (confirmed, created_at desc);

-- Index for n8n daily sends: only confirmed and active subscribers
create index if not exists idx_newsletter_sendable
  on public.newsletter_subscribers (created_at desc)
  where confirmed = true
    and is_active = true
    and newsletter_ai = true
    and unsubscribed_at is null;

-- Row-level security: no public reads or writes (service role only)
alter table public.newsletter_subscribers enable row level security;

-- No public policies: all access via service role key from API

comment on table public.newsletter_subscribers is
  'Double opt-in newsletter subscribers for k2-ai.it';
