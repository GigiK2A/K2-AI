-- Tasks
create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    description text not null,
    assigned_to text not null,
    requested_by text not null default 'founder',
    status text not null default 'pending',
    priority int not null default 3,
    input_data jsonb,
    output_data jsonb,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Agent logs
create table if not exists agent_logs (
    id uuid primary key default gen_random_uuid(),
    agent text not null,
    task_id uuid references tasks(id) on delete set null,
    action text not null,
    llm_provider text,
    llm_model text,
    input_summary text,
    output_summary text,
    status text not null,
    tokens_used int,
    duration_ms int,
    created_at timestamptz not null default now()
);

-- Approvals
create table if not exists approvals (
    id uuid primary key default gen_random_uuid(),
    task_id uuid references tasks(id) on delete cascade,
    agent text not null,
    content_type text not null,
    content_preview text not null,
    full_content jsonb not null,
    status text not null default 'draft',
    founder_notes text,
    created_at timestamptz not null default now(),
    reviewed_at timestamptz
);

-- Pipeline leads
create table if not exists pipeline_leads (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    company text,
    sector text,
    channel text,
    pain_point text,
    offer_fit text,
    status text not null default 'identified',
    score int check (score >= 1 and score <= 10),
    next_action text,
    next_action_date timestamptz,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Shared memory
create table if not exists shared_memory (
    key text primary key,
    value jsonb not null,
    category text not null,
    updated_at timestamptz not null default now(),
    updated_by text not null default 'founder'
);

-- Indexes utili
create index if not exists idx_tasks_status on tasks(status);
create index if not exists idx_tasks_assigned_to on tasks(assigned_to);
create index if not exists idx_agent_logs_agent on agent_logs(agent);
create index if not exists idx_agent_logs_created_at on agent_logs(created_at desc);
create index if not exists idx_approvals_status on approvals(status);
create index if not exists idx_pipeline_leads_status on pipeline_leads(status);
