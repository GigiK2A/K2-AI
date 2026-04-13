create table if not exists board_users (
    id uuid primary key default gen_random_uuid(),
    email text not null unique,
    display_name text,
    role text not null default 'viewer' check (role in ('admin', 'operator', 'viewer')),
    password_hash text not null,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    last_login_at timestamptz
);

create table if not exists board_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references board_users(id) on delete cascade,
    token_hash text not null unique,
    created_at timestamptz not null default now(),
    expires_at timestamptz not null,
    last_seen_at timestamptz,
    user_agent text,
    ip_address text
);

create index if not exists idx_board_users_role on board_users(role);
create index if not exists idx_board_users_active on board_users(is_active);
create index if not exists idx_board_sessions_user on board_sessions(user_id);
create index if not exists idx_board_sessions_expires on board_sessions(expires_at);
