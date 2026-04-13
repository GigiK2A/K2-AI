-- Progetti cliente
create table if not exists projects (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    client_name text,
    sector text,
    offer_type text,
    status text not null default 'active',
    progress_pct int not null default 0,
    start_date date,
    end_date_estimated date,
    agent_ref text,
    value_eur int,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Fasi progetto
create table if not exists project_phases (
    id uuid primary key default gen_random_uuid(),
    project_id uuid references projects(id) on delete cascade,
    name text not null,
    status text not null default 'pending',
    phase_order int not null,
    date_completed timestamptz,
    date_estimated date
);

-- Task progetto
create table if not exists project_tasks (
    id uuid primary key default gen_random_uuid(),
    project_id uuid references projects(id) on delete cascade,
    title text not null,
    status text not null default 'pending',
    due_date date,
    completed_at timestamptz
);

-- Documenti progetto
create table if not exists project_documents (
    id uuid primary key default gen_random_uuid(),
    project_id uuid references projects(id) on delete cascade,
    filename text not null,
    filepath text not null,
    source text not null default 'upload',
    agent_log_id uuid references agent_logs(id) on delete set null,
    created_at timestamptz not null default now()
);

-- Agenti collegati al progetto
create table if not exists project_agent_links (
    id uuid primary key default gen_random_uuid(),
    project_id uuid references projects(id) on delete cascade,
    agent_name text not null,
    role text
);

-- Aggiungi project_id alle tabelle esistenti
alter table approvals add column if not exists project_id uuid references projects(id) on delete set null;
alter table agent_logs add column if not exists project_id uuid references projects(id) on delete set null;

-- Indici
create index if not exists idx_projects_status on projects(status);
create index if not exists idx_project_phases_project on project_phases(project_id);
create index if not exists idx_project_tasks_project on project_tasks(project_id);
create index if not exists idx_project_docs_project on project_documents(project_id);
create index if not exists idx_approvals_project on approvals(project_id);
