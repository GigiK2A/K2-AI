create table if not exists public.newsletter_issues (
  id bigserial primary key,
  slug text not null unique,
  subject text not null,
  preview_text text,
  html text not null,
  source text,
  published_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists newsletter_issues_published_at_idx
  on public.newsletter_issues (published_at desc);
