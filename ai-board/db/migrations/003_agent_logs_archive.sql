create table if not exists agent_logs_archive (
    id uuid primary key,
    agent text not null,
    task_id uuid,
    action text not null,
    llm_provider text,
    llm_model text,
    input_summary text,
    output_summary text,
    status text not null,
    tokens_used int,
    duration_ms int,
    created_at timestamptz not null,
    project_id uuid,
    archived_at timestamptz not null default now()
);

create index if not exists idx_agent_logs_archive_agent on agent_logs_archive(agent);
create index if not exists idx_agent_logs_archive_created_at on agent_logs_archive(created_at desc);
create index if not exists idx_agent_logs_archive_archived_at on agent_logs_archive(archived_at desc);
create index if not exists idx_agent_logs_archive_project on agent_logs_archive(project_id);
